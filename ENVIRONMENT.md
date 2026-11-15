# Recorded execution environment

The new experiment completed on CPU on 15 November 2026. It used Windows, Python 3.11, PyTorch 2.14.0+cpu, eight torch threads, deterministic algorithms, and offline cached DINOv2-base. Original dependency/configuration records are retained in `configs/`; the exact executed sources and runtime snapshots are under `reproduction/research_completion_2026-11-02/`.

Each of 15 models used five full epochs, batch size 16, AdamW learning rate 1e-4 and weight decay 1e-4, uniform sampling with replacement, 4,405 draws/epoch, and 276 batches/epoch. LoRA uses rank 8, alpha 16, dropout 0.1 on query/key/value projections. The constant auxiliary vector is [1,0,0,1]. The 128-class training-only head has 98,432 parameters and is excluded from the model parameter table.

Training rows are 4,405; validation 844; test 922. The 6,171-row manifest excludes known exact duplicates/conflicts and both copies of the confirmed cross-split near-duplicate photograph. Each result is bound to a checkpoint hash and executed source/protocol hashes. Dataset and checkpoint binaries are not included in Git. Embedding regeneration therefore requires the licensed files, pretrained weights, and training/checkpoint access.

Wall-clock durations in the records include interruptions/sleep and are not uninterrupted benchmark timings. Peak memory was not instrumented. Exact optimizer/RNG continuation was tested within the recorded runtime; equality across hardware/package versions is not claimed. The periocular-only new trainer skips an unused whole-face forward pass, so it is not bitwise identical to the historical trainer.

Historical 7,295-row training, 6,173-row exact-hash-only cleaning, historical 10-thread records, corrected MFR2 inference, and post-hoc sensitivities remain separate audit stages. None of those stage counts defines the current new experiment.
