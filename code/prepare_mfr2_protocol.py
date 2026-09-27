"""Freeze the complete-case subset of the official MFR2 pair list."""
import argparse, csv, hashlib, json
from pathlib import Path

def norm(p): return str(Path(p).resolve()).lower()
def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--pairs',required=True); ap.add_argument('--crops',required=True); ap.add_argument('--out-dir',required=True); a=ap.parse_args()
    pairs=list(csv.DictReader(open(a.pairs,newline='',encoding='utf-8')))
    crops=list(csv.DictReader(open(a.crops,newline='',encoding='utf-8')))
    crop_by_face={norm(r['face_path']):r for r in crops if r.get('crop_status')=='valid' and r.get('peri_path') and Path(r['peri_path']).is_file()}
    out=[]; excluded=[]
    for i,r in enumerate(pairs):
        c1,c2=crop_by_face.get(norm(r['path1'])),crop_by_face.get(norm(r['path2']))
        if not c1 or not c2:
            excluded.append({'official_index':i,'path1':r['path1'],'path2':r['path2'],'label':r['label'],'missing_side':'both' if not c1 and not c2 else ('path1' if not c1 else 'path2')}); continue
        out.append({'pair_id':f'mfr2-{i:04d}','official_index':i,'label':int(r['label']),'identity1':r['identity1'],'identity2':r['identity2'],'face_path1':r['path1'],'peri_path1':c1['peri_path'],'face_path2':r['path2'],'peri_path2':c2['peri_path']})
    od=Path(a.out_dir); od.mkdir(parents=True,exist_ok=True)
    fields=['pair_id','official_index','label','identity1','identity2','face_path1','peri_path1','face_path2','peri_path2']
    with open(od/'mfr2_official_complete_pairs.csv','w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(out)
    with open(od/'mfr2_excluded_pairs.csv','w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['official_index','path1','path2','label','missing_side']); w.writeheader(); w.writerows(excluded)
    pos=sum(int(r['label']) for r in out); meta={'official_pairs':len(pairs),'included_pairs':len(out),'excluded_pairs':len(excluded),'included_genuine':pos,'included_impostor':len(out)-pos,'far_resolution':1/(len(out)-pos),'source_pairs_sha256':digest(a.pairs),'crop_manifest_sha256':digest(a.crops)}
    json.dump(meta,open(od/'mfr2_protocol_metadata.json','w',encoding='utf-8'),indent=2); print(json.dumps(meta,indent=2))
if __name__=='__main__': main()
