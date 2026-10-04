/-
Copyright (c) 2023 Rémy Degenne. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Rémy Degenne, Etienne Marion
-/
import Mathlib.Probability.Kernel.Composition.MeasureComp
import Mathlib.Probability.Kernel.MeasurableIntegral

/-!
# Bochner integral of a function against the composition and the composition-products of two kernels

We prove properties of the composition and the composition-product of two kernels.

If `κ` is a kernel from `α` to `β` and `η` is a kernel from `β` to `γ`, we can form their
composition `η ∘ₖ κ : Kernel α γ`. We proved in `ProbabilityTheory.Kernel.lintegral_comp` that it
verifies `∫⁻ c, f c ∂((η ∘ₖ κ) a) = ∫⁻ b, ∫⁻ c, f c ∂(η b) ∂(κ a)`. In this file, we
prove the same equality for the Bochner integral.

If `κ` is an s-finite kernel from `α` to `β` and `η` is an s-finite kernel from `α × β` to `γ`,
we can form their composition-product `κ ⊗ₖ η : Kernel α (β × γ)`.
We proved in `ProbabilityTheory.Kernel.lintegral_compProd` that it
verifies `∫⁻ bc, f bc ∂((κ ⊗ₖ η) a) = ∫⁻ b, ∫⁻ c, f (b, c) ∂(η (a, b)) ∂(κ a)`. In this file, we
prove the same equality for the Bochner integral.

## Main statements

* `ProbabilityTheory.integral_compProd`: the integral against the composition-product is
  `∫ z, f z ∂((κ ⊗ₖ η) a) = ∫ x, ∫ y, f (x, y) ∂(η (a, x)) ∂(κ a)`.

* `ProbabilityTheory.integral_comp`: the integral against the composition is
  `∫⁻ z, f z ∂((η ∘ₖ κ) a) = ∫⁻ x, ∫⁻ y, f y ∂(η x) ∂(κ a)`.

## Implementation details

This file is to a large extent a copy of part of `Mathlib/MeasureTheory/Integral/Prod.lean`.
The product of two measures is a particular case of composition-product of kernels and
it turns out that once the measurability of the Lebesgue integral of a kernel is proved,
almost all proofs about integrals against products of measures extend with minimal modifications
to the composition-product of two kernels.

The composition of kernels can also be expressed easily with the composition-product and therefore
the proofs about the composition are only simplified versions of the ones for the
composition-product. However it is necessary to do all the proofs once again because the
composition-product requires s-finiteness while the composition does not.
-/


noncomputable section

open Set Function Real ENNReal MeasureTheory Filter ProbabilityTheory ProbabilityTheory.Kernel
open scoped Topology ENNReal MeasureTheory

variable {α β γ E : Type*} {mα : MeasurableSpace α} {mβ : MeasurableSpace β}
  {mγ : MeasurableSpace γ} [NormedAddCommGroup E] {a : α}

namespace ProbabilityTheory

section compProd

variable {κ : Kernel α β} [IsSFiniteKernel κ] {η : Kernel (α × β) γ} [IsSFiniteKernel η]

