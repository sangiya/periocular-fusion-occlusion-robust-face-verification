# Source entry points

- `verify_results.py`: historical and current evidence, manuscript tables, compiled bindings.
- `verify_completed_cpu.py`: independent arithmetic/calibration checks for all 15 new models and 120 raw score files.
- `regenerate_completed_assets.py`: current five publication figures from the new scores.
- `../reproduction/research_completion_2026-11-02/`: exact executed CPU trainer, evaluator, coordinator, tests, and runtime snapshots; copy next to the release as described in the Windows guide.
- `regenerate_publication_assets.py`, `run_seed_sweep.py`, older train/evaluate scripts: historical operations retained for audit, not the current paper entry point.

The recorded source hashes must remain unchanged for resume/provenance validation. Do not overwrite historical measurements with new numbers. Full checkpoint and image files are intentionally excluded from Git; score-level verification needs neither.

After regenerating a completed-results manuscript with the preserved promotion script, run `python tools/prepare_submission_review.py` to reapply the checked citation additions and preprint-preparation notice. These source edits require recompilation and refreshed build/verification records before packaging. The source packager includes only referenced TeX inputs and figures.

For the academic revision, apply `tools/polish_academic_manuscript.py` after the submission-review pass. Then generate `tools/draw_thesis_method.py`, build `tools/build_research_thesis.py`, and compile `document/thesis/Research_Thesis_Draft.tex`. `tools/verify_thesis_document.py` checks the shared measured tables, register, and compiled PDF bindings. The main artifact verifier also checks those thesis bindings. Font/PDF generation needs Tectonic; diagrams need Matplotlib; PDF structure checking needs pypdf.
