"""Verify final manuscript tables, paired venue sources and upload dependencies.

Uses only Python's standard library. PDF page counts come from a checked build
record and remain bound to the compiled bytes; this is not portal validation.
"""
from pathlib import Path
import json,re,statistics,zipfile
from verify_results import SEEDS,VARIANTS,KEYS,digest,recorded_relative_path

def blocks(tex):
    return re.findall(r'\\begin\{table\}.*?\\end\{table\}',tex,re.S)

def table_rows(tex,label):
    matches=[b for b in blocks(tex) if '\\label{tab:'+label+'}' in b]
    assert len(matches)==1,('table missing/duplicated',label)
    return [line for line in matches[0].splitlines() if ' & ' in line and not line.startswith(('Protocol','Configuration','Config &','ID &'))]

def displayed(actual,text,context):
    places=len(text.partition('.')[2]);assert abs(float(text)-actual)<=.5*10**(-places)+1e-11,(context,text,actual)

def verify_documents(root):
    ieee=root/'submission_ieee';arxiv=root/'submission_arxiv'
    main=(ieee/'main.tex').read_text(encoding='utf-8');supp=(ieee/'supplement.tex').read_text(encoding='utf-8')
    pre=(arxiv/'main.tex').read_text(encoding='utf-8');body=(arxiv/'supplement_body.tex').read_text(encoding='utf-8')
    assert main.split(r'\begin{abstract}',1)[1].rsplit(r'\end{document}',1)[0]==pre.split(r'\begin{abstract}',1)[1].split(r'\input{supplement_body.tex}',1)[0].rstrip()+'\n'
    assert blocks(main)==blocks(pre) and blocks(supp)==blocks(body)
    assert len(blocks(main))==10 and len(blocks(supp))==3
    assert r'\mbox{occluded verification}' in main and '95\\% identity-resampling sensitivity interval' in main
    assert 'no known exact-name overlap remains' in main and 'RMFRD is exploratory' in main
    assert 'Aligned SFace diagnostic' in main and 'Shared-crop SFace preprocessing control' in main
    assert 'post-hoc exploratory cohort-composition sensitivity analysis' in main
    assert 'ethics approval or exemption' in main and 'Data provenance and ethics records' in supp
    keys=re.findall(r'\\bibitem\{([^}]+)\}',main);seen=[]
    assert len(keys)==len(set(keys))==38
    for group in re.findall(r'\\cite\{([^}]+)\}',main):
        for key in group.split(','):
            assert key in keys
            if key not in seen:seen.append(key)
    assert seen==keys
    assert main.split(r'\begin{thebibliography}',1)[1].split(r'\end{thebibliography}',1)[0]==pre.split(r'\begin{thebibliography}',1)[1].split(r'\end{thebibliography}',1)[0]
    reports={(seed,v):json.loads((root/f'results/cpu_clean/evaluation/seed{seed}_{v}/EVALUATION_REPORT.json').read_text()) for seed in SEEDS for v in VARIANTS}
    cells=0
    for num,condition in zip(range(3,8),['test_masked','test_sunglasses','test_neutral','mfr2','rmfrd']):
        rows=table_rows(main,'checked'+str(num));assert len(rows)==5
        for row,v in zip(rows,VARIANTS):
            values=row.split(' & ')[1:];assert len(values)==4
            for field,cell in zip(KEYS,values):
                mean,sd=re.findall(r'\d+\.\d+',cell);nums=[reports[seed,v]['protocols'][condition]['metrics'][field] for seed in SEEDS]
                displayed(statistics.mean(nums),mean,(num,v,field,'mean'));displayed(statistics.stdev(nums),sd,(num,v,field,'SD'));cells+=2
    assert cells==200
    params=table_rows(supp,'checked2');assert len(params)==5
    for row,(total,trainable) in zip(params,[(87171072,590592),(87613440,1032960),(175226880,2065920),(175226880,2065920),(175424257,2263297)]):
        a,b,c=[s.strip().rstrip('\\') for s in row.split(' & ')[1:]];assert (int(a),int(b))==(total,trainable);displayed(100*trainable/total,c,'parameter fraction')
    for row,c in zip(table_rows(supp,'checked10'),['test_masked','test_sunglasses','test_neutral','mfr2','rmfrd']):
        for cell,seed in zip(row.split(' & ')[1:],SEEDS):
            mean,sd=re.findall(r'\d+\.\d+',cell);dist=reports[seed,'gated_fusion']['gate_controls'][c]['gate_distribution'];displayed(dist['mean'],mean,'gate mean');displayed(dist['sd'],sd,'gate SD')
    aligned=json.loads((root/'results/sface/BASELINE_REPORT.json').read_text());shared=json.loads((root/'results/shared_crop_sface/REPORT.json').read_text())
    rows=table_rows(supp,'sfaceshared');assert len(rows)==5
    for row,c in zip(rows,['test_masked','test_sunglasses','test_neutral','mfr2','rmfrd']):
        a,b,s,f=[v.strip().rstrip('\\') for v in row.split(' & ')[1:]]
        displayed(aligned['protocols'][c]['all_pairs_metrics']['auc'],a,'aligned SFace');assert int(b)==aligned['protocols'][c]['failed_pairs']
        displayed(shared['protocols'][c]['metrics']['auc'],s,'shared SFace');assert int(f)==shared['protocols'][c]['failed_pairs']
    for folder,texts,expected in [(ieee,main+supp,{'main.tex','supplement.tex'}),(arxiv,pre+body,{'main.tex','supplement_body.tex'})]:
        figures=set(re.findall(r'\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}',texts));assert len(figures)==6
        for name in figures:
            assert Path(name).name==name and (folder/name).is_file()
            assert digest(ieee/name)==digest(arxiv/name)
        archive=folder/('IEEE_TBIOM_Source.zip' if folder==ieee else 'arXiv_Source.zip')
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None and set(z.namelist())==expected|figures
            for name in z.namelist():assert z.read(name)==(folder/name).read_bytes()
        meta=json.loads((folder/'SUBMISSION_METADATA.json').read_text(encoding='utf-8'));assert meta['corresponding_author_email']=='asan935para@gmail.com'
    build=json.loads((root/'document/BUILD_REPORT.json').read_text())
    for name,value in build['inputs'].items():assert digest(root/recorded_relative_path(name))==value,('build input changed',name)
    expected={'submission_ieee/IEEE_TBIOM_Paper.pdf':10,'submission_ieee/IEEE_TBIOM_Supplement.pdf':3,'submission_arxiv/arXiv_Preprint.pdf':13}
    assert {r['file']:r['pages'] for r in build['pdfs']}==expected
    for item in build['pdfs']:assert digest(root/recorded_relative_path(item['file']))==item['sha256']
    assert all(not item['overfull_boxes'] and not item['missing_characters'] and not item['undefined_citations_or_references'] for item in build['pdfs'])
    return {'main_tables':10,'supplement_tables':3,'headline_mean_SD_cells':cells,'references':38,'venue_source_alignment':True,'source_archives':2,'compiled_PDF_bindings':3,'supplement_SFace_AUC_cells':10}
