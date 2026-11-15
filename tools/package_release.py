"""Build deterministic arXiv/source and release archives from current checked files."""
from pathlib import Path
import argparse,hashlib,json,re,zipfile

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def zip_bytes(p,items):
    with zipfile.ZipFile(p,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in sorted(items.items()):
            info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED;info.create_system=3;info.external_attr=0o100644<<16
            z.writestr(info,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root",type=Path,default=Path(__file__).resolve().parent.parent)
    ap.add_argument("--output",type=Path)
    a=ap.parse_args();root=a.root.resolve()
    archive=(a.output or root.parent/"publication_release.zip").resolve()
    if archive.is_relative_to(root):raise SystemExit("Release ZIP must be outside its input directory")
    text=(root/"document/arXiv_Preprint_10Page_Final.tex").read_text(encoding="utf-8")
    text=text.replace("\\graphicspath{{../submission_ieee_10page/}}","\\graphicspath{{./}}")
    arxiv={"arXiv_Preprint_10Page_Final.tex":text.encode("utf-8")}
    for name in re.findall(r"\\input\{([^}]+)\}",text):
        name=name if name.endswith('.tex') else name+'.tex'
        if Path(name).name!=name:raise SystemExit('Expected flat source input: '+name)
        arxiv[name]=(root/'document'/name).read_bytes()
    figures=re.findall(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}",text)
    for name in figures:
        if Path(name).name!=name:raise SystemExit('Expected flat figure filename: '+name)
        arxiv[name]=(root/'submission_ieee_10page'/name).read_bytes()
    if len(set(figures))!=5:raise SystemExit('Expected five referenced vector figures')
    zip_bytes(root/"arxiv_source.zip",arxiv)
    files={}
    payloads={}
    for p in sorted(root.rglob("*")):
        rel=p.relative_to(root)
        if p.is_file() and not any(x in rel.parts for x in [".git","__pycache__","data","work"]) and rel.as_posix()!="RELEASE_MANIFEST.json":
            data=p.read_bytes()
            payloads[rel.as_posix()]=data
            files[rel.as_posix()]={"sha256":hashlib.sha256(data).hexdigest(),"bytes":len(data)}
    manifest={"format":1,"note":"Hashes cover every packaged file except this manifest. Archive checksum is external to avoid self-reference.","files":files}
    (root/"RELEASE_MANIFEST.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    items=payloads
    items["RELEASE_MANIFEST.json"]=(root/"RELEASE_MANIFEST.json").read_bytes()
    zip_bytes(archive,items)
    digest=sha(archive)
    archive.with_suffix(archive.suffix+".sha256").write_text(digest+"  "+archive.name+"\n",encoding="ascii")
    print(json.dumps({"archive":str(archive),"sha256":digest,"entries":len(items),"bytes":archive.stat().st_size},indent=2))
if __name__=="__main__":main()

