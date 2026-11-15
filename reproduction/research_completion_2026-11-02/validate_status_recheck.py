from pathlib import Path
import hashlib,json,zipfile

base=Path(__file__).resolve().parent.parent
root=base/'publication_release'
archive=base/'publication_release.zip'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
with zipfile.ZipFile(archive) as z:
    manifest=json.loads(z.read('RELEASE_MANIFEST.json'))
    changed=[]
    for name,item in manifest['files'].items():
        content=z.read(name)
        assert hashlib.sha256(content).hexdigest()==item['sha256'],name
        assert len(content)==item['bytes'],name
        if sha(root/name)!=item['sha256']: changed.append(name)
    count=len(z.namelist())
    assert count==len(manifest['files'])+1
assert archive.with_suffix('.zip.sha256').read_text().split()[0]==sha(archive)
old=json.loads((base/'publication_repair_2026-11-02/before_hashes.json').read_text())
names=[n for n in old if n.startswith('results/seed_sweep/')]
assert len(names)==185
assert all(sha(root/n)==old[n] for n in names)
research=Path(__file__).parent
sweep_path=research/'cpu_runs/SWEEP_STATUS.json'
sweep=json.loads(sweep_path.read_text()) if sweep_path.exists() else {}
progress_path=research/'cpu_runs/checkpoints'/(sweep.get('job','none')+'_progress.json')
progress=json.loads(progress_path.read_text()) if progress_path.exists() else {}
report={'sha256':sha(archive),'archive_entries':count,
    'archive_internal_manifest_and_checksum_match':True,
    'working_files_changed_after_snapshot':changed,
    'historical_files_preserved':len(names),
    'verification_failures':json.loads((root/'document/VERIFICATION_REPORT.json').read_text())['failures'],
    'journal_submission_ready':False,
    'new_training_started':progress.get('optimizer_steps',0)>0 or bool(sweep.get('completed_jobs')),
    'cpu_sweep_state':sweep.get('state','not_started'),
    'fully_trained_and_evaluated_models':len(sweep.get('completed_jobs',[])),
    'active_cpu_model':sweep.get('job'),'active_model_optimizer_steps':progress.get('optimizer_steps',0)}
(Path(__file__).parent/'STATUS_RECHECK_RESULT.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
assert not changed,'Working files changed during or after packaging'
