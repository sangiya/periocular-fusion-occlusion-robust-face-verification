"""Prepare a clearly named delivery bundle from the checked publication release."""
from pathlib import Path
import hashlib,io,json,re,zipfile
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parent.parent
DEST=ROOT.parent/'FINAL_PUBLICATION_2026-11-16'

def digest(data):return hashlib.sha256(data).hexdigest()

def archive(items):
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in sorted(items.items()):
            info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            info.create_system=3;info.external_attr=0o100644<<16
            z.writestr(info,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    return buffer.getvalue()

def main():
    build=json.loads((ROOT/'document/BUILD_REPORT.json').read_text())
    verifier=json.loads((ROOT/'document/VERIFICATION_REPORT.json').read_text())
    tests=json.loads((ROOT/'document/TEST_REPORT.json').read_text())
    citations=json.loads((ROOT/'document/submission_preparation/REFERENCE_RELEVANCE_AUDIT.json').read_text())
    assert not verifier['failures'] and tests['regression_status']=='passed'
    assert citations['references_reviewed']==len(re.findall(r'\\bibitem\{([^}]+)\}',(ROOT/'submission_ieee_10page/IEEE_TBIOM_Submission_10Page_Final.tex').read_text(encoding='utf-8'))) and citations['bibliography_order_matches_first_citation']
    records=build['pdfs']+[build['supplement'],build['thesis']]
    for record in records:
        assert digest((ROOT/record['file']).read_bytes())==record['sha256']
        assert digest((ROOT/record['source']).read_bytes())==record['source_sha256']
        assert len(PdfReader(ROOT/record['file']).pages)==record['pages']
    assert citations['journal_source_sha256']==digest((ROOT/'submission_ieee_10page/IEEE_TBIOM_Submission_10Page_Final.tex').read_bytes())
    mapping={
        'IEEE_TBIOM_Paper.pdf':'submission_ieee_10page/IEEE_TBIOM_Submission_10Page_Final.pdf',
        'IEEE_TBIOM_Supplement.pdf':'document/cpu_followup/CPU_Integrity_Followup.pdf',
        'arxiv/arXiv_Preprint.pdf':'document/arXiv_Preprint_10Page_Final.pdf',
        'arxiv/arxiv_source.zip':'arxiv_source.zip',
        'thesis/Research_Thesis_Draft.pdf':'document/thesis/Research_Thesis_Draft.pdf',
        'thesis/thesis_source.zip':'document/thesis/thesis_source.zip',
        'author_review/COVER_LETTER_DRAFT.md':'document/submission_preparation/COVER_LETTER_DRAFT.md',
        'author_review/SUBMISSION_METADATA.json':'document/submission_preparation/SUBMISSION_METADATA.json',
        'author_review/DATASET_SOURCE_TRACE.md':'document/submission_preparation/DATASET_SOURCE_TRACE.md',
        'author_review/SCIENTIFIC_READINESS_REVIEW.md':'document/submission_preparation/SCIENTIFIC_READINESS_REVIEW.md',
        'audit/COMPREHENSIVE_RECHECK.md':'document/COMPREHENSIVE_RECHECK_2026-11-16.md',
        'audit/REFERENCE_RELEVANCE_AUDIT.md':'document/submission_preparation/REFERENCE_RELEVANCE_AUDIT.md',
        'audit/REFERENCE_RELEVANCE_AUDIT.json':'document/submission_preparation/REFERENCE_RELEVANCE_AUDIT.json',
        'audit/REFERENCE_CHECKS.json':'document/submission_preparation/REFERENCE_CHECKS.json',
        'audit/VERIFICATION_REPORT.json':'document/VERIFICATION_REPORT.json',
        'audit/BUILD_REPORT.json':'document/BUILD_REPORT.json',
        'audit/TEST_REPORT.json':'document/TEST_REPORT.json',
        'audit/FIGURE_DATA_AUDIT.json':'document/FIGURE_DATA_AUDIT.json',
        'audit/PAIRED_INTERVAL_AUDIT.json':'document/PAIRED_INTERVAL_AUDIT.json',
        'audit/TEXT_INTEGRITY_RECHECK.json':'document/TEXT_INTEGRITY_RECHECK.json',
        'audit/SCIENTIFIC_STRENGTHENING_REPORT.md':'document/SCIENTIFIC_STRENGTHENING_REPORT.md',
        'audit/NOVELTY_COMPARISON.md':'document/submission_preparation/NOVELTY_COMPARISON.md',
        'audit/MASKED_IDENTITY_SENSITIVITY.json':'results/strengthening/MASKED_IDENTITY_SENSITIVITY.json',
        'audit/SHARED_CROP_SFACE_REPORT.json':'results/shared_crop_sface/REPORT.json',
    }
    items={name:(ROOT/rel).read_bytes() for name,rel in mapping.items()}
    source=ROOT/'submission_ieee_10page/IEEE_TBIOM_Submission_10Page_Final.tex'
    text=source.read_text(encoding='utf-8')
    figures=re.findall(r'\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}',text)
    assert len(figures)==len(set(figures))==5 and r'\graphicspath{{./}}' in text
    source_items={source.name:source.read_bytes()}
    for figure in figures:
        assert Path(figure).name==figure
        source_items[figure]=(source.parent/figure).read_bytes()
    items['IEEE_TBIOM_Source.zip']=archive(source_items)
    standalone=ROOT.parent/'research_completion_2026-11-02/final_ieee_source_check_2026-11-16'
    if (standalone/source.with_suffix('.pdf').name).exists():
        assert (standalone/source.name).read_bytes()==source.read_bytes()
        compiled=standalone/source.with_suffix('.pdf').name
        current=ROOT/'submission_ieee_10page'/compiled.name
        rebuilt=PdfReader(compiled);distributed=PdfReader(current)
        assert len(rebuilt.pages)==len(distributed.pages)==10
        assert [p.extract_text() for p in rebuilt.pages]==[p.extract_text() for p in distributed.pages]
        log=(standalone/source.with_suffix('.log').name).read_text(encoding='utf-8',errors='replace')
        assert 'Overfull' not in log and 'Missing character' not in log
        assert not re.search(r'(Citation|Reference).{0,150}undefined|There were undefined',log,re.I)
        check={'date':'2026-11-16','pages':10,'flat_source_files':6,
               'source_archive_sha256':digest(items['IEEE_TBIOM_Source.zip']),
               'distributed_pdf_sha256':digest(current.read_bytes()),
               'standalone_pdf_sha256':digest(compiled.read_bytes()),
               'extracted_page_text_identical':True,'overfull_boxes':0,
               'scope':'Independent compilation from the six-file source ZIP with cached Tectonic; not an IEEE submission-system check.'}
        items['audit/STANDALONE_IEEE_SOURCE_CHECK.json']=(json.dumps(check,indent=2)+'\n').encode('utf-8')
    readme='''# Final publication delivery — 16 November 2026

The journal manuscript is `IEEE_TBIOM_Paper.pdf` (10 pages). This is the latest scientifically revised version. Use this journal paper for T-BIOM; the separate __THESIS_PAGES__-page generic thesis draft is reference material, not the journal manuscript.

- `IEEE_TBIOM_Source.zip`: the matching TeX source and five vector figures (six flat files).
- `IEEE_TBIOM_Supplement.pdf`: separate two-page research supplement.
- `arxiv/`: the matching ten-page preprint and flat TeX source archive.
- `thesis/`: the __THESIS_PAGES__-page generic research thesis draft and its source archive. Institution-specific formatting remains pending.
- `audit/`: numerical, compilation, test, figure, interval and reference evidence.
- `author_review/`: factual metadata, dataset trace and an unsent cover-letter draft. These contain outstanding author declarations and are not finished editor-facing documents.

All 15 CPU models are complete. Recorded arithmetic checks and 21 regression tests pass. All __REFERENCES__ references were assessed for relevance, and the bibliography follows first citation. The original numerical tables are unchanged. New CPU controls evaluate shared-crop SFace (3,402 images/eight protocols) and masked identity deletion (nine subsets). Preprocessing is controlled only in input-file selection; pretraining, resolution and target supervision still differ. AI assistance is disclosed.

This is the final technical delivery for author review; formal submission clearance remains pending. Resolve factual ethics/consent and dataset-use permissions, approve the scientific contribution and citations, and supply correspondence and submission declarations. No licensed similarity report or AI-detector clearance is asserted. Nothing has been submitted to IEEE or arXiv.

Do not upload this entire delivery archive as the manuscript: it also contains author-review notes, the preprint and the thesis. Select the journal paper, separate supplement and source files as requested by the submission system.

The complete code/raw-score release remains in the sibling `publication_release` directory and `publication_release.zip`. This smaller delivery bundle does not duplicate datasets or model/checkpoint binaries.
'''
    readme=readme.replace('__THESIS_PAGES__',str(build['thesis']['pages'])).replace('__REFERENCES__',str(citations['references_reviewed']))
    items['READ_ME_FIRST.md']=readme.encode('utf-8')
    manifest={'date':'2026-11-16','status':'technical_delivery_complete_author_clearance_pending',
              'journal_pages':10,'preprint_pages':10,'supplement_pages':2,'thesis_pages':build['thesis']['pages'],
              'references_reviewed':citations['references_reviewed'],'regression_tests':21,
              'source_mapping':mapping,
              'files':{name:{'sha256':digest(data),'bytes':len(data)} for name,data in sorted(items.items())}}
    items['DELIVERY_MANIFEST.json']=(json.dumps(manifest,indent=2)+'\n').encode('utf-8')
    DEST.mkdir(parents=True,exist_ok=True)
    for name,data in items.items():
        path=DEST/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    data=archive(items);output=DEST.with_suffix('.zip');output.write_bytes(data)
    output.with_suffix('.zip.sha256').write_text(digest(data)+'  '+output.name+'\n',encoding='ascii')
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        assert set(z.namelist())==set(items)
        for name,content in items.items():assert z.read(name)==content==(DEST/name).read_bytes()
    print(json.dumps({'folder':str(DEST),'archive':str(output),'files':len(items),'sha256':digest(data)},indent=2))

if __name__=='__main__':main()
