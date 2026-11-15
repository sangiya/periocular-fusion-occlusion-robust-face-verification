"""Verify archived and corrected results, raw scores, manuscript tables and portable provenance.
No model weights, image datasets, torch, or sklearn are needed.
ALL CHECKS PASSED means these explicit artifact checks pass, not journal readiness.
"""
from __future__ import annotations
import argparse,csv,hashlib,itertools,json,math,re,statistics
from pathlib import Path

SEEDS=[7,42,123]
VARIANTS=["frozen_whole","whole_lora","peri_lora","fixed_fusion","gated_fusion"]
KEYS=["auc","eer","tar_far_1e-2","tar_far_1e-3"]
ROOT=Path(__file__).resolve().parent.parent

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
    with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def score_metrics(rows):
    if not rows:raise ValueError("Empty raw-score file")
    values=[]
    for r in rows:
        score=float(r["score"]);label=int(r["label"])
        if not math.isfinite(score) or label not in (0,1):raise ValueError("Invalid score/label")
        values.append((score,label))
    pos=sum(y for _,y in values);neg=len(values)-pos
    if not pos or not neg:raise ValueError("Both score classes are required")
    values.sort(reverse=True);points=[(0.,0.)];tp=fp=0
    for _,group in itertools.groupby(values,key=lambda x:x[0]):
        for _,y in group:tp+=y;fp+=1-y
        points.append((fp/neg,tp/pos))
    auc=sum((x1-x0)*(y1+y0)/2 for (x0,y0),(x1,y1) in zip(points,points[1:]))
    eer=None
    for (x0,y0),(x1,y1) in zip(points,points[1:]):
        d0=x0+y0-1;d1=x1+y1-1
        if d0<=0<=d1:
            alpha=-d0/(d1-d0) if d1!=d0 else 0
            eer=x0+alpha*(x1-x0);break
    return {"auc":auc,"eer":eer,
            "tar_far_1e-2":max(y for x,y in points if x<=.01),
            "tar_far_1e-3":max(y for x,y in points if x<=.001),
            "n_pairs":len(values),"n_genuine":pos,"n_impostor":neg}

def logical_path(s):
    s=s.replace("\\","/")
    for part in ["data/","work/"]:
        at=s.find("/"+part)
        if at>=0:return s[at+1:]
    return s

def align(raw,pairs):
    if len(raw)!=len(pairs):raise ValueError("Raw/protocol lengths differ")
    for r,p in zip(raw,pairs):
        if r["label"]!=p["label"]:raise ValueError("Raw/protocol labels differ")
        for key in ["pair_id","probe_identity","enroll_identity","identity1","identity2"]:
            if key in r and key in p and r[key]!=p[key]:raise ValueError(f"Raw/protocol {key} differs")
        for key in ["face_path1","face_path2"]:
            if key in r and logical_path(r[key])!=logical_path(p[key]):raise ValueError(f"Raw/protocol {key} differs")
        for key,target in [("enroll_id","enroll_image_id"),("probe_id","probe_image_id")]:
            if key in r and r[key]!=p[target]:raise ValueError(f"Raw/protocol {key} differs")

