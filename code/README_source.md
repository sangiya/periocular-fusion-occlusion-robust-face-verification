# Final source entry points

- `verify_results.py`: final CPU/SFace evidence, final manuscript tables, source dependencies and build bindings.
- `verify_completed_cpu.py`: all fifteen completed models, 120 raw scores and calibrated operating points.
- `verify_strengthening.py`: shared-crop SFace and nine-identity cohort sensitivity.
- `verify_final_documents.py`: thirteen measured tables, matching IEEE/arXiv sources, thirty-eight references and two source ZIPs.
- `regenerate_completed_assets.py`: the five measured publication plots.
- `evaluate_shared_crop_sface.py` and `analyze_masked_identity_sensitivity.py`: recorded additional controls; their signed source bytes are retained.
- Remaining data/preprocessing modules and frozen input manifests preserve protocol construction and auditing. The final training input is exclusively `manifests/cpu_followup/training_manifest.csv`; original audit inputs must not be substituted.
- `../reproduction/research_completion_2026-11-02/`: byte-preserved executed CPU sources and runtime. Follow the root reproduction guide; do not edit signed source bytes or misrepresent old weights as newly trained models.

No training is needed for score-level verification. Image and checkpoint binaries are excluded. Obsolete paper-generation and old-sweep asset writers have been removed from the active release.
