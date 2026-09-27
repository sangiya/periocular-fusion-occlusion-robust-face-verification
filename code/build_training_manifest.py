"""Build the final complete-case training manifest from the person-disjoint crop manifest.

This step is the bridge between periocular crop generation and training. It keeps
only rows that are genuinely usable, i.e.:

  * the source face image exists on disk,
  * the generated periocular crop exists on disk,
  * the condition label is one of the three used in the study.

It then rewrites ``identity`` to ``person_id`` so that the neutral, masked and
sunglasses variants of the same person collapse into a single training class.
Without this rewrite the model would see the same person as three unrelated
identities, which defeats the person-disjoint protocol.

The output is the manifest consumed by ``run_seed_sweep.py`` and ``train.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

INPUT = ROOT / "work" / "crop_manifest_person_disjoint.csv"
OUTPUT = ROOT / "work" / "crop_manifest_training_person_disjoint.csv"

VALID_CONDITIONS = ["neutral", "sunglasses", "masked"]
SPLITS = ["train", "val", "test"]


def main() -> None:
    if not INPUT.is_file():
        raise FileNotFoundError(
            f"\nInput manifest not found:\n  {INPUT}\n\n"
            "Generate the periocular crops first, for example:\n"
            "  python .\\code\\generate_periocular_mediapipe.py `\n"
            "    --input .\\work\\rof_manifest_crop_input.csv `\n"
            "    --output .\\work\\crop_manifest_person_disjoint.csv `\n"
            "    --crop-dir .\\data\\ROF\\peri `\n"
            "    --margin 0.20"
        )

    df = pd.read_csv(INPUT)

    print("=" * 70)
    print("BUILD COMPLETE-CASE TRAINING MANIFEST")
    print("=" * 70)
    print(f"Input : {INPUT}")
    print(f"Rows  : {len(df):,}")

    required = {"face_path", "peri_path", "condition", "split", "person_id"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    face_valid = df["face_path"].map(
        lambda x: isinstance(x, str) and Path(x).is_file()
    )
    peri_valid = df["peri_path"].map(
        lambda x: isinstance(x, str) and Path(x).is_file()
    )
    condition_valid = df["condition"].isin(VALID_CONDITIONS)

    keep = face_valid & peri_valid & condition_valid
    train_df = df[keep].copy()

    # Collapse the per-condition identities of one person into a single class.
    train_df["identity"] = train_df["person_id"]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    train_df.to_csv(OUTPUT, index=False)

    print()
    print(f"Face images present   : {int(face_valid.sum()):,}")
    print(f"Periocular crops present: {int(peri_valid.sum()):,}")
    print(f"Known conditions      : {int(condition_valid.sum()):,}")
    print(f"Complete cases kept   : {len(train_df):,}")
    print(f"Rows removed          : {len(df) - len(train_df):,}")
    print(f"Output                : {OUTPUT}")

    print()
    print("Split counts:")
    print(train_df["split"].value_counts().sort_index().to_string())

    print()
    print("Condition counts:")
    print(pd.crosstab(train_df["split"], train_df["condition"]).to_string())

    person_sets = {
        s: set(train_df.loc[train_df["split"] == s, "person_id"])
        for s in SPLITS
    }

    print()
    print("Person counts:")
    for s in SPLITS:
        print(f"  {s:5s} : {len(person_sets[s]):,}")

    train_val = person_sets["train"] & person_sets["val"]
    train_test = person_sets["train"] & person_sets["test"]
    val_test = person_sets["val"] & person_sets["test"]

    print()
    print("Person overlap:")
    print(f"  Train & Val  : {len(train_val)}")
    print(f"  Train & Test : {len(train_test)}")
    print(f"  Val   & Test : {len(val_test)}")

    if train_val or train_test or val_test:
        raise RuntimeError("Person leakage detected in the training manifest.")

    print()
    print("PERSON-DISJOINT: OK")
    print("SUCCESS: complete-case training manifest created.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
