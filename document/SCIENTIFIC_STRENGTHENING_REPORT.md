# Scientific strengthening report ? 16 November 2026

The paper is now titled **Regional Complementarity and Learned Weighting for Occluded Face Verification: A Controlled Study**. It is positioned as an empirical attribution study. No first-use, state-of-the-art, acceptance or submission-clearance claim is made.

The 15 original trained models and ten measured table blocks are unchanged. Additional CPU-only inference and post-hoc analyses add evidence without replacing the original stronger aligned SFace diagnostic.

| Protocol | Original aligned SFace AUC | Shared-input-crop SFace AUC |
|---|---:|---:|
| ROF masked | 0.939905 | 0.840822 |
| ROF sunglasses | 0.943978 | 0.777533 |
| ROF neutral | 0.999117 | 0.868929 |
| MFR2 retained | 0.996847 | 0.951280 |
| RMFRD exploratory | 0.818685 | 0.653181 |

The new control used the same 3,402 whole-face input files as the DINO protocols, hash-checked against the original image ledger. It resized those files to SFace native 112?112 resolution without YuNet redetection/alignment. No target fine-tuning or test-based threshold selection was performed. Eight ordered raw-score files, an image ledger, and 20 validation/test operating-point checks are included under `results/shared_crop_sface/`. All extraction failures remain in the denominator; none occurred in this run.

This controls input-file selection only. Pretraining, resolution, model architecture, normalizations and target supervision still differ. The preprocessing-pipeline change materially shifts SFace scores, so the new results cannot establish that the adapted DINO architecture is superior to a matched face-specific system. Aligned SFace remains the stronger ranking diagnostic on every reported condition.

## Masked identity influence

Each of nine masked-test identity nodes was removed in turn together with every incident genuine/impostor pair. The existing models were rescored from their raw scores; no retraining or threshold reselection occurred. Periocular LoRA led mean AUC in eight of nine subsets and fixed fusion in one. Periocular mean AUC ranged from 0.894752 to 0.944038. Gated-minus-fixed mean AUC ranged from -0.024280 to -0.002572 and was negative in every subset. The report contains all 135 per-seed subset AUCs, pair counts and input hashes.

This shows that the masked gated-versus-fixed direction is not driven by one specific identity deletion. It does not add independent subjects, remove label uncertainty, establish population significance, or repair the limited nine-identity cohort.

## Literature and contribution

The earlier relevance review checked the fit of the 35 references already present; it did not establish that the bibliography was complete. A broader search found three closer 2025/2026 works. They are now cited and compared explicitly. There are 38 references (25 directly relevant, 13 contextual), ordered by first citation. See [the novelty comparison](submission_preparation/NOVELTY_COMPARISON.md) and [reference relevance review](submission_preparation/REFERENCE_RELEVANCE_AUDIT.md).

The revised introduction distinguishes three empirical contributions: regional/adaptation comparisons under frozen protocols; same-branch controls that separate representation quality from the learned weighting rule; and threshold/preprocessing/cohort diagnostics that qualify robustness claims. CPU use is documented in experimental settings, with less prominence in the abstract and conclusion.

## Verification and limits

The standard-library verifier independently recomputes the additional eight score files, validation thresholds and accept counts, image-ledger/source hashes, and all 135 subset AUCs. The unchanged historical and 15-model experiment checks still run. No neural inference is represented as independently reproduced by arithmetic checking.

The strongest remaining gaps are broader independent masked identities, fully controlled training/pretraining comparisons, and a persuasive journal-level scientific advance against the newly cited close work. Ethics/consent, data permissions, author approval and any required licensed similarity screening remain unresolved. The new analysis improves experimental attribution; it does not make the paper automatically strong enough for T-BIOM.
