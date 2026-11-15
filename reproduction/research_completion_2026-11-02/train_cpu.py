"""Full CPU training with atomic batch checkpoints and optimizer/RNG resume.

No smoke limit is used by the research sweep. Samples are drawn with replacement
as in the historical single-source sampler. Only training-split rows are read.
"""
import argparse,csv,os,random,sys,time
from pathlib import Path
os.environ['HF_HUB_OFFLINE']='1'
os.environ['TRANSFORMERS_OFFLINE']='1'
os.environ['CUDA_VISIBLE_DEVICES']=''
print('Loading CPU research runtime (offline cached DINOv2).',flush=True)
import numpy as np
from PIL import Image
import torch
from torch import nn
from torchvision.transforms import v2
from cpu_common import HERE,DATA,EXPERIMENT,RUN,VARIANTS,sha,save_json
sys.path.insert(0,str(RUN/'runtime'))
from model import VerificationModel,pooled

def transform():
    return v2.Compose([v2.ToImage(),v2.Resize((224,224)),
        v2.ToDtype(torch.float32,scale=True),v2.Normalize([.485,.456,.406],[.229,.224,.225])])

def forward(model,face,peri,quality):
    if model.variant=='peri_lora':
        # The historical unused whole-face branch has no influence on the loss.
        return nn.functional.normalize(model.peri_proj(pooled(model.peri_encoder,peri)),dim=-1)
    return model(face,peri,quality)

