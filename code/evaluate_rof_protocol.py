"""Evaluate one checkpoint on a frozen ROF pair CSV and save raw scores."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from pathlib import Path

import numpy as np
from PIL import Image
import torch
from torchvision.transforms import v2

from model import VerificationModel
from verification import summarize


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


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--pairs", required=True)
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument("--bootstrap", type=int, default=1000)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out-prefix", required=True)
    args = p.parse_args()
    random.seed(args.seed); np.random.seed(args.seed); torch.manual_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    with open(args.pairs, newline="", encoding="utf-8") as f:
        pairs = list(csv.DictReader(f))
    if not pairs:
        raise ValueError("Pair CSV is empty")

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

    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
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
    for start in range(0, len(ids), args.batch_size):
        batch_ids = ids[start:start + args.batch_size]
        def load(path: str) -> torch.Tensor:
            with Image.open(path) as image:
                return transform(image.convert("RGB"))
        face = torch.stack([load(images[i]["face_path"]) for i in batch_ids]).to(device)
        peri = torch.stack([load(images[i]["peri_path"]) for i in batch_ids]).to(device)
        quality = torch.tensor([images[i]["quality"] for i in batch_ids], dtype=torch.float32, device=device)
        with torch.inference_mode():
            z = torch.nn.functional.normalize(model(face, peri, quality), dim=1).cpu().numpy()
        embeddings.update({iid: z[j].astype(np.float32) for j, iid in enumerate(batch_ids)})
        print(f"embedded {min(start + args.batch_size, len(ids))}/{len(ids)}", flush=True)

    scores = np.asarray([float(np.dot(embeddings[p["probe_image_id"]], embeddings[p["enroll_image_id"]]))
                         for p in pairs], dtype=np.float64)
    labels = np.asarray([int(p["label"]) for p in pairs], dtype=np.int64)
    subjects = np.asarray([p["probe_identity"] for p in pairs])
    metrics = summarize(scores, labels)
    metrics["identity_bootstrap_ci"] = identity_bootstrap(scores, labels, subjects, args.bootstrap, args.seed)
    metrics.update({
        "variant": variant, "condition": pairs[0]["condition"], "device": str(device),
        "eligible_identities": int(len(np.unique(subjects))),
        "far_resolution": float(1.0 / np.sum(labels == 0)),
        "tar_far_1e-3_supported": bool(np.sum(labels == 0) >= 1000),
        "checkpoint": str(Path(args.checkpoint).resolve()), "checkpoint_sha256": sha256(args.checkpoint),
        "pairs": str(Path(args.pairs).resolve()), "pairs_sha256": sha256(args.pairs),
    })

    prefix = Path(args.out_prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    raw_path = prefix.with_name(prefix.name + "_raw_scores.csv")
    metric_path = prefix.with_name(prefix.name + "_metrics.json")
    raw_fields = ["pair_id", "condition", "label", "probe_identity", "enroll_identity", "score", "variant"]
    with raw_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=raw_fields); writer.writeheader()
        for pair, score in zip(pairs, scores):
            writer.writerow({**{k: pair[k] for k in raw_fields if k not in {"score", "variant"}},
                             "score": f"{score:.10f}", "variant": variant})
    with metric_path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(json.dumps(metrics, indent=2))
    print(f"Saved {raw_path}\nSaved {metric_path}")


if __name__ == "__main__":
    main()
