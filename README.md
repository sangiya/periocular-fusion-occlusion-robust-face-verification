# Parameter-Efficient Periocular Fusion for Cross-Condition and Cross-Dataset Occlusion-Robust Face Verification

Reproduction package for the IEEE Transactions on Biometrics, Behavior, and Identity Science (T-BIOM)
submission. This bundle contains the manuscript, the full source code needed to
reproduce the reported results, the frozen evaluation protocols, and the exact
result files the paper cites.

## Research topic

**The problem.** Under a mask or sunglasses, the part of the face that
verification systems rely on is missing or visually altered. Two questions
follow. First, does adapting a large pretrained face backbone help, or is
adapting only the region that survives occlusion enough? Second, when a face
image is degraded, should the system be told how degraded it is, or should it
decide for itself?

**The approach.** A frozen DINOv2 ViT-B/14 backbone with LoRA adapters on two
branches: a whole-face branch and a landmark-cropped periocular branch. Five
configurations are compared under one identity-disjoint protocol, and the
fifth replaces fixed fusion with a learned gate that receives both branch
embeddings plus four auxiliary quality descriptors.

| | |
|---|---|
| **Task** | 1:1 face verification (genuine vs impostor), not classification |
| **Conditions** | neutral, masked, sunglasses |
| **Backbone** | `facebook/dinov2-base` (ViT-B/14, 768-d), LoRA-adapted |
| **Datasets** | ROF (train + in-domain eval), MFR2 and RMFRD (cross-dataset) |
| **Protocol** | person-disjoint split, 3 seeds (7, 42, 123), frozen pair lists |
| **Trainable cost** | 2.26 M of 175 M parameters (1.29 %) at the largest variant |
| **Hardware** | CPU only (Intel i7-13620H); 63.1 h for all 15 runs |

**What was found.** Periocular LoRA gives the best masked ranking
(AUC 0.8989) and learned gating the best sunglasses ranking (0.8998) and the best
neutral control (0.9441). The advantage is **not uniform**: gating loses to
fixed fusion on RMFRD (0.7063 vs 0.7184) and collapses at a stringent
false-accept rate on MFR2 (TAR@FAR 1e-3 of 0.0089 against 0.1246 for fixed
fusion). The paper therefore states a conditional conclusion rather than a
uniform win, and reports the conditions under which each branch wins.

**Reported limitations, stated rather than hidden.** MFR2 shares identities with
the ROF training set, so its numbers mix generalization with memorization and
are not evidence of unseen-identity transfer. RMFRD contains duplicate image
paths across nominal identities and is treated as exploratory. The quality
descriptors fed to the gate are largely constant during training, so the gate is
described as a learned fusion mechanism and **not** as a calibrated reliability
estimator. All training ran on CPU with no GPU.

> **Status:** manuscript under review. Posted as a preprint artifact; the
> headline numbers here are the ones claimed in the paper, and
> `code/verify_results.py` re-derives them from the shipped files in seconds
> without a GPU, a dataset, or a checkpoint.

---

## 1. Which files to submit and share

| File | Purpose | Use |
|---|---|---|
| `submission_ieee_10page/IEEE_TBIOM_Submission_10Page_Final.pdf` | 10-page journal submission | **Submit to IEEE** |
| `submission_ieee_10page/IEEE_TBIOM_Submission_10Page_Final.tex` | Canonical LaTeX source | **Submit with the PDF** |
| `submission_ieee_10page/fig_*.png` (5 files) | Figures referenced by the source | **Submit with the source** |
| `document/arXiv_Preprint_10Page_Final.pdf` | 10-page preprint, arXiv title page | **Post to arXiv** |
| `submission_ieee_10page/IEEE_TBIOM_Submission_10Page_Final.pdf` | Same PDF, kept next to the preprint | Convenience copy |

The IEEE PDF and the arXiv PDF are the **same 10-page manuscript** with different
title pages, so every number, table, and figure is identical between them. There
is no third, condensed version: the earlier 8-page draft was retired and removed
so that exactly one manuscript content exists.

If IEEE asks for a source package, send the contents of `submission_ieee_10page/`
as-is. It compiles standalone with Tectonic or pdfLaTeX and needs no other files
(the bibliography is inline and the figures are flat, not in subfolders).

Verify the page count:

