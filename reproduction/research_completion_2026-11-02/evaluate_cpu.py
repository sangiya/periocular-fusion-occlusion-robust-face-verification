"""Batched CPU evaluation, validation thresholds, and same-branch gate controls."""
import argparse,csv,json,os,sys,time
from pathlib import Path
os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1';os.environ['CUDA_VISIBLE_DEVICES']=''
print('Loading offline CPU evaluation runtime.',flush=True)
import numpy as np
from PIL import Image
import torch
from torch import nn
from torchvision.transforms import v2
from cpu_common import HERE,DATA,RELEASE,EXPERIMENT,RUN,VARIANTS,sha,save_json,calibrate,at_threshold
from audit_images import read,write
sys.path.insert(0,str(RUN/'runtime'))
from model import VerificationModel,pooled
from verification import summarize

def protocols():
    files={p.stem.removesuffix('_pairs'):p for p in EXPERIMENT.glob('*_pairs.csv')}
    files['mfr2']=RELEASE/'manifests/cleaned/mfr2_official_complete_pairs.csv'
    files['rmfrd']=RELEASE/'manifests/cleaned/rmfrd_pairs.csv'
    if len(files)!=8:raise ValueError('Expected six ROF and two external protocols')
    return files

def endpoints(r):
    if 'face_path1' in r:
        return ((r['face_path1'],r['peri_path1']),(r['face_path2'],r['peri_path2']))
    return tuple((r[f'{role}_face_path'],r[f'{role}_peri_path']) for role in ('probe','enroll'))

def identity_endpoints(r):
    if 'identity1' in r:return r['identity1'],r['identity2']
    return r['probe_identity'],r['enroll_identity']

def normalize(z):return z/np.maximum(np.linalg.norm(z,axis=1,keepdims=True),1e-12)

def json_ready_report(value):
    """Represent a legitimate +infinity ROC threshold as an explicit reject-all rule.

    Nonfinite scores/other statistics remain errors under strict JSON writing.
    """
    if isinstance(value,dict):
        result={}
        for key,item in value.items():
            if key.endswith('_threshold') and isinstance(item,float) and np.isposinf(item):
                result[key]=None
                result[key+'_rule']='reject_all; ROC threshold is positive infinity'
            else:result[key]=json_ready_report(item)
        return result
    if isinstance(value,list):return [json_ready_report(item) for item in value]
    return value

def sorted_auc_plan(scores,labels):
    order=np.argsort(scores,kind='stable')
    starts=np.r_[0,np.flatnonzero(np.diff(scores[order])!=0)+1]
    def auc(weights):
        pos=np.add.reduceat((weights*labels)[order],starts)
        neg=np.add.reduceat((weights*(1-labels))[order],starts)
        if not pos.sum() or not neg.sum():return None
        return float(np.sum(pos*(np.cumsum(neg)-neg+.5*neg))/(pos.sum()*neg.sum()))
    return auc

