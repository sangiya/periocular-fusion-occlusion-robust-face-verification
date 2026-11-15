# Current readiness recheck — 15 November 2026

All 15 CPU models (seeds 7, 42, 123; five variants) completed five full epochs and evaluation on eight frozen protocols. The current paper uses these new models, not historical score-filtered runs. The manifest has 6,171 rows: 4,405 train, 844 validation, 922 test. All 15 final training records report 1,380 optimizer steps, no smoke cap, and CPU execution.

The new release contains 120 raw-score CSVs, 15 evaluation reports, 15 training completion records, a 25-row five-condition summary, ten paired AUC contrasts, calibration thresholds/counts, same-branch gate controls, and image/source/checkpoint provenance. Known MFR2 training-name-overlap exclusion retains 802 pairs. RMFRD exact-conflict exclusion retains 21,798 pairs. Unknown aliases, semantic label correctness, exhaustive perceptual duplicates, and pretraining overlap remain unresolved.

Periocular LoRA leads masked mean AUC (0.922061); fixed fusion leads sunglasses (0.894972) and exploratory RMFRD (0.724015); learned gating leads neutral (0.945826) and retained MFR2 (0.954794). The gate is embedding-conditioned with a constant auxiliary vector. Constant and permuted controls limit claims of adaptive reliability. The separate SFace baseline is stronger by AUC on these protocols, with unmatched pretraining/alignment. No state-of-the-art or population low-FAR guarantee is claimed.

Training and evaluation are complete. Current IEEE/arXiv text, figures, and metric tables are being checked against the completed evidence; build/verification records identify the exact finalized bytes. This status supersedes the interim reports under `history/`.

Submission readiness still requires author scientific review and any required licensed similarity screening. No automated pass certifies novelty, semantic image labels, journal acceptance, or AI-detector clearance. Matched strong face-recognition baselines and broader independent identities remain substantive limitations, not pending CPU jobs.

# CPU research results

Completed and evaluated models: 15/15. Status: complete.

All new runs use the frozen 6,171-row duplicate-excluded manifest. Historical models are separate.

| Protocol | Variant | Seeds complete | Mean AUC | Seed SD |
|---|---|---:|---:|---:|
| test_masked | frozen_whole | 3 | 0.830315 | 0.024009 |
| test_masked | whole_lora | 3 | 0.885186 | 0.005234 |
| test_masked | peri_lora | 3 | 0.922061 | 0.004552 |
| test_masked | fixed_fusion | 3 | 0.913441 | 0.006606 |
| test_masked | gated_fusion | 3 | 0.898936 | 0.001884 |
| test_sunglasses | frozen_whole | 3 | 0.877989 | 0.003140 |
| test_sunglasses | whole_lora | 3 | 0.891257 | 0.001719 |
| test_sunglasses | peri_lora | 3 | 0.790531 | 0.013856 |
| test_sunglasses | fixed_fusion | 3 | 0.894972 | 0.002127 |
| test_sunglasses | gated_fusion | 3 | 0.892374 | 0.005800 |
| test_neutral | frozen_whole | 3 | 0.932790 | 0.001199 |
| test_neutral | whole_lora | 3 | 0.941304 | 0.001512 |
| test_neutral | peri_lora | 3 | 0.887455 | 0.005384 |
| test_neutral | fixed_fusion | 3 | 0.942830 | 0.001371 |
| test_neutral | gated_fusion | 3 | 0.945826 | 0.002609 |
| mfr2 | frozen_whole | 3 | 0.841164 | 0.005662 |
| mfr2 | whole_lora | 3 | 0.935973 | 0.014746 |
| mfr2 | peri_lora | 3 | 0.906825 | 0.010288 |
| mfr2 | fixed_fusion | 3 | 0.939767 | 0.004923 |
| mfr2 | gated_fusion | 3 | 0.954794 | 0.002203 |
| rmfrd | frozen_whole | 3 | 0.695724 | 0.004475 |
| rmfrd | whole_lora | 3 | 0.704538 | 0.010296 |
| rmfrd | peri_lora | 3 | 0.713228 | 0.004494 |
| rmfrd | fixed_fusion | 3 | 0.724015 | 0.009870 |
| rmfrd | gated_fusion | 3 | 0.717452 | 0.012143 |

Validation-calibrated operating points, actual FAR counts, gate controls, and provenance are in each EVALUATION_REPORT.json.
The completed grid supplies the current manuscript tables. No journal-readiness or detector-clearance claim is made.
