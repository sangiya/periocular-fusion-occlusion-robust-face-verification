"""Create a manifest and identity-disjoint train/val/test split.

Expected image layout (flexible): root/condition/identity/image.jpg or
root/identity/condition/image.jpg. Use --condition-map when names differ.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import random
from pathlib import Path

EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
CONDITION_NAMES = {"neutral", "masked", "mask", "sunglasses", "sun", "occluded", "occlusion"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def infer_parts(path: Path, root: Path) -> tuple[str, str]:
    rel = path.relative_to(root)
    parts = [p.lower() for p in rel.parts[:-1]]
    condition = next((p for p in parts if p in CONDITION_NAMES), "unknown")
    identity = next((p for p in reversed(parts) if p not in CONDITION_NAMES), rel.parts[-2] if len(rel.parts) > 1 else "unknown")
    if condition == "mask": condition = "masked"
    if condition == "sun": condition = "sunglasses"
    return identity, condition


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, type=Path)
    ap.add_argument("--out", default=Path("manifest.csv"), type=Path)
    ap.add_argument("--seed", default=42, type=int)
    ap.add_argument("--train", default=.70, type=float)
    ap.add_argument("--val", default=.15, type=float)
    args = ap.parse_args()
    files = sorted(p for p in args.root.rglob("*") if p.suffix.lower() in EXTS)
    if not files:
        raise SystemExit("No images found")
    rows = []
    for p in files:
        identity, condition = infer_parts(p, args.root)
        rows.append({"path": str(p.resolve()), "identity": identity, "condition": condition, "sha256": sha256(p)})
    identities = sorted({r["identity"] for r in rows})
    rng = random.Random(args.seed)
    rng.shuffle(identities)
    n_train = int(len(identities) * args.train)
    n_val = int(len(identities) * args.val)
    split_by_id = {x: "train" for x in identities[:n_train]}
    split_by_id.update({x: "val" for x in identities[n_train:n_train+n_val]})
    split_by_id.update({x: "test" for x in identities[n_train+n_val:]})
    for r in rows: r["split"] = split_by_id[r["identity"]]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["path", "identity", "condition", "split", "sha256"])
        writer.writeheader(); writer.writerows(rows)
    print(f"images={len(rows)} identities={len(identities)}")
    print({s: len({r['identity'] for r in rows if r['split'] == s}) for s in ['train','val','test']})
    print("Wrote", args.out)

if __name__ == "__main__": main()
