# Exact executed CPU sources

The source/runtime tree here is byte-preserved from the completed execution. Reports bind these bytes by SHA-256. Copy `research_completion_2026-11-02/` next to `publication_release/` under the dataset root to run it; see the release Windows guide. This arrangement preserves the original relative paths without editing signed source.

The completed reports/raw scores are under `results/cpu_clean/`. The reproduction tree excludes images, checkpoint binaries, embedding caches, live locks, and PIDs. Checkpoint hashes are recorded, but hashes alone do not permit inference without access to the weights.
