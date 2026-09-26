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

## Results (2026-09-26, `harness/scores.json`, `harness/folds.json`, `harness/run.log`)

66 asks materialised (142 labelled comparison asks, minus 51 whose analogue is one of the PR's own
siblings, 14 with no built base at or before the review, 8 with no site, file or importable header,
3 whose own imports are absent at the base); the site declaration exists at its base in **50**
(the other 16 fail to elaborate: unknown constants from the PR's other files, or drift). Median 49 s
per file, maximum 161 s, on one core each.

| | count |
|---|---|
| sites present | 50 |
| sites with at least one fold | 33 (32 in the naming tier) |
| sites where a fold is the readers' analogue | **6**, all naming tier: `QuotSMulTop`, `SimpleGraph.IsBipartite`, `Pi.single`, `Subgroup.FiniteIndex`, `Submodule.IsPrincipal`, `Set.preimage` |
| among the 30 present sites labelled findable by API shape | 4 hits |
| fold family at a hit | 2 to 4 folds, 1 to 3 in the naming tier |
| non-site added declarations | 176, every one with a fold: 4.97 folds each, **2.12 in the naming tier** |

**Reading.**
- **The mechanism is real and narrow.** When the PR wrote out the body of a named concept, the
  search returns that concept with a small typed family around it, and the six hits are exactly
  that class. Six of 50 is the size of that class among the asks the readers labelled "API shape",
  not a failure of the search: the readers' label also covers primed constructor variants
  (`TotalSpace.mk'`, 5 asks), a structure literal that should go through a smart constructor
  (`Fork.ofι`, `Cofork.ofπ`), missing twins (`Set.EqOn` variants, `app_sub`, the `lt` twin), and
  two-step relations (`Finsupp.prod` against a subtype product), none of which is a one-step fold.
  Each of those is a different mechanical route: name-twin enumeration, a smart-constructor check
  on structure literals of a type that has `T.of*`, the twin check, and rewrite chains.
- **Binder order defeats unification.** `∀ i j, j ≤ i → p i → p j` is `Antitone p` with the binders
  swapped, and no permutation is tried; two or three binders could be.
- **Noise is the cost.** Two naming folds per added declaration is what the arm would have to read;
  most are true synonyms fired by common subterms (`Option α` into `WithBot`/`WithTop`/`WithOne`,
  `Set.Icc` into `uIcc`, `algebraMap R R`), which a per-constant blacklist or a frequency cap would
  cut, at the risk of the carrier-axis twins the decoy reading asked for.
- **Drift bounds the harness, not the search.** Sixteen sites of 66 did not elaborate at a base up
  to 30 days before the review; the search never ran on them.

**Against the todo's closing criterion** (two thirds of the 43 validation analogues with at most
one wrong in five): not met, and not the right criterion for this route. The route settles the
"wrote out the body of a named concept" class at high precision and small families; the remaining
comparison asks need the other routes above or role retrieval.