def atomic_checkpoint(path,state):
    tmp=path.with_suffix('.partial');torch.save(state,tmp);os.replace(tmp,path)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--seed',required=True,type=int)
    ap.add_argument('--variant',required=True,choices=VARIANTS)
    ap.add_argument('--threads',type=int,default=8)
    ap.add_argument('--epochs',type=int,default=5)
    ap.add_argument('--max-batches',type=int,default=0,help='smoke test only; isolated smoke output')
    args=ap.parse_args()
    torch.set_num_threads(args.threads);torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    random.seed(args.seed);np.random.seed(args.seed);torch.manual_seed(args.seed)
    manifest=EXPERIMENT/'training_manifest.csv'
    plan=__import__('json').loads((EXPERIMENT/'EXPERIMENT_PLAN.json').read_text())
    if sha(manifest)!=plan['manifest_sha256']:raise ValueError('Frozen manifest changed')
    with manifest.open(encoding='utf-8',newline='') as f: allrows=list(csv.DictReader(f))
    if len({r['sha256'] for r in allrows})!=len(allrows):raise ValueError('Repeated content')
    splits={}
    for r in allrows: splits.setdefault(r['identity'],set()).add(r['split'])
    if any(len(s)>1 for s in splits.values()):raise ValueError('Identity split overlap')
    rows=[r for r in allrows if r['split']=='train']
    for r in rows:
        if sha(DATA/r['face_path'])!=r['sha256']:raise ValueError('Image changed: '+r['face_path'])
    labels={s:i for i,s in enumerate(sorted({r['identity'] for r in rows}))}
    model=VerificationModel(args.variant).cpu()
    head=nn.Linear(768,len(labels))
    optimizer=torch.optim.AdamW([p for p in list(model.parameters())+list(head.parameters()) if p.requires_grad],lr=1e-4,weight_decay=1e-4)
    out=RUN/('smoke' if args.max_batches else 'checkpoints')
    out.mkdir(parents=True,exist_ok=True)
    path=out/f'seed{args.seed}_{args.variant}.pt'
    status=out/f'seed{args.seed}_{args.variant}_progress.json'
    batch_size=16;total_batches=(len(rows)+batch_size-1)//batch_size
    limit=min(total_batches,args.max_batches) if args.max_batches else total_batches
    epoch=1;batch_start=0;order=None;losses=[];elapsed=0.;steps=0
    signature={'manifest_sha256':sha(manifest),'trainer_sha256':sha(Path(__file__)),
        'model_code_sha256':sha(RUN/'runtime/model.py'),'seed':args.seed,'variant':args.variant,
        'epochs':args.epochs,'batch_size':batch_size,'max_batches':args.max_batches,
        'lr':1e-4,'weight_decay':1e-4,'torch_version':torch.__version__,
        'threads':args.threads,'device':'cpu','quality_vector':[1,0,0,1],
        'sampler':'uniform replacement, n_train draws per epoch',
        'peri_optimization':'unused whole-face forward skipped; no target/test data used'}
    if path.exists():
        c=torch.load(path,map_location='cpu',weights_only=False)
        if c['signature']!=signature: raise ValueError('Resume signature mismatch')
        if c['complete']:print('Already complete',path,flush=True);return
        model.load_state_dict(c['model']);head.load_state_dict(c['head']);optimizer.load_state_dict(c['optimizer'])
        epoch=c['next_epoch'];batch_start=c['next_batch'];order=c['sample_order'];losses=c['epoch_losses']
        elapsed=c['elapsed_seconds'];steps=c['optimizer_steps']
        random.setstate(c['rng_python']);np.random.set_state(c['rng_numpy']);torch.set_rng_state(c['rng_torch'])
        print(f'Resuming epoch={epoch} batch={batch_start+1} steps={steps}',flush=True)
    tf=transform();session_start=time.monotonic();last_save=time.monotonic()
    criterion=nn.CrossEntropyLoss()
    print(f'FULL CPU RUN {args.variant} seed={args.seed} training_rows={len(rows)} batches={limit} epochs={args.epochs} smoke={bool(args.max_batches)}',flush=True)
    def checkpoint(next_epoch,next_batch,complete=False):
        duration=elapsed+time.monotonic()-session_start
        state={'model':model.state_dict(),'head':head.state_dict(),'optimizer':optimizer.state_dict(),
            'variant':args.variant,'seed':args.seed,'epoch':args.epochs if complete else next_epoch-1,
            'manifest_sha256':signature['manifest_sha256'],'id_to_label':labels,'signature':signature,
            'next_epoch':next_epoch,'next_batch':next_batch,'sample_order':order,'epoch_losses':losses,
            'rng_python':random.getstate(),'rng_numpy':np.random.get_state(),'rng_torch':torch.get_rng_state(),
            'elapsed_seconds':duration,'optimizer_steps':steps,'complete':complete}
        atomic_checkpoint(path,state)
        save_json(status,{'variant':args.variant,'seed':args.seed,'next_epoch':next_epoch,
            'next_batch':next_batch,'batches_per_epoch':limit,'epochs':args.epochs,'complete':complete,
            'optimizer_steps':steps,'elapsed_seconds':duration,'mean_loss_this_epoch':float(np.mean(losses)) if losses else None,
            'signature':signature})
    for e in range(epoch,args.epochs+1):
        if order is None:
            order=torch.multinomial(torch.ones(len(rows),dtype=torch.double),len(rows),replacement=True).tolist()
            losses=[];batch_start=0
        model.train();head.train()
        for b in range(batch_start,limit):
            started=time.monotonic()
            selected=[rows[i] for i in order[b*batch_size:(b+1)*batch_size]]
            def load(key):
                tensors=[]
                for r in selected:
                    with Image.open(DATA/r[key]) as image:tensors.append(tf(image.convert('RGB')))
                return torch.stack(tensors)
            face=load('face_path') if args.variant!='peri_lora' else None
            peri=load('peri_path') if args.variant in ('peri_lora','fixed_fusion','gated_fusion') else None
            quality=torch.tensor([[1.,0.,0.,1.]]*len(selected))
            target=torch.tensor([labels[r['identity']] for r in selected])
            optimizer.zero_grad(set_to_none=True)
            loss=criterion(head(forward(model,face,peri,quality)),target)
            if not torch.isfinite(loss):raise RuntimeError('Nonfinite training loss')
            loss.backward();optimizer.step();steps+=1;losses.append(float(loss.detach()))
            print(f'epoch={e}/{args.epochs} batch={b+1}/{limit} loss={losses[-1]:.6f} seconds={time.monotonic()-started:.2f}',flush=True)
            # At most 10 minutes of progress lost after an interruption.
            if time.monotonic()-last_save>=600 or b==0:
                checkpoint(e,b+1);last_save=time.monotonic()
            else:
                save_json(status,{'variant':args.variant,'seed':args.seed,'epoch':e,'batch':b+1,
                    'batches_per_epoch':limit,'epochs':args.epochs,'complete':False,'optimizer_steps':steps,
                    'elapsed_seconds':elapsed+time.monotonic()-session_start,'last_loss':losses[-1],'device':'cpu'})
        print(f'EPOCH COMPLETE {e} mean_loss={np.mean(losses):.6f}',flush=True)
        order=None;batch_start=0;losses=[]
        checkpoint(e+1,0,complete=e==args.epochs);last_save=time.monotonic()
    print('TRAINING COMPLETE',path,flush=True)

if __name__=='__main__': main()
