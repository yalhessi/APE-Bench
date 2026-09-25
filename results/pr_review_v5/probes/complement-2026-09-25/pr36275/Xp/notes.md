# PR #36275 review notes

## Mathlib.lean
- Adds one import for the new file, in sorted position. Nothing to ask.

## Mathlib/NumberTheory/NumberField/AdeleRing.lean (notation `𝔸ᶠ[K]` removed)
- content_search for `𝔸ᶠ[` across Mathlib: only the Dedekind file and the new file use it, so nothing in Mathlib breaks.
- Downstream users of `open scoped NumberField.AdeleRing` lose `𝔸ᶠ[K]` unless they import the new file. I could not show that importing the new file from AdeleRing.lean is possible, so I asked for nothing.

## Mathlib/NumberTheory/NumberField/Completion/FinitePlace.lean
- Header: three unrelated imports are dropped and a double blank line is left (file_read lines 8-19). Advisory scope/style ask.
- `two_le_absNorm_nnreal`: the proof is correct (`mod_cast` from `1 < n` in ℕ). It is the only undocumented lemma in the `absNorm` group: documentation ask.
- `FinitePlace.two_le_norm_of_one_lt_norm`: `variable (K)` from line 278 makes K explicit. Confirmed by compiling `two_le_norm_of_one_lt_norm K y h`. `variable {K} in` compiles, and the call becomes `... y h`. The proof itself compiles, so I made no golf ask. A generalization to `absNorm v ≤ ‖x‖` is possible, but I did not propose it.

## Mathlib/NumberTheory/NumberField/FiniteAdeleRing.lean (new)
- Module doc mentions a nonexistent `R` and lists no main results: documentation ask.
- `mulSupport_finite`: the library has `Function.HasFiniteMulSupport` (declaration_search), which `tprod_eq_finprod` takes and `FinitePlace.hasFiniteMulSupport` uses. Restate and rename (naming_norm was unresolved, so this rests on the sibling evidence).
- Private helpers: their names are swapped relative to the sets they range over (naming ask). The term-mode `have` chain and the double space call for a style ask. I did not try to golf the `Fintype`/`finprod_eq_prod_of_fintype` helper.
- `hasProd_zero_of_not_isUnit`: the logic reads sound. The decomposition into `<1`, `=1` and `>1` parts is fine. No separate ask beyond the `x.1 v` vs `x v` consistency.
- `tprod_norm_of_isUnit` / `tprod_norm_of_unit` / `norm_def_unit` / `tprod_eq_zero_of_not_isUnit` / `norm_eq_zero_of_not_isUnit`: the same fact is stated two or three times (`norm_def` is rfl). One duplication ask, plus a naming ask for `norm_def_unit` (not a `_def` lemma).
- `Norm` instance: precedent_search surfaced PR #12249, and content_search confirmed that `mixedEmbedding.norm` is a named `→*₀ ℝ` def, not an instance. Advisory ask to use a def.
- `unitEmbedding_norm_apply`: a thin wrapper over `norm_def_unit`. Nothing separate to ask.
- `unitEmbedding_norm_apply_eq_finprod_finitePlace`: `finprod_comp_equiv equivHeightOneSpectrum.symm` (the idiom ProductFormula.lean uses) replaces the manual reindexing. The first attempt failed on higher-order unification; supplying `(f := fun w : FinitePlace K ↦ w x)` introduced no errors.
- `unitEmbedding_norm_eq_inv_abs_norm`: the proof is fine. I proposed an `algebraMap` form for `x ≠ 0`, which compiled as a one-liner. The unconditional form fails (there is no `Nontrivial 𝔸ᶠ[K]` instance, and `Algebra.norm` is only `→*`), so I did not propose it.
- Imports: `Topology.Algebra.Valued.NormedValued` is redundant (FinitePlace re-exports it publicly). I judged this too minor to ask.
- Compile note: lean_verify_edit resolves imports against base build products, so the errors marked "already in the file" (unknown `norm_eq_one_iff`, `finite_valued_one_lt`, `two_le_norm_of_one_lt_norm`) are artifacts. The tool itself says the PR compiles.

## Mathlib/RingTheory/DedekindDomain/FiniteAdeleRing.lean
- `cofinite_mem_adicCompletionIntegers`: `RestrictedProduct.eventually` already states this (content_search, Basic.lean:124). Asked for the `eventually_` naming and a docstring. naming_norm was unresolved.
- `finite_valued_one_lt`: the name matches the sibling `unitsEquiv_finite_valued_eq_one`, and the proof is a one-line `simpa`. Nothing to ask. The `variable {R K}` / `variable (R K)` toggling is ugly, but not worth a separate ask.

## Mathlib/Topology/Algebra/Valued/NormedValued.lean
- `norm_eq_one_iff`: the statement is correct. All six siblings are `@[simp]` and this one is not. `@[simp]` plus `simp only [le_antisymm_iff, norm_le_one_iff, one_le_norm_iff]` compiled successfully, so I made one style/golf ask.
