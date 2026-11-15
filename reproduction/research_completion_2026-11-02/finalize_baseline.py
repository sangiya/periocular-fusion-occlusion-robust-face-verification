"""Bind baseline statistics and calibrated thresholds to the saved score precision."""
import json,sys
import numpy as np
from cpu_common import HERE,EXPERIMENT,RELEASE,sha,save_json,calibrate,at_threshold
from audit_images import read
sys.path.insert(0,str(HERE/'cpu_runs/runtime'))
from verification import summarize
from evaluate_cpu import identity_bootstrap_auc

def main():
    out=HERE/'sface';path=out/'BASELINE_REPORT.json';report=json.loads(path.read_text())
    backup=out/'BASELINE_REPORT_before_precision_binding.json'
    if not backup.exists():backup.write_bytes(path.read_bytes())
    arrays={}
    for name,item in report['protocols'].items():
        raw=out/f'{name}_raw_scores.csv'
        if sha(raw)!=item['raw_scores_sha256']:raise ValueError('Raw scores changed: '+str(raw))
        rows=read(raw);scores=np.array([float(r['score']) for r in rows]);labels=np.array([int(r['label']) for r in rows])
        failures=np.array([int(r['detector_failure']) for r in rows],dtype=bool)
        arrays[name]=(scores,labels)
        item['all_pairs_metrics']=summarize(scores,labels)
        item['detected_only_metrics']=summarize(scores[~failures],labels[~failures])
        item['far_resolution']=float(1/np.sum(labels==0))
        if not name.startswith('val_'):item['identity_bootstrap_auc']=identity_bootstrap_auc(scores,labels,rows)
    for condition in ['masked','sunglasses','neutral']:
        vs,vl=arrays[f'val_{condition}'];ts,tl=arrays[f'test_{condition}']
        report['protocols'][f'test_{condition}']['validation_calibrated']={str(far):{
            'validation':at_threshold(vs,vl,calibrate(vs,vl,far)),
            'test':at_threshold(ts,tl,calibrate(vs,vl,far)),
            'validation_far_resolution':float(1/np.sum(vl==0))} for far in [.01,.001]}
    report['score_precision']='All statistics, intervals and thresholds recomputed from the saved 10-decimal raw scores.'
    report['postprocessor_sha256']=sha(__file__)
    report['model_sources']={
        'sface':'https://github.com/opencv/opencv_zoo/tree/main/models/face_recognition_sface',
        'yunet':'https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet'}
    report['image_ledger_sha256']=sha(out/'image_ledger.csv')
    save_json(path,report)
    print(json.dumps({k:{'auc':v['all_pairs_metrics']['auc'],'failed_pairs':v['failed_pairs']} for k,v in report['protocols'].items()},indent=2))

if __name__=='__main__':main()
