# PR 27099 — reviewer notes (condition Y)

Reference files: Mathlib/ModelTheory/Algebra/Ring/Basic.lean (Language.ring) and Mathlib/ModelTheory/Order.lean (Language.order), the two existing languages built from operations.

## Definitions
- `FirstOrder.presburgerFunc` (inductive): compared against `ringFunc` (Ring/Basic.lean:48). It has the same shape, name form and `deriving DecidableEq`. No finding.
- `Language.presburger` (def): mirrors `Language.ring` (Ring/Basic.lean:57), including `deriving IsAlgebraic`. On naming I found no problem. The ring language's `card_ring` / `Fintype Symbols` API is missing here, but I dropped that as not owed: nothing in the PR needs it.
- `presburger.succ` (def): nothing in the PR uses it except `realize_succ`, and it has no return type. I found no count or exhibit for a norm and only a weak judgment (a second spelling of `t + 1`, possibly used in #27100). Dropped.
- `presburger.finsum` (def): the library cell hit. `_root_.finsum` (Finprod.lean:96) is a different concept, and the body is `List.sum` unfolded (List/Defs.lean:24-26). Finding 2 asks for a rename to `sum` over a `Finset`. Its docstring ("defined via choice, only makes sense when commutative") is roughly accurate, so no prose finding.

## Instances
- `Zero`/`One`/`Add (presburger.Term α)`: these match the ring's term instances (Ring/Basic.lean:94-105). The ring file also has `zero_def`/`add_def` lemmas, but the PR's lemmas here are `rfl`, so I dropped it. No other instance on `L.Term` exists (grep for `Structure (L.Term` gave 0 hits), so there is no diamond.
- `NatCast` via `Nat.unaryCast` and `SMul ℕ` via `nsmulRec`: these are needed because Term is not an AddMonoid. The same pattern appears at RingTheory/FractionalIdeal/Basic.lean:579 and GradedAlgebra/HomogeneousLocalization.lean:427. No finding.
- `presburger.Structure M` from `[Zero M] [One M] [Add M]`: the typeclass-layer cell. Both precedents deliberately use a def rather than an instance, with the rationale written down: `compatibleRingOfRing` (Ring/Basic.lean:203-218) and `orderStructure` (Order.lean:202-204). I looked for a concrete existing diamond in ultraproducts (Filter.Product has no Add instance), substructures and quotients and found none. So finding 1 is a judgment and advisory, grounded in the module's own TODO of defining the theory.

## Theorems
- `natCast_zero`, `natCast_succ`: on the norms cell, the projection form `NatCast.natCast` appears in 0 Mathlib lemma statements, against the coercion form in `Nat.cast_zero`/`cast_add_one` and elsewhere (finding 4). On the automation cell, `natCast_succ` should not be simp (finding 5).
- `zero_nsmul`, `succ_nsmul`: these shadow root lemma names. I looked for a `protected` convention and found no count (the only namespaced `succ_nsmul` is Tropical/Basic.lean:489, which is unprotected), so I dropped that. `succ_nsmul` being `@[simp]` goes against the root's attributes (Group/Defs.lean:578-584), which is part of finding 5.
- `funMap_zero`/`funMap_one`/`funMap_add`: the `@Structure.funMap presburger M _ _ …` form has precedent: 6 statement uses of `@funMap (L.sum L') …` in Basic.lean/LanguageMap.lean, against 6 typed `abbrev …Func` declarations in ring/graph. The count is mixed, so I dropped the idea of typed abbreviations. They would fall away anyway if finding 1 is adopted.
- `realize_zero`, `realize_one`, `realize_add`, `realize_succ`: these are `rfl`, stated with `Term.realize`, in the same form as the ring's `realize_*` (Ring/Basic.lean:178-199). No finding.
- `realize_natCast`, `realize_nsmul`: `[AddMonoidWithOne M]` could be weakened to `[AddMonoid M] [One M]` for `realize_nsmul`, since the proof never uses NatCast. I dropped this as no case a user needs. The only other change is the proof edit that follows from finding 5.
- `realize_finsum`: the proof cell hit. `Finset.sum_map_toList` (Finset/Defs.lean:392-394) replaces the Nodup/`fold_insert` detour (finding 3, compile). `[AddCommMonoidWithOne M]` is appropriate.

## Location / imports
- The new directory `ModelTheory/Arithmetic/Presburger/` sits beside `ModelTheory/Algebra/Ring/`, which is reasonable. I did not check whether `Mathlib.Algebra.Group.Basic` is redundant given `ModelTheory.Semantics`, because I had no import graph tool. No finding.

## Prose
- The module doc is accurate. The "Main Definitions" list omits `finsum`/`succ`, and the `presburgerFunc` docstring lacks a final period. Both are minor, with no count gathered, so I dropped them. The TODO mentioning `presburger.finsum` is folded into finding 2.

## PR as a whole
- The description states the motivation (#27100) and scopes out the theory, and the PR does one thing. I found no process finding.
