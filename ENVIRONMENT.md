# Environment and Reproducibility Record

This file records the **actual** hardware and software used to produce every
number reported in the manuscript. The manuscript states that hardware, runtime,
software versions, and hashes are "stored in the artifact rather than inferred
from scores"; this file is that record.

Nothing here is estimated or reconstructed from metric values.

---

## 1. Hardware

| Component | Value |
|---|---|
| CPU | 13th Gen Intel(R) Core(TM) i7-13620H |
| Cores / threads | 10 physical / 16 logical |
| Clock | 2.40 GHz base |
| RAM | 31.6 GB |
| GPU | Intel(R) UHD Graphics (integrated) |
| NVIDIA GPU | **None** |
| OS | Windows 10/11, build 26200 |
| PyTorch threads used | 10 |

**All training in this paper was performed on CPU.** No CUDA device was
available or used. `torch.cuda.is_available()` returns `False` on this machine,
and all 45 ROF metric files record `"device": "cpu"`, so the execution device is
documented machine-readably in the results themselves.

This is disclosed rather than framed as a limitation of the method. The study
measures verification accuracy and parameter efficiency, not wall-clock
throughput. The efficiency claim in the paper is about **trainable parameters**
(2.26 M of 175 M, 1.29 %), which is hardware-independent.

## 2. Software

| Package | Version used |
|---|---|
| Python | 3.11.9 |
| torch | 2.14.0+cpu |
| torchvision | 0.29.0 |
| transformers | 5.17.0 |
| peft | 0.20.0 |
| mediapipe | 0.10.21 |
| numpy | 1.26.4 |
| pandas | 2.2.2 |
| scipy | 1.17.1 |
| scikit-learn | 1.9.0 |
| opencv-python-headless | 4.10.0.84 |
| Pillow | 12.3.0 |

> **Note on `configs/requirements-used.txt` vs `configs/requirements-colab.txt`.**
> `requirements-used.txt` is the authoritative lock file: the exact versions
> below, captured from the interpreter that produced every reported number.
> `requirements-colab.txt` is a looser convenience list for a hosted GPU
> runtime, and several of its ranges disagree with this environment
> (`transformers` `>=4.36,<5` vs 5.17.0; `scikit-learn` `==1.5.2` vs 1.9.0;
> `Pillow` `>=10,<12` vs 12.3.0). It also lists `timm`, `seaborn` and
> `requests`, none of which were installed. The backbone is loaded with
> `transformers.AutoModel` for `facebook/dinov2-base`, not through `timm`.

## 3. Training configuration

Held constant across all 15 runs:

```
--epochs 5 --batch-size 16 --lr 1e-4 --num-workers 0 --max-batches 0
```

- Seeds: `123`, `7`, `42`
- Variants: `frozen_whole`, `whole_lora`, `peri_lora`, `fixed_fusion`, `gated_fusion`
- Split seed: `42` (person-disjoint). The split is 128 / 27 / 28 persons over
  7,752 images; the complete-case filter drops one validation person, so the
  training manifest holds 128 / 26 / 28 persons over 7,295 images.
- Training manifest: 7,295 complete cases from 7,752 attempted

## 4. Runtime

The final sweep driver reported `SWEEP COMPLETE in 63.1 h`.

Per-run training times recorded in `work/seed_sweep/logs/driver.out.log`:

| Seed | Variant | Hours |
|---|---|---|
| 7 | frozen_whole | 2.11 |
| 42 | frozen_whole | 1.96 |
| 42 | whole_lora | 5.00 |
| 42 | fixed_fusion | 8.24 |
| 42 | peri_lora | 8.81 |
| 42 | gated_fusion | 11.44 |
| 123 | gated_fusion | 20.09 |

Sum of individually logged training runs: **57.6 h** (207,514 s). The remaining
runs predate this log and were skipped as already complete; their times are not
recoverable from it.

Peak memory was not instrumented during the runs and is therefore not reported.

## 5. Reproducibility status

| Item | Status |
|---|---|
| Person-disjoint split | Reproducible, seed 42, verified by SHA-256 |
| Complete-case training manifest | Reproducible, verified by SHA-256 |
| LaTeX source | Compiles standalone, 10 pages verified |
| Python modules | All 17 compile under Python 3.11 |
| Metric JSON + raw score CSV | Shipped for all 15 runs x 3 protocols |
| Checkpoint SHA-256 | **Recorded** in all 45 ROF metric files, verified against the checkpoints |
| Protocol pair SHA-256 | **Recorded** in all 45 ROF metric files, verified against the pair files |
| Execution device | Recorded as `device: cpu` in all 45 ROF metric files |
| Environment lock file | **Exact**, `configs/requirements-used.txt` |
| Peak memory | Not instrumented, so not reported |

Training is deterministic given the same seeds, library versions, and thread
count, but the thread count is not pinned by the code. Runs on different
hardware or with a different `torch` build may differ in the last reported
digit of the metrics.

## 6. If you want to retrain faster

Retraining is **not required** to submit, verify, or defend this paper. The
trained checkpoints and all result files are the evidence.

If you ever want a faster independent rerun, use a GPU runtime (Kaggle
Notebooks, Google Colab, or WSL2 with an NVIDIA GPU) and follow
`WINDOWS_REPRODUCTION_GUIDE.md`. Note that a GPU rerun will not reproduce these
numbers bit-exactly; treat it as an independent check of the method, not a
regeneration of the reported table.
