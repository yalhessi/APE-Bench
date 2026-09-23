# Batching, kinds and prompt repair — three reps on the held-out twelve

*2026-09-15. Conditions: `pr5_A_lead_heldout12_v2_rep{1,2,3}` on `dev-medium-0.3.0` against
`pr5_A_lead_heldout12_rel050_rep{1,2,3}` on `dev-medium-0.5.0`. Same twelve PRs, same 23 scored
obligations, same model, same judge, three repetitions each, all six complete with 0 coverage
gaps.*

## Result

**Recall is unchanged within noise and cost is 46% lower.**

| | per-rep | mean | union | stable |
|---|---|---:|---:|---:|
| issue, 0.3.0 | 7, 5, 6 | 0.261 | 0.304 | 0.217 |
| issue, 0.5.0 | 7, 5, 7 | 0.275 | 0.348 | 0.217 |
| resolution, 0.3.0 | 4, 3, 4 | 0.159 | 0.174 | 0.130 |
| resolution, 0.5.0 | 4, 3, 4 | 0.159 | 0.217 | 0.130 |
| `issue_recall_reachable`, 0.3.0 | 0.417, 0.333, 0.333 | 0.361 | | |
| `issue_recall_reachable`, 0.5.0 | 0.333, 0.333, 0.417 | 0.361 | | |
| billed | 13.83, 12.75, 13.75 | **$13.44** | | |
| billed | 7.28, 7.20, 7.31 | **$7.26** | | |
| control-PR candidates | 2, 3, 4 | | | |
| control-PR candidates | 0, 0, 1 | | | |

The judge splits its own vote on about 11% of pairs and one obligation of 23 is ~4pp, so every
recall difference here is inside the noise floor and none of them is claimed. The cost difference
is not: it is 46% and it replicates across three repetitions.

`coverage_gaps` is 0 in all six runs and `issue_recall_reachable` means are identical, so
scheduling coverage never moved. What changed is what the reviewer chose to say.

## What produced it

Four changes, landing together as `dev-medium-0.4.0` → `0.5.0`:

1. **Target kinds.** `command` was the bucket every unrecognised entity fell into and was 85%
   severed declaration parts: 59 doc-comments and 26 attributes against 6 real commands. They are
   now `doc_comment` and `attribute`, and carry `attached_to` naming the declaration they belong
   to. 73 of 85 attach.
2. **Packing.** The budget summed every target's `diff_fragments`, but a unit's targets share a
   hunk and the renderer prints each once — PR 33145 charged 62,352 characters for content
   measuring 10,198. Charging once per unit, and bundling a declaration with its parts, took the
   held-out twelve from **203 work units to 92** and the release from 225 to 101.
3. **Scoped diffs** (`9d4de8f`): a target's `### Exact changed fragments` is its own change, not
   the `@@` hunk it sits in. Removes 94.0% of the release's fragment characters.
4. **`candidate-prompt/14`**: the checklist once per prompt, the contract kept in the user
   message, and a declaration's parts joined the way the file has them.

The cost came from (2). The prompt-volume work in (3) and (4) is measurable in characters and was
*not* where the money was — see `docs/todo/lead-prompt-cost.md`.

## Two things this does not say

