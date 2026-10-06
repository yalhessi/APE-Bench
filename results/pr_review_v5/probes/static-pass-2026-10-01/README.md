# The static analysis pass, measured alone (pre-registered 2026-10-01, before its results)

Layer 1 of `docs/plans/2026-10-01-beyond-the-solo-baseline.md`; step 2 of
`docs/todo/static-analysis-pass.md`. Before any model reads the pass, what does the pass alone
say about the dev PRs, and at what false-positive floor?

## The first check: the standard linter set

`standard_set_alone.py` compiles every changed `.lean` file of every dev episode in its reviewed
workspace with `-Dweak.linter.mathlibStandardSet=true`, the package build's own linter set, which
the hygiene layer switched on for every whole-file compile (`0a3d7d33`). Every message with a
position is kept and mapped through the release's change graph: a line inside a changed range's
`reviewed_span` belongs to the change targets that cite that range. A message outside every
changed range is pre-existing and is counted apart, never charged to the PR.

Inputs: `inputs/pr_review_v4/releases/dev-medium-0.3.0` (change graphs, gold judgments) and the
episode-to-workspace map of a completed dev run (`reviewed_workspaces.json`). Outputs beside this
file: `hits.jsonl` (one row per message, with `in_diff`, `change_ids`, `declarations`),
`compiles.jsonl` (status and seconds per file), `summary.json`.

## Reading rule, stated before the run

The pass is scored without a judge, on the dev held-out 12 (23 obligations) and the two control
PRs (33304, 33315):

- **Located**: a gold obligation is located when a diff hit shares a change target with it. This is
  the judge's `location_hit` notion and it is not a hit: whether the linter's message *is* the
  maintainer's ask is read by hand from `hits.jsonl` and written here as a second count,
  obligation by obligation, with the message quoted.
- **False-positive floor**: the number of diff hits on the two control PRs, where maintainers
  asked for nothing. This is what the pass would file on a clean PR at zero model cost.
- **Volume**: diff hits per PR and the distribution of linter kinds, so that a hit count is read
  beside what kind of hit it is (a long line is a maintainer ask on this set; a `cdot` style note
  may be noise).
- **Pre-existing**: counted and never charged.

The pass is a lever for the packet if it reaches, by hand-read ask match, at least 2 of the 23
obligations (the two long-line asks, `cc44bb99` on 33305 and the 33117 line the maintainers
flagged, are the ones in reach by construction) with at most 2 diff hits per control PR. It is
not a lever as a finder if it reaches none, or if its control-PR hits exceed what a single Opus
pass emits there (1.0 per control PR). Either way the pre-existing and in-diff counts say what a
packet section restricted to the diff would carry.

One check (the standard set), one set (dev): what this says about the other checks in the todo
(`shake`, `#lint`, the tacticAnalysis set) is nothing; each gets its own run under the same rule.

## Result, the standard set alone (2026-10-01)

84 changed `.lean` files over the 15 dev episodes, every one compiled (663 s of compile in all,
2-35 s a file in the prebuilt workspaces; the mapping was rerun by declaration span after a first
pass by changed range located every 33149 obligation at once, since a new file is one range).

| | |
|---|---|
| messages with a position, in the diff | **20** (0 outside it) |
| on the control PRs 33304, 33315 | **0, 0** |
| PRs with any hit | 2 of 15: 33149 (19), 33305 (1) |
| kinds | `linter.unusedVariables` 17, `linter.style.longLine` 1, Lean's own `#print axioms` output 2 |
| gold obligations located (shared change target) | 2 of 25 |

**By hand, against the asks.**
- `cc44bb99` (33305, style, blocking): the one `longLine` warning, `Inverses.lean:23`, is the ask
  verbatim ("wrap the overly long doc comment line ... around line 20"). An exact match, on the
  obligation no lead or solo condition located in six reps.
- `3e19231d` (33149, "rewrite the file to meet mathlib standards"): located through the unused
  variables in `fourierDecay`, `spectralNSResidual` and `SolvesNavierStokes`, which are part of
  that ask and not its substance (the axioms). Partial.
- The two information messages at `GalerkinRegularity.lean:467-469` are a `#print axioms` the
  author left in the file: "'GalerkinLimit.smooth' depends on axioms: [bkm_implies_regularity, ...]".
  That is the fact behind the two blocking axiom obligations (`3dacf72e`, `f54010d8`), stated by
  Lean; it does not share their change targets (it maps to the command, not the axiom
  declarations), so it is not counted as located. Evidence, not an ask.

**By the rule.** Strictly, 1 exact ask match of 23 with 0 control hits: under the 2-ask bar for
"a lever". Generously, 1 exact, 1 partial and 2 evidenced: over it. What is not in doubt: the
packet section this check would add is 20 lines on 2 of 15 PRs, at zero cost on the clean PRs,
and 19 of the 20 lines are on the AI-generated PR, which is the population this project is
aimed at. The standard set is nearly silent on human PRs at the reviewed state: 13 of 15 PRs,
including every control, produced nothing in 83 files. So this check earns its place in the
packet by cost and by what it says on AI-generated PRs, not by recall on this gold; the other
checks in `docs/todo/static-analysis-pass.md` (`shake`, `#lint`, the tacticAnalysis set) are
where the try-it and unused-import asks live, and each gets this measurement before it is
believed.
