"""Independent standard-library check of every completed follow-up score file."""
from pathlib import Path
import csv,hashlib,json,sys
HERE=Path(__file__).resolve().parent
RELEASE=HERE.parent/'publication_release'
sys.path.insert(0,str(RELEASE/'code'))
from verify_results import score_metrics

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
    with p.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

def main():
    failures=[];checked=0
    def check(raw,pairs,expected,metrics):
        nonlocal checked
        if sha(raw)!=expected:raise ValueError('Raw hash differs: '+str(raw))
        rows=read(raw);target=read(pairs)
        if len(rows)!=len(target):raise ValueError('Pair count differs')
        for r,p in zip(rows,target):
            if any(r.get(k)!=v for k,v in p.items()):raise ValueError('Pair alignment differs')
        actual=score_metrics(rows)
        for k in ['auc','eer','tar_far_1e-2','tar_far_1e-3']:
            if abs(actual[k]-metrics[k])>1e-8:raise ValueError(f'{raw.name} {k}: {actual[k]} != {metrics[k]}')
        checked+=1
    old=json.loads((HERE/'archived_reevaluation/REEVALUATION_REPORT.json').read_text())
    if len(old['runs'])!=45:raise ValueError('Expected 45 historical reevaluations')
    for r in old['runs']:
        try:
            if sha(HERE/r['pairs'])!=r['pairs_sha256']:raise ValueError('Protocol hash differs')
            if sha(RELEASE/r['source'])!=r['source_sha256']:raise ValueError('Historical source changed')
            check(HERE/'archived_reevaluation'/r['raw_scores'],HERE/r['pairs'],r['raw_scores_sha256'],r['metrics'])
        except Exception as e:failures.append(str(e))
    baseline=json.loads((HERE/'sface/BASELINE_REPORT.json').read_text())
    if len(baseline['protocols'])!=8:raise ValueError('Expected eight SFace protocols')
    for name,r in baseline['protocols'].items():
        try:
            if name=='mfr2':pairs=RELEASE/'manifests/cleaned/mfr2_official_complete_pairs.csv'
            elif name=='rmfrd':pairs=RELEASE/'manifests/cleaned/rmfrd_pairs.csv'
            else:pairs=HERE/'experiment'/(name+'_pairs.csv')
            if sha(pairs)!=r['pairs_sha256']:raise ValueError('SFace protocol hash differs')
            check(HERE/'sface'/(name+'_raw_scores.csv'),pairs,r['raw_scores_sha256'],r['all_pairs_metrics'])
        except Exception as e:failures.append(str(e))
    report={'score_files_checked':checked,'expected_score_files':53,'failures':failures,
        'scope':'Completed historical reevaluations and SFace baseline, not the still-running clean training sweep.',
        'verifier_sha256':sha(Path(__file__))}
    (HERE/'FOLLOWUP_VERIFICATION.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
    if failures or checked!=53:raise SystemExit(1)

if __name__=='__main__':main()
