# Source code

Implementation of the ROF training and cross-dataset verification pipeline.
Licensed under Apache-2.0 (see `LICENSE`).

For setup and end-to-end instructions see [`../WINDOWS_REPRODUCTION_GUIDE.md`](../WINDOWS_REPRODUCTION_GUIDE.md).
For which files to submit see [`../README.md`](../README.md).

---

## Pipeline order

These modules must run in this order. Each consumes the previous stage's output.

| # | Module | Input | Output |
|---|---|---|---|
| 0 | `remap_manifest_paths.py` | `manifests/` | same files, paths rewritten to your root |
| 1 | `prepare_data.py` | `data/ROF/images` | `work/rof_manifest_raw.csv` |
| 2 | `create_person_disjoint_split.py` | `work/rof_manifest_raw.csv` | `work/rof_manifest_person_disjoint.csv` |
| 3 | `create_crop_input.py` | `work/rof_manifest_person_disjoint.csv` | `work/rof_manifest_crop_input.csv` |
| 4 | `generate_periocular_mediapipe.py` | `work/rof_manifest_crop_input.csv` | `work/crop_manifest_person_disjoint.csv` + `work/periocular_person_disjoint/` |
| 5 | `build_training_manifest.py` | `work/crop_manifest_person_disjoint.csv` | `work/crop_manifest_training_person_disjoint.csv` |
| 6 | `freeze_rof_protocol.py` | training manifest | `work/protocol_v2/rof_{masked,sunglasses}_pairs.csv` |
| 7 | `train.py` | training manifest | `work/seed_sweep/checkpoints/seed{S}_{variant}.pt` |
| 8 | `evaluate_rof_protocol.py` | checkpoint + pair list | `work/seed_sweep/results/seed{S}_{variant}_{cond}_*` |
| 9 | `compare_rof_models.py` | two raw-score files | paired comparison JSON with bootstrap CI |

`../run_seed_sweep.py` drives steps 7-9 for all seeds and variants.

### Step 0 is mandatory

Every manifest in `manifests/` was produced on the machine that ran the study and
contains absolute paths from it. Nothing downstream works until they are
rewritten:

```powershell
python .\code\remap_manifest_paths.py --root . --dry-run
python .\code\remap_manifest_paths.py --root . --in-place
```

It rewrites every column whose name contains `path` and preserves the structure
after `data\` and `work\`. It also normalises the leftover `/kaggle/` prefix in
the raw MFR2 pair file.

---

## Key invariants

**Person-disjointness.** Steps 2-3 merge the `..._wearing_mask` and
`..._wearing_sunglasses` identity folders of one person into a single
`person_id`, then split *by person*. No person may appear in more than one of
train / val / test. The split is 128 / 27 / 28 persons; after the complete-case
filter the training manifest holds 128 / 26 / 28.

**Training classes collapse per person.** `build_training_manifest.py` sets
`identity = person_id`. Without this, a person's neutral, masked and sunglasses
images would be three unrelated classes and the person-disjoint protocol would
be undermined.

**No face-image substitution for crops.** `generate_periocular_mediapipe.py`
never writes a whole-face image into `peri_path`. Failed MediaPipe detections
get an empty `peri_path` with `crop_status=failed` and a
`crop_failure_reason`. 457 of 7,752 rows failed; the complete-case filter then
keeps the 7,295 valid rows.

**Crop margin.** The reported results used `--margin 0.20`. The script default
is `0.35`, so pass the flag explicitly.

**Determinism.** Steps 2 and 5 are seeded (`SEED = 42`) and regenerate
byte-identical manifests. Both were verified by SHA-256 against the shipped
copies.

---

## Model variants

`model.py` defines the five ablation variants used throughout:

| Variant | Description |
|---|---|
| `frozen_whole` | Whole-image DINOv2, fully frozen |
| `whole_lora` | Whole image + LoRA adapters |
| `peri_lora` | Periocular crop + LoRA adapters |
| `fixed_fusion` | Fixed (unweighted) whole + periocular fusion |
| `gated_fusion` | Learned gated fusion (best) |

Training configuration held constant across all variants and seeds:
`--epochs 5 --batch-size 16 --lr 1e-4 --num-workers 0`, seeds `123, 7, 42`.

---

## Cross-dataset evaluation

| Module | Role |
|---|---|
| `prepare_mfr2_protocol.py` | Map MFR2 official pairs to local crop paths, emit the 820-pair complete-case protocol |
| `prepare_rmfrd_protocol_v2.py` | Build the RMFRD v2 protocol (22,554 pairs) |
| `audit_rmfrd.py` | RMFRD duplicate-path / quality-metadata audit |
| `evaluate_all_cross_dataset_fixed.py` | Runs every seed-sweep checkpoint on MFR2 + RMFRD + neutral |

**All MFR2 and RMFRD numbers in the manuscript come from
`evaluate_all_cross_dataset_fixed.py`.** There is no second MFR2 or RMFRD
evaluator in this bundle, so there is no ambiguity about which produced
`tab:mfr2` and `tab:rmfrd`.

That evaluator computes its own identity-level bootstrap intervals
(`auc_ci_low`, `auc_ci_high`, ...), so no separate CI script is required. The
manuscript reports MFR2 and RMFRD as mean +/- std over the three training seeds
rather than as paired comparisons, which is why only `compare_rof_models.py`
exists for the ROF contrasts.

`evaluate_all_cross_dataset_fixed.py --root <folder>` requires `--root` to be the
folder containing `work/seed_sweep/checkpoints/`, and it must be the same root
passed to `remap_manifest_paths.py`.

MFR2's official `pairs.txt` is preserved as-is; the pair list is never rebuilt
randomly, because that would change the protocol.

---

## Verification

Two tools, in increasing order of cost.

**`verify_results.py` - no dataset, no GPU, no checkpoints.** Recomputes every
headline value in the manuscript directly from the shipped metric JSON files and
prints PASS/FAIL per claim. This is the fastest way to confirm the release
matches the paper.

```powershell
python .\code\verify_results.py
```

**`verification.py` - metric smoke test.** The positive-control AUC should be
near 1.0 and random scores near 0.5. Needs no dataset.

```powershell
python .\code\verification.py
```