**The conditions are complementary, not equivalent.** Hit-set overlap is 5, against a union of 7
for 0.3.0 and 8 for 0.5.0; **combined union is 10 of 23 = 0.435**. 0.5.0 finds two renames no
baseline repetition ever did (33294 dot-notation, 33421 `round_eq'` → `round_eq_div`) and misses
two the baselines got (33117 `@[to_fun]`, 33321's docstring). Equal aggregates, different content.

**Nothing here is a precision result.** `gold_alignment_rate` rose from 0.069–0.091 to
0.181–0.202, and control-PR emission fell to 0/0/1 from 2/3/4. Both are real counts, and neither
is precision: gold is a lower bound on what a maintainer could legitimately ask for, so a
candidate absent from it is unaligned rather than wrong. **Roughly 90% of findings are not
maintainer obligations and nothing in the current evaluation adjudicates them.** Until something
does, "fewer candidates with a higher alignment rate" cannot be read as better or worse output —
only as less output that overlaps gold more often.

## The mechanism the means conceal

Consolidating 203 units into 92 cut **generalist candidates per target from 0.494 to 0.154**, a
3.2× drop. The generalist emits roughly a constant number of candidates per *job*, not per
target, so halving the job count divides the attention each target receives.

Two of the three losses trace to it directly:

- **33321's docstring.** In 0.3.0 the doc-comment sat alone in its own work unit and drew a
  dedicated generalist job whose entire scope was that one comment; it read it and caught
  `crystallogrphic`. In 0.5.0 the comment is correctly attached to its declaration and packed
  into a unit of ten-plus targets, whose generalist filed one candidate about a different
  declaration. The `docs` arm was **eligible and pruned by the lead**, which chose `duplication`,
  `proof_golf` and `proof_idiom` instead.
- **33117 `@[to_fun]`.** Its 13 change-ids spanned 5 units in 0.3.0 and 1 in 0.5.0 — the family
  grouping working as designed. Five units meant five generalist jobs plus arms on each, and the
  baseline's single hit came from `api_reuse` across those shots. In 0.5.0 all ten arms ran on the
  one unit and none asked for `@[to_fun]`; `family_design` abstained `already_correct`. That arm's
  ignorance of `@[to_fun]` is already on `dead-ends.md`.

So the repair that reunited a doc-comment with its declaration also removed the dedicated job that
had been reviewing it. Both effects are real; at that site the second dominated.

## Corrections this comparison forced

**`location_recall` was over-weighted throughout the investigation.** It counts obligations where
some candidate anchored to the gold `change_id` *without* naming the issue — the agent asking for
something else at the right line. A drop in it means a quieter run said fewer off-target things,
which is at best neutral. An intermediate run's 0.478 was read as a neutrality failure and drove
the six-site investigation; the investigation was worth it, but the metric was not carrying that
weight. The number now ships with a note in the semantic report and a rule in `CLAUDE.md`.

**Two defects were found by reading a prediction back against a result**, not by a test:

- The packer carried a stale fresh-fragment set across a unit boundary, so each new unit was
  charged again for a hunk it already held. PR 33149 packed into 31 units where the dedup predicts
  12, and the held-out twelve into 111 where `docs/todo/batching-work-units.md` had predicted 92.
  Fixed; both numbers now reproduce exactly.
- The attachment join inserted a blank line that is not in the source, turning an ordinary Lean
  docstring-then-attribute into two floating comments. The reviewer answered the artifact, asking
  to remove "an extra adjacent doc comment" on an obligation about that docstring's content.

## What is open

- **Off-gold adjudication.** The blocker for reading precision at all, and now the largest gap in
  the evaluation.
- **Per-target attention.** Either a cap on targets per unit, or telling the generalist how many
  targets it holds and that one candidate for ten is not coverage. Untested.
- **The lead's pruning.** With 92 jobs instead of 203, each prune removes a larger share of a PR's
  attention. `docs` pruned off a documentation obligation is the concrete case; one occurrence is
  not a pattern.
- The rest of `docs/todo/batching-work-units.md`: authority, `patch_set`, family-claim siting, and
  the `exact` closure cap are all untouched.

## Artifacts

Runs `results/pr_review_v5/runs/pr5_A_lead_heldout12_rel050_rep{1,2,3}`, audits
`results/pr_review_v5/audits/pr5-A-lead-heldout12-rel050-rep{1,2,3}`, and the intermediate
`rel040_rep1` on `0.4.0` at `candidate-prompt/13`, kept because it is the only measurement of the
contract's effect: dropping it took generalist emission from 1.24–1.30 to 0.71 per job and issue
recall to 4 hits, and restoring it recovered both.
