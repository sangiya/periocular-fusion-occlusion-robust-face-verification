# Windows CPU reproduction

The recorded 15-model run is complete. A GPU is not required. Do not retrain merely to verify the shipped results.

For score-level verification, from this release folder:

```powershell
python code/verify_results.py --report document/VERIFICATION_REPORT.json
python -m unittest discover -s code/tests -v
```

To reproduce training, arrange the following folders under a common dataset root:

```text
data_plan/
  publication_release/                 # this release
  research_completion_2026-11-02/       # copy from release/reproduction/
  data/                               # licensed images at manifest paths
  work/                               # crops at manifest paths
```

Copy the complete `reproduction/research_completion_2026-11-02/` folder next to this release; its executed sources are preserved byte for byte because reports bind their SHA-256 hashes. Prepare the Python/torch/transformers/peft environment recorded under `configs/` and `ENVIRONMENT.md`, and cache `facebook/dinov2-base` from the official provider before going offline. Restore the image/crop files required by the frozen manifests. The new trainer uses `experiment/training_manifest.csv` with SHA-256 `e1be6e7ce28e795a8b4a0d66cce8c704964b589607b0622ae9eea600682d8560`.

From the common root, using the intended environment interpreter:

```powershell
python -u research_completion_2026-11-02/run_cpu_sweep.py
python research_completion_2026-11-02/status_cpu.py
```

The coordinator trains then evaluates each model, updates its summary, and advances through 15 jobs. It uses CPU, eight threads, batch size 16, five epochs, and no research batch cap. It saves optimizer, sample order, RNG states, and source/manifest signatures atomically about every ten minutes and at epoch boundaries. Repeating the command resumes the last saved batch; unsaved batches repeat. A worker lock prevents simultaneous coordinators. Sleep suspends work; shutdown ends the process and requires relaunch. The coordinator has bounded retries for one recorded Windows exit condition, not universal reboot auto-start.

Keep the laptop powered and awake during a reproduction. Different hardware/software may change floating-point results; bitwise equality across systems is not promised. Do not copy this release's completed reports into a fresh training folder to pretend new work is complete. For verification of existing completed outputs, use the standard-library verifier instead.

Current plot generation: `python code/regenerate_completed_assets.py`. Final documents are in `submission_ieee/` and `submission_arxiv/`. The root `run_seed_sweep.py` is now a status/guarded launcher for the exact preserved CPU coordinator; the superseded historical driver has been removed.

When reconstructing a fresh runtime folder, also copy `manifests/cpu_followup/` into `research_completion_2026-11-02/experiment/`, and retain `cpu_runs/runtime/` from the executed snapshot. The original frozen experiment-plan status predates training; completion is established by the fifteen final records, not by editing that signed plan. Do not copy final scores/progress into a fresh runtime to impersonate a completed reproduction.
