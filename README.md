# Occlusion-robust face verification - final publication release

Updated 22 November 2026. Publication files are prepared; submission, permissions clearance and acceptance are not asserted.

## Final manuscripts and LaTeX

| Target | Read | LaTeX entry point | Upload source |
| --- | --- | --- | --- |
| IEEE T-BIOM | [10-page paper](submission_ieee/IEEE_TBIOM_Paper.pdf) and [separate 3-page supplement](submission_ieee/IEEE_TBIOM_Supplement.pdf) | [main.tex](submission_ieee/main.tex), [supplement.tex](submission_ieee/supplement.tex) | [IEEE_TBIOM_Source.zip](submission_ieee/IEEE_TBIOM_Source.zip) |
| arXiv | [13-page preprint, including supporting material](submission_arxiv/arXiv_Preprint.pdf) | [main.tex](submission_arxiv/main.tex) includes [supplement_body.tex](submission_arxiv/supplement_body.tex) | [arXiv_Source.zip](submission_arxiv/arXiv_Source.zip) |

Editable IEEE Word documents, submission metadata and an unfinished cover-letter draft are in `submission_ieee/`. Corresponding-author email: asan935para@gmail.com. Use [SUBMISSION_GUIDE.txt](SUBMISSION_GUIDE.txt) for exact file selections and unresolved author fields.

arXiv does not mandate a separate supplement. This preprint includes the supporting material because the text refers to its architecture diagram, parameter table, SFace controls and provenance records. `supplement_body.tex` is a required source input for this version, not a second article or separate upload. IEEE keeps the same material in a separate PDF to respect the regular-paper limit. References are inline in the TeX; no separate BibTeX file is required by these sources.

## Final experiments

All fifteen CPU models completed five epochs: five configurations, seeds 7/42/123, 1,380 optimizer steps per model. The frozen ROF manifest has 6,171 rows: 4,405 training, 844 validation and 922 test. Retained external protocols contain 802 MFR2 pairs and 21,798 exploratory RMFRD pairs.

- `results/cpu_clean/`: 120 raw-score files, 15 evaluation reports, training records, 25 summary rows, ten paired AUC contrasts and validation-calibrated operating points.
- `results/sface/`: aligned YuNet/SFace diagnostic.
- `results/shared_crop_sface/`: separate shared-crop preprocessing control.
- `results/strengthening/`: nine masked identity-deletion sensitivity subsets.
- `manifests/cpu_followup/`: final training and ROF protocols. Its plan is the original frozen pre-training record; final completion is established by `results/cpu_clean/`.
- `manifests/cleaned/`: retained external pairs and exclusion evidence.
- Other frozen manifests document original input and cleaning provenance; they are not the current training protocol.
- `reproduction/research_completion_2026-11-02/`: byte-preserved executed CPU trainer, evaluator, coordinator, runtime and recovery tests.

Periocular LoRA leads masked mean AUC (0.922061); fixed fusion leads sunglasses (0.894972) and exploratory RMFRD (0.724015); learned fusion leads neutral (0.945826) and retained MFR2 (0.954794). Constant/permuted gate controls and the unmatched SFace diagnostics bound the interpretation. No universal robustness, state-of-the-art or population low-FAR security claim is made.

## Verify

From the repository root, Python 3.10 or newer, Windows or Linux:

```sh
python code/verify_results.py
python code/verify_completed_cpu.py
python -m unittest discover -s code/tests -v
```

The final-only verifier checks current raw-score arithmetic, alignment, thresholds, counts, summaries, all headline mean/SD cells, auxiliary tables, frozen source hashes, matching venue sources, source ZIP dependencies and compiled-PDF bindings. It uses only the Python standard library. It does not regenerate embeddings, establish semantic identity truth or grant data-use rights. Stored Windows separators are read portably without altering signed original records.

Optional independent plot checks need NumPy, Matplotlib and scikit-learn:

```sh
python tools/audit_current_figures.py
python tools/audit_paired_intervals.py
```

Regenerate current vector figures with `python code/regenerate_completed_assets.py`. Any source/figure change requires recompilation and refreshed build bindings before packaging. Package final upload sources and a deterministic release with `python tools/package_release.py`.

`run_seed_sweep.py --status` reports the recorded final grid. Reproduction of training requires licensed image/crop inputs and pretrained weights; use the exact preserved coordinator as explained in [WINDOWS_REPRODUCTION_GUIDE.md](WINDOWS_REPRODUCTION_GUIDE.md). No image or checkpoint binaries are redistributed.

## Remaining author facts

Dataset/image permissions, project ethics/consent position, funding, competing interests, final author approval, and publication/account/license choices remain unresolved. The small masked cohort, semantic labels, unknown aliases and pretraining overlap remain scientific limitations. See [current readiness](document/CURRENT_READINESS_RECHECK.md) and [dataset source records](document/DATASET_SOURCE_TRACE.md).

The active tree contains only current publication versions and current result families. Superseded papers, old sweeps and obsolete writing tools were removed; earlier versions remain recoverable through Git. `document/CLEANUP_RECORD.json` records the cleanup and an external local recovery archive. The previous untracked `verify_output.txt` is preserved locally and is not part of release archives.