```powershell
python -c "from pypdf import PdfReader; print(PdfReader('submission_ieee_10page/IEEE_TBIOM_Submission_10Page_Final.pdf').get_num_pages())"
```

---

## 2. Reproducing the results

Full step-by-step instructions: **[`WINDOWS_REPRODUCTION_GUIDE.md`](WINDOWS_REPRODUCTION_GUIDE.md)**

Short version:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r .\configs\requirements-used.txt
# torch 2.14.0+cpu is the CPU build and needs no extra index.
# For a GPU instead: pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# 0. (nothing to fix - manifest paths are already relative to this folder)
# 1. index, person-disjoint split, periocular crops, training manifest
python .\code\prepare_data.py --root .\data\ROF\images --out .\work\rof_manifest_raw.csv
python .\code\create_person_disjoint_split.py
python .\code\create_crop_input.py
python .\code\generate_periocular_mediapipe.py `
  --input .\work\rof_manifest_crop_input.csv `
  --output .\work\crop_manifest_person_disjoint.csv `
  --crop-dir .\work\periocular_person_disjoint `
  --margin 0.20 --size 224
python .\code\build_training_manifest.py

# 2. freeze protocols, train 3 seeds x 5 variants, evaluate, compare
python .\code\freeze_rof_protocol.py `
  --manifest .\work\crop_manifest_training_person_disjoint.csv `
  --out-dir .\work\protocol_v2 --max-impostors-per-probe 100
python .\run_seed_sweep.py

# 3. confirm the shipped results match the manuscript (no GPU needed)
python .\code\verify_results.py
```

The **reported results were produced entirely on CPU** (Intel Core i7-13620H, no
NVIDIA GPU, `torch 2.14.0+cpu`); all 45 ROF metric files record `device: cpu`.
A GPU is **not** required to reproduce this work — it is only an option for
running the 15 training runs faster. Expect roughly 63 hours on the reference
CPU; a single modern GPU cuts that substantially. A GPU is also **not** required
to check the results: `verify_results.py` runs in seconds from the shipped files.

See `ENVIRONMENT.md` for the exact hardware, package versions, and runtimes.

---

## 3. What is in this bundle

```
publication_release/
  submission_ieee_10page/   10-page IEEE .tex + PDF + 5 figures  <- SUBMIT THIS
  document/                 arXiv 10-page preprint PDF + convenience copy of the IEEE PDF
  code/                     17 Python modules, Apache-2.0
  configs/                  dependency lists (pinned lock file + GPU-runtime list)
  manifests/                18 frozen manifests and protocol files
  results/seed_sweep/       185 result files cited by the paper
  run_seed_sweep.py         multi-seed train + evaluate + compare driver
  WINDOWS_REPRODUCTION_GUIDE.md
  ENVIRONMENT.md            hardware, software versions, runtimes
  README.md, LICENSE, CITATION.cff
