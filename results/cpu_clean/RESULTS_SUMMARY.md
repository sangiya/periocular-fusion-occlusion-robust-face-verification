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
