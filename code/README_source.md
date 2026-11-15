# Source entry points

- `verify_results.py`: historical and current evidence, manuscript tables, compiled bindings.
- `verify_completed_cpu.py`: independent arithmetic/calibration checks for all 15 new models and 120 raw score files.
- `regenerate_completed_assets.py`: current five publication figures from the new scores.
- `../reproduction/research_completion_2026-11-02/`: exact executed CPU trainer, evaluator, coordinator, tests, and runtime snapshots; copy next to the release as described in the Windows guide.
- `regenerate_publication_assets.py`, `run_seed_sweep.py`, older train/evaluate scripts: historical operations retained for audit, not the current paper entry point.

The recorded source hashes must remain unchanged for resume/provenance validation. Do not overwrite historical measurements with new numbers. Full checkpoint and image files are intentionally excluded from Git; score-level verification needs neither.
