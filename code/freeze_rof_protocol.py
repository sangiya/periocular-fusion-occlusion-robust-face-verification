"""Freeze deterministic ROF verification pairs for all model variants."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path


def row_key(row: dict[str, str]) -> tuple[str, str]:
    return (row.get("path", ""), row.get("face_path", ""))


def image_id(row: dict[str, str]) -> str:
    value = "|".join([
        row.get("identity", ""), row.get("condition", ""),
        row.get("face_path", ""), row.get("peri_path", ""),
    ])
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:20]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--max-impostors-per-probe", type=int, default=100)
    args = p.parse_args()
    if args.max_impostors_per_probe < 1:
        raise ValueError("--max-impostors-per-probe must be >= 1")

    with open(args.manifest, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    required = {"face_path", "peri_path", "identity", "condition", "split"}
    missing = required - set(rows[0].keys() if rows else [])
    if missing:
        raise ValueError(f"Manifest missing columns: {sorted(missing)}")

    split_ids = defaultdict(set)
    for row in rows:
        if row["split"] in {"train", "val", "test"}:
            split_ids[row["split"]].add(row["identity"])
    if ((split_ids["train"] & split_ids["val"]) or
            (split_ids["train"] & split_ids["test"]) or
            (split_ids["val"] & split_ids["test"])):
        raise RuntimeError("Identity leakage detected between splits")

    test = [r for r in rows if r["split"] == "test"]
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    metadata = {"manifest": str(Path(args.manifest).resolve()), "conditions": {}}

    fields = [
        "pair_id", "condition", "label", "probe_identity", "enroll_identity",
        "probe_image_id", "probe_face_path", "probe_peri_path",
        "probe_face_conf", "probe_peri_conf", "probe_blur", "probe_visible_ratio",
        "enroll_image_id", "enroll_face_path", "enroll_peri_path",
        "enroll_face_conf", "enroll_peri_conf", "enroll_blur", "enroll_visible_ratio",
    ]

    for condition in ("masked", "sunglasses"):
        grouped = defaultdict(list)
        for row in test:
            if row["condition"] in {"neutral", condition}:
                grouped[row["identity"]].append(row)

        eligible = {}
        for identity, identity_rows in grouped.items():
            neutral = sorted((r for r in identity_rows if r["condition"] == "neutral"), key=row_key)
            probes = sorted((r for r in identity_rows if r["condition"] == condition), key=row_key)
            if neutral and probes:
                eligible[identity] = {"enroll": neutral[0], "probes": probes}
        identities = sorted(eligible)
        if len(identities) < 2:
            raise RuntimeError(f"Too few eligible identities for {condition}")

        pairs = []
        counter = 0
        for identity in identities:
            for probe in eligible[identity]["probes"]:
                enroll_ids = [identity] + [x for x in identities if x != identity][:args.max_impostors_per_probe]
                for enroll_identity in enroll_ids:
                    enroll = eligible[enroll_identity]["enroll"]
                    pair_id = f"{condition}-{counter:08d}"
                    counter += 1
                    pairs.append({
                        "pair_id": pair_id, "condition": condition,
                        "label": int(enroll_identity == identity),
                        "probe_identity": identity, "enroll_identity": enroll_identity,
                        "probe_image_id": image_id(probe),
                        "probe_face_path": probe["face_path"], "probe_peri_path": probe["peri_path"],
                        "probe_face_conf": probe.get("face_conf", ""), "probe_peri_conf": probe.get("peri_conf", ""),
                        "probe_blur": probe.get("blur", ""), "probe_visible_ratio": probe.get("visible_ratio", ""),
                        "enroll_image_id": image_id(enroll),
                        "enroll_face_path": enroll["face_path"], "enroll_peri_path": enroll["peri_path"],
                        "enroll_face_conf": enroll.get("face_conf", ""), "enroll_peri_conf": enroll.get("peri_conf", ""),
                        "enroll_blur": enroll.get("blur", ""), "enroll_visible_ratio": enroll.get("visible_ratio", ""),
                    })

        output = out_dir / f"rof_{condition}_pairs.csv"
        with output.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(pairs)
        labels = [int(x["label"]) for x in pairs]
        metadata["conditions"][condition] = {
            "file": output.name, "eligible_identities": len(identities),
            "pairs": len(pairs), "genuine": sum(labels), "impostor": len(labels) - sum(labels),
            "far_resolution": 1.0 / (len(labels) - sum(labels)),
        }

    with (out_dir / "rof_protocol_metadata.json").open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
