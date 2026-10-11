import json
F = "Mathlib/Algebra/Group/Irreducible/Indecomposable.lean"
img_proof = """  suffices ∀ (f : G →* S),
      v '' baseOf v (invMonoidHom.comp f) ⊆ (invMonoidHom ∘ v) '' baseOf v f by
    apply subset_antisymm (this f)
    replace this := image_mono (f := invMonoidHom) <| this (invMonoidHom.comp f)
    rw [← MonoidHom.comp_assoc, invMonoidHom_comp_invMonoidHom, MonoidHom.id_comp, image_comp,
      ← image_comp invMonoidHom invMonoidHom, ← MonoidHom.coe_comp, invMonoidHom_comp_invMonoidHom,
      ← image_comp] at this
    simpa using this
  clear f
  rintro f g ⟨i, ⟨hi, hi'⟩, rfl⟩
  refine ⟨i⁻¹, ⟨by simpa [hv_inv] using hi, fun j hj k hk hi ↦ ?_⟩, by simp [hv_inv]⟩
  replace hi : v i = v j⁻¹ * v k⁻¹ := by
    rwa [hv_inv, inv_eq_iff_eq_inv, mul_inv, ← hv_inv, ← hv_inv] at hi
  specialize hi' j⁻¹ (by simpa [hv_inv]) k⁻¹ (by simpa [hv_inv]) hi
  aesop"""
block = """@[to_additive]
lemma isMulIndecomposable_id_univ [Subsingleton Mˣ] {x : M} (hx : x ≠ 1) :
    IsMulIndecomposable id univ x ↔ Irreducible x :=
  ⟨fun h ↦ ⟨by simpa, by simpa using h⟩, fun h ↦ by simpa using h.isUnit_or_isUnit⟩

namespace IsMulIndecomposable

@[to_additive]
protected lemma subset (v : ι → M) (s : Set ι) : {i | IsMulIndecomposable v s i} ⊆ s :=
  fun _ hi ↦ hi.1

/-- The "base" of a set of points of a monoid relative to a morphism `f`. -/
@[to_additive /-- The "base" of `v` relative to a morphism `f`.

In the case that `v` is the set of roots of a crystallographic root system, and `S = ℚ`, this is the
base of the root system associated to `f`. -/]
def baseOf [Monoid S] (v : ι → M) (f : M →* S) : Set ι :=
  IsMulIndecomposable v {i | 1 < f (v i)}

@[to_additive]
lemma baseOf_subset_one_lt [Monoid S] (v : ι → M) (f : M →* S) :
    baseOf v f ⊆ {i | 1 < f (v i)} :=
  IsMulIndecomposable.subset _ _

@[to_additive]
lemma image_baseOf_inv_comp_eq [InvolutiveInv ι] [CommGroup S] [IsOrderedMonoid S]
    (v : ι → G) (hv_inv : ∀ i, v i⁻¹ = (v i)⁻¹) (f : G →* S) :
    v '' baseOf v (invMonoidHom.comp f) = (invMonoidHom ∘ v) '' baseOf v f := by
""" + img_proof + """

end IsMulIndecomposable"""
spec = [
 ("subset golf", {"path":F,"declaration_name":"IsMulIndecomposable.subset","new_declaration":"protected lemma IsMulIndecomposable.subset (v : ι → M) (s : Set ι) :\n    {i | IsMulIndecomposable v s i} ⊆ s :=\n  fun _ hi ↦ hi.1"}),
 ("namespace block lines 34-77", {"path":F,"line_start":34,"line_end":77,"replacement":block}),
]
json.dump(spec, open("/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/conventions-dossiers/results/pr_review_v5/probes/model-gap-dev-medium-0.3.0/pr33321/TA1/tmp/ind1.json","w"))
