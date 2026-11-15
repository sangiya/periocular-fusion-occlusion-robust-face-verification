"""Read-only CPU sweep status; standard library Python is sufficient."""
from pathlib import Path
import json,time
from datetime import datetime,timezone,timedelta

root=Path(__file__).resolve().parent/'cpu_runs'
path=root/'SWEEP_STATUS.json'
status=json.loads(path.read_text())
print('Sweep:',status['state'],'device:',status.get('device','cpu'))
print('Completed and evaluated:',len(status.get('completed_jobs',[])),'/',status.get('total_jobs',15))
print('Current job:',status.get('job','none'),'phase:',status.get('phase','none'))
if status.get('started_utc'):
    local=datetime.fromisoformat(status['started_utc']).astimezone(timezone(timedelta(hours=5,minutes=30)))
    print('Coordinator started (Asia/Colombo):',local.strftime('%Y-%m-%d %H:%M:%S'))
job=status.get('job')
if job:
    progress=root/'checkpoints'/(job+'_progress.json')
    if progress.exists():
        data=json.loads(progress.read_text())
        print('Model training:',json.dumps(data,indent=2))
        print('Seconds since last model progress update:',round(time.time()-progress.stat().st_mtime,1))
if status['state']=='failed':print('Error:',status.get('error'))
print('Journal submission readiness: not certified; completed experiments require scientific and manuscript review.')
