"""Inspect the final CPU grid or explicitly launch its preserved coordinator."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--status',action='store_true',help='Show recorded final completion; no training')
    ap.add_argument('--run',action='store_true',help='Launch the exact coordinator after restoring licensed inputs and a runtime folder')
    ap.add_argument('--runtime-dir',type=Path,default=ROOT.parent/'research_completion_2026-11-02')
    args=ap.parse_args()
    if not args.run:
        report=json.loads((ROOT/'results/cpu_clean/RESULTS_SUMMARY.json').read_text())
        print(json.dumps({'recorded_state':report['state'],'completed_models':report['completed_models'],'missing':report['missing'],'training_started':False},indent=2))
        return 0
    if args.status:ap.error('Choose --status or --run, not both.')
    runtime=args.runtime_dir.resolve();preserved=ROOT/'reproduction/research_completion_2026-11-02'
    for name in ['run_cpu_sweep.py','cpu_common.py','train_cpu.py','evaluate_cpu.py']:
        p=runtime/name
        if not p.is_file() or hashlib.sha256(p.read_bytes()).digest()!=hashlib.sha256((preserved/name).read_bytes()).digest():
            ap.error('Restore the exact preserved runtime before launching: '+str(p))
    frozen=ROOT/'manifests/cpu_followup'
    for p in frozen.glob('*'):
        if p.suffix not in ['.csv','.json']:continue
        q=runtime/'experiment'/p.name
        if not q.is_file() or q.read_bytes()!=p.read_bytes():ap.error('Restore frozen experiment input: '+str(q))
    return subprocess.call([sys.executable,'-u',str(runtime/'run_cpu_sweep.py')],cwd=runtime.parent)
if __name__=='__main__':raise SystemExit(main())
