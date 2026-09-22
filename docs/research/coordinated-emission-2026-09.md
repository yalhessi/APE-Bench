# A fix that spans declarations can now be submitted (2026-09-22)

The generation-side half of the question this thread started on: not why the arms are silent, but
what they cannot say when they speak. Five audits and a code stress-test put it at one shape —
a maintainer's ask that is only correct as a set of edits, against a submission that carries one
edit about one declaration. Nothing was spent; this is code plus two local compiles.

## What was wrong, and it was five things

| | mechanism | evidence |
|---|---|---|
| 1 | granted to one arm of ten | `family_design`: 182 recorded responses, **0 candidates**, ever |
| 2 | `_patch_set_workspace` did `Path(WorkspaceInfo)` | `TypeError` on first real use; every other consumer reads `.path` |
| 3 | `apply` spliced a declaration by `text.replace(name, new, 1)` | rewrites the first *mention* — on a real file, its own docstring |
| 4 | the contract template omitted the field | under "This supersedes any field list above"; the one arm that could was told 2,400 chars earlier |
| 5 | the finding schema drops it | the judge never sees the edit |

Each is independently sufficient, and together they explain a number with no other explanation:
**0 of 3,411 candidates across 60 runs has ever carried a `patch_set`.**

Mechanism 3 was not in the record. Its comment claimed it did "exactly as the single-edit path
does"; the single-edit path parses with `extract_proof_blocks`, refuses an ambiguous match and
replaces `header_span`..`body_span` with prefix handling. Demonstrated on three lines of Lean: an
edit naming `Dense.continuous_sup` put the whole replacement inside the doc comment, left the
declaration standing, and reported no problem — then compiled the wreckage and returned the errors
to the model as its own fault. No test in this repository could see it, because every source in the
patch-set tests was one line whose declaration name occurred exactly once.

Mechanism 2 had a test written to catch its sibling. That test assigned a **string** to
`target_workspace`, so it agreed with itself and never with the class — the rules file's "a
hand-built fake cannot disagree with the class it stands in for", verbatim.

## What changed

One splice, used twice. `splice_declaration` is factored out of `_edited_file_code` unchanged and
passed into `patchset.apply` as a required argument — passed rather than imported, so `patchset`
keeps no dependency on the task layer, and required rather than defaulted because the default it
had was the bug. An empty `new_declaration` now deletes a declaration, which `PatchEdit.mode()`
already admitted and nothing implemented; `deletion` is 3 of the 11 obligation shapes needing a
coordinated fix.

**Confinement moved from the file to the anchor**, which the 2026-09-08 plan set as the
precondition for widening the grant and nobody had done. Each edit names the `change_id` it is
about; `anchor_problems` refuses an anchor the candidate does not claim, a file that is not that
anchor's file, and — the tightening — a declaration-mode edit naming a *different* target of the
unit. That last rule is what makes a wider grant safe: before the repack a unit was nearly one
declaration, so file confinement was almost anchor confinement; now a unit holds up to a dozen.

**The grant is a rule, not a list**: `patch_set_arms() == checkable_arms() | {family_design}` — an
arm may submit a coordinated patch when its fix is a change to code whose correctness a compile
settles, or when the group itself is its whole remit. `naming`, `docs` and `style` ask for names,
prose and formatting, where the compile is not what makes the ask right. The audited ledger's
`answerable_arm_ids` for the 6 `patch_set` and 3 `deletion` request groups are exactly that set,
which is evidence for the rule and is asserted in a test rather than written into the registry.

**The instruction moved into the contract that supersedes everything above it**, for the seven
granted arms. The three ungranted ones render byte-identically to the previous commit — checked,
not assumed, and asserted — which is what `focused-prompt/4` records.

## Does it work? Two local compiles, no model

Against a real reviewed workspace (`0bf098ca…+b156e3e2`) and a real Mathlib file:

- **A two-edit coordinated patch applies through the real splice and compiles**, returning
  `ok=True` and a `lean_compile_patchset` artifact naming both edits and the touched file.
- **The negative control refuses the whole candidate**: a valid first edit plus a second that does
  not elaborate gives `ok=False` with the compiler's own errors. The gate is not passing vacuously,
  which for a warrant is the property that matters.

## What this does not establish

- **That an arm will use it.** This is the most likely falsifier and the reason the next runs are
  ordinary and unforced. The arms can already voice these asks in prose — the three obligations
  this targets have 20, 10 and 6 judge issue-matches — and decline to build the fix; if they emit
  zero patch sets with the field in their schema and the clause provably in their prompt, the
  constraint was never the schema.
- **That `resolution_match` will move.** Pairing already reaches a multi-site finding, because the
  `anchor` tier joins on the candidate's full `change_ids`. What the judge cannot see is the edit:
  `patch_set` is dropped at `candidates_from_response`. That is deliberately deferred until a run
  shows an arm emitting one, rather than built on a hope.
- **That this is 11 of 40 obligations.** Those 11 are **6 maintainer comments**, two of which
  expand to 7 obligations on PR 33098 alone; outside it the shape is 4 of ~26. And the ledger
  under-counts the shape it was built to count — it classifies the corpus's most-matched,
  never-resolved obligation as a plain rename, dropping its second conjunct. A second
  classification pass comes before any headline.
- **Cross-file patches still cannot be verified.** `verify` compiles each patched file against
  unpatched `.olean`s, so PR 33337's two-file rename pair stays out of reach. Work units are one
  file, so this binds rarely and it binds absolutely.
- **The statement gate is skipped on the patch path**, so a `proof_simplification` patch could move
  a statement unnoticed. The anchors make a per-edit gate possible; recorded, not built.

## Evidence

- `src/mathlib_review/patchset.py` (`anchor_problems`, `apply`, `verify`),
  `src/ape/tasks/lean_tasks/formal_math/review/base.py` (`splice_declaration`),
  `.../review/candidates.py`, `src/mathlib_review/agenda/registry.py`,
  `src/mathlib_review/agenda/render_focused.py`.
- `docs/plans/2026-09-22-coordinated-emission.md` (the plan and its falsifiers);
  `docs/todo/batching-work-units.md` item 2; `docs/dead-ends.md`, "Track 1.C's second half".
- `src/mathlib_review/analysis/request_groups.py` — the audited ledger, evaluation-only, read here
  as evidence for a decision and never by generation.
