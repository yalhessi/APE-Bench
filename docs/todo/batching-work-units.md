# Work-unit batching — the partition an arm holds authority over is produced by a hash

**Status** — **the grouping half landed on `batching-work-units` (`12a3939`…`24746b2`), producing
release `dev-medium-0.4.0`.** Work units 225 → 121, declaration-free units 96/203 → 46/121,
attached targets split from their declaration 73 → 0. Authority, `patch_set` and the family-claim
siting are still open.
**Cost** — the diagnosis cost nothing; the landed fixes cost nothing; a confirming rep is unrun
**Owner question** — what set of declarations is one unit of review, and who may file about it?

## Motivating example

PR 33145's six `Dense.continuous_*` theorems all live in one file and are one family. The
maintainer asked for a coordinated rename plus a dualization across them. They were split across
**four work units**, and the dual pair the maintainer asked to be derived from one another —
`continuous_sup` and `continuous_inf` — landed in units 1 and 3.

Nothing semantic caused that split. `build_work_units` sorts `(path, change_id)` — the change_id is
a content hash — and greedy-packs to 24,000 characters (`work_units.py:21,36,39`). A declaration's
own docstring is a separate `command` target and routinely lands in a different unit from its
declaration: `change:fef41c8` is the upperBounds docstring at line 169, in unit 4, while
`Dense.continuous_upperBounds` at line 171 is in unit 2.

**And the budget that forced the split is double-counted.** PR 33145 has exactly one distinct diff
fragment, 5,196 chars, attached to all 12 targets. The packer charges it 12 times — 62,352 + 5,002
base/reviewed + 6,000 padding = 73,354 chars against a 24,000 cap — but `render_focused._target_blocks`
prints each distinct hunk once and points later targets at it, so the real rendered content for the
whole PR is 10,198 chars, **42.5% of a single unit's budget**. Repacking the held-out 12 on
deduplicated content gives **92 work units instead of 203**; PR 33149 goes from 108 units to 12.

## Why it matters

Every authority boundary (`change_ids ⊆ unit`), every routing claim (one required `family_design`
per PR) and every cost unit (one mandatory generalist per unit) is keyed to that partition.

- **41 of 62** family components on the held-out set span more than one work unit; unit-span
  distribution `{1:21, 2:30, 3:5, 4:2, 5:2, 6:1, 32:1}`.
- **22 of 32** required family-grain jobs give the arm authority over only part of the family it is
  required to review as a group. On 33149 the one required `family_design` job holds 1 of 32
  members — an arm whose whole remit is "are these right AS A GROUP" shown one declaration.
- The required family job is sited at the **lexicographically smallest work_unit_id** (8/8 PRs
  confirmed). On 33145 that put the single `family_design` look on the upperBounds/lowerBounds unit
  and never on the sup/inf units, which is where the two `ciSup`/`ciInf` obligations live.
- **5 of 24** anchored gold obligations name targets in more than one unit and are unfileable by any
  single arm: 33145 (2 units), 33117 (13 targets / 5 units), 33149 (19, 19 and 22 units).
- **47.3%** of held-out units (96 of 203) contain no declaration target at all — 41 command, 40
  module_doc, 13 import, 4 section, 3 namespace — and each draws a mandatory generalist pass. They
  emit *more* candidates per session than units with declarations (1.54–1.67 vs 0.85–1.07).

## What is NOT the problem (checked and refuted)

The candidate schema does **not** forbid expressing a group ask: `change_ids` is a list, and arms
demonstrably voice whole-family asks in free text. The verified statement is narrower — the judge's
`level_status` hits an obligation only if a *single* candidate matches, and on 33145 the `naming`
arm filed both gold renames as two separate candidates, each `issue_match=True`,
`resolution_match=False`, in every run. `obligation:e83e6544d51cc95d5` has scored
`resolution_match=False` in all 8 runs across 43 anchor-paired rows.

So the open question is whether the loss is authority, judging, or emission — not "the schema
forbids it".

## `patch_set` has never been exercised once

The capability built for exactly these asks: **1,660 `patch_set` keys across 258 artifact files
under `results/pr_review_v5/runs/`, every one null.** Three compounding defects:

1. Only `family_design` holds the grant.
2. Its prompt explains `patch_set` at `focused_prompts.py:553-562`; the SUBMISSION_CONTRACT
   rendered 2,413 chars below it opens "This supersedes any field list above" and its JSON template
   omits `patch_set` entirely.
3. `_patch_set_workspace` does `Path(self.target_workspace)` where that attribute is a
   `WorkspaceInfo` — every other call site uses `.path` — so first use raises TypeError. The
   guarding test assigns a *string*, so it passes while pinning a type the runtime never produces.

Any claim that "arms cannot express coordinated fixes" currently rests on a mechanism that would
crash rather than refuse.

## What would close it

In order, cheapest first:

1. ~~**Fix the packing accounting**~~ — **done in `12a3939`.** `_pack_bundles` charges a hunk once
   per unit; 225 → 121 units. It also fixed a defect the entry did not know about: `command` was
   85% severed declaration parts (59 doc-comments, 26 attributes, 6 real commands), so a
   declaration's own docstring was scheduled away from it — 38 of 59 doc-comments sat in a unit
   with no declaration at all. They are now named (`doc_comment`, `attribute`), carry `attached_to`,
   pack with their declaration, and are diffed with it. That was a *recall* defect, not tidiness:
   it cost the two PR 33321 obligations every baseline repetition had found.
2. **Fix `patch_set` and exercise it once** — `.path`, retype the test, add the field to the
   contract template for `PATCH_SET_ARMS`, then force one submission on 33145.
3. **Rank the once-per-PR family claim by component coverage**, not by `work_unit_id`. Three lines
   in `plan_coverage`'s sort.
4. **Decide the authority question.** `build_file_task_data` (`task_adapter.py:78-114`) already
   widens every per-target map beyond a work unit and documents why all the maps must widen
   together — it has one caller, a v4 path, and is unreachable from the v5 agenda. Per CLAUDE.md's
   "find the primitive and use it", extend that rather than build a second widening path.
5. **Cap the `exact` family closure.** `components.py:135-215` warns at length about union-find
   over-grouping and guards the `hypothesis` branch — but `exact` is itself a union-find closure and
   on 33149 it produces a **32-member component** rendered to the arm as "these ARE one group",
   containing `FourierCoeff`, `Vorticity`, `bkm_implies_regularity` and 29 others.

## Risk

Items 1 and 3 move frozen hashes; that cost is paid once and should be paid in the same change.
Item 4 is a design decision, not a refactor. None of this is on `dead-ends.md` — batching has never
been tried and abandoned, it is documented-and-unfixed inside `patchset.py` and `request_groups.py`.

## Record correction this forces

`dead-ends.md`'s "Specialists as the coverage floor" entry attributes the 33145 miss to "the right
arm was never asked … the arms present were duplication/api_reuse/style". The artifacts of the run
it cites show `naming` ran on all four 33145 units and at the gold unit returned `status=success`
with both renames, `admission=published`. The entry's *conclusion* is untouched; its 33145 clause
points the next session at routing when the artifacts point at resolution scope. See
[record-corrections.md](record-corrections.md).
