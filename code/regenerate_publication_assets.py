"""Regenerate publication plots and corrected MFR2 numeric text from saved scores.
Historical scores are retained. Corrected gated MFR2 scores take precedence.
"""
from pathlib import Path
import csv,json,re,statistics
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve,roc_auc_score
from verify_results import SEEDS,VARIANTS
ROOT=Path(__file__).resolve().parent.parent
LABELS=["Frozen + projection","Whole LoRA","Periocular LoRA","Fixed fusion","Learned gating"]
COLORS=["#0072B2","#E69F00","#009E73","#D55E00","#CC79A7"]
def raw_path(seed,v,c):
    folder="rof_seed_sweep" if c in ["masked","sunglasses","neutral"] else "cross_dataset"
    if c=="mfr2" and v=="gated_fusion":return ROOT/f"results/corrections/mfr2_quality_v2/seed{seed}_{v}_{c}_raw_scores.csv"
    return ROOT/f"results/seed_sweep/{folder}/seed{seed}_{v}_{c}_raw_scores.csv"
def metrics(seed,v,c):
    return json.loads(raw_path(seed,v,c).with_name(raw_path(seed,v,c).name.replace("_raw_scores.csv","_metrics.json")).read_text()).get("metrics") or json.loads(raw_path(seed,v,c).with_name(raw_path(seed,v,c).name.replace("_raw_scores.csv","_metrics.json")).read_text())
def load(seed,v,c):
    with raw_path(seed,v,c).open(encoding="utf-8",newline="") as f:rs=list(csv.DictReader(f))
    return np.array([int(r["label"]) for r in rs]),np.array([float(r["score"]) for r in rs])
def save(fig,name):
    folder=ROOT/"submission_ieee_10page"
    fig.savefig(folder/(name+".pdf"),bbox_inches="tight")
    fig.savefig(folder/(name+".png"),dpi=300,bbox_inches="tight")
    plt.close(fig)
