# Shape search through Loogle (2026-09-26)

**Question.** Does a statement-shape search reach the analogue for the asks where the PR wrote out
the body of something the library names? Loogle (https://loogle.lean-lang.org, current Mathlib,
so PR-merged declarations are in the index and are flagged) with **one derivation rule**: the
hunk's target expression with its bound identifiers replaced by `_`, recorded per ask in
`loogle_shape_test.json` so the rule, not knowledge of the answer, can be seen to have set the query.

**Result, 15 queries.** Analogue ranked first in **1** (`Subgroup.index _ ≠ 0` → `FiniteIndex`),
rank 89 in 1 (`QuotSMulTop`, behind 88 quotient lemmas), absent or unparsed in 13:
- **a different spelling of the same thing**: `∃ x, _ = Ideal.span {x}` matches nothing because
  `IsPrincipal` is stated with `Submodule.span R {a}`; `if _ = _ then 1 else 0` returns `Nat.one_sub`
  and `List.count_*` decoys because `Pi.single_apply` has a variable where the PR has the literal `1`;
- **the analogue is a definition body, not a statement**: `MulAction.orbit` and `QuotSMulTop` are
  reached by unfolding, which a statement index cannot do;
- **the pattern language**: `_` cannot stand for a function, so `{y | ∃ t, _ t _ = y}` and the
  `Finsupp.prod` shape do not parse; `∀ y, _ ≤ y` times out;
- **role analogues do not have a shape**: `FunLike` for a `CoeFun` instance, `Module.Invertible`
  for a localisation equivalence, `IsCompact` for a sequentially phrased predicate.

**Reading.** Shape retrieval works when the PR's expression is the library's statement verbatim
up to renaming, and that is rare: the useful matches need unification modulo reducible unfolding
(`Ideal.span` to `Submodule.span`), generalisation of literals, and an index of definition bodies
and `_apply`/`_def` right-hand sides, not statements alone. That is an `exact?`-style search
against definitions, run inside Lean, and it is the build the todo now names. The decoy exemplar
v2006 returned nothing at all, so the shape route neither finds the analogue nor the decoy there.
