# Environment and run record

## Historical experiments

The archived files record CPU execution. Historical documentation identifies an Intel Core i7-13620H, 31.6 GB RAM, Windows build 26200, Python 3.11.9, and 10 torch threads. The reported driver elapsed 63.1 hours; seven recoverable training log entries total about 57.6 hours, with other models already present. This is not a verified total duration for 15 freshly trained models.

Package pins are in configs/requirements-used.txt. It records torch 2.14.0, torchvision 0.29.0, transformers 5.17.0, and peft 0.20.0 among others. The actual existing interpreter used for the repair reports torch 2.14.0+cpu, transformers 5.17.0, and peft 0.20.0.

The historical source split has 128/26/28 complete-case identity labels and 7,295 rows. Its content audit found four identical rows under different labels across train/validation, and repeated images. The clean manifest has 6,173 unique-content rows (4,406/844/923) with the same 128/26/28 retained label counts. Historical checkpoints were not retrained on it.

## New verified correction

results/corrections/mfr2_quality_v2/ records actual inference using the three final gated checkpoints, CPU, batch size 8, quality vector [1,0,0,1], bootstrap RNG seed 42, and 1,000 one-sided identity bootstrap repetitions. Per-run JSONs contain training seed, evaluator hash, checkpoint/pair/raw-score hashes, elapsed seconds, and image/pair counts.

New inference does not imply new training. Post-hoc subsets use the existing checkpoints and retain this distinction in their metadata.

## Runtime limitations

Peak memory was not instrumented. No hardware-independent inference speedup is claimed from a small trainable-parameter percentage. M0 includes a trained projection; M2's nominal accounting includes an inactive whole-face branch. The training-only classifier adds 98,432 parameters and is excluded from the model table.

Exact deterministic continuation is not established for historical partial checkpoints without optimizer/RNG state. New training is isolated by manifest hash and rejects unknown/different manifest resumption.

## PDF environment

The repair used portable Tectonic 0.17.0 with a workspace copy of existing cached resources. document/BUILD_REPORT.json records the final actual output and hashes. A successful source edit alone is not a PDF build.

## New CPU research sweep

A new 6,171-row manifest excludes the subsequently confirmed cross-split near-duplicate photograph. The prospective sweep has 4,405 training rows, five complete epochs, seeds 7/42/123 and five variants. It runs on CPU with eight threads and offline cached weights. Atomic checkpoints store optimizer, sample order and all RNG states. The full sweep is in progress and its completed results must be reviewed before manuscript promotion. The separate README_CPU.md documents resume commands and the periocular-only unused-branch optimization.
