"""Build a thesis-style source from the current checked journal and explanatory appendices."""
from pathlib import Path
import hashlib,json,re

ROOT=Path(__file__).resolve().parent.parent
def main():
    source=ROOT/'submission_ieee_10page/IEEE_TBIOM_Submission_10Page_Final.tex'
    text=source.read_text(encoding='utf-8')
    text=text.replace('Erak\u0131n',r'Erak{\i}n')
    abstract=text.split(r'\begin{abstract}')[1].split(r'\end{abstract}')[0].strip()
    body=r'\section{Introduction}'+text.split(r'\section{Introduction}',1)[1].split(r'\section{Acknowledgments}')[0]
    # Promote the hierarchy without changing numbered measured tables or their values.
    body=body.replace(r'\subsection{',r'\section{')
    # The original section headings are known; convert only these to chapters.
    headings=re.findall(r'^\\section\{([^}]+)\}',text,re.M)
    for name in headings:
        if name!='Acknowledgments':body=body.replace('\\section{'+name+'}', '\\chapter{'+name+'}',1)
    method_diagram=r'''
\begin{figure}[htbp]
\centering
\includegraphics[width=\textwidth]{./fig_gated_architecture.pdf}
\caption{Executed gated-fusion inference path for one image. Both crop embeddings feed the gate and the normalized mixture. The auxiliary vector is constant, and the training-only identity classifier is omitted from this inference diagram. The enrollment image is processed by the same model before cosine comparison.}
\label{fig:thesismethod}
\end{figure}
'''
    body=body.replace(r'\chapter{Method}',r'\chapter{Method}'+'\n'+method_diagram,1)
    body=body.replace('The constant auxiliary vector also changes how the method should be described.',
        r'\enlargethispage{\baselineskip}'+'\nThe constant auxiliary vector also changes how the method should be described.',1)
    bibliography=r'\begin{thebibliography}{00}'+text.split(r'\begin{thebibliography}{00}',1)[1].split(r'\end{thebibliography}')[0]+r'\end{thebibliography}'
    acknowledgment=text.split(r'\section{Acknowledgments}')[1].split(r'\bibliographystyle')[0].strip()
    intro=r'''\documentclass[12pt,a4paper,oneside]{report}
\usepackage[OT1]{fontenc}
\renewcommand{\rmdefault}{ptm}
\usepackage{amsmath,amssymb,booktabs,multirow,graphicx,subcaption,url,xcolor,threeparttable}
\usepackage[hidelinks]{hyperref}
\setlength{\textwidth}{155mm}
\setlength{\textheight}{230mm}
\setlength{\oddsidemargin}{4.6mm}
\setlength{\evensidemargin}{4.6mm}
\setlength{\topmargin}{-10mm}
\linespread{1.25}
\setlength{\emergencystretch}{3em}
\graphicspath{{../figures/}}
\newcommand{\AUC}{\operatorname{AUC}}
\newcommand{\EER}{\operatorname{EER}}
\newcommand{\TAR}{\operatorname{TAR}}
\newcommand{\FAR}{\operatorname{FAR}}
\begin{document}
\hypersetup{pageanchor=false}
\begin{titlepage}
\centering
\vspace*{12mm}
{\Large Research Thesis Draft\par}
\vspace{15mm}
{\LARGE Regional Complementarity and Learned Weighting for Occluded Face Verification: A Controlled Study\par}
\vspace{20mm}
{\Large Pararajasingham Sangiya\par}
\vspace{5mm}
Independent Researcher\par
ORCID: 0009-0005-3407-2154\par
\vfill
Prepared for author review\par
15 November 2026\par
\vspace{12mm}
\raggedright
This report presents the completed research in an extended thesis format. It is not an institution-approved thesis or a record of submission. No university, degree, supervisor, ethics approval, or examination outcome is asserted. Institution-specific front matter and formatting must be supplied before an academic submission.
\end{titlepage}
\pagenumbering{roman}
\hypersetup{pageanchor=true}
\chapter*{Abstract}
\addcontentsline{toc}{chapter}{Abstract}
'''
    front=r'''
\chapter*{Reader's Guide}
\addcontentsline{toc}{chapter}{Reader's Guide}
The central question in this research is when a periocular representation should supplement a whole-face verifier. The experiment is complete: five model configurations have been trained with three seeds and evaluated on the same frozen protocols. The report explains the resulting differences in terms of adaptation, the visible facial region, and the weights used to combine the branches.

The chapters follow the evidence from research motivation to interpretation. The first chapters establish the problem and related methods; the middle chapters define the model, datasets, training, and evaluation; the final chapters discuss the results and their limits. The appendices explain the underlying mathematics, summarize the experiment, and provide a guide to the released evidence. The measured tables are shared with the current journal manuscript, so this longer presentation does not introduce a second set of results.

The main finding is conditional. Periocular adaptation is useful under masks, but sunglasses remove the region on which it depends. A learned gate can be associated with useful branch features without providing the best rule for combining them. Threshold calibration also matters: a validation target does not guarantee the same test false-accept rate. These distinctions are important when interpreting a verification system for practical use.

\chapter*{Research Integrity and Author Review}
\addcontentsline{toc}{chapter}{Research Integrity and Author Review}
This draft is based on existing ROF, MFR2, and RMFRD data and the recorded CPU experiment. It reports no new participant recruitment or image-collection procedure. Project guides and execution logs identify GitHub dataset sources and Kaggle-hosted copies. A complete image-acquisition log was not located, and the image labels and original consent conditions have not been independently certified.

No project-specific institutional approval, formal exemption, or participant-consent record was identified in the inspected project documents. This draft does not claim that public availability establishes consent or an exemption. The author must resolve the applicable review and dataset-permission requirements before formal submission. The source-trace report distinguishes original dataset sources from Kaggle execution copies.

OpenAI ChatGPT assisted with drafting, revision, explanatory appendices, code, and checks. The author is responsible for reviewing the scientific claims, citations, measurements, and declarations. No similarity-screening certificate, authorship-detector score, degree award, or journal acceptance is claimed. This is an unsigned draft for review, not a signed originality declaration.

\tableofcontents
\listoffigures
\listoftables
\chapter*{Abbreviations and Notation}
\addcontentsline{toc}{chapter}{Abbreviations and Notation}
\begin{tabular}{lp{110mm}}
\toprule
AUC & Area under the receiver operating characteristic curve.\\
EER & Equal error rate.\\
FAR & False-accept rate among impostor comparisons.\\
TAR & True-accept rate among genuine comparisons.\\
LoRA & Low-rank adaptation of frozen encoder weights.\\
ROF & Real World Occluded Faces.\\
MFR2 & Masked Faces in the Real World for Face Recognition.\\
RMFRD & Real-world masked face recognition dataset.\\
$z_f,z_p$ & Normalized whole-face and periocular embeddings.\\
$g$ & Mixing weight assigned to the whole-face branch.\\
$\tau$ & Verification threshold fixed before a test decision.\\
$c_i$ & Multiplicity of identity $i$ in a node-resampling replicate.\\
\bottomrule
\end{tabular}
\clearpage
\pagenumbering{arabic}
'''
    appendices=r'''
\appendix
\chapter{Mathematical Foundations}
\section{Verification as a decision problem}
A verifier receives two images and produces a score. In this experiment the score is a cosine similarity between normalized embeddings. If $z_i$ and $z_j$ have unit Euclidean norm, then
\begin{equation}
s(i,j)=z_i^{\top}z_j.
\end{equation}
The score orders the evidence but does not itself decide whether to accept a claimed identity. A threshold $\tau$ gives the rule $s(i,j)\geq\tau$. Increasing the threshold usually rejects more impostor comparisons and more genuine comparisons. This trade-off is the reason a ranking metric and an operating-point metric answer different questions.

For genuine scores $\mathcal G$ and impostor scores $\mathcal I$, the empirical rates are
\begin{align}
\TAR(\tau)&=\frac{1}{|\mathcal G|}\sum_{s\in\mathcal G}\mathbf 1[s\geq\tau],\\
\FAR(\tau)&=\frac{1}{|\mathcal I|}\sum_{s\in\mathcal I}\mathbf 1[s\geq\tau].
\end{align}
The denominators are as important as the decimal rates. In the masked test protocol, one changed impostor acceptance changes FAR by $1/376$, while one changed genuine acceptance changes TAR by $1/47$. Reporting a small nominal FAR cannot overcome this finite resolution.

The ROC curve evaluates the decision at every score boundary. Its AUC can also be understood as the fraction of genuine--impostor score orderings that are correct, assigning half credit to ties. EER summarizes the crossing of false-accept and false-reject rates. Neither statistic chooses a deployment threshold independently of the test data.

\section{What low-rank adaptation changes}
For a frozen weight matrix $W_0\in\mathbb R^{d_{\rm out}\times d_{\rm in}}$, a LoRA update has the form
\begin{equation}
W=W_0+\frac{\alpha}{r}BA,
\qquad A\in\mathbb R^{r\times d_{\rm in}},\quad
B\in\mathbb R^{d_{\rm out}\times r}.
\end{equation}
The factorization introduces $r(d_{\rm in}+d_{\rm out})$ parameters for that update, instead of optimizing every entry of $W_0$. The experiment uses rank $r=8$ and scaling parameter $\alpha=16$ on attention query, key, and value projections. Projection heads and, where present, the fusion network also receive gradients.

Parameter efficiency concerns the optimized weights. The base transformer still performs its forward computation, and a two-encoder system still evaluates two image branches. A small trainable fraction is therefore not evidence of an equivalent reduction in inference time, peak memory, or energy. Those quantities require their own measurements. The nominal parameter table also includes an unused instantiated whole-face branch for the periocular-only configuration; the executed forward pass skips that branch.

\section{Why gate controls are necessary}
The training objective sends gradients through the fusion rule into both branches. Changing from fixed to learned fusion can therefore change the representation itself. Comparing two independently trained models combines these effects. It cannot, on its own, attribute the observed difference to the gate used at inference.

The same-branch controls hold the trained embeddings fixed and change only their combination. Equal weighting tests whether adaptive weights are needed at all. The validation-mean gate supplies a constant learned from validation endpoints. Permutation tests whether attaching a particular gate value to a particular image matters within the selected protocol. Individual-branch controls show what the jointly trained face and periocular representations can do separately. These are diagnostic comparisons of a trained system, not substitutes for a randomized study of all possible training procedures.

The auxiliary input is constant. A constant term in the first affine layer can be absorbed into its bias, which explains the numerical folding check. Variation in gate outputs must come from the embeddings rather than measured quality variation. A value such as $g=0.8$ consequently means a mixing coefficient; it is not an 80\% probability that the face is reliable.

\section{Calibration and dependent comparisons}
Validation calibration fixes $\tau$ using impostor comparisons from validation identities. When scores tie at the acceptance boundary, the rule excludes the boundary tie group rather than allowing more false accepts than the specified integer budget. Test scores are then evaluated at that frozen threshold. A shift in the score distribution can change test FAR even if the validation budget was satisfied exactly.

Pairs are not independent observations when one identity occurs in many comparisons. The node-resampling sensitivity analysis draws identities and weights their associated edges. Genuine edges receive the sampled multiplicity of their shared identity; impostor edges receive the product of the two endpoint multiplicities. Using the same weights for two models preserves their pairing. The result describes sensitivity to the observed identity graph and the three fitted seeds. It does not remove label error or uncertainty about an unobserved population.

\chapter{Experiment Register and Evidence Map}
\section{Completed experiment}
The completed grid contains five variants, each trained with seeds 7, 42, and 123. Every full run has five epochs and 1,380 optimizer steps. Validation is used for the specified threshold and gate-mean rules, while the final fifth-epoch model is used for evaluation. No model is selected by its test AUC. Smoke runs are isolated from the research outputs.

\begin{table}[htbp]
\centering
\caption{Mean AUC and sample seed SD in the completed experiment.}
\label{tab:thesisregister}
\begin{tabular}{llrr}
\toprule
Protocol & Variant & Mean AUC & Seed SD\\
\midrule
'''
    summary=json.loads((ROOT/'results/cpu_clean/RESULTS_SUMMARY.json').read_text())
    labels={'frozen_whole':'Frozen + projection','whole_lora':'Whole LoRA','peri_lora':'Periocular LoRA','fixed_fusion':'Fixed fusion','gated_fusion':'Learned fusion'}
    protocols={'test_masked':'ROF masked','test_sunglasses':'ROF sunglasses','test_neutral':'ROF neutral','mfr2':'MFR2 retained','rmfrd':'RMFRD exploratory'}
    for row in summary['summary']:
        appendices+=protocols[row['condition']]+' & '+labels[row['variant']]+f" & {row['auc_mean']:.6f} & {row['auc_seed_sd']:.6f}"+r'\\'+'\n'
    appendices+=r'''\bottomrule
\end{tabular}
\end{table}

\section{Connecting questions to evidence}
RQ1 is answered by the whole-face LoRA and frozen-projection comparison. Both use a face input; the relevant change is encoder adaptation. RQ2 uses the periocular-only model and its contrast with whole-face and fusion models across masks, sunglasses, and neutral faces. RQ3 uses both separately trained fixed/gated models and the same-branch inference controls. Calibration analysis adds the separate question of whether thresholds transfer from validation identities to the held-out protocol.

The tests are deliberately not collapsed into a single winning model. Selecting a method for masked ranking is different from selecting one for neutral ranking or threshold transfer. The report therefore includes unfavorable directions and the stronger unmatched SFace diagnostic. That comparison helps set the scope of the claim, while its different pretraining and alignment prevent a controlled architecture conclusion.

\section{Where each claim can be checked}
The artifact's results/cpu\_clean directory contains the fifteen evaluation reports, final training records, and 120 raw-score files. Each report records eight protocols, input hashes, checkpoint hashes, metrics, calibration counts, and gate controls where applicable. The summary contains 25 condition--variant rows and ten paired mean-AUC comparisons. The frozen training and ROF pair manifests are under manifests/cpu\_followup; the retained external pair lists are under manifests/cleaned.

The executed source snapshots are under reproduction/research\_completion\_2026-11-02. The standard-library verifier can reconstruct score-level metrics and calibrated counts without images or torch. Embedding regeneration needs the licensed image/crop inputs and model weights, which are not distributed in the artifact. Hashes identify binaries but do not reconstruct them.

\chapter{Dataset Provenance and Submission Status}
\section{Sources and execution copies}
The original source identifiers are the ROF repository at \url{https://github.com/ekremerakin/RealWorldOccludedFaces}, the MFR2 maintainer page at \url{https://sites.google.com/view/masktheface/mfr2-dataset}, and the RMFRD repository at \url{https://github.com/X-zhangyang/Real-World-Masked-Face-Dataset}. Project workflows identify a Kaggle package named sangiyaparara/tbiom-dataset. Captured MFR2 and RMFRD run paths identify a second package named sangiyaparara/research-dataset. These are execution-copy identifiers; their presence does not establish the original acquisition dates or permissions for every image.

The ROF annotation audit matches 437 local files to the recorded upstream tree. Its scope is limited to the annotations. The local image counts differ from the maintainer's inventory, and a complete image acquisition log was not found. The source-trace document preserves the supporting local excerpts and their file hashes.

\section{Author decisions that remain}
The author reports that the work has not been submitted elsewhere. No submission has been performed by the drafting agent. An ethics/consent explanation, applicable dataset permissions, correspondence details, and any earlier public thesis or preprint version still require confirmation. Downloading an existing dataset is evidence about acquisition, not a substitute for those declarations.

The scientific contribution also needs author assessment against the intended venue. The experiment is reproducible at score level and distinguishes useful regional information from successful adaptive weighting. It does not establish a state-of-the-art result. Stronger claims require matched modern baselines, broader independent identities, and semantic label review. These limitations should be resolved or explained, rather than removed to make the document sound more conclusive.

Institution-specific title pages, approval pages, supervisor details, degree wording, and formatting are deliberately not invented. This report can be adapted when the actual university template is provided. The journal manuscript remains a separate ten-page document, and the research result files are shared between the two presentations.
'''
    thesis=intro+abstract+'\n'+front+body+'\n'+appendices+'\n'+r'\chapter*{Acknowledgments}'+'\n'+acknowledgment+'\n'+bibliography+'\n'+r'\end{document}'+'\n'
    folder=ROOT/'document/thesis';folder.mkdir(exist_ok=True)
    target=folder/'Research_Thesis_Draft.tex';target.write_text(thesis,encoding='utf-8')
    # Markdown companion is an editable review document with linked definitive evidence.
    outline='''# Research thesis draft

Author: Pararajasingham Sangiya. Independent Researcher. ORCID: 0009-0005-3407-2154.

This is an extended research thesis draft, not an approved university thesis. The PDF and TeX source contain the current journal chapters, explanatory mathematical appendices, the complete experiment register, and source/submission limitations. No institution, degree, supervisor, ethics approval, or signature is invented.

## Abstract

'''+abstract.replace('$','').replace(r'\pm','+/-')+'''

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
'''
    (folder/'README.md').write_text(outline,encoding='utf-8')
    provenance={'date':'2026-11-15','journal_source':source.relative_to(ROOT).as_posix(),
        'journal_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'summary_sha256':hashlib.sha256((ROOT/'results/cpu_clean/RESULTS_SUMMARY.json').read_bytes()).hexdigest(),
        'thesis_source_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
        'new_experiments':False,'institutional_approval_claimed':False,'measured_tables_shared_with_journal':True,
        'method_diagram_sha256':hashlib.sha256((folder/'fig_gated_architecture.pdf').read_bytes()).hexdigest()}
    (folder/'THESIS_SOURCE_RECORD.json').write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8')
    print('Prepared extended thesis source, review guide, and evidence bindings.')

if __name__=='__main__':main()
