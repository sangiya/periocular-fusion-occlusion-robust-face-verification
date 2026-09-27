# Windows Reproduction Guide

Step-by-step PowerShell instructions to reproduce the reported results from a clean
checkout of this release.

This guide replaces the older ad-hoc command files (`script_window1.txt`,
`script1.txt`, `scripts.txt`). Those are terminal transcripts, not runnable
scripts, and they contain superseded commands. **Do not use them.**

---

## 0. Before you start: what you need

| Requirement | Notes |
|---|---|
| Windows 10/11 | PowerShell 5.1+ |
| Python 3.10 or 3.11 | 3.11 was used for the reported results |
| NVIDIA GPU + CUDA | **Required for training.** The reference machine had no NVIDIA GPU, so steps 6-9 were not run locally. |
| ROF, MFR2, RMFRD datasets | Not redistributable. See `README.md` for sources. |

Check for a GPU:

```powershell
nvidia-smi
```

If that command is not found, you cannot train locally. Use **WSL2 with an NVIDIA
GPU**, **Google Colab**, or **Kaggle Notebooks**. Steps 1-5 (manifests, crops,
protocol freezing) run fine on CPU.

---

## 1. Set up the environment

```powershell
cd "D:\path\to\publication_release"

py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
```

Install the pinned environment that actually produced the reported results:

```powershell
pip install -r .\configs\requirements-used.txt
```

> Use `requirements-used.txt` for reproduction. `requirements-colab.txt` is a
> looser convenience list for a hosted GPU runtime and its version ranges do
> **not** match the environment behind the reported numbers.
>
> `requirements-used.txt` pins the CPU build of torch. For a CUDA machine,
> install the matching wheel first:
>
> ```powershell
> pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
> pip install -r .\configs\requirements-used.txt
> ```

Verify:

```powershell
python -c "import torch, mediapipe, pandas, sklearn; print('torch', torch.__version__); print('cuda', torch.cuda.is_available())"
```

---

## 2. Place the datasets

Expected layout inside the release folder:

```
data\
  ROF\images\{neutral,masked,sunglasses}\<identity>\*.jpg
  mfr2\...
  RMFRD\...
```

ROF conditions must be named exactly `neutral`, `masked`, `sunglasses`. Identity
folder names must be the raw names (for example
`alexander_zverev_wearing_mask`), because the person-disjoint split derives the
person from them.

---

## 2a. Manifest paths (no action needed)

Every manifest in `manifests\` already stores paths relative to this bundle's
root with forward slashes, so the pipeline works unchanged on Windows, Linux,
and macOS. Place the datasets under `data\` and run every command from the
bundle root.

If you move the bundle or want absolute paths instead, use the helper:

```powershell
python .\code\remap_manifest_paths.py --root . --dry-run
python .\code\remap_manifest_paths.py --root . --in-place
```

The periocular crop directories do not exist until you run steps 4-5, so the
tool will report unresolved references at first. That is expected.

---

## 3. Build the ROF index (manifest)

```powershell
python .\code\prepare_data.py `
  --root .\data\ROF\images `
  --out  .\work\rof_manifest_raw.csv
```

Produces `path,identity,condition,split,sha256`. The `split` column it writes is
**discarded** in the next step.

---

## 4. Create the person-disjoint split

This is the step that prevents identity leakage. It merges the
`..._wearing_mask` / `..._wearing_sunglasses` variants of one person into a
single `person_id`, then splits **by person**, not by image.

```powershell
python .\code\create_person_disjoint_split.py
```

```powershell
python .\code\create_crop_input.py
```

Expected (reported run):

| Split | Rows | Persons |
|---|---|---|
| train | 5,506 | 128 |
| val | 1,066 | 27 |
| test | 1,180 | 28 |

---

## 5. Generate periocular crops

```powershell
python .\code\generate_periocular_mediapipe.py `
  --input    .\work\rof_manifest_crop_input.csv `
  --output   .\work\crop_manifest_person_disjoint.csv `
  --crop-dir .\work\periocular_person_disjoint `
  --margin   0.20 `
  --size     224
```

> `--margin 0.20` is what produced the reported results. The script default is
> `0.35`, so always pass this flag explicitly.

Failed detections get an **empty** `peri_path` and `crop_status=failed`. Whole-face
images are never substituted for a failed crop.

