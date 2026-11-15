"""Persistent serial CPU sweep. Restart this command to resume saved progress."""
from pathlib import Path
import atexit,json,os,subprocess,sys,time,traceback
from datetime import datetime,timezone
from cpu_common import HERE,DATA,EXPERIMENT,RUN,SEEDS,VARIANTS,sha,save_json

def utc(): return datetime.now(timezone.utc).isoformat()

TRANSIENT_EXIT_CODES={0x40010004}

def retryable_exit(code,attempt):
    # Retry the observed Windows termination only. Python/data errors and
    # deliberate Ctrl+C remain visible failures rather than infinite retries.
    return (code & 0xffffffff) in TRANSIENT_EXIT_CODES and attempt<3

def verified_completed(seed,variant):
    name=f'seed{seed}_{variant}'
    folder=RUN/'evaluation'/name
    path=folder/'EVALUATION_REPORT.json'
    if not path.exists():return False
    report=json.loads(path.read_text())
    progress=json.loads((RUN/'checkpoints'/(name+'_progress.json')).read_text())
    signature=report['signature']
    required={
        'checkpoint_sha256':RUN/'checkpoints'/(name+'.pt'),
        'evaluator_sha256':HERE/'evaluate_cpu.py',
        'model_code_sha256':RUN/'runtime/model.py',
        'metrics_code_sha256':RUN/'runtime/verification.py',
        'common_code_sha256':HERE/'cpu_common.py'}
    if report['status']!='complete' or report['seed']!=seed or report['variant']!=variant:
        raise ValueError('Completed evaluation identity mismatch: '+name)
    if not progress.get('complete') or progress['signature']['epochs']!=5 or progress['signature']['max_batches']!=0:
        raise ValueError('Evaluation has no full-training completion record: '+name)
    if progress['signature']['trainer_sha256']!=sha(HERE/'train_cpu.py'):
        raise ValueError('Completed trainer source changed: '+name)
    for key,source in required.items():
        if sha(source)!=signature[key]:raise ValueError('Completed provenance differs: '+name+' '+key)
    files={p.stem.removesuffix('_pairs'):p for p in EXPERIMENT.glob('*_pairs.csv')}
    files['mfr2']=HERE.parent/'publication_release/manifests/cleaned/mfr2_official_complete_pairs.csv'
    files['rmfrd']=HERE.parent/'publication_release/manifests/cleaned/rmfrd_pairs.csv'
    if set(files)!=set(report['protocols']):raise ValueError('Incomplete protocol coverage: '+name)
    for protocol,source in files.items():
        if sha(source)!=signature['pairs_sha256'][protocol]:raise ValueError('Completed protocol changed: '+name)
        item=report['protocols'][protocol]
        if sha(folder/item['raw_scores'])!=item['raw_scores_sha256']:raise ValueError('Completed scores changed: '+name)
    return True

def main():
    RUN.mkdir(exist_ok=True);logs=RUN/'logs';logs.mkdir(exist_ok=True)
    lock=(RUN/'worker.lock').open('a+b');lock.seek(0)
    if os.name=='nt':
        import msvcrt
        if (RUN/'worker.lock').stat().st_size==0:lock.write(b'0');lock.flush();lock.seek(0)
        try:msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        except OSError:raise SystemExit('Another CPU sweep already holds the worker lock')
    (RUN/'worker.pid').write_text(str(os.getpid()),encoding='ascii')
    env=dict(os.environ,HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',CUDA_VISIBLE_DEVICES='',PYTHONUNBUFFERED='1')
    started=utc();completed=[];status=RUN/'SWEEP_STATUS.json'
    plan=json.loads((EXPERIMENT/'EXPERIMENT_PLAN.json').read_text())
    for name,digest in plan['input_hashes'].items():
        if sha(EXPERIMENT/name)!=digest:raise ValueError('Frozen protocol modified: '+name)
    jobs=[(seed,variant) for seed in SEEDS for variant in VARIANTS]
    children=0x08000000 if os.name=='nt' else 0
    try:
        for seed,variant in jobs:
            name=f'seed{seed}_{variant}'
            if verified_completed(seed,variant):
                completed.append(name)
                print(utc(),'verified and retained completed job',name,flush=True)
                continue
            for phase,script in [('training','train_cpu.py'),('evaluation','evaluate_cpu.py')]:
                if (RUN/'STOP_AFTER_CURRENT_PHASE').exists():
                    save_json(status,{'state':'stopped','reason':'STOP_AFTER_CURRENT_PHASE requested',
                        'job':name,'phase':phase,'completed_jobs':completed,'total_jobs':len(jobs),'device':'cpu','updated_utc':utc()})
                    return
                save_json(status,{'state':'running','phase':phase,'job':name,'pid':os.getpid(),
                    'started_utc':started,'updated_utc':utc(),'completed_jobs':completed,'total_jobs':len(jobs),
                    'device':'cpu','manifest_sha256':plan['manifest_sha256']})
                cmd=[sys.executable,'-u',str(HERE/script),'--seed',str(seed),'--variant',variant,'--threads','8']
                logfile=logs/f'{name}_{phase}.log'
                print(utc(),phase,name,flush=True)
                for attempt in range(4):
                    with logfile.open('a',encoding='utf-8') as f:
                        f.write('\nSTART '+utc()+' attempt='+str(attempt+1)+'\n');f.flush()
                        worker=subprocess.Popen(cmd,cwd=DATA,env=env,stdout=f,stderr=subprocess.STDOUT,creationflags=children)
                        save_json(status,{'state':'running','phase':phase,'job':name,'pid':os.getpid(),
                            'child_pid':worker.pid,'attempt':attempt+1,'started_utc':started,'updated_utc':utc(),
                            'completed_jobs':completed,'total_jobs':len(jobs),'device':'cpu',
                            'manifest_sha256':plan['manifest_sha256']})
                        code=worker.wait()
                    if code==0:break
                    if not retryable_exit(code,attempt):raise subprocess.CalledProcessError(code,cmd)
                    if (RUN/'STOP_AFTER_CURRENT_PHASE').exists():raise subprocess.CalledProcessError(code,cmd)
                    delay=[10,30,60][attempt]
                    print(utc(),'interrupted',name,phase,'exit',hex(code & 0xffffffff),'resume in',delay,'seconds',flush=True)
                    time.sleep(delay)
            if not verified_completed(seed,variant):raise RuntimeError('Job has no verified completed evaluation: '+name)
            completed.append(name)
            subprocess.run([sys.executable,str(HERE/'summarize_cpu_results.py')],cwd=DATA,env=env,check=True)
        save_json(status,{'state':'complete','completed_jobs':completed,'total_jobs':len(jobs),
            'started_utc':started,'updated_utc':utc(),'device':'cpu','journal_submission_ready':False,
            'note':'Training/evaluation complete; manuscript and scientific review are separate required steps.'})
    except BaseException as e:
        save_json(status,{'state':'failed','job':locals().get('name'),'phase':locals().get('phase'),
            'error':str(e),'traceback':traceback.format_exc(),'completed_jobs':completed,
            'total_jobs':len(jobs),'updated_utc':utc(),'pid':os.getpid(),'device':'cpu'})
        raise

if __name__=='__main__':main()
