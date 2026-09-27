"""Freeze deterministic complete-case RMFRD neutral-to-masked pairs."""
import argparse,csv,hashlib,json,random
from collections import defaultdict
from pathlib import Path
def iid(r): return hashlib.sha256((r['identity']+'|'+r['condition']+'|'+r['face_path']+'|'+r['peri_path']).encode()).hexdigest()[:20]
def main():
 p=argparse.ArgumentParser();p.add_argument('--crops',required=True);p.add_argument('--out-dir',required=True);p.add_argument('--impostors-per-probe',type=int,default=20);p.add_argument('--seed',type=int,default=42);a=p.parse_args()
 rows=list(csv.DictReader(open(a.crops,newline='',encoding='utf-8'))); valid=[r for r in rows if r.get('crop_status')=='valid' and r.get('peri_path') and Path(r['peri_path']).is_file() and Path(r['face_path']).is_file()];g=defaultdict(list)
 for r in valid:g[r['identity']].append(r)
 eligible={}
 for ident,rs in g.items():
  n=sorted([r for r in rs if r['condition']=='neutral'],key=lambda x:x['face_path']);m=sorted([r for r in rs if r['condition']=='masked'],key=lambda x:x['face_path'])
  if n and m:eligible[ident]={'enroll':n[0],'probes':m}
 ids=sorted(eligible)
 if len(ids)<2 or not 1<=a.impostors_per_probe<len(ids):raise ValueError('Need at least two eligible identities and 1 <= impostors-per-probe < identity count')
 od=Path(a.out_dir)
 if (od/'rmfrd_pairs.csv').exists():raise FileExistsError('Protocol already exists; use a fresh output directory to preserve it')
 fields=['pair_id','condition','label','probe_identity','enroll_identity','probe_image_id','probe_face_path','probe_peri_path','probe_face_conf','probe_peri_conf','probe_blur','probe_visible_ratio','enroll_image_id','enroll_face_path','enroll_peri_path','enroll_face_conf','enroll_peri_conf','enroll_blur','enroll_visible_ratio'];out=[];k=0
 for ident in ids:
  for probe in eligible[ident]['probes']:
   candidates=[x for x in ids if x!=ident]
   probe_seed=int(hashlib.sha256((str(a.seed)+'|'+iid(probe)).encode()).hexdigest(),16)
   targets=[ident]+random.Random(probe_seed).sample(candidates,a.impostors_per_probe)
   for target in targets:
    en=eligible[target]['enroll'];out.append({'pair_id':f'rmfrd-{k:08d}','condition':'masked','label':int(target==ident),'probe_identity':ident,'enroll_identity':target,'probe_image_id':iid(probe),'probe_face_path':probe['face_path'],'probe_peri_path':probe['peri_path'],'probe_face_conf':probe.get('face_conf',''),'probe_peri_conf':probe.get('peri_conf',''),'probe_blur':probe.get('blur',''),'probe_visible_ratio':probe.get('visible_ratio',''),'enroll_image_id':iid(en),'enroll_face_path':en['face_path'],'enroll_peri_path':en['peri_path'],'enroll_face_conf':en.get('face_conf',''),'enroll_peri_conf':en.get('peri_conf',''),'enroll_blur':en.get('blur',''),'enroll_visible_ratio':en.get('visible_ratio','')});k+=1
 od=Path(a.out_dir);od.mkdir(parents=True,exist_ok=True);op=od/'rmfrd_pairs.csv'
 with open(op,'w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(out)
 pos=sum(int(r['label']) for r in out);meta={'protocol_version':2,'sampling':'uniform_without_replacement_per_probe','seed':a.seed,'pairs_sha256':hashlib.sha256(op.read_bytes()).hexdigest(),'eligible_identities':len(ids),'masked_probes':pos,'impostors_per_probe':a.impostors_per_probe,'genuine_pairs':pos,'impostor_pairs':len(out)-pos,'total_pairs':len(out),'far_resolution':1/(len(out)-pos),'crop_rows':len(rows),'valid_crops':len(valid)};json.dump(meta,open(od/'rmfrd_protocol_metadata.json','w'),indent=2);print(json.dumps(meta,indent=2))
if __name__=='__main__':main()
