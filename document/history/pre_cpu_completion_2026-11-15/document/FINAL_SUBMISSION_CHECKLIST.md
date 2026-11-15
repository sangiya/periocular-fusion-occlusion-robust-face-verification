# Final submission checklist — revised 2 November 2026

## Completed artifact repairs

- [x] Actual corrected gated MFR2 inference, three final seeds, with raw scores and provenance.
- [x] Cleaned ROF input manifest and exclusion reasons; unsafe new training is blocked.
- [x] Exact-conflict-excluded RMFRD and known-name-overlap-excluded MFR2 protocols.
- [x] Seventy-five post-hoc sensitivity results and a manuscript sensitivity table.
- [x] Accurate threshold/FAR, bootstrap, baseline, parameter, environment, and reproduction descriptions.
- [x] AI assistance described in Acknowledgments; unsupported first-page verifier claim removed.
- [x] Vector figures and PNG previews regenerated from documented scores.
- [x] Both source documents compiled to ten-page PDFs; actual build hashes recorded.
- [x] Raw-score/table/provenance verification and regression checks passed.
- [x] Deterministic release packaging and flat arXiv source packaging; external checksum avoids self-reference.

## Required before stronger scientific claims

- [x] Reevaluate historical ROF scores after the newly confirmed cross-split near-duplicate photograph exclusion and rebuild both manuscripts with disclosure.
- [x] Complete the SFace/YuNet CPU diagnostic baseline with raw scores and validation-calibrated thresholds.
- [ ] Complete the newly launched full five-epoch, 15-model CPU training/evaluation sweep and review its gate controls.
- [ ] Train new models on the clean manifest and evaluate them as a distinct experiment.
- [ ] Resolve ROF dataset selection/version provenance and validate remaining labels/near-duplicates.
- [ ] Add matched contemporary face-recognition/fusion comparisons and substantive gate analysis.
- [ ] Obtain/inspect a licensed similarity report if available; no plagiarism percentage is certified here.
- [ ] Author reviews the revised disclosure, scientific claims, and current journal/source-format requirements.

**Status: artifact repairs and checked numerical consistency complete; journal-level scientific readiness is not certified.** Historical tables remain explicitly qualified and distinguish corrected inference from post-hoc filtering and future clean training.

## Files

- IEEE: submission_ieee_10page/IEEE_TBIOM_Submission_10Page_Final.pdf and its TeX, integrity_sensitivity.tex, and five vector figure PDFs.
- arXiv: document/arXiv_Preprint_10Page_Final.pdf and arxiv_source.zip.
- Evidence: document/VERIFICATION_REPORT.json, BUILD_REPORT.json, TEST_REPORT.json; results/corrections/; manifests/cleaned/; manifests/provenance_map.json.
- Archive checksum: external publication_release.zip.sha256. Do not paste the archive's own checksum into a file that must be inside that same archive.
