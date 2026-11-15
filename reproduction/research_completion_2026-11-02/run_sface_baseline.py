"""Official OpenCV SFace + YuNet baseline on the prospective frozen protocols.

Detection failures stay in the denominator (score -1); detected-only results
are separately labelled. No target fine-tuning or test threshold selection.
"""
from pathlib import Path
import csv, hashlib, json, sys, time
import cv2
import numpy as np
from audit_images import HERE, DATA, RELEASE, read, write
sys.path.insert(0,str(RELEASE/'code'))
from verification import summarize

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def calibration(scores,labels,far):
    impostors=np.sort(scores[labels==0])
    allowed=int(np.floor(far*len(impostors)))
    return float(np.nextafter(impostors[-allowed-1],np.inf))

def operating(scores,labels,threshold):
    return {'threshold':threshold,'far':float(np.mean(scores[labels==0]>=threshold)),
            'tar':float(np.mean(scores[labels==1]>=threshold))}

def main():
    cv2.setNumThreads(2); started=time.time()
    out=HERE/'sface'; out.mkdir(exist_ok=True)
    files={p.stem.removesuffix('_pairs'): p for p in (HERE/'experiment').glob('*_pairs.csv')}
    files.update({'mfr2':RELEASE/'manifests/cleaned/mfr2_official_complete_pairs.csv',
                  'rmfrd':RELEASE/'manifests/cleaned/rmfrd_pairs.csv'})
    protocols={k:read(p) for k,p in files.items()}
    def endpoints(r):
        return (r['face_path1'],r['face_path2']) if 'face_path1' in r else (r['probe_face_path'],r['enroll_face_path'])
    paths=sorted({p for rs in protocols.values() for r in rs for p in endpoints(r)})
    recognizer=cv2.FaceRecognizerSF.create(str(HERE/'models/sface.onnx'),'')
    detector=cv2.FaceDetectorYN.create(str(HERE/'models/yunet.onnx'),'',(320,320),0.8,0.3,5000)
    embeddings={};ledger=[]
    for n,rel in enumerate(paths):
        row={'path':rel,'sha256':sha(DATA/rel),'faces_detected':0,'selected_score':'','failure':''}
        try:
            image=cv2.imread(str(DATA/rel))
            if image is None: raise ValueError('image_decode_failure')
            h,w=image.shape[:2]; scale=320/max(w,h)
            small=cv2.resize(image,(max(32,int(w*scale)),max(32,int(h*scale))))
            detector.setInputSize((small.shape[1],small.shape[0]))
            _,faces=detector.detect(small)
            if faces is None or not len(faces): raise ValueError('no_face_at_frozen_threshold_0.8')
            row['faces_detected']=len(faces)
            # Deterministic closest-to-centre face; no manual test-label selection.
            centres=faces[:,:2]+faces[:,2:4]/2
            chosen=int(np.argmin(((centres-np.array([small.shape[1]/2,small.shape[0]/2]))**2).sum(axis=1)))
            box=faces[chosen].copy();box[:14]/=scale
            aligned=recognizer.alignCrop(image,box)
            z=recognizer.feature(aligned).reshape(-1).astype(np.float32)
            embeddings[rel]=z/np.linalg.norm(z)
            row['selected_score']=float(box[-1])
        except Exception as e: row['failure']=str(e)
        ledger.append(row)
        if n%100==0: print(f'SFace {n}/{len(paths)}; failures={sum(bool(r["failure"]) for r in ledger)}',flush=True)
    write(out/'image_ledger.csv',ledger)
    arrays={};report={}
    for name,rs in protocols.items():
        scores=np.array([float(embeddings[a]@embeddings[b]) if a in embeddings and b in embeddings else -1.
                         for a,b in map(endpoints,rs)])
        labels=np.array([int(r['label']) for r in rs])
        failures=np.array([a not in embeddings or b not in embeddings for a,b in map(endpoints,rs)])
        arrays[name]=(scores,labels)
        raw=[dict(r,score=f'{s:.10f}',detector_failure=int(f)) for r,s,f in zip(rs,scores,failures)]
        write(out/f'{name}_raw_scores.csv',raw)
        report[name]={'all_pairs_metrics':summarize(scores,labels),
            'detected_only_metrics':summarize(scores[~failures],labels[~failures]),
            'failed_pairs':int(failures.sum()),'failed_genuine':int(failures[labels==1].sum()),
            'pairs_sha256':sha(files[name]),'raw_scores_sha256':sha(out/f'{name}_raw_scores.csv')}
    for condition in ('masked','sunglasses','neutral'):
        vs,vl=arrays[f'val_{condition}'];ts,tl=arrays[f'test_{condition}']
        report[f'test_{condition}']['validation_calibrated']={}
        for far in (.01,.001):
            threshold=calibration(vs,vl,far)
            report[f'test_{condition}']['validation_calibrated'][str(far)]={
                'validation':operating(vs,vl,threshold),'test':operating(ts,tl,threshold)}
    meta={'model':'OpenCV SFace 2021dec + YuNet 2023mar, external pretraining, no target fine-tuning',
        'comparability':'Identical prospective pair lists; preprocessing and pretraining differ. Not a matched-training SOTA claim.',
        'pretraining_identity_overlap':'unknown; celebrity overlap cannot be ruled out',
        'detector_threshold':.8,'failure_policy':'all affected pair scores -1, included; detected-only secondary metrics labelled',
        'opencv_version':cv2.__version__,'device':'cpu','elapsed_seconds':time.time()-started,
        'model_hashes':{p.name:sha(p) for p in (HERE/'models').glob('*.onnx')},
        'evaluator_sha256':sha(Path(__file__)),'protocols':report}
    (out/'BASELINE_REPORT.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    print(json.dumps(meta,indent=2))

if __name__=='__main__':main()
