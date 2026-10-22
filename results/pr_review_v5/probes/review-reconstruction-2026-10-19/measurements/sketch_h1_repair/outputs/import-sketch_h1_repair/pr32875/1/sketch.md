# Sketch: golf of eight proofs

All Lean below is unchecked. Paths are under `base/Mathlib/`; "(recalled)" marks names not seen here.

## 1. What counts as better
- **Choice:** shorter *and* no slower. Report per-declaration elaboration time before/after; drop any rewrite that is noticeably slower.
- **Alternatives:** shortness only, timings informational; speed as the goal, keeping only faster rewrites.
- **References:** context [1] (a few characters shorter is not progress), [2] ("shorter but slower"), [3] (small slow-downs acceptable for `grind`), [4] (10,000-heartbeat threshold).
- **What would decide it:** a maintainer ruling for this series; the sources disagree. Open.

## 2. Scope of the edits
- **Choice:** exactly the eight proofs. No hypothesis, attribute, binder name (`[hι' : Fintype ι']`, `MeasureTheory/Constructions/Pi.lean:446`), declaration order or import changes. Leave the invited golf of `inv_ofNat_num` (`Data/Rat/Lemmas.lean:316-322`) to another batch.
- **Alternatives:** include `inv_ofNat_num`; split order/data/topology from measure/probability; allow reordering where a later lemma gives a one-liner (5, 6).
- **References:** goal brief §3-4; `Data/Rat/Lemmas.lean:317`.
- **What would decide it:** the series' size guideline, not in the folder. Open.

## 3. Technique
- **Choice:** close with one existing lemma or a terminal `simp`/`simpa`; no non-terminal `simp` followed by rigid tactics; `grind` only where neighbours use it and timing allows.
- **Alternatives:** systematic `grind`; fully explicit terms.
- **References:** [1](b) prefers tactic calls to explicit lemma calls; [5] flexible linter; [6] a reverted `grind` golf in kernel files; `Data/Finset/Image.lean:93-100`.
- **What would decide it:** timings (decision 1) and robustness to simp-set changes.

## 4. `Finset.mem_map_equiv` (`Data/Finset/Image.lean:74`)
- **Choice:** `by simp [Equiv.apply_eq_iff_eq_symm_apply]` (via `mem_map`, then `exists_eq_right`).
- **Alternatives:** `by grind` as for `coe_map` (line 100); keep the term, tightened.
- **References:** `mem_map` `@[simp, grind =]` at `Data/Finset/Image.lean:68-70`; `Equiv.apply_eq_iff_eq_symm_apply`, `exists_eq_right` (recalled).
- **What would decide it:** which compiles faster. Open.

## 5. `Rat.inv_intCast_den_of_pos` (`Data/Rat/Lemmas.lean:302`)
- **Choice:** `by simp [ha0.ne', ha0.le]`: simp reaches the `if a = 0 then 1 else a.natAbs` form it proves `inv_intCast_den` with, then `Int.natCast_natAbs`, `abs_eq_self` (recalled).
- **Alternatives:** move `inv_intCast_den` (line 324) above and `rw [inv_intCast_den, if_neg ha0.ne', Int.natAbs_of_nonneg ha0.le]`; `simp [*]` as in `inv_intCast_num_of_pos` (line 296).
- **References:** `Data/Rat/Lemmas.lean:296-297, 309, 324`; the consumer at 309 is unaffected.
- **What would decide it:** whether simp closes it; reordering is excluded by 2.

## 6. `Measure.pi_map_piCongrLeft` (`MeasureTheory/Constructions/Pi.lean:446`)
- **Choice:** reuse the `measurePreserving_piCongrLeft` route in place:
  ```lean
  refine (pi_eq fun s _ ↦ ?_).symm
  rw [MeasurableEquiv.map_apply, MeasurableEquiv.coe_piCongrLeft e,
    Equiv.piCongrLeft_preimage_univ_pi, pi_pi, e.prod_comp fun i ↦ μ i (s i)]
  ```
- **Alternatives:** move it below line 731 as `(measurePreserving_piCongrLeft μ e).map_eq`; derive that lemma's `map_eq` from this one (a ninth proof); deprecate one form (three `map`-form consumers, [11]).
- **References:** `MeasureTheory/Constructions/Pi.lean:702-705, 724-731`.
- **What would decide it:** whether moving declarations is in scope. Open; the inline route needs none.

