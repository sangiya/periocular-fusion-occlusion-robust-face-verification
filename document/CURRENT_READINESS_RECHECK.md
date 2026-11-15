# Current readiness recheck â€” 15 November 2026

All 15 CPU models (seeds 7, 42, 123; five variants) completed five full epochs and evaluation on eight frozen protocols. The current paper uses these new models, not historical score-filtered runs. The manifest has 6,171 rows: 4,405 train, 844 validation, 922 test. All 15 final training records report 1,380 optimizer steps, no smoke cap, and CPU execution.

The new release contains 120 raw-score CSVs, 15 evaluation reports, 15 training completion records, a 25-row five-condition summary, ten paired AUC contrasts, calibration thresholds/counts, same-branch gate controls, and image/source/checkpoint provenance. Known MFR2 training-name-overlap exclusion retains 802 pairs. RMFRD exact-conflict exclusion retains 21,798 pairs. Unknown aliases, semantic label correctness, exhaustive perceptual duplicates, and pretraining overlap remain unresolved.

Periocular LoRA leads masked mean AUC (0.922061); fixed fusion leads sunglasses (0.894972) and exploratory RMFRD (0.724015); learned gating leads neutral (0.945826) and retained MFR2 (0.954794). The gate is embedding-conditioned with a constant auxiliary vector. Constant and permuted controls limit claims of adaptive reliability. The separate SFace baseline is stronger by AUC on these protocols, with unmatched pretraining/alignment. No state-of-the-art or population low-FAR guarantee is claimed.

Training and evaluation are complete. Current IEEE/arXiv text, figures, and metric tables have been updated and checked against the completed evidence. Both manuscripts compile to 10 pages, 21 regression tests pass, and the artifact verifier reports ALL CHECKS PASSED. Build/verification records identify the exact checked bytes. This status supersedes the interim reports under `history/`.

Submission readiness still requires author scientific review and any required licensed similarity screening. No automated pass certifies novelty, semantic image labels, journal acceptance, or AI-detector clearance. Matched strong face-recognition baselines and broader independent identities remain substantive limitations, not pending CPU jobs.

The targeted submission review and prepared author materials are in [submission_preparation](submission_preparation/SCIENTIFIC_READINESS_REVIEW.md). Journal-level novelty and the factual ethics/consent declaration remain unresolved; downloading data from online sources does not establish review or consent. The author reports no previous submission.
