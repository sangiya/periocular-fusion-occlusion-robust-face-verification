
- **MFR2 gate inputs**: Corrected evaluator quality vector from [1.0, 1.0, 0.0, 1.0] to [1.0, 0.0, 0.0, 1.0] to match training distribution (all peri_conf==0 in training). Re-evaluated all three seeds; mean AUC: 0.955412.
# Final publication artifact audit — 2 November 2026

See [CURRENT_READINESS_RECHECK.md](CURRENT_READINESS_RECHECK.md) for the later near-duplicate finding, checkpoint limitations, and repaired MFR2 archive inconsistency. The PDFs now disclose that later finding. A separate full CPU training sweep is in progress; completed historical reevaluations and the SFace baseline are documented in cpu_followup/CPU_FOLLOWUP_REPORT.md.

## Decision

Artifact verification passes for the checked files. This is NOT approval of the scientific protocol or a guarantee of journal acceptance. The former “unfixable in this environment” description was incorrect for PDF compilation, text editing, exclusion manifests, and corrected inference.

## Work actually completed

- Downloaded official portable Tectonic 0.17.0 into the workspace, used a workspace copy of existing cached TeX resources, and compiled both manuscripts. Each final PDF is 10 pages; no overfull boxes or unresolved references remain. Minor underfull-box warnings and a nonfatal Fontconfig message are recorded in build logs.
- Ran actual CPU inference on final gated checkpoints for training seeds 7, 42, and 123, batch size 8, 262 unique MFR2 images and 820 pairs per run. Gate inputs are [1,0,0,1]. Each result records training/bootstrap seeds, device, elapsed time, evaluator/checkpoint/pair/raw-score hashes. All three evaluations completed successfully.
- Corrected gated-MFR2 mean AUC is 0.9554123834, EER 0.1156164731, TAR at FAR 0.01 is 0.4644012945. FAR-0.001 remains descriptive only, below the empirical nonzero FAR resolution. Manuscript values/figures are regenerated from these results.
- Prepared a content-unique ROF training manifest: 6,173 rows (4,406 train, 844 validation, 923 test), with 128/26/28 labels. Removed four cross-label/split conflict rows and 1,118 repeated-content rows. No original image was deleted, relabeled, or replaced.
- Prepared identical model-independent score-exclusion protocols: ROF masked/sunglasses/neutral retain 423/6,672/15,988 pairs; known-name-overlap-excluded MFR2 retains 802; exact-conflict-excluded RMFRD retains 21,798 after excluding 756 pairs touching 36 source/crop hash-conflict groups.
- Recomputed 75 post-hoc sensitivity runs, across five models, five conditions and three seeds. These are predictions of archived models, NOT newly clean-trained results. No new confidence intervals are claimed for these subsets.
- Added clean-training orchestration with an isolated manifest-hash checkpoint directory. New training rejects repeated content, label split overlap, and mismatched/unknown-manifest resumption. A dry run completed; model training itself was NOT run.
- Replaced the former count-only verifier with independent standard-library raw-score metric/table/provenance checks. It checks 90 archived metric files, 75 archived raw-score files, 160 main-table numbers, three actual corrected runs, and 75 sensitivity runs.
- Regenerated five figures as vector PDFs plus 300-DPI PNG previews. ROC charts show only positive empirical FAR points and label their resolution; zero-FAR points are not plotted at invented positive FAR. Histograms use common bin edges and class counts; the comparison uses points and SD bars.
- Corrected threshold/conditional-bootstrap wording, M0 trained-projection and M2 nominal/active parameter descriptions, dataset count language, runtime claims, AI disclosure, broken grammar, and reproduction instructions.
- Added original-to-portable protocol provenance mapping, explicit exclusion ledgers, a flat arXiv source package, per-file release manifest, and external ZIP checksum sidecar.
- Preserved earlier audit statements and failed rerun logs under document/history/. Historical score files remain unchanged.

## Validation scope

See VERIFICATION_REPORT.json, BUILD_REPORT.json, TEST_REPORT.json and the retained logs. All released Python sources parse; metric/invalid-input regression checks pass; missing checkpoints produce a nonzero exit instead of a misleading “Done.” All 20 final PDF pages were rendered and inspected.

No claim is made that every historical bootstrap interval, real-person label, perceptual duplicate, literature claim, or third-party license has been independently validated. The explicit artifact tests do not constitute plagiarism or AI-authorship certification.

## Research limitations that remain

1. The historical ROF checkpoints were trained with the original content conflict/repetition. Removing rows from new manifests does not retrain old weights. New clean training and evaluation are still required to claim clean-trained performance.
2. The local ROF image selection differs from the maintainer's published inventory. The version/selection discrepancy remains unresolved. Historical split assignments are preserved; re-indexing/reseeding is a new protocol unless matching assignments are demonstrated.
3. Exact-conflict and known-name exclusions do not validate every remaining identity, near-duplicate, or alias. RMFRD remains exploratory, and original MFR2 results retain their overlap caveat.
4. Matched face-specialized/fusion baselines, gate analysis, and stronger external evidence are research tasks, not repaired by documentation.
5. Small/correlated impostor populations do not establish deployment FAR 0.001. Reported thresholds are retrospective ROC summaries, and one-sided bootstrap intervals are conditional.
6. Public original images and final model binaries are not included. Provenance hashes alone cannot regenerate embeddings.

## Source and package status

IEEE and arXiv share substantive source and sensitivity table content; arXiv adds a preprint line and uses a different relative figure search path. Both PDFs were actually rebuilt. arxiv_source.zip contains the main source, sensitivity table and five vector figures with local paths.

The release ZIP is deterministic for identical input files. Its SHA-256 is in publication_release.zip.sha256 outside the archive; RELEASE_MANIFEST.json hashes packaged files without a self-referential archive checksum. Old fixed hashes/counts in historical audits are superseded.

This repair does not commit, push, publish, or certify the remote repository's privacy/synchronization state.
