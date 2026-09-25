# PR 36275: how each target was reviewed

## Mathlib.lean
- Checked that the new import sits in sorted position (between `ExistsRamified` and `FinitePlaces`). Nothing to ask.

## Mathlib/NumberTheory/NumberField/AdeleRing.lean (notation `𝔸ᶠ[K]` removed)
- The notation moves to the new file, still under `namespace AdeleRing`, so `open scoped AdeleRing` keeps working wherever the new file is imported. mlgrep found no other use of `𝔸ᶠ[K]` at the base.
- A file that imports only AdeleRing.lean loses the notation. I decided the move was acceptable (the new file cannot import AdeleRing.lean without inverting the hierarchy) and asked for nothing.

## Mathlib/NumberTheory/NumberField/Completion/FinitePlace.lean
- Imports: three existing imports are removed with no connection to the feature, and a double blank line is left behind. Filed as scope/style.
- `two_le_absNorm_nnreal`: the proof (`mod_cast one_lt_absNorm`) is fine. Its siblings all have docstrings and it does not, so I filed a documentation finding. A ℕ version is trivial, so I did not ask for one.
- `FinitePlace.two_le_norm_of_one_lt_norm`: it sits after `variable (K)` (line 278), so `K` is explicit although `x` determines it, and it shadows the section `v`. It belongs next to `FinitePlace.norm_def`. Its proof really establishes `absNorm ≤ ‖x‖`, so I asked for that generalization. No existing lemma covers it (mlgrep came back empty).

## Mathlib/NumberTheory/NumberField/FiniteAdeleRing.lean (new)
- Found a close precedent in InfiniteAdeleRing.lean:110-130: a `Norm K∞` instance with a docstring, `norm_def`, `norm_eq_zero_of_not_isUnit`, and `coe_norm_eq_abs_norm (x : K)` stated through `algebraMap` with a docstring. Because of this precedent, a Norm instance that is not a norm is acceptable here, so I did not flag it. I used the precedent for the docstring, product-formula-statement and API-shape findings.
- `mulSupport_finite`: this spelling was deprecated in FinitePlace.lean (2026-03-03) in favour of `HasFiniteMulSupport`, and `tprod_eq_finprod` takes `HasFiniteMulSupport`. Marked blocking.
- Private lemmas: their names are swapped relative to their sets. The first one duplicates `Set.Finite.multipliable ... |>.hasProd`. I read the rest of the `hasProd_zero_subset_…` proof (a `2^card` lower bound, then inverse tends to 0) and found it mathematically sound; my only request there is a whitespace nit.
- `hasProd_zero_of_not_isUnit`: the three-way split into `>1`, `=1` and `<1` is sound. The only change asked here is dropping the first private helper.
- `tprod_norm_of_isUnit` / `tprod_norm_of_unit` / `tprod_eq_zero_of_not_isUnit` / `norm_def_unit` / `norm_eq_zero_of_not_isUnit`: redundant layers, so I asked to keep only the norm-level API. `norm_def` (rfl) is fine.
- `.1` against `x v`: the file mixes the subtype projection with the DFunLike coercion. I asked for `x v` and coercions throughout.
- `unitEmbedding_norm_*`: the LHS is not in simp-normal form (`unitEmbedding_apply` is simp), and `_apply` is a misnomer. The final product formula also holds for `x = 0`, so I asked for it to be stated as `∀ x : K` via `algebraMap`, matching the infinite version. The reindexing proof should use `finprod_comp_equiv`, as ProductFormula.lean:48 does.
- Generality: nothing except the product formula needs `𝓞 K`. The FinitePlace norm API holds for general `R` with `[Ring.HasFiniteQuotients R] [Infinite R]`, and AdeleRing is deliberately general in `R`, so I filed a generalization finding.
- Module docstring: it wrongly describes the file as being about a general Dedekind `R`, and it has no main results section. Imports: redundant and unsorted.

## Mathlib/RingTheory/DedekindDomain/FiniteAdeleRing.lean
- `cofinite_mem_adicCompletionIntegers`: duplicates `RestrictedProduct.eventually` (x.2), and its name departs from the `eventually_` convention. Asked to rename or inline it.
- `finite_valued_one_lt`: the statement and proof are fine, and the name is consistent with `unitsEquiv_finite_valued_eq_one`. Nothing to ask.
- The `variable {R K}` / `variable (R K)` bracketing restores the original binder state before `algebraMap`. Checked; nothing to ask.

## Mathlib/Topology/Algebra/Valued/NormedValued.lean
- `norm_eq_one_iff`: correct and not a duplicate. mlgrep found no `Valued` `norm_eq_one_iff`, and `Valuation.restrict_eq_one_iff` exists at RingTheory/Valuation/Basic.lean:543. All six siblings are `@[simp]` with one shared proof shape, so I asked to add `@[simp]` and align the proof.
