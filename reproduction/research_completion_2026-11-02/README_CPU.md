# CPU research execution ? completed 15 November 2026

The full 15-model sweep was launched on 2 November 2026. It uses CPU only, eight PyTorch threads, offline cached DINOv2, five complete epochs, three seeds (7, 42, 123), and five variants. No research run uses a smoke-test batch cap. GPU hardware is not required. Keep the machine powered and awake for training to proceed.

The frozen experiment has 6,171 manifest rows: 4,405 train, 844 validation and 922 test. The additional cross-split near-duplicate photograph is excluded on both sides. Full semantic label validation and unknown pretraining identity overlap remain unresolved.

The serial coordinator trains one model, evaluates it, updates the summary, and then advances to the next model. It never promotes partial results into the main manuscript tables. Successful completion means 15 fully trained AND evaluated models. The initial smoke tests are stored under `cpu_runs/smoke/` and cannot count as completed research runs.

From the workspace root, read progress with:

```powershell
python manus/data_plan/research_completion_2026-11-02/status_cpu.py
```

The recorded sweep is complete (15/15 trained and evaluated models). No training worker remains to resume. For a fresh reproduction or an interrupted independent run, use:

```powershell
& '.\manus\data_plan\.venv\Scripts\python.exe' -u '.\manus\data_plan\research_completion_2026-11-02\run_cpu_sweep.py'
```

A file lock rejects simultaneous coordinators. Full checkpoints are written atomically after the first batch, approximately every ten minutes, and at epoch boundaries. They include optimizer state, sample order, next batch, all RNG states, manifest hash, trainer hash and model-code hash. An interrupted run resumes from its last saved batch. Changing the trainer or model code intentionally invalidates resumption; preserve the active code while the sweep runs. Exact continuation was tested in the same runtime; bitwise equality across hardware or package changes is not claimed.

The original model implementation instantiated and computed an unused face branch for periocular-only training. The new CPU trainer skips that unused forward pass. This does not alter which branch supplies the periocular loss, but it changes random-number consumption; the new experiment is not claimed to reproduce historical training bit for bit.

Evaluation batches unique image/crop endpoints, caches branch embeddings, records score/model/protocol/image hashes, and computes operating points from validation identities. Gate controls use the same learned branches: fixed 0.5, validation-mean, permuted gate, face-only and periocular-only. A constant quality vector is explicitly treated as a fixed bias rather than evidence of quality adaptation. Test-identity uncertainty uses 1,000 two-endpoint node-resampling sensitivity replicates. Paired AUC intervals are produced only after the full three-seed grid exists.

The completed new sweep remains separate from historical reevaluation:

- `archived_reevaluation/`: 45 score reevaluations of historical models on the new ROF test pairs; training is unchanged.
- `sface/`: actual SFace/YuNet CPU baseline on eight frozen protocols, raw scores, image ledger, validation thresholds and identity-resampling sensitivity intervals.
- `FOLLOWUP_VERIFICATION.json`: independent arithmetic and pair-alignment check of those 53 completed score files.
- `cpu_runs/SWEEP_STATUS.json`: live coordinator state.
- `cpu_runs/checkpoints/*_progress.json`: live model batch progress.
- `cpu_runs/RESULTS_SUMMARY.md`: results of completed and evaluated new models only.

The initial measured frozen-model smoke batches took 5.47 and 5.67 seconds with eight threads. The gated LoRA smoke batch took 103.81 seconds with two threads while other CPU work ran. These measurements validate execution; they are not a guaranteed sweep duration. Expect sustained CPU work over days, not instantaneous completion.

The separate CPU research bundle includes source, frozen protocols and completed follow-up evidence; datasets, pretrained weights, new full checkpoints, temporary embedding caches and live training logs are not bundled. Reproduction requires the existing `publication_release/`, local dataset/crops and virtual environment beside this directory. Comprehensive licensed similarity screening, author approval and a journal acceptance decision cannot be inferred from successful execution.

## Recovery on 3 November 2026

Three models were fully trained, evaluated and verified before fixed-fusion seed 7 was interrupted. It resumed from saved optimizer step 149 at epoch 1, batch 150; the most recent unsaved batches are repeated. The coordinator now validates completed checkpoint, score, source and protocol hashes before skipping those jobs. It retries the observed Windows termination code 0x40010004 at most three times per phase, with 10/30/60-second delays. Python/data errors and deliberate Ctrl+C are not retried automatically. This recovery works while the coordinator remains running; it does not install a Windows startup task or resume automatically after a reboot. Creating cpu_runs/STOP_AFTER_CURRENT_PHASE requests a stop before the next phase; remove that file before an intentional restart.
