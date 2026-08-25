# PR Review v4 0.8.11 temporal retrieval smoke verdict

## Verdict

Confirmed directional pass. Temporal context-to-ask retrieval produced the first strict
semantic-recall gain in this smoke sequence without increasing control pressure. The frozen semantic
judge confirmed the three-pair manual audit exactly. Do not expand to nine PRs yet: the same treatment
must replicate once under a fresh run name.

Replication update: the identical second run did not reproduce the issue hit and restored raw control
candidates. Treat this document as the first-run verdict only; the treatment-level verdict is the
failed-replication audit in `dev-pilot-0.8.11-temporal-retrieval-smoke3-rep2-verdict.md`.

This is stronger than a location-only gain. One included obligation has the same specific issue, and
one additional model request exactly recovers a maintainer naming request currently hidden from the
metric because its source intervention is pending decomposition.

## Gates

| Gate | Result | Evidence |
| --- | --- | --- |
| Execution and ingestion | Pass | 3/3 calls succeeded; four model and one deterministic candidate ingested. |
| Attribution | Pass | PR 33057 had no precedent and repeated its empty model output; no synthetic or post-cutoff content appeared. |
| Deterministic channel | Pass | Exactly one supported and selected blocking PR 33057 compile finding; no deterministic control finding. |
| Semantic effect | Pass | The frozen judge confirms one issue match among three included PR 33098 obligations. |
| Transfer discipline | Pass | The model did not copy the retrieved request to make an unrelated declaration an iff lemma. |
| Control | Pass | PR 33438 produced zero raw candidates and zero selected findings. |
| Replication | Pending | One fresh three-unit run is still required before expansion. |

## Included-pair audit

1. `pr33098_i02`, `isCover_maximalSeparatedSet`: `issue_match=true`,
   `resolution_match=false`. Both identify the verbose manual membership/separation argument as the
   aspect to refactor. The candidate retains a `by_cases`/`simp` construction and does not request
   `isSeparated_insert_of_notMem` plus the encard contradiction chain, so it does not achieve the
   maintainer's requested result.
2. `pr33098_i03`, `card_maximalSeparatedSet`: false/false. The candidate requests an `encard_`
   rename; the included obligation concerns rewriting the consumer
   `coveringNumber_le_packingNumber`. The shared change ID and renamed dependency are insufficient.
3. `pr33098_i04`, `coveringNumber_two_mul_le_externalCoveringNumber`: false/false. The candidate
   objects to the unused `h_nonempty` binder and proposes `by_cases`; the maintainer requests the
   `rfl` empty branch. These are different binders and transformations under the strict rubric.

Confirmed included metrics:

- location recall: 3/4 overall (`0.75`), versus `0.25` in 0.8.9 and `0.50` in 0.8.10;
- PR 33098 issue recall: 1/3;
- PR 33098 resolution recall: 0/3;
- paired-candidate issue precision: 1/3;
- selected-finding control false-positive rate: `0.00`.

## Pending-decomposition diagnostic

The candidate to rename `card_maximalSeparatedSet` to `encard_maximalSeparatedSet` matches an
independent clause of `pr33098_i01` nearly exactly. That view is marked `pending_decomposition`
because it combines proof simplification, attributes, analogous targets, and cardinality-lemma
renames in one obligation. It is therefore absent from the official denominator and pair set.

Before a larger pilot, split `pr33098_i01` into target-level atomic obligations and add a separate
diagnostic report for matches against pending-decomposition gold. Do not silently promote those rows
into the headline metric or alter this run's frozen evaluation.

## Evidence and cost

- Evidence packets: one supported deterministic compile candidate, four inconclusive model asks.
- Selected findings: one PR 33057 blocking compile finding.
- Generator cost reported by the three samples: $0.22987825.

## Automated confirmation

`gpt_5_mini` under `v4-semantic-v1-v7.1-rubric` returned the same labels as the manual
audit for all three candidate-obligation pairs. The generated report and standing audit are stored
under `results/pr_review_v4/runs/dev-pilot-0.8.11-temporal-retrieval-smoke3/semantic-judge-v1/`.
