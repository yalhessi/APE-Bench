# Review designs: the one-PR smokes, 2026-10-02

The build session for `docs/plans/2026-10-02-review-designs.md` (branch `review-designs`).
Nothing here called a model; every record is the task driven by hand against the real
reviewed workspace. The dev runs of the designs are scheduled by the user per subscription
window after the hygiene reps.

## D1 `structured` on PR 33337 (`smoke_structured.py`, `smoke_structured.json`)

The task was built as `cli run` builds it from `configs/designs/structured_dev_claude_sub.yaml`
restricted to 33337, set up on the reviewed workspace `a36c84ab…+ae229ca53e6b`, its tools
registered (`declaration_search`, `lean_verify_edit`, `naming_norm`, `precedent_search`,
`proof_profile`, `submit_findings`, `zulip_search`; the first and the grant are the hygiene
config's, `proof_profile` included because the config's `solo_context_tools` is the base's), and
its own `submit_findings` called with a full ledger (5 declarations x 6 concerns) carrying five
`would_change` cells:

| change | check at submission | outcome |
|---|---|---|
| `starProjection_le_starProjection_iff`, proof: the declaration as the PR leaves it, as an edit | whole-file compile of `Positive.lean`, linters on | **verified**, 0 warnings introduced |
| `coe_starProjection_eq_isComplProjection`, proof: `exact nonexistent_lemma_for_the_smoke` | whole-file compile of `Submodule.lean` | **refuted**: "the edit introduces 1 error(s); the first: Unknown identifier `nonexistent_lemma_for_the_smoke`" |
| `IsSymmetricProjection.le_iff_range_le_range`, library: `duplicate_of: IsCompl.projection_range` | declaration lookup, base and reviewed | **verified**: declared in `Mathlib/LinearAlgebra/Projection.lean:186` before this PR |
| `coe_orthogonalProjection_eq_linearProjOfIsCompl`, name: `rename_to: Submodule.starProjection` | declaration lookup of the new name | **refuted**: already declared at `Projection/Basic.lean:177` |
| `orthogonalProjection_apply_eq_linearProjOfIsCompl`, docstring: a wording ask | nothing can check it | **filed advisory, unverified** |

The first submission was handed back naming the two refuted changes with the tools' answers
(27 s, two whole-file compiles and the baseline compile of the file with the error). The second
dropped the clashing `rename_to` (the finding then files unverified) and kept the broken edit past
the press bound: accepted in 11 s, "30 ledger cells, 4 findings filed, 1 refuted". The result
carries the ledger with the outcome on each `would_change` cell, the four findings with the solo's
keys plus `concern_label`, `declaration`, `concern` and `verification`, and the refuted row with
Lean's error. The prompt is the solo's (23,245 characters for this PR) with the ledger contract
appended and the `notes` line removed.

What the smoke could not settle, and the first paid rep must: whether the Claude Code session
writes the typed `ledger` and `findings` in one `submit_findings` call, and what the ledger costs
in turns and tokens on the large PRs -- `plan` reports 336 cells on 33149 and 516 on 33294
(86 declarations), which a row deciding several concerns at once brings down to at least 86 rows.

## D2 `structured_critic` on PR 33337 (`smoke_structured_critic.py`, `smoke_structured_critic.json`)

D1's smoke now also writes `stage_structured/ledgers.jsonl`, the row the runner's `_ledger_rows`
writes for the PR (it was re-run for this: the same outcomes, 26 s and 12 s). The critic smoke
reads that row as its first stage through the runner's own `stage_rows_for` -- `StageInput`
pointed at the directory beside the script, since the smoke's stage is not under
`results/pr_review_v5/runs/` -- builds the task as `cli run --of <run>` would from
`configs/designs/structured_critic_dev_claude_sub.yaml`, sets it up on the same reviewed
workspace, and drives its submission by hand. The payload line `plan` would print:
"stage review_designs_smoke_structured: 30 cells, 5 would_change, 4 finding(s) filed, 1 refuted".
The prompt (25,927 characters) renders D1's ledger, its filed changes and its refuted change.

Positions: 23 `concede`, 2 `overturn`, 2 `confirm`, 2 `refute`, 1 `undecided`. The first
submission was handed back in 18 s: the critic's rename of `le_iff_range_le_range` onto
`Submodule.starProjection` is already declared at `Projection/Basic.lean`. Resubmitted without
the name, it was accepted in 9 s: "30 cells, 6 findings in the union (2 the critic's), 0 refuted".

| in the union | stage | critic's position | agreed | verification |
|---|---|---|---|---|
| `starProjection_le_starProjection_iff`, proof | structured | refute | false | verified |
| `le_iff_range_le_range`, library | structured | confirm | true | verified |
| `coe_orthogonalProjection_eq_linearProjOfIsCompl`, name | structured | undecided | none | unverified |
| `orthogonalProjection_apply_eq_linearProjOfIsCompl`, docstring | structured | confirm | true | unverified |
| `coe_orthogonalProjection_eq_linearProjOfIsCompl`, proof | critic | overturn | false | verified (identity edit compiles) |
| `le_iff_range_le_range`, name | critic | overturn | false | unverified (the clashing name dropped) |

The critic's `refute` of D1's verified identity edit is a label: the finding stays, carried as D1
filed it. D1's change the tools refuted at its own submission is in neither stage's findings.

What this smoke cannot settle: whether a Claude Code session argues with a ledger in this form,
and what a critic session costs. That is D2's first paid rep, after D1's. Nesting the critic
inside D1's session (the plan's first choice) was not built and not smoked: any test of it is a
live Claude Code session on the subscription, and the chained form needs no nesting.
