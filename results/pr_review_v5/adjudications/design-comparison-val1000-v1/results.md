# Design asks: what the maintainer compared against (results, 2026-09-26)

Two blind readers (A: the session; B: a subagent given only the rubric and the packet) over the
95 design-family asks with an agreed reference; labels on the 31 `variant` and 43 `library` +
`siblings` asks. `results.json` holds every count; kappa is Cohen's, per field.

## Group A: the 31 asks where the maintainer proposed a different design

| question | result |
|---|---|
| could both readers write the principle as a one-sentence rule? | **30 of 31** (B: `none` on v0297, "inline this definition") |
| stated explicitly in the comment (agreed) | 4; implicit (agreed) 18; split 9; kappa 0.33 |
| source (agreed) | library practice 15, mathematical 3, tacit 1; split 12 (A reads "how the library does it" where B reads "the maintainer's own model"); kappa 0.31 |
| in Mathlib's written guidance (`written_guidance_match.jsonl`, checked against `written_sources.md`) | **written 8, a maxim only 12, nowhere 11** |

The written eight are the general maxims: simp-normal forms, split long proofs, API for new
definitions, strong conclusions. The eleven written nowhere are the encoding choices: inline a
relation into its instance, define the extended structure in one go, iterate as a functor, an
`ObjectProperty` stated with `IsIso`, a `default` by its canonical construction, expanded functions
over compositions. So the taste is articulable, and three quarters of it is not written down.

## Group B: the 43 asks that compare the PR against something that exists

| question | result |
|---|---|
| same comparison object named by both readers | **43 of 43** (35 by string match on the declaration names; the other 8 are the same object in different words, listed in `results.json`) |
| analogue named in the comment (agreed) | yes 27, implied 6; split 10; kappa 0.43 |
| how it was findable (agreed) | API shape 13, the PR's own siblings 5, role 3, name 3; split 19; kappa 0.37. The splits are `name` against `api_shape` and `role` against `name` **for the same analogue**: a primed constructor is both a name sibling and an API shape |
| a wrong analogue plausible | agreed yes **2** (`Finsupp.single` for `Pi.single`; `IsSeqCompact` for `IsCountablyCompact`); by either reader **7 of 43**; agreed no 36; kappa 0.40 |
| name-token search from the PR's own declarations (`name_search_baseline.json`) | analogue in the top ten for **0 of 43**, with 32 present in the index; the top hits are lookalikes |

## Reading

- **Identifying the analogue is not the hard part; retrieving it is.** Given the ask, two blind
  readers agree on the comparison object every time. A name search reaches it never, and its top
  hits would compare the PR against the wrong sibling in nearly every case. That is the risk the
  user named, located: it lives in retrieval, not in judgment.
- **The largest findable class is API shape, and it is mechanisable.** In 17 (A) to 23 (B) of 43,
  the PR wrote out the body of something the library already names: `index ≠ 0` is `FiniteIndex`,
  `∃ x, I = span {x}` is `IsPrincipal`, `if n = k then 1 else 0` is `Pi.single`, `f.comp g = id` is
  `LeftInverse`, `CoeFun` plus an `ext` lemma is `FunLike`. A search that matches the PR's
  expressions against the bodies of the library's definitions and classes, up to renaming, is the
  next retrieval to build and test on these 43.
- **The decoys are near-miss concepts, and one of them defeats shape matching.** Metric against
  emetric, ring-level against ideal-level principal, `SL(2,ℤ)` against its image, sequential against
  filter compactness. Shape matching separates most of them. It does not separate v2006: the PR
  *wrote* the sequential form, so a shape match returns `IsSeqCompact` and would suggest keeping it,
  while the maintainer's ask is the opposite, "define it as `IsCompact` and `IsLindelof` are defined".
  That ask rests on a role-level convention (compactness predicates are stated with filters) that no
  shape carries. It is the exemplar to test any retrieval against.
- **The written guidance covers a quarter of the taste.** Handing the reviewer the style guide,
  the review guide and the values page supplies the maxims; the encoding choices come from the
  library's practice or from nowhere written, which is where the model's own knowledge, and the
  probe-cutoff caveat, enter.

## Caveats

- Both readers are language models reading merged PRs; the rubric confined them to the comment and
  hunk, and the `analogue` field is what the comment names or implies, not what a reviewer would
  find.
- The name-search baseline ran against one built base, not each PR's own; 11 of the 43 analogues
  are absent from it (PR-internal siblings, notation), and for the rest the library state differs by
  months.
- Kappa on the route labels is low because the vocabulary overlaps; the object agreement is what
  the guard needs, and it is measured directly.
