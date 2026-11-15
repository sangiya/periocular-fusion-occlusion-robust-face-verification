"""Promote the completed CPU experiment without altering executed source or history."""
from pathlib import Path
import csv, hashlib, json, shutil, statistics

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent / 'publication_release'
RUN = HERE / 'cpu_runs'
SEEDS = [7, 42, 123]
VARIANTS = ['frozen_whole', 'whole_lora', 'peri_lora', 'fixed_fusion', 'gated_fusion']
LABELS = ['Frozen + projection', 'Whole LoRA', 'Periocular LoRA', 'Fixed fusion', 'Learned gating']
CONDITIONS = ['test_masked', 'test_sunglasses', 'test_neutral', 'mfr2', 'rmfrd']

def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')

def main():
    summary = json.loads((RUN/'RESULTS_SUMMARY.json').read_text())
    assert summary['state'] == 'complete' and summary['completed_models'] == 15 and not summary['missing']
    records = {(s,v):json.loads((RUN/f'evaluation/seed{s}_{v}/EVALUATION_REPORT.json').read_text()) for s in SEEDS for v in VARIANTS}
    # Exact executed sources remain unchanged: signatures in the reports bind them.
    dest = ROOT/'reproduction/research_completion_2026-11-02'
    for name in ['cpu_common.py','train_cpu.py','evaluate_cpu.py','run_cpu_sweep.py','status_cpu.py',
                 'summarize_cpu_results.py','test_cpu_pipeline.py','test_cpu_evaluation.py','test_cpu_recovery.py']:
        (dest/name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(HERE/name, dest/name)
    for source, target in [(HERE/'experiment',dest/'experiment'),(RUN/'runtime',dest/'cpu_runs/runtime')]:
        for p in source.iterdir():
            if p.is_file() and p.suffix in ('.py','.csv','.json'):
                (target/p.name).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target/p.name)
    out = ROOT/'results/cpu_clean'
    for s,v in records:
        source=RUN/f'evaluation/seed{s}_{v}'
        for p in source.iterdir():
            if p.is_file() and p.suffix in ('.csv','.json'):
                target=out/'evaluation'/source.name/p.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
        target=out/'training'/f'seed{s}_{v}_progress.json';target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(RUN/'checkpoints'/target.name,target)
    for name in ['RESULTS_SUMMARY.json','RESULTS_SUMMARY.md','SWEEP_STATUS.json']:
        shutil.copy2(RUN/name,out/name)
    for p in (HERE/'experiment').glob('*.csv'):shutil.copy2(p,ROOT/'manifests/cpu_followup'/p.name)
    shutil.copy2(HERE/'experiment/EXPERIMENT_PLAN.json',ROOT/'manifests/cpu_followup/EXPERIMENT_PLAN.json')
    for name in ['BASELINE_REPORT.json','image_ledger.csv']+[c+'_raw_scores.csv' for c in json.loads((HERE/'sface/BASELINE_REPORT.json').read_text())['protocols']]:
        target=ROOT/'results/sface'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(HERE/'sface'/name,target)
    source=ROOT/'submission_ieee_10page/IEEE_TBIOM_Submission_10Page_Final.tex'
    history=ROOT/'document/history/pre_cpu_completion_2026-11-15'
    if not history.exists():
        history.mkdir(parents=True)
        for p in [source, ROOT/'document/arXiv_Preprint_10Page_Final.tex',ROOT/'document/arXiv_Preprint_10Page_Final.pdf',ROOT/'document/BUILD_REPORT.json']:
            shutil.copy2(p,history/p.name)
    old=(history/source.name).read_text(encoding='utf-8')
    prefix=old.split(r'\section{Datasets and Protocol}')[0]
    abstract=r'''Face verification under masks and sunglasses requires representations that retain identity information across different visible regions. We compare frozen DINOv2 with a trained projection, whole-face LoRA, periocular LoRA, fixed dual-branch fusion, and learned fusion. Fifteen new models are trained on CPU for five complete epochs, using three seeds and a frozen 6,171-row ROF manifest that excludes exact-content duplicates and a confirmed cross-split near-identical photograph. On the new test pairs, periocular LoRA leads masked ROC-AUC (0.9221$\pm$0.0046), fixed fusion leads sunglasses AUC (0.8950$\pm$0.0021), and learned gating leads neutral AUC (0.9458$\pm$0.0026). Known training-name-overlap exclusion leaves 802 MFR2 pairs, on which gating achieves 0.9548$\pm$0.0022; exact-conflict exclusion leaves 21,798 exploratory RMFRD pairs, where fixed fusion achieves 0.7240$\pm$0.0099. Validation-calibrated operating points are distinguished from retrospective ROC summaries. Same-branch controls show that learned gating does not consistently improve on constant or permuted weights. A separate pretrained SFace baseline is stronger on several protocols, with different training and alignment. These findings support condition-dependent benefits of adaptation and complementary regions, while limiting claims about adaptive reliability, low-FAR deployment, and state-of-the-art performance.'''
    a=prefix.index(r'\begin{abstract}')+len(r'\begin{abstract}');b=prefix.index(r'\end{abstract}')
    prefix=prefix[:a]+'\n'+abstract+'\n'+prefix[b:]
    prefix=prefix.replace('MFR2 is evaluated as an identity-overlap diagnostic (see the MFR2 protocol subsection), not as a clean cross-identity benchmark.', 'The new experiments remove the known MFR2 training-name overlap before evaluation; unknown aliases and pretraining overlap remain limitations.')
    prefix=prefix.replace('Later audits found an exact-content train--validation conflict and a near-identical photograph across training and test; label disjointness does not establish content independence.', 'Audits found an exact-content train--validation conflict and a near-identical photograph across historical training and test partitions. The new training manifest excludes the implicated content before any new run; label disjointness alone does not establish content independence.')
    prefix=prefix.replace('Fourth, it reports an external MFR2 evaluation as an identity-overlap diagnostic (not a clean cross-identity benchmark). Fifth, it documents an RMFRD audit limitation rather than using the external dataset to support an unqualified generalization claim.', 'Fourth, it reports MFR2 after excluding the known overlapping training name and RMFRD after excluding exact cross-label content conflicts. Fifth, it measures same-branch gate controls and validation-threshold transfer, exposing cases where adaptive fusion offers no advantage.')
    prefix=prefix.replace('the auxiliary fields are constant in all 7,295 archived complete-case ROF rows: the effective training vector is $[1,0,0,1]$. The original MFR2 evaluator supplied $[1,1,0,1]$; the corrected inference is reported separately.', 'all new training and evaluation use the constant vector $[1,0,0,1]$. Historical auxiliary-input and cache-key defects are recorded separately and do not supply the new headline results.')
    prefix=prefix.replace('direct gate-distribution analysis is needed.', 'gate distributions and constant-weight controls are therefore measured directly.')
    prefix=prefix.replace('The reported EER and TAR thresholds are retrospective evaluation-ROC operating points, not thresholds calibrated on validation data.', 'EER and ROC-constrained TAR are retrospective summaries. Separately, validation identities determine thresholds that are frozen before test evaluation; both actual test FAR and TAR are reported at those thresholds.')
    prefix=prefix.replace('M. E. ErakÄ±n','M. E. Erak{\\i}n').replace('ErakÄ±n','Erak{\\i}n')
    dataset=r'''
\section{Datasets and Protocol}
\subsection{ROF content and identity audit}
The local ROF reconstruction contains 7,751 indexed files, 399 condition-specific labels, 182 normalized names, and 6,491 distinct file hashes. It excludes a resource illustration previously indexed as an identity. Its image inventory differs from the maintainer's published counts. All 437 local annotation pickles match the checked official Git blob hashes, but an acquisition log establishing the image download history was not located. Annotation provenance therefore does not certify every downloaded image or semantic label.

Condition suffixes are normalized before identity partitioning. The historical complete-case manifest had 7,295 rows; an exact-content audit found four rows of one image across training and validation under different names. A perceptual screen subsequently found a near-identical photograph under different names across training and test despite different file hashes. The new manifest excludes exact repetitions, undecodable content, the cross-label conflict, and both copies of the confirmed cross-split near-duplicate photograph. It contains 6,171 rows: 4,405 training, 844 validation, and 922 test images, with 128, 26, and 28 normalized identity labels respectively. File-hash uniqueness and label partition disjointness are checked before training. The manifest hash is recorded in every new checkpoint; historical checkpoints are not resumed into this experiment.

The new ROF protocol uses one neutral enrollment image per eligible identity and condition-specific probes. Self-image comparisons are excluded. The masked test protocol contains 423 pairs (47 genuine, 376 impostor) over nine eligible identity labels; sunglasses contains 6,648 pairs (277 genuine, 6,371 impostor) over 24; neutral contains 15,960 pairs (570 genuine, 15,390 impostor) over 28. Every model uses the same ordered pairs. Validation protocols are constructed only from validation identities, with 300 masked, 5,148 sunglasses, and 14,404 neutral pairs. The masked validation protocol has 30 genuine and 270 impostor pairs over ten eligible identities. This small identity coverage limits extrapolation.

\subsection{External protocols after recorded exclusions}
The original complete-case MFR2 protocol has 820 pairs. A normalized exact-name match identified one ROF training name, Joe Biden, affecting 18 pairs. Removing those pairs before the new evaluation leaves 802 pairs: 406 genuine and 396 impostor. This removes the known overlap; aliases, unrecognized identities, and overlap with backbone pretraining remain unknown. No MFR2 image is used for new gradient updates or threshold selection.

The RMFRD source index has 91,849 entries. Its historical exploratory verification protocol contained 22,554 pairs. The exact-content audit identified 36 source/crop conflict groups across nominal identities, affecting 756 pairs. Their exclusion leaves 21,798 pairs: 1,038 genuine and 20,760 impostor. This is an exact-conflict-excluded exploratory protocol, rather than an independently certified semantic identity benchmark. Perceptual duplicates and mislabeled photographs can remain. The same constant auxiliary vector is used on ROF, MFR2, and RMFRD, so missing external quality metadata cannot be interpreted as measured quality.

\subsection{Metrics, calibration, and uncertainty}
We report ROC-AUC, EER, and empirical TAR subject to FAR at most $10^{-2}$ and $10^{-3}$. These ROC operating points use the test scores retrospectively and are not deployment thresholds. All metrics are recomputed from saved ten-decimal raw scores. The first nonzero masked test FAR is $1/376\approx0.00266$; the $10^{-3}$ summary therefore uses the zero-observed-false-accept portion of this finite ROC. It does not demonstrate population FAR below $10^{-3}$.

For a separate calibration analysis, validation impostor scores set the most permissive threshold permitting at most $\lfloor\alpha N_{\rm val}^{-}\rfloor$ false accepts, with ties excluded using the next representable larger threshold. The threshold is frozen for the matching ROF test condition. MFR2 and RMFRD receive the ROF masked-validation threshold without external calibration. We report actual test false accepts, genuine accepts, FAR, and TAR, rather than naming the validation target as an achieved test FAR. At a masked validation target of $10^{-3}$, only zero observed validation false accepts are permitted because $N_{\rm val}^{-}=270$.

Seed variation is described by the arithmetic mean and sample standard deviation of three independently trained seeds, 7, 42, and 123. A distinct sensitivity analysis draws 1,000 multinomial identity-node bootstrap replicates, with RNG seed 42. If identity $i$ is drawn $c_i$ times, a same-identity edge receives weight $c_i$, and an impostor edge between $i$ and $j$ receives weight $c_i c_j$. This accounts for reuse of identities at both endpoints. The paired comparison applies the same weights to both systems and all three fixed training seeds, then averages their AUC differences within each replicate. The percentile interval is conditional on the trained checkpoints and selected identities; it does not quantify uncertainty over all possible training sets or establish a population security guarantee. Ten descriptive contrasts are reported without a multiple-comparison significance claim.

\section{Experimental Settings}
\textbf{Inputs and backbone.} Face and periocular crops are resized to $224\times224$ and normalized with ImageNet channel statistics. Both branches use DINOv2 ViT-B/14 with a 768-dimensional projected embedding. LoRA rank is 8, scaling is 16, and dropout is 0.1; query, key, and value attention projections receive the updates. Base encoder weights remain frozen.

\textbf{Optimization.} All 15 new models use CPU, eight PyTorch threads, five complete epochs, batch size 16, AdamW with learning rate $10^{-4}$ and weight decay $10^{-4}$, and identity cross-entropy over the 128 training labels. Each epoch draws 4,405 training samples uniformly with replacement, producing 276 batches, and each full run executes 1,380 optimizer steps. There is no smoke-test batch cap in a research run. Training-time classifiers do not contribute to verification scores. Final fifth-epoch checkpoints are evaluated without selecting a best epoch on test performance.

\textbf{Execution and recovery.} The executed environment records PyTorch 2.14.0+cpu, deterministic algorithms, and an offline cached DINOv2 model. Atomic checkpoints retain optimizer state, sample order, next batch, epoch losses, and Python, NumPy, and PyTorch RNG states. Manifest and source signatures reject incompatible resumes. The serial coordinator verifies completed score hashes before retaining a run. Periocular-only training skips the unused whole-face forward pass; this changes random-number consumption relative to the historical trainer, so the new experiment is not claimed to reproduce historical optimization bit for bit.

\subsection{Parameter efficiency}
'''
    params=old.split(r'\subsection{Parameter efficiency}')[1].split(r'\subsection{Reproducibility safeguards}')[0]
    def table(c,label,title):
        rows=[r for r in summary['summary'] if r['condition']==c]
        keys=['auc','eer','tar_far_1e-2','tar_far_1e-3']
        text=[r'\begin{table}[t]',r'\centering',r'\caption{'+title+r' Values are mean with sample seed SD in subscripts; three seeds. TAR columns are retrospective ROC summaries, not validation-calibrated test rates.}',r'\label{tab:'+label+'}',r'\begin{tabular}{lrrrr}',r'\toprule',r'Configuration & AUC & EER & TAR$_{.01}$ & TAR$_{.001}$\\',r'\midrule']
        for v,name in zip(VARIANTS,LABELS):
            row=next(r for r in rows if r['variant']==v);cells=[]
            for k in keys:
                x=f"{row[k+'_mean']:.4f}".lstrip('0');sd=f"{row[k+'_seed_sd']:.3f}".lstrip('0')
                best=(min if k=='eer' else max)(r[k+'_mean'] for r in rows)
                if row[k+'_mean']==best:x=r'\textbf{'+x+'}'
                cells.append(x+r'$_{\pm'+sd+'}$')
            text.append(name+' & '+' & '.join(cells)+r'\\')
        text.insert(2,r'\setlength{\tabcolsep}{2.2pt}')
        return '\n'.join(text+[r'\bottomrule',r'\end{tabular}',r'\end{table}',''])
    def figure(name,caption,label):
        return '\n'.join([r'\begin{figure}[t]',r'\centering',r'\includegraphics[width=\columnwidth]{'+name+'.pdf}',r'\caption{'+caption+'}',r'\label{fig:'+label+'}',r'\end{figure}',''])
    results=r'''
\section{Results}
All results in this section come from the 15 newly trained models on the duplicate-excluded manifest. Historical numerical files are retained for audit and are not pooled with these runs. Tables distinguish the new protocol from earlier complete-case and post-hoc score-filtered analyses.

\subsection{Masked ROF verification}
Periocular LoRA has the highest masked mean AUC, 0.9221, followed by fixed fusion at 0.9134 and gating at 0.8989. Whole-face LoRA improves from the frozen projection baseline's 0.8303 to 0.8852. Thus adaptation improves ranking, and restricting attention to the upper face is useful under lower-face occlusion. The gated model does not recover the best periocular-only ranking. The gate-minus-fixed mean AUC difference is $-0.0145$, with a two-endpoint identity-resampling sensitivity interval of $[-0.0560,0.0144]$. Only nine masked test identities are eligible, so the interval is broad and the protocol supports a conditional comparison.

The low-FAR columns must be read with the finite denominator. A zero-observed-false-accept point can have nonzero TAR, but does not validate a security operating point below the first nonzero FAR step. The seed-42 ROC plot omits FAR-zero points on the logarithmic axis; those points remain included in metric computation.
'''
    results+=table('test_masked','rofmasked','New ROF masked test: 47 genuine and 376 impostor pairs.')
    results+=figure('fig_rof_masked_roc','New masked ROF ROC, seed 42. Positive empirical FAR points only; first nonzero FAR is $1/376$. FAR-zero points are omitted from this logarithmic plot.','rofmaskedroc')
    results+=r'''
\subsection{Sunglasses and neutral ROF verification}
Sunglasses occlude the region used by the periocular-only model. Its mean AUC falls to 0.7905, below the frozen whole-face baseline at 0.8780. Fixed fusion leads at 0.8950, narrowly ahead of gating at 0.8924 and whole-face LoRA at 0.8913. The gated-minus-fixed difference is $-0.0026$, with sensitivity interval $[-0.0155,0.0116]$. These results show that the availability of a second branch does not ensure a gain from learned weighting.

On neutral images, learned gating has the largest mean AUC, 0.9458, compared with fixed fusion at 0.9428 and whole-face LoRA at 0.9413. The gated-minus-fixed difference is 0.0030, with sensitivity interval $[-0.0034,0.0108]$. This small ordering should not be interpreted as a conclusive population advantage. Periocular-only AUC is 0.8875, indicating information loss when clean lower-face cues are discarded. Table~\ref{tab:rofneutral} includes this neutral control so that cross-condition claims do not rely only on occluded probes.
'''
    results+=table('test_sunglasses','rofsunglasses','New ROF sunglasses test: 277 genuine and 6,371 impostor pairs.')
    results+=table('test_neutral','rofneutral','New ROF neutral test: 570 genuine and 15,390 impostor pairs.')
    results+=figure('fig_rof_sunglasses_roc','New sunglasses ROF ROC, seed 42. Only positive empirical FAR points are plotted; all systems use the same frozen pairs.','rofsunglassesroc')
    results+=r'''
\subsection{Known-overlap-excluded MFR2}
Learned gating has the highest mean AUC on the 802 retained MFR2 pairs, 0.9548, compared with fixed fusion at 0.9398. The gated-minus-fixed difference is 0.0150, with identity-resampling interval $[-0.0005,0.0310]$. Whole-face LoRA reaches 0.9360, compared with 0.8412 for the frozen baseline; the adaptation gain is larger than the gate-versus-fixed difference. No target-domain labels are used for gradient updates or calibration.

The known overlapping training name has been excluded, so these are not the earlier contaminated 820-pair headline results. However, exclusion by normalized exact name is not a complete identity audit. Unknown aliases and DINOv2 pretraining overlap remain possible. The external ROC describes ranking on the retained protocol; transferred ROF validation thresholds are evaluated separately.
'''
    results+=table('mfr2','mfr2','Known-name-overlap-excluded MFR2: 406 genuine and 396 impostor pairs.')
    results+=figure('fig_mfr2_roc','MFR2 ROC after known training-name-overlap exclusion, seed 42; positive empirical FAR points only. Auxiliary inputs match training.','mfr2roc')
    results+=r'''
\subsection{Exact-conflict-excluded RMFRD}
Fixed fusion has the highest exploratory RMFRD mean AUC, 0.7240, followed by learned gating at 0.7175 and periocular LoRA at 0.7132. Whole-face LoRA reaches 0.7045 and the frozen baseline 0.6957. The gated-minus-fixed difference is $-0.0066$, with sensitivity interval $[-0.0116,-0.0027]$. The completed descriptive interval includes zero; it neither establishes a conclusive ordering nor validates the dataset labels.

The much lower AUC than on MFR2 shows substantial transfer difficulty. Removing known exact conflicts avoids their direct influence, while remaining annotation and acquisition uncertainty prevents a strong unseen-identity or deployment claim. Figure~\ref{fig:crossauc} summarizes all five test conditions with seed variation rather than selecting one favorable dataset.
'''
    results+=table('rmfrd','rmfrd','Exact-conflict-excluded exploratory RMFRD: 1,038 genuine and 20,760 impostor pairs.')
    results+=figure('fig_auc_cross_dataset','New CPU-trained models: mean AUC and one sample SD across three seeds. MFR2 excludes the known overlapping name; RMFRD excludes known exact-content conflicts and remains exploratory.','crossauc')
    # Numeric tables generated directly from completed reports.
    results+=r'''
\subsection{Validation-calibrated operating points}
Table~\ref{tab:calibration} reports the gated system at a validation target FAR of 0.01. Each entry shows mean test TAR and FAR; acceptance counts are listed in seed order 7/42/123. ROF uses its matching validation condition, while both external datasets use ROF masked validation. The observed test FAR can exceed the validation target. In particular, the neutral test distribution produces appreciably more false accepts than the validation calibration suggests. This discrepancy is obscured if retrospective test ROC points are presented as preselected thresholds.

At validation target 0.001, masked calibration allows zero observed validation false accepts. That finite-sample event does not certify a population FAR of 0.001. Full per-seed thresholds, calibration and test counts, and both targets are included for all models in the machine-readable reports. Calibration is fixed by the stated rule and is not revised after observing test errors.
\begin{table}[t]
\centering
\caption{Gated model at validation target FAR 0.01. Means over three seeds; TA/FA list actual test accept counts in seed order. External thresholds are transferred from masked ROF validation.}
\label{tab:calibration}
\begin{tabular}{lrrrr}
\toprule
Protocol & TAR & FAR & TA & FA\\
\midrule
'''
    names=['Masked','Sunglasses','Neutral','MFR2','RMFRD']
    for c,n in zip(CONDITIONS,names):
        key='validation_calibrated' if c.startswith('test_') else 'transferred_rof_validation_thresholds'
        values=[records[(s,'gated_fusion')]['protocols'][c][key]['0.01'] for s in SEEDS]
        values=[x['test'] if 'test' in x else x for x in values]
        results+=n+' & '+f"{statistics.mean(x['tar'] for x in values):.4f} & {statistics.mean(x['far'] for x in values):.4f} & "+'/'.join(str(x['true_accepts']) for x in values)+' & '+'/'.join(str(x['false_accepts']) for x in values)+r'\\'+'\n'
    results+=r'''\bottomrule
\end{tabular}
\end{table}

\subsection{Same-branch gate controls}
Training separate fixed and gated models changes both their branch features and their fusion rule. To isolate the latter, each trained gated checkpoint is also evaluated with its own branches under constant 0.5, validation-mean, and permuted weights, plus the individual branches. A validation-mean weight is calculated only from validation endpoints. Permutation uses seed 42 within unique endpoints of each protocol, with no cross-protocol mixing. It is a post-hoc diagnostic, not a deployable fusion policy or a new training run.

\begin{table}[t]
\centering
\caption{Mean AUC of fusion controls on the same trained gated branches. These are distinct from separately trained M3.}
\label{tab:gatecontrols}
\begin{tabular}{lrrrr}
\toprule
Protocol & Learned & Equal & Val. mean & Permuted\\
\midrule
'''
    for c,n in zip(CONDITIONS,names):
        vals=[statistics.mean(records[(s,'gated_fusion')]['gate_controls'][c][k]['auc'] for s in SEEDS) for k in ['learned','constant_0.5_same_branches','validation_mean_gate_same_branches','permuted_gate_same_branches']]
        results+=n+' & '+' & '.join(f'{v:.4f}' for v in vals)+r'\\'+'\n'
    results+=r'''\bottomrule
\end{tabular}
\end{table}

On masked ROF, equal weighting of the gated model's branches gives mean AUC 0.9250, above learned weighting at 0.8989. The validation-mean gate also slightly exceeds learned gating on sunglasses and neutral images. Permuting weights gives 0.8942 on sunglasses, compared with learned weighting at 0.8924. MFR2 is more favorable to image-dependent gating: learned weighting gives 0.9548 versus 0.9420 with the validation-mean weight and 0.9391 after permutation. Thus evidence for useful sample-dependent weighting is protocol-specific rather than universal.

Mean gate values across seeds range from 0.709 to 0.749 on masked ROF and from 0.825 to 0.841 on sunglasses, assigning more weight to the face branch under sunglasses. Within-seed variation remains nonzero. This pattern is consistent with condition-dependent use of the branches, but does not establish calibrated reliability or causal detection of occlusion. Folding the constant auxiliary input into the first-layer bias changes gate outputs by at most $1.20\times10^{-7}$ across the recorded checks. The auxiliary fields therefore supply no measured image-specific quality information.
'''
    results+=figure('fig_rof_masked_scores','New masked ROF gated-fusion scores, seed 42. Shared bins; each class is normalized separately. Genuine and impostor counts remain visible.','scores')
    results+=r'''
\subsection{Pretrained face-recognition diagnostic}
The artifact also evaluates OpenCV SFace (December 2021 weights) using YuNet (March 2023) detection, five-landmark alignment, confidence threshold 0.8, and the detection closest to the image center. No target fine-tuning is performed. Failed pair detections receive score $-1$ and remain in the primary denominator; detected-only metrics are secondary. SFace reaches AUC 0.9399 on masked ROF, 0.9440 on sunglasses, 0.9991 on neutral, 0.9968 on retained MFR2, and 0.8187 on retained RMFRD. Respectively, 9, 48, 0, 0, and 1,155 pairs contain failed detections. The published ledger records the actual endpoints and raw scores.

These results exceed the mean AUC of the new DINOv2 variants on each listed protocol, but the comparison is not matched for pretraining data, identity exposure, detector, alignment, or training objective. It is a diagnostic showing that this ablation study does not establish state-of-the-art face verification. A matched modern face-recognition baseline and independent external labels would be required for a stronger comparative claim.

\section{Discussion}
\subsection{Adaptation and regional complementarity}
The new experiment supports the direction of H1: whole-face LoRA improves mean AUC over the frozen projection baseline on all five test protocols. The effect is largest on MFR2 and masked ROF, while its RMFRD advantage is modest. This is evidence about supervised adaptation on the particular ROF training identities, rather than a general guarantee that LoRA will outperform a pretrained face-specific representation.

H2 receives condition-dependent support. Periocular LoRA has the highest masked AUC, consistent with using visible upper-face cues when the lower face is covered. Its sunglasses deficit and weaker neutral ranking show the cost of discarding complementary full-face information. A single regional representation is therefore an incomplete solution to mixed occlusion. Fixed fusion combines complementary cues and is a strong baseline, leading sunglasses and RMFRD mean AUC.

The results do not establish H3 as a universal improvement. Learned gating leads MFR2 and neutral mean AUC, but loses to fixed fusion on masked ROF, sunglasses, and RMFRD. Several paired identity-resampling intervals include zero. More decisively, holding the learned branches fixed can remove apparent benefits of image-dependent weights: a constant validation-mean gate is competitive on ROF, and equal weighting is better under masks. An improvement between separately trained models must not be attributed entirely to a better gate policy.

\subsection{AUC, calibration, and deployment}
AUC describes ranking over the full score range, whereas a deployed verifier uses a particular threshold. A small AUC gain can coexist with poor TAR at a strict FAR constraint. The saved validation-calibrated counts demonstrate distribution shift directly: a threshold satisfying a validation target does not necessarily attain that rate on new identities. This is especially important for neutral scores, where many reused enrollment and probe identities make nominal pair counts look larger than the amount of independent information.

The masked test protocol has only 47 genuine comparisons and nine eligible labels. One changed genuine accept shifts TAR by $1/47$, and one changed impostor accept shifts FAR by $1/376$. Reporting four decimal places aids arithmetic verification but does not imply four-decimal statistical precision. Identity-node resampling is a sensitivity analysis of this finite protocol, not a substitute for collecting more independent identities and sessions.

The score-distribution plot illustrates overlap between genuine and impostor scores without diagnosing the identity or cause of individual errors. Qualitative identity-label decisions require human review of licensed source data. The retained manifests and exclusion ledgers make such review possible without distributing private or restricted face images in the repository.

\subsection{Positioning and negative findings}
This work is a reproducible comparison of parameter-efficient region adaptation and fusion, with content-audit corrections and explicit gate controls. Face--periocular combination, LoRA, and quality-related fusion have existing precedents; their combination alone does not establish novelty. The stronger SFace diagnostic narrows the contribution to an ablation and integrity study. Any claim of competitive biometric recognition should be supported by matched face-specific baselines, broader identities, and independently checked labels.

The constant auxiliary vector is an important negative finding. Although the gate architecture accepts descriptors, the executed protocol supplies no varying quality measurement. The learned scalar can depend on embeddings, but cannot demonstrate measured quality-aware fusion. Relabeling it as an embedding-conditioned fusion gate is more faithful to the evidence. A future quality study would need validated varying descriptors, controlled descriptor ablations, and a hypothesis fixed before test evaluation.

\section{Limitations and Threats to Validity}
The duplicate-excluded manifest removes the known exact conflicts and confirmed cross-split near-duplicate photograph; it does not certify all semantic labels or exhaustively detect perceptual duplicates. The annotation-source match does not resolve the local image acquisition discrepancy. Exact normalized-name overlap checks can miss aliases. Public-figure images may also appear in DINOv2 or SFace pretraining; those identity exposures are unknown.

Only three training initializations are measured. Seed SD is descriptive, and the node-bootstrap intervals condition on those three fitted systems and the frozen identity graph. Identity resampling cannot recreate missing acquisition sessions or repair mislabeled photographs. The ten contrasts are exploratory without family-wise error control. The small masked identity set and finite impostor denominator preclude strong security claims at very low FAR.

RMFRD remains exploratory after exact-conflict exclusion. MFR2's retained protocol removes one known overlap rather than proving all identities unseen. SFace uses different alignment and pretraining, preventing a controlled architecture ranking. Peak memory was not instrumented. Logged wall-clock training durations include interruptions or sleep and should not be treated as uninterrupted throughput benchmarks. CPU determinism was configured and checkpoint recovery tested within the recorded runtime, but bitwise reproduction across package versions or hardware is not asserted.

\section{Reproducibility and Artifact Specification}
The release contains the completed 15-model grid, 120 ordered raw-score files covering eight validation/test/external protocols, per-run evaluation reports, final training-progress records, checkpoint hashes, and the 25-row five-condition metric summary. Ten paired three-seed AUC comparisons include per-seed deltas, bootstrap configuration, and conditional intervals. The exact executed trainer, evaluator, common utilities, and model/metric runtime snapshots are shipped with source hashes; changing those sources invalidates the recorded execution signatures.

The reproducibility sequence is to obtain licensed images, restore the documented face/periocular paths, verify the frozen training and pair manifests, prepare the recorded software environment and DINOv2 cache, and run the CPU coordinator. Each model is trained for five epochs, scored on the same eight protocols, and summarized only after complete evaluation. A file lock prevents duplicate coordinators. Repeated launches retain verified completed runs; interruptions resume from atomic optimizer and RNG checkpoints rather than restarting the experiment. The repository does not include the face images, pretrained weight binaries, or approximately 10~GB of new trained checkpoints. Their recorded hashes permit local provenance checks but do not replace access to the binaries for inference reproduction.

Arithmetic verification can be performed without torch, images, or checkpoints: the release verifier independently reconstructs ROC metrics from raw scores, checks frozen-pair alignment and hashes, recalculates seed means and SDs, and checks manuscript table values. It separately retains the 90 historical metric files, historical sensitivities, and corrected historical MFR2 inference. Passing these checks means that the recorded files are internally consistent; it does not certify scientific novelty, journal acceptance, or semantic image labels.

Historical manuscript and interim follow-up snapshots remain under the history directory. Their claims and numerical tables are superseded by the completed CPU experiment in the current paper. No historical score filtering is represented as new training, and no incomplete or smoke-limited run supplies a headline table. Shared IEEE and arXiv substantive text and vector figures are regenerated together from the completed result evidence.

\section{Conclusion}
Fifteen new CPU-trained models on a frozen duplicate-excluded ROF manifest show that adaptation and regional information help different verification conditions. Periocular LoRA leads masked mean AUC at 0.9221, fixed fusion leads sunglasses at 0.8950 and exploratory RMFRD at 0.7240, while learned gating leads neutral at 0.9458 and known-overlap-excluded MFR2 at 0.9548. Same-branch controls limit the interpretation of learned gating: constant or permuted weights remain competitive on several ROF conditions. Validation-calibrated operating points also expose FAR shift that retrospective ROC summaries cannot resolve.

The results support condition-dependent complementarity rather than universal adaptive robustness. The completed artifact permits score-level arithmetic and provenance checks. Stronger publication claims still require semantic label review, broader independent identities, matched modern baselines, and author assessment of the contribution. Remaining limitations are explicit rather than treated as evidence of deployment readiness.
'''
    diagnostics=[r'\begin{table}[t]',r'\centering',r'\caption{Mean face-branch gate weight by protocol and training seed; within-endpoint SD in parentheses. These are descriptive gate outputs, not calibrated reliability probabilities.}',r'\label{tab:gatedistribution}',r'\begin{tabular}{lrrr}',r'\toprule',r'Protocol & Seed 7 & Seed 42 & Seed 123\\',r'\midrule']
    for c,n in zip(CONDITIONS,names):
        values=[records[(s,'gated_fusion')]['gate_controls'][c]['gate_distribution'] for s in SEEDS]
        diagnostics.append(n+' & '+' & '.join(f"{x['mean']:.3f} ({x['sd']:.3f})" for x in values)+r'\\')
    diagnostics += [r'\bottomrule',r'\end{tabular}',r'\end{table}']
    results=results.replace(r'\subsection{Pretrained face-recognition diagnostic}','\n'.join(diagnostics)+'\n'+r'\subsection{Pretrained face-recognition diagnostic}')
    baseline=json.loads((HERE/'sface/BASELINE_REPORT.json').read_text())
    btable=[r'\begin{table}[t]',r'\centering',r'\caption{SFace diagnostic on the same retained test protocols. Failed pairs receive score $-1$ and remain in the denominator. Different pretraining and alignment prevent a matched architecture claim.}',r'\label{tab:sface}',r'\begin{tabular}{lrr}',r'\toprule',r'Protocol & AUC & Failed pairs\\',r'\midrule']
    for c,n in zip(CONDITIONS,names):
        item=baseline['protocols'][c]
        failures=item['failed_pairs']
        auc=item['all_pairs_metrics']['auc']
        btable.append(n+f' & {auc:.4f} & {failures}'+r'\\')
    btable += [r'\bottomrule',r'\end{tabular}',r'\end{table}']
    results=results.replace(r'\section{Discussion}','\n'.join(btable)+'\n'+r'\section{Discussion}')
    paired=[r'\subsection{Paired comparison record}',
        'Table~\\ref{tab:paired} gives every prespecified descriptive contrast from the completed summary, including unfavorable directions. Positive differences favor the first model. The same resampled identity counts are applied to both models and all three training seeds; differences are averaged within each replicate. These intervals condition on the fitted checkpoints and frozen protocols. They are not confidence intervals for performance on an arbitrary future population.',
        r'\begin{table}[t]',r'\centering',r'\caption{Paired mean AUC differences and two-endpoint identity-resampling 95\% sensitivity intervals; 1,000 replicates. G--F denotes gated minus fixed fusion; W--B denotes whole LoRA minus frozen baseline.}',r'\label{tab:paired}',r'\begin{tabular}{llrrr}',r'\toprule',r'Protocol & Contrast & Difference & Lower & Upper\\',r'\midrule']
    for x in summary['paired_auc_comparisons']:
        n=names[CONDITIONS.index(x['condition'])];contrast='G--F' if x['contrast'].startswith('gated') else 'W--B'
        lo,hi=x['paired_two_endpoint_identity_bootstrap_ci95']
        paired.append(n+' & '+contrast+f" & {x['mean_auc_difference']:.4f} & {lo:.4f} & {hi:.4f}"+r'\\')
    paired += [r'\bottomrule',r'\end{tabular}',r'\end{table}',
        'A positive or negative interval on an audited subset cannot resolve selection bias in that subset. Exclusion rules were fixed before these new runs, but they were motivated by defects found during the earlier experiment. The prospective retraining removes the direct influence of those known images; it does not turn the local reconstruction into a newly collected independent cohort. The provenance records identify the revised experiment so that its numbers cannot be mistaken for measurements from the original complete-case protocol.']
    results=results.replace(r'\section{Discussion}','\n'.join(paired)+'\n'+r'\section{Discussion}')
    # Bind all quoted paired intervals to the actual final summary, avoiding manual transcription.
    for c, old_interval in [('test_sunglasses','[-0.0155,0.0116]'),('test_neutral','[-0.0034,0.0108]'),('mfr2','[-0.0005,0.0310]'),('rmfrd','[-0.0116,-0.0027]')]:
        item=next(x for x in summary['paired_auc_comparisons'] if x['condition']==c and x['contrast']=='gated_fusion minus fixed_fusion')
        lo,hi=item['paired_two_endpoint_identity_bootstrap_ci95'];results=results.replace(old_interval,f'[{lo:.4f},{hi:.4f}]')
    tail=r'\section{Acknowledgments}'+old.split(r'\section{Acknowledgments}')[1]
    tail=tail.replace('ErakÄ±n',r'Erak{\i}n')
    tex=prefix+dataset+params+results+tail
    tex=tex.replace(r'\graphicspath{{paper_assets/}}',r'\graphicspath{{./}}')
    write(source,tex)
    arxiv=tex.replace(r'\graphicspath{{./}}',r'\graphicspath{{../submission_ieee_10page/}}')
    arxiv=arxiv.replace(r'\maketitle',r'\maketitle'+'\n'+r'\noindent\textit{Preprint submitted for scholarly dissemination.}\par')
    write(ROOT/'document/arXiv_Preprint_10Page_Final.tex',arxiv)
    print('Promoted 15 models, exact execution sources, protocols, raw evidence, and revised substantive paper sources.')

if __name__ == '__main__':main()
