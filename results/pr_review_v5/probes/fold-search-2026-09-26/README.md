# Fold search: finding the library concept a PR's expression is an unfolded instance of (2026-09-26)

**Question.** `docs/todo/review-design-comparison.md`: comparison-design asks are a stable tenth of
round-1 asks, and in 17-23 of 43 (validation) and 25 of 73 (outside the sets) the PR wrote out the
body of something the library already names. Name search finds 0 of 43; statement-shape search
through Loogle 1 of 15. Can unification against the library's definitions, single-field classes and
rewrite-lemma sides find the analogue, and does it return the twin family the decoy readings demand?

**The search** (`lean/Fold.lean`, a Lean 4 metaprogram run inside a Mathlib workspace):
- one discrimination tree over three kinds of pattern, each with the declaration's parameters as
  holes: definition bodies (`QuotSMulTop`, `IsSeqCompact`), the field of a one-field `Prop` class
  or structure (`Submodule.IsPrincipal`), and both sides of every `Eq`/`Iff` lemma whose other side
  has a non-generic head (`Subgroup.finiteIndex_iff`, `Pi.single_apply`);
- `#fold e` walks `e` and its subterms, entering binders, queries the tree with each subterm and
  its alias-unfolded form (`Ideal.span` to `Submodule.span`), unifies at default transparency, and
  keeps a hit only if the fold drops the subterm's head symbol and its non-generic constants, keeps
  none of its non-atomic proper subterms, and introduces a new non-generic constant; under a binder
  `x`, a fold `F … x` with `x` last is also reported as the function-level fold `F …`;
- `#fold_decl c` folds a declaration's type and, for a definition, its body;
- `lean/FoldIndex.lean` records the index (about 200k entries) into its olean at compile time, so a
  file importing it pays seconds, not the 53 s build.

**The harness** (`harness/`): for every labelled comparison ask whose analogue is not one of the
PR's own siblings, the PR's file at the commit the comment was made on (fetched into the local
clone), compiled against one built base (`7ee74e7d…`, 2026-01-16) with `#fold_decl` on every
declaration the PR added to that file. The declaration under the comment is the SITE; the others
measure noise. Scored by `score_harness.py`: compiled or not, the site's folds against the
readers' analogue, folds per non-site declaration.
