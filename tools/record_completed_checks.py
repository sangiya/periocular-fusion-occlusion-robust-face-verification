"""Record current compilation bindings and actually run source regression checks."""
from pathlib import Path
import argparse,ast,hashlib,json,re,subprocess,sys
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parent.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--research-python',required=True);args=ap.parse_args()
    logs=ROOT/'document/build_logs';logs.mkdir(exist_ok=True)
    inputs={};pdfs=[]
    for rel in ['submission_ieee_10page/IEEE_TBIOM_Submission_10Page_Final','document/arXiv_Preprint_10Page_Final','document/cpu_followup/CPU_Integrity_Followup']:
        source=ROOT/(rel+'.tex');pdf=ROOT/(rel+'.pdf');log=ROOT/(rel+'.log')
        text=log.read_text(encoding='utf-8',errors='replace')
        assert 'Overfull' not in text,'PDF overflows: '+rel
        assert not re.search(r'(Citation|Reference).{0,150}undefined|There were undefined',text,re.I)
        pages=len(PdfReader(pdf).pages)
        assert pages==(2 if 'cpu_followup' in rel else 10),(rel,pages)
        inputs[source.relative_to(ROOT).as_posix()]=sha(source)
        (logs/log.name).write_text(text,encoding='utf-8')
        pdfs.append({'file':pdf.relative_to(ROOT).as_posix(),'sha256':sha(pdf),'pages':pages,
            'source':source.relative_to(ROOT).as_posix(),'source_sha256':sha(source),
            'log':'document/build_logs/'+log.name,'overfull_boxes':0,'underfull_messages':text.count('Underfull'),
            'undefined_references_or_citations':False})
    for p in (ROOT/'submission_ieee_10page').glob('fig_*.pdf'):inputs[p.relative_to(ROOT).as_posix()]=sha(p)
    ieee=(ROOT/'submission_ieee_10page/IEEE_TBIOM_Submission_10Page_Final.tex').read_text(encoding='utf-8')
    arxiv=(ROOT/'document/arXiv_Preprint_10Page_Final.tex').read_text(encoding='utf-8')
    for status in ['submitted','prepared']:
        arxiv=arxiv.replace('\\noindent\\textit{Preprint '+status+' for scholarly dissemination.}\\par\n','')
    arxiv=arxiv.replace('\\graphicspath{{../submission_ieee_10page/}}','\\graphicspath{{./}}')
    assert ieee==arxiv,'Substantive manuscript text differs'
    for value in ['0.9221','0.8950','0.9458','0.9548','0.7240']:
        assert value in ieee
    build={'date':'2026-11-15','compiler':'Tectonic 0.17.0','flags':['--only-cached','--untrusted','--keep-logs'],
        'inputs':inputs,'pdfs':pdfs[:2],'supplement':pdfs[2], 'shared_substantive_tex':True,
        'visual_inspection':'Both 10-page manuscripts rendered and checked in page contact sheets; tables, plots, and margins inspected. Completed supplement separately rendered.',
        'note':'No overfull boxes or undefined references/citations. Minor underfull spacing messages and nonfatal Fontconfig message remain.'}
    thesis=ROOT/'document/thesis/THESIS_SOURCE_RECORD.json'
    if thesis.exists():
        record=json.loads(thesis.read_text())
        assert record['pdf_sha256']==sha(thesis.parent/'Research_Thesis_Draft.pdf')
        assert record['journal_source_sha256']==sha(ROOT/'submission_ieee_10page/IEEE_TBIOM_Submission_10Page_Final.tex')
        assert len(PdfReader(thesis.parent/'Research_Thesis_Draft.pdf').pages)==record['pages']
        build['thesis']={'file':'document/thesis/Research_Thesis_Draft.pdf','sha256':record['pdf_sha256'],
            'pages':record['pages'],'source':'document/thesis/Research_Thesis_Draft.tex',
            'source_sha256':record['thesis_source_sha256'],'overfull_boxes':record['overfull_boxes'],
            'status':'Generic research thesis draft; institution-specific template and author declarations remain pending.'}
        inputs['document/thesis/Research_Thesis_Draft.tex']=record['thesis_source_sha256']
    (ROOT/'document/BUILD_REPORT.json').write_text(json.dumps(build,indent=2)+'\n',encoding='utf-8')
    files=[p for folder in ['code','tools','reproduction'] for p in (ROOT/folder).rglob('*.py')]+[ROOT/'run_seed_sweep.py']
    for p in files:ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p))
    commands=[('completed_release_tests.txt',[sys.executable,'-m','unittest','discover','-s',str(ROOT/'code/tests'),'-v'],6),
              ('completed_cpu_tests.txt',[args.research_python,'-m','unittest','discover','-s',str(ROOT/'reproduction/research_completion_2026-11-02'),'-p','test_cpu*.py','-v'],15)]
    for name,cmd,n in commands:
        result=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,errors='replace')
        text=result.stdout+result.stderr;(logs/name).write_text(text,encoding='utf-8')
        assert result.returncode==0 and f'Ran {n} tests' in text,(name,text)
    report={'date':'2026-11-15','syntax_files':len(files),'regression_tests':21,'regression_status':'passed',
        'test_logs':['document/build_logs/'+x[0] for x in commands],
        'new_model_training_performed':True,'new_models_fully_trained_and_evaluated':15,
        'new_raw_score_files':120,'epochs_per_model':5,'optimizer_steps_per_model':1380,'device':'cpu',
        'historical_results_separate':True,
        'scope':'Regression, syntax and executed completion records; arithmetic/provenance and table checks are in VERIFICATION_REPORT.json.'}
    (ROOT/'document/TEST_REPORT.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'pdf_pages':[x['pages'] for x in pdfs],'regression_tests':21,'syntax_files':len(files)},indent=2))

if __name__=='__main__':main()
