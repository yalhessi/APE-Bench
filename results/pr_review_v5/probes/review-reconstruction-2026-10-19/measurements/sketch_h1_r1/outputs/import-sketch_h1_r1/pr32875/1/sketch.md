# Sketch: golfing eight proofs

All Lean below is unchecked. Paths are under `base/Mathlib/`.

## 1. Acceptance criterion
- **Choice:** keep a new proof only if it is shorter *and* not measurably slower; the description gives per-declaration elaboration time before/after. Prefer replacing explicit lemma plumbing by one library lemma or one terminal tactic.
- **Alternatives:** brevity alone (small slow-downs tolerated); speed alone.
- **References:** decision_context [1]-[4] (Buzzard: speed or fewer explicit calls; Morrison: tolerate small slow-downs).
- **What would decide it:** open; maintainers disagree, so the timing table is what a reviewer weighs.

## 2. Scope and form
- **Choice:** replace each proof whole; statements, attributes (`@[simp 1100]`), docstrings, comments and declaration order untouched; no new lemmas, imports, aliases or deprecations; neighbours (`inv_ofNat_num`, `measurePreserving_piCongrLeft`) left to later PRs.
- **Alternatives:** take the invited golf at `Data/Rat/Lemmas.lean:317`; make `measurePreserving_piCongrLeft`'s `map_eq` reuse decision 5's lemma.
- **References:** `Data/Rat/Lemmas.lean:316-322`; consumers of the `map` form (context [11]).
- **What would decide it:** the series' size limit; open otherwise.

## 3. `Finset.mem_map_equiv`
- **Choice:** `by simp [Equiv.apply_eq_iff_eq_symm_apply]` (`mem_map` unfolds, then `exists_eq_right`).
- **Alternatives:** `by grind`; `by nth_rw 1 [← f.apply_symm_apply b]; exact mem_map' f.toEmbedding`.
- **References:** `Data/Finset/Image.lean:68-69` (`mem_map`, `grind =`), `:82` (`mem_map'`), `:93-94` (bare `grind` neighbours); `Equiv.apply_eq_iff_eq_symm_apply` recalled.
- **What would decide it:** which closes it at all, then timing.

## 4. `Rat.inv_intCast_den_of_pos`
- **Choice:** `by simp [ha0.ne', ha0.le]`, mirroring `inv_intCast_num_of_pos`'s `simp [*]`; simp reaches `if a = 0 then 1 else |a|`.
- **Alternatives:** move it below `inv_intCast_den` and `rw [inv_intCast_den, if_neg ha0.ne', Int.natAbs_of_nonneg ha0.le]`.
- **References:** `Data/Rat/Lemmas.lean:296-297`, `:302`, `:324`; consumer `:308-310` must still rewrite with it.
- **What would decide it:** timing; reordering violates decision 2.

## 5. `Measure.pi_map_piCongrLeft`
- **Choice:** the route already proving the same fact:
  ```
  refine (pi_eq fun s _ ↦ ?_).symm
  rw [MeasurableEquiv.map_apply, MeasurableEquiv.coe_piCongrLeft,
    Equiv.piCongrLeft_preimage_univ_pi, pi_pi, e.prod_comp fun i ↦ μ i (s i)]
  ```
- **Alternatives:** move below and use `(measurePreserving_piCongrLeft μ e).map_eq`; keep the `map` statement either way, it is rewritten right to left downstream.
- **References:** `MeasureTheory/Constructions/Pi.lean:446-466`, `:724-731`.
- **What would decide it:** file order; duplication versus moving.

## 6. `tendsto_of_forall_isClosed_limsup_real_le'`
- **Choice:** keep the reduction to the `ENNReal` version and the `L = ⊥` split, but rewrite the goal rather than `h` (removing `simp only … at h; rwa`) and close finiteness in one term:
  ```
  have h1 : ∀ᶠ i in L, (μs i : Measure Ω) F ≤ 1 := .of_forall fun _ ↦ prob_le_one
  rw [← ENNReal.toReal_le_toReal (ne_top_of_le_ne_top one_ne_top
      (limsup_le_of_le (by isBoundedDefault) h1)) (by finiteness),
    ← ENNReal.limsup_toReal_eq one_ne_top h1]
  exact h F hF
  ```
- **Alternatives:** go through the `ℝ≥0` version `tendsto_of_forall_isClosed_limsup_le` with a monotone-limsup transfer.
- **References:** `MeasureTheory/Measure/Portmanteau.lean:614-618`, `:637-658`; flexible linter (context [5]).
- **What would decide it:** whether `exact` sees `.real` through its definition; timing.

## 7. `limsup_finset_sup'`
- **Choice:** keep the antisymmetry of `limsup_max`; obtain the cobound by `hs.imp fun i hi ↦ ⟨hi, h₁ i hi⟩`; close the eventual bound with `simp only [sup'_lt_iff, eventually_all_finset]` then `exact fun i hi ↦ eventually_lt_of_limsup_lt ((le_sup' _ hi).trans_lt hb) (h₂ i hi)`; reverse direction `sup'_le hs _ fun i hi ↦ limsup_le_limsup (.of_forall fun a ↦ le_sup' (F · a) hi) (h₁ i hi) bddsup`.
- **Alternatives:** `mem_of_superset` over a `⋂` as now; induction on `s` via `limsup_max` (needs bounds on partial sups).
- **References:** `Order/LiminfLimsup.lean:1115-1130`, `:1142-1167`; `Filter.eventually_all_finset` recalled.
- **What would decide it:** that `eventually_all_finset` is imported here.

## 8. The two `setLIntegral_condKernel_eq_measure_prod`
- **Choice:** the file's own pattern plus the product-set lemma:
  `conv_rhs => rw [← κ.disintegrate κ.condKernel]` then `rw [Kernel.compProd_apply_prod hs ht]`; measure version with `ρ.disintegrate` and `compProd_apply_prod hs ht`.
- **Alternatives:** `rw [← Kernel.compProd_apply_prod hs ht, κ.disintegrate]` (higher-order pattern, fragile); keep the indicator argument.
- **References:** `Probability/Kernel/Disintegration/Integral.lean:46`, `:49-61`, `:143`, `:147-159`; `compProd_apply_prod` (context [8]).
- **What would decide it:** none needed; the lemma states exactly the goal.

## 9. `Metric.exists_lt_mem_ball_of_mem_ball`
- **Choice:** term proof `(exists_between h).imp fun _ ↦ And.symm` (membership is `dist x y < ε` by `Iff.rfl`).
- **Alternatives:** `let ⟨ε', h₁, h₂⟩ := exists_between h; ⟨ε', h₂, h₁⟩`; keep `linarith` with midpoint.
- **References:** `Topology/MetricSpace/Pseudo/Defs.lean:351-352`, `:377-379`, `:693`.
- **What would decide it:** whether unfolding `ball` elaborates; readability.
