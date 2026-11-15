"""Evaluate all seed-sweep checkpoints on MFR2, RMFRD, and Neutral protocols."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import os
import time
from pathlib import Path

import numpy as np
from PIL import Image
import torch
from torchvision.transforms import v2

from model import VerificationModel
from verification import summarize


SEEDS = [7, 42, 123]
VARIANTS = ["frozen_whole", "whole_lora", "peri_lora", "fixed_fusion", "gated_fusion"]

PAIR_FILES = {
    "mfr2": "work/mfr2_protocol/mfr2_official_complete_pairs.csv",
    "rmfrd": "work/rmfrd_protocol_v2/rmfrd_pairs.csv",
    "neutral": "Final Results/neutral_eval/rof_neutral_pairs.csv",
}


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def number(value: str, default: float) -> float:
    try:
        x = float(value)
        return x if np.isfinite(x) else default
    except (TypeError, ValueError):
        return default


def identity_bootstrap(scores: np.ndarray, labels: np.ndarray, subjects: np.ndarray,
                       n_boot: int, seed: int) -> dict[str, list[float]]:
    unique = np.unique(subjects)
    rng = np.random.default_rng(seed)
    values = {"auc": [], "eer": [], "tar_far_1e-2": [], "tar_far_1e-3": []}
    for _ in range(n_boot):
        sampled = rng.choice(unique, size=len(unique), replace=True)
        indices = np.concatenate([np.where(subjects == subject)[0] for subject in sampled])
        if len(np.unique(labels[indices])) < 2:
            continue
        metrics = summarize(scores[indices], labels[indices])
        for key in values:
            values[key].append(float(metrics[key]))
    return {key: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]
            for key, v in values.items() if v}


def evaluate_standard(checkpoint_path: Path, pairs_path: Path, out_prefix: Path,
                      batch_size: int = 8, bootstrap: int = 1000, seed: int = 42) -> dict:
    """Standard ROF/neutral protocol with probe/enroll columns."""
    started = time.time()
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    with open(pairs_path, newline="", encoding="utf-8") as f:
        pairs = list(csv.DictReader(f))
    if not pairs:
        raise ValueError(f"Pair CSV empty: {pairs_path}")

    images = {}
    for pair in pairs:
        for role in ("probe", "enroll"):
            iid = pair[f"{role}_image_id"]
            images[iid] = {
                "face_path": pair[f"{role}_face_path"], "peri_path": pair[f"{role}_peri_path"],
                "quality": [number(pair.get(f"{role}_face_conf", ""), 1.0),
                            number(pair.get(f"{role}_peri_conf", ""), 1.0),
                            number(pair.get(f"{role}_blur", ""), 0.0),
                            number(pair.get(f"{role}_visible_ratio", ""), 1.0)],
            }
    for iid, row in images.items():
        for key in ("face_path", "peri_path"):
            if not Path(row[key]).is_file():
                raise FileNotFoundError(f"Missing {key} for {iid}: {row[key]}")

    checkpoint = torch.load(str(checkpoint_path), map_location="cpu", weights_only=False)
    variant = checkpoint["variant"]
    model = VerificationModel(variant)
    state = checkpoint["model"]
    if state and all(key.startswith("module.") for key in state):
        state = {key[7:]: value for key, value in state.items()}
    model.load_state_dict(state)
    model.to(device).eval()

    transform = v2.Compose([v2.ToImage(), v2.Resize((224, 224)),
                            v2.ToDtype(torch.float32, scale=True),
                            v2.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])
    ids = sorted(images)
    embeddings = {}

    for iid in ids:
        row = images[iid]
        face = transform(Image.open(row["face_path"]).convert("RGB")).unsqueeze(0).to(device)
        peri = transform(Image.open(row["peri_path"]).convert("RGB")).unsqueeze(0).to(device)
        quality = torch.tensor(row["quality"], dtype=torch.float32).unsqueeze(0).to(device)
        with torch.no_grad():
            emb = model(face, peri, quality)
        embeddings[iid] = emb.squeeze(0).cpu()

    scores = []
    labels = []
    subjects = []
    for pair in pairs:
        e = embeddings[pair["enroll_image_id"]]
        p = embeddings[pair["probe_image_id"]]
        score = float((e * p).sum())
        scores.append(score)
        labels.append(int(pair["label"]))
        subjects.append(pair["enroll_identity"])
    scores = np.array(scores, dtype=np.float32)
    labels = np.array(labels, dtype=np.int32)
    subjects = np.array(subjects)

    metrics = summarize(scores, labels)
    ci = identity_bootstrap(scores, labels, subjects, bootstrap, seed)
    for k in ci:
        metrics[f"{k}_ci_low"] = ci[k][0]
        metrics[f"{k}_ci_high"] = ci[k][1]

    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    raw_path = Path(str(out_prefix) + "_raw_scores.csv")
    with open(raw_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["enroll_id", "probe_id", "enroll_identity", "probe_identity", "score", "label"])
        for i, pair in enumerate(pairs):
            w.writerow([pair["enroll_image_id"], pair["probe_image_id"],
                        pair["enroll_identity"], pair["probe_identity"],
                        f"{scores[i]:.10f}", labels[i]])

    meta = {
        "checkpoint": str(checkpoint_path),
        "checkpoint_sha256": sha256(str(checkpoint_path)),
        "pairs": str(pairs_path),
        "pairs_sha256": sha256(str(pairs_path)),
        "variant": variant,
        "seed": seed,
        "training_seed": checkpoint.get("seed"),
        "bootstrap_seed": seed,
        "device": str(device),
        "evaluator_sha256": sha256(__file__),
        "raw_scores_sha256": sha256(str(raw_path)),
        "elapsed_seconds": time.time() - started,
        "batch_size": batch_size,
        "bootstrap": bootstrap,
        "num_pairs": len(pairs),
        "num_genuine": int(np.sum(labels == 1)),
        "num_impostor": int(np.sum(labels == 0)),
        "num_identities": len(np.unique(subjects)),
        "metrics": metrics,
    }
    meta_path = Path(str(out_prefix) + "_metrics.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"  {out_prefix.name}: AUC={metrics['auc']:.4f}, EER={metrics['eer']:.4f}, "
          f"TAR@1e-2={metrics['tar_far_1e-2']:.4f}, TAR@1e-3={metrics['tar_far_1e-3']:.4f}")
    return meta


def evaluate_mfr2(checkpoint_path: Path, pairs_path: Path, out_prefix: Path,
                  batch_size: int = 8, bootstrap: int = 1000, seed: int = 42) -> dict:
    """MFR2 protocol evaluated per unique image path, not per identity.

    Important: an identity can have multiple images in the official pair list. Using
    identity as an embedding-cache key collapses those images and can turn genuine
    comparisons into self-comparisons. Each face/periocular image pair is therefore
    keyed by its concrete paths.
    """
    started = time.time()
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    with open(pairs_path, newline="", encoding="utf-8") as f:
        pairs = list(csv.DictReader(f))
    if not pairs:
        raise ValueError(f"Pair CSV empty: {pairs_path}")

    required = {"identity1", "identity2", "face_path1", "face_path2",
                "peri_path1", "peri_path2", "label"}
    missing = required.difference(pairs[0])
    if missing:
        raise ValueError(f"MFR2 pair CSV missing columns: {sorted(missing)}")

    # Cache by the concrete image pair. Do NOT cache by identity: MFR2 can contain
    # multiple images for one identity and identity-keying corrupts pair scores.
    images = {}
    for pair in pairs:
        for idx in (1, 2):
            face_path = pair[f"face_path{idx}"]
            peri_path = pair[f"peri_path{idx}"]
            image_key = (face_path, peri_path)
            images[image_key] = {
                "face_path": face_path,
                "peri_path": peri_path,
                "quality": [1.0, 0.0, 0.0, 1.0],  # MFR2: match training distribution (all peri_conf=0 in training)
            }

    for image_key, row in images.items():
        for key in ("face_path", "peri_path"):
            if not Path(row[key]).is_file():
                raise FileNotFoundError(f"Missing {key} for {image_key}: {row[key]}")

    checkpoint = torch.load(str(checkpoint_path), map_location="cpu", weights_only=False)
    variant = checkpoint["variant"]
    model = VerificationModel(variant)
    state = checkpoint["model"]
    if state and all(key.startswith("module.") for key in state):
        state = {key[7:]: value for key, value in state.items()}
    model.load_state_dict(state)
    model.to(device).eval()

    transform = v2.Compose([v2.ToImage(), v2.Resize((224, 224)),
                            v2.ToDtype(torch.float32, scale=True),
                            v2.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])
    embeddings = {}

    image_keys = list(images)
    for start in range(0, len(image_keys), batch_size):
        keys = image_keys[start:start + batch_size]
        def load_rgb(path):
            with Image.open(path) as im:
                return transform(im.convert("RGB"))
        face = torch.stack([load_rgb(images[k]["face_path"]) for k in keys]).to(device)
        peri = torch.stack([load_rgb(images[k]["peri_path"]) for k in keys]).to(device)
        quality = torch.tensor([images[k]["quality"] for k in keys], dtype=torch.float32, device=device)
        with torch.inference_mode():
            emb = model(face, peri, quality).cpu()
        embeddings.update({k: emb[i] for i, k in enumerate(keys)})
        print(f"embedded {min(start + batch_size, len(image_keys))}/{len(image_keys)}", flush=True)

    scores = []
    labels = []
    subjects = []
    accidental_self_pairs = 0
    for pair in pairs:
        key1 = (pair["face_path1"], pair["peri_path1"])
        key2 = (pair["face_path2"], pair["peri_path2"])
        if key1 == key2:
            accidental_self_pairs += 1
        e = embeddings[key1]
        p = embeddings[key2]
        score = float((e * p).sum())
        scores.append(score)
        labels.append(int(pair["label"]))
        subjects.append(pair["identity1"])

    if accidental_self_pairs:
        raise ValueError(
            f"MFR2 protocol contains {accidental_self_pairs} exact image self-pairs; "
            "audit the pair CSV before reporting results."
        )

    scores = np.array(scores, dtype=np.float32)
    labels = np.array(labels, dtype=np.int32)
    subjects = np.array(subjects)

    metrics = summarize(scores, labels)
    ci = identity_bootstrap(scores, labels, subjects, bootstrap, seed)
    for k in ci:
        metrics[f"{k}_ci_low"] = ci[k][0]
        metrics[f"{k}_ci_high"] = ci[k][1]

    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    raw_path = Path(str(out_prefix) + "_raw_scores.csv")
    with open(raw_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["identity1", "identity2", "face_path1", "face_path2", "score", "label"])
        for i, pair in enumerate(pairs):
            w.writerow([pair["identity1"], pair["identity2"],
                        pair["face_path1"], pair["face_path2"],
                        f"{scores[i]:.10f}", labels[i]])

    meta = {
        "checkpoint": str(checkpoint_path),
        "checkpoint_sha256": sha256(str(checkpoint_path)),
        "pairs": str(pairs_path),
        "pairs_sha256": sha256(str(pairs_path)),
        "variant": variant,
        "seed": seed,
        "training_seed": checkpoint.get("seed"),
        "bootstrap_seed": seed,
        "device": str(device),
        "evaluator_sha256": sha256(__file__),
        "raw_scores_sha256": sha256(str(raw_path)),
        "elapsed_seconds": time.time() - started,
        "batch_size": batch_size,
        "bootstrap": bootstrap,
        "num_pairs": len(pairs),
        "num_genuine": int(np.sum(labels == 1)),
        "num_impostor": int(np.sum(labels == 0)),
        "num_identities": len(np.unique(subjects)),
        "num_unique_images": len(images),
        "embedding_cache_key": "(face_path, peri_path)",
        "quality_vector": [1.0, 0.0, 0.0, 1.0],
        "quality_policy": "constant matching archived complete-case training manifest",
        "metrics": metrics,
    }
    meta_path = Path(str(out_prefix) + "_metrics.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"  {out_prefix.name}: AUC={metrics['auc']:.4f}, EER={metrics['eer']:.4f}, "
          f"TAR@1e-2={metrics['tar_far_1e-2']:.4f}, TAR@1e-3={metrics['tar_far_1e-3']:.4f}")
    return meta


def main():
    parser = argparse.ArgumentParser(description="Evaluate final checkpoints; missing inputs and failed evaluations are errors")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, help="Root for relative image/crop paths; defaults to --root")
    parser.add_argument("--checkpoint-root", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42, help="Bootstrap RNG seed, not training seed")
    parser.add_argument("--seeds", type=int, nargs="+", default=SEEDS)
    parser.add_argument("--variants", choices=VARIANTS, nargs="+", default=VARIANTS)
    parser.add_argument("--protocol", choices=["all", "mfr2", "rmfrd", "neutral"], default="all")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if args.batch_size < 1 or args.bootstrap < 0:
        parser.error("--batch-size must be positive and --bootstrap nonnegative")
    root = args.root.resolve()
    data_root = (args.dataset_root or root).resolve()
    ckpt_dir = (args.checkpoint_root or root / "work/seed_sweep/checkpoints").resolve()
    out_dir = (args.output_dir or root / "Final Results/seed_sweep/cross_dataset").resolve()
    selected = list(PAIR_FILES) if args.protocol == "all" else [args.protocol]
    paths = {}
    for cond in selected:
        candidates = [root / PAIR_FILES[cond], root / "manifests" / Path(PAIR_FILES[cond]).name]
        paths[cond] = next((p for p in candidates if p.is_file()), candidates[0])
    missing = [str(p) for p in paths.values() if not p.is_file()]
    missing += [str(ckpt_dir / f"seed{s}_{v}.pt") for s in args.seeds for v in args.variants
                if not (ckpt_dir / f"seed{s}_{v}.pt").is_file()]
    if missing:
        raise SystemExit("Missing required inputs (no evaluation performed):\n" + "\n".join(missing))
    if not data_root.is_dir():
        raise SystemExit(f"Dataset root is not a directory: {data_root}")
    os.chdir(data_root)
    out_dir.mkdir(parents=True, exist_ok=True)
    completed = 0
    for training_seed in args.seeds:
        for variant in args.variants:
            ckpt = ckpt_dir / f"seed{training_seed}_{variant}.pt"
            for cond in selected:
                prefix = out_dir / f"seed{training_seed}_{variant}_{cond}"
                meta_path = Path(str(prefix) + "_metrics.json")
                raw_path = Path(str(prefix) + "_raw_scores.csv")
                if (meta_path.exists() or raw_path.exists()) and not args.overwrite:
                    raise SystemExit(f"Refusing to reuse possibly stale outputs: {prefix}; choose a new --output-dir or --overwrite")
                print(f"training_seed={training_seed} variant={variant} protocol={cond}", flush=True)
                fn = evaluate_mfr2 if cond == "mfr2" else evaluate_standard
                meta = fn(ckpt, paths[cond], prefix, batch_size=args.batch_size,
                          bootstrap=args.bootstrap, seed=args.seed)
                if meta["variant"] != variant or meta["training_seed"] != training_seed:
                    raise RuntimeError(f"Checkpoint variant/seed disagrees with filename: {ckpt}")
                completed += 1
    expected = len(args.seeds) * len(args.variants) * len(selected)
    if completed != expected:
        raise RuntimeError(f"Only {completed}/{expected} evaluations completed")
    print(f"SUCCESS: {completed}/{expected} evaluations completed", flush=True)


if __name__ == "__main__":
    main()
