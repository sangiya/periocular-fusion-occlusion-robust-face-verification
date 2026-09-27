"""Multi-seed robustness sweep driver.

Trains all seeds x 5 variants (fresh, including seed 42), evaluates every run on
the three ROF protocols (masked, sunglasses, neutral), computes paired comparisons,
and writes a summary.

Resumable: every stage skips work whose outputs already exist, and partial
(< epoch 5) checkpoints are deleted and retrained.

Paths are resolved relative to this file. The manifest and protocol pair files
are located automatically so the driver works both in the original working tree
and in a clean extraction of this release bundle.
"""

from __future__ import annotations

import json
import statistics
import subprocess
import sys
import time
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parent
CODE = ROOT / "code"
CKPT_DIR = ROOT / "work" / "seed_sweep" / "checkpoints"
RESULT_DIR = ROOT / "Final Results" / "seed_sweep"
WORK_RES = ROOT / "work" / "seed_sweep" / "results"
LOG_DIR = ROOT / "work" / "seed_sweep" / "logs"
RUNNING = ROOT / "work" / "seed_sweep" / "RUNNING"


def _first_existing(*candidates: Path) -> Path:
    """Return the first candidate that exists, else the first (for error messages)."""
    for c in candidates:
        if c.is_file():
            return c
    return candidates[0]


MANIFEST = _first_existing(
    ROOT / "work" / "crop_manifest_training_person_disjoint.csv",
    ROOT / "manifests" / "crop_manifest_training_person_disjoint.csv",
)

PAIRS = {
    "masked": _first_existing(
        ROOT / "work" / "protocol_v2" / "rof_masked_pairs.csv",
        ROOT / "manifests" / "rof_masked_pairs.csv",
    ),
    "sunglasses": _first_existing(
        ROOT / "work" / "protocol_v2" / "rof_sunglasses_pairs.csv",
        ROOT / "manifests" / "rof_sunglasses_pairs.csv",
    ),
    "neutral": _first_existing(
        ROOT / "Final Results" / "neutral_eval" / "rof_neutral_pairs.csv",
        ROOT / "manifests" / "rof_neutral_pairs.csv",
    ),
}

SEEDS = [123, 7, 42]  # finish seed 123 (gated) -> seed 7 (frozen_whole partial) -> seed 42
VARIANTS = ["frozen_whole", "whole_lora", "peri_lora", "fixed_fusion", "gated_fusion"]


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def run(args, tag: str) -> None:
    log(f"RUN {tag}: " + " ".join(args))
    t0 = time.time()
    proc = subprocess.run([sys.executable, "-m"] if False else [sys.executable] + args,
                          cwd=str(ROOT), capture_output=True, text=True)
    if proc.returncode != 0:
        log(f"FAIL {tag}: {proc.stderr[-2000:]}")
        raise RuntimeError(f"{tag} failed (see log). Exit {proc.returncode}")
    log(f"DONE {tag} in {time.time() - t0:.1f}s")


def metric_prefix(seed: int, variant: str, cond: str) -> Path:
    return WORK_RES / f"seed{seed}_{variant}_{cond}"


def checkpoint_is_final(ckpt: Path) -> bool:
    try:
        c = torch.load(ckpt, map_location="cpu", weights_only=False)
        return int(c.get("epoch", 0)) >= 5
    except Exception:
        return False


def train_seed(seed: int) -> None:
    for v in VARIANTS:
        ckpt = CKPT_DIR / f"seed{seed}_{v}.pt"
        if ckpt.is_file() and checkpoint_is_final(ckpt):
            log(f"skip train {seed}/{v} (epoch-5 checkpoint exists)")
            continue
        args = [
            str(CODE / "train.py"),
            "--manifest", str(MANIFEST),
            "--variant", v,
            "--epochs", "5",
            "--batch-size", "16",
            "--lr", "1e-4",
            "--seed", str(seed),
            "--num-workers", "0",
            "--max-batches", "0",
            "--out", str(ckpt),
        ]
        if ckpt.is_file():
            log(f"resume {seed}/{v} from partial {ckpt.name}")
            args += ["--resume-from", str(ckpt)]
        run(args, f"train seed={seed} variant={v}")


def eval_seed(seed: int) -> None:
    for v in VARIANTS:
        ckpt = CKPT_DIR / f"seed{seed}_{v}.pt"
        if not (ckpt.is_file() and checkpoint_is_final(ckpt)):
            log(f"skip eval {seed}/{v} (no epoch-5 checkpoint)")
            continue
        for cond, pairs in PAIRS.items():
            prefix = metric_prefix(seed, v, cond)
            if Path(str(prefix) + "_metrics.json").is_file():
                log(f"skip eval {seed}/{v}/{cond} (exists)")
                continue
            run([
                str(CODE / "evaluate_rof_protocol.py"),
                "--pairs", str(pairs),
                "--checkpoint", str(ckpt),
                "--batch-size", "8",
                "--bootstrap", "1000",
                "--seed", "42",
                "--out-prefix", str(prefix),
            ], f"eval seed={seed} variant={v} cond={cond}")


