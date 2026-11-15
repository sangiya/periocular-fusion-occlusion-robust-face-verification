"""Produce a growing report; full-grid completion is explicit, never inferred."""
import csv,json
from pathlib import Path
import numpy as np
from cpu_common import HERE,RUN,SEEDS,VARIANTS,sha,save_json

CONDITIONS=['test_masked','test_sunglasses','test_neutral','mfr2','rmfrd']

def bootstrap_paired(records,condition,left,right):
    sources={}
    for seed in SEEDS:
        for variant in (left,right):
            report=records[(seed,variant)]
            p=RUN/'evaluation'/f'seed{seed}_{variant}'/report['protocols'][condition]['raw_scores']
            with p.open(encoding='utf-8',newline='') as f:rs=list(csv.DictReader(f))
            sources[(seed,variant)]=rs
    reference=sources[(SEEDS[0],left)]
    def endpoints(r):
        return (r['identity1'],r['identity2']) if 'identity1' in r else (r['probe_identity'],r['enroll_identity'])
    def key(r):return tuple(sorted((k,v) for k,v in r.items() if k!='score'))
    keys=[key(r) for r in reference]
    for rows in sources.values():
        if [key(r) for r in rows]!=keys:raise ValueError('Paired comparison input alignment differs')
    nodes=sorted({s for r in reference for s in endpoints(r)});ids={s:i for i,s in enumerate(nodes)}
    a=np.array([ids[endpoints(r)[0]] for r in reference]);b=np.array([ids[endpoints(r)[1]] for r in reference]);same=a==b
    labels=np.array([int(r['label']) for r in reference])
    functions={}
    for name,rows in sources.items():
        scores=np.array([float(r['score']) for r in rows]);order=np.argsort(scores,kind='stable')
        starts=np.r_[0,np.flatnonzero(np.diff(scores[order])!=0)+1]
        def calc(w,order=order,starts=starts):
            pos=np.add.reduceat((w*labels)[order],starts);neg=np.add.reduceat((w*(1-labels))[order],starts)
            if not pos.sum() or not neg.sum():return None
            return float(np.sum(pos*(np.cumsum(neg)-neg+.5*neg))/(pos.sum()*neg.sum()))
        functions[name]=calc
    rng=np.random.default_rng(42);values=[]
    for _ in range(1000):
        count=rng.multinomial(len(nodes),np.full(len(nodes),1/len(nodes)))
        weights=count[a]*count[b];weights[same]=count[a[same]]
        diffs=[]
        for seed in SEEDS:
            l=functions[(seed,left)](weights);r=functions[(seed,right)](weights)
            if l is None or r is None:break
            diffs.append(l-r)
        if len(diffs)==len(SEEDS):values.append(float(np.mean(diffs)))
    delta=[records[(seed,left)]['protocols'][condition]['metrics']['auc']-records[(seed,right)]['protocols'][condition]['metrics']['auc'] for seed in SEEDS]
    return {'condition':condition,'contrast':f'{left} minus {right}','seed_differences':delta,
        'mean_auc_difference':float(np.mean(delta)),'seed_sd':float(np.std(delta,ddof=1)),
        'paired_two_endpoint_identity_bootstrap_ci95':np.percentile(values,[2.5,97.5]).tolist(),
        'valid_replicates':len(values),'requested_replicates':1000,'bootstrap_seed':42,
        'interpretation':'Conditional test-identity resampling sensitivity, averaged over three fixed trained seeds; descriptive, no multiple-comparison significance claim.'}

def main():
    records={}; hashes={}
    for p in sorted((RUN/'evaluation').glob('*/EVALUATION_REPORT.json')):
        r=json.loads(p.read_text());key=(r['seed'],r['variant'])
        if key in records:raise ValueError('Duplicate completed evaluation')
        if r['status']!='complete':continue
        for item in r['protocols'].values():
            if sha(p.parent/item['raw_scores'])!=item['raw_scores_sha256']:raise ValueError('Score hash mismatch')
        records[key]=r;hashes[str(p.relative_to(HERE))]=sha(p)
    grid={(s,v) for s in SEEDS for v in VARIANTS};complete=set(records)==grid
    rows=[]
    for condition in CONDITIONS:
        for variant in VARIANTS:
            runs=[records[(s,variant)] for s in SEEDS if (s,variant) in records]
            if not runs:continue
            metrics={key:[r['protocols'][condition]['metrics'][key] for r in runs] for key in ['auc','eer','tar_far_1e-2','tar_far_1e-3']}
            row={'condition':condition,'variant':variant,'completed_seeds':len(runs)}
            for key,values in metrics.items():
                row[key+'_mean']=float(np.mean(values));row[key+'_seed_sd']=float(np.std(values,ddof=1)) if len(values)>1 else None
            rows.append(row)
    paired=[]
    if complete:
        for condition in CONDITIONS:
            for left,right in [('gated_fusion','fixed_fusion'),('whole_lora','frozen_whole')]:
                paired.append(bootstrap_paired(records,condition,left,right))
    report={'state':'complete' if complete else 'partial','completed_models':len(records),'expected_models':15,
        'missing':[f'seed{s}_{v}' for s,v in sorted(grid-set(records))],
        'summary':rows,'paired_auc_comparisons':paired,'evaluation_report_hashes':hashes,
        'journal_submission_ready':False,'note':'Scientific interpretation, author review, similarity screening and manuscript revision are separate tasks.'}
    save_json(RUN/'RESULTS_SUMMARY.json',report)
    text=['# CPU research results','',f"Completed and evaluated models: {len(records)}/15. Status: {report['state']}.",'',
        'All new runs use the frozen 6,171-row duplicate-excluded manifest. Historical models are separate.','',
        '| Protocol | Variant | Seeds complete | Mean AUC | Seed SD |','|---|---|---:|---:|---:|']
    for r in rows:
        sd='pending' if r['auc_seed_sd'] is None else f"{r['auc_seed_sd']:.6f}"
        text.append(f"| {r['condition']} | {r['variant']} | {r['completed_seeds']} | {r['auc_mean']:.6f} | {sd} |")
    text += ['','Validation-calibrated operating points, actual FAR counts, gate controls, and provenance are in each EVALUATION_REPORT.json.',
             'Partial results do not replace the main manuscript tables. No journal-readiness or detector-clearance claim is made.','']
    (RUN/'RESULTS_SUMMARY.md').write_text('\n'.join(text),encoding='utf-8')
    print(f"Research summary: {len(records)}/15 fully trained and evaluated models; state={report['state']}",flush=True)

if __name__=='__main__':main()
