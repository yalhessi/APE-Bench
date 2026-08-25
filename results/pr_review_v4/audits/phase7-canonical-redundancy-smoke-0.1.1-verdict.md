# Phase 7 canonical redundancy smoke verdict

## Verdict

Pass. Two independent live adjudications of the frozen canonical-API opportunity both requested the
same source-level transformation and supplied edits that Lean successfully recompiled. Selective
redundancy resolved to agreement with final worthiness `request`.

## Run integrity

- `rep1b` and `rep2` are fresh, distinct APE runs with separate attempt directories, response hashes,
  generated edits, and charged model calls.
- `rep1b` completed from attempt `attempt_1_20260717114650`; reported cost was $0.24353875.
- `rep2` completed from attempt `attempt_1_20260717114512`; reported cost was $0.21917875.
- Both terminal responses succeeded with one adjudication, one candidate, and one successful Lean
  verification artifact.

## Ingestion

The first artifact implementation briefly aliased the adjudication evidence list. Consequently,
`rep2` serialized its verification artifact ID into that artifact's own source list after its digest
had been computed. Ingestion repairs this exact legacy form only when removing the self-reference
reproduces both the stored SHA and content-addressed artifact ID. One artifact was repaired this way;
`rep1b` required no repair.

The final report records:

- requests: 1;
- votes: 2;
- verification artifacts: 2;
- repaired legacy aliases: 1;
- consensuses: 1;
- outcome: `agreement`, final worthiness `request`.

Artifacts are under
`results/pr_review_v4/runs/phase7-canonical-redundancy-smoke-0.1.1/`.
