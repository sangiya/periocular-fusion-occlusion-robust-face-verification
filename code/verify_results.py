"""Verify final CPU results, raw scores, manuscript tables and portable provenance.
No model weights, image datasets, torch, or sklearn are needed.
ALL CHECKS PASSED means these explicit artifact checks pass, not journal readiness.
"""
from __future__ import annotations
import argparse,csv,hashlib,itertools,json,math,re,statistics
from pathlib import Path, PurePosixPath, PureWindowsPath

SEEDS=[7,42,123]
VARIANTS=["frozen_whole","whole_lora","peri_lora","fixed_fusion","gated_fusion"]
KEYS=["auc","eer","tar_far_1e-2","tar_far_1e-3"]
ROOT=Path(__file__).resolve().parent.parent

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def recorded_relative_path(value, prefix=None):
    """Interpret stored artifact paths independently of the current OS.

    Historical Windows records contain backslashes (sometimes doubled). Keep
    those signed records unchanged; normalize separators only when reading.
    Absolute paths, drive paths and parent traversal are not release-relative.
    """
    if not isinstance(value,str) or '\x00' in value:
        raise ValueError('Recorded artifact path must be a relative string')
    path=PurePosixPath(value.replace('\\','/'))
    if not path.parts or path.is_absolute() or PureWindowsPath(value).drive or '..' in path.parts:
        raise ValueError(f'Not a release-relative artifact path: {value!r}')
    if prefix is not None:
        path=path.relative_to(PurePosixPath(prefix))
        if not path.parts:raise ValueError('Recorded artifact path must name a file below its prefix')
    return path
def read(p):
    with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def score_metrics(rows):
    if not rows:raise ValueError("Empty raw-score file")
    values=[]
    for r in rows:
        score=float(r["score"]);label=int(r["label"])
        if not math.isfinite(score) or label not in (0,1):raise ValueError("Invalid score/label")
        values.append((score,label))
    pos=sum(y for _,y in values);neg=len(values)-pos
    if not pos or not neg:raise ValueError("Both score classes are required")
    values.sort(reverse=True);points=[(0.,0.)];tp=fp=0
    for _,group in itertools.groupby(values,key=lambda x:x[0]):
        for _,y in group:tp+=y;fp+=1-y
        points.append((fp/neg,tp/pos))
    auc=sum((x1-x0)*(y1+y0)/2 for (x0,y0),(x1,y1) in zip(points,points[1:]))
    eer=None
    for (x0,y0),(x1,y1) in zip(points,points[1:]):
        d0=x0+y0-1;d1=x1+y1-1
        if d0<=0<=d1:
            alpha=-d0/(d1-d0) if d1!=d0 else 0
            eer=x0+alpha*(x1-x0);break
    return {"auc":auc,"eer":eer,
            "tar_far_1e-2":max(y for x,y in points if x<=.01),
            "tar_far_1e-3":max(y for x,y in points if x<=.001),
            "n_pairs":len(values),"n_genuine":pos,"n_impostor":neg}

def logical_path(s):
    s=s.replace("\\","/")
    for part in ["data/","work/"]:
        at=s.find("/"+part)
        if at>=0:return s[at+1:]
    return s

def align(raw,pairs):
    if len(raw)!=len(pairs):raise ValueError("Raw/protocol lengths differ")
    for r,p in zip(raw,pairs):
        if r["label"]!=p["label"]:raise ValueError("Raw/protocol labels differ")
        for key in ["pair_id","probe_identity","enroll_identity","identity1","identity2"]:
            if key in r and key in p and r[key]!=p[key]:raise ValueError(f"Raw/protocol {key} differs")
        for key in ["face_path1","face_path2"]:
            if key in r and logical_path(r[key])!=logical_path(p[key]):raise ValueError(f"Raw/protocol {key} differs")
        for key,target in [("enroll_id","enroll_image_id"),("probe_id","probe_image_id")]:
            if key in r and r[key]!=p[target]:raise ValueError(f"Raw/protocol {key} differs")

def verify(root,results=None):
    root=Path(root).resolve()
    if results is not None and Path(results).resolve()!=(root/'results/cpu_clean').resolve():
        raise ValueError('Only final results/cpu_clean is supported; superseded sweeps are not part of this release.')
    counts={};failures=[]
    from verify_completed_cpu import verify_completed
    from verify_strengthening import verify_strengthening
    from verify_final_documents import verify_documents
    for name,fn in [('completed_cpu',verify_completed),('strengthening',verify_strengthening),('final_documents',verify_documents)]:
        try:counts[name]=fn(root)
        except Exception as exc:failures.append(f'{name}: {type(exc).__name__}: {exc}')
    manifest=root/'RELEASE_MANIFEST.json'
    if manifest.exists():
        try:
            record=json.loads(manifest.read_text())
            for name,item in record['files'].items():
                p=root/recorded_relative_path(name)
                assert p.is_file() and p.stat().st_size==item['bytes'] and digest(p)==item['sha256'],name
        except Exception as exc:failures.append(f'release_manifest: {type(exc).__name__}: {exc}')
    return {'counts':counts,'failures':failures,'scope':'Final CPU/SFace score arithmetic, calibration, frozen protocols, executed-source provenance, final manuscript tables, source archives and compiled bindings. No new neural inference, permission clearance or publication approval.'}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,default=ROOT)
    ap.add_argument('--results-dir',type=Path)
    ap.add_argument('--report',type=Path)
    a=ap.parse_args()
    try:report=verify(a.root,a.results_dir)
    except Exception as exc:report={'counts':{},'failures':[f'Required input/structure error: {exc}']}
    print(json.dumps(report,indent=2))
    if a.report:
        a.report.parent.mkdir(parents=True,exist_ok=True)
        a.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('RESULT: CHECKS FAILED' if report['failures'] else 'RESULT: ALL CHECKS PASSED')
    return 1 if report['failures'] else 0
if __name__=='__main__':raise SystemExit(main())
