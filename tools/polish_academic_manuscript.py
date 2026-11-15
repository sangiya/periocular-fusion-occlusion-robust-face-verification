"""Revise academic prose while preserving the completed experimental evidence."""
from pathlib import Path
import hashlib,json,re,shutil

ROOT=Path(__file__).resolve().parent.parent
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    if (ROOT/'results/shared_crop_sface/REPORT.json').exists():
        raise SystemExit('This editorial template predates the scientific strengthening revision. Edit the current TeX sources; do not overwrite the new controls and literature positioning.')
    source=ROOT/'submission_ieee_10page/IEEE_TBIOM_Submission_10Page_Final.tex'
    history=ROOT/'document/history/before_academic_writing_revision'
    if not history.exists():
        history.mkdir(parents=True)
        for p in [source,source.with_suffix('.pdf'),ROOT/'document/arXiv_Preprint_10Page_Final.tex',ROOT/'document/arXiv_Preprint_10Page_Final.pdf']:
            shutil.copy2(p,history/p.name)
    original=source.read_text(encoding='utf-8')
    tex=original
    def replace_section(start,end,text):
        nonlocal tex
        a=tex.index(start);b=tex.index(end,a+len(start));tex=tex[:a]+text.rstrip()+'\n\n'+tex[b:]
    replace_section(r'\begin{abstract}',r'\end{abstract}',r'''\begin{abstract}
Masks and sunglasses remove different sources of facial identity information, making it unclear when a periocular representation should complement a whole-face model. We study this question using DINOv2, low-rank adaptation (LoRA), and five configurations ranging from a frozen encoder with a trained projection to dual-branch learned fusion. Fifteen models are trained for five complete epochs on CPU using three seeds and a 6,171-image ROF manifest that excludes known content conflicts. Periocular LoRA achieves the highest masked ROC-AUC (0.9221$\pm$0.0046), fixed fusion leads on sunglasses (0.8950$\pm$0.0021), and learned fusion leads on neutral faces (0.9458$\pm$0.0026). After excluding a known training-name overlap, learned fusion achieves 0.9548$\pm$0.0022 on 802 MFR2 pairs. Fixed fusion leads on 21,798 exact-conflict-excluded RMFRD pairs (0.7240$\pm$0.0099). Controls that retain the same trained branches show that image-dependent gate weights do not consistently improve on constant weights. Validation-calibrated thresholds also reveal false-accept shifts that retrospective ROC summaries conceal. A separate SFace diagnostic achieves higher AUC under different pretraining and alignment. The results support condition-dependent regional complementarity, while showing why neither the presence of a learned gate nor a high AUC alone establishes reliable verification under occlusion.''')
    replace_section(r'\section{Introduction}',r'\section{Related Work}',r'''\section{Introduction}
Face verification asks whether two images depict the same person. A model must make that decision even when the visible evidence differs between enrollment and use. Masks remove much of the lower face, whereas sunglasses obscure the eyes and surrounding skin. A representation that works well for one occlusion can therefore lose information under the other. This matters most when a verifier must control false accepts, rather than merely rank genuine pairs above impostor pairs on average.

The periocular region offers a useful example of this trade-off. It preserves upper-face detail when a mask covers the mouth and nose, but discards other facial cues that remain useful on neutral images. Sunglasses pose a more direct problem because they obscure the region itself. Combining periocular and whole-face representations is consequently plausible, but an additional branch does not by itself establish that a learned fusion rule improves the decision.

We examine this question with DINOv2 \cite{dinov2} and LoRA \cite{lora}. The study compares a frozen whole-face encoder with a trained projection, whole-face LoRA, periocular LoRA, equal-weight dual-branch fusion, and embedding-conditioned learned fusion. All five configurations use the same frozen verification pairs. Each is trained independently with three seeds, and the completed results are traced to saved raw scores and source signatures. The goal is to determine which part of the system explains an observed improvement: adaptation, access to a second region, or the fusion rule applied to those regions.

This distinction is important because separately trained fixed and gated models differ in their learned branch features as well as their final weights. We therefore evaluate each gated checkpoint with alternative weights while retaining its branches. These controls reveal a result that the five-model comparison alone would miss: equal weighting of the gated model's own branches performs better than its learned weights on masked ROF. The analysis separates a useful representation from an effective inference policy, without assuming that the two necessarily improve together.

The experimental protocol also addresses known weaknesses in the historical data. An exact image conflict crossed the training--validation boundary, and a near-identical photograph appeared under different labels across training and test. Both were excluded before the new training runs. The external protocols exclude the known MFR2 training-name overlap and recorded RMFRD cross-label content conflicts. These corrections remove specific defects; they do not certify every semantic label or establish independence from backbone pretraining.

The contribution is a controlled empirical account of regional adaptation and fusion, supported by content-audited inputs, repeated training, same-branch controls, and validation-threshold transfer. Periocular LoRA is strongest under masks, while fixed and learned fusion lead on different remaining protocols. The paper reports these differences together with their limits. Its conclusions distinguish ranking performance, threshold transfer, and evidence for the learned weighting policy.''')
    replace_section(r'\section{Research Questions and Hypotheses}',r'\section{Method}',r'''\section{Research Questions and Hypotheses}
The experiments address three questions. RQ1 asks how much identity-supervised LoRA adaptation adds to a frozen whole-face representation with a trained projection. RQ2 asks when the periocular region helps, and what is lost when the model relies on that region alone. RQ3 asks whether learned weighting improves on equal weighting and whether any improvement persists across ROF, MFR2, and RMFRD.

H1 predicts an advantage for whole-face LoRA over the frozen projection baseline. H2 predicts that periocular adaptation helps under masks but can lose information under sunglasses or on neutral faces. H3 predicts an advantage for learned fusion at selected low-FAR operating points. These hypotheses guide the ablations; the results are reported even where a predicted advantage is absent. AUC comparisons and calibration analysis answer related but distinct questions, so an AUC gain is not treated as sufficient evidence for H3.''')
    tex=tex.replace('The learned-gating system computes a scalar reliability value','The learned-fusion model computes a scalar mixing weight')
    tex=tex.replace('where $q_f$ and $q_p$ are available crop-quality descriptors. The final embedding is',
        'where $q_f$ and $q_p$ denote auxiliary descriptor slots. Their values are constant in this experiment, as discussed below. The final embedding is')
    tex=tex.replace('Auxiliary quality therefore cannot explain sample-dependent gate variation; gate distributions and constant-weight controls are therefore measured directly.',
        'Any image-dependent change in the gate must therefore arise from the branch embeddings. We examine that dependence through gate distributions and controls that replace the learned weights.')
    tex=tex.replace('The five configurations in Table~\\ref{tab:ablations} cover the frozen baseline, the adaptation effect, the periocular-only effect, fusion without gating, and the proposed learned gate.',
        'Table~\\ref{tab:ablations} separates the effects of adaptation, region selection, and fusion. M0 freezes the encoder but trains its projection; it is not an entirely untrained system.')
    tex=tex.replace('Five required configurations.','Model configurations and the comparison each supports.')
    tex=tex.replace('Proposed adaptive fusion','Learned fusion')
    tex=tex.replace('Our gate consumes branch embeddings and crop-quality descriptors to produce a scalar mixing weight, distinct from margin-adaptive losses',
        'Our gate combines branch embeddings and auxiliary input slots to produce a mixing weight. Because those slots are constant in the executed experiment, the gate is embedding-conditioned rather than demonstrably quality-aware. It differs from margin-adaptive losses')
    replace_section(r'\subsection{Adaptation and regional complementarity}',r'\subsection{AUC, calibration, and deployment}',r'''\subsection{Adaptation and regional complementarity}
Whole-face LoRA improves mean AUC over the frozen projection baseline on every test protocol, supporting the direction of H1. The gain is largest on MFR2 and masked ROF and smaller on RMFRD. This comparison establishes an effect of supervised adaptation within the present experiment. It does not show that adapting a general visual encoder is preferable to using a face-specific pretrained model.

The answer to RQ2 depends on which region remains visible. Periocular LoRA leads the masked comparison, but performs poorly under sunglasses and loses useful information on neutral faces. H2 is therefore supported in a limited sense: the upper face is an effective source of identity evidence under lower-face occlusion, but is not a sufficient representation for all three conditions. Fixed fusion is a strong baseline because it can retain information from both regions without learning a separate weighting policy.

The answer to RQ3 is less favorable to learned weighting. The gated model leads mean AUC on MFR2 and neutral ROF, but not on masks, sunglasses, or RMFRD. Several paired sensitivity intervals include zero. More importantly, the same-branch controls show that its inference rule is not consistently responsible for the quality of its representation. Equal weights improve masked AUC for the trained gated branches, and a constant validation-mean weight remains competitive on ROF. The evidence does not support treating a learned gate as an automatic improvement in robustness.''')
    replace_section(r'\subsection{Positioning and negative findings}',r'\section{Limitations and Threats to Validity}',r'''\subsection{Positioning and negative findings}
Face--periocular fusion, LoRA, and quality-dependent weighting all have established precedents. The scientific value of this experiment lies in testing their roles separately and reporting where the expected benefit fails. In particular, a favorable comparison between two jointly trained systems is not enough to attribute the difference to adaptive weighting. The same-branch controls provide a more direct diagnostic of that inference policy.

The SFace results set a further boundary on the contribution. They show that a face-specific pretrained model can obtain stronger ranking performance on these protocols, although different training data and alignment prevent a matched architecture comparison. The present study should therefore be read as an ablation and reproducibility study. Claims of competitive face recognition would require matched baselines, a broader identity sample, and independent label checks.

The constant auxiliary vector also changes how the method should be described. The architecture accepts descriptor inputs, but this experiment supplies no varying quality measurement. The gate can react to its embeddings; it cannot demonstrate the value of measured quality cues. A future quality-aware study would need validated descriptors and controlled descriptor ablations, with its evaluation rule fixed before the test results are inspected.''')
    replace_section(r'\section{Conclusion}',r'\section{Acknowledgments}',r'''\section{Conclusion}
This study compared five parameter-efficient whole-face and periocular configurations using fifteen newly trained CPU models. No configuration led every condition. Periocular LoRA achieved the highest masked mean AUC (0.9221), fixed fusion led sunglasses (0.8950) and exploratory RMFRD (0.7240), and learned fusion led neutral ROF (0.9458) and retained MFR2 (0.9548).

The controls explain why those rankings need careful interpretation. A learned model can acquire useful branch representations without learning the best weights for combining them. Constant weighting can remain competitive, and validation-calibrated thresholds can produce a different test FAR from the intended target. Regional complementarity is supported by the evidence; universal adaptive robustness and deployment security are not.

The released scores, frozen protocols, and execution records make the reported experiment auditable. Broader independent identities, matched face-specific baselines, semantic label review, and a resolved ethics and permissions statement remain necessary for stronger claims and submission clearance.''')
    # Numeric result-table rows are immutable under this editorial pass.
    labels=['rofmasked','rofsunglasses','rofneutral','mfr2','rmfrd','calibration','gatecontrols','gatedistribution','sface','paired']
    for label in labels:
        marker='\\label{tab:'+label+'}'
        before=original.split(marker)[1].split('\\end{table}')[0]
        after=tex.split(marker)[1].split('\\end{table}')[0]
        assert before==after,('Editorial pass changed measured table',label)
    assert set(re.findall(r'\\bibitem\{([^}]+)\}',tex))==set(re.findall(r'\\bibitem\{([^}]+)\}',original))
    source.write_text(tex,encoding='utf-8')
    preprint=tex.replace(r'\graphicspath{{./}}',r'\graphicspath{{../submission_ieee_10page/}}')
    preprint=preprint.replace(r'\maketitle',r'\maketitle'+'\n'+r'\noindent\textit{Preprint prepared for scholarly dissemination.}\par')
    (ROOT/'document/arXiv_Preprint_10Page_Final.tex').write_text(preprint,encoding='utf-8')
    report={'date':'2026-11-15','purpose':'Clear, precise academic prose grounded in verified measurements',
        'revised':['Abstract','Introduction','Research Questions','Method terminology','Discussion','Conclusion'],
        'measured_table_blocks_preserved':labels,'reference_keys_preserved':len(re.findall(r'\\bibitem\{([^}]+)\}',original)),'experimental_code_modified':False,
        'ai_disclosure_retained':True,'ethics_or_permission_claims_invented':False,
        'journal_source_sha256':digest(source),'historical_source_sha256':digest(history/source.name)}
    (ROOT/'document/WRITING_REVISION_REPORT.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('Revised academic prose; ten measured table blocks and 35 reference keys preserved.')

if __name__=='__main__':main()
