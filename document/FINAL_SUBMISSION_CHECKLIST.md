# Final submission checklist

**Audit date:** 2026-09-28  
**Package audited:** `publication_release`

## Decision

**Conditionally ready for submission after the documentation corrections in this package.** The reported values, frozen protocols, result files, source-code syntax, manuscript citation wiring, and PDF page counts are internally consistent. Two release-documentation defects were corrected during this audit:

1. `README.md` referenced a non-existent `document/IEEE_TBIOM_Submission_10Page_Final.pdf`; the entry was replaced by the audit document that is actually present. The IEEE PDF remains at `submission_ieee_10page/IEEE_TBIOM_Submission_10Page_Final.pdf`.
2. `FINAL_PUBLICATION_AUDIT.md` incorrectly said “All 25 Python modules”; it now states the verifiable count: 17 modules in `code/` plus the top-level `run_seed_sweep.py`.

## Checks completed

| Area | Result | Evidence |
|---|---|---|
| Release inventory | Pass | 17 code modules, 19 manifest files, 185 result files, 5 submission figures |
| Python syntax | Pass | `python3 -m compileall -q code run_seed_sweep.py` |
| Shipped-result verifier | Pass | `python3 code/verify_results.py`; all checks passed |
| ROF metrics | Pass | 45 files = 3 seeds × 5 variants × 3 conditions |
| Cross-dataset metrics | Pass | 45 files = 3 seeds × 5 variants × MFR2/RMFRD/neutral |
| Paired comparisons | Pass | 18 files |
| PDF page count | Pass | IEEE PDF: 10 pages; arXiv PDF: 10 pages |
| Manuscript citation wiring | Pass | 32 citation keys, 32 bibliography entries, 0 undefined, 0 unused |
| Manifest portability | Pass | 0 drive-letter paths, 0 `/home/`, 0 `/kaggle/`, 0 backslashes |
| Secret/artifact scan | Pass | No suspicious credential-bearing filenames found |

## Independent numerical recomputation

The shipped pair files independently reproduce these counts:

- ROF masked: **58 genuine + 464 impostor = 522**
- ROF sunglasses: **327 genuine + 7,521 impostor = 7,848**
- ROF neutral: **677 genuine + 18,279 impostor = 18,956**
- MFR2 complete case: **412 genuine + 408 impostor = 820**
- RMFRD v2: **1,074 genuine + 21,480 impostor = 22,554**

The three-seed AUC means and sample standard deviations recomputed from JSON files match the manuscript tables, including:

- ROF masked: periocular LoRA **0.8989 ± 0.0085**, fixed fusion **0.8949 ± 0.0089**
- ROF sunglasses: learned gating **0.8998 ± 0.0049**
- ROF neutral: learned gating **0.9441 ± 0.0019**, fixed fusion **0.9424 ± 0.0025**, periocular LoRA **0.8832 ± 0.0058**
- MFR2: learned gating **0.9554 ± 0.0019**
- RMFRD: fixed fusion **0.7184 ± 0.0113**; learned gating **0.7063 ± 0.0062**

The manuscript's masked `TAR@FAR=10^-3` winner, fixed fusion **0.2069 ± 0.130**, is consistent with the shipped results. The manuscript correctly warns that 464 impostor pairs give a smallest non-zero empirical FAR increment of approximately **0.00216**, so the 0.001 operating point is below empirical resolution.

## Protocol and interpretation checks

- ROF complete-case manifest: **7,295 rows**, **182 identities**.
- Person-disjoint split documentation is consistent: initial split **128/27/28** persons; after complete-case filtering, the training manifest is **128/26/28** persons.
- MFR2 has one normalized-name overlap with a ROF training identity affecting **18/820 pairs**. The manuscript now treats it as an overlap diagnostic rather than clean unseen-identity transfer.
- RMFRD is explicitly labelled exploratory because of duplicate-path and incomplete-quality metadata limitations.
- No checkpoint binaries or original face datasets are shipped; this is accurately disclosed. Result and protocol hashes are shipped for provenance, but exact embedding recomputation from the archive alone is not possible.

## Citation and citation-graph audit

