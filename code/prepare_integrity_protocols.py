"""Prepare auditable, non-destructive clean-input and score-sensitivity protocols."""
from pathlib import Path
import argparse,csv,json,hashlib
from collections import defaultdict,Counter

def read(p):
    with p.open(encoding="utf-8-sig",newline="") as f: return list(csv.DictReader(f))
def write(p,rs,fields=None):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields or list(rs[0]));w.writeheader();w.writerows(rs)
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def normalize(s): return "".join(c for c in s.lower() if c.isalnum())
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root",type=Path,default=Path(__file__).resolve().parent.parent)
    ap.add_argument("--dataset-root",type=Path,required=True)
    a=ap.parse_args();root=a.root.resolve();data=a.dataset_root.resolve()
    out=root/"manifests/cleaned";out.mkdir(parents=True,exist_ok=True)
    train=read(root/"manifests/crop_manifest_training_person_disjoint.csv")
    hashes=defaultdict(list)
    for r in train:
        if not r.get("sha256"): raise ValueError("Every ROF row must carry a content hash")
        hashes[r["sha256"]].append(r)
    conflict={h for h,rs in hashes.items() if len({r["identity"] for r in rs})>1 or len({r["split"] for r in rs})>1}
    kept=[];excluded=[];seen=set()
    for r in sorted(train,key=lambda r:r["face_path"]):
        reason="cross_identity_or_split_content_conflict" if r["sha256"] in conflict else ("repeated_image_content" if r["sha256"] in seen else "")
        if reason: excluded.append({**r,"exclusion_reason":reason})
        else:kept.append(r);seen.add(r["sha256"])
    write(out/"rof_training_clean.csv",kept)
    write(out/"rof_training_exclusions.csv",excluded)
    meta={"status":"Clean training inputs require NEW training; archived checkpoints are NOT retrained.",
          "rof_training":{"input_rows":len(train),"kept_rows":len(kept),"excluded_rows":len(excluded),
                          "conflicting_hash_groups":len(conflict),"exclusions_by_reason":dict(Counter(r["exclusion_reason"] for r in excluded)),
                          "rows_by_split":dict(Counter(r["split"] for r in kept)),
                          "persons_by_split":{s:len({r["identity"] for r in kept if r["split"]==s}) for s in ["train","val","test"]}},
          "protocols":{},"inputs":{}}
    raw=read(root/"manifests/rof_manifest.csv");path_hash={r["path"]:r["sha256"] for r in raw}
    for cond in ["masked","sunglasses","neutral"]:
        name=f"rof_{cond}_pairs.csv";pairs=read(root/"manifests"/name);probe_by_hash={}
        for r in sorted(pairs,key=lambda r:r["probe_face_path"]):
            h=path_hash[r["probe_face_path"]]
            if h not in conflict:probe_by_hash.setdefault(h,r["probe_face_path"])
        clean=[];removed=[]
        for r in pairs:
            h=path_hash[r["probe_face_path"]]
            reason="conflicting_content" if h in conflict else ("repeated_probe_content" if probe_by_hash[h]!=r["probe_face_path"] else "")
            (removed if reason else clean).append({**r,"exclusion_reason":reason} if reason else r)
        write(out/name,clean)
        write(out/f"rof_{cond}_excluded_pairs.csv",removed, list(pairs[0])+["exclusion_reason"])
        meta["protocols"][cond]={"input_pairs":len(pairs),"retained_pairs":len(clean),"removed_pairs":len(removed),
                                "genuine":sum(int(r["label"]) for r in clean),"kind":"post-hoc unique-probe sensitivity; not a clean-trained model"}
    pairs=read(root/"manifests/mfr2_official_complete_pairs.csv")
    trained={normalize(r["identity"]) for r in train if r["split"]=="train"}
    clean=[];removed=[]
    for r in pairs:
        bad=normalize(r["identity1"]) in trained or normalize(r["identity2"]) in trained
        (removed if bad else clean).append({**r,"exclusion_reason":"known_training_identity_name_overlap"} if bad else r)
    write(out/"mfr2_official_complete_pairs.csv",clean)
    write(out/"mfr2_excluded_overlap_pairs.csv",removed)
    meta["protocols"]["mfr2"]={"input_pairs":len(pairs),"retained_pairs":len(clean),"removed_pairs":len(removed),
                             "genuine":sum(int(r["label"]) for r in clean),"kind":"known-name-overlap-excluded sensitivity; no claim that all aliases are resolved"}
    pairs=read(root/"manifests/rmfrd_pairs.csv");identities=defaultdict(set)
    for r in pairs:
        for role in ["probe","enroll"]:
            for kind in ["face","peri"]:identities[r[f"{role}_{kind}_path"]].add(r[f"{role}_identity"])
    by_hash=defaultdict(list);content=[]
    for rel,ids in sorted(identities.items()):
        p=data/rel
        if not p.is_file():raise FileNotFoundError(p)
        h=digest(p);by_hash[h].append(rel);content.append({"path":rel,"sha256":h,"identities":"|".join(sorted(ids))})
    conflicts=[ps for ps in by_hash.values() if len(set().union(*(identities[p] for p in ps)))>1]
    flagged={p for ps in conflicts for p in ps};clean=[];removed=[]
    for r in pairs:
        bad=any(r[f"{role}_{kind}_path"] in flagged for role in ["probe","enroll"] for kind in ["face","peri"])
        (removed if bad else clean).append({**r,"exclusion_reason":"cross_identity_exact_content_conflict"} if bad else r)
    write(out/"rmfrd_pairs.csv",clean);write(out/"rmfrd_excluded_pairs.csv",removed)
    write(out/"rmfrd_content_hashes.csv",content)
    meta["protocols"]["rmfrd"]={"input_pairs":len(pairs),"retained_pairs":len(clean),"removed_pairs":len(removed),
                              "genuine":sum(int(r["label"]) for r in clean),"duplicate_groups":len(conflicts),
                              "kind":"known exact-conflict exclusion sensitivity; other label/perceptual issues remain"}
    for name in ["rof_manifest.csv","crop_manifest_training_person_disjoint.csv","mfr2_official_complete_pairs.csv","rmfrd_pairs.csv"]:
        meta["inputs"][name]=digest(root/"manifests"/name)
    meta["output_hashes"]={p.name:digest(p) for p in sorted(out.glob("*.csv"))}
    (out/"protocol_metadata.json").write_text(json.dumps(meta,indent=2),encoding="utf-8")
    print(json.dumps(meta,indent=2))
if __name__=="__main__":main()