theorem hasFiniteIntegral_prodMk_left (a : α) {s : Set (β × γ)} (h2s : (κ ⊗ₖ η) a s ≠ ∞) :
    HasFiniteIntegral (fun b => (η (a, b)).real (Prod.mk b ⁻¹' s)) (κ a) := by
  let t := toMeasurable ((κ ⊗ₖ η) a) s
  simp_rw [hasFiniteIntegral_iff_enorm, measureReal_def, enorm_eq_ofReal toReal_nonneg]
  calc
    ∫⁻ b, ENNReal.ofReal (η (a, b) (Prod.mk b ⁻¹' s)).toReal ∂κ a
    _ ≤ ∫⁻ b, η (a, b) (Prod.mk b ⁻¹' t) ∂κ a := by
      refine lintegral_mono_ae ?_
      filter_upwards [ae_kernel_lt_top a h2s] with b hb
      rw [ofReal_toReal hb.ne]
      exact measure_mono (preimage_mono (subset_toMeasurable _ _))
    _ ≤ (κ ⊗ₖ η) a t := le_compProd_apply _ _ _ _
    _ = (κ ⊗ₖ η) a s := measure_toMeasurable s
    _ < ⊤ := h2s.lt_top

@[deprecated (since := "2025-03-05")]
alias hasFiniteIntegral_prod_mk_left := hasFiniteIntegral_prodMk_left

theorem integrable_kernel_prodMk_left (a : α) {s : Set (β × γ)} (hs : MeasurableSet s)
    (h2s : (κ ⊗ₖ η) a s ≠ ∞) : Integrable (fun b => (η (a, b)).real (Prod.mk b ⁻¹' s)) (κ a) := by
  constructor
  · exact (measurable_kernel_prodMk_left' hs a).ennreal_toReal.aestronglyMeasurable
  · exact hasFiniteIntegral_prodMk_left a h2s

@[deprecated (since := "2025-03-05")]
alias integrable_kernel_prod_mk_left := integrable_kernel_prodMk_left

theorem _root_.MeasureTheory.AEStronglyMeasurable.integral_kernel_compProd [NormedSpace ℝ E]
    ⦃f : β × γ → E⦄ (hf : AEStronglyMeasurable f ((κ ⊗ₖ η) a)) :
    AEStronglyMeasurable (fun x => ∫ y, f (x, y) ∂η (a, x)) (κ a) :=
  ⟨fun x => ∫ y, hf.mk f (x, y) ∂η (a, x), hf.stronglyMeasurable_mk.integral_kernel_prod_right'', by
    filter_upwards [ae_ae_of_ae_compProd hf.ae_eq_mk] with _ hx using integral_congr_ae hx⟩

theorem _root_.MeasureTheory.AEStronglyMeasurable.compProd_mk_left {δ : Type*} [TopologicalSpace δ]
    {f : β × γ → δ} (hf : AEStronglyMeasurable f ((κ ⊗ₖ η) a)) :
    ∀ᵐ x ∂κ a, AEStronglyMeasurable (fun y => f (x, y)) (η (a, x)) := by
  filter_upwards [ae_ae_of_ae_compProd hf.ae_eq_mk] with x hx using
    ⟨fun y => hf.mk f (x, y), hf.stronglyMeasurable_mk.comp_measurable measurable_prodMk_left, hx⟩

/-! ### Integrability -/


theorem hasFiniteIntegral_compProd_iff ⦃f : β × γ → E⦄ (h1f : StronglyMeasurable f) :
    HasFiniteIntegral f ((κ ⊗ₖ η) a) ↔
      (∀ᵐ x ∂κ a, HasFiniteIntegral (fun y => f (x, y)) (η (a, x))) ∧
        HasFiniteIntegral (fun x => ∫ y, ‖f (x, y)‖ ∂η (a, x)) (κ a) := by
  simp only [hasFiniteIntegral_iff_enorm]
  rw [lintegral_compProd _ _ _ h1f.enorm]
  have : ∀ x, ∀ᵐ y ∂η (a, x), 0 ≤ ‖f (x, y)‖ := fun x => Eventually.of_forall fun y => norm_nonneg _
  simp_rw [integral_eq_lintegral_of_nonneg_ae (this _)
      (h1f.norm.comp_measurable measurable_prodMk_left).aestronglyMeasurable,
    enorm_eq_ofReal toReal_nonneg, ofReal_norm_eq_enorm]
  have : ∀ {p q r : Prop} (_ : r → p), (r ↔ p ∧ q) ↔ p → (r ↔ q) := fun {p q r} h1 => by
    rw [← and_congr_right_iff, and_iff_right_of_imp h1]
  rw [this]
  · intro h2f; rw [lintegral_congr_ae]
    filter_upwards [h2f] with x hx
    rw [ofReal_toReal]; finiteness
  · intro h2f; refine ae_lt_top ?_ h2f.ne; exact h1f.enorm.lintegral_kernel_prod_right''

theorem hasFiniteIntegral_compProd_iff' ⦃f : β × γ → E⦄
    (h1f : AEStronglyMeasurable f ((κ ⊗ₖ η) a)) :
    HasFiniteIntegral f ((κ ⊗ₖ η) a) ↔
      (∀ᵐ x ∂κ a, HasFiniteIntegral (fun y => f (x, y)) (η (a, x))) ∧
        HasFiniteIntegral (fun x => ∫ y, ‖f (x, y)‖ ∂η (a, x)) (κ a) := by
  rw [hasFiniteIntegral_congr h1f.ae_eq_mk,
    hasFiniteIntegral_compProd_iff h1f.stronglyMeasurable_mk]
  apply and_congr
  · apply eventually_congr
    filter_upwards [ae_ae_of_ae_compProd h1f.ae_eq_mk.symm] with x hx using
      hasFiniteIntegral_congr hx
  · apply hasFiniteIntegral_congr
    filter_upwards [ae_ae_of_ae_compProd h1f.ae_eq_mk.symm] with _ hx using
      integral_congr_ae (EventuallyEq.fun_comp hx _)

theorem integrable_compProd_iff ⦃f : β × γ → E⦄ (hf : AEStronglyMeasurable f ((κ ⊗ₖ η) a)) :
    Integrable f ((κ ⊗ₖ η) a) ↔
      (∀ᵐ x ∂κ a, Integrable (fun y => f (x, y)) (η (a, x))) ∧
