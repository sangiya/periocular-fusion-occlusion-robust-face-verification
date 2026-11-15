# Current readiness - 16 November 2026, scientific strengthening revision

The paper is **Regional Complementarity and Learned Weighting for Occluded Face Verification: A Controlled Study**. All fifteen original models completed five CPU epochs, and their original numerical results and ten manuscript measurement tables are unchanged.

A new CPU-only SFace control uses the same 3,402 input crop files without redetection/alignment across eight frozen protocols. It exposes substantial preprocessing sensitivity; aligned SFace remains stronger by AUC. A post-hoc masked identity-deletion analysis checks all nine identity deletions and 135 per-seed subset AUCs. These controls do not match pretraining or add independent identities.

The broader literature search added three close 2025/2026 works. The paper now has 38 references and explicitly rejects first-use claims for DINOv2-LoRA face/periocular adaptation or quality-aware fusion. See [the strengthening report](SCIENTIFIC_STRENGTHENING_REPORT.md), [novelty comparison](submission_preparation/NOVELTY_COMPARISON.md), and [reference review](submission_preparation/REFERENCE_RELEVANCE_AUDIT.md).

The IEEE paper and preprint remain 10 pages; the expanded generic thesis is 55 pages. The original training requires no restart or GPU retraining for this revision. The code/raw-score release and final delivery package are regenerated from the current checked evidence.

Submission clearance remains pending factual ethics/consent and dataset permissions, author scientific approval, correspondence/submission declarations and any required licensed similarity screening. Broader independent identities, a fully controlled face-specific comparison and journal-level novelty remain scientific limitations. No AI-detector clearance, plagiarism-free certificate, state-of-the-art result or acceptance guarantee is asserted.
