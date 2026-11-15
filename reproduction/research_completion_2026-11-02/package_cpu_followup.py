"""Package completed evidence and CPU source, excluding live/large training state."""
from pathlib import Path
import hashlib,json,zipfile
from cpu_common import HERE,DATA,sha

def main():
    selected={}
    def include(p):selected[p.relative_to(DATA).as_posix()]=p.read_bytes()
    for p in sorted(HERE.glob('*.py')):include(p)
    for name in ['README_CPU.md','IMAGE_AUDIT.json','DATASET_PROVENANCE.json',
        'CHECKPOINT_MANIFEST_AUDIT.json','FOLLOWUP_VERIFICATION.json','CPU_SMOKE_VALIDATION.json',
        'image_inventory.csv','annotation_inventory.csv','perceptual_review.csv',
        'perceptual_cross_identity_candidates.csv','upstream_rof_tree.json']:
        include(HERE/name)
    for p in sorted((HERE/'experiment').glob('*')):
        if p.is_file() and p.suffix in ('.json','.csv'):include(p)
    for p in sorted((HERE/'archived_reevaluation').glob('*')):
        if p.is_file() and p.suffix in ('.json','.csv'):include(p)
    baseline=json.loads((HERE/'sface/BASELINE_REPORT.json').read_text())
    for name in ['BASELINE_REPORT.json','image_ledger.csv']+[k+'_raw_scores.csv' for k in baseline['protocols']]:include(HERE/'sface'/name)
    for p in sorted((HERE/'cpu_runs/runtime').glob('*.py')):include(p)
    for p in sorted((HERE/'cpu_runs/evaluation').glob('*/*')):
        if p.is_file() and p.suffix in ('.json','.csv'):include(p)
    for p in sorted((HERE/'cpu_runs/checkpoints').glob('*_progress.json')):include(p)
    for name in ['RESULTS_SUMMARY.json','RESULTS_SUMMARY.md','SWEEP_STATUS.json']:include(HERE/'cpu_runs'/name)
    metadata={'exclusions':['datasets','model weights','full/smoke checkpoints','embedding caches','live logs, locks and PIDs'],
        'status':'Full new CPU training and evaluation complete: 15/15 models',
        'files':{name:{'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)} for name,data in selected.items()}}
    selected['CPU_FOLLOWUP_MANIFEST.json']=(json.dumps(metadata,indent=2)+'\n').encode('utf-8')
    output=DATA/'cpu_research_followup.zip'
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in sorted(selected.items()):
            info=zipfile.ZipInfo(name,(1980,1,1,0,0,0));info.create_system=3;info.external_attr=0o100644<<16
            z.writestr(info,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    digest=sha(output)
    output.with_suffix('.zip.sha256').write_text(digest+'  '+output.name+'\n',encoding='ascii')
    with zipfile.ZipFile(output) as z:
        for name,item in metadata['files'].items():
            assert hashlib.sha256(z.read(name)).hexdigest()==item['sha256'],name
    print(json.dumps({'archive':str(output),'sha256':digest,'files':len(selected),'bytes':output.stat().st_size},indent=2))

if __name__=='__main__':main()
