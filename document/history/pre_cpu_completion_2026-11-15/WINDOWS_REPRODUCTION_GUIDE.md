# Reproduction and PDF build guide — revised 2 November 2026

A GPU is optional. Historical result records and the corrected three-seed MFR2 inference use CPU. A failed import or a run that skips checkpoints is not successful evaluation.

## Environment

Use Python 3.11 and install configs/requirements-used.txt into a dedicated virtual environment. These are historical recorded package pins; they are not a complete transitive, hash-locked environment.

    py -3.11 -m venv .venv
    .venv/Scripts/Activate.ps1
    python -m pip install -r configs/requirements-used.txt

For the recorded CPU wheel build, use the matching official CPU wheel index where necessary:

    python -m pip install torch==2.14.0 torchvision==0.29.0 --index-url https://download.pytorch.org/whl/cpu

The repair used the existing parent data_plan/.venv/Scripts/python.exe, which includes torch 2.14.0+cpu, transformers 5.17.0, and peft 0.20.0. Running an unrelated global Python can produce ModuleNotFoundError even when the project environment is valid.

## Data and models

The dataset root must contain the relative data/ and work/ paths stored in the manifests. The checkpoints are not redistributed. For the local repair, the dataset root was the parent data_plan directory, and checkpoint-root was data_plan/work/seed_sweep/checkpoints.

Use the frozen manifests for exact archived pair construction. The historical raw index contained a resource image outside data/ROF/images; re-indexing only images/ and reseeding is not guaranteed to recreate the archived split. Do not claim byte-identical split regeneration without comparing person assignments.

Generate audited inputs:

    python code/prepare_integrity_protocols.py --root . --dataset-root D:/path/to/data_plan

No original image is deleted or relabeled. The script writes cleaned CSVs and explicit exclusion reasons under manifests/cleaned/. New clean-trained results require actual training:

    python code/train_clean_seed_sweep.py --root . --dataset-root D:/path/to/data_plan --dry-run
    python code/train_clean_seed_sweep.py --root . --dataset-root D:/path/to/data_plan

New checkpoints are isolated by clean-manifest hash. The trainer checks content uniqueness and label split separation. Historical training logs/checkpoints are not represented as newly trained clean models.

## Corrected inference

    python code/evaluate_all_cross_dataset_fixed.py --root . --dataset-root D:/path/to/data_plan --checkpoint-root D:/path/to/checkpoints --output-dir results/new_mfr2_check --protocol mfr2 --variants gated_fusion --seeds 7 42 123 --batch-size 8 --bootstrap 1000

All selected checkpoints and pair lists must exist. A new output directory is required unless explicit --overwrite is used. The default pair lookup tries the historical working location, then the shipped manifests/. The final success line reports completed/expected evaluations. Do not infer success from an empty output directory.

## Score sensitivities and assets

    python code/build_score_sensitivities.py
    python code/regenerate_publication_assets.py
    python code/verify_results.py --report document/VERIFICATION_REPORT.json

Sensitivities filter already archived predictions with the same pair-ID selection for each model; they do not retrain models. MFR2 gated sensitivity uses corrected inference. Their point estimates and seed SDs are descriptive, with no newly computed bootstrap CIs.

The strict verifier compares the manuscript's corrected MFR2 row with results/corrections/mfr2_quality_v2/, and other main performance rows with archived results. It verifies both old and new score files.

## Compile both PDFs

Tectonic is a portable compiler: a full system LaTeX installation is not required. The repair downloaded the official portable Tectonic 0.17.0 binary into a sibling repair directory and copied existing TeX cache resources into the workspace. It compiled with --only-cached and --untrusted.

From submission_ieee_10page/:

    tectonic --only-cached --untrusted --keep-logs IEEE_TBIOM_Submission_10Page_Final.tex

From document/:

    tectonic --only-cached --untrusted --keep-logs arXiv_Preprint_10Page_Final.tex

The arXiv source refers to the sibling submission figure folder in this working layout. The flat arxiv_source.zip uses local figure paths instead and includes all figures plus integrity_sensitivity.tex. The bibliography is inline; references.bib is not required.

Without a pre-populated cache, Tectonic needs network access to acquire its TeX resources. The PDF build records include compiler output, warnings, page counts, and source/PDF hashes. Editing source without a subsequent successful build does not update a PDF.

## Verify and package

Use the release verification and build reports to distinguish arithmetic checks from outstanding research limitations. Archive SHA-256 lives in a sidecar outside the ZIP, avoiding a self-referential checksum. Git HEAD, ahead/behind state, remote privacy, and synchronization are separate from artifact correctness; this repair does not push changes.

The default clean seed driver now uses manifests/cpu_followup/training_manifest.csv (6,171 rows), which supersedes the earlier exact-hash-only 6,173-row input. The already launched resumable CPU coordinator and its restart instructions are in the separate CPU research bundle README_CPU.md. Do not launch a second training sweep while it is running.
