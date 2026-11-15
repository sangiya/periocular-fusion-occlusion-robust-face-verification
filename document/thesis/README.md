# Research thesis draft

Author: Pararajasingham Sangiya. Independent Researcher. ORCID: 0009-0005-3407-2154.

This is an extended research thesis draft, not an approved university thesis. The PDF and TeX source contain the current journal chapters, explanatory mathematical appendices, the complete experiment register, and source/submission limitations. No institution, degree, supervisor, ethics approval, or signature is invented.

## Abstract

Masks and sunglasses remove different sources of facial identity information, making it unclear when a periocular representation should complement a whole-face model. We study this question using DINOv2, low-rank adaptation (LoRA), and five configurations ranging from a frozen encoder with a trained projection to dual-branch learned fusion. Fifteen models are trained for five complete epochs on CPU using three seeds and a 6,171-image ROF manifest that excludes known content conflicts. Periocular LoRA achieves the highest masked ROC-AUC (0.9221+/-0.0046), fixed fusion leads on sunglasses (0.8950+/-0.0021), and learned fusion leads on neutral faces (0.9458+/-0.0026). After excluding a known training-name overlap, learned fusion achieves 0.9548+/-0.0022 on 802 MFR2 pairs. Fixed fusion leads on 21,798 exact-conflict-excluded RMFRD pairs (0.7240+/-0.0099). Controls that retain the same trained branches show that image-dependent gate weights do not consistently improve on constant weights. Validation-calibrated thresholds also reveal false-accept shifts that retrospective ROC summaries conceal. A separate SFace diagnostic achieves higher AUC under different pretraining and alignment. The results support condition-dependent regional complementarity, while showing why neither the presence of a learned gate nor a high AUC alone establishes reliable verification under occlusion.

## Review map

1. Introduction: problem, contribution, and scope.
2. Related work: face verification, occlusion, periocular representations, self-supervision, adaptation, and fusion.
3. Research questions: adaptation, regional information, and learned weighting.
4. Method: branches, fixed/learned fusion, and identity-supervised training.
5. Datasets and protocol: content exclusions, frozen pairs, calibration, and identity resampling.
6. Experimental settings: CPU training and parameter accounting.
7. Results: condition-specific metrics, calibration, controls, and SFace diagnostic.
8. Discussion: what the comparisons establish and where they remain inconclusive.
9. Limitations: labels, acquisition, sample size, overlap, and measurement scope.
10. Reproducibility: the exact evidence and source needed to audit the claims.
11. Conclusion: conditional regional complementarity.
12. Appendices: foundations, experiment register, evidence map, and provenance/submission status.

For precise numbers use [the completed results summary](../../results/cpu_clean/RESULTS_SUMMARY.md). The journal PDF and this thesis source share the same measured tables. See [the source trace](../submission_preparation/DATASET_SOURCE_TRACE.md) and [the scientific readiness review](../submission_preparation/SCIENTIFIC_READINESS_REVIEW.md) for unresolved declarations and research limitations.

AI assistance is disclosed in the report. The author must verify the text, citations, data rights and ethics statement before formal submission. University-specific formatting can be applied when its actual template and author details are available.
