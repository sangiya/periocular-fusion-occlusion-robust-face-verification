"""Package only canonical final venue sources and the current reproducibility release."""
from pathlib import Path
import argparse,hashlib,json,re,zipfile

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def zip_bytes(path,items):
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in sorted(items.items()):
            info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            info.create_system=3;info.external_attr=0o100644<<16
            z.writestr(info,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    with zipfile.ZipFile(path) as z:assert z.testzip() is None

def source_files(folder,entrypoints):
    items={};queue=list(entrypoints)
    while queue:
        name=queue.pop()
        if name in items:continue
        if Path(name).name!=name:raise ValueError('Expected flat source path: '+name)
        path=folder/name;data=path.read_bytes();items[name]=data
        text=data.decode('utf-8')
        for child in re.findall(r'\\input\{([^}]+)\}',text):queue.append(child if child.endswith('.tex') else child+'.tex')
        for figure in re.findall(r'\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}',text):
            if Path(figure).name!=figure:raise ValueError('Expected flat figure path: '+figure)
            items[figure]=(folder/figure).read_bytes()
    assert len(items)==8 and sum(n.endswith('.tex') for n in items)==2 and sum(n.endswith('.pdf') for n in items)==6
    return items

def payloads(root):
    result={}
    for path in sorted(root.rglob('*')):
        rel=path.relative_to(root)
        if not path.is_file() or any(p in {'.git','__pycache__','data','work','.venv','.pytest_cache'} for p in rel.parts):continue
        if rel.as_posix() in {'RELEASE_MANIFEST.json','verify_output.txt'} or path.name.startswith('~$') or path.suffix in {'.log','.aux','.out','.pyc'}:continue
        result[rel.as_posix()]=path.read_bytes()
    return result

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent)
    ap.add_argument('--output',type=Path)
    ap.add_argument('--sources-only',action='store_true')
    ap.add_argument('--check',action='store_true',help='Verify final manifest without writing')
    args=ap.parse_args();root=args.root.resolve()
    if args.check:
        data=payloads(root);manifest=json.loads((root/'RELEASE_MANIFEST.json').read_text())
        assert set(data)==set(manifest['files']),'Packaged membership changed'
        for name,contents in data.items():assert manifest['files'][name]=={'sha256':hashlib.sha256(contents).hexdigest(),'bytes':len(contents)},name
        print('Final release manifest: ALL CHECKS PASSED ('+str(len(data))+' files)');return
    for folder,entries,archive in [('submission_ieee',['main.tex','supplement.tex'],'IEEE_TBIOM_Source.zip'),('submission_arxiv',['main.tex'],'arXiv_Source.zip')]:
        directory=root/folder;zip_bytes(directory/archive,source_files(directory,entries))
    if args.sources_only:
        print('Final IEEE and arXiv source ZIPs rebuilt: two TeX files and six used figure PDFs each.');return
    archive=(args.output or root.parent/'publication_release_final.zip').resolve()
    if archive.is_relative_to(root):raise SystemExit('Release ZIP must be outside its input directory')
    data=payloads(root)
    manifest={'format':2,'note':'Final canonical publication and current result files only. Hashes cover every packaged file except this manifest. Original input manifests remain provenance records; superseded result sweeps are excluded.','files':{name:{'sha256':hashlib.sha256(contents).hexdigest(),'bytes':len(contents)} for name,contents in data.items()}}
    (root/'RELEASE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    data['RELEASE_MANIFEST.json']=(root/'RELEASE_MANIFEST.json').read_bytes();zip_bytes(archive,data)
    checksum=sha(archive);archive.with_suffix(archive.suffix+'.sha256').write_text(checksum+'  '+archive.name+'\n',encoding='ascii')
    print(json.dumps({'archive':str(archive),'sha256':checksum,'entries':len(data),'bytes':archive.stat().st_size},indent=2))
if __name__=='__main__':main()
