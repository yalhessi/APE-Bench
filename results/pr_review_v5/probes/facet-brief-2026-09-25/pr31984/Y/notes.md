# PR #31984 — reasoning notes (condition Y)

## Module doc (`# Convex spaces`, Main definitions, TODO)
- intent: the list matches the three main declarations; it is accurate. norms: it has headings and backticks and follows convention. It does not mention the existing `stdSimplex` (Analysis/Convex/StdSimplex.lean:35–36, "free object in the category of convex spaces"). I folded that into the FiniteProbability library finding rather than a separate prose finding.

## `FiniteProbability` (structure)
- library: `mlgrep` found no existing ConvexSpace or FiniteProbability. `stdSimplex` (Fintype, Set-valued) and `PMF` (ENNReal, pure/bind/map) are the neighbours. Finding: relate it to `stdSimplex` or rename after it (exhibit).
- API: compared with the PMF API (ext, pure_apply, support_pure, bind_apply, pure_bind/bind_pure/bind_bind, map). None of it exists here. Finding (exhibit).
- norms: `UpperCamelCase` for a type is correct. better version: `extends weights : ι →₀ R` is a reasonable encoding and `[LE R] [AddCommMonoid R] [One R]` is already minimal. Dropped.

## `FiniteProbability.single` and its doc comment
- proof, better version: `open Classical in` covers the whole def but only the proof needs it. `Finsupp.single_nonneg` exists (Data/Finsupp/Order.lean:69). Classical usage counts are 2356 against 246. Finding (compile, advisory).
- intent (docstring "point mass"): accurate.

## `FiniteProbability.duple` and its doc comment
- intent: the docstring names weights `x`, `y`, but the parameters are `s`, `t`. Finding (judgment).
- better version: the author's own question (generalise to `i j : ι`) holds with no extra hypothesis. I used it as the fix in the `convexCombo₂` universe finding.
- norms: the name `duple` is unusual, but I found no count to warrant a rename. Dropped.

## `FiniteProbability.comp` and its doc comment
- proof `total`: the four-lemma chain exists (sum_sum_index = to_additive of prod_sum_index at BigOperators/Finsupp/Basic.lean:468, sum_embDomain from :455, Data/Finsupp/SMul.lean:177 sum_smul_index, :610 Finsupp.mul_sum). Finding (compile, to verify by compiling).
- proof `nonneg`: a non-terminal `simp [Finsupp.embDomain]` unfolds the definition, then `bound` runs. `bound` has 0 uses in Algebra/LinearAlgebra and is the only reason for the Tactic.Bound import. Finding (judgment, robustness).
- norms (name): Kernel.comp marginalises (Comp.lean:48), while compProd keeps the pair (CompProd.lean:69, MeasureCompProd.lean:43). This `comp` keeps the Σ-pair. Finding (exhibit).
- better version (universes `κ ι : Type v`): these could be independent, but the class forces them equal, so the redesign finding subsumes this. Dropped.

## `ConvexSpace` (class) and its doc comments
- better version: `ι : Type v` couples the index universe to `M`, and the `ext` axiom is of unknown necessity (the author says so). The basic laws are only `proof_wanted`. Proposed the monad-algebra form (convexCombination on `FiniteProbability R M`, with map/join assoc). Finding (judgment, blocking).
- norms: the field name `ext` has congruence shape. Finsupp.prod_congr/sum_congr (BigOperators/Finsupp/Basic.lean:175) and Finset.prod_congr (Group/Finset/Basic.lean:108) are the precedents. Finding (count).
- typeclass layer: the class has no instances and no parents, so it has no diamond risk. The only relevant cell was the missing motivating instance (Module → ConvexSpace), which gets an advisory judgment finding.
- hypotheses: `IsStrictOrderedRing` is stronger than any proof uses, and stdSimplex uses `IsOrderedRing`. Finding (compile). Binder order `[PartialOrder R] [Semiring R]` against the 186:1 library convention. Finding (count).

## `open ConvexSpace`, `variable` command
- This `variable` line has the same order and strictness issues as above, and both findings name it. `variable {R M}` with untyped binders is what lets the universe of `M` be fixed to 0 by the body of `convexCombo₂`.

## `convexCombo₂`
- better version: the body instantiates `ι := Fin 2 : Type`, so `v := 0`. The def and the `proof_wanted`s exist only for `M : Type`. Finding (judgment, blocking; check with `#check @convexCombo₂`).
- norms: "combo" has precedent in lemma names (Convex.combo_self etc., 17 hits), so I dropped the naming concern. Proof arguments `hs ht h` match Mathlib's `Convex` a/b convention. Dropped.
- library: `AffineMap.lineMap` (LinearAlgebra/AffineSpace/AffineMap.lean:482) is the vector-space analogue, and the TODO already plans to relate the two. No finding.

## `proof_wanted` lemmas (convexCombo₂_zero/_one/_same)
- These are used as evidence in the class-design finding: the axioms were not validated against the binary laws. `proof_wanted` itself is acceptable in Mathlib. No separate finding.

## Imports / location / `Mathlib.lean`
- `Mathlib.lean` import line: alphabetical and correct.
- `Mathlib.Data.ZMod.Defs` supplies the ring structure on `Fin n`, plausibly needed by `grind` or numerals in `duple`. I could not warrant removing it. Dropped.
- `Mathlib.Tactic.Bound` is covered by the `comp.nonneg` finding.
- Location: `LinearAlgebra/` against `Analysis/Convex/` (StdSimplex, Combination). The file is purely algebraic and `lineMap` lives in `LinearAlgebra/AffineSpace`, so the placement is defensible. No present problem. Dropped.

## Sections / namespaces / `@[expose] public section` attribute / `noncomputable section`
- Standard module-system boilerplate with nothing to check against. No findings.

## PR as a whole
- process: the description is empty, AI provenance appears only in a code comment, and open questions sit in source comments. Finding (judgment, advisory). Splitting is not needed; it is one coherent definition PR.
- Removed/renamed declarations: none.
