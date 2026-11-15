"""Train a new, isolated seed sweep on the audited content-unique ROF manifest.
This does not reuse historical checkpoints or claim historical scores were cleaned.
"""
from pathlib import Path
import argparse,csv,hashlib,subprocess,sys
VARIANTS=["frozen_whole","whole_lora","peri_lora","fixed_fusion","gated_fusion"]
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root",type=Path,default=Path(__file__).resolve().parent.parent)
    ap.add_argument("--dataset-root",type=Path,required=True)
    ap.add_argument("--seeds",type=int,nargs="+",default=[7,42,123])
    ap.add_argument("--variants",nargs="+",choices=VARIANTS,default=VARIANTS)
    ap.add_argument("--dry-run",action="store_true")
    a=ap.parse_args();root=a.root.resolve();data=a.dataset_root.resolve()
    # The later perceptual audit supersedes the preliminary exact-hash-only input.
    manifest=root/"manifests/cpu_followup/training_manifest.csv"
    rows=list(csv.DictReader(manifest.open(encoding="utf-8",newline="")))
    hashes=[r["sha256"] for r in rows]
    if not rows or len(hashes)!=len(set(hashes)):raise SystemExit("Clean training manifest is absent or has repeated hashes")
    groups={}
    for r in rows:
        groups.setdefault(r["identity"],set()).add(r["split"])
        for key in ["face_path","peri_path"]:
            if not (data/r[key]).is_file():raise FileNotFoundError(data/r[key])
    if any(len(x)>1 for x in groups.values()):raise SystemExit("Identity overlap between splits")
    digest=hashlib.sha256(manifest.read_bytes()).hexdigest()
    out=root/"work/clean_training"/digest[:12]/"checkpoints"
    for seed in a.seeds:
        for v in a.variants:
            target=out/f"seed{seed}_{v}.pt"
            if target.exists():raise FileExistsError(f"Refusing to reuse an existing checkpoint: {target}")
            cmd=[sys.executable,str(root/"code/train.py"),"--manifest",str(manifest),
                 "--variant",v,"--epochs","5","--batch-size","16","--lr","1e-4",
                 "--num-workers","0","--max-batches","0","--seed",str(seed),"--out",str(target)]
            print(" ".join(cmd),flush=True)
            if not a.dry_run:subprocess.run(cmd,cwd=data,check=True)
    print(f"{'DRY RUN: no models trained.' if a.dry_run else 'Training completed.'} New checkpoint directory: {out}")
if __name__=="__main__":main()