def main():
    import os
    if os.environ.get("LEGACY_ASSET_REGENERATION") != "1":
        raise SystemExit("Historical asset generator. Use code/regenerate_completed_assets.py for the current paper. Set LEGACY_ASSET_REGENERATION=1 only to reproduce historical figures in a separate copy.")
    plt.rcParams.update({"font.size":10,"axes.labelsize":11,"legend.fontsize":8,"pdf.fonttype":42,"ps.fonttype":42})
    for cond,title in [("masked","ROF masked; seed 42"),("sunglasses","ROF sunglasses; seed 42"),("mfr2","MFR2; seed 42; corrected gate inputs")]:
        fig,ax=plt.subplots(figsize=(5.4,4.1));neg=None
        for v,label,color in zip(VARIANTS,LABELS,COLORS):
            y,s=load(42,v,cond);f,t,_=roc_curve(y,s,drop_intermediate=False);keep=f>0;neg=int(sum(y==0))
            ax.step(f[keep],t[keep],where="post",color=color,lw=1.3,label=f"{label} ({roc_auc_score(y,s):.3f})")
        resolution=1/neg;ax.set_xscale("log");ax.set_xlim(resolution,1);ax.set_ylim(0,1.01)
        ax.axvline(resolution,color=".4",ls=":",lw=1)
        ax.set(xlabel="Empirical false acceptance rate",ylabel="True acceptance rate",title=title)
        ax.grid(alpha=.2);ax.legend(loc="lower right",framealpha=.9)
        fig.text(.5,.005,f"Positive-FAR points only; first nonzero FAR = 1/{neg}. FAR=0 points omitted.",ha="center",fontsize=8)
        fig.tight_layout(rect=[0,.025,1,1])
        save(fig,"fig_mfr2_roc" if cond=="mfr2" else f"fig_rof_{cond}_roc")
    conditions=["masked","sunglasses","mfr2","rmfrd"]
    fig,ax=plt.subplots(figsize=(6.5,4.1))
    for i,(v,label,color) in enumerate(zip(VARIANTS,LABELS,COLORS)):
        vals=[[metrics(s,v,c)["auc"] for s in SEEDS] for c in conditions]
        x=np.arange(len(conditions))+(i-2)*.105
        ax.errorbar(x,[statistics.mean(a) for a in vals],yerr=[statistics.stdev(a) for a in vals],
                    fmt="o",markersize=4,color=color,capsize=3,label=label,lw=1)
    ax.set_xticks(range(4),["ROF masked","ROF sunglasses","MFR2 overlap","RMFRD exploratory"])
    ax.set(ylabel="ROC-AUC (mean ± seed SD)",ylim=(.65,.98))
    ax.grid(axis="y",alpha=.2);ax.legend(ncol=2,loc="lower left")
    fig.tight_layout();save(fig,"fig_auc_cross_dataset")
    y,s=load(42,"gated_fusion","masked");bins=np.linspace(s.min(),s.max(),26)
    fig,ax=plt.subplots(figsize=(5.4,3.6))
    for label,mask,color in [("Impostor",y==0,"#D55E00"),("Genuine",y==1,"#009E73")]:
        ax.hist(s[mask],bins=bins,density=True,alpha=.5,color=color,label=f"{label} (n={sum(mask)})")
    ax.set(xlabel="Cosine score",ylabel="Within-class density",title="ROF masked gated scores; seed 42")
    ax.legend();ax.grid(alpha=.15);fig.tight_layout();save(fig,"fig_rof_masked_scores")
    source=ROOT/"submission_ieee_10page/IEEE_TBIOM_Submission_10Page_Final.tex"
    tex=source.read_text(encoding="utf-8")
    keys=["auc","eer","tar_far_1e-2","tar_far_1e-3"]
    values={v:{k:[metrics(s,v,"mfr2")[k] for s in SEEDS] for k in keys} for v in VARIANTS}
    winners={k:(min if k=="eer" else max)(VARIANTS,key=lambda v:statistics.mean(values[v][k])) for k in keys}
    block=tex.split("\\label{tab:mfr2}")[1].split("\\bottomrule")[0]
    lines=[l for l in block.splitlines() if "\\pm" in l]
    for v,label,line in zip(VARIANTS,["Frozen + projection","Whole LoRA","Periocular LoRA","Fixed fusion","Learned gating"],lines):
        cells=[]
        for k in keys:
            mean=statistics.mean(values[v][k]);sd=statistics.stdev(values[v][k])
            cell=f"{mean:.4f}".lstrip("0")
            if winners[k]==v:cell="\\textbf{"+cell+"}"
            cells.append(cell+"$_{\\pm"+f"{sd:.3f}".lstrip("0")+"}$")
        tex=tex.replace(line,label+" & "+" & ".join(cells)+r"\\")
    gate_auc=statistics.mean(values["gated_fusion"]["auc"]);gate_eer=statistics.mean(values["gated_fusion"]["eer"])
    # Known historical prose tokens; these occur only in MFR2 descriptions.
    tex=tex.replace("0.9554",f"{gate_auc:.4f}").replace("0.1148",f"{gate_eer:.4f}")
    tex=tex.replace("Table~\\ref{tab:mfr2} reports the mean and standard deviation over three training seeds",
        "Table~\\ref{tab:mfr2} uses actual re-inference of the three final gated checkpoints with the training-consistent $[1,0,0,1]$ vector; the four ungated variants are unchanged. It reports the mean and standard deviation over three training seeds")
    tex=tex.replace("0.9554$\\pm$0.002",f"{gate_auc:.4f}"+"$\\pm$"+f"{statistics.stdev(values['gated_fusion']['auc']):.3f}")
    for name in ["fig_rof_masked_roc","fig_rof_sunglasses_roc","fig_mfr2_roc","fig_auc_cross_dataset","fig_rof_masked_scores"]:
        tex=tex.replace(name+".png",name+".pdf")
    tex=tex.replace("The small number of eligible masked test identities makes low-FAR estimates discrete and uncertain.","Only positive empirical FAR points are plotted; zero-FAR points are omitted. The first nonzero FAR is $1/464$.")
    tex=tex.replace("Fusion reduces the degradation observed for periocular-only LoRA.","Positive empirical FAR points are plotted; zero-FAR points are omitted.")
    tex=tex.replace("MFR2 official-pair ROC curves (seed 42).","MFR2 official-pair ROC curves (seed 42), with corrected gate inputs. Only positive empirical FAR points are plotted.")
    tex=tex.replace("Mean ROC-AUC over three training seeds across the evaluated protocols.","Mean ROC-AUC over three training seeds for ROF masked/sunglasses and the external protocols, with corrected MFR2 gating.")
    tex=tex.replace("Gated-fusion score distributions on ROF masked probes.","Gated-fusion score distributions on ROF masked probes, with shared bin edges and class counts.")
    source.write_text(tex,encoding="utf-8")
    arxiv=tex.replace(r"\maketitle",r"\maketitle"+"\n"+r"\noindent\textit{Preprint submitted for scholarly dissemination.}\par")
    arxiv=arxiv.replace(r"\graphicspath{{paper_assets/}}",r"\graphicspath{{../submission_ieee_10page/}}")
    (ROOT/"document/arXiv_Preprint_10Page_Final.tex").write_text(arxiv,encoding="utf-8")
    report={"corrected_gated_mfr2":{k:{"mean":statistics.mean(values["gated_fusion"][k]),"sample_sd":statistics.stdev(values["gated_fusion"][k])} for k in keys},
            "per_seed":{str(s):metrics(s,"gated_fusion","mfr2") for s in SEEDS}}
    (ROOT/"results/corrections/mfr2_quality_summary.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report["corrected_gated_mfr2"],indent=2))
if __name__=="__main__":main()
