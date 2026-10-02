# Review designs: the one-PR smokes, 2026-10-02

The build session for `docs/plans/2026-10-02-review-designs.md` (branch `review-designs`).
Nothing here called a model; every record is the task driven by hand against the real
reviewed workspace. The dev runs of the designs are scheduled by the user per subscription
window after the hygiene reps.

## D1 `structured` on PR 33337 (`smoke_structured.py`, `smoke_structured.json`)

*Re-run 2026-10-02 after the contract change (an entry per declaration with six fixed concern
cells, recorded through `record_ledger`; see the gpt-5.2 section below for why): the same five
outcomes, the first three entries recorded through the registered tool and the rest in the
submission, 27 s and 13 s.*

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

## The first paid test: D1 on gpt-5.2, PRs 33315 and 33337 (2026-10-02)

The user's "Let's test with GPT models for now": `configs/designs/structured_dev_gpt52.yaml`,
run `probe_dev_structured_gpt52_Grc_contract2_smoke1`, $3.57 billed (33315 $0.99 in 24 turns,
33337 $2.58 in 28), no retries, complete.

- The contract ran: the typed ledger was filled and submitted in one call, with no refusals.
  33315 (control): 6 cells, all `no_issue`, nothing filed, as the baseline g52v2 did. 33337: one
  `would_change`, 3 filings, none verified, none refuted.
- **The ledger collapsed.** Every declaration got one row over all six concerns with one shared
  reason. The multi-concern row was this branch's compression, and it gave back one decision per
  object. The contract now has an entry per declaration with a field per concern, each with its
  own verdict and reason, through `record_ledger`; the second test reads whether that holds.
- The one real filing is the baseline's own ask, renaming `coe_starProjection_eq_isComplProjection`
  to `..._isCompl_projection`. The reviewer had called `naming_norm` on it and seen `toLinearMap_`
  lead `coe_` 21 to 7 -- the gold direction on this PR -- and asked for the suffix change anyway.
- The other two filings are a tool artifact: a `commandStart` linter warning at each changed
  file's end, "will fail CI". `eof_linter_check.py` reproduces it with no spend: the Lean tool
  strips the file's final newline before compiling. Recorded in
  `docs/todo/framework-defects-2026-09.md`; not fixed here, since it changes the frozen
  baseline's tools between hygiene reps.

## The second D1 test and the D2 test on gpt-5.2 (2026-10-02)

- D1 under the six-cell entries (`probe_dev_structured_gpt52_Grc_contract2_smoke2`, $1.79): six
  distinct reasons for every declaration on both PRs, against one shared reason before; one
  `record_ledger` call per session; 33315 nothing filed, 33337 the baseline's rename only.
- D2 on that run (`probe_dev_structured_critic_gpt52_Grc_contract2_smoke2`, `--of` the D1 run,
  $1.69): 35 cells conceded with their own evidence, the rename confirmed, nothing overturned.

## D1 on gpt-5.2, dev rep 1: the reading rule, stated before the run

Run `probe_dev_structured_gpt52_Grc_contract2_rep1` on the 15 dev PRs, judged with
`configs/pr_review_v5_medium_heldout_judge.yaml` on the held-out 12 (23 obligations, judge v9).
Read against its own baseline, gpt-5.2 contract v2 (`probe_dev_gpt52_Grc_contract2_rep1`, g52v2):
**2 of 23**, 44 findings, control emission 0.0 per control PR.

- **A lever on gpt-5.2:** at least 5 of 23 (the baseline plus 3, beyond the judge's one to two
  obligations of noise on 23) with control emission at most 2.0 per control PR.
- **Not, as built:** at most 3 of 23, or control emission above 2.0. Four is provisional either way.
- Read beside it: hits per finding, control emission per claim and on the docs family separately,
  how many findings are the end-of-file linter artifact, `unstated` cells, and whether the large
  PRs (33149: 56 declarations, 33294: 86) recorded their ledgers.
- One rep on dev is provisional whatever it shows, and says nothing yet about Claude: the
  Claude rule (plan §5) is read on the subscription runs.

## D1 on gpt-5.2, dev rep 1: read against the rule

`probe_dev_structured_gpt52_Grc_contract2_rep1`: 15 of 15 sessions, $35.80 billed, judged for
$0.08 (audit `probe-dev-structured-gpt52-Grc-contract2-rep1`).

