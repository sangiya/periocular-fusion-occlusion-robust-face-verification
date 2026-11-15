"""Freeze a distinct prospective experiment before training any new model."""
from pathlib import Path
import csv, hashlib, json
from collections import Counter
from audit_images import HERE, DATA, RELEASE, read, write

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    inventory=read(HERE/'image_inventory.csv')
    if any(r['sha256_matches']!='True' for r in inventory):
        raise ValueError('Physical image hash mismatch')
    candidates=read(HERE/'perceptual_cross_identity_candidates.csv')
    # Comparing the photographs establishes duplicated content, not the person's identity.
    confirmed={candidates[0]['path1'],candidates[0]['path2']}
    assert candidates[0]['hamming_distance']=='2'
    for i,r in enumerate(candidates):
        r['decision']='exclude_both_near_identical_photograph' if i==0 else 'different_photographs_no_duplicate_exclusion'
    write(HERE/'perceptual_review.csv',candidates)
    rows=read(RELEASE/'manifests/cleaned/rof_training_clean.csv')
    removed=[dict(r,exclusion_reason='visually_confirmed_cross_split_near_duplicate') for r in rows if r['face_path'] in confirmed]
    retained=[r for r in rows if r['face_path'] not in confirmed]
    assert len(removed)==2
    out=HERE/'experiment'; out.mkdir(exist_ok=True)
    manifest=out/'training_manifest.csv'; write(manifest,retained)
    write(out/'additional_exclusions.csv',removed)
    pixel={r['path']:r for r in inventory}
    for r in retained:
        if pixel[r['face_path']]['decode_error']: raise ValueError(r['face_path'])
        # Validate every periocular image, not only its path.
        from PIL import Image
        with Image.open(DATA/r['peri_path']) as im: im.load()
    fields=['pair_id','condition','label','probe_identity','enroll_identity']
    for role in ('probe','enroll'):
        fields += [f'{role}_image_id',f'{role}_face_path',f'{role}_peri_path',
                   f'{role}_face_conf',f'{role}_peri_conf',f'{role}_blur',f'{role}_visible_ratio']
    counts={}
    for split in ('val','test'):
        splitrows=[r for r in retained if r['split']==split]
        for condition in ('masked','sunglasses','neutral'):
            eligible={}
            for identity in sorted({r['identity'] for r in splitrows}):
                local=sorted([r for r in splitrows if r['identity']==identity],key=lambda r:r['face_path'])
                neutral=[r for r in local if r['condition']=='neutral']
                probes=[r for r in local if r['condition']==condition and (not neutral or r['face_path']!=neutral[0]['face_path'])]
                if neutral and probes: eligible[identity]=(neutral[0],probes)
            pairs=[]
            for identity,(unused,probes) in eligible.items():
                for probe in probes:
                    for eid,(enroll,_) in eligible.items():
                        pair={'pair_id':f'{split}-{condition}-{len(pairs):08d}', 'condition':condition,
                              'label':int(identity==eid),'probe_identity':identity,'enroll_identity':eid}
                        for role,image in (('probe',probe),('enroll',enroll)):
                            pair[f'{role}_image_id']=hashlib.sha256(image['face_path'].encode()).hexdigest()[:20]
                            for kind in ('face_path','peri_path'): pair[f'{role}_{kind}']=image[kind]
                            for key,default in [('face_conf','1'),('peri_conf','0'),('blur','0'),('visible_ratio','1')]:
                                pair[f'{role}_{key}']=image.get(key) or default
                        pairs.append(pair)
            write(out/f'{split}_{condition}_pairs.csv',pairs,fields)
            counts[f'{split}_{condition}']={'pairs':len(pairs),'genuine':sum(r['label'] for r in pairs),'eligible_identities':len(eligible)}
    tree=json.loads((HERE/'upstream_rof_tree.json').read_text(encoding='utf-8-sig'))
    upstream={r['path']:r['sha'] for r in tree['tree'] if r['type']=='blob'}
    matched=[];different=[]
    for p in sorted((DATA/'data/ROF/ROF').glob('*/*.pkl')):
        b=p.read_bytes(); blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
        rel=p.relative_to(DATA/'data/ROF').as_posix()
        (matched if upstream.get(rel)==blob else different).append(rel)
    provenance={'official_repository':'https://github.com/ekremerakin/RealWorldOccludedFaces',
        'official_tree_sha':tree['sha'],'local_annotations_matching_upstream':len(matched),
        'local_annotation_mismatches':different,
        'missing_official_annotations':sorted(k for k in upstream if k.endswith('.pkl') and k not in matched+different),
        'image_acquisition_log_available':False,
        'interpretation':'Annotation snapshot verified separately from reconstructed JPEG origin. URL availability, converter behavior, and labels remain distinct issues.'}
    (HERE/'DATASET_PROVENANCE.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8')
    plan={'status':'protocol frozen; training not yet completed','manifest_sha256':sha(manifest),
        'rows_by_split':dict(Counter(r['split'] for r in retained)),
        'seeds':[7,42,123],'variants':['frozen_whole','whole_lora','peri_lora','fixed_fusion','gated_fusion'],
        'epochs':5,'batch_size':16,'lr':1e-4,'max_batches':0,
        'selection':'fixed final epoch; no selection on test scores',
        'quality_vector':[1,0,0,1],
        'threshold_calibration':'per-condition validation identities only; report actual test FAR and TAR',
        'gate_controls':['learned','constant_0.5_same_branches','validation_mean_gate_same_branches','permuted_gate_same_branches','face_branch','peri_branch'],
        'pair_counts':counts,'unresolved':'Full semantic identity validation and unknown pretraining identity overlap are not certified.'}
    plan['input_hashes']={p.name:sha(p) for p in sorted(out.glob('*.csv'))}
    (out/'EXPERIMENT_PLAN.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
    print(json.dumps(plan,indent=2)); print(json.dumps(provenance,indent=2))

if __name__=='__main__':main()
