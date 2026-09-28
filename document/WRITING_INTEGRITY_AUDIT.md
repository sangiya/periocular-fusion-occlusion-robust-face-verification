# Writing Integrity Audit

Record of the checks run on the manuscript prose, what they found, what was
changed, and — as importantly — what could **not** be verified with the tooling
available.

Manuscript: `IEEE_TBIOM_Submission_10Page_Final` (10 pages), with the parallel
`arXiv_Preprint_10Page_Final` and the retired 8-page `IEEE_TBIOM_PAPER`.

Date of audit: 2026-09-28.

---

## 1. Summary

| Area | Status | Tooling |
|---|---|---|
| Formulaic / templated phrasing | **Pass**, no changes needed | local scan |
| Filler and hedging words | **Pass**, 0 occurrences | local scan |
| Sentence rhythm | **Reviewed**, 3 sentences rewritten | local measurement |
| Citation integrity | **Pass**, 32/32 | local scan |
| Self-plagiarism vs. author's prior paper | **Pass**, 0 shared sequences | local n-gram |
| Similarity vs. published literature | **Not verified** | needs Turnitin / iThenticate |
| Commercial AI-detection score | **Not run, and not treated as meaningful** | see section 5 |

**Nothing in the manuscript was changed to raise a detector score.** The three
edits in section 4 were made because the sentences were genuinely hard to read,
and every number in them was re-verified afterwards against the result files.

---

## 2. Phrasing scan

Scanned roughly 5,700 words of prose for the vocabulary that machine-generated
academic text tends to overuse.

**Zero occurrences** of: `delve`, `underscore`, `pivotal`, `robustly`,
`seamless`, `realm`, `landscape`, `paradigm`, `leverage`, `harness`, `foster`,
`showcase`, `encompass`, `myriad`, `plethora`, `Furthermore`, `Moreover`,
`Additionally`, `Notably`, `Interestingly`, `In conclusion`, `It is worth
noting`, `It should be noted`, `It is important to note`, `That said`.

**Zero standalone occurrences** of `very`, `just`, `really`, `quite`,
`basically`, `actually`, `obviously`, `clearly`, `indeed`.

One use of `simply`, doing real work: *"not simply the combination of established
components"*.

---

## 3. Sentence rhythm

Measured on the manuscript with LaTeX markup removed (304 sentences of 4+ words):

| Metric | Value |
|---|---|
| Prose words | 5,743 |
| Mean sentence length | **18.9** |
| Median | 17.0 |
| Standard deviation | 8.9 |
| Range | 4 – 60 words |
| Sentences of 10 words or fewer | 49 (16.1%) |
| Sentences of 41+ words | 6 (2.0%) |

The distribution is broad, not uniform: a sixth of sentences are short, and the
spread from 4 to 60 words is wide.

---

## 4. Changes actually made

Three sentences were rewritten. In each case the problem is ordinary clarity,
and each was verified numerically afterwards.

**4.1 Conclusion — was 77 words carrying four results and a caveat**

> Before: *"However, the learned gate is not uniformly dominant: periocular LoRA
> gives the best ROF masked mean AUC (0.8989±0.008), learned gating gives the
> best ROF sunglasses mean AUC (0.8998±0.005) and neutral mean AUC
> (0.9441±0.002), fixed fusion gives the highest recorded ROF masked TAR at FAR
> 10⁻³ (0.2069±0.130), although this operating point lies below the protocol FAR
> resolution, and fixed fusion is strongest by mean AUC in the exploratory RMFRD
> v2 results (0.7184±0.011)."*
>
> After: split into four sentences — "No single variant dominates." followed by
> one sentence per variant family, with the FAR-resolution caveat attached to the
> claim it actually qualifies.

**4.2 Discussion — was 46 words with three statistics and a semicolon pivot**

> Before: *"…gives a large mean AUC gain of +0.0643±0.0156 on masked probes,
> +0.0179±0.0102 on sunglasses, and +0.0111±0.0041 on neutral, with positive
> point estimates across seeds; however, the per-seed identity-aware intervals do
> not exclude zero in every case."*
>
> After: three sentences, with the caveat promoted to its own sentence rather
> than buried after a semicolon.

**4.3 Reproducibility section — was a 42-word twelve-item list, and hedged**

