"""Independent stdlib checks for additional inference and identity-influence results."""
from pathlib import Path
import json,math,statistics
from verify_results import read,digest,score_metrics,align,KEYS

def verify_strengthening(root):
    out=root/'results/shared_crop_sface';report=json.loads((out/'REPORT.json').read_text())
    assert report['status']=='complete' and report['device']=='cpu'
    assert digest(root/'code/evaluate_shared_crop_sface.py')==report['evaluator_sha256']
    assert report['model_sha256']=='0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79'
    assert digest(out/'image_ledger.csv')==report['image_ledger_sha256']
    ledger=read(out/'image_ledger.csv');original={x['path']:x for x in read(root/'results/sface/image_ledger.csv')}
    assert len(ledger)==report['unique_images']==3402 and {x['path'] for x in ledger}==set(original)
    assert all(x['sha256']==original[x['path']]['sha256'] for x in ledger)
    loaded={};points=0
    for name,item in report['protocols'].items():
        path=out/f'{name}_raw_scores.csv';assert digest(path)==item['raw_scores_sha256']
        reference=root/'results/sface'/f'{name}_raw_scores.csv';assert digest(reference)==item['reference_score_file_sha256']
        rows=read(path);reference_rows=read(reference);align(rows,reference_rows)
        for current,previous in zip(rows,reference_rows):
            assert {k:v for k,v in current.items() if k not in ['score','embedding_failure']}=={k:v for k,v in previous.items() if k not in ['score','detector_failure']}
        actual=score_metrics(rows)
        for key in KEYS+['n_pairs','n_genuine','n_impostor']:
            assert abs(actual[key]-item['metrics'][key])<1e-8,(name,key)
        assert sum(int(x['embedding_failure']) for x in rows)==item['failed_pairs']
        assert all(float(x['score'])==-1 for x in rows if int(x['embedding_failure']))
        loaded[name]=rows
    for name,item in report['protocols'].items():
        if name.startswith('val_'):continue
        validation=item['calibration_validation_protocol'];negative=sorted(float(x['score']) for x in loaded[validation] if x['label']=='0')
        for target,pair in item['validation_calibrated'].items():
            threshold=math.nextafter(negative[-int(math.floor(float(target)*len(negative)))-1],math.inf)
            for side,rows in [('validation',loaded[validation]),('test',loaded[name])]:
                point=pair[side];assert point['threshold']==threshold
                for label,count,total,rate in [('0','false_accepts','impostors','far'),('1','true_accepts','genuine','tar')]:
                    subset=[x for x in rows if x['label']==label];accepted=sum(float(x['score'])>=threshold for x in subset)
                    assert point[count]==accepted and point[total]==len(subset)
                    assert abs(point[rate]-accepted/len(subset))<1e-12
                points+=1
    sensitivity=json.loads((root/'results/strengthening/MASKED_IDENTITY_SENSITIVITY.json').read_text())
    for name,value in sensitivity['input_sha256'].items():assert digest(root/name)==value
    variants=['frozen_whole','whole_lora','peri_lora','fixed_fusion','gated_fusion'];subset_count=0
    results={v:[] for v in variants};winners=[];deltas=[]
    for item in sensitivity['subsets']:
        node=item['removed_identity'];means={}
        for variant in variants:
            aucs=[]
            for seed in [7,42,123]:
                rows=read(root/f'results/cpu_clean/evaluation/seed{seed}_{variant}/test_masked_raw_scores.csv')
                kept=[x for x in rows if node not in [x['probe_identity'],x['enroll_identity']]]
                assert len(kept)==item['retained_pairs'] and sum(x['label']=='1' for x in kept)==item['retained_genuine']
                aucs.append(score_metrics(kept)['auc']);subset_count+=1
            # Python versions can differ in final-bit floating-point summation.
            # Keep exact hashes/counts, but compare derived AUCs to 1e-12.
            expected=item['metrics'][variant]
            assert len(aucs)==len(expected['seed_aucs']) and all(math.isclose(a,b,rel_tol=0,abs_tol=1e-12) for a,b in zip(aucs,expected['seed_aucs'])),(node,variant,'seed AUCs')
            means[variant]=statistics.mean(aucs);assert math.isclose(means[variant],expected['auc_mean'],rel_tol=0,abs_tol=1e-12),(node,variant,'mean AUC');results[variant].append(means[variant])
        winner=max(variants,key=means.get);winners.append(winner);assert winner==item['highest_mean_auc_variant']
        delta=means['gated_fusion']-means['fixed_fusion'];assert math.isclose(delta,item['gated_minus_fixed_mean_auc'],rel_tol=0,abs_tol=1e-12),(node,'AUC contrast');deltas.append(delta)
    assert len(winners)==sensitivity['identity_nodes']==9
    for variant in variants:
        row=sensitivity['summary'][variant]
        assert math.isclose(row['minimum_auc_mean'],min(results[variant]),rel_tol=0,abs_tol=1e-12) and math.isclose(row['maximum_auc_mean'],max(results[variant]),rel_tol=0,abs_tol=1e-12),(variant,'AUC range')
        assert row['highest_mean_count']==winners.count(variant)
    assert len(sensitivity['gated_minus_fixed_range'])==2 and all(math.isclose(a,b,rel_tol=0,abs_tol=1e-12) for a,b in zip(sensitivity['gated_minus_fixed_range'],[min(deltas),max(deltas)])),'AUC contrast range'
    tex=(root/'submission_ieee_10page/IEEE_TBIOM_Submission_10Page_Final.tex').read_text(encoding='utf-8')
    for name in ['test_masked','test_sunglasses','test_neutral','mfr2','rmfrd']:
        assert f"{report['protocols'][name]['metrics']['auc']:.4f}" in tex
    assert 'eight of nine' in tex and '0.8948--0.9440' in tex
    return {'shared_crop_score_files':len(loaded),'shared_crop_images':len(ledger),'calibrated_operating_points':points,
            'masked_identity_subsets':9,'per_seed_subset_aucs':subset_count}

if __name__=='__main__':print(json.dumps(verify_strengthening(Path(__file__).resolve().parent.parent),indent=2))
