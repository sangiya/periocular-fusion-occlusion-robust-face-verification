"""CPU SFace control using the exact whole-face input files, without redetection.

This controls crop-file selection, not pretraining, input resolution or training.
The original YuNet/aligned SFace diagnostic and all DINO results are preserved.
"""
from pathlib import Path
import argparse,csv,hashlib,json,sys,time
import cv2
import numpy as np
from PIL import Image
from verification import summarize

ROOT=Path(__file__).resolve().parent.parent

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write(path,rows):
    with Path(path).open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
def endpoints(row):
    return (row['face_path1'],row['face_path2']) if 'face_path1' in row else (row['probe_face_path'],row['enroll_face_path'])
def operating(scores,labels,threshold):
    fa=int(np.sum(scores[labels==0]>=threshold));ta=int(np.sum(scores[labels==1]>=threshold))
    return {'threshold':threshold,'far':fa/int(np.sum(labels==0)),'tar':ta/int(np.sum(labels==1)),
            'false_accepts':fa,'true_accepts':ta,'impostors':int(np.sum(labels==0)),'genuine':int(np.sum(labels==1))}
def calibrate(scores,labels,far):
    negatives=np.sort(scores[labels==0]);allowed=int(np.floor(far*len(negatives)))
    return float(np.nextafter(negatives[-allowed-1],np.inf))
def finite(value):
    if isinstance(value,dict):return {k:finite(v) for k,v in value.items()}
    if isinstance(value,list):return [finite(v) for v in value]
    if isinstance(value,float) and not np.isfinite(value):return None
    return value

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--data-root',type=Path,default=ROOT.parent)
    ap.add_argument('--model',type=Path,default=ROOT.parent/'research_completion_2026-11-02/models/sface.onnx')
    args=ap.parse_args();cv2.setNumThreads(2);start=time.monotonic()
    assert sha(args.model)=='0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79'
    baseline=json.loads((ROOT/'results/sface/BASELINE_REPORT.json').read_text())
    protocols={};sources={}
    for name,item in baseline['protocols'].items():
        path=ROOT/'results/sface'/f'{name}_raw_scores.csv'
        assert sha(path)==item['raw_scores_sha256']
        sources[name]=sha(path)
        protocols[name]=[{k:v for k,v in row.items() if k not in ['score','detector_failure']} for row in read(path)]
    paths=sorted({p for rows in protocols.values() for row in rows for p in endpoints(row)})
    original={row['path']:row for row in read(ROOT/'results/sface/image_ledger.csv')}
    assert set(paths)==set(original)
    out=ROOT/'results/shared_crop_sface';out.mkdir(exist_ok=True)
    model=cv2.FaceRecognizerSF.create(str(args.model),'');embeddings={};ledger=[]
    for i,rel in enumerate(paths):
        path=args.data_root/rel;value={'path':rel,'sha256':sha(path),'failure':''}
        assert value['sha256']==original[rel]['sha256'],rel
        try:
            with Image.open(path) as image:
                rgb=np.asarray(image.convert('RGB').resize((112,112),Image.Resampling.BILINEAR))
            bgr=np.ascontiguousarray(rgb[:,:,::-1]);z=model.feature(bgr).reshape(-1).astype(np.float32)
            norm=np.linalg.norm(z)
            if not np.isfinite(z).all() or norm<=0:raise ValueError('Invalid embedding')
            embeddings[rel]=z/norm
        except Exception as exc:value['failure']=str(exc)
        ledger.append(value)
        if i%100==0:print(f'Shared-crop SFace: {i}/{len(paths)} images',flush=True)
    write(out/'image_ledger.csv',ledger)
    arrays={};report={}
    for name,rows in protocols.items():
        raw=[]
        for row in rows:
            a,b=endpoints(row);failed=a not in embeddings or b not in embeddings
            score=-1. if failed else float(embeddings[a]@embeddings[b])
            raw.append(dict(row,score=f'{score:.10f}',embedding_failure=int(failed)))
        path=out/f'{name}_raw_scores.csv';write(path,raw)
        scores=np.array([float(row['score']) for row in raw]);labels=np.array([int(row['label']) for row in raw]);arrays[name]=(scores,labels)
        report[name]={'metrics':finite(summarize(scores,labels)),
                      'failed_pairs':sum(int(row['embedding_failure']) for row in raw),
                      'raw_scores_sha256':sha(path),'frozen_pair_list_sha256':baseline['protocols'][name]['pairs_sha256'],
                      'reference_score_file_sha256':sources[name]}
    for name in ['test_masked','test_sunglasses','test_neutral','mfr2','rmfrd']:
        validation='val_'+name.removeprefix('test_') if name.startswith('test_') else 'val_masked'
        vs,vl=arrays[validation];ts,tl=arrays[name]
        report[name]['calibration_validation_protocol']=validation
        report[name]['validation_calibrated']={}
        for far in [.01,.001]:
            threshold=calibrate(vs,vl,far)
            report[name]['validation_calibrated'][str(far)]={'validation':operating(vs,vl,threshold),'test':operating(ts,tl,threshold)}
    metadata={'status':'complete','device':'cpu','opencv_threads':2,'opencv_version':cv2.__version__,
              'model_sha256':sha(args.model),'evaluator_sha256':sha(__file__),
              'preprocessing':'Exact DINO whole-face input files, PIL RGB bilinear resize to SFace native 112x112; BGR for OpenCV feature API; no redetection, landmark alignment or target fine-tuning.',
              'comparability':'Shared input crop files; resolution, feature normalization, architecture and pretraining differ. Not matched training or proof of architecture superiority.',
              'failure_policy':'Any affected score -1 retained in primary denominator; missing input or changed image hashes abort.',
              'score_precision':'All metrics/calibration from saved ten-decimal scores; nonfinite retrospective thresholds represented by null.',
              'unique_images':len(paths),'image_ledger_sha256':sha(out/'image_ledger.csv'),
              'elapsed_seconds':time.monotonic()-start,'protocols':report}
    (out/'REPORT.json').write_text(json.dumps(metadata,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({name:row['metrics']['auc'] for name,row in report.items()},indent=2),flush=True)

if __name__=='__main__':main()
