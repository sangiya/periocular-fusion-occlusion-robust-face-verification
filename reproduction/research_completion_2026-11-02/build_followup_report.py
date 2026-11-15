"""Build a labelled interim supplement from completed, score-bound experiments."""
import json
from pathlib import Path
from cpu_common import HERE,RELEASE,RUN,sha,save_json

def main():
    historical=json.loads((HERE/'archived_reevaluation/REEVALUATION_REPORT.json').read_text())
    baseline=json.loads((HERE/'sface/BASELINE_REPORT.json').read_text())
    if not baseline.get('postprocessor_sha256'):raise ValueError('Baseline precision binding incomplete')
    out=RELEASE/'document/cpu_followup';out.mkdir(exist_ok=True)
    for source,name in [(HERE/'archived_reevaluation/REEVALUATION_REPORT.json','ARCHIVED_REEVALUATION_REPORT.json'),
        (HERE/'sface/BASELINE_REPORT.json','SFACE_BASELINE_REPORT.json'),
        (HERE/'IMAGE_AUDIT.json','IMAGE_AUDIT.json'),(HERE/'DATASET_PROVENANCE.json','DATASET_PROVENANCE.json')]:
        (out/name).write_bytes(source.read_bytes())
    variants=['frozen_whole','whole_lora','peri_lora','fixed_fusion','gated_fusion']
    labels=['Frozen + projection','Whole LoRA','Periocular LoRA','Fixed fusion','Learned gating']
    table=[]
    for v,label in zip(variants,labels):
        cells=[]
        for c in ['masked','sunglasses','neutral']:
            r=next(r for r in historical['summary'] if r['variant']==v and r['condition']==c)
            cells.append(f"{r['auc_mean']:.4f} $\\pm$ {r['auc_seed_sd']:.4f}")
        table.append(label+' & '+' & '.join(cells)+r'\\')
    table.append('SFace (external pretraining) & '+' & '.join(f"{baseline['protocols']['test_'+c]['all_pairs_metrics']['auc']:.4f}" for c in ['masked','sunglasses','neutral'])+r'\\')
    operating=[]
    for c in ['masked','sunglasses','neutral']:
        x=baseline['protocols']['test_'+c];v=x['validation_calibrated']['0.01']['test']
        operating.append(c.capitalize()+f" & {x['all_pairs_metrics']['auc']:.4f} & {x['failed_pairs']} & {v['far']:.4f} & {v['tar']:.4f}"+r'\\')
    external=[]
    for c in ['mfr2','rmfrd']:
        x=baseline['protocols'][c];ci=x['identity_bootstrap_auc']['auc_ci_95']
        external.append(c.upper()+f" & {x['all_pairs_metrics']['n_pairs']} & {x['all_pairs_metrics']['auc']:.4f} & [{ci[0]:.4f}, {ci[1]:.4f}] & {x['failed_pairs']}"+r'\\')
    tex=r'''\documentclass[10pt,journal,onecolumn,compsoc]{IEEEtran}
\usepackage{booktabs,amsmath,url,hyperref}
\title{CPU Integrity Follow-up and Face-specific Baseline\\\large Interim supplement: full training sweep in progress}
\author{Pararajasingham Sangiya}
\date{2 November 2026}
\begin{document}\maketitle
\section{Status and scope}
This supplement reports completed duplicate-excluded reevaluations of 15 historical models and actual CPU inference with OpenCV SFace and YuNet. New full training on the corrected manifest has started, but its complete 15-model results are not yet available. Smoke tests are excluded from research tables. This is an interim research record, not a submission-readiness certificate.
\section{Data and protocol corrections}
A perceptual screen confirmed a near-identical photograph under different recorded labels across training and test, despite different byte hashes. Both copies were excluded from the prospective manifest. The new manifest contains 6,171 rows: 4,405 training, 844 validation and 922 test. Exact-content conflicts and repeated content had been excluded earlier. Semantic identity labels and all possible perceptual duplicates are not independently certified. All 437 local ROF annotation files match the official repository tree \texttt{c927509a039ad9e74d15705f1af99a6a7ae7d3b7}; JPEG acquisition history remains a separate provenance limitation.

Validation and test identities have separate frozen pair lists. Each eligible identity contributes a neutral enrollment image, condition-matched genuine probes and comparisons to other eligible enrollments. The test lists contain 423 masked, 6,648 sunglasses and 15,960 neutral pairs. Reusing a historical score requires exact agreement of both face/crop endpoints and the pair label. All 45 historical ROF reevaluations satisfied this requirement. This is score recomputation after exclusions, not new model training.
\section{Completed comparison}
\begin{center}
\begin{tabular}{lrrr}\toprule
Configuration & Masked AUC & Sunglasses AUC & Neutral AUC\\\midrule
'''+ '\n'.join(table)+r'''
\bottomrule\end{tabular}
\end{center}
Historical configurations show mean and sample SD across three training seeds. SFace is one fixed external pretrained checkpoint and therefore has no training-seed SD here. Both use identical frozen test pair lists, but preprocessing, pretraining and training objectives differ. Unknown celebrity overlap in external pretraining prevents a clean unseen-identity interpretation. The comparison does not establish matched-training superiority or a state-of-the-art claim. It shows that the DINOv2 ablation alone is insufficient evidence of superiority to a face-specific system.

SFace uses YuNet at confidence 0.8, the detected face closest to image centre, five-landmark alignment and cosine similarity. No target fine-tuning or manual identity selection is used. Failed-detection pairs stay in the denominator with score $-1$. Detected-only metrics are recorded separately; they do not replace the all-pair results.

\begin{center}
\begin{tabular}{lrrrr}\toprule
SFace condition & AUC & Failed pairs & Test FAR & Test TAR\\\midrule
'''+ '\n'.join(operating)+r'''
\bottomrule\end{tabular}
\end{center}
Test FAR/TAR use thresholds chosen solely on the corresponding validation protocol at target FAR 0.01. Actual test FAR is reported rather than presumed to equal the target. The masked validation protocol has only 270 impostor pairs: its first nonzero empirical FAR is $1/270$. Neither a zero count nor correlated impostor counts certify a population false-accept rate of $10^{-3}$.

\begin{center}
\begin{tabular}{lrrrr}\toprule
External SFace protocol & Pairs & AUC & Node-resampling interval & Failed pairs\\\midrule
'''+ '\n'.join(external)+r'''
\bottomrule\end{tabular}
\end{center}
MFR2 excludes the known normalized-name training overlap (802 retained pairs). RMFRD excludes known cross-identity exact-content conflicts (21,798 retained pairs). Unknown aliases, remaining labels and pretraining overlap remain limitations. Intervals use 1,000 two-endpoint identity-node resampling replicates, conditional on the fixed checkpoint and frozen protocol; they are sensitivity intervals, not deployment guarantees.
\section{New CPU experiment and gate controls}
The new sweep trains all five configurations for five complete epochs at seeds 7, 42 and 123, batch size 16, learning rate $10^{-4}$ and AdamW weight decay $10^{-4}$. No smoke batch cap is applied. Checkpoints record manifest and trainer hashes, optimizer state, sample order and Python/NumPy/PyTorch RNG states. Training and evaluation use only CPU and a locally cached DINOv2 backbone. The periocular-only run skips the unused whole-face forward pass; this new run is not claimed bit-identical to historical training.

Each completed model is evaluated on validation/test ROF and the two retained external protocols. Threshold calibration uses validation identities only. The learned gate is compared with a 0.5 gate, a validation-mean gate, a seeded permuted gate and each branch alone, all using the same learned branches. Constant auxiliary input $q=[1,0,0,1]$ can be absorbed into the first gate-layer bias, $b'=b+W_q q$; it cannot explain sample-dependent quality adaptation. Gate distributions and this equivalence check will be saved with actual completed evaluations. No pending measurement is presented as a result here.
\section{Evidence and limitations}
Raw scores, protocol lists, exclusions, source code, model hashes and image ledgers are in the accompanying CPU research bundle. Live training progress is recorded in \texttt{cpu\_runs/SWEEP\_STATUS.json}; completion requires all 15 trained and evaluated models, not a successful smoke test. The main manuscript tables remain historical and explicitly qualified. Comprehensive licensed similarity screening and author review have not been completed. AI assistance must remain disclosed; no detector score or plagiarism percentage is certified.

Official baseline sources: \url{https://github.com/opencv/opencv_zoo/tree/main/models/face_recognition_sface} and \url{https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet}.
\end{document}
'''
    (out/'CPU_Integrity_Followup.tex').write_text(tex,encoding='utf-8')
    lines=['# CPU research follow-up — interim','',
        'Full clean-manifest CPU training is running. The complete 15-model sweep is not yet finished.','',
        'Completed: 45 duplicate-excluded historical ROF score reevaluations, SFace/YuNet CPU inference on eight frozen protocols, validation-only SFace threshold calibration, and 1,000-replicate two-endpoint identity-resampling AUC sensitivity intervals.','',
        '| Protocol | SFace AUC | Failed pairs retained |','|---|---:|---:|']
    for c in ['test_masked','test_sunglasses','test_neutral','mfr2','rmfrd']:
        x=baseline['protocols'][c];lines.append(f"| {c} | {x['all_pairs_metrics']['auc']:.6f} | {x['failed_pairs']} |")
    lines+=['','SFace uses external pretraining and different alignment. Unknown pretraining identity overlap remains; these are diagnostic comparisons, not a matched-training or SOTA claim.','',
        'The main 10-page PDFs now disclose the later cross-split near-duplicate photograph. New clean-trained results remain pending.','',
        'Live progress: `manus/data_plan/research_completion_2026-11-02/cpu_runs/SWEEP_STATUS.json` and the current model progress JSON.','',
        'Raw evidence and reproducible CPU scripts are supplied in the separate `cpu_research_followup.zip` bundle. Its SHA-256 is in its external sidecar.','']
    (out/'CPU_FOLLOWUP_REPORT.md').write_text('\n'.join(lines),encoding='utf-8')
    print('Interim supplement sources and completed reports generated.')

if __name__=='__main__':main()
