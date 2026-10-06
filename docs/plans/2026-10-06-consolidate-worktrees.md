# Consolidating the worktrees into one state (2026-10-06) — written as built

Before a code clean-up round, every topic worktree's unmerged work was read and either landed on
`develop`, landed in part, or parked on a tag. The integration was done on branch `consolidate`
in its own worktree, because the main checkout had other sessions in it; the suite and
`verify_frozen verify` passed at every commit. The commit bodies carry each conflict's resolution.

## What was read

34 worktrees. 20 were already fully on `develop` and needed nothing: abstention-capture,
claude-code-harness (codex-harness), claude-subscription, coordinated-emission, decision-replay,
elm-provider, eval-set-selection, gpt-harness-parity, integration (integration-typed-handoffs),
merge-probe, openai-responses-provider, pipeline-overfit-review, post-carryover-replan,
specialist-silences, stage-provenance, subtask-contract, test-suite-runtime, unify-contract,
wall-clock and work-enumeration. Their only leftovers are untracked run directories the record
already calls partial, stopped or smoke runs. The other 14 are below.

## Merged whole

| Branch | Why |
|---|---|
| conventions-models (fast-forward), conventions-nature | The census and the conventions-ceiling probe, stages L, C, F, G, H and M; none of it was on `develop`. |
| hygiene-layer, review-designs | Harness fixes wanted whatever the experiments read, the frozen solo baseline (9, 9, 7) and the D1/D2 designs `develop`'s after-structure plan reruns next. |
| ensemble-union, evidence-layer | Results `develop`'s plans already quoted or linked; `cli report union`. |
| local-model-unlock | A preflight fix, and the steering screen's negative read. |
| removed-declarations | Closes a study `develop` still listed as open. |

**Run boundary.** hygiene-layer changes every scaffold's compile-tool output, and ensemble-union's
two new `ReviewFinding` fields change `source_sha256` for any finding finalized from here. A run
after this point is not on the same tools as the runs before it.

## Landed in part

| Branch | Taken | Left on the tag |
|---|---|---|
| convening-demo | the overlay entrypoint fix, the worktree re-root in `cli trajectory`, the rel050 trajectory record | `review_demo.py` and its page (`parked/convening-demo`) |
| increment0-rebaseline | the lead-orientation audit, warrant by issue kind, the synthesis-flag note | nothing else (`parked/increment0-rebaseline`) |
| arm-division | three fixes (half an edit, the artifact join, dev text in tool schemas), the family-division run and its per-job write-up | the family-division and `pr_level` arms (`parked/arm-division`) |
| naming-from-statement | the bench retrieval-cutoff fix, the testbed pre-registration, results and write-up | the statement index, `naming_parts`, the `naming_statement` tool (`parked/naming-from-statement`) |

Two picks were adapted rather than applied. The half-edit fix keeps hygiene's rule that a span
with no `replacement` is a deletion. The tool-text contamination gate needed `to_additive` on its
generic-vocabulary list for D1's text.

## Dropped

arm-naming-bar (`parked/arm-naming-bar`): its fixes were ported or superseded on `develop`; its
`MIN_SUPPORT_RATIO` refutation is now in `docs/dead-ends.md`. arms-speak: already carried over by
the unify-contract work, kept on `pre-unify/arms-speak`. `docs/dead-ends.md` has an entry for every
parked thread.

Branches with no worktree: `pr-review` and `s3-support` predate the August restaging and add no
code. `s3-support`'s snapshot `f61c1a1a` is the only copy of about 271 MB that the restaging left
out, so it is tagged `parked/s3-support-snapshot`. `verify-reviewed-state` is already on `develop`.

## Files that lived only in a worktree

521 gitignored files existed only inside a worktree: `arm_pool.jsonl` input pools, which `cli
replay` reads, and rendered probe briefs. They total about 650 MB and were copied into the main
checkout at the same paths, never overwriting. 14 committed runs index their tasks through a
worktree path; `cli trajectory` now re-roots those onto the shared `.ape`, so removing a
worktree no longer silently empties them.

## Not done here

- Fast-forwarding `develop` to `consolidate`: it rewrites files under any session working in the
  main checkout, so it waits for those to be idle.
- Removing the worktrees and deleting the merged and parked branches: on the user's word only.
- `docs/research/gpt-reviewer-gap-diagnosis-2026-10-05.md`, untracked in the main checkout, links
  into `.claude/worktrees/review-designs/results/...`; once `develop` has the merge those paths
  exist in the main tree, and the links should drop the worktree prefix before that worktree goes.
