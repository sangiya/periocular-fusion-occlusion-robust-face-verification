# Dataset source trace - 15 November 2026

The author reports obtaining existing datasets through GitHub and Kaggle. The local documents below support specific source and execution-copy identifiers. They do not establish a complete chain of image-download custody or an ethics approval/exemption.

| Dataset / copy | Source identified | Local evidence | What the evidence establishes |
|---|---|---|---|
| ROF original annotations | https://github.com/ekremerakin/RealWorldOccludedFaces | `manus/data_plan/FINAL_FULL_GUIDE.md:73`; local `data/ROF/README.md:15`; `research_completion_2026-11-02/DATASET_PROVENANCE.json` | The project names the original repository; 437 local annotation files match its audited tree `c927509a039ad9e74d15705f1af99a6a7ae7d3b7`. This verifies annotations, not every reconstructed JPEG download. |
| MFR2 original dataset | https://sites.google.com/view/masktheface/mfr2-dataset | `manus/data_plan/FINAL_FULL_GUIDE.md:87` | The guide names the maintainers' dataset page and official protocol. This is a source recommendation/description, not a download receipt. |
| RMFRD original dataset | https://github.com/X-zhangyang/Real-World-Masked-Face-Dataset | `manus/data_plan/FINAL_FULL_GUIDE.md:99` | The guide names the maintainers' repository. Its current README provides labeled dataset download links and the 2023 citation. |
| ROF Kaggle execution/staging copy | `/kaggle/input/datasets/sangiyaparara/tbiom-dataset/data/data/ROF` | `manus/data_plan/KAGGLE_FULL_WORKFLOW.md:33-45` | The project workflow explicitly identifies this mounted copy. It does not prove who originally collected all images or which dataset version/terms applied. |
| MFR2 Kaggle execution copy | `/kaggle/input/datasets/sangiyaparara/research-dataset/data_plan/data/mfr2` | `manus/script_window1.txt:7328-7332` | Captured console rows show MFR2 inputs under this mount. |
| RMFRD Kaggle execution copy | `/kaggle/input/datasets/sangiyaparara/research-dataset/data_plan/data/RMFRD` | `manus/script_window1.txt:8367-8371` | Captured console rows show RMFRD inputs under this mount. |

The Kaggle page URLs inferred from the mount identifiers are `https://www.kaggle.com/datasets/sangiyaparara/tbiom-dataset` and `https://www.kaggle.com/datasets/sangiyaparara/research-dataset`. Both pages were inaccessible to the web tool during this check. Their visibility, dataset versions, stated license, publication dates and contents have not been independently confirmed. These may be staging/repackaging copies; they should not replace attribution to the original dataset creators.

## Rights and ethics evidence actually located

- The [ROF repository license](https://github.com/ekremerakin/RealWorldOccludedFaces/blob/main/LICENSE) matches a local MIT license naming the repository author. Its text concerns software and associated documentation. This record is not treated as individual subject consent or blanket permission for all underlying web photographs. The [ROF README](https://github.com/ekremerakin/RealWorldOccludedFaces) describes web-image collection.
- The [MFR2 maintainer page](https://sites.google.com/view/masktheface/mfr2-dataset) describes internet-collected celebrity/politician images. It mentions Creative Commons without identifying a specific license in the displayed page. No exact image-level permission or participant-consent record is established here.
- The [RMFRD maintainer README](https://github.com/X-zhangyang/Real-World-Masked-Face-Dataset) describes web collection and offers dataset downloads. An explicit image-use license or project-specific ethics approval was not found in the local files and source material inspected. This is an audit limit, not a conclusion that permission is absent everywhere.
- No institutional approval number, formal exemption, or participant-consent record for this project was located in the inspected documents. The author's responses identify download platforms, not a committee determination. The status remains unconfirmed; no approval, exemption or consent is inferred.

## Factual wording that the records support

"This study uses existing ROF, MFR2 and RMFRD datasets. Project workflows and captured execution paths identify Kaggle-hosted copies, while the original dataset sources are the ROF GitHub repository, the MFR2 maintainer page and the RMFRD GitHub repository. The local ROF annotation snapshot matches the audited upstream files, but a complete image-acquisition log was not available. The released artifact excludes image binaries and retains source identifiers, frozen manifests and result provenance."

This wording can support a provenance paragraph. It is not a complete IEEE ethics/consent statement. Do not add 'ethics approval was unnecessary', 'all subjects consented', or 'all images are freely licensed' without evidence. Dataset permissions and any applicable ethics-review explanation remain author responsibilities.

The scientific novelty assessment is unchanged by locating the Kaggle paths. Training is complete; this trace does not launch or require another sweep.
