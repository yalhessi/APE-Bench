# Design asks: what the maintainer compared against (reader rubric, pre-registered 2026-09-26)

**Population.** The 95 design-family (F6) asks in the 506-ask validation facet relabel on which
both facet readers agreed on `reference` (and both arm-coverage readers on the family). Source rows
are the validation feedback (`cid`, body, diff hunk, parent comment when a reply).

**Question.** `docs/todo/review-design-comparison.md`: is the design taste behind an ask
articulable, and where did the maintainer's comparison object come from? Two label sets, one per
reference group. Readers label blind to each other; kappa is reported per field.

## Group A: `variant` asks (the maintainer proposes a different design)

- `principle_stated`: `explicit` (the comment states the principle in general form: "we prefer X
  because Y"), `implicit` (a specific alternative is given and the principle is recoverable from
  it), `none` (an alternative with no recoverable reason).
- `principle_source`: where that principle lives, best guess: `written` (Mathlib's style guide,
  library notes, naming conventions, module docs, `docs/`), `library_practice` (how the library
  does this everywhere, not written down), `mathematical` (a mathematical reason: generality,
  the right notion), `tacit` (the maintainer's own model of good design; nothing to point at),
  `pr_internal` (a reason from the PR's own content or description).
- `principle`: the principle in one general sentence, as a rule a reviewer could be given.

## Group B: `library` and `siblings` asks (comparison against something that exists)

- `analogue_named`: `yes` (the comment names the declaration, file or PR sibling), `implied` (it
  is identifiable from the comment and hunk without being named), `no`.
- `analogue`: what it is, in a few words.
- `findable_by`: how a reviewer without memory could have located it: `name` (a name or docstring
  word of the PR's own declaration leads to it), `role` (the same kind of object playing the same
  role: the hom type of X, the free object, the `Prop`-valued predicate for a structure),
  `api_shape` (the same API pattern: `map`, `comp`, `ext`, `coe`), `neighbourhood` (the same file,
  directory or import closure), `pr_internal` (another declaration of the same PR), `unclear`.
- `wrong_analogue_plausible`: `yes` if a nearby declaration a naive similarity search would rank
  as high or higher would lead to a wrong ask; `no`; with a note naming the decoy when `yes`.

## Reading rules, stated before reading

- The principle is read from the comment and hunk only, not from the PR's later history.
- `written` is claimed only when the reader can name the document; otherwise `library_practice`.
- A reply inherits its parent's comparison object when the reply does not state one.
- Counts are reported as agreed / split, never averaged.
