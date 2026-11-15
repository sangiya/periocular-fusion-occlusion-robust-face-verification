"""Record an editorial assessment of every cited reference and check its linkage.

The curated judgments below are based on publisher/author abstracts and accessible
papers. The mechanical checks establish coverage/order, not scientific truth.
"""
from pathlib import Path
from collections import Counter
import hashlib,json,re

ROOT=Path(__file__).resolve().parent.parent
# key: role, relevance, reason, citation disposition
ASSESSMENTS={
 'froundation2025':('Closest prior work','direct','Already adapts DINOv2 and CLIP to face recognition using LoRA.','Added after broader currency search; essential boundary on claims of novel backbone adaptation.'),
 'foundationcomparison2025':('Closest prior work','direct','Studies generic versus face-specific models, crop context and fusion.','Added to explain preprocessing and pretraining confounds; no cross-protocol performance claim.'),
 'perilora2026':('Closest prior work','direct','Combines LoRA DINOv2 periocular features with quality-aware enrollment-template fusion in cross-spectral recognition.','Added from the publisher abstract; distinguish its template/spectral setting from our visible-occlusion branch-weight controls. Full text not independently reviewed.'),
 'dinov2':('Executed component','direct','Backbone actually used; transferable self-supervised visual features.','Retain; also cited at introduction of the experimental system.'),
 'lora':('Executed component','direct','Low-rank adaptation mechanism actually used, despite its original language-model experiments.','Retain; explicitly distinguish original language-model work from our visual adaptation.'),
 'rof':('Dataset','direct','Source study of the ROF masks/sunglasses data used for training and evaluation.','Retain; reconstructed local protocol is distinguished from the original benchmark.'),
 'mfr2':('Dataset','direct','Introduces MaskTheFace and MFR2, an external evaluation dataset in this study.','Retain; our retained pair protocol differs from the original protocol.'),
 'rmfrd':('Dataset','direct','Original dataset family and maintainer-requested journal citation for RMFRD.','Retain; does not validate the local labels or our derived pair list.'),
 'sface':('Executed diagnostic','direct','Face-recognition method underlying the actual OpenCV SFace diagnostic.','Retain; paper and checkpoint implementation details serve different provenance roles.'),
 'yunet':('Executed diagnostic','direct','Face detector used in the SFace preprocessing pipeline.','Retain as an implementation-source citation; not a verification competitor.'),
 'periocular':('Closest prior work','direct','Studies periocular matching, eyebrow cues, face/periocular fusion and partial occlusion.','Retain; removed the uncited BTAS-2009 aside rather than conflating two publications.'),
 'fbr2024':('Closest prior work','direct','Face/periocular fusion, transformer attention, prompt tuning and cross-modality matching.','Retain; essential novelty comparator, not reproduced experimentally here.'),
 'ckd2024':('Closest prior work','direct','Transfers face identity information into periocular embeddings through distillation.','Retain; does not imply that this manuscript implements CKD.'),
 'ocularcrop2025':('Closest prior work','direct','Trains periocular recognition from crops of large face datasets; acquisition/crop protocol matters.','Retain the identified arXiv version; no cross-protocol numerical ranking.'),
 'from2022':('Occlusion recognition','direct','Learns masks to suppress corrupted facial features under occlusion.','Retain as related recognition work, not a reproduced baseline.'),
 'masklearn':('Occlusion recognition','direct','Pairwise differential Siamese mask learning discards occlusion-corrupted features.','Retain as a distinct earlier occlusion strategy.'),
 'umr':('Occlusion recognition','direct','Embedding unmasking with a self-restrained triplet objective for masked-face recognition.','Retain corrected final journal title/DOI from the preceding audit.'),
 'focusface':('Occlusion recognition','direct','Multi-task contrastive learning for masked/unmasked face verification.','Retain; related objective and task, not our training loss.'),
 'beyondmasks':('Occlusion recognition','direct','Examines transfer between masked-face and broader occluded-face recognition.','Retain; directly relevant to cross-condition generalization.'),
 'hsu2022':('Occlusion recognition','direct','Studies synthetic-mask training and evaluation on real masked faces.','Retain; replaced vague synthesis-to-reality wording with the specific supported claim.'),
 'mfr2021':('Masked benchmark','direct','Competition evaluates recognition under real masks.','Retain for evaluation context; no score comparison across unmatched protocols.'),
 'insightfacemfr':('Masked benchmark','direct','Documents a large-scale masked-face recognition challenge.','Retain for evaluation context; challenge identities/protocol are not our test cohort.'),
 'surveyocc':('Occlusion survey','direct','Organizes methods for face recognition under occlusion.','Retain as a 2021 publication; removed the unsupported claim of exhaustive coverage through 2021.'),
 'fusionRossJain':('Fusion foundations','direct','Studies biometric matching-score fusion.','Retain the narrower matching-score attribution; our implemented fusion combines embeddings.'),
 'quality':('Fusion foundations','direct','Reviews biometric sample utility and quality-dependent processing/fusion.','Retain; Tables II/III and Section VII support the qualified statement, not measured quality-awareness of our gate.'),
 'sphereface':('Face-embedding background','context','Multiplicative angular-margin face-recognition loss.','Retain as background; replace priority claim with its specific mechanism.'),
 'cosface':('Face-embedding background','context','Additive cosine-margin face-recognition loss.','Retain as background; not used as a loss or baseline here.'),
 'arcface':('Face-embedding background','context','Additive angular-margin face-recognition loss.','Retain as background; not a matched experimental baseline here.'),
 'magface':('Face-embedding background','context','Magnitude-aware face embeddings connect feature magnitude and image quality.','Retain with more precise magnitude-aware description; no claim that our gate estimates MagFace quality.'),
 'adaface':('Face-embedding background','context','Quality-adaptive face-recognition margin.','Retain to distinguish training-margin adaptation from inference fusion.'),
 'dino':('Visual pretraining background','context','Self-supervised vision-transformer predecessor to DINOv2.','Retain as backbone lineage, not an evaluated model.'),
 'mae':('Visual pretraining background','context','Learns visual features through masked-patch reconstruction.','Retain as a different pretraining approach, not evidence of face-occlusion performance.'),
 'simclr':('Visual pretraining background','context','Contrasts augmented image views to learn representations.','Retain; wording now states its image-based objective separately from CLIP.'),
 'clip':('Visual pretraining background','context','Learns transferable representations from paired images and natural language.','Retain as broader background; corrected natural-language supervision and stated not evaluated here.'),
 'vpt':('Adaptation alternatives','context','Learns prompts for frozen vision transformers.','Retain as a visual adaptation alternative; not tested in the ablation grid.'),
 'prompt':('Cross-field adaptation background','context','Soft-prompt tuning of frozen language models.','Least direct reference; defensible only as broader adaptation context. Explicitly marked language-model work, not face/periocular evidence.'),
 'adaptformer':('Adaptation alternatives','context','Lightweight adapters for pretrained visual transformers.','Retain as an alternative to LoRA; not implemented in this study.'),
 'llecnn':('Detection background','context','MAFA and LLE-CNNs address masked-face localization/detection.','Retain only as detection context; explicitly distinguish localization from identity verification.'),
}

