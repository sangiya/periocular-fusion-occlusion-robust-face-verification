"""Verify the thesis draft's measured tables and bind its compiled output."""
from pathlib import Path
import hashlib,json,re
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parent.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    folder=ROOT/'document/thesis';source=folder/'Research_Thesis_Draft.tex';pdf=source.with_suffix('.pdf')
    text=source.read_text(encoding='utf-8');paper=ROOT/'submission_ieee_10page/IEEE_TBIOM_Submission_10Page_Final.tex'
    journal=paper.read_text(encoding='utf-8');record=json.loads((folder/'THESIS_SOURCE_RECORD.json').read_text())
    assert record['journal_source_sha256']==sha(paper) and record['thesis_source_sha256']==sha(source)
    assert record['summary_sha256']==sha(ROOT/'results/cpu_clean/RESULTS_SUMMARY.json')
    assert record['method_diagram_sha256']==sha(folder/'fig_gated_architecture.pdf')
    labels=['rofmasked','rofsunglasses','rofneutral','mfr2','rmfrd','calibration','gatecontrols','gatedistribution','sface','paired']
    for label in labels:
        marker='\\label{tab:'+label+'}'
        assert text.split(marker)[1].split('\\end{table}')[0]==journal.split(marker)[1].split('\\end{table}')[0],label
    assert set(re.findall(r'\\bibitem\{([^}]+)\}',text))==set(re.findall(r'\\bibitem\{([^}]+)\}',journal))
    block=text.split('\\label{tab:thesisregister}')[1].split('\\end{table}')[0]
    rows=[x for x in block.splitlines() if len(re.findall(r'\b0\.\d{6}\b',x))==2]
    summary=json.loads((ROOT/'results/cpu_clean/RESULTS_SUMMARY.json').read_text())['summary']
    assert len(rows)==len(summary)==25
    for row,value in zip(rows,summary):
        mean,sd=map(float,re.findall(r'\b0\.\d{6}\b',row))
        assert abs(mean-value['auc_mean'])<=.00000050001 and abs(sd-value['auc_seed_sd'])<=.00000050001
    log=source.with_suffix('.log').read_text(encoding='utf-8',errors='replace')
    assert 'Overfull' not in log and 'Missing character' not in log
    assert not re.search(r'(Citation|Reference).{0,150}undefined|There were undefined',log,re.I)
    reader=PdfReader(pdf);texts=[p.extract_text() or '' for p in reader.pages]
    assert all(x.strip() for x in texts),'Blank thesis page'
    assert len(reader.pages)>=30
    assert 'Research Thesis Draft' in texts[0]
    assert 'Math' in '\n'.join(texts) and 'Experiment Register' in '\n'.join(texts)
    record.update({'pdf_sha256':sha(pdf),'pages':len(reader.pages),'overfull_boxes':0,'missing_characters':0,
        'undefined_references_or_citations':False,'verified_measured_table_blocks':len(labels),'verified_register_rows':25,
        'references':len(re.findall(r'\\bibitem\{([^}]+)\}',journal)),'compiler':'Tectonic 0.17.0; cached report class and fonts',
        'layout':'A4, 12-point Times, 1.25 line spacing; generic draft, not an institutional template',
        'scope':'Shared measurement tables, register arithmetic, provenance bindings, PDF structure and compilation; no institution or publication approval.'})
    (folder/'THESIS_SOURCE_RECORD.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'thesis_pages':len(reader.pages),'measured_tables_checked':10,'register_rows_checked':25,'overfull_boxes':0},indent=2))
if __name__=='__main__':main()
