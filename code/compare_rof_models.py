"""Paired, probe-identity bootstrap comparisons from V2 raw score files."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score
from verification import eer


def load(path: str) -> dict[str, dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return {row["pair_id"]: row for row in rows}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--reference", required=True)
    p.add_argument("--candidate", required=True)
    p.add_argument("--bootstrap", type=int, default=5000)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    ref, cand = load(args.reference), load(args.candidate)
    if set(ref) != set(cand):
        raise RuntimeError("Raw-score files do not contain the same frozen pair IDs")
    ids = sorted(ref)
    labels = np.asarray([int(ref[i]["label"]) for i in ids])
    subjects = np.asarray([ref[i]["probe_identity"] for i in ids])
    a = np.asarray([float(ref[i]["score"]) for i in ids])
    b = np.asarray([float(cand[i]["score"]) for i in ids])
    unique = np.unique(subjects); rng = np.random.default_rng(args.seed)
    auc_delta, eer_delta = [], []
    for _ in range(args.bootstrap):
        sampled = rng.choice(unique, len(unique), replace=True)
        idx = np.concatenate([np.where(subjects == s)[0] for s in sampled])
        if len(np.unique(labels[idx])) < 2: continue
        auc_delta.append(roc_auc_score(labels[idx], b[idx]) - roc_auc_score(labels[idx], a[idx]))
        eer_delta.append(eer(b[idx], labels[idx])[0] - eer(a[idx], labels[idx])[0])
    result = {
        "reference": next(iter(ref.values()))["variant"],
        "candidate": next(iter(cand.values()))["variant"],
        "condition": next(iter(ref.values()))["condition"],
        "auc_delta_candidate_minus_reference": float(roc_auc_score(labels, b) - roc_auc_score(labels, a)),
        "auc_delta_95_ci": [float(np.percentile(auc_delta, 2.5)), float(np.percentile(auc_delta, 97.5))],
        "eer_delta_candidate_minus_reference": float(eer(b, labels)[0] - eer(a, labels)[0]),
        "eer_delta_95_ci": [float(np.percentile(eer_delta, 2.5)), float(np.percentile(eer_delta, 97.5))],
        "paired_probe_identity_bootstrap_iterations": args.bootstrap,
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f: json.dump(result, f, indent=2)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
