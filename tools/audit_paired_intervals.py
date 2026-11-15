"""Independently reconstruct recorded paired identity-resampling intervals."""
from pathlib import Path
import csv, json
import numpy as np

ROOT=Path(__file__).resolve().parent.parent

def main():
    summary=json.loads((ROOT/'results/cpu_clean/RESULTS_SUMMARY.json').read_text())
    results=[]
    for contrast in summary['paired_auc_comparisons']:
        condition=contrast['condition'];left,right=contrast['contrast'].split(' minus ')
        datasets=[];reference=None;index=None
        for seed in [7,42,123]:
            for variant in [left,right]:
                path=ROOT/f'results/cpu_clean/evaluation/seed{seed}_{variant}/{condition}_raw_scores.csv'
                with path.open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
                keys=[tuple(sorted((k,v) for k,v in row.items() if k!='score')) for row in rows]
                if reference is None:
                    reference=keys
                    endpoints=[(r['identity1'],r['identity2']) if 'identity1' in r else (r['probe_identity'],r['enroll_identity']) for r in rows]
                    names=sorted({name for pair in endpoints for name in pair});index={name:i for i,name in enumerate(names)}
                    a=np.array([index[pair[0]] for pair in endpoints]);b=np.array([index[pair[1]] for pair in endpoints])
                    labels=np.array([int(row['label']) for row in rows],dtype=bool)
                assert reference==keys
                values=np.array([float(row['score']) for row in rows])
                unique,groups=np.unique(values,return_inverse=True)
                datasets.append((groups[labels],groups[~labels],len(unique)))
        rng=np.random.default_rng(contrast['bootstrap_seed']);deltas=[]
        for _ in range(contrast['requested_replicates']):
            counts=rng.multinomial(len(index),np.full(len(index),1/len(index)))
            # A genuine same-node edge has one sampled identity, not two independent nodes.
            weights=np.where(a==b,counts[a],counts[a]*counts[b])
            positive=weights[labels];negative=weights[~labels]
            if positive.sum()==0 or negative.sum()==0:continue
            aucs=[]
            for posgroups,neggroups,size in datasets:
                pos=np.bincount(posgroups,weights=positive,minlength=size)
                neg=np.bincount(neggroups,weights=negative,minlength=size)
                # Midrank concordance counts a tied genuine/impostor pair as one half.
                below=np.r_[0,np.cumsum(neg)[:-1]]
                aucs.append(float(np.dot(pos,below+neg/2)/(positive.sum()*negative.sum())))
            deltas.append(float(np.mean(np.array(aucs)[::2]-np.array(aucs)[1::2])))
        actual=np.percentile(deltas,[2.5,97.5])
        np.testing.assert_allclose(actual,contrast['paired_two_endpoint_identity_bootstrap_ci95'],atol=1e-12,rtol=0)
        assert len(deltas)==contrast['valid_replicates']
        results.append({'condition':condition,'contrast':contrast['contrast'],'ci95':actual.tolist(),'valid_replicates':len(deltas)})
        print(condition,contrast['contrast'],'interval matches',flush=True)
    record={'date':'2026-11-16','status':'passed','comparisons':results,
            'scope':'Independent NumPy midrank reconstruction from raw scores with the recorded two-endpoint multinomial resampling rule and shared three-seed weights. Conditional sensitivity intervals, not population confidence or corrected multiple-testing inference.'}
    (ROOT/'document/PAIRED_INTERVAL_AUDIT.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