```

### Start here if you just want to check the numbers

```powershell
python .\code\verify_results.py
```

No dataset, no GPU, no checkpoints. It recomputes every headline value in the
manuscript from the shipped result files and prints PASS/FAIL per claim.

### Pipeline source (`code/`)

Ordered as the pipeline runs:

| Stage | Module |
|---|---|
| Path remapping (do first) | `remap_manifest_paths.py` |
| Index images | `prepare_data.py` |
| Person-disjoint split | `create_person_disjoint_split.py` |
| Crop input prep | `create_crop_input.py` |
| Periocular cropping | `generate_periocular_mediapipe.py` |
| Complete-case training manifest | `build_training_manifest.py` |
| Protocol freezing | `freeze_rof_protocol.py` |
| Model definition | `model.py` |
| Training | `train.py` |
| ROF evaluation | `evaluate_rof_protocol.py` |
| Cross-dataset evaluation (MFR2 + RMFRD + neutral) | `evaluate_all_cross_dataset_fixed.py` |
| MFR2 protocol | `prepare_mfr2_protocol.py` |
| RMFRD protocol v2 | `prepare_rmfrd_protocol_v2.py` |
| RMFRD duplicate/quality audit | `audit_rmfrd.py` |
| Paired ROF comparisons | `compare_rof_models.py` |
| Verification | `verification.py`, `verify_results.py` |

These 17 modules are the complete reported pipeline. Every number in the
manuscript is produced by exactly one of them:

- `tab:ablations`, `tab:rofmasked`, `tab:rofsunglasses` and the neutral figures
  <- `train.py` + `evaluate_rof_protocol.py`, driven by `run_seed_sweep.py`
- `tab:mfr2`, `tab:rmfrd` <- `evaluate_all_cross_dataset_fixed.py`
- the 18 paired comparisons and `seed_sweep_summary.*` <- `compare_rof_models.py`
- the ROF identity audit <- `create_person_disjoint_split.py`
- the 820-pair MFR2 protocol <- `prepare_mfr2_protocol.py`
- the 22,554-pair RMFRD protocol and its audit <- `prepare_rmfrd_protocol_v2.py`, `audit_rmfrd.py`

Superseded single-seed scripts that predate the final seed sweep were removed
rather than shipped, so there is exactly one implementation of each reported
result. See `CHANGELOG.md` Round 10 in the source archive for the audit trail.

### Manifests (`manifests/`)

**All 18 files use paths relative to this bundle's root** (`data/ROF/images/...`,
`work/periocular_person_disjoint/...`), with forward slashes. Nothing needs
editing: clone the repository, place the datasets under `data/`, and run from the
bundle root on Windows, Linux, or macOS.

If you relocate the bundle, or prefer absolute paths, `code/remap_manifest_paths.py`
can rewrite them:

```powershell
python .\code\remap_manifest_paths.py --root . --dry-run
python .\code\remap_manifest_paths.py --root . --in-place              # absolute
python .\code\remap_manifest_paths.py --root . --in-place --relative  # back to relative
```

**ROF (training + in-domain evaluation)**

| File | Rows | Contents |
|---|---|---|
| `rof_manifest.csv` | 7,752 | ROF image index; **includes `sha256` per image** |
| `rof_crop_manifest.csv` | 7,751 | Crop quality metrics (confidence, blur, visible ratio) |
| `crop_manifest_training_person_disjoint.csv` | 7,295 | **Exact training manifest** used by `train.py` |
| `rof_masked_pairs.csv` | - | Frozen ROF masked protocol |
| `rof_sunglasses_pairs.csv` | - | Frozen ROF sunglasses protocol |
| `rof_neutral_pairs.csv` | - | Frozen ROF neutral protocol |
| `rof_protocol_metadata.json` | - | Protocol freeze parameters |

**Cross-dataset**

| File | Rows | Contents |
|---|---|---|
| `mfr2_official_complete_pairs.csv` | 820 | **MFR2 protocol actually used for the reported result** |
| `mfr2_official_pairs.csv` | 848 | Raw official MFR2 pairs (provenance; still has `/kaggle/` paths) |
| `mfr2_excluded_pairs.csv` | 28 | Pairs dropped from the MFR2 protocol, with reason |
| `mfr2_pairs_local.csv` | 848 | Official pairs mapped to local paths (input to the prepare step) |
| `mfr2_crop_manifest.csv` | - | MFR2 periocular crop index |
| `mfr2_protocol_metadata.json` | - | MFR2 protocol hashes and counts |
| `rmfrd_pairs.csv` | 22,554 | **RMFRD protocol used for the reported result** |
| `rmfrd_manifest.csv` | - | RMFRD image index |
| `rmfrd_eval_images.csv` | - | RMFRD evaluation subset |
| `rmfrd_crop_manifest.csv` | - | RMFRD periocular crop index |
| `rmfrd_protocol_metadata.json` | - | RMFRD protocol parameters |

Only `rof_manifest.csv` carries per-image SHA-256 hashes. The pair lists and
`rmfrd_manifest.csv` carry paths and labels but no per-image hashes. However,
every shipped **result** file records the `checkpoint_sha256` and
`pairs_sha256` it was computed from.

> The files in `results/seed_sweep/` deliberately keep the original machine's
> absolute paths inside their `checkpoint` and `pairs` fields. Those are
> provenance: they record exactly which model and which protocol list each
> number came from, and the accompanying SHA-256 values bind them. They are left
> untouched rather than rewritten.

> Manifests contain **absolute paths from the machine that produced them**.
> Rewrite the path columns to your own dataset location before use. The
> person-disjoint split and the complete-case filter are both deterministic
> (seed 42) and regenerate byte-identical manifests once paths are corrected.

### Results (`results/seed_sweep/`)

| Path | Files | Contents |
|---|---|---|
| `rof_seed_sweep/` | 45 metrics + 45 raw scores | ROF masked / sunglasses / neutral, 3 seeds x 5 variants |
| `cross_dataset/` | 45 metrics + 30 raw scores | MFR2, RMFRD, and neutral cross-checks |
| *(top level)* | 18 comparisons + 2 summaries | Paired CIs and `seed_sweep_summary.{json,csv}` |

Headline neutral-condition mean AUC:

| Variant | Mean AUC |
|---|---|
| Gated fusion | 0.9441 |
| Fixed fusion | 0.9424 |
| Periocular | 0.8832 |

---

## 4. Datasets

The datasets are **not redistributed** here. Obtain them from their official
sources and accept the original licence terms.

| Dataset | Role |
|---|---|
| ROF | Training + masked / sunglasses / neutral evaluation |
| MFR2 | Cross-dataset verification |
| RMFRD | Cross-dataset verification |

Expected layout: `data/ROF/images/{neutral,masked,sunglasses}/<identity>/*.jpg`.
Condition folder names must match exactly; the person-disjoint split derives
`person_id` from the identity folder name.

---

## 5. Hardware used

**All reported training was performed on CPU**, on a 13th Gen Intel Core
i7-13620H (10 cores / 16 threads, 31.6 GB RAM) with **no NVIDIA GPU**
(`torch 2.14.0+cpu`, `torch.cuda.is_available() == False`). The full 15-run
sweep took 63.1 hours.

This is disclosed in full in [`ENVIRONMENT.md`](ENVIRONMENT.md), which also
records the exact package versions and per-run training times. No GPU is
required to submit, verify, or defend this work; the results, metric JSON files,
and raw score CSVs are shipped.

---

## 6. Integrity notes

Verified during packaging:

- `create_person_disjoint_split.py` regenerates `rof_manifest_person_disjoint.csv`
  byte-identically (SHA-256 match).
- `build_training_manifest.py` regenerates
  `crop_manifest_training_person_disjoint.csv` byte-identically (SHA-256 match).
- `verify_results.py` recomputes all headline values from the shipped result
  files: **all checks pass**.
- `remap_manifest_paths.py` rewrites 348,793 path cells across all 18 manifests;
  remapped against the original working tree, only **1** of those references
  fails to resolve, which confirms the manifests are internally consistent.
- Every shipped ROF result records `checkpoint_sha256` and `pairs_sha256`; both
  were re-verified against the actual checkpoint and pair files.
- All 45 ROF results record `device: cpu`.
- `submission_ieee_10page/` compiles standalone to 10 pages.
- All 17 Python modules compile under Python 3.11.
  - Person-disjointness is enforced by the split code. The split assigns
    **128 / 27 / 28** persons to train / val / test over all 7,752 images; the
    complete-case filter that follows removes one validation person whose crops
    all failed, so the **training manifest that `train.py` actually consumes**
    holds **128 / 26 / 28** persons over 7,295 images (5,194 training rows). Both
    numbers are correct for their artifact; the manuscript reports the latter.

Corrections applied for Windows portability:

- `create_person_disjoint_split.py` no longer crashes on `âˆ©` (U+2229) under the
  cp1252 console, and resolves paths relative to the script rather than the
  shell's working directory.
- `run_seed_sweep.py` locates its manifest and protocol pair files in either
  `work/` or `manifests/`, and validates them before starting.
- `generate_periocular_mediapipe.py` documents the real `--margin 0.20` used for
  the reported results (its default is 0.35).

Superseded material was **removed** rather than shipped: `run_rof_v2.ps1`,
`run_mfr2.ps1`, `run_rmfrd_v2.ps1` (they referenced single-seed checkpoint names
and scripts not present in the bundle) and `run_commands_colab.py` (hard-coded
Colab paths from a superseded run).

---

## 7. Licensing
- **Code** (`code/`, `run_seed_sweep.py`, `configs/`): Apache-2.0. See `LICENSE`
  and `code/LICENSE`.
- **Documentation and manifests** (`README.md`, `document/`,
  `submission_ieee_10page/`, `manifests/`, `results/`): CC BY 4.0.
- **Datasets**: not included; governed by their original licences.
- **Model weights**: DINOv2 weights are used through `timm`/`transformers` and
  remain subject to their original licence.

---

## 8. Citation

See `CITATION.cff`. Cite the 10-page IEEE version.
