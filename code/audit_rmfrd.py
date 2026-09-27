"""Read-only input audit and deterministic contact sheets; no model inference."""
import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pairs', default='manifests/rmfrd_pairs.csv',
                   help='RMFRD protocol pair file. The frozen one is shipped in manifests/.')
    p.add_argument('--out', default='work/rmfrd_audit')
    p.add_argument('--sample', type=int, default=24)
    a = p.parse_args()
    pairs = list(csv.DictReader(open(a.pairs, encoding='utf-8-sig', newline='')))
    if not pairs:
        raise ValueError('Empty pair file')
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    issues, images, genuine = [], {}, []
    exposure = Counter()
    seen = set()
    for r in pairs:
        if r['pair_id'] in seen:
            issues.append('Duplicate pair_id: ' + r['pair_id'])
        seen.add(r['pair_id'])
        if int(r['label']) != int(r['probe_identity'] == r['enroll_identity']):
            issues.append('Label/identity mismatch: ' + r['pair_id'])
        if int(r['label']) == 0:
            exposure[r['enroll_identity']] += 1
        else:
            genuine.append(r)
        for role in ('probe', 'enroll'):
            for kind in ('face', 'peri'):
                path = r[f'{role}_{kind}_path']
                images.setdefault(path, set()).add(r[f'{role}_identity'])
    records, hashes = [], defaultdict(list)
    for path, identities in sorted(images.items()):
        record = {'path': path, 'identities': '|'.join(sorted(identities)), 'error': ''}
        try:
            with Image.open(path) as im:
                im.load()
                record.update(width=im.width, height=im.height, mode=im.mode)
            digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()
            record['sha256'] = digest
            hashes[digest].append((path, identities))
        except Exception as exc:
            record['error'] = str(exc)
            issues.append('Unreadable image: ' + path)
        records.append(record)
    duplicates = [v for v in hashes.values() if len(v) > 1]
    cross_identity = [[x[0] for x in group] for group in duplicates
                      if len(set().union(*(x[1] for x in group))) > 1]
    fields = ['path', 'identities', 'width', 'height', 'mode', 'sha256', 'error']
    with (out / 'image_audit.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fields); w.writeheader(); w.writerows(records)
    # Sample different identities without selecting by model score or quality.
    by_identity = defaultdict(list)
    for r in genuine:
        by_identity[r['probe_identity']].append(r)
    identities = sorted(by_identity, key=lambda s: hashlib.sha256(('audit42|' + s).encode()).hexdigest())
    samples = [sorted(by_identity[s], key=lambda r: r['pair_id'])[0]
               for s in identities[:max(0, a.sample)]]
    for page in range(0, len(samples), 6):
        rows = samples[page:page + 6]
        canvas = Image.new('RGB', (896, len(rows) * 260), 'white')
        draw = ImageDraw.Draw(canvas)
        for j, r in enumerate(rows):
            draw.text((8, j * 260 + 4), f"{r['pair_id']} | {r['probe_identity']}", fill='black')
            for col, key in enumerate(('enroll_face_path', 'enroll_peri_path', 'probe_face_path', 'probe_peri_path')):
                draw.text((col * 224 + 8, j * 260 + 20), key, fill='black')
                try:
                    with Image.open(r[key]) as im:
                        thumb = ImageOps.contain(im.convert('RGB'), (216, 216))
                        canvas.paste(thumb, (col * 224 + 4, j * 260 + 40))
                except Exception:
                    draw.text((col * 224 + 8, j * 260 + 60), 'UNREADABLE', fill='red')
        canvas.save(out / f'contact_sheet_{page // 6 + 1:02d}.jpg')
    quality = {}
    for role in ('probe', 'enroll'):
        for field in ('face_conf', 'peri_conf', 'blur', 'visible_ratio'):
            vals = {r[f'{role}_image_id']: r.get(f'{role}_{field}', '') for r in pairs}
            quality[f'{role}_{field}'] = dict(Counter(vals.values()))
    summary = {'pairs': len(pairs), 'genuine_pairs': len(genuine),
               'impostor_pairs': sum(exposure.values()),
               'probe_identities': len(by_identity),
               'distinct_impostor_enrollment_identities': len(exposure),
               'top_impostor_enrollment_counts': exposure.most_common(25),
               'unique_image_paths': len(images), 'issues': issues,
               'cross_identity_exact_duplicate_groups': cross_identity,
               'quality_values_per_unique_image': quality,
               'note': 'Matching folder labels do not verify real-person identity. Inspect contact sheets manually.'}
    (out / 'audit_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in summary.items() if k != 'quality_values_per_unique_image'}, indent=2))
    print('Saved audit and contact sheets:', out.resolve())
    if issues:
        raise SystemExit('Resolve input errors before rerunning evaluation.')


if __name__ == '__main__':
    main()
