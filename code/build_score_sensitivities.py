"""Recompute post-hoc score sensitivities on audited, frozen exclusion subsets.
No retraining; these must not be interpreted as clean-trained performance.
"""
from pathlib import Path
import csv,json,statistics
from verify_results import score_metrics,align,digest,SEEDS,VARIANTS

def read(p):
    with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def main():
    root=Path(__file__).resolve().parent.parent
    out=root/"results/corrections/sensitivities";out.mkdir(parents=True,exist_ok=True)
    names={"masked":"rof_masked_pairs.csv","sunglasses":"rof_sunglasses_pairs.csv","neutral":"rof_neutral_pairs.csv",
           "mfr2":"mfr2_official_complete_pairs.csv","rmfrd":"rmfrd_pairs.csv"}
    runs=[]
    for cond,name in names.items():
        original=read(root/"manifests"/name);clean_path=root/"manifests/cleaned"/name
        retained={r["pair_id"] for r in read(clean_path)}
        keep=[i for i,r in enumerate(original) if r["pair_id"] in retained]
        for seed in SEEDS:
            for variant in VARIANTS:
                prefix=f"seed{seed}_{variant}_{cond}"
                folder="rof_seed_sweep" if cond in ["masked","sunglasses","neutral"] else "cross_dataset"
                source=root/f"results/seed_sweep/{folder}/{prefix}_raw_scores.csv"
                if cond=="mfr2" and variant=="gated_fusion":
                    source=root/f"results/corrections/mfr2_quality_v2/{prefix}_raw_scores.csv"
                rs=read(source);align(rs,original)
                filtered=[{"pair_id":original[i]["pair_id"],**rs[i]} for i in keep]
                target=out/f"{prefix}_raw_scores.csv"
                with target.open("w",encoding="utf-8",newline="") as f:
                    w=csv.DictWriter(f,fieldnames=list(filtered[0]));w.writeheader();w.writerows(filtered)
                align(filtered,read(clean_path))
                source_meta=source.with_name(source.name.replace("_raw_scores.csv","_metrics.json"))
                recorded=json.loads(source_meta.read_text())
                runs.append({"seed":seed,"variant":variant,"condition":cond,"metrics":score_metrics(filtered),
                             "raw_scores":target.relative_to(root).as_posix(),"raw_sha256":digest(target),
                             "pairs":clean_path.relative_to(root).as_posix(),"pairs_sha256":digest(clean_path),
                             "source_raw_scores":source.relative_to(root).as_posix(),"source_raw_sha256":digest(source),
                             "checkpoint_sha256":recorded["checkpoint_sha256"],
                             "training_status":"archived checkpoint, not retrained on cleaned manifest"})
    aggregate={}
    for cond in names:
        aggregate[cond]={}
        for v in VARIANTS:
            rs=[r for r in runs if r["condition"]==cond and r["variant"]==v]
            aggregate[cond][v]={k:{"mean":statistics.mean(r["metrics"][k] for r in rs),
                                  "sample_sd":statistics.stdev(r["metrics"][k] for r in rs)}
                               for k in ["auc","eer","tar_far_1e-2","tar_far_1e-3"]}
    summary={"interpretation":"Post-hoc exclusion sensitivities of archived checkpoints; no clean-trained model, no new confidence intervals, and no claim that every label/perceptual duplicate is validated.",
             "runs":runs,"aggregated":aggregate}
    (root/"results/corrections/sensitivity_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    lines=[r"\begin{table}[t]",r"\centering",r"\caption{Post-hoc sensitivity mean AUC over three seeds. Unique-probe ROF, known-name-overlap-excluded MFR2, and exact-conflict-excluded RMFRD. Archived models are not retrained; MFR2 gating uses corrected quality inputs. SDs and exclusion ledgers are in the artifact.}",r"\label{tab:sensitivity}",
           r"\resizebox{\columnwidth}{!}{\begin{tabular}{lrrrrr}",r"\toprule",r"Variant & Masked & Sunglasses & Neutral & MFR2 & RMFRD\\",r"\midrule"]
    labels=["Frozen + projection","Whole LoRA","Periocular LoRA","Fixed fusion","Learned gating"]
    for v,label in zip(VARIANTS,labels):
        lines.append(label+" & "+" & ".join(f"{aggregate[c][v]['auc']['mean']:.4f}" for c in names)+r"\\")
    lines += [r"\bottomrule",r"\end{tabular}}",r"\end{table}",""]
    text="\n".join(lines)
    for folder in ["submission_ieee_10page","document"]:
        (root/folder/"integrity_sensitivity.tex").write_text(text,encoding="utf-8")
    print(json.dumps({"runs":len(runs),"auc_means":{c:{v:aggregate[c][v]["auc"]["mean"] for v in VARIANTS} for c in names}},indent=2))
if __name__=="__main__":main()

