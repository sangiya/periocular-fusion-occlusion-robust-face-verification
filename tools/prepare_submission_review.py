"""Apply checked citation additions and prepare factual, unsubmitted author materials."""
from pathlib import Path
import json,re,shutil

ROOT=Path(__file__).resolve().parent.parent
def put(path,text):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text.rstrip()+'\n',encoding='utf-8')

def main():
    ieee=ROOT/'submission_ieee_10page/IEEE_TBIOM_Submission_10Page_Final.tex'
    preprint=ROOT/'document/arXiv_Preprint_10Page_Final.tex'
    backup=ROOT/'document/history/completed_cpu_before_submission_review'
    if not backup.exists():
        backup.mkdir(parents=True)
        for p in [ieee,preprint,ieee.with_suffix('.pdf'),preprint.with_suffix('.pdf')]:shutil.copy2(p,backup/p.name)
    tex=ieee.read_text(encoding='utf-8')
    tex=tex.replace('demonstrated feasibility in the visible spectrum, showing rank-one accuracy of 87.3\\% on FRGC v2.0 and confirming that the periocular region carries much of the identity signal',
        'studied visible-spectrum periocular matching, including eyebrow cues, face--periocular fusion, and partially occluded face images')
    if '\\cite{ocularcrop2025}' not in tex:
        anchor=r'\subsection{Self-supervised visual representations}'
        tex=tex.replace(anchor,'More recent work by Alonso-Fernandez \\textit{et al.} trains periocular networks from ocular crops of large face datasets and evaluates both face-derived and dedicated periocular protocols \\cite{ocularcrop2025}. This reinforces the need to distinguish training-data scale, crop construction, and acquisition protocol when comparing whole-face and periocular performance. Its reported results are not directly comparable to our frozen ROF pairs.\n\n'+anchor)
    tex=tex.replace('OpenCV SFace (December 2021 weights) using YuNet (March 2023)',
                    r'OpenCV SFace \cite{sface} (December 2021 weights) using YuNet \cite{yunet} (March 2023)')
    tex=tex.replace('prose in the Abstract, Introduction, Methods, Results, Discussion, and reproducibility documentation',
        'prose in the Abstract, Introduction, Related Work, Research Questions, Methods, Datasets and Protocol, Experimental Settings, Results, Discussion, Limitations, Conclusion, and reproducibility documentation')
    refs=[('sface',r'''\bibitem{sface} Y. Zhong, W. Deng, J. Hu, D. Zhao, X. Li, and D. Wen, ``SFace: Sigmoid-constrained hypersphere loss for robust face recognition,'' \textit{IEEE Trans. Image Process.}, vol. 30, pp. 2587--2598, 2021, doi: 10.1109/TIP.2020.3048632.'''),
          ('yunet',r'''\bibitem{yunet} W. Wu, H. Peng, and S. Yu, ``YuNet: A tiny millisecond-level face detector,'' \textit{Machine Intelligence Research}, vol. 20, no. 5, pp. 656--665, 2023, doi: 10.1007/s11633-023-1423-y.'''),
          ('ocularcrop2025',r'''\bibitem{ocularcrop2025} F. Alonso-Fernandez, K. Hernandez-Diaz, J. M. Buades Rubio, and J. Bigun, ``Leveraging large-scale face datasets for deep periocular recognition via ocular cropping,'' arXiv:2510.26294, 2025. [Online]. Available: \url{https://arxiv.org/abs/2510.26294}''')]
    for key,item in refs:
        if '\\bibitem{'+key+'}' not in tex:tex=tex.replace(r'\end{thebibliography}',item+'\n'+r'\end{thebibliography}')
    put(ieee,tex)
    arxiv=tex.replace(r'\graphicspath{{./}}',r'\graphicspath{{../submission_ieee_10page/}}')
    arxiv=arxiv.replace(r'\maketitle',r'\maketitle'+'\n'+r'\noindent\textit{Preprint prepared for scholarly dissemination.}\par')
    put(preprint,arxiv)
    folder=ROOT/'document/submission_preparation';folder.mkdir(exist_ok=True)
    title=re.search(r'\\title\{([^}]+)\}',tex)[1]
    abstract=tex.split(r'\begin{abstract}')[1].split(r'\end{abstract}')[0].strip()
    abstract=re.sub(r'\$\\pm\$', ' +/- ',abstract)
    abstract=abstract.replace(r'\pm','+/-').replace('$','')
    keywords=tex.split(r'\begin{IEEEkeywords}')[1].split(r'\end{IEEEkeywords}')[0].strip()
    metadata={'title':title,'author':'Pararajasingham Sangiya','affiliation':'Independent Researcher',
        'orcid':'0009-0005-3407-2154','target':'IEEE Transactions on Biometrics, Behavior, and Identity Science',
        'article_type':'Regular paper','abstract':abstract,'keywords':keywords,
        'prior_submission_status':'Author stated on 2026-11-15 that this work has not been submitted anywhere.',
        'submission_performed':False,'ethics_review_and_consent':'Awaiting direct confirmation of whether a committee reviewed the project; no approval, exemption, consent, or legal clearance inferred.',
        'dataset_acquisition_author_statement':'Author reports downloading all datasets from online sources described as ethical; this is not evidence of IRB approval or individual consent.',
        'prior_public_thesis_or_preprint':'Not established; disclose any such version at submission.',
        'corresponding_author_email':'Not provided','license_and_access_choices':'Author selection at submission',
        'ai_assistance':'Disclosed in manuscript Acknowledgments; ChatGPT, named sections and implementation/checking assistance.'}
    put(folder/'SUBMISSION_METADATA.json',json.dumps(metadata,indent=2,ensure_ascii=False))
    put(folder/'COVER_LETTER_DRAFT.md',f'''# Cover letter draft - not submitted

Dear Editor,

Please consider "{title}" as a regular paper for IEEE Transactions on Biometrics, Behavior, and Identity Science.

The paper presents a controlled study of frozen and LoRA-adapted whole-face/periocular representations, fixed fusion, and embedding-conditioned learned fusion. Fifteen models were trained on CPU using three seeds and a manifest that excludes known content conflicts. Results include validation-calibrated acceptance counts, two-endpoint identity-resampling sensitivities, and same-branch gate controls. The conclusions are condition-dependent, and the paper explicitly reports negative gate findings and a stronger unmatched face-recognition diagnostic.

The accompanying artifact contains frozen protocols, raw scores, executed source snapshots, and provenance. Dataset images and model/checkpoint binaries are excluded. Exact known MFR2 training-name overlap and RMFRD cross-label content conflicts are removed; remaining semantic labels, unknown identity aliases and pretraining overlap are disclosed as limitations.

The author has confirmed that this manuscript has not been submitted elsewhere. AI assistance is disclosed in the manuscript acknowledgments.

[AUTHOR TO COMPLETE: ethics-review/consent statement and factual reason if no review was conducted.]

[AUTHOR TO COMPLETE: disclose any earlier public thesis/preprint version, or confirm none.]

[AUTHOR TO COMPLETE: corresponding-author email and any funding/competing-interest declarations.]

Sincerely,
Pararajasingham Sangiya
Independent Researcher
ORCID: 0009-0005-3407-2154

Preparation note: this draft is not an editor-facing assertion of sufficient novelty or acceptance readiness. Complete the factual declarations and assess the novelty concern in SCIENTIFIC_READINESS_REVIEW.md before use.
''')
    put(folder/'SCIENTIFIC_READINESS_REVIEW.md','''# Scientific and submission review - 15 November 2026

Assessment: the specified CPU experiment is complete and numerically consistent, but this review does not recommend treating the manuscript as fully cleared for T-BIOM submission. Two substantive issues remain: a compelling novel improvement over related work has not been established, and the author has not yet supplied the ethics-review/consent facts needed for a complete declaration.

The [T-BIOM author instructions](https://ieee-biometrics.org/publications/t-biom/author-instructions/) describe a novelty requirement, allow regular papers up to ten pages, and require supplements separately. The current 10-page paper plus separate two-page supplement fit those length/packaging provisions. My inference from the stated novelty criterion is that a combination of existing DINOv2, LoRA and periocular fusion faces substantial editorial risk unless the experimental/integrity contribution is made persuasive. Numerical consistency alone does not resolve that risk.

The learned gate leads only neutral and retained MFR2 mean AUC. Constant or permuted same-branch controls are competitive on ROF. The stronger SFace diagnostic uses unmatched pretraining/alignment, so it cannot establish a controlled architecture ranking, but it also prevents a supported state-of-the-art claim for the new models. A matched modern face-specific baseline and a clear statement of the scientific insight would materially strengthen the submission. These are research limitations, not failed training jobs; no additional training is launched by this review.

Masked evaluation has nine eligible labels, 47 genuine and 376 impostor pairs. This limits generalization and low-FAR security claims. Semantic label correctness, unknown aliases, pretraining exposure, and exhaustive perceptual duplicates remain unresolved. Exact-conflict exclusions are necessary but do not certify a fully independent cohort. The manuscript now states these bounds.

The [IEEE submission policy](https://journals.ieeeauthorcenter.ieee.org/become-an-ieee-journal-author/publishing-ethics/guidelines-and-policies/submission-and-peer-review-policies/) requires appropriate human-subject ethics and consent reporting or an explanation. No approval number, exemption, or consent status is fabricated. The author confirmed no previous submission; ethics facts, correspondence details, and any earlier public version still require clarification. AI use is disclosed by system, sections and scope. The manuscript has not been submitted by this agent.

The [arXiv TeX guidance](https://info.arxiv.org/help/submit_tex.html) requires checking the server-generated PDF. The source ZIP has been compiled independently with the local cached compiler; this is not an arXiv server validation or an endorsement decision. Author account, category, endorsement where applicable, and license choices remain submission-time steps.

Targeted reference checks confirmed FBR (CVPR 2024), CKD (Neurocomputing 2024), DINOv2 (TMLR 2024), and the original SFace/YuNet sources. The SFace and YuNet references have been added where the actual baseline is described. The 2025 ocular-cropping work has been included as related work with no cross-protocol numerical comparison. The isolated Park 87.3%/FRGC claim was removed because its specific dataset/number attribution was not verified during this check. This is a targeted citation review, not a certificate that every reference entry or literature claim is fully validated.

No licensed similarity report or detector clearance has been obtained. The next concrete step is author review of contribution, image labels and declarations, followed by submission preparation using the factual metadata and cover-letter draft. No messages were sent to editors and no repository visibility was changed.
''')
    put(folder/'REFERENCE_CHECKS.json',json.dumps({'checked_on':'2026-11-15','scope':'Targeted core and newly cited references; not all bibliography entries',
        'sources':[
          {'key':'fbr2024','url':'https://openaccess.thecvf.com/content/CVPR2024/html/Tiong_Flexible_Biometrics_Recognition_Bridging_the_Multimodality_Gap_through_Attention_Alignment_CVPR_2024_paper.html','checked':'Authors, title, CVPR 2024 pages 267-276'},
          {'key':'ckd2024','url':'https://www.sciencedirect.com/science/article/abs/pii/S0925231224000341','checked':'Author list and publication identity; DOI confirmed by author-institution record'},
          {'key':'dinov2','url':'https://openreview.net/forum?id=a68SUt6zFt','checked':'TMLR 2024 paper'},
          {'key':'sface','url':'https://ieeexplore.ieee.org/document/9318547','checked':'IEEE TIP 2021 volume 30 pages 2587-2598, DOI 10.1109/TIP.2020.3048632; authors also confirmed in author preprint arXiv:2205.12010'},
          {'key':'yunet','url':'https://link.springer.com/article/10.1007/s11633-023-1423-y','checked':'Authors and 2023 volume 20 pages 656-665'},
          {'key':'ocularcrop2025','url':'https://arxiv.org/abs/2510.26294','checked':'Authors, title, 2025 preprint record'},
          {'key':'periocular','url':'https://cse.msu.edu/~rossarun/pubs/ParkPeriocularBiometrics_TIFS2011.pdf','checked':'Author-hosted abstract indexed; specific 87.3%/FRGC assertion not verified and removed'},
          {'key':'rmfrd','url':'https://doi.org/10.1109/TBIOM.2023.3242085','checked':'DOI resolved to IEEE document 10036007; publisher page blocked by robot check, so full metadata not certified in this check'}]},indent=2))
    check=ROOT/'document/FINAL_SUBMISSION_CHECKLIST.md'
    text=check.read_text(encoding='utf-8')
    if 'ethics-review/consent' not in text:
        text=text.replace('- [ ] Author approves','- [ ] Complete factual ethics-review/consent explanation; do not infer exemption from public availability.\n- [ ] Establish and approve the journal-level novelty argument; see submission_preparation/SCIENTIFIC_READINESS_REVIEW.md.\n- [ ] Author approves')
    put(check,text)
    print('Updated core citations and prepared scientific review, metadata and unsent cover-letter draft.')

if __name__=='__main__':main()
