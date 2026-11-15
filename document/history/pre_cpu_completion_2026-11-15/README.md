# Occlusion-robust face verification research artifact

Target venue: IEEE Transactions on Biometrics, Behavior, and Identity Science (T-BIOM).
Status: revised research artifact; journal submission/acceptance status is not asserted.

This release distinguishes historical results, corrected MFR2 inference, post-hoc exclusion sensitivities, and new clean training inputs. Passing artifact verification does not establish journal readiness or absence of all dataset errors.

## What changed on 2 November 2026

- Actual gated-MFR2 inference uses [1,0,0,1], matching all archived ROF training rows. Per-seed raw scores and provenance are under results/corrections/mfr2_quality_v2/.
- manifests/cleaned/ contains a content-unique ROF manifest and frozen exclusion protocols/ledgers.
- The preliminary exact-hash-clean ROF manifest has 6,173 rows. The current training input, manifests/cpu_followup/training_manifest.csv, additionally excludes the later cross-split near-duplicate photograph: 6,171 rows (4,405 train, 844 validation, 922 test). Both stages preserve exclusion ledgers.
- Unique-probe ROF subsets retain 423 masked, 6,672 sunglasses, and 15,988 neutral pairs.
- Known-name-overlap exclusion retains 802 MFR2 pairs; exact-conflict exclusion retains 21,798 RMFRD pairs, removing 756 affected pairs.
- Score sensitivities use historical models, including corrected MFR2 gated inference. They are NOT results from clean-trained models.
- The verifier recomputes raw-score metrics, compares manuscript tables, checks provenance mappings and corrected run hashes, and checks clean-input invariants.

Historical files under results/seed_sweep/ remain unchanged. Old checkpoint names do not certify training on cleaned data. Exact image duplicates under different labels existed between the original training and validation inputs; no clean-trained performance is claimed.

## Check the release

From this folder:

    python code/verify_results.py --report document/VERIFICATION_REPORT.json

This check needs Python's standard library only; no GPU, original images, trained weights, numpy, or sklearn. It verifies the explicit checks in the report, not plagiarism, real-person labels, all confidence intervals, or publication suitability.

## Reproduce data checks and sensitivities

Obtain licensed datasets and periocular crops. Paths in manifests are relative to the root containing data/ and work/.

    python code/prepare_integrity_protocols.py --root . --dataset-root D:/path/to/data_plan
    python code/build_score_sensitivities.py

The first command hashes RMFRD images/crops and constructs deterministic exclusion ledgers. The second computes point metrics from the shipped scores. No new confidence intervals are claimed for these post-hoc sensitivities.

For corrected gated MFR2 inference, use the working environment and actual checkpoint directory:

    python code/evaluate_all_cross_dataset_fixed.py --root . --dataset-root D:/path/to/data_plan --checkpoint-root D:/path/to/checkpoints --output-dir results/new_mfr2_check --protocol mfr2 --variants gated_fusion --seeds 7 42 123 --batch-size 8 --bootstrap 1000

Missing files, stale output collisions, and evaluation errors are fatal. Use a new output directory to preserve recorded runs. A GPU is optional; the verified corrections ran on CPU.

## Train genuinely new clean models

    python code/train_clean_seed_sweep.py --root . --dataset-root D:/path/to/data_plan --dry-run
    python code/train_clean_seed_sweep.py --root . --dataset-root D:/path/to/data_plan

The dry run checks inputs and prints all commands. Actual training creates a manifest-hash-specific checkpoint directory under work/clean_training/. It never reuses the historical checkpoints. The trainer rejects repeated image hashes, split overlap, and resumption from a different/unknown training manifest.

The original run_seed_sweep.py is retained as historical orchestration; it is not the clean-training entry point. A new raw re-index/repartition is a different protocol unless its person assignments are explicitly shown to match the archived manifest.

## Manuscripts and figures

- submission_ieee_10page/ contains the IEEE source/PDF, inline bibliography, shared sensitivity table, vector figures, and PNG previews.
- document/ contains the arXiv source/PDF and current audit/checklist.
- arxiv_source.zip is a flat source-and-figure package, suitable for source compilation.
- code/regenerate_publication_assets.py rebuilds figures and updates numerical MFR2 text/table values from the corrected scores.
- code/build_score_sensitivities.py regenerates integrity_sensitivity.tex from the archived/corrected score subsets.

PDFs must be compiled after editing source. See WINDOWS_REPRODUCTION_GUIDE.md for the compiler commands and actual checked output. Exact page counts are recorded in document/BUILD_REPORT.json.

## Interpretation and outstanding research work

M0 freezes the DINOv2 encoder but trains a projection. M2's nominal parameter count includes an unused whole-face branch; active versus instantiated parameters are explained in the manuscript. DINOv2 is a general visual encoder, not a face-specialized recognition model.

Reported TAR thresholds are retrospective test-ROC summaries, not independently calibrated deployment thresholds. Masked ROF and MFR2 have fewer than 1,000 impostor pairs: FAR 0.001 values indicate zero observed false accepts and do not validate population FAR below 0.001. Bootstrap intervals are conditional on the endpoint actually resampled and do not fully account for both endpoints' dependence.

ROF's corrected inventory has 7,751 files but 6,491 recorded unique hashes. Its selection differs from the maintainer's published dataset counts; the version/selection difference remains unresolved. The raw image index had incorrectly included a resources illustration, removed before this revision. Content cleaning does not itself establish that every remaining label is correct.

Fresh training on the clean manifest, further perceptual/identity validation, and stronger matched face-recognition/fusion baselines remain necessary for strong scientific claims. No claim of journal acceptance, corpus-wide plagiarism clearance, or AI-authorship certification is made.

## Provenance and distribution

manifests/provenance_map.json maps original absolute-path protocol hashes to portable files and canonical logical rows. Historical metadata are preserved. Public checkpoint binaries and original face images are not included. Hashes support traceability but cannot regenerate embeddings.

FINAL_PUBLICATION_AUDIT.md and FINAL_SUBMISSION_CHECKLIST.md in document/ are authoritative. document/history/ contains superseded statements and failed-run logs, not current verification.

The archive is built deterministically. Its SHA-256 is stored in the external publication_release.zip.sha256 sidecar; the archive does not contain its own checksum. RELEASE_MANIFEST.json records individual release-file hashes.

Code: Apache-2.0 (code/LICENSE). Documentation/results/manifests: CC BY 4.0 (LICENSE). Original dataset and model terms apply separately.

The existing Git policy ignores submission_ieee_10page/. This repair preserves that policy. The complete release ZIP includes those submission files; a Git push alone would not distribute the ignored IEEE sources/PDF. No commit or push was performed.

Hash-bound artifact files are byte-preserved by .gitattributes. Automatic newline conversion after recording hashes would invalidate evaluator, protocol, and PDF-build bindings.

## CPU research follow-up in progress

The full clean-manifest CPU training sweep has started; completed new results remain pending. Both manuscripts now disclose the later training/test near-duplicate photograph. Completed duplicate-excluded historical reevaluations and the additional SFace/YuNet baseline are in [the interim follow-up report](document/cpu_followup/CPU_FOLLOWUP_REPORT.md). Raw evidence and CPU scripts are in the separate cpu_research_followup.zip beside this release. The live local status is ../research_completion_2026-11-02/cpu_runs/SWEEP_STATUS.json.
