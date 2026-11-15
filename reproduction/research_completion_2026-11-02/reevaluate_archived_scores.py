"""Recompute archived-model results on new pairs with identical endpoints.

Reusing a saved score is valid only when both image/crop endpoints and the label
are exactly the same. Missing endpoint pairs fail rather than being invented.
"""
import csv,json,sys
import numpy as np
from cpu_common import HERE,RELEASE,EXPERIMENT,RUN,SEEDS,VARIANTS,sha,save_json
from audit_images import read,write
sys.path.insert(0,str(RELEASE/'code'))
from verify_results import score_metrics

def key(r):
    return tuple(r[k] for k in ['probe_face_path','probe_peri_path','enroll_face_path','enroll_peri_path','label'])

def main():
    out=HERE/'archived_reevaluation';out.mkdir(exist_ok=True)
    results=[]
    for condition in ['masked','sunglasses','neutral']:
        original=read(RELEASE/f'manifests/rof_{condition}_pairs.csv')
        targetpath=EXPERIMENT/f'test_{condition}_pairs.csv';target=read(targetpath)
        oldids={r['pair_id']:key(r) for r in original}
        for seed in SEEDS:
            for variant in VARIANTS:
                source=RELEASE/f'results/seed_sweep/rof_seed_sweep/seed{seed}_{variant}_{condition}_raw_scores.csv'
                raw=read(source)
                saved={oldids[r['pair_id']]:r['score'] for r in raw}
                missing=[r['pair_id'] for r in target if key(r) not in saved]
                if missing:raise ValueError(f'{source}: {len(missing)} new endpoint pairs need actual inference')
                selected=[dict(r,score=saved[key(r)]) for r in target]
                dest=out/f'seed{seed}_{variant}_{condition}_raw_scores.csv';write(dest,selected)
                metrics=score_metrics(selected)
                results.append({'seed':seed,'variant':variant,'condition':condition,'metrics':metrics,
                    'source':str(source.relative_to(RELEASE)),'source_sha256':sha(source),
                    'pairs':str(targetpath.relative_to(HERE)),'pairs_sha256':sha(targetpath),
                    'raw_scores':dest.name,'raw_scores_sha256':sha(dest),
                    'training_status':'historical checkpoint; repeated training images remain; not clean-trained'})
    summary=[]
    for condition in ['masked','sunglasses','neutral']:
        for variant in VARIANTS:
            rows=[r for r in results if r['condition']==condition and r['variant']==variant]
            summary.append({'condition':condition,'variant':variant,
                'auc_mean':float(np.mean([r['metrics']['auc'] for r in rows])),
                'auc_seed_sd':float(np.std([r['metrics']['auc'] for r in rows],ddof=1)),
                'eer_mean':float(np.mean([r['metrics']['eer'] for r in rows]))})
    report={'status':'completed actual recomputation from matching archived endpoint scores',
        'scope':'known duplicate-excluded prospective ROF test pairs; historical training unchanged; no validation-calibrated threshold claim',
        'runs':results,'summary':summary,'evaluator_sha256':sha(__file__)}
    save_json(out/'REEVALUATION_REPORT.json',report)
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