Then build the complete-case training manifest:

```powershell
python .\code\build_training_manifest.py
```

This keeps only rows where the face image, the crop, and the condition label are
all valid, and rewrites `identity` to `person_id` so a person's three conditions
form one training class.

Expected: **7,295** rows (7,752 attempted, 457 failed detections), 182 persons,
zero person overlap across splits.

---

## 6. Freeze the ROF evaluation protocols

```powershell
python .\code\freeze_rof_protocol.py `
  --manifest .\work\crop_manifest_training_person_disjoint.csv `
  --out-dir  .\work\protocol_v2 `
  --max-impostors-per-probe 100
```

---

## 7. Train (3 seeds x 5 variants)

Use the driver. It is resumable and skips finished work.

```powershell
python .\run_seed_sweep.py
```

It trains seeds `123, 7, 42` for variants
`frozen_whole, whole_lora, peri_lora, fixed_fusion, gated_fusion`, then evaluates
each checkpoint on the masked, sunglasses and neutral protocols, runs paired
comparisons, and writes `seed_sweep_summary.{json,csv}`.

Training settings (fixed, do not change):

```
--epochs 5 --batch-size 16 --lr 1e-4 --num-workers 0
```

To run a single configuration manually:

```powershell
python .\code\train.py `
  --manifest .\work\crop_manifest_training_person_disjoint.csv `
  --variant  gated_fusion `
  --epochs   5 `
  --batch-size 16 `
  --lr 1e-4 `
  --seed 123 `
  --num-workers 0 `
  --out .\work\seed_sweep\checkpoints\seed123_gated_fusion.pt
```

---

## 8. Evaluate the cross-dataset protocols (MFR2, RMFRD)

The protocol pair files are **already shipped and frozen** in `manifests\`, so you
can skip the prepare stage if you only want to reproduce the reported numbers:

| Purpose | File in `manifests\` |
|---|---|
| MFR2 protocol (820 pairs, used for the reported result) | `mfr2_official_complete_pairs.csv` |
| MFR2 raw official pairs (848, provenance only) | `mfr2_official_pairs.csv` |
| RMFRD protocol (22,554 pairs) | `rmfrd_pairs.csv` |
| MFR2 crop manifest | `mfr2_crop_manifest.csv` |
| RMFRD crop manifest | `rmfrd_crop_manifest.csv` |

To regenerate the periocular crops for these datasets instead, run the
preparation stage:

```powershell
# MFR2
python .\code\prepare_mfr2_protocol.py `
  --pairs   .\manifests\mfr2_pairs_local.csv `
  --crops   .\manifests\mfr2_crop_manifest.csv `
  --out-dir .\work\mfr2_protocol

# RMFRD
python .\code\prepare_rmfrd_protocol_v2.py `
  --crops              .\manifests\rmfrd_crop_manifest.csv `
  --out-dir            .\work\rmfrd_protocol_v2 `
  --impostors-per-probe 20 `
  --seed 42
```

Then evaluate every seed-sweep checkpoint on all cross-dataset protocols:

```powershell
python .\code\evaluate_all_cross_dataset_fixed.py `
  --root "D:\path\to\publication_release" `
  --protocol all `
  --batch-size 8 `
  --bootstrap 1000 `
  --seed 42
```

> `--root` must be the folder that contains `work\seed_sweep\checkpoints\`, and
> it must be the same root you passed to `remap_manifest_paths.py`.

This writes to `Final Results\seed_sweep\cross_dataset\`. See the mapping table
in section 11 for how that relates to the shipped `results\seed_sweep\` layout.

---

## 9. Aggregate and compare

```powershell
python .\code\compare_rof_models.py `
  --reference .\work\seed_sweep\results\seed123_fixed_fusion_masked_raw_scores.csv `
  --candidate .\work\seed_sweep\results\seed123_gated_fusion_masked_raw_scores.csv `
  --bootstrap 5000 --seed 42 `
  --out .\comparison_gated_vs_fixed_masked.json