| | g52v2 (baseline) | D1 on gpt-5.2 |
|---|---|---|
| held-out obligations hit, of 23 | 2 | **2** (the same two: `3dacf72e`, `f54010d8`) |
| findings | 44 | 46 (51 filed before merging) |
| paired with gold | 11 | 11 |
| control-PR findings | 0 | 0 |
| change targets shared (Jaccard) | | 0.45 |

**Not, as built, on gpt-5.2** (rule: at most 3 of 23). The contract was kept everywhere: 1,698
cells, every declaration with six distinct reasons, nothing `unstated`, nothing refuted, the
86-declaration ledger of 33294 recorded. But 1,660 cells (98%) are `no_issue`, and the 38
`would_change` cells produce the baseline's volume, on the baseline's PRs. What gpt-5.2 lacks
here is not an occasion to decide; it decides "nothing to ask" one cell at a time. Filed by
concern: proof 16, docstring 10, placement 12, statement 8, name 5; 29 verified by a compile or a
lookup, 22 unverified. Six filings are the end-of-file linter artifact.

Altitude: one rep, one model, the design as built. Untried before anything is concluded: D1 on
Claude (the model the plan measured the inconsistency on, `configs/designs/structured_dev_claude_sub.yaml`),
D1 on gpt-5.5, D2 on this run (its job is exactly the 1,660 `no_issue` cells), and reps.

## D2 on gpt-5.2, dev rep 1: the reading rule, stated before the run

Run `probe_dev_structured_critic_gpt52_Grc_contract2_rep1`, `--of probe_dev_structured_gpt52_Grc_contract2_rep1`,
judged the same way. Plan §5's D2 rule, against D1's 2 of 23 at 0.0 control emission:
- **A lever:** at least 4 of 23 (D1 plus 2) with control emission at most 2.0 per control PR.
- **Not, as built:** at most 2 of 23, or the critic's additions on the control PRs refuted or
  above 2.0 per control PR. Three is provisional.
- Read beside it: positions by kind (`overturn` / `concede` / `confirm` / `refute`), the critic's
  filings and their verification, and which obligations an `overturn` reached.

## D2 on gpt-5.2, dev rep 1: read against the rule

`probe_dev_structured_critic_gpt52_Grc_contract2_rep1`, reading D1's dev rep 1 (15 ledger rows,
sha256 83e333352ad5, after the empty-ledger fix): 15 of 15 sessions, $49.36 billed, judged for
$0.08 (audit `probe-dev-structured-critic-gpt52-Grc-contract2-rep1`).

| | g52v2 | D1 on gpt-5.2 | D2 on gpt-5.2 |
|---|---|---|---|
| held-out obligations hit, of 23 | 2 | 2 | **2** (the same two) |
| findings | 44 | 46 | 56 |
| paired with gold | 11 | 11 | 12 |
| control-PR findings | 0 | 0 | 0 |
| billed | $28.68 | $35.80 | $49.36 on top of D1 |

**Not, as built, on gpt-5.2** (rule: at most 2 of 23). The critic took the task seriously and
still agreed almost everywhere: 1,652 `concede`, 38 `confirm` (every D1 change), 0 `refute`, 8
`overturn`, which with three file-level changes gave 11 critic filings, all verified, on 33149 (4),
33321 (3), 33098, 33285, 33362 and 33421 (1 each), by concern docstring 4, statement 4, proof 2,
name 1. None hit an obligation; one moved a site from nothing to `loc` (33321's module doc,
`0bb42bd2`). D1 and D2 share their change targets at Jaccard 0.79.

What the two designs say together, at this altitude (one rep each, one model, the designs as
built): on gpt-5.2 the unit of decision is not what binds. Asked separately about every
declaration under every concern, and then asked to argue every "nothing to ask", gpt-5.2 says
"nothing to ask" with reasons in 98% of cells and reaches the same two obligations its unstructured
baseline reaches. That is the reviewer-model gap's reading (docs/todo/reviewer-model-gap.md) seen
from a new side, and says nothing about Claude, whose inconsistency the designs were built against.

Untried, before anything is concluded about the designs: D1 and D2 on Claude Opus 5.5 on the
subscription (the configs are ready), D1 on gpt-5.5, reps of either, and the confirmation sets.
