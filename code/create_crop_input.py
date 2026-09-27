from pathlib import Path
import pandas as pd


# ============================================================
# Configuration
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_MANIFEST = BASE_DIR / "work" / "rof_manifest_person_disjoint.csv"
OUTPUT_MANIFEST = BASE_DIR / "work" / "rof_manifest_crop_input.csv"


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 80)
    print("ROF - CREATE CROP INPUT MANIFEST")
    print("=" * 80)

    # --------------------------------------------------------
    # Check input
    # --------------------------------------------------------

    if not INPUT_MANIFEST.exists():
        raise FileNotFoundError(
            f"\nInput manifest not found:\n{INPUT_MANIFEST}\n\n"
            "Create the person-disjoint manifest first using:\n"
            "python .\\work\\create_person_disjoint_split.py"
        )

    # --------------------------------------------------------
    # Load person-disjoint manifest
    # --------------------------------------------------------

    print("\nInput:")
    print(f"  {INPUT_MANIFEST}")

    df = pd.read_csv(INPUT_MANIFEST)

    print(f"\nRows loaded: {len(df):,}")

    print("Columns:")
    for column in df.columns:
        print(f"  - {column}")

    # --------------------------------------------------------
    # Required columns
    # --------------------------------------------------------

    required_columns = {
        "identity",
        "person_id",
        "source_identity",
        "split",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            "\nMissing required columns:\n"
            + "\n".join(f"  - {x}" for x in sorted(missing))
        )

    # --------------------------------------------------------
    # Determine face path column
    # --------------------------------------------------------

    if "face_path" in df.columns:
        source_path_column = "face_path"

    elif "path" in df.columns:
        source_path_column = "path"

    else:
        raise ValueError(
            "\nCould not find an image path column.\n"
            "Expected either 'face_path' or 'path'."
        )

    print(f"\nSource image column: {source_path_column}")

    # --------------------------------------------------------
    # Create standardized face_path
    # --------------------------------------------------------

    if source_path_column == "path":
        df["face_path"] = df["path"].astype(str)
    else:
        df["face_path"] = df["face_path"].astype(str)

    # --------------------------------------------------------
    # Clean values
    # --------------------------------------------------------

    df["identity"] = df["identity"].astype(str).str.strip()
    df["person_id"] = df["person_id"].astype(str).str.strip()
    df["source_identity"] = (
        df["source_identity"].astype(str).str.strip()
    )
    df["split"] = (
        df["split"].astype(str).str.strip().str.lower()
    )

    # --------------------------------------------------------
    # Validate splits
    # --------------------------------------------------------

    valid_splits = {"train", "val", "test"}

    invalid_splits = set(df["split"].unique()) - valid_splits

    if invalid_splits:
        raise ValueError(
            f"\nInvalid split values found: {sorted(invalid_splits)}\n"
            f"Expected only: {sorted(valid_splits)}"
        )

    # --------------------------------------------------------
    # Validate required values
    # --------------------------------------------------------

    for column in [
        "identity",
        "person_id",
        "source_identity",
        "face_path",
        "split",
    ]:

        missing_count = df[column].isna().sum()

        if missing_count > 0:
            raise ValueError(
                f"\nColumn '{column}' contains "
                f"{missing_count:,} missing values."
            )

        empty_count = (
            df[column]
            .astype(str)
            .str.strip()
            .eq("")
            .sum()
        )

        if empty_count > 0:
            raise ValueError(
                f"\nColumn '{column}' contains "
                f"{empty_count:,} empty values."
            )

    # --------------------------------------------------------
    # IMPORTANT:
    # Verify that each person exists in only ONE split
    # --------------------------------------------------------

    person_split_counts = (
        df.groupby("person_id")["split"]
        .nunique()
    )

    leaking_persons = person_split_counts[
        person_split_counts > 1
    ]

    if len(leaking_persons) > 0:

        print("\nERROR: Person leakage detected!")

        print(leaking_persons.head(20))

        raise RuntimeError(
            f"\n{len(leaking_persons):,} persons occur "
            "in multiple splits."
        )

    print("\nPerson-disjointness check: PASSED")

    # --------------------------------------------------------
    # Check train / validation / test overlap
    # --------------------------------------------------------

    train_people = set(
        df.loc[df["split"] == "train", "person_id"]
    )

    val_people = set(
        df.loc[df["split"] == "val", "person_id"]
    )

    test_people = set(
        df.loc[df["split"] == "test", "person_id"]
    )

    train_val = train_people & val_people
    train_test = train_people & test_people
    val_test = val_people & test_people

    if train_val or train_test or val_test:

        raise RuntimeError(
            "\nPerson overlap detected:\n"
            f"Train ∩ Val = {len(train_val)}\n"
            f"Train ∩ Test = {len(train_test)}\n"
            f"Val ∩ Test = {len(val_test)}"
        )

    print("Train / Val / Test overlap: 0")

    # --------------------------------------------------------
    # Validate source image paths
    # --------------------------------------------------------

    print("\nChecking source image paths...")

    path_series = df["face_path"].astype(str)

    existing_mask = path_series.apply(
        lambda x: Path(x).exists()
    )

    existing_count = int(existing_mask.sum())
    missing_count = int((~existing_mask).sum())

    print(f"Existing images : {existing_count:,}")
    print(f"Missing images  : {missing_count:,}")

    if missing_count > 0:

        print("\nWARNING: Missing image examples:")

        for path in path_series[~existing_mask].head(20):
            print(f"  {path}")

        raise FileNotFoundError(
            f"\n{missing_count:,} image paths do not exist."
        )

    print("Source image path check: PASSED")

    # --------------------------------------------------------
    # Preserve useful columns
    # --------------------------------------------------------

    preferred_columns = [
        "face_path",
        "identity",
        "condition",
        "split",
        "person_id",
        "source_identity",
        "sha256",
    ]

    final_columns = []

    for column in preferred_columns:

        if (
            column in df.columns
            and column not in final_columns
        ):
            final_columns.append(column)

    # Preserve any remaining columns as well.

    for column in df.columns:

        if column not in final_columns:
            final_columns.append(column)

    df = df[final_columns]

    # --------------------------------------------------------
    # Remove exact duplicate rows
    # --------------------------------------------------------

    before_duplicates = len(df)

    df = (
        df
        .drop_duplicates()
        .reset_index(drop=True)
    )

    removed_duplicates = (
        before_duplicates - len(df)
    )

    print(
        f"\nExact duplicate rows removed: "
        f"{removed_duplicates:,}"
    )

    # --------------------------------------------------------
    # Final ordering
    # --------------------------------------------------------

    sort_columns = [
        column
        for column in [
            "split",
            "person_id",
            "condition",
            "face_path",
        ]
        if column in df.columns
    ]

    if sort_columns:

        df = (
            df
            .sort_values(
                sort_columns,
                kind="stable"
            )
            .reset_index(drop=True)
        )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    OUTPUT_MANIFEST.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_MANIFEST,
        index=False
    )

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    print("\n" + "=" * 80)
    print("CROP INPUT MANIFEST SUMMARY")
    print("=" * 80)

    print("\nOutput:")
    print(f"  {OUTPUT_MANIFEST}")

    print("\nTotal rows:")
    print(f"  {len(df):,}")

    print("\nSplit summary:")

    for split in ["train", "val", "test"]:

        subset = df[df["split"] == split]

        rows = len(subset)
        persons = subset["person_id"].nunique()

        print(
            f"  {split:5s} "
            f"rows={rows:8,} "
            f"persons={persons:6,}"
        )

    # --------------------------------------------------------
    # Condition summary
    # --------------------------------------------------------

    if "condition" in df.columns:

        print("\nCondition summary:")

        condition_summary = (
            df.groupby(
                ["split", "condition"],
                dropna=False
            )
            .size()
            .reset_index(name="rows")
        )

        for _, row in condition_summary.iterrows():

            print(
                f"  {str(row['split']):5s} "
                f"{str(row['condition']):20s} "
                f"{int(row['rows']):8,}"
            )

    # --------------------------------------------------------
    # Person overlap final verification
    # --------------------------------------------------------

    print("\nFinal person-overlap verification:")

    train_people = set(
        df.loc[df["split"] == "train", "person_id"]
    )

    val_people = set(
        df.loc[df["split"] == "val", "person_id"]
    )

    test_people = set(
        df.loc[df["split"] == "test", "person_id"]
    )

    print(
        f"  Train ∩ Val  : "
        f"{len(train_people & val_people)}"
    )

    print(
        f"  Train ∩ Test : "
        f"{len(train_people & test_people)}"
    )

    print(
        f"  Val ∩ Test   : "
        f"{len(val_people & test_people)}"
    )

    print("\n" + "=" * 80)
    print("SUCCESS")
    print("=" * 80)

    print(
        "\nThe person-disjoint manifest is now ready "
        "for the periocular crop generation stage."
    )

    print(
        f"\nNext file:\n"
        f"  {OUTPUT_MANIFEST}"
    )


if __name__ == "__main__":
    main()