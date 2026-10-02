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

## D2 `structured_critic`

Built as a chained stage (`cli run … --of <structured run>`), reading D1's `ledgers.jsonl`
through `StageInput`; see the module docstring for why, and the session report for the open
question (nesting a critic session inside a Claude Code session on the subscription is untested,
and the chained form needs no nesting). Its smoke is the unit tests with the verification faked:
no stage-1 run exists yet to read.