def verify(root,results):
    failures=[];counts={"archived_metrics":0,"raw_files":0,"table_numbers":0,"correction_runs":0,"sensitivity_runs":0}
    def check(name,fn):
        try:fn()
        except Exception as e:failures.append(f"{name}: {e}")
    def require(ok,message):
        if not ok:raise ValueError(message)
    protocols={"masked":"rof_masked_pairs.csv","sunglasses":"rof_sunglasses_pairs.csv","neutral":"rof_neutral_pairs.csv",
               "mfr2":"mfr2_official_complete_pairs.csv","rmfrd":"rmfrd_pairs.csv"}
    pairs={k:read(root/"manifests"/v) for k,v in protocols.items()}
    mapping=json.loads((root/"manifests/provenance_map.json").read_text())
    metrics={}
    for folder,conditions in [("rof_seed_sweep",["masked","sunglasses","neutral"]),("cross_dataset",["mfr2","rmfrd","neutral"])]:
        expected={f"seed{s}_{v}_{c}_metrics.json" for s in SEEDS for v in VARIANTS for c in conditions}
        found={p.name for p in (results/folder).glob("*_metrics.json")}
        check(folder+" exact grid",lambda:require(found==expected,f"Missing={expected-found}; unexpected={found-expected}"))
        for seed in SEEDS:
            for v in VARIANTS:
                for cond in conditions:
                    path=results/folder/f"seed{seed}_{v}_{cond}_metrics.json"
                    if not path.is_file():continue
                    j=json.loads(path.read_text());m=j.get("metrics",j);metrics[(folder,seed,v,cond)]=m
                    counts["archived_metrics"]+=1
                    record=mapping["protocols"][cond]
                    check(path.name+" provenance",lambda j=j,record=record,cond=cond:(
                        require(bool(re.fullmatch("[0-9a-f]{64}",j.get("checkpoint_sha256",""))),"Missing/invalid checkpoint hash"),
                        require(j.get("pairs_sha256") in record["recorded_original_hashes"],"Unknown recorded original protocol hash"),
                        require(digest(root/"manifests"/protocols[cond])==record["portable_sha256"],"Portable protocol hash mismatch")))
                    if folder=="rof_seed_sweep":
                        check(path.name+" device",lambda j=j:require(j.get("device")=="cpu","Archived ROF device must be recorded as cpu"))
                    raw=path.with_name(path.name.replace("_metrics.json","_raw_scores.csv"))
                    if raw.exists():
                        def raw_check(raw=raw,m=m,cond=cond):
                            rs=read(raw);align(rs,pairs[cond]);fresh=score_metrics(rs)
                            for key in KEYS+["n_pairs","n_genuine","n_impostor"]:
                                require(abs(fresh[key]-m[key])<=1e-5,f"{key}: {fresh[key]} != {m[key]}")
                        check(raw.name,raw_check);counts["raw_files"]+=1
                    elif not (folder=="cross_dataset" and cond=="neutral"):
                        failures.append(f"Missing raw scores: {raw}")
    for seed in SEEDS:
        for v in VARIANTS:
            def neutral_cross(seed=seed,v=v):
                a=metrics[("rof_seed_sweep",seed,v,"neutral")]
                b=metrics[("cross_dataset",seed,v,"neutral")]
                for k in KEYS:require(abs(a[k]-b[k])<=1e-5,"Cross-evaluator neutral metric mismatch")
            check(f"neutral cross-check {seed}/{v}",neutral_cross)
    summary=json.loads((results/"seed_sweep_summary.json").read_text())
    check("summary grid",lambda:(
        require(sorted(summary["seeds"])==SEEDS,"Summary seeds differ"),
        require(summary["variants"]==VARIANTS,"Summary variants differ"),
        require(summary["protocols"]==["masked","sunglasses","neutral"],"Summary protocols differ"),
        require(len(summary["per_run"])==45,"Summary row count differs")))
    for r in summary["per_run"]:
        def summary_row(r=r):
            m=metrics[("rof_seed_sweep",r["seed"],r.get("variant_inferred") or r["variant"],r["condition"])]
            for key in KEYS:require(abs(float(r[key])-m[key])<1e-8,f"Summary mismatch {r['seed']} {key}")
        check("summary row",summary_row)
    comparisons=list(results.glob("comparison_*.json"))
    check("comparison completeness",lambda:require(len(comparisons)==18,"Expected 18 comparisons"))
    for p in comparisons:
        def comparison(p=p):
            j=json.loads(p.read_text());seed=int(re.search(r"seed(\d+)",p.name)[1]);c=j["condition"]
            ref=metrics[("rof_seed_sweep",seed,j["reference"],c)];cand=metrics[("rof_seed_sweep",seed,j["candidate"],c)]
            for k in ["auc","eer"]:require(abs(cand[k]-ref[k]-j[f"{k}_delta_candidate_minus_reference"])<1e-8,"Comparison point delta mismatch")
        check(p.name,comparison)
    corrected={}
    for seed in SEEDS:
        p=root/f"results/corrections/mfr2_quality_v2/seed{seed}_gated_fusion_mfr2_metrics.json"
        def correction(p=p,seed=seed):
            j=json.loads(p.read_text());raw=p.with_name(p.name.replace("_metrics.json","_raw_scores.csv"))
            require(j["quality_vector"]==[1.,0.,0.,1.],"Incorrect corrected quality vector")
            require(j["training_seed"]==seed,"Incorrect training seed")
            require(j["device"]=="cpu","Corrected release run must record CPU")
            old=json.loads((results/f"cross_dataset/seed{seed}_gated_fusion_mfr2_metrics.json").read_text())
            require(j["checkpoint_sha256"]==old["checkpoint_sha256"],"Corrected run did not use the final historical checkpoint")
            require(j["bootstrap_seed"]==42 and j["bootstrap"]==1000,"Corrected bootstrap configuration differs")
            require(j["elapsed_seconds"]>0,"Missing corrected run timing")

            require(j["evaluator_sha256"]==digest(root/"code/evaluate_all_cross_dataset_fixed.py"),"Corrected evaluator has changed since inference")
            require(j["raw_scores_sha256"]==digest(raw),"Corrected raw-score hash mismatch")
            require(j["pairs_sha256"] in mapping["protocols"]["mfr2"]["recorded_original_hashes"] + [mapping["protocols"]["mfr2"]["portable_sha256"]],"Correction pairs differ")
            rs=read(raw);align(rs,pairs["mfr2"]);fresh=score_metrics(rs)
            for k in KEYS:require(abs(fresh[k]-j["metrics"][k])<=1e-5,f"Corrected {k} mismatch")
            corrected[seed]=j["metrics"]
        check(f"quality-corrected seed {seed}",correction);counts["correction_runs"]+=1
    tex=(root/"submission_ieee_10page/IEEE_TBIOM_Submission_10Page_Final.tex").read_text(encoding="utf-8")
    completed={}
    if (root/"results/cpu_clean/RESULTS_SUMMARY.json").exists():
        from verify_completed_cpu import verify_completed
        check("completed CPU experiment",lambda:counts.update({"completed_cpu":verify_completed(root)}))
        for s in SEEDS:
            for v in VARIANTS:
                completed[(s,v)]=json.loads((root/f"results/cpu_clean/evaluation/seed{s}_{v}/EVALUATION_REPORT.json").read_text())
    for label,cond,folder in [("rofmasked","masked","rof_seed_sweep"),("rofsunglasses","sunglasses","rof_seed_sweep"),("rofneutral","neutral","rof_seed_sweep"),("mfr2","mfr2","cross_dataset"),("rmfrd","rmfrd","cross_dataset")]:
        def table(label=label,cond=cond,folder=folder):
            block=tex.split("\\label{tab:"+label+"}")[1].split("\\bottomrule")[0]
            ls=[l for l in block.splitlines() if "\\pm" in l]
            require(len(ls)==5,f"Expected 5 rows in {label}")
            for v,line in zip(VARIANTS,ls):
                cells=re.findall(r"(?:\\textbf\{)?(\.\d+)\}?\$_\{\\pm(\.\d+)\}",line)
                require(len(cells)==4,"Expected four mean/SD cells")
                for key,(mean,sd) in zip(KEYS,cells):
                    protocol="test_"+cond if cond in ("masked","sunglasses","neutral") else cond
                    vals=[(completed[(s,v)]["protocols"][protocol]["metrics"] if completed else (corrected[s] if cond=="mfr2" and v=="gated_fusion" else metrics[(folder,s,v,cond)]))[key] for s in SEEDS]
                    require(abs(statistics.mean(vals)-float(mean))<=.000050001,f"{label}/{v}/{key} mean")
                    require(abs(statistics.stdev(vals)-float(sd))<=.000500001,f"{label}/{v}/{key} SD")
                    counts["table_numbers"]+=2
        check(label+" manuscript table",table)
    clean=root/"manifests/cleaned"
    train=read(clean/"rof_training_clean.csv");seen=set();identities={}
    for r in train:
        check("clean ROF hash uniqueness",lambda r=r:require(r["sha256"] not in seen,"Repeated image hash"))
        seen.add(r["sha256"]);identities.setdefault(r["identity"],set()).add(r["split"])
    check("clean identity splits",lambda:require(all(len(v)==1 for v in identities.values()),"Identity split overlap"))
    if (root/"results/corrections/sensitivity_summary.json").exists():
        sens=json.loads((root/"results/corrections/sensitivity_summary.json").read_text())
        grid={(r["seed"],r["variant"],r["condition"]) for r in sens["runs"]}
        expected={(s,v,c) for s in SEEDS for v in VARIANTS for c in protocols}
        check("sensitivity completeness",lambda:require(grid==expected and len(sens["runs"])==75,"Sensitivity grid is incomplete/duplicated"))
        for r in sens["runs"]:
            def sensitivity(r=r):
                raw=root/r["raw_scores"];pair=root/r["pairs"]
                require(digest(raw)==r["raw_sha256"] and digest(pair)==r["pairs_sha256"],"Sensitivity input hash mismatch")
                rs=read(raw);align(rs,read(pair));m=score_metrics(rs)
                for k in KEYS:require(abs(m[k]-r["metrics"][k])<1e-8,"Sensitivity metric mismatch")
            check("sensitivity "+r["raw_scores"],sensitivity);counts["sensitivity_runs"]+=1
        table_text=(root/"submission_ieee_10page/integrity_sensitivity.tex").read_text(encoding="utf-8")
        table_rows=[line for line in table_text.splitlines() if re.match(r"^(Frozen|Whole|Periocular|Fixed|Learned)",line)]
        def sensitivity_table():
            require(len(table_rows)==5,"Expected five sensitivity table rows")
            for v,line in zip(VARIANTS,table_rows):
                cells=re.findall(r"\b0\.\d{4}\b",line)
                require(len(cells)==5,"Expected five sensitivity AUCs")
                for cond,cell in zip(protocols,cells):
                    vals=[row["metrics"]["auc"] for row in sens["runs"] if row["condition"]==cond and row["variant"]==v]
                    require(abs(statistics.mean(vals)-float(cell))<=.000050001,"Sensitivity table mean mismatch")
            require((root/"document/integrity_sensitivity.tex").read_bytes()==(root/"submission_ieee_10page/integrity_sensitivity.tex").read_bytes(),"Shared sensitivity sources differ")
        check("sensitivity manuscript table",sensitivity_table)
        counts["sensitivity_table_numbers"]=25
    else:failures.append("Missing sensitivity_summary.json")
    build=json.loads((root/"document/BUILD_REPORT.json").read_text())
    for name,hash_value in build["inputs"].items():
        check("PDF build input "+name,lambda name=name,hash_value=hash_value:require(digest(root/name)==hash_value,"PDF build input changed since compilation"))
    for record in build["pdfs"]:
        check(record["file"]+" compiled binding",lambda record=record:(
            require(digest(root/record["file"])==record["sha256"],"PDF hash differs from successful build"),
            require(record["pages"]==10,"Expected ten-page manuscript")))
    thesis_path=root/"document/thesis/THESIS_SOURCE_RECORD.json"
    if thesis_path.exists():
        def thesis_binding():
            record=json.loads(thesis_path.read_text())
            require(record['journal_source_sha256']==digest(root/record['journal_source']),'Thesis cites stale journal source')
            require(record['thesis_source_sha256']==digest(root/'document/thesis/Research_Thesis_Draft.tex'),'Thesis source changed since checking')
            require(record['pdf_sha256']==digest(root/'document/thesis/Research_Thesis_Draft.pdf'),'Thesis PDF changed since compilation')
            require(record['method_diagram_sha256']==digest(root/'document/thesis/fig_gated_architecture.pdf'),'Thesis method diagram changed since checking')
            require(record['summary_sha256']==digest(root/'results/cpu_clean/RESULTS_SUMMARY.json'),'Thesis results summary changed')
            require(record['overfull_boxes']==0 and record['missing_characters']==0,'Thesis layout issues remain')
            require(record['verified_measured_table_blocks']==10 and record['verified_register_rows']==25,'Incomplete thesis numerical checking')
            counts['thesis_pages']=record['pages']
        check('thesis source/result/PDF bindings',thesis_binding)
    return {"counts":counts,"failures":failures,"scope":"Artifact arithmetic, raw-score alignment, table values, recorded provenance mappings, corrected inference and clean input checks; not publication approval."}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument("--root",type=Path,default=ROOT);ap.add_argument("--results-dir",type=Path);ap.add_argument("--report",type=Path)
    a=ap.parse_args()
    try:report=verify(a.root,a.results_dir or a.root/"results/seed_sweep")
    except Exception as e:report={"counts":{},"failures":[f"Required input/structure error: {e}"]}
    print(json.dumps(report,indent=2))
    if a.report:a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2),encoding="utf-8")
    print("RESULT: CHECKS FAILED" if report["failures"] else "RESULT: ALL CHECKS PASSED")
    return 1 if report["failures"] else 0
if __name__=="__main__":raise SystemExit(main())