def comparisons() -> None:
    for seed in SEEDS:
        for cond in PAIRS:
            for a, b, out_name in (
                ("gated_fusion", "fixed_fusion", "gated_vs_fixed"),
                ("fixed_fusion", "frozen_whole", "fixed_vs_frozen"),
            ):
                ref_prefix = metric_prefix(seed, b, cond)
                cand_prefix = metric_prefix(seed, a, cond)
                out = RESULT_DIR / f"comparison_seed{seed}_{cond}_{out_name}.json"
                if out.is_file():
                    continue
                run([
                    str(CODE / "compare_rof_models.py"),
                    "--reference", str(ref_prefix) + "_raw_scores.csv",
                    "--candidate", str(cand_prefix) + "_raw_scores.csv",
                    "--bootstrap", "5000",
                    "--seed", "42",
                    "--out", str(out),
                ], f"compare seed={seed} cond={cond} {out_name}")


def summarize() -> None:
    rows = []
    for seed in SEEDS:
        for v in VARIANTS:
            for cond in PAIRS:
                mpath = Path(str(metric_prefix(seed, v, cond)) + "_metrics.json")
                if not mpath.is_file():
                    continue
                j = json.loads(mpath.read_text(encoding="utf-8"))
                ci = (j.get("identity_bootstrap_ci") or {}).get("auc") or [float("nan"), float("nan")]
                rows.append({
                    "seed": seed, "variant": v, "condition": cond,
                    "auc": float(j.get("auc", float("nan"))),
                    "auc_ci_low": float(ci[0]), "auc_ci_high": float(ci[1]),
                    "eer": float(j.get("eer", float("nan"))),
                    "tar_far_1e-2": float(j.get("tar_far_1e-2", float("nan"))),
                    "tar_far_1e-3": float(j.get("tar_far_1e-3", float("nan"))),
                })
    summary = {"seeds": SEEDS, "variants": VARIANTS, "protocols": list(PAIRS), "per_run": rows}
    agg = {}
    for v in VARIANTS:
        agg[v] = {}
        for cond in PAIRS:
            vals = [r["auc"] for r in rows if r["variant"] == v and r["condition"] == cond]
            eers = [r["eer"] for r in rows if r["variant"] == v and r["condition"] == cond]
            if not vals:
                continue
            import statistics
            agg[v][cond] = {
                "auc_mean": statistics.mean(vals), "auc_std": statistics.stdev(vals) if len(vals) > 1 else 0.0,
                "auc_min": min(vals), "auc_max": max(vals),
                "eer_mean": statistics.mean(eers), "eer_std": statistics.stdev(eers) if len(eers) > 1 else 0.0,
                "n_seeds": len(vals),
            }
    summary["aggregated_variant_x_condition"] = agg
    out = RESULT_DIR / "seed_sweep_summary.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    log(f"Wrote {out}")
    import csv as _csv
    csv_path = RESULT_DIR / "seed_sweep_summary.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = _csv.DictWriter(f, fieldnames=list(summary["per_run"][0].keys()) + ["variant_inferred"])
        w.writeheader()
        for r in rows:
            w.writerow(r)
    log(f"Wrote {csv_path}")


def preflight() -> None:
    """Fail fast with actionable messages if required inputs are missing."""
    missing = []
    if not MANIFEST.is_file():
        missing.append(f"training manifest: {MANIFEST}")
    for cond, p in PAIRS.items():
        if not p.is_file():
            missing.append(f"{cond} protocol pairs: {p}")
    if missing:
        raise SystemExit(
            "Cannot start the sweep. Missing required input files:\n"
            + "\n".join(f"  - {m}" for m in missing)
            + "\n\nSee WINDOWS_REPRODUCTION_GUIDE.md for how to regenerate them."
        )
    log(f"manifest: {MANIFEST}")
    for cond, p in PAIRS.items():
        log(f"pairs[{cond}]: {p}")


def main() -> None:
    preflight()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    WORK_RES.mkdir(parents=True, exist_ok=True)
    CKPT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    if RUNNING.exists():
        log("Another run is active (work/seed_sweep/RUNNING exists). Refusing to start.")
        return
    RUNNING.write_text(str(time.time()))

    try:
        t0 = time.time()
        for seed in SEEDS:
            train_seed(seed)
        for seed in SEEDS:
            eval_seed(seed)
        comparisons()
        summarize()
        log(f"SWEEP COMPLETE in {(time.time() - t0) / 3600:.1f} h")
    finally:
        RUNNING.unlink(missing_ok=True)


if __name__ == "__main__":
    main()