## 7. `tendsto_of_forall_isClosed_limsup_real_le'` (`MeasureTheory/Measure/Portmanteau.lean:645`)
- **Choice:** keep the reduction and the `eq_or_neBot` split; fold the trailing `≠ ⊤` goal into the rewrite:
  ```lean
  have h1 : ∀ᶠ i in L, (μs i : Measure Ω) F ≤ 1 := .of_forall fun _ ↦ prob_le_one
  have := h F hF
  simp only [Measure.real_def] at this
  rwa [ENNReal.limsup_toReal_eq (b := 1) (by simp) h1, ENNReal.toReal_le_toReal
    (ne_top_of_le_ne_top ENNReal.one_ne_top (limsup_le_of_le (by isBoundedDefault) h1))
    (by finiteness)] at this
  ```
- **Alternatives:** route through the `ℝ≥0` lemma `tendsto_of_forall_isClosed_limsup_le` (line 637); leave unchanged.
- **References:** `MeasureTheory/Measure/Portmanteau.lean:645-659`; `isBoundedDefault` in complete lattices (recalled).
- **What would decide it:** compilation and timing. Open.

## 8. `limsup_finset_sup'` (`Order/LiminfLimsup.lean:1142`)
- **Choice:** keep the `limsup_max` skeleton; replace the explicit `⋂` with `eventually_all_finset`:
  ```lean
  have bdd := isBoundedUnder_le_finset_sup' hs h₂
  have cobdd := isCoboundedUnder_le_finset_sup' hs (let ⟨i, hi⟩ := hs; ⟨i, hi, h₁ i hi⟩)
  refine le_antisymm ((limsup_le_iff cobdd bdd).2 fun b hb ↦ ?_) <| sup'_le hs _ fun i hi ↦
    limsup_le_limsup (.of_forall fun a ↦ le_sup' (F · a) hi) (h₁ i hi) bdd
  filter_upwards [(eventually_all_finset s).2 fun i hi ↦ eventually_lt_of_limsup_lt
    ((le_sup' (fun i ↦ limsup (F i) f) hi).trans_lt hb) (h₂ i hi)] with a ha
  simpa [sup'_lt_iff] using ha
  ```
- **Alternatives:** induction via `Finset.Nonempty.cons_induction` and `limsup_max` (longer bound plumbing); `mem_of_superset` as in `limsup_max`.
- **References:** `Order/LiminfLimsup.lean:1115-1130`; `Filter.eventually_all_finset` (recalled).
- **What would decide it:** open.

## 9. Both `setLIntegral_condKernel_eq_measure_prod` (`Probability/Kernel/Disintegration/Integral.lean:49, 147`)
- **Choice:** the file's disintegration idiom plus the product-set lemma, dropping the `classical`/indicator detour:
  ```lean
  conv_rhs => rw [← κ.disintegrate κ.condKernel]
  rw [Kernel.compProd_apply_prod hs ht]
  -- measure version: ρ.disintegrate ρ.condKernel, then compProd_apply_prod hs ht
  ```
- **Alternatives:** one line `rw [← compProd_apply_prod hs ht, ρ.disintegrate ρ.condKernel]`; derive the measure version from the kernel one.
- **References:** `conv_rhs` idiom at `Probability/Kernel/Disintegration/Integral.lean:46, 143`; [8] `compProd_apply_prod` (context, not in `base/`).
- **What would decide it:** consistency with neighbours versus one line. Open.

## 10. `Metric.exists_lt_mem_ball_of_mem_ball` (`Topology/MetricSpace/Pseudo/Defs.lean:377`)
- **Choice:** term mode, `(exists_between (mem_ball.1 h)).imp fun _ ↦ And.symm`.
- **Alternatives:** `let ⟨ε', h₁, h₂⟩ := exists_between h; ⟨ε', h₂, h₁⟩`; keep the `linarith` midpoint.
- **References:** `exists_between` at `Topology/MetricSpace/Pseudo/Defs.lean:693`; `mem_ball` is `Iff.rfl` (line 351).
- **What would decide it:** open; dropping two `linarith` calls is likely faster.
