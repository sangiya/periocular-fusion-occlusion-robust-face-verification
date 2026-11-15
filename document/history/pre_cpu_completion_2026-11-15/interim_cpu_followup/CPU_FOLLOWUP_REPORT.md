# CPU research follow-up — interim

Full clean-manifest CPU training is running. The complete 15-model sweep is not yet finished.

Completed: 45 duplicate-excluded historical ROF score reevaluations, SFace/YuNet CPU inference on eight frozen protocols, validation-only SFace threshold calibration, and 1,000-replicate two-endpoint identity-resampling AUC sensitivity intervals.

| Protocol | SFace AUC | Failed pairs retained |
|---|---:|---:|
| test_masked | 0.939905 | 9 |
| test_sunglasses | 0.943978 | 48 |
| test_neutral | 0.999117 | 0 |
| mfr2 | 0.996847 | 0 |
| rmfrd | 0.818685 | 1155 |

SFace uses external pretraining and different alignment. Unknown pretraining identity overlap remains; these are diagnostic comparisons, not a matched-training or SOTA claim.

The main 10-page PDFs now disclose the later cross-split near-duplicate photograph. New clean-trained results remain pending.

Live progress: `manus/data_plan/research_completion_2026-11-02/cpu_runs/SWEEP_STATUS.json` and the current model progress JSON.

Raw evidence and reproducible CPU scripts are supplied in the separate `cpu_research_followup.zip` bundle. Its SHA-256 is in its external sidecar.