Internal citation graph checks pass in both manuscript source documents represented by the release: every in-text key maps to one bibliography entry, and every bibliography entry is cited. The source contains **32 unique cited works**. It contains **9 explicit publisher DOI strings** and **1 dataset URL**; the remaining entries use standard conference/journal bibliographic metadata without DOI links.

Authoritative external records checked during this audit include:

- ROF: Istanbul Technical University publication record confirms Erakin, Demir, Ekenel, BIOSIG 2021, and DOI `10.1109/BIOSIG52210.2021.9548293`.
- RMFRD: IEEE Biometrics publication listing confirms Wang, Huang, Wang, Yi, Jiang, 2023, pages 298–304.
- MFR 2021: arXiv `2106.15288` confirms the title, competition context, full author record, and relation to IJCB 2021; the manuscript's `F. Boutros et al.` abbreviation is appropriate for IEEE style.
- DINOv2: arXiv `2304.07193` confirms title, authors, and the 142M-data foundation-model context.
- LoRA: arXiv `2106.09685` confirms title, authors, and the frozen-base/trainable-low-rank adaptation description.
- Periocular CKD: ScienceDirect confirms the title, author list, Neurocomputing volume 575, article 127263, publication date, and DOI `10.1016/j.neucom.2024.127263`.

The package's citation graph is therefore **internally complete and key metadata is externally corroborated**. A publisher-style cited-by count for all 32 references is not frozen into the release and should not be used as a submission gate because citation counts change over time. No claim of plagiarism/similarity percentage is made; that requires institutional iThenticate/Turnitin access.

## Submission contents

Submit the IEEE folder as-is:

- `submission_ieee_10page/IEEE_TBIOM_Submission_10Page_Final.pdf`
- `submission_ieee_10page/IEEE_TBIOM_Submission_10Page_Final.tex`
- the five `fig_*.png` files in that folder

For arXiv, use `document/arXiv_Preprint_10Page_Final.pdf`. Share the code, manifests, result JSON/CSV files, `ENVIRONMENT.md`, and this audit document as the reproducibility artifact.

## Remaining reviewer-facing limitations

1. MFR2 is not perfectly identity-independent because of the measured 18-pair overlap.
2. RMFRD remains exploratory until duplicate/perceptual-duplicate records and quality metadata are resolved and the models are rerun.
3. The public archive does not contain checkpoints or datasets, so it verifies reported scores and provenance rather than independently regenerating embeddings.
4. **Resolved — LaTeX compilation verified.** The earlier caveat that no TeX engine was available has been closed. `submission_ieee_10page/IEEE_TBIOM_Submission_10Page_Final.tex` was compiled with Tectonic from a **fresh extraction of the release archive**, with no other files present, and produced exactly **10 pages**. The bibliography is inline and the five figures are flat in the same directory, so the folder is self-contained.

## Release archive

| | |
|---|---|
| File | `publication_release.zip` |
| Entries | 245 (manifests updated; resources entry removed) (note: some entries updated in manifests) files |
| SHA-256 | `2c14375d11b83f55f7fbef942bbd80a0c66ed158040bd8661500bb4d95da7bc6` |
| Size | 13.5 MB |

The archive is built **deterministically**: every entry carries a fixed
timestamp and entries are written in sorted order, so rebuilding it from the
same inputs yields byte-identical output and therefore the same hash. Verify it
with:

```powershell
Get-FileHash .\publication_release.zip -Algorithm SHA256
```

The archive excludes `.git/` internals, `__pycache__`, and any editor or
download duplicates. All entry names use forward slashes, so it extracts
correctly on Linux and macOS as well as Windows.

> Two earlier archives were discarded. One embedded 499 `.git/` entries,
> including the full commit history, and the SHA-256 quoted in that audit did
> not match the file on disk. A second was built with normal ZIP timestamps,
> which produced a different digest on every rebuild and therefore made any
> recorded hash unverifiable. The archive above is the reproducible one.

## Author and manuscript identity

The manuscripts carry the named author
(`Pararajasingham Sangiya`, Independent Researcher, ORCID 0009-0005-3407-2154),
so the same PDF is suitable for both arXiv and a non-anonymous T-BIOM
submission. A separate anonymised copy would be required only if the optional
double-anonymous review track is chosen.
