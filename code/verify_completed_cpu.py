"""Independent standard-library verification of completed CPU evidence and calibration."""
from pathlib import Path
import csv,hashlib,json,math,statistics
from verify_results import SEEDS,VARIANTS,KEYS,score_metrics,align,read,digest,recorded_relative_path

def verify_completed(root):
    base=root/'results/cpu_clean';src=root/'reproduction/research_completion_2026-11-02'
    summary=json.loads((base/'RESULTS_SUMMARY.json').read_text())
    assert summary['state']=='complete' and summary['completed_models']==15 and not summary['missing'],'Incomplete model grid'
    assert json.loads((base/'SWEEP_STATUS.json').read_text())['state']=='complete'
    records={};counts={'models':0,'raw_score_files':0,'calibrated_operating_points':0,'paired_point_comparisons':0}
    for seed in SEEDS:
        for variant in VARIANTS:
            name=f'seed{seed}_{variant}';folder=base/'evaluation'/name
            r=json.loads((folder/'EVALUATION_REPORT.json').read_text());records[(seed,variant)]=r
            assert r['status']=='complete' and r['seed']==seed and r['variant']==variant and r['device']=='cpu'
            progress=json.loads((base/'training'/(name+'_progress.json')).read_text())
            assert progress['complete'] and progress['optimizer_steps']==1380
            signature=progress['signature'];assert signature['epochs']==5 and signature['max_batches']==0
            assert signature['trainer_sha256']==digest(src/'train_cpu.py')
            assert signature['manifest_sha256']==digest(root/'manifests/cpu_followup/training_manifest.csv')
            expected={'evaluator_sha256':src/'evaluate_cpu.py','common_code_sha256':src/'cpu_common.py',
                      'model_code_sha256':src/'cpu_runs/runtime/model.py','metrics_code_sha256':src/'cpu_runs/runtime/verification.py'}
            for key,p in expected.items():assert r['signature'][key]==digest(p),(name,key)
            assert r['signature']['quality_vector']==[1,0,0,1]
            ledger=folder/'image_provenance.csv'
            if not ledger.exists():
                candidates=list(folder.glob('*ledger*.csv'))+list(folder.glob('*provenance*.csv'))
                assert len(candidates)==1,(name,'missing image ledger');ledger=candidates[0]
            assert digest(ledger)==r['image_provenance_sha256']
            loaded={}
            assert set(r['protocols'])=={'test_masked','test_sunglasses','test_neutral','val_masked','val_sunglasses','val_neutral','mfr2','rmfrd'}
            for condition,item in r['protocols'].items():
                pairs=root/'manifests/cpu_followup'/(condition+'_pairs.csv')
                if condition=='mfr2':pairs=root/'manifests/cleaned/mfr2_official_complete_pairs.csv'
                if condition=='rmfrd':pairs=root/'manifests/cleaned/rmfrd_pairs.csv'
                assert digest(pairs)==item['pairs_sha256']==r['signature']['pairs_sha256'][condition]
                raw=folder/recorded_relative_path(item['raw_scores']);assert digest(raw)==item['raw_scores_sha256']
                rows=read(raw);align(rows,read(pairs));loaded[condition]=rows
                m=score_metrics(rows)
                for key in KEYS+['n_pairs','n_genuine','n_impostor']:
                    assert abs(m[key]-item['metrics'][key])<1e-8,(name,condition,key)
                assert abs(item['far_resolution']-1/m['n_impostor'])<1e-12
                counts['raw_score_files']+=1
            for condition in ['test_masked','test_sunglasses','test_neutral','mfr2','rmfrd']:
                item=r['protocols'][condition]
                calibration=condition.replace('test_','val_') if condition.startswith('test_') else 'val_masked'
                key='validation_calibrated' if condition.startswith('test_') else 'transferred_rof_validation_thresholds'
                negatives=sorted(float(x['score']) for x in loaded[calibration] if x['label']=='0')
                for target,point in item[key].items():
                    threshold=math.nextafter(negatives[-int(math.floor(float(target)*len(negatives)))-1],math.inf)
                    actual=point['test'] if 'test' in point else point
                    assert actual['threshold']==threshold,(name,condition,target,'threshold')
                    for side,rows in [('test',loaded[condition])]+([('validation',loaded[calibration])] if 'validation' in point else []):
                        x=point[side] if side in point else point
                        pos=[float(a['score']) for a in rows if a['label']=='1'];neg=[float(a['score']) for a in rows if a['label']=='0']
                        ta=sum(a>=threshold for a in pos);fa=sum(a>=threshold for a in neg)
                        assert x['true_accepts']==ta and x['false_accepts']==fa
                        assert x['genuine']==len(pos) and x['impostors']==len(neg)
                        assert abs(x['tar']-ta/len(pos))<1e-12 and abs(x['far']-fa/len(neg))<1e-12
                    counts['calibrated_operating_points']+=1
            if variant=='gated_fusion':
                assert r['constant_quality_fold_max_absolute_error']<2e-7
                for c in r['protocols']:
                    assert abs(r['gate_controls'][c]['learned']['auc']-r['protocols'][c]['metrics']['auc'])<1e-12
            counts['models']+=1
    assert len(summary['summary'])==25
    for row in summary['summary']:
        assert row['completed_seeds']==3
        for k in KEYS:
            values=[records[(s,row['variant'])]['protocols'][row['condition']]['metrics'][k] for s in SEEDS]
            assert abs(row[k+'_mean']-statistics.mean(values))<1e-12
            assert abs(row[k+'_seed_sd']-statistics.stdev(values))<1e-12
    for item in summary['paired_auc_comparisons']:
        left,right=item['contrast'].split(' minus ')
        values=[records[(s,left)]['protocols'][item['condition']]['metrics']['auc']-records[(s,right)]['protocols'][item['condition']]['metrics']['auc'] for s in SEEDS]
        assert values==item['seed_differences']
        assert abs(statistics.mean(values)-item['mean_auc_difference'])<1e-12
        assert item['requested_replicates']==1000 and item['valid_replicates']>0
        counts['paired_point_comparisons']+=1
    assert counts['paired_point_comparisons']==10
    rows=read(root/'manifests/cpu_followup/training_manifest.csv')
    assert len(rows)==6171 and len({x['sha256'] for x in rows})==6171
    splits={}
    for row in rows:splits.setdefault(row['identity'],set()).add(row['split'])
    assert all(len(v)==1 for v in splits.values())
    for split,total in [('train',4405),('val',844),('test',922)]:
        assert sum(x['split']==split for x in rows)==total
    # Shipped report paths are recorded relative to the original execution folder.
    for path,value in summary['evaluation_report_hashes'].items():
        assert digest(base/recorded_relative_path(path,prefix='cpu_runs'))==value
    tex=(root/'submission_ieee/main.tex').read_text(encoding='utf-8')
    def lines(label):
        return [x for x in tex.split('\\label{tab:'+label+'}')[1].split('\\bottomrule')[0].splitlines() if '&' in x and not x.startswith(('Protocol','Configuration'))]
    conditions=['test_masked','test_sunglasses','test_neutral','mfr2','rmfrd']
    for c,line in zip(conditions,lines('checked8')):
        key='validation_calibrated' if c.startswith('test_') else 'transferred_rof_validation_thresholds'
        values=[records[(s,'gated_fusion')]['protocols'][c][key]['0.01'] for s in SEEDS]
        values=[x['test'] if 'test' in x else x for x in values];cells=[x.strip().rstrip('\\') for x in line.split('&')]
        assert abs(float(cells[1])-statistics.mean(x['tar'] for x in values))<=.000050001
        assert abs(float(cells[2])-statistics.mean(x['far'] for x in values))<=.000050001
        assert cells[3]=='/'.join(str(x['true_accepts']) for x in values)
        assert cells[4]=='/'.join(str(x['false_accepts']) for x in values)
    for c,line in zip(conditions,lines('checked9')):
        for key,cell in zip(['constant_0.5_same_branches','learned','validation_mean_gate_same_branches','permuted_gate_same_branches'],line.split('&')[1:]):
            expected=statistics.mean(records[(s,'gated_fusion')]['gate_controls'][c][key]['auc'] for s in SEEDS)
            assert abs(float(cell.strip().rstrip('\\'))-expected)<=.000050001
    for item,line in zip(summary['paired_auc_comparisons'],lines('checked12')):
        values=[item['mean_auc_difference']]+item['paired_two_endpoint_identity_bootstrap_ci95']
        for expected,cell in zip(values,line.split('&')[2:]):
            assert abs(float(cell.strip().rstrip('\\'))-expected)<=.000050001
    baseline=json.loads((root/'results/sface/BASELINE_REPORT.json').read_text())
    for c,item in baseline['protocols'].items():
        raw=root/'results/sface'/(c+'_raw_scores.csv');assert digest(raw)==item['raw_scores_sha256']
        pairs=root/'manifests/cpu_followup'/(c+'_pairs.csv')
        if c=='mfr2':pairs=root/'manifests/cleaned/mfr2_official_complete_pairs.csv'
        if c=='rmfrd':pairs=root/'manifests/cleaned/rmfrd_pairs.csv'
        assert digest(pairs)==item['pairs_sha256'];rows=read(raw);align(rows,read(pairs));m=score_metrics(rows)
        for key in KEYS:assert abs(m[key]-item['all_pairs_metrics'][key])<1e-8
    for c,line in zip(conditions,lines('checked11')):
        cells=[x.strip().rstrip('\\') for x in line.split('&')]
        assert abs(float(cells[1])-baseline['protocols'][c]['all_pairs_metrics']['auc'])<=.000050001
        assert int(cells[2])==baseline['protocols'][c]['failed_pairs']
    counts['sface_score_files']=len(baseline['protocols'])
    counts['auxiliary_manuscript_tables']=4
    return counts

if __name__=='__main__':
    root=Path(__file__).resolve().parent.parent
    print(json.dumps(verify_completed(root),indent=2))
