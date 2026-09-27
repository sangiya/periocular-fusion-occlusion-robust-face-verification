"""Recompute the manuscript's headline numbers from the shipped result files.

This needs **no GPU, no dataset, and no checkpoints**. It reads only the metric
JSON files in ``results/seed_sweep/`` and rebuilds the aggregates the paper
reports, so a reviewer or co-author can confirm the tables without rerunning a
single training run.

It prints a PASS/FAIL line for every claimed value and exits non-zero if any
claim does not match the shipped files.

Usage:

    python code/verify_results.py
    python code/verify_results.py --results-dir results/seed_sweep
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (label, value the manuscript reports, tolerance)
CLAIMED_NEUTRAL_AUC = [
    ("gated_fusion", 0.9441, 5e-5),
    ("fixed_fusion", 0.9424, 5e-5),
    ("peri_lora", 0.8832, 5e-5),
]

EXPECTED_SEEDS = [7, 42, 123]
EXPECTED_VARIANTS = [
    "frozen_whole",
    "whole_lora",
    "peri_lora",
    "fixed_fusion",
    "gated_fusion",
]
EXPECTED_CONDITIONS = ["masked", "sunglasses", "neutral"]
EXPECTED_CROSS = ["mfr2", "rmfrd", "neutral"]


class Report:
    def __init__(self) -> None:
        self.failures: list[str] = []

    def check(self, label: str, ok: bool, detail: str = "") -> None:
        mark = "PASS" if ok else "FAIL"
        print(f"  [{mark}] {label}{('  ' + detail) if detail else ''}")
        if not ok:
            self.failures.append(label)


def load_metrics(folder: Path) -> dict[tuple[int, str, str], dict]:
    out: dict[tuple[int, str, str], dict] = {}
    if not folder.is_dir():
        return out
    for path in sorted(folder.glob("seed*_metrics.json")):
        stem = path.name[: -len("_metrics.json")]
        parts = stem.split("_")
        if len(parts) < 3:
            continue
        seed = int(parts[0].replace("seed", ""))
        variant = "_".join(parts[1:-1])
        condition = parts[-1]
        try:
            out[(seed, variant, condition)] = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"  [FAIL] unreadable JSON: {path.name} ({exc})")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", type=Path, default=ROOT / "results" / "seed_sweep")
    args = ap.parse_args()

    base = args.results_dir
    rep = Report()

    print("=" * 74)
    print("VERIFICATION OF SHIPPED RESULTS (no GPU, no dataset, no retraining)")
    print("=" * 74)
    print(f"Results directory: {base}")
    print()

    # ---------------------------------------------------------------- ROF
    rof_dir = base / "rof_seed_sweep"
    rof = load_metrics(rof_dir)
    print("1. ROF sweep completeness")
    expected = len(EXPECTED_SEEDS) * len(EXPECTED_VARIANTS) * len(EXPECTED_CONDITIONS)
    rep.check(f"ROF metric files present ({expected} expected)",
              len(rof) == expected, f"found {len(rof)}")
    for cond in EXPECTED_CONDITIONS:
        n = sum(1 for k in rof if k[2] == cond)
        rep.check(f"ROF condition '{cond}'", n == len(EXPECTED_SEEDS) * len(EXPECTED_VARIANTS),
                  f"{n} files")

    # ------------------------------------------------------- headline AUC
    print()
    print("2. Headline neutral-condition mean AUC (manuscript Table)")
    for variant, claimed, tol in CLAIMED_NEUTRAL_AUC:
        vals = [rof[(s, variant, "neutral")]["auc"]
                for s in EXPECTED_SEEDS
                if (s, variant, "neutral") in rof]
        if len(vals) != len(EXPECTED_SEEDS):
            rep.check(f"{variant} neutral AUC", False, f"only {len(vals)} seeds found")
            continue
        mean = statistics.mean(vals)
        rep.check(f"{variant:<14} mean AUC = {mean:.4f} (claimed {claimed:.4f})",
                  abs(mean - claimed) <= tol, f"n={len(vals)}")

    # ------------------------------------------------------ hash presence
    print()
    print("3. Provenance fields recorded in result files")
    missing_ck = [k for k, v in rof.items() if not v.get("checkpoint_sha256")]
    missing_ps = [k for k, v in rof.items() if not v.get("pairs_sha256")]
    rep.check("every ROF metric records checkpoint_sha256",
              not missing_ck, f"missing in {len(missing_ck)}")
    rep.check("every ROF metric records pairs_sha256",
              not missing_ps, f"missing in {len(missing_ps)}")
    devices = {v.get("device") for v in rof.values()}
    rep.check("execution device recorded", devices == {"cpu"}, f"devices={sorted(map(str, devices))}")

    # --------------------------------------------------------- cross-dataset
    print()
    print("4. Cross-dataset evaluation (MFR2 / RMFRD / neutral)")
    cross = load_metrics(base / "cross_dataset")
    rep.check(f"cross-dataset metric files ({len(EXPECTED_SEEDS) * len(EXPECTED_VARIANTS) * len(EXPECTED_CROSS)} expected)",
              len(cross) == len(EXPECTED_SEEDS) * len(EXPECTED_VARIANTS) * len(EXPECTED_CROSS),
              f"found {len(cross)}")
    for cond in EXPECTED_CROSS:
        n = sum(1 for k in cross if k[2] == cond)
        rep.check(f"cross-dataset protocol '{cond}'",
                  n == len(EXPECTED_SEEDS) * len(EXPECTED_VARIANTS), f"{n} files")

    # ------------------------------------------------------------- summary
    print()
    print("5. Aggregate summary file")
    summary_path = base / "seed_sweep_summary.json"
    if summary_path.is_file():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        rep.check("summary lists 3 seeds",
                  sorted(summary.get("seeds", [])) == EXPECTED_SEEDS,
                  str(summary.get("seeds")))
        rep.check("summary lists 5 variants", summary.get("variants") == EXPECTED_VARIANTS)
        rep.check("summary lists 3 protocols", summary.get("protocols") == EXPECTED_CONDITIONS)
        rep.check("summary has 45 per-run rows", len(summary.get("per_run", [])) == 45,
                  f"{len(summary.get('per_run', []))} rows")
    else:
        rep.check("seed_sweep_summary.json present", False, str(summary_path))

    # -------------------------------------------------------- comparisons
    print()
    print("6. Paired comparisons")
    n_cmp = len(list(base.glob("comparison_*.json")))
    rep.check("18 comparison files (2 contrasts x 3 conditions x 3 seeds)",
              n_cmp == 18, f"found {n_cmp}")

    # -------------------------------------------------------------- verdict
    print()
    print("=" * 74)
    if rep.failures:
        print(f"RESULT: {len(rep.failures)} CHECK(S) FAILED")
        for f in rep.failures:
            print(f"  - {f}")
        return 1
    print("RESULT: ALL CHECKS PASSED")
    print("The shipped result files reproduce every headline value in the manuscript.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
