"""Delete each masked-test identity node and all incident pairs, without retraining."""
from pathlib import Path
import json,statistics
from verify_results import read,score_metrics,digest

ROOT=Path(__file__).resolve().parent.parent
SEEDS=[7,42,123]
VARIANTS=['frozen_whole','whole_lora','peri_lora','fixed_fusion','gated_fusion']

def main():
    scores={};hashes={};reference=None
    for seed in SEEDS:
        for variant in VARIANTS:
            path=ROOT/f'results/cpu_clean/evaluation/seed{seed}_{variant}/test_masked_raw_scores.csv'
            rows=read(path);keys=[(r['pair_id'],r['label'],r['probe_identity'],r['enroll_identity']) for r in rows]
            if reference is None:reference=keys
            assert reference==keys
            scores[(seed,variant)]=rows;hashes[path.relative_to(ROOT).as_posix()]=digest(path)
    nodes=sorted({name for row in next(iter(scores.values())) for name in [row['probe_identity'],row['enroll_identity']]})
    assert len(nodes)==9
    results=[]
    for node in nodes:
        metrics={}
        for variant in VARIANTS:
            aucs=[]
            for seed in SEEDS:
                rows=[r for r in scores[(seed,variant)] if node not in (r['probe_identity'],r['enroll_identity'])]
                aucs.append(score_metrics(rows)['auc'])
            metrics[variant]={'seed_aucs':aucs,'auc_mean':statistics.mean(aucs)}
        results.append({'removed_identity':node,'retained_pairs':len(rows),'retained_genuine':sum(r['label']=='1' for r in rows),
                        'retained_impostor':sum(r['label']=='0' for r in rows),'metrics':metrics,
                        'gated_minus_fixed_mean_auc':metrics['gated_fusion']['auc_mean']-metrics['fixed_fusion']['auc_mean'],
                        'highest_mean_auc_variant':max(VARIANTS,key=lambda v:metrics[v]['auc_mean'])})
    summary={v:{'minimum_auc_mean':min(r['metrics'][v]['auc_mean'] for r in results),
                'maximum_auc_mean':max(r['metrics'][v]['auc_mean'] for r in results),
                'highest_mean_count':sum(r['highest_mean_auc_variant']==v for r in results)} for v in VARIANTS}
    report={'date':'2026-11-16','method':'Leave one identity node out of masked ROF test; delete all incident pairs; average AUC over three existing checkpoints; no retraining or threshold reselection.',
            'scope':'Post-hoc finite-protocol influence diagnostic, not independent identities, population uncertainty, or additional training seeds.',
            'input_sha256':hashes,'identity_nodes':9,'subsets':results,'summary':summary,
            'gated_minus_fixed_range':[min(r['gated_minus_fixed_mean_auc'] for r in results),max(r['gated_minus_fixed_mean_auc'] for r in results)]}
    out=ROOT/'results/strengthening';out.mkdir(exist_ok=True)
    (out/'MASKED_IDENTITY_SENSITIVITY.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'summary':summary,'gated_minus_fixed_range':report['gated_minus_fixed_range']},indent=2))

if __name__=='__main__':main()