def identity_bootstrap_auc(scores,labels,rows,reps=1000):
    ends=[identity_endpoints(r) for r in rows]
    identities=sorted({i for pair in ends for i in pair});lookup={s:i for i,s in enumerate(identities)}
    left=np.array([lookup[a] for a,b in ends]);right=np.array([lookup[b] for a,b in ends]);same=left==right
    rng=np.random.default_rng(42);values=[];calc=sorted_auc_plan(scores,labels)
    for _ in range(reps):
        counts=rng.multinomial(len(identities),np.full(len(identities),1/len(identities)))
        weights=counts[left]*counts[right];weights[same]=counts[left[same]]
        value=calc(weights)
        if value is not None:values.append(value)
    return {'method':'two-endpoint identity node resampling sensitivity; same-identity edge weight count, different-identity edge weight product',
        'conditional_on':'fixed trained checkpoint and frozen protocol; not a population security guarantee',
        'requested_replicates':reps,'valid_replicates':len(values),'seed':42,
        'auc_ci_95':[float(x) for x in np.percentile(values,[2.5,97.5])],
        'identities':len(identities)}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--seed',required=True,type=int);ap.add_argument('--variant',required=True,choices=VARIANTS)
    ap.add_argument('--threads',type=int,default=8);args=ap.parse_args()
    torch.set_num_threads(args.threads);torch.set_num_interop_threads(1)
    torch.manual_seed(42)
    started=time.monotonic();name=f'seed{args.seed}_{args.variant}'
    checkpoint=RUN/'checkpoints'/f'{name}.pt'
    out=RUN/'evaluation'/name;out.mkdir(parents=True,exist_ok=True)
    files=protocols();pairs={k:read(p) for k,p in files.items()}
    signature={'checkpoint_sha256':sha(checkpoint),'evaluator_sha256':sha(__file__),
        'model_code_sha256':sha(RUN/'runtime/model.py'),'metrics_code_sha256':sha(RUN/'runtime/verification.py'),
        'common_code_sha256':sha(HERE/'cpu_common.py'),
        'pairs_sha256':{k:sha(p) for k,p in files.items()},'quality_vector':[1,0,0,1]}
    reportfile=out/'EVALUATION_REPORT.json'
    if reportfile.exists():
        previous=json.loads(reportfile.read_text())
        if previous['signature']==signature and previous['status']=='complete':
            for item in previous['protocols'].values():
                if sha(out/item['raw_scores'])!=item['raw_scores_sha256']:raise ValueError('Score output changed')
            print('Verified evaluation already complete',name,flush=True);return
        raise ValueError('Existing evaluation has a different signature; preserve it and choose a new output directory')
    c=torch.load(checkpoint,map_location='cpu',weights_only=False)
    if not c.get('complete') or c.get('seed')!=args.seed or c.get('variant')!=args.variant:
        raise ValueError('Checkpoint incomplete or wrong seed/variant')
    model=VerificationModel(args.variant).cpu();model.load_state_dict(c['model']);model.eval();del c
    keys=sorted({k for rs in pairs.values() for r in rs for k in endpoints(r)})
    lookup={key:i for i,key in enumerate(keys)}
    dual=args.variant in ('fixed_fusion','gated_fusion')
    cache=out/'branch_embeddings.npz'
    face=np.zeros((len(keys),768),np.float32);peri=np.zeros_like(face);done=np.zeros(len(keys),bool)
    if cache.exists():
        with np.load(cache,allow_pickle=False) as saved:
            if str(saved['signature'])!=json.dumps(signature,sort_keys=True):raise ValueError('Stale embedding cache')
            face=saved['face'];peri=saved['peri'];done=saved['done']
    tf=v2.Compose([v2.ToImage(),v2.Resize((224,224)),v2.ToDtype(torch.float32,scale=True),
        v2.Normalize([.485,.456,.406],[.229,.224,.225])])
    def load(part,indices):
        images=[]
        for i in indices:
            with Image.open(DATA/keys[i][part]) as im:images.append(tf(im.convert('RGB')))
        return torch.stack(images)
    def save_cache():
        tmp=cache.with_suffix('.tmp')
        with tmp.open('wb') as f:np.savez(f,face=face,peri=peri,done=done,signature=json.dumps(signature,sort_keys=True))
        os.replace(tmp,cache)
    todo=np.flatnonzero(~done)
    for start in range(0,len(todo),8):
        indices=todo[start:start+8]
        with torch.inference_mode():
            if args.variant!='peri_lora':
                z=nn.functional.normalize(model.face_proj(pooled(model.face_encoder,load(0,indices))),dim=-1)
                face[indices]=z.numpy()
            if dual or args.variant=='peri_lora':
                z=nn.functional.normalize(model.peri_proj(pooled(model.peri_encoder,load(1,indices))),dim=-1)
                peri[indices]=z.numpy()
        done[indices]=True
        print(f'embedded={done.sum()}/{len(keys)}',flush=True)
        if (start//8)%12==0:save_cache()
    save_cache()
    if not done.all():raise ValueError('Incomplete embeddings')
    image_ledger=[{'face_path':a,'peri_path':b,'face_sha256':sha(DATA/a),'peri_sha256':sha(DATA/b)} for a,b in keys]
    write(out/'image_provenance.csv',image_ledger)
    gate=None;validation_mean=None
    if args.variant=='gated_fusion':
        with torch.inference_mode():
            quality=torch.tensor([[1.,0.,0.,1.]]*len(keys))
            gate=torch.sigmoid(model.gate(torch.cat([torch.from_numpy(face),torch.from_numpy(peri),quality],dim=1))).numpy().reshape(-1)
        valkeys={k for name,rs in pairs.items() if name.startswith('val_') for r in rs for k in endpoints(r)}
        validation_mean=float(np.mean([gate[lookup[k]] for k in valkeys]))
        embeddings={
            'learned':normalize(gate[:,None]*face+(1-gate[:,None])*peri),
            'constant_0.5_same_branches':normalize(.5*face+.5*peri),
            'validation_mean_gate_same_branches':normalize(validation_mean*face+(1-validation_mean)*peri),
            'permuted_gate_same_branches':None,
            'face_branch':face,'peri_branch':peri}
        # Constant q contributes only a fixed bias to the first gate layer.
        first=model.gate[0];q=torch.tensor([1.,0.,0.,1.])
        folded=nn.Linear(1536,128)
        with torch.no_grad():
            folded.weight.copy_(first.weight[:,:1536]);folded.bias.copy_(first.bias+first.weight[:,1536:]@q)
            alternate=torch.sigmoid(model.gate[2](model.gate[1](folded(torch.from_numpy(np.concatenate([face,peri],axis=1)))))).numpy().reshape(-1)
        fold_error=float(np.max(np.abs(gate-alternate)))
        if fold_error>1e-5:raise ValueError('Constant-quality fold equivalence failed')
    elif dual:embeddings={'primary':normalize(.5*face+.5*peri)}
    else:embeddings={'primary':peri if args.variant=='peri_lora' else face}
    primary='learned' if gate is not None else 'primary'
    all_scores={};reports={};controls={}
    for protocol,rs in pairs.items():
        left=np.array([lookup[endpoints(r)[0]] for r in rs]);right=np.array([lookup[endpoints(r)[1]] for r in rs])
        labels=np.array([int(r['label']) for r in rs])
        for control,z in embeddings.items():
            if control=='permuted_gate_same_branches':
                # Preserve this protocol's gate distribution; do not exchange
                # weights across validation, test, or external datasets.
                indices=np.unique(np.r_[left,right])
                shuffled=gate.copy()
                shuffled[indices]=gate[np.random.default_rng(42).permutation(indices)]
                z=normalize(shuffled[:,None]*face+(1-shuffled[:,None])*peri)
            scores=np.sum(z[left].astype(np.float64)*z[right].astype(np.float64),axis=1)
            if not np.all(np.isfinite(scores)):raise ValueError('Invalid scores')
            if control==primary:
                raw=out/f'{protocol}_raw_scores.csv';write(raw,[dict(r,score=f'{s:.10f}') for r,s in zip(rs,scores)])
                # Compute exactly from the shipped precision.
                scores=np.array([float(f'{s:.10f}') for s in scores]);all_scores[protocol]=(scores,labels)
                reports[protocol]={'metrics':summarize(scores,labels),'pairs_sha256':sha(files[protocol]),
                    'raw_scores':raw.name,'raw_scores_sha256':sha(raw),
                    'far_resolution':float(1/np.sum(labels==0))}
                if not protocol.startswith('val_'):
                    reports[protocol]['identity_bootstrap_auc']=identity_bootstrap_auc(scores,labels,rs)
            controls.setdefault(protocol,{})[control]=summarize(scores,labels)
        if gate is not None:
            ids=sorted(set(left)|set(right));values=gate[ids]
            controls[protocol]['gate_distribution']={'unique_images':len(ids),'mean':float(values.mean()),
                'sd':float(values.std()),'quantiles':np.quantile(values,[0,.05,.25,.5,.75,.95,1]).tolist(),
                'fraction_below_0.05':float(np.mean(values<.05)),'fraction_above_0.95':float(np.mean(values>.95))}
    for condition in ('masked','sunglasses','neutral'):
        vs,vl=all_scores[f'val_{condition}'];ts,tl=all_scores[f'test_{condition}']
        reports[f'test_{condition}']['validation_calibrated']={}
        for far in (.01,.001):
            threshold=calibrate(vs,vl,far)
            reports[f'test_{condition}']['validation_calibrated'][str(far)]={
                'calibration_protocol':f'val_{condition}','validation':at_threshold(vs,vl,threshold),
                'test':at_threshold(ts,tl,threshold),'validation_far_resolution':float(1/np.sum(vl==0))}
    for external in ('mfr2','rmfrd'):
        vs,vl=all_scores['val_masked'];ts,tl=all_scores[external]
        reports[external]['transferred_rof_validation_thresholds']={str(far):at_threshold(ts,tl,calibrate(vs,vl,far)) for far in (.01,.001)}
    report={'status':'complete','seed':args.seed,'variant':args.variant,'device':'cpu',
        'elapsed_seconds':time.monotonic()-started,'signature':signature,
        'training_status':'new full clean-manifest five-epoch training',
        'image_provenance_sha256':sha(out/'image_provenance.csv'),
        'protocols':reports,'gate_controls':controls if gate is not None else None,
        'gate_validation_mean':validation_mean,
        'gate_permutation_policy':'seed 42, within the unique image endpoints of each protocol separately',
        'constant_quality_fold_max_absolute_error':fold_error if gate is not None else None,
        'limitations':['unknown pretraining identity overlap','remaining semantic labels not independently certified',
            'retrospective ROC metrics distinct from validation-calibrated operating points',
            'very low FAR claims limited by finite and dependent impostor pairs']}
    save_json(reportfile,json_ready_report(report))
    print('EVALUATION COMPLETE',name,flush=True)

if __name__=='__main__':main()
