import pandas as pd
import re
from pathlib import Path
from sklearn.model_selection import train_test_split

# ============================================================
# Configuration
# ============================================================

ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / "work" / "rof_manifest_raw.csv"
OUTPUT = ROOT / "work" / "rof_manifest_person_disjoint.csv"

SEED = 42
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

# ============================================================
# Load manifest
# ============================================================

print("=" * 70)
print("Creating person-disjoint train / validation / test split")
print("=" * 70)

df = pd.read_csv(INPUT)

print(f"Input manifest : {INPUT}")
print(f"Total rows     : {len(df):,}")
print(f"Columns        : {list(df.columns)}")

# ============================================================
# Validate required columns
# ============================================================

required_columns = {"identity"}

missing = required_columns - set(df.columns)

if missing:
    raise ValueError(
        f"Missing required columns: {sorted(missing)}"
    )

# ============================================================
# Create normalized person identity
# ============================================================
#
# Examples:
#   person001
#   person001_wearing_mask
#   person001_wearing_sunglasses
#
# All conditions belonging to the same person must remain
# in the same split.
# ============================================================

def normalize_person_id(identity):
    identity = str(identity).strip()

    return re.sub(
        r"_wearing_(mask|sunglasses)$",
        "",
        identity,
        flags=re.IGNORECASE
    )


df["person_id"] = df["identity"].apply(normalize_person_id)

# Keep original identity for traceability
df["source_identity"] = df["identity"]

# ============================================================
# Validate person IDs
# ============================================================

if df["person_id"].isna().any():
    raise ValueError("Found missing person_id values.")

if (df["person_id"].astype(str).str.strip() == "").any():
    raise ValueError("Found empty person_id values.")

persons = sorted(df["person_id"].unique())

print(f"Unique persons  : {len(persons):,}")

# ============================================================
# Person-level split
# ============================================================

train_persons, temp_persons = train_test_split(
    persons,
    test_size=(VAL_RATIO + TEST_RATIO),
    random_state=SEED,
    shuffle=True
)

# Split remaining persons equally into validation/test
relative_test_ratio = TEST_RATIO / (VAL_RATIO + TEST_RATIO)

val_persons, test_persons = train_test_split(
    temp_persons,
    test_size=relative_test_ratio,
    random_state=SEED,
    shuffle=True
)

train_persons = set(train_persons)
val_persons = set(val_persons)
test_persons = set(test_persons)

# ============================================================
# Verify zero person overlap
# ============================================================

train_val_overlap = train_persons & val_persons
train_test_overlap = train_persons & test_persons
val_test_overlap = val_persons & test_persons

if train_val_overlap:
    raise RuntimeError(
        f"Train/validation person overlap: {train_val_overlap}"
    )

if train_test_overlap:
    raise RuntimeError(
        f"Train/test person overlap: {train_test_overlap}"
    )

if val_test_overlap:
    raise RuntimeError(
        f"Validation/test person overlap: {val_test_overlap}"
    )

# ============================================================
# Assign split
# ============================================================

def assign_split(person_id):
    if person_id in train_persons:
        return "train"

    if person_id in val_persons:
        return "val"

    if person_id in test_persons:
        return "test"

    raise ValueError(f"Unknown person_id: {person_id}")


df["split"] = df["person_id"].apply(assign_split)

# ============================================================
# Save
# ============================================================

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

df.to_csv(
    OUTPUT,
    index=False
)

# ============================================================
# Report
# ============================================================

print()
print("=" * 70)
print("SPLIT SUMMARY")
print("=" * 70)

for split in ["train", "val", "test"]:
    subset = df[df["split"] == split]

    print(
        f"{split:5s} | "
        f"rows: {len(subset):8,} | "
        f"persons: {subset['person_id'].nunique():6,}"
    )

print()
print("Person overlap checks:")
print(f"  Train & Val  : {len(train_val_overlap)}")
print(f"  Train & Test : {len(train_test_overlap)}")
print(f"  Val   & Test : {len(val_test_overlap)}")

print()
print(f"Saved to:")
print(f"  {OUTPUT}")

print()
print("SUCCESS: Person-disjoint split created.")