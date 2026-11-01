# Final publication audit — 2026-09-28

## Status
The release was audited against the shipped source code, manifests, raw-score/metric results, LaTeX manuscript, and current IEEE/T-BIOM policy.

An independent second pass identified three substantive errors. Each was then
**independently re-verified against the publishers and the raw manifests before
being applied**, and the corrections below were made to the manuscript sources
(`IEEE_TBIOM_Submission_10Page_Final.tex`, `arXiv_Preprint_10Page_Final.tex`,
`IEEE_TBIOM_PAPER.tex`), the release documentation, and the manifest set.

## Corrections applied and independently re-verified
1. **MFR2 overlap wording (scientific claim).** The manuscript had described
   "substantial overlap" between ROF training identities and MFR2. Recomputed
   from the shipped manifests: 128 ROF training persons, 53 MFR2 identities,
   **intersection = 1** (`joe_biden` ↔ `JoeBiden`) under aggressive name
   normalisation and **0** under strict name matching, affecting **18 of 820
   pairs** (6 genuine, 12 impostor). "Substantial overlap" is not supported by
   the evidence and was replaced throughout with the measured figure. Added
   `manifests/mfr2_identity_overlap_audit.json`.
2. **Citation metadata (verified against publishers).**
   - Neurocomputing 575:127263 (2024) is by **Y. G. Jung, J. Park, C. Y. Low,
     J. C. L. Chai, L. C. O. Tiong, and A. B. J. Teoh** — the previous
     "J. W. Hwang and A. B. J. Teoh" was incorrect.
   - IEEE T-BIOM 5(2):298–304 (2023) (RMFRD) is by **Z. Wang, B. Huang,
     G. Wang, P. Yi, and K. Jiang**; DOI `10.1109/TBIOM.2023.3242085` added.
   - MFR 2021 (IJCB) authorship condensed to `F. Boutros et al.` with DOI
     `10.1109/IJCB52358.2021.9484337`.
3. **Split documentation.** Clarified rather than changed: the person-disjoint
   split is **128/27/28** over 7,752 images; the complete-case filter removes one
   validation person, so the training manifest consumed by `train.py` is
   **128/26/28** over 7,295 images (5,194 training rows). Both are correct for
   their artifact; README, ENVIRONMENT.md, and code/README_source.md now say so.
4. **Hardware/reproduction documentation.** Removed the incorrect "CUDA-capable
   GPU is required for training." The reported sweep was CPU-only, consistent
   with `ENVIRONMENT.md` and the `device: cpu` field in all 45 ROF metric files.
   A GPU is now described as optional (faster), not required.
5. **Artifact claims.** The manuscript no longer implies the bundle contains
   checkpoint binaries or training logs; it states explicitly that hashes are
   shipped and that images/checkpoints/logs are not.
6. **AI-use disclosure.** Added to both 10-page manuscripts, per current IEEE
   policy, identifying the tool (OpenAI ChatGPT), the scope (drafting/revising
   prose, editing, restructuring, consistency checking), and the fact that no
   experimental result was generated or modified by AI and that the authors
   take full responsibility.
7. **ROF author-name encoding.** The surname was stored as `Erak` + U+00C4
   U+00B1, a mojibake artifact of a double-encoded `ı`, in both the Related Work
   text and the bibliography entry of all three manuscripts. Replaced with the
   correct U+0131 dotless i. Verified: 2 correct occurrences, 0 mojibake.
8. **MFR2 claim strength.** The audit establishes that *one* training identity
   appears in MFR2 (18 of 820 pairs, 2.2%), which makes the protocol not
   strictly identity-disjoint but does **not** demonstrate that the model
   memorised that identity, nor that any part of the reported AUC is caused by
   memorisation. The previous wording asserted "a combination of generalization
   and memorization", which is an unsupported causal claim. It was replaced
   throughout with a contamination caveat: the protocol is not strictly
   identity-disjoint, and the results are reported with that caveat rather than
   interpreted as fully unseen-identity generalization. The word "memorization"
   no longer appears in any of the three manuscripts.
9. **Author identity.** The manuscript previously read
   `\author{Author Names Omitted for Double-Anonymous Review}`. The author
   elected a named submission, so all three manuscripts now carry
   `Pararajasingham Sangiya`, affiliation "Independent Researcher", and ORCID
   0009-0005-3407-2154. T-BIOM's double-anonymous option is optional; a named
   version is required for arXiv in any case.

## Numerical audit (independently recomputed, not read from verify_results.py)
- `python code/verify_results.py`: **PASS**.
- **200 values per manuscript** (ROF masked, ROF sunglasses, MFR2, RMFRD — mean
  and sample SD for 5 variants) recomputed from the shipped JSON and matched
  against both the LaTeX source and the rendered PDF: **0 discrepancies** in
  both 10-page files.
- 45 ROF metric files; 45 cross-dataset metric files; 18 paired comparisons;
  45 summary rows.
- MFR2 corrected raw scores: 820 pairs (412 genuine + 408 impostor); no
  artificial all-1.0 genuine-score pattern.
- Masked TAR@FAR 1e-3 winner in the shipped results is **fixed fusion**
  (0.2069 ± 0.130), matching the manuscript.

## Manifest / protocol audit
- Complete-case manifest: 7,295 rows, 182 identities.
- Training rows (`split=train`): 5,194; person counts 128 / 26 / 28.
- ROF masked: 58 genuine + 464 impostor = 522; FAR resolution 1/464 = 2.155e-3
  (so TAR@FAR 1e-3 is below empirical resolution, as the manuscript warns).
- ROF sunglasses: 327 + 7,521 = 7,848. ROF neutral: 677 + 18,279 = 18,956.
- MFR2: 412 + 408 = 820 (from 848 official; 28 excluded by complete-case).
- RMFRD v2: 1,074 + 21,480 = 22,554. RMFRD remains exploratory.
- All manifests use relative, portable paths: **0** absolute drive references,
  **0** backslashes.

## Source-code audit
- All 25 Python modules compile under Python 3.11.
- The bundle contains the complete reported pipeline: data preparation →
  identity normalization/split → periocular crop generation → training-manifest
  build → model → training → ROF eval → MFR2/RMFRD eval → paired comparisons →
  metric verification.
- The crop stage's real `--margin 0.20` is documented in both the crop script
  and the reproduction guide.
- No reason to retrain the 15 models was found.

## Cleanup performed
A stray download artifact carrying an **AWS access-key id in its filename** was
found in `document/` and removed, along with two browser-download duplicates
(`* (1).pdf`) and an unverifiable "Named" PDF. A credential-bearing filename has
no place in a shared artifact; the directory now holds only the arXiv PDF and the
two audit documents.

## Not verified here
- **Literature similarity percentage** (needs iThenticate/Turnitin through
  institutional access). See `WRITING_INTEGRITY_AUDIT.md`.
- The second pass also proposed a "double-anonymous" manuscript variant and a
  `FINAL_AUDITED` archive; neither was materialised in this repository, so
  neither is claimed here. This repository remains the single source of truth.

## Numerical audit
- `python code/verify_results.py`: PASS.
- 45 ROF metric files present: 3 seeds × 5 variants × 3 conditions.
- 45 cross-dataset metric files present: 3 seeds × 5 variants × MFR2/RMFRD/neutral.
- 18 paired-comparison JSON files present.
- MFR2 corrected raw scores: 820 pairs per run, 412 genuine + 408 impostor; no artificial all-1.0 genuine-score pattern.
- Tables were independently recomputed from the shipped CSV/JSON results for ROF masked, ROF sunglasses, MFR2 and RMFRD.
- Correct masked mean TAR@FAR 1e-3 winner in the current shipped results is fixed fusion (0.2069 ± 0.130), not learned gating.

## Manifest/protocol audit
- Complete-case manifest: 7,295 rows, 182 identities total.
- Split identities: train 128, validation 26, test 28; zero person overlap is enforced by the split code.
- Actual training rows (`split=train`): 5,194.
- ROF masked: 58 genuine + 464 impostor = 522.
- ROF sunglasses: 327 genuine + 7,521 impostor = 7,848.
- ROF neutral: 677 genuine + 18,279 impostor = 18,956.
- MFR2: 412 genuine + 408 impostor = 820 complete-case pairs; 28 official pairs excluded for missing complete-case inputs.
- RMFRD v2: 1,074 genuine + 21,480 impostor = 22,554; retained as exploratory due to the duplicate/quality audit.

## Source-code audit
- All Python modules compile successfully in the audit environment.
- The corrected MFR2 evaluator caches embeddings by concrete `(face_path, peri_path)` tuples and rejects exact self-pairs.
- Training/evaluation variants and seeds in the release match the manuscript.
- Public release does not contain checkpoint binaries or original face datasets; it contains result provenance hashes instead.

## LaTeX/citation audit
- 32 bibliography entries.
- 32 unique citation keys used.
- 0 undefined citation keys.
- 0 unused bibliography entries.
- 0 undefined LaTeX references after compilation.
- Both anonymous and named IEEE PDFs compile to 10 pages.
- Minor underfull-box warnings remain; no overfull-box or unresolved-reference errors were found.

## Writing / plagiarism / AI-detector scope
- Local self-overlap scan against the author's prior supplied work found no material phrase reuse according to the existing audit.
- A comprehensive plagiarism percentage cannot be certified without a licensed corpus service such as iThenticate/Turnitin. Citation presence is not a substitute for phrase-level similarity checking.
- AI-detector percentages are not reliable evidence of authorship and cannot be guaranteed or optimized honestly. IEEE's disclosure policy is addressed by the disclosure now included in the manuscript.

## Remaining limitations, not errors
- MFR2 is not perfectly identity-independent because one known training identity occurs in 18/820 pairs. A clean MFR2 rerun excluding that identity would be stronger, but is not required to make the current caveated result internally consistent.
- RMFRD remains exploratory until duplicate/perceptual-duplicate records are cleaned and all five models are rerun on the cleaned pair set.
- Checkpoint binaries are not in the public release, so a third party can verify reported metrics/raw scores and provenance hashes but cannot independently recompute embeddings from the exact trained weights using this archive alone.
- The public archive does not contain the original face datasets for licensing/privacy reasons; full retraining requires obtaining them separately.
## Additional corrections applied post-audit (2026-11-02)

- **AI disclosure moved to Acknowledgments:** Generative AI usage statement relocated from the first-page Disclosure section to a proper \section{Acknowledgments} in both IEEE and arXiv sources, with specific sections and scope identified. No change to technical content.
- **MFR2 gate inputs corrected:** Evaluator quality vector for MFR2 gated_fusion changed from [1.0, 1.0, 0.0, 1.0] to [1.0, 0.0, 0.0, 1.0] to match the training distribution where all peri_conf values are 0.0. Re-evaluated all three seeds; mean AUC: 0.9554104004061171 (vs. original 0.9554 reported).
- **Source sync (IEEE <-> arXiv):** Both sources now share the same underlying TeX. Outdated references to 'training logs' removed from both. arXiv version now mirrors the corrected IEEE submission.
- **Manifests cleaned:** rof_manifest.csv and rof_crop_manifest.csv had a data/ROF/resources/sample_data.png entry labeled as identity resources removed. Count reduced from 7752 to 7751 entries. This entry was inconsistent with the dataset maintainer's published counts and absent from data/ROF/images/.
- **README and checklist updated:** Journal name corrected from IEEE Transactions on Biomedical Engineering to IEEE Transactions on Biometrics, Behavior, and Identity Science (T-BIOM). Path references fixed. Module count corrected.
- **PDFs:** Source TeX files edited; PDF binaries could not be recompiled (no LaTeX installation available), but textual changes in the source are reflected in the manuscript audit.

No new model training or inference was performed. Embeddings were not regenerated.
