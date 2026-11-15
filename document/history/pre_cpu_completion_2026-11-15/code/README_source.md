# Source and evidence paths

The historical pipeline remains available for traceability. The current safe paths are:

1. prepare_integrity_protocols.py: hash-based conflict/repetition exclusions, new training manifest and evaluation sensitivity pair lists.
2. train_clean_seed_sweep.py: input validation and genuinely new, isolated training (optional --dry-run).
3. train.py: rejects repeated image hashes and cross-split identity labels; stores training-manifest hash.
4. evaluate_all_cross_dataset_fixed.py: corrected gate vector, explicit dataset/checkpoint/output roots, fatal missing inputs, and per-run provenance.
5. build_score_sensitivities.py: identical post-hoc pair selection across models; no new clean-trained claim.
6. regenerate_publication_assets.py: vector plots, previews, and corrected MFR2 table/prose values.
7. verify_results.py: standard-library raw-score/table/provenance validation.

model.py retains checkpoint compatibility. M0 freezes the encoder but trains its projection. M2 constructs an inactive face branch; the model table distinguishes nominal and active parameters.

The root run_seed_sweep.py is historical orchestration, not the clean-training entry point. Running clean training must not silently reuse historical epoch-5 checkpoints. See ../WINDOWS_REPRODUCTION_GUIDE.md for paths and commands.

Current clean training defaults to manifests/cpu_followup/training_manifest.csv (6,171 rows). The preliminary manifests/cleaned/rof_training_clean.csv is retained as an exact-hash-only audit stage, not the current training default. Resumable CPU research scripts and frozen runtime snapshots are in the sibling CPU research bundle.