def main():
    source=ROOT/'submission_ieee_10page/IEEE_TBIOM_Submission_10Page_Final.tex'
    text=source.read_text(encoding='utf-8');body=text.split(r'\begin{thebibliography}')[0]
    entries=re.findall(r'\\bibitem\{([^}]+)\}([^\n]*)',text)
    first=list(dict.fromkeys(k.strip() for group in re.findall(r'\\cite\{([^}]+)\}',body) for k in group.split(',')))
    keys=[key for key,_ in entries]
    assert len(keys)==len(set(keys))==len(ASSESSMENTS)
    assert keys==first,'IEEE bibliography must follow first citation order'
    assert set(keys)==set(ASSESSMENTS),'Assessment coverage differs from bibliography'
    refs=json.loads((ROOT/'document/submission_preparation/REFERENCE_CHECKS.json').read_text())
    evidence={row['key']:row for row in refs['sources']}
    overrides={
      'dinov2':'https://arxiv.org/abs/2304.07193', 'lora':'https://arxiv.org/abs/2106.09685',
      'ckd2024':'https://yonsei.elsevierpure.com/en/publications/periocular-embedding-learning-with-consistent-knowledge-distillat/',
      'from2022':'https://arxiv.org/abs/2108.09468', 'focusface':'https://arxiv.org/abs/2110.14940',
      'sface':'https://arxiv.org/abs/2205.12010','quality':'https://arxiv.org/pdf/2111.08704',
      'hsu2022':'https://www.researchgate.net/publication/363074637_Masked_Face_Recognition_From_Synthesis_to_Reality'}
    rows=[]
    for number,(key,entry) in enumerate(entries,1):
        role,level,reason,action=ASSESSMENTS[key]
        match=re.search(r'``(.*?)\x27\x27',entry)
        title=match.group(1).rstrip(',') if match else entry.strip()
        locations=[]
        for line_no,line in enumerate(body.splitlines(),1):
            if any(key in [k.strip() for k in group.split(',')] for group in re.findall(r'\\cite\{([^}]+)\}',line)):
                locations.append(line_no)
        rows.append({'number':number,'key':key,'title':title,'role':role,'relevance':level,
                     'reason':reason,'disposition':action,'source_url':overrides.get(key,evidence[key]['url']),
                     'citation_lines':locations})
    counts=Counter(row['relevance'] for row in rows)
    report={'date':'2026-11-16','journal_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'references_reviewed':len(rows),'counts':dict(counts),'all_references_cited':True,
            'bibliography_order_matches_first_citation':True,'references':rows,
            'scope':'Reference-by-reference topic fit and support for the short attributed claim using primary publisher/author abstracts, indexed primary-source extracts and accessible papers. Not a full systematic review or line-by-line verification of all cited full texts. Access failures and prior metadata limits remain in REFERENCE_CHECKS.json.',
            'conclusion':f"{counts['direct']} directly relevant sources and {counts['context']} contextual sources. Three closer 2025/2026 works were added after a broader currency search; the earlier 35-reference fit review did not establish literature completeness. Lester prompt tuning is the least direct and optional; relevance does not mean experimental comparability or novelty clearance."}
    folder=ROOT/'document/submission_preparation'
    (folder/'REFERENCE_RELEVANCE_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    lines=['# Citation relevance review — 16 November 2026','',report['conclusion'],'',report['scope'],'',
           f'The original numerical results and ten measured table blocks are unchanged. All {len(rows)} references are cited and ordered by first appearance. Additional CPU controls and interpretation are reported separately. The IEEE, preprint and thesis versions are synchronized.','',
           '| Ref. / key | Paper | Role | Why it belongs / disposition |','|---|---|---|---|']
    for row in rows:
        lines.append(f"| [{row['number']}] `{row['key']}` | [{row['title']}]({row['source_url']}) | {row['role']} ({row['relevance']}) | {row['reason']} {row['disposition']} |")
    lines+=['','Corrections made in this pass: distinguish CLIP language supervision from SimCLR self-supervision; identify original LoRA and Lester prompt tuning as language-model work; distinguish MAFA detection from verification; qualify margin mechanisms and the survey coverage; remove an uncited BTAS-2009 aside; qualify held-out identity language; reorder the bibliography by first citation.','',
            'The earlier Boutros title/DOI and Ross–Jain matching-score corrections remain. The Park primary-source abstract now supports the retained qualitative description; the previously removed numerical aside is unnecessary and is not restored.','',
            'The closest research comparators include FRoundation, the 2026 LoRA/periocular/template-fusion paper, the 2025 foundation-versus-domain comparison, FBR, CKD, Park et al. and ocular cropping. Their existence narrows the contribution to controlled experimental attribution, not first use of DINOv2/LoRA or periocular fusion. Citing them does not establish that this study outperforms them. No literature-wide superiority claim is implied.','']
    (folder/'REFERENCE_RELEVANCE_AUDIT.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps({'references_reviewed':len(rows),'counts':dict(counts),'first_citation_order':True},indent=2))

if __name__=='__main__':main()
