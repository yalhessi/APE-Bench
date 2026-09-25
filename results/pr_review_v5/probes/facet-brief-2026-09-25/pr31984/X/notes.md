# PR 31984 — notes (condition X)

## Mathlib.lean
- Checked the single added import line. It is in alphabetical order (Contraction < ConvexSpace < Countable). Nothing to ask.

## Mathlib/LinearAlgebra/ConvexSpace.lean — header, imports, module doc
- Searched for an existing `ConvexSpace`, `FiniteProbability` or `convexCombination`: nothing found, so there is no name clash (only `StrictConvexSpace`, `LocallyConvexSpace`, `UniformConvexSpace`).
- Found three places that anticipate convex spaces: `Finset.expect` (Expect.lean:34-40), `stdSimplex` ("free object in the category of convex spaces") and the ProbabilityMeasure TODO. I asked for the module doc to reference them and for the Expect note to be updated.
- Imports: `Data.ZMod.Defs` supplies the ring structure on `Fin n` that `grind` may use. I could not show that any import is unused without compiling, so I asked nothing.
- Location (`LinearAlgebra/`): the TODO targets AffineSpace/lineMap, which live in LinearAlgebra/AffineSpace, so the placement is defensible. Nothing to ask.

## FiniteProbability (structure)
- It is a finitely supported analogue of `stdSimplex`. I asked for the naming and docs to be aligned with `stdSimplex` (advisory).
- The minimal `[LE R] [AddCommMonoid R] [One R]` assumptions are fine. I considered stating `nonneg` as `0 ≤ weights` in the Finsupp order; that form is definitionally the same (Order/Preorder/Finsupp.lean:30), so I only used it in the `single` golf.

## FiniteProbability.single
- `open Classical in` is common in Mathlib (246 uses), but here it only serves a proof field. `Finsupp.single_nonneg` (Data/Finsupp/Order.lean:69) gives the proof in one line. I raised this as proof-golf.

## FiniteProbability.duple
- The docstring says "weights `x` and `y`", but the parameters are `s`, `t`: a documentation fix, and I also asked to drop the in-code open question.
- The `simp; grind` proof is short. It is a non-terminal `simp`, but I did not raise it separately; low value.
- Naming `duple`: I found no clear sibling convention to cite, so I asked nothing.

## FiniteProbability.comp
- The `total` proof is AI-generated ("Aristotle") and long, and the needed lemmas exist: `sum_sum_index`, `sum_embDomain`, `Finsupp.sum_smul_index` (Data/Finsupp/SMul.lean:177) and `Finsupp.mul_sum` (BigOperators/Finsupp/Basic.lean:610). I asked for a short rewrite chain.
- The `nonneg` proof unfolds `Finsupp.embDomain` although the API lemmas exist (`embDomain_apply` / `embDomain_notin_range`), and it uses anonymous `have`s where `bound [..]` would do. Style finding.
- Universe polymorphism: κ and ι share the universe `v`. `Type*` would be more general, but I did not raise it because the class ties the index universe to M anyway.

## ConvexSpace (class)
- `IsStrictOrderedRing` is stronger than needed: `IsOrderedRing` supplies ZeroLEOneClass and PosMulMono, and ℝ≥0∞ has only `IsOrderedRing` (ENNReal/Basic.lean:126). I raised a generalization finding and included the binder order.
- The `ext` field is a congruence property, not extensionality, and would squat the name `ConvexSpace.ext`. I raised a naming finding.
- I considered whether reindexing invariance or commutativity of binary combinations follows from the axioms. The module TODO already acknowledges that the axioms are unsettled, and I have no concrete counterexample, so I did not raise it.

## convexCombo₂ and the variable line
- `fun | 0 => x | 1 => y` should use the `![x, y]` idiom (122 vs 2 occurrences).
- `variable {R M}` introduces untyped fresh binders, because the earlier `R` was scoped to the ended namespace. I asked for explicit types.

## proof_wanted convexCombo₂_zero / _one / _same
- The statements look true given `single` + `ext`: `duple 0 1` has the same weights as `single 1`. Inline `(by simp)` side proofs are fine and `proof_wanted` is allowed. Nothing to ask.
