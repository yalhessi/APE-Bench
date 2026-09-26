# Design comparison on PRs outside every set: does the problem generalise? (rubric, pre-registered 2026-09-26)

**Why.** The first reading (`design-comparison-val1000-v1`) measured 95 design asks drawn from the
validation set. The user (2026-09-26): expand the PRs "to ensure that this is a worthwhile
investment to solve a problem that actually matters in PRs outside of our immediate focus". This
reading sizes the same phenomenon on round-1 review comments from PRs that belong to no evaluation
or development set, and, when collection allows, from months outside the 2025-06..2026-03 window.

**Unit.** A round-1 reviewer comment (review, review comment, or issue comment before the first
author response, as the episode projection cuts it), with its diff hunk and parent comment. AI
authorship is carried on every row and reported apart, never excluded.

## Stage 1: every comment, one label

`ask_kind`, exactly one:
- `not_an_ask`: approval, thanks, a question answered by the author, bot output, a maintainer note
  with no request.
- `other`: an ask that is not about design: proof golf, naming, formatting, docstring wording,
  attributes, imports, PR process, correctness.
- `design_library`: the ask compares the PR's definition, statement or lemma family against
  something that already exists in Mathlib (a construction, predicate, API pattern or notation) and
  asks the PR to use or align with it.
- `design_siblings`: the ask compares the PR against its own other declarations: a missing twin
  (dual, left/right, additive), an inconsistency between two of its declarations, a duplicated proof.
- `design_variant`: the maintainer proposes a different design or statement from taste, with no
  existing object named or implied.
- `design_norm`: a design ask that cites a stated convention (bundled morphisms, `FunLike`,
  simp-normal form) without a specific analogue.
- `design_other`: a design ask that fits none of the above (generality, API owed, encoding choice
  argued from the mathematics).

The `design_*` labels correspond to the first reading's `reference` facet on the design family.

## Stage 2: `design_library` and `design_siblings` only

Same fields and vocabularies as the first reading:
- `analogue_named`: `yes` / `implied` / `no`; `analogue`: a few words.
- `findable_by`: `name` / `role` / `api_shape` / `neighbourhood` / `pr_internal` / `unclear`.
- `wrong_analogue_plausible`: `yes` (name the decoy in `note`) / `no`.

## Rules

- Read the comment, its parent and the hunk only; never the PR's later history.
- Two readers, blind to each other; counts reported as agreed / split; kappa per field.
- Report by AI authorship and, when the out-of-window collection exists, by created month.
- The number this reading exists for: the share of round-1 asks that are `design_library` or
  `design_siblings`, and within them the share findable by `api_shape` and by `role`. If that share
  on PRs outside the sets is far below the validation reading's (43 of the 506-sample's asks, 8.5%),
  the retrieval build is not general and does not proceed.
