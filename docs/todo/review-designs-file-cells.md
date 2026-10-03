# The structured reviewer's ledger covers declarations only, so a PR's file-level asks have no cell

**Status** — built, not measured (2026-10-02, `review-designs`, design `structured/3`: one ledger entry
per changed file with `module_doc`, `style` and `organization`). Closes with the next D1 reps on Claude.
**Cost** — no spend to build; one Claude subscription window per dev rep to measure.

**Motivating example.** D1 `structured` on Claude Opus 5.5, dev rep 1
(`probe_dev_structured_hygiene_claude_sub_rep1`, results/pr_review_v5/probes/review-designs-2026-10-02/README.md)
reached 10 of 23 held-out obligations against the hygiene reps' 9, 9, 7, and lost exactly one that
all three hygiene reps hit: `cc44bb99`, "wrap" a line in `Mathlib/GroupTheory/Submonoid/Inverses.lean`
on 33305. 33305 leaves no declaration in place (`plan`: 0 ledger cells), so D1's contract gave the
reviewer nothing to decide there; its asks could only come as file-level findings (it filed two,
neither the wrap). The ledger is built from the change graph's `declaration` targets
(`structured.py::declarations_of`); module docs, commands, sections and imports -- 36 `command`
and 15 `module_doc` targets on 33149 alone -- have no cell.

**What would close it.** Add one ledger entry per changed file, with the concerns that apply to a
file as a whole (its module doc, style and linting, imports and placement), built the same way
from the change graph and checked by the same completeness rule; then a D1 rep on Claude, read
against D1 rep 1 and the hygiene reps on the obligations at file-level targets (`cc44bb99`,
`0bb42bd2`, `38e72250` among them). A lever if those are reached without losing the declaration
hits or raising control emission above 2.0 per control PR -- with the caveat that every control
finding D1 rep 1 made is already a module-doc wording ask.

**Start here.**
- read: `src/ape/tasks/lean_tasks/formal_math/review/structured.py` (`declarations_of`,
  `DeclarationVerdicts`, `_check_ledger`), `structured_critic.py` (positions mirror the cells),
  the README above.
- run: `ape/bin/python -m src.mathlib_review.review.cli plan --config configs/designs/structured_dev_claude_sub.yaml --run-name probe_dev_structured_hygiene_claude_sub_rep2`
- bounded by: the selection ruling (`.claude/rules/mathlib-review.md`): a file entry is an occasion
  to decide, never a filter; the end-of-file linter artifact (`docs/todo/framework-defects-2026-09.md`)
  will look like a file-level style ask until it is fixed.

**Risk.** Control PRs are mostly module-doc edits (33304, 33315), and D1's three control findings
are all module-doc wording; a file cell for the module doc invites more of exactly that.

**First measurement (2026-10-03).** `structured/3` dev rep 1 on Claude reached `cc44bb99` (the
33305 line wrap) and 10 of 23 overall at control emission 1.5; every control filing is a
module-doc wording ask, 4 in the ledgers, 3 by the judge's count, as under `structured/2`. Lost
against `structured/2`: `585e5e0b` and `e8e02821`. One rep; the close condition (the file-level
obligations reached without losing declaration hits) waits for reps 2 and 3.