```

The 18 paired comparisons and `seed_sweep_summary.{json,csv}` that the manuscript
cites are produced automatically by `run_seed_sweep.py` in step 7; you only need
`compare_rof_models.py` directly if you want a single extra contrast.

> **A note on the word "corrected".** The manuscript's corrected MFR2 values come
> from the image-keyed evaluator `evaluate_all_cross_dataset_fixed.py` in step 8,
> which caches embeddings by the concrete `(face_path, peri_path)` tuple and
> rejects exact image self-pairs. That is the only MFR2 path that produces
> reported numbers. A separate one-off check of the MFR2 gate-input quality
> vector is not part of this release, because it is not cited and its inputs
> predate the final seed sweep.

---

## 10. Verify against the shipped results

### 10a. Verify the shipped results (no GPU needed)

This is the fast check. It reads only the metric JSON files in `results\seed_sweep\`
and recomputes every headline value in the manuscript. It needs **no dataset, no
checkpoints, and no retraining**, so it runs in a couple of seconds on any
machine:

```powershell
python .\code\verify_results.py
```

It checks sweep completeness, the three headline neutral AUCs, that every result
records its checkpoint and protocol hashes and execution device, the
cross-dataset coverage, the aggregate summary, and the 18 paired comparisons.
It exits non-zero if any claim does not match.

Expected final line:

```text
RESULT: ALL CHECKS PASSED
```

### 10b. Verify the metric implementation

```powershell
python .\code\verification.py
```

The positive-control AUC should be near 1.0 and random scores near 0.5.

### 10c. Compare a fresh run against the shipped copy

| Fresh output location | Shipped location in this bundle |
|---|---|
| `work\seed_sweep\results\seed{S}_{variant}_{cond}_*` | `results\seed_sweep\rof_seed_sweep\` |
| `Final Results\seed_sweep\cross_dataset\*` | `results\seed_sweep\cross_dataset\` |
| `Final Results\seed_sweep\comparison_*.json` | `results\seed_sweep\` (top level) |
| `Final Results\seed_sweep\seed_sweep_summary.{json,csv}` | `results\seed_sweep\` (top level) |

The bundle reorganises the original working tree into a single `results\seed_sweep\`
folder. The file contents are unchanged.

Key numbers to confirm:

| Quantity | Value |
|---|---|
| Gated fusion, neutral mean AUC | 0.9441 |
| Fixed fusion, neutral mean AUC | 0.9424 |
| Periocular, neutral mean AUC | 0.8832 |

---

## 11. Where each output goes

| Stage | Output |
|---|---|
| 3. index | `work\rof_manifest_raw.csv` |
| 4. split | `work\rof_manifest_person_disjoint.csv`, `work\rof_manifest_crop_input.csv` |
| 5. crops | `work\periocular_person_disjoint\`, `work\crop_manifest_person_disjoint.csv`, `work\crop_manifest_training_person_disjoint.csv` |
| 6. protocols | `work\protocol_v2\rof_{masked,sunglasses}_pairs.csv` |
| 7. train | `work\seed_sweep\checkpoints\seed{S}_{variant}.pt` |
| 8. eval | `work\seed_sweep\results\`, `Final Results\seed_sweep\cross_dataset\` |
| 9. compare | `Final Results\seed_sweep\comparison_*.json`, `seed_sweep_summary.{json,csv}` |

`Final Results\` contains a space and is a legacy directory name. It is kept
because it is where the reported run actually wrote its files; the shipped
bundle copies the contents under `results\seed_sweep\`.

---

## Troubleshooting

**`UnicodeEncodeError: 'charmap' codec`**
Some older scripts used `âˆ©` (U+2229) in `print()` calls, which crashes the default
Windows cp1252 console. The scripts shipped here use ASCII output. If you hit
this in your own copy, either set `$env:PYTHONIOENCODING="utf-8"` or replace the
character.

**`FileNotFoundError: work\rof_manifest_raw.csv`**
Steps 3-5 must run in order. `create_person_disjoint_split.py` and
`create_crop_input.py` resolve paths relative to the script location, not the
shell's current directory, so you can run them from anywhere inside the folder.

**`Cannot start the sweep. Missing required input file`**
`run_seed_sweep.py` checks its inputs before doing any work. Complete steps 5-6.

**CUDA out of memory**
Lower `--batch-size` (try 8) and keep `--num-workers 0`. Note that changing the
batch size changes the result, so prefer a smaller `--batch-size` consistently
across all seeds rather than per-run tweaks.

**MediaPipe fails to install**
`mediapipe==0.10.21` requires `protobuf==4.x`. Do not let pip upgrade Protobuf
to 5.x.
