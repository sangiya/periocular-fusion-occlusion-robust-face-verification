"""Decode local ROF images; verify bytes and flag pixel/perceptual conflicts.

Perceptual candidates are review items, never proof of a wrong identity.
No image is changed. Restricted annotation reader permits only NumPy scalars.
"""
from pathlib import Path
import csv, hashlib, io, json, pickle
from collections import Counter, defaultdict
import numpy as np
import cv2
from PIL import Image, ImageOps, ImageDraw

HERE = Path(__file__).resolve().parent
DATA = HERE.parent
RELEASE = DATA / 'publication_release'

def read(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def write(path, rows, fields=None):
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields or list(rows[0]))
        w.writeheader(); w.writerows(rows)

class AnnotationReader(pickle.Unpickler):
    def find_class(self, module, name):
        if module in ('numpy.core.multiarray', 'numpy._core.multiarray') and name in ('scalar','_reconstruct'):
            return getattr(np.core.multiarray, name)
        if module == 'numpy' and name == 'dtype':
            return np.dtype
        if module == 'numpy' and name == 'ndarray':
            return np.ndarray
        raise pickle.UnpicklingError(f'Forbidden global: {module}.{name}')

def main():
    raw = read(RELEASE / 'manifests/rof_manifest.csv')
    clean = read(RELEASE / 'manifests/cleaned/rof_training_clean.csv')
    training = {r['face_path']: r for r in clean}
    import sys
    reuse = '--reuse-inventory' in sys.argv
    rows = read(HERE/'image_inventory.csv') if reuse else []
    if reuse:
        for r in rows:
            r['in_clean_manifest'] = int(r['in_clean_manifest'])
            r['sha256_matches'] = r['sha256_matches'] == 'True'
    for n, r in enumerate([] if reuse else raw):
        rel = r['path']; p = DATA / rel
        out = {'path':rel, 'identity': training.get(rel, {}).get('identity', ''),
               'split':training.get(rel, {}).get('split', ''), 'condition':r.get('condition', ''),
               'in_clean_manifest':int(rel in training), 'decode_error':'',
               'sha256_matches':False, 'pixel_sha256':'', 'phash':'', 'width':0,'height':0}
        try:
            actual = hashlib.sha256(p.read_bytes()).hexdigest()
            out['sha256_matches'] = actual == r['sha256']
            with Image.open(p) as im:
                im.load(); im = ImageOps.exif_transpose(im).convert('RGB')
                out['width'], out['height'] = im.size
                out['pixel_sha256'] = hashlib.sha256(str(im.size).encode()+im.tobytes()).hexdigest()
                gray = np.asarray(im.convert('L').resize((32,32)), dtype=np.float32)
                dct = cv2.dct(gray)[:8,:8].reshape(-1)
                bits = dct > np.median(dct[1:])
                bits[0] = False
                out['phash'] = np.packbits(bits).tobytes().hex()
        except Exception as e:
            out['decode_error'] = str(e)
        rows.append(out)
        if n % 1000 == 0: print(f'decoded {n}/{len(raw)}', flush=True)
    write(HERE/'image_inventory.csv', rows)
    selected = [r for r in rows if r['in_clean_manifest'] and not r['decode_error']]
    bypixel = defaultdict(list)
    for r in selected: bypixel[r['pixel_sha256']].append(r)
    pixel_groups = [rs for rs in bypixel.values() if len(rs)>1]
    candidates = []
    hashes = np.array([list(bytes.fromhex(r['phash'])) for r in selected], dtype=np.uint8)
    popcount = np.array([int(i).bit_count() for i in range(256)], dtype=np.uint8)
    for i, r in enumerate(selected):
        distances = popcount[np.bitwise_xor(hashes[i+1:], hashes[i])].sum(axis=1)
        for offset in np.where(distances <= 6)[0]:
            j = i + 1 + int(offset); other = selected[j]
            if r['identity'] == other['identity'] and r['split'] == other['split']: continue
            candidates.append({'path1':r['path'],'path2':other['path'],
                'identity1':r['identity'],'identity2':other['identity'],
                'split1':r['split'],'split2':other['split'],
                'hamming_distance':int(distances[offset]),
                'decoded_pixels_equal':r['pixel_sha256']==other['pixel_sha256'],
                'decision':'pending_visual_review'})
    candidates.sort(key=lambda r:(r['hamming_distance'], r['path1'], r['path2']))
    write(HERE/'perceptual_cross_identity_candidates.csv', candidates,
          ['path1','path2','identity1','identity2','split1','split2','hamming_distance','decoded_pixels_equal','decision'])
    sheets = HERE/'review_sheets'; sheets.mkdir(exist_ok=True)
    for start in range(0,len(candidates),12):
        sheet = Image.new('RGB',(960,12*145),'white'); draw=ImageDraw.Draw(sheet)
        for k, pair in enumerate(candidates[start:start+12]):
            for side in (1,2):
                x=(side-1)*480; y=k*145
                with Image.open(DATA/pair[f'path{side}']) as im:
                    im=ImageOps.contain(im.convert('RGB'),(135,135))
                    sheet.paste(im,(x,y))
                draw.text((x+140,y+10),pair[f'identity{side}'][:38],fill='black')
                draw.text((x+140,y+35),pair[f'split{side}'],fill='black')
                draw.text((x+140,y+60),f"candidate {start+k}; distance {pair['hamming_distance']}",fill='black')
        sheet.save(sheets/f'candidates_{start:04d}.jpg')
    annots=[]
    for p in sorted((DATA/'data/ROF/ROF').glob('*/*.pkl')):
        row={'path':p.relative_to(DATA).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
             'condition':p.parent.name,'identity_file':p.stem,'records':0,'faces':0,'error':''}
        try:
            obj=AnnotationReader(io.BytesIO(p.read_bytes())).load()
            row['records']=len(obj)
            row['faces']=sum(len(v.get('faces',[])) for v in obj.values())
        except Exception as e: row['error']=str(e)
        annots.append(row)
    write(HERE/'annotation_inventory.csv',annots)
    report={'scope':'ROF bytes, decoded pixels, and perceptual candidates; no automatic identity certification',
        'raw_rows':len(raw),'clean_rows':len(clean),
        'decode_failures':sum(bool(r['decode_error']) for r in rows),
        'recorded_sha256_mismatches':sum(not r['sha256_matches'] for r in rows),
        'clean_decoded_pixel_duplicate_groups':len(pixel_groups),
        'clean_pixel_cross_identity_groups':sum(len({r['identity'] for r in rs})>1 for rs in pixel_groups),
        'clean_pixel_cross_split_groups':sum(len({r['split'] for r in rs})>1 for rs in pixel_groups),
        'cross_identity_perceptual_candidates':len(candidates),
        'cross_split_perceptual_candidates':sum(r['split1']!=r['split2'] for r in candidates),
        'annotation_files':len(annots),'annotation_read_failures':sum(bool(r['error']) for r in annots),
        'annotation_counts':{c:{'identities':sum(r['condition']==c for r in annots),
            'records':sum(r['records'] for r in annots if r['condition']==c),
            'faces':sum(r['faces'] for r in annots if r['condition']==c)}
            for c in ('masked','sunglasses','neutral')},
        'pixel_duplicate_groups':[[r['path'] for r in rs] for rs in pixel_groups]}
    (HERE/'IMAGE_AUDIT.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='pixel_duplicate_groups'},indent=2))

if __name__=='__main__':main()
