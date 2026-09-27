"""Rewrite absolute dataset/crop paths in a manifest to a new project root.

Every manifest in this bundle was produced on the machine that ran the study, so
its path columns contain absolute paths such as::

    D:\\...\\data_plan\\data\\ROF\\images\\neutral\\alice\\000001.jpg
    D:\\...\\data_plan\\work\\periocular_person_disjoint\\peri_000000.jpg

Those paths do not exist on another machine. This tool rewrites them in place
(or to a new file) so the manifest points at a local checkout, for example::

    D:\\mywork\\data\\ROF\\images\\neutral\\alice\\000001.jpg
    D:\\mywork\\work\\periocular_person_disjoint\\peri_000000.jpg

Only the known original root is replaced; everything after ``data\\`` or
``work\\`` is preserved byte-for-byte, so the relative structure of every dataset
is retained.

It can also report coverage: how many referenced files actually exist after
remapping.

Typical use (dry run first):

    python code/remap_manifest_paths.py --root . --in-place --dry-run
    python code/remap_manifest_paths.py --root . --in-place
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

# Absolute prefixes used by the machines that produced the shipped manifests.
# The first is the local Windows checkout; the second is the Kaggle notebook
# input mount, which still appears in the raw MFR2 official pair file.
OLD_ROOTS = (
    r"D:\Sangiya\NIV-2026\Thesis\Claude\2026- Latest Research\manus\data_plan",
    "/kaggle/input/datasets/sangiyaparara/research-dataset/data_plan",
)

# Any column whose name contains "path" is treated as holding a filesystem
# path. This covers the plain columns (path, face_path, peri_path, path1,
# path2) as well as the numbered and role-prefixed variants used by the
# cross-dataset protocol files (face_path1, probe_peri_path, enroll_face_path).
PATH_COLUMN_HINT = "path"

# Old absolute root, as it appears in the files (single backslashes in memory).
def rewrite(value: str, new_root: str, relative: bool = False) -> tuple[str, bool]:
    """Replace any known old root in *value*. Return (new_value, changed).

    With ``relative=True`` the known root is simply stripped, yielding a path
    relative to the project root (forward slashes), which is what makes the
    bundle work on Windows, Linux, and macOS without any further editing.
    """
    if not isinstance(value, str):
        return value, False
    for old in OLD_ROOTS:
        if old in value:
            tail = value[len(old):].lstrip("\\/")
            tail = tail.replace("\\", "/")
            if relative:
                return tail, True
            prefix = new_root.replace("/", "\\").rstrip("\\")
            return f"{prefix}\\{tail}", True
    return value, False


def count_old_roots(text: str) -> int:
    return sum(text.count(old) for old in OLD_ROOTS)


def remap_csv(path: Path, new_root: str, in_place: bool, dry_run: bool, relative: bool = False) -> dict:
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    present = [c for c in fieldnames if PATH_COLUMN_HINT in c.lower()]
    changed_cells = 0
    missing_after: Counter = Counter()

    for row in rows:
        for col in present:
            new_value, changed = rewrite(row.get(col, ""), new_root, relative)
            if changed:
                changed_cells += 1
                row[col] = new_value
            resolved = row.get(col, "")
            if resolved and not Path(resolved).is_file():
                missing_after[col] += 1

    if changed_cells and in_place and not dry_run:
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    return {
        "file": path.name,
        "rows": len(rows),
        "path_columns": present,
        "rewritten_cells": changed_cells,
        "missing_after_remap": dict(missing_after),
    }


def remap_json(path: Path, new_root: str, in_place: bool, dry_run: bool, relative: bool = False) -> dict:
    raw = path.read_text(encoding="utf-8")
    # JSON escapes backslashes, so a stored Windows path appears as "D:\\Sangiya\\...".
    # Normalise the escaped form to the plain form for matching, then map back.
    escaped = {old.replace("\\", "\\\\"): old for old in OLD_ROOTS}
    variants: list[tuple[str, str | None]] = []
    for esc, plain in escaped.items():
        variants.append((plain, None))            # plain, for CSV-style content
        variants.append((esc, plain))             # JSON-escaped, for .json content
    count = sum(raw.count(v) for v, _ in variants)
    if count and in_place and not dry_run:
        for old in OLD_ROOTS:
            if relative:
                raw = raw.replace(old, "")
                raw = raw.replace(old.replace("\\", "\\\\"), "")
            else:
                target = new_root.replace("/", "\\")
                raw = raw.replace(old, target)
                raw = raw.replace(old.replace("\\", "\\\\"), target.replace("\\", "\\\\"))
        path.write_text(raw, encoding="utf-8")
    return {"file": path.name, "rewritten_cells": count}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True, type=Path,
                    help="Local project root that replaces the original absolute root, "
                         "e.g. the folder containing data\\ and work\\")
    ap.add_argument("--manifests", type=Path, default=None,
                    help="Folder of manifests to remap (default: <root>/manifests)")
    ap.add_argument("--in-place", action="store_true", help="Write changes back to the files")
    ap.add_argument("--dry-run", action="store_true", help="Report only, change nothing")
    ap.add_argument("--relative", action="store_true",
                    help="Emit paths relative to the project root (forward slashes) instead "
                         "of absolute paths. Use this when publishing the bundle so it works "
                         "on any operating system without editing.")
    args = ap.parse_args()

    new_root = str(args.root.resolve())
    manifests = args.manifests or (args.root / "manifests")

    if not manifests.is_dir():
        print(f"ERROR: manifests folder not found: {manifests}", file=sys.stderr)
        return 1

    print("=" * 70)
    print("REMAP MANIFEST PATHS")
    print("=" * 70)
    print(f"Old roots :")
    for old in OLD_ROOTS:
        print(f"           {old}")
    print(f"New root : {new_root}")
    print(f"Folder   : {manifests}")
    print(f"Mode     : {'dry run' if args.dry_run else ('in place' if args.in_place else 'report only')}"
          f"{', relative paths' if args.relative else ''}")
    print()
    if args.relative:
        print("Paths will be stored relative to the bundle root and separated by '/'.")
        print("Run everything from the bundle root so they resolve.")
        print()

    targets = sorted(list(manifests.glob("*.csv")) + list(manifests.glob("*.json")))
    if not targets:
        print("ERROR: no manifests found.", file=sys.stderr)
        return 1

    total_rewritten = 0
    total_missing = 0

    for path in targets:
        report = remap_csv(path, new_root, args.in_place, args.dry_run, args.relative) \
            if path.suffix == ".csv" \
            else remap_json(path, new_root, args.in_place, args.dry_run, args.relative)

        total_rewritten += report["rewritten_cells"]
        missing = report.get("missing_after_remap") or {}
        total_missing += sum(missing.values())

        flag = "OK " if report["rewritten_cells"] else "-- "
        print(f"[{flag}] {report['file']:<46} rewritten={report['rewritten_cells']:>6}")
        if report.get("path_columns"):
            print(f"        columns: {', '.join(report['path_columns'])}")
        if missing:
            detail = ", ".join(f"{k}={v}" for k, v in sorted(missing.items()))
            print(f"        not found on disk after remap: {detail}")

    print()
    print(f"Total cells rewritten : {total_rewritten:,}")
    print(f"Total refs not found  : {total_missing:,}")

    if total_missing:
        print()
        print("A non-zero 'not found' count is expected before you generate the")
        print("periocular crops, because the crop directories are not shipped.")
        print("Run the crop stage (steps 4-5 of WINDOWS_REPRODUCTION_GUIDE.md) first.")

    if args.dry_run and total_rewritten:
        print()
        print("This was a dry run. Re-run without --dry-run to apply.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
