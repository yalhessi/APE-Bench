# PR Review v4 0.8.7 smoke3 verdict

## Verdict

The execution and evidence plumbing are now a go. The reviewer is still a no-go for the nine-PR
pilot because semantic candidate recall and evidence-to-message fidelity remain inadequate.

## Execution

- 10/10 work units completed successfully across PRs 33057, 33098, and 33438.
- All workspaces and prompt hashes were preserved.
- 20 candidates were accepted: 1 on PR 33057, 17 on PR 33098, and 2 on control PR 33438.
- Candidate generation cost approximately $1.89, including approximately $1.22 reported as cached
  cost.
- Evidence initially repeated the same large baseline compilation for every candidate and was
  terminated during PR 33098. Run-scoped baseline compilation caching was added and regression
  tested; evidence then completed all 20 packets.

## Evidence and selection

- Packet status: 1 supported, 19 inconclusive, 0 contradicted.
- Exactly one finding was selected, on PR 33057.
- Both raw candidates on control PR 33438 remained inconclusive, so the selected control false
  finding rate is 0/1.
- The only terminal collector disposition was that the selected PR 33057 candidate had no
  temporally eligible precedent. Its direct compiler evidence completed successfully.
- PR 33057 fails Lean at the candidate's exact target with an unsolved goal in `expand_apply`.

## Semantic audit

The selected PR 33057 finding identifies the right location and underlying compile problem, but its
published wording says the proof is "likely fine" and labels it advisory. The evidence proves that
the reviewed file currently fails. The collector therefore supports a nearby, stronger proposition
than the candidate actually states. Reusing the pre-evidence claim verbatim is not publication-safe.

PR 33098 still misses all four eligible atomic maintainer requests. It has two location overlaps out
of four, but neither is an issue match:

- At `isCover_maximalSeparatedSet`, the candidate questions a `simp` step instead of proposing the
  requested `C := {x} union maximalSeparatedSet ...` refactor.
- At `coveringNumber_two_mul_le_externalCoveringNumber`, the candidate is attached to that target ID
  but discusses the neighboring `coveringNumber_le_packingNumber` theorem. This is a primary-target
  grounding failure, not partial semantic recall.

The run again notices an `encard_` naming direction inside a compound intervention excluded pending
decomposition, plus several plausible incidental comments. These do not improve eligible atomic
recall.

## Scoped metrics

`evaluation-scoped.json` explicitly limits denominators to the three executed PRs:

- 4 eligible atomic obligations, all on PR 33098.
- Candidate location recall: 2/4 (50%).
- Manual semantic candidate recall on those obligations: 0/4.
- Selected eligible-obligation recall: 0/4.
- Control selected findings: 0/1.

PR 33057 is excluded from these formal obligation metrics because its migrated broad CI-failure
obligation is marked `not_evaluable`, although the live compiler independently confirms the issue.

## Required next

1. Add a primary-subject grounding contract that validates the claimed declaration/identifier
   against the selected change/entity, while allowing separately typed external evidence anchors.
2. Add evidence-conditioned finalization. Publication must restate a supported proposition and
   normalize severity when direct evidence is stronger than the candidate wording.
3. Change candidate discovery on multi-obligation PRs. The current open-ended "find plausible
   concerns" behavior produces speculative correctness/style commentary but does not recover the
   maintainer's concrete transformations.
4. Rerun these same three PRs before paying for all nine.