> Before: *"For complete archival reproducibility, the package **should
> retain** SHA-256 values…"*
>
> After: the list is grouped ("…and the run configuration: split seed, training
> seed, LoRA rank, optimizer, learning rate, epoch count, hardware, and
> runtime"), and the claim is corrected from *should retain* to *retains*,
> because the artifact does in fact contain these files.

Item 4.3 is the only edit that changes a factual claim, and it changes it from
an aspiration to what is actually shipped. `ENVIRONMENT.md` and the per-result
`checkpoint_sha256` / `pairs_sha256` fields satisfy the corrected wording.

**Applied to:** all three `.tex` files. The 8-page condensed draft does not
contain the sentences in 4.2 and 4.3.

**Post-edit verification:** all 100 tabulated values (masked, sunglasses, MFR2,
RMFRD — mean and standard deviation) were recomputed from
`results/seed_sweep/` and re-checked against the manuscript. **Zero
discrepancies.** Both PDFs rebuilt and confirmed at exactly 10 pages.

---

## 5. On the AI-detection score

Two automated detectors were run against the extracted text. Both were
disregarded, and neither changed the manuscript.

**A free detector returned "90% AI / 3% Mixed / 97% Human"** and justified it
with sentence length, claiming the text showed "comparatively steady, formal
prose" against stated baselines of ~29.2 words for AI text and ~23.2 for human
text. That reasoning does not survive contact with the document:

| The tool's claim | Measured value |
|---|---|
| AI-typical average ≈ 29.2 words | This manuscript averages **18.9** |
| Human average ≈ 23.2 words | Still longer than this manuscript |
| "comparatively steady, uniform prose" | St dev 8.9, range 4–60 words, 16.1% of sentences ≤10 words |
| Quoted a "long-tail, multi-clause sentence" | *"All five systems use the same saved pair lists."* — 9 words, one clause |
| 90% + 3% + 97% | Sums to 190%, not a valid distribution |

The stated evidence is contradicted on every point, including the one sentence
the tool quoted.

**A second service reported "71% high plagiarism"** on the same extracted
text. That is addressed in section 6.2 and is likewise an artefact of reading a
PDF rather than the source.

**Why these tools mislead.** Detectors estimate perplexity and
sentence-length variance. Scientific prose uses dense, predictable terminology
and is edited toward uniformity, so it scores "machine-like" by construction.
Scores vary between runs, tool versions, and input chunking. A single
percentage is not evidence of authorship.

**No prose was written or altered to move either number.** Optimising against a
detector degrades clarity, and "the text was tuned to pass a detector" is a
worse position to be asked about than a 90% score.

### 5.1 A third check, at editor level

After both detector results were reported, the manuscript was scanned for
constructions a human IEEE editor would mark down regardless of any automated
tool: empty framing, throat-clearing, stock phrasing, and filler.

| Construction | Occurrences |
|---|---|
| "It is important/worth/essential to note..." | 0 |
| "In order to", "due to the fact that", "in the event that" | 0 |
| "very large/important", "a large number of", "plays an important role" | 0 |
| "basically", "essentially", "actually", "really", "quite" | 0 |
| "has been shown", "it is well known that", "as can be seen" | 0 |
| "make use of", "carries out", "the case of" | 0 |
| Sentences opening with a discourse connector | 4 of 313 (1.3%) |

A naive scan also matched "rather" 17 times. Each occurrence was read in
context and every one is contrastive technical prose — "rather than assuming
that either is uniformly reliable", "rather than a calibrated reliability
estimator" — which is precise, not filler. No change was warranted.

Nothing in the manuscript required editing for style at editor level. The three
sentence changes recorded in section 4 were the complete set.

---

## 5a. Spelling and grammar, measured on the source

The manuscript source was audited with an English dictionary (5,573 prose
words, 1,360 unique) rather than on extracted PDF text.

| Check | Result |
|---|---|
| Words not in the dictionary | 218, all technical terms, dataset names, or proper nouns |
| Words matching a misspelling signature | **0** |
| Common misspellings (teh, adn, recieve, seperate, occured) | **0** |
| Doubled words | **0** |
| Double spaces | **0** |
| Brace balance | balanced |
| Math delimiter parity | even |
| `whole face` vs `whole-face` inconsistency | 0 unhyphenated |
| `periocular` spelling variants | only `Periocular` / `periocular` |

The eight longest "unrecognised" items are legitimate: `perceptual-duplicate`,
`identity-discriminative`, `identity-independent`, `distribution-dependent`,
`verification-centered`, `independent-identity`, `rmfrd-v2`, and
`pararajasingham`. Each is correctly spelled.

The 264 corrections proposed by the online grammar checker were **not applied**.
Every one was an artefact of PDF text extraction: soft hyphens at line breaks,
spaces around rendered citation brackets, table cells concatenated without
separators, IEEE bibliography numbering, and math-mode spacing. Applying them
to the `.tex` would have inserted spaces inside `\cite{}` and corrupted the
equations.

---

## 6. Plagiarism and citation checks

### 6.1 Measured phrase overlap against the cited sources

The manuscript prose (6,106 words after stripping LaTeX, tables, figures,
equations, and the bibliography) was compared word-by-word against the
verbatim abstracts retrieved from the publishers and preprint servers during
this audit.

| Source | Longest identical word-run |
|---|---|
| LoRA, arXiv:2106.09685 | 3 words ("low rank adaptation") |
| DINOv2, arXiv:2304.07193 | 2 words |
| MaskTheFace / MFR2, arXiv:2008.11104 | 3 words ("the same person") |
| Periocular CKD, Neurocomputing 575:127263 | 3 words |
| ROF, BIOSIG 2021 | 4 words ("occlusion robust face recognition") |

**Overall longest identical run: 4 words.** Coverage of the manuscript by
shared n-grams against all five sources:

| n-gram | Shared | Coverage |
|---|---|---|
| 3 words | 7 | 0.130% |
| 4 words | 1 | 0.018% |
| 5+ words | 0 | 0.000% |

A copied sentence would show a run of 10 or more consecutive words. Four words
is ordinary technical terminology that any paper on this topic uses, and every
such instance sits in a sentence carrying the correct citation. No copying was
detected.

**Self-plagiarism — pass.** The abstract of the author's prior paper
(arXiv:2608.08521, on classical feature-based disguise and spoofing detection)
was compared against all three manuscripts. **Zero** shared 6-, 8-, or 10-word
sequences. None of that paper's subject vocabulary appears in this work —
`disguise`, `spoofing`, `NUAA`, `FEI`, `Local Binary Patterns`, `Histogram of
Oriented Gradients`, `Speeded-Up Robust Features`, `Harris`, `MED`. The two
papers share no method, dataset, or claim.

**Citation integrity — pass.**

| Check | Result |
|---|---|
| Bibitems defined | 32 |
| Unique `\cite` keys in the body | 32 |
| `\cite` with no matching bibitem | none |
| Bibitem never cited | none |
| Undefined `\ref` targets | none |
| Literature claims lacking a citation | none |

**Cross-document overlap — expected, not an issue.** The IEEE and arXiv files
are the same manuscript in two formats (99.8% shared 8-grams). The 8-page draft
shares 69% with the 10-page version. This is the same author's own work in
parallel formats, not misappropriation.

### 6.2 Why online plagiarism scores are not usable

A free checker reported "71% high plagiarism" on this manuscript. That figure
is not a similarity measurement against the scholarly corpus, for three
reasons.

1. **It was run on the PDF, not the source.** A text extractor cannot tell a
   line break from a missing space, so LaTeX's end-of-line hyphenation appears
   as broken words (`un- available`, `parameter- e fficient`). The same
   extraction concatenates table cells (`M087171072 5905920.68`) and inserts
   spaces around rendered citation brackets. 264 "corrections" were proposed on
   the basis of those artefacts. The `.tex` source contains none of them: each
   flagged word is present in its correct, unbroken form and the broken form
   does not occur anywhere.
2. **The reported categories do not form a distribution.** The same result
   reported 71% + 42% + 5% + 42%, totalling 160%.
3. **The measurement is not reproducible.** Free web tools vary between runs,
   versions, and input chunking, and none of them exposes the corpus or the
   algorithm.

A meaningful similarity percentage requires a licensed service
(iThenticate or Turnitin) run through institutional access, which parses PDFs
correctly and reports a defensible number. That check has not been performed
and no percentage is claimed here. The measurements in 6.1 bound the realistic
exposure: the only sentences that could match anything are the Related Work
restatements, and they are short, cited, and share at most four consecutive
words with their sources.

---

## 7. Disclosure

IEEE policy requires authors to **disclose AI assistance in the writing
process**. That is an obligation to declare, not a threshold to clear, and no
detector result changes it. Whatever assistance was used, the disclosure
statement in the submission's cover material should say so.

---

## 8. How to reproduce this audit

From the bundle root:

```powershell
# headline numbers still match the manuscript
python .\code\verify_results.py

# manifest paths are portable
python .\code\remap_manifest_paths.py --root . --dry-run
```

The prose analyses in sections 2, 3 and 6 were run with local scripts over the
`.tex` sources. They are reported here as measurements, with the method stated,
so a reader can disagree with the judgement and re-run the measurement.
