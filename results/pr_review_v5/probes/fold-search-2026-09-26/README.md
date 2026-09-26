# Fold search: finding the library concept a PR's expression is an unfolded instance of (2026-09-26)

**Question.** `docs/todo/review-design-comparison.md`: comparison-design asks are a stable tenth of
round-1 asks, and in 17-23 of 43 (validation) and 25 of 73 (outside the sets) the PR wrote out the
body of something the library already names. Name search finds 0 of 43; statement-shape search
through Loogle 1 of 15. Can unification against the library's definitions, single-field classes and
rewrite-lemma sides find the analogue, and does it return the twin family the decoy readings demand?

**The search** (`lean/Fold.lean`, a Lean 4 `module` importing only `Lean`, so any file, module-system
or not, can import it; `FoldPlain.lean` is the same for pre-module toolchains):
- one discrimination tree, built over the importing file's environment in about 40 s for all of
  Mathlib, over three kinds of pattern with the declaration's parameters as holes: definition bodies
  (`QuotSMulTop`, `IsSeqCompact`), the field of a one-field `Prop` class (`Submodule.IsPrincipal`),
  and both sides of every `Eq`/`Iff` lemma whose other side has a non-generic head
  (`Subgroup.finiteIndex_iff`, `Pi.single_apply`); entries whose key is a bare hole, or whose side
  is a binder telescope over a hole, are dropped, since they match everything;
- `#fold e` walks `e` and its subterms, entering binders, and queries the tree with each subterm at
  up to three spellings: as written, with alias definitions unfolded one level (`Ideal.span` to
  `Submodule.span`; an alias is a non-instance definition whose body is one application whose
  arguments are variables, constants or instances), and once more; unification at `instances`
  transparency;
- a hit is kept only if the fold contains none of the levels' non-generic heads, none of the
  original's distinctive constants (instances and instance projections excluded), no non-atomic
  part or binder body of any level, and introduces a non-generic constant no level has; instance
  terms are never subjects; under a binder `x`, a fold `F … x` with `x` last is also reported as the
  function-level fold `F …`, and otherwise as pointwise-only;
- `#fold_decl c` folds a declaration's type and, for a definition, its body; `#fold_try c : kind e`
  traces one entry against a term with every filter's verdict.

On the six canonical cases (`lean/probe2.lean`): `B.index ≠ 0` ⇒ `B.FiniteIndex` and `Finite (A ⧸ B)`;
`∃ x, I = Ideal.span {x}` ⇒ `Submodule.IsPrincipal I` (through the alias level); `if n = k then 1 else 0`
⇒ `Pi.single k 1` as a function, `EuclideanSpace.single` as a typed family member, `SkewMonoidAlgebra`
pointwise-only; `M ⧸ x • ⊤` ⇒ `QuotSMulTop x M` from the definition body; the flow orbit and the
sequentially phrased compactness statement fold to nothing, the latter as the guard requires (this
Mathlib's `IsSeqCompact` is the subsequence formulation, so no shape fold exists).

**The harness** (`harness/`): for every labelled comparison ask whose analogue is not one of the PR's
own siblings, the PR's file at the commit the comment was made on (fetched into the local clone),
compiled against the latest built base dated at or before the review comment (the library the
maintainer saw; 64 of 71 within 30 days), with the whole of Mathlib at that base imported and the
file's declarations wrapped in a fresh namespace so they never clash with the base's copy of the
module, and `#fold_decl` on every declaration the PR added. The declaration under the comment is
the SITE; the others measure noise. Eight toolchains from 4.22 to 4.29; the search is compiled once
per toolchain and variant. Scored by `score_harness.py`: whether the site declaration exists at that
base, the site's folds against the readers' analogue, folds per non-site declaration.
