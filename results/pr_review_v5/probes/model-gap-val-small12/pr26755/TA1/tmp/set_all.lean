/-! ### `0`/`1` as sets -/

section One

variable [One α] {s : Set α} {a : α}

/-- The set `1 : Set α` is defined as `{1}` in locale `Pointwise`. -/
@[to_additive "The set `0 : Set α` is defined as `{0}` in locale `Pointwise`."]
protected def one : One (Set α) where one := {1}

scoped[Pointwise] attribute [instance] Set.one Set.zero

open Pointwise

-- TODO: This would be a good simp lemma scoped to `Pointwise`, but it seems `@[simp]` can't be
-- scoped
@[to_additive]
theorem singleton_one : ({1} : Set α) = 1 :=
  rfl

@[to_additive (attr := simp)]
theorem mem_one : a ∈ (1 : Set α) ↔ a = 1 :=
  Iff.rfl

@[to_additive]
theorem one_mem_one : (1 : α) ∈ (1 : Set α) :=
  Eq.refl _

@[to_additive (attr := simp)]
theorem one_subset : 1 ⊆ s ↔ (1 : α) ∈ s :=
  singleton_subset_iff

@[to_additive (attr := simp)]
theorem one_nonempty : (1 : Set α).Nonempty :=
  ⟨1, rfl⟩

@[to_additive (attr := simp)]
theorem image_one {f : α → β} : f '' 1 = {f 1} :=
  image_singleton

@[to_additive]
theorem subset_one_iff_eq : s ⊆ 1 ↔ s = ∅ ∨ s = 1 :=
  subset_singleton_iff_eq

@[to_additive]
theorem Nonempty.subset_one_iff (h : s.Nonempty) : s ⊆ 1 ↔ s = 1 :=
  h.subset_singleton_iff

/-- The singleton operation as a `OneHom`. -/
@[to_additive "The singleton operation as a `ZeroHom`."]
def singletonOneHom : OneHom α (Set α) where
  toFun := singleton
  map_one' := singleton_one

@[to_additive (attr := simp)]
theorem coe_singletonOneHom : (singletonOneHom : α → Set α) = singleton :=
  rfl

@[to_additive] lemma image_op_one : (1 : Set α).image op = 1 := image_singleton

@[to_additive (attr := simp) zero_prod_zero]
lemma one_prod_one [One β] : (1 ×ˢ 1 : Set (α × β)) = 1 := by ext; simp [Prod.ext_iff]

@[deprecated (since := "2025-03-11")]
alias zero_sum_zero := zero_prod_zero

end One

/-! ### Set negation/inversion -/


section Inv

/-- The pointwise inversion of set `s⁻¹` is defined as `{x | x⁻¹ ∈ s}` in locale `Pointwise`. It is
equal to `{x⁻¹ | x ∈ s}`, see `Set.image_inv_eq_inv`. -/
@[to_additive
      "The pointwise negation of set `-s` is defined as `{x | -x ∈ s}` in locale `Pointwise`.
      It is equal to `{-x | x ∈ s}`, see `Set.image_neg_eq_neg`."]
protected def inv [Inv α] : Inv (Set α) :=
  ⟨preimage Inv.inv⟩

scoped[Pointwise] attribute [instance] Set.inv Set.neg

open Pointwise

section Inv

variable {ι : Sort*} [Inv α] {s t : Set α} {a : α}

@[to_additive (attr := simp)]
theorem mem_inv : a ∈ s⁻¹ ↔ a⁻¹ ∈ s :=
  Iff.rfl

@[to_additive (attr := simp)]
theorem inv_preimage : Inv.inv ⁻¹' s = s⁻¹ :=
  rfl

@[to_additive (attr := simp)]
theorem inv_empty : (∅ : Set α)⁻¹ = ∅ :=
  rfl

@[to_additive (attr := simp)]
theorem inv_univ : (univ : Set α)⁻¹ = univ :=
  rfl

@[to_additive (attr := simp)]
theorem inter_inv : (s ∩ t)⁻¹ = s⁻¹ ∩ t⁻¹ :=
  preimage_inter

@[to_additive (attr := simp)]
theorem union_inv : (s ∪ t)⁻¹ = s⁻¹ ∪ t⁻¹ :=
  preimage_union

@[to_additive (attr := simp)]
theorem compl_inv : sᶜ⁻¹ = s⁻¹ᶜ :=
  preimage_compl

@[to_additive (attr := simp) neg_prod]
lemma inv_prod [Inv β] (s : Set α) (t : Set β) : (s ×ˢ t)⁻¹ = s⁻¹ ×ˢ t⁻¹ := rfl

@[deprecated (since := "2025-03-11")]
alias neg_sum := neg_prod

end Inv

section InvolutiveInv

variable [InvolutiveInv α] {s t : Set α} {a : α}

@[to_additive]
theorem inv_mem_inv : a⁻¹ ∈ s⁻¹ ↔ a ∈ s := by simp only [mem_inv, inv_inv]

@[to_additive (attr := simp)]
theorem nonempty_inv : s⁻¹.Nonempty ↔ s.Nonempty :=
  inv_involutive.surjective.nonempty_preimage

@[to_additive]
theorem Nonempty.inv (h : s.Nonempty) : s⁻¹.Nonempty :=
  nonempty_inv.2 h

@[to_additive (attr := simp)]
theorem image_inv_eq_inv : (·⁻¹) '' s = s⁻¹ :=
  congr_fun (image_eq_preimage_of_inverse inv_involutive.leftInverse inv_involutive.rightInverse) _

@[to_additive (attr := simp)]
theorem inv_eq_empty : s⁻¹ = ∅ ↔ s = ∅ := by
  rw [← image_inv_eq_inv, image_eq_empty]

@[to_additive (attr := simp)]
instance involutiveInv : InvolutiveInv (Set α) where
  inv := Inv.inv
  inv_inv s := by simp only [← inv_preimage, preimage_preimage, inv_inv, preimage_id']

@[to_additive (attr := simp)]
theorem inv_subset_inv : s⁻¹ ⊆ t⁻¹ ↔ s ⊆ t :=
  (Equiv.inv α).surjective.preimage_subset_preimage_iff

@[to_additive]
theorem inv_subset : s⁻¹ ⊆ t ↔ s ⊆ t⁻¹ := by rw [← inv_subset_inv, inv_inv]

@[to_additive (attr := simp)]
theorem inv_singleton (a : α) : ({a} : Set α)⁻¹ = {a⁻¹} := by
  rw [← image_inv_eq_inv, image_singleton]

@[to_additive (attr := simp)]
theorem inv_insert (a : α) (s : Set α) : (insert a s)⁻¹ = insert a⁻¹ s⁻¹ := by
  rw [insert_eq, union_inv, inv_singleton, insert_eq]

@[to_additive]
theorem inv_range {ι : Sort*} {f : ι → α} : (range f)⁻¹ = range fun i => (f i)⁻¹ := by
  rw [← image_inv_eq_inv]
  exact (range_comp ..).symm

open MulOpposite

@[to_additive]
theorem image_op_inv : op '' s⁻¹ = (op '' s)⁻¹ := by
  simp_rw [← image_inv_eq_inv, Function.Semiconj.set_image op_inv s]

end InvolutiveInv

end Inv

open Pointwise

/-! ### Set addition/multiplication -/


section Mul

variable {ι : Sort*} {κ : ι → Sort*} [Mul α] {s s₁ s₂ t t₁ t₂ u : Set α} {a b : α}

/-- The pointwise multiplication of sets `s * t` and `t` is defined as `{x * y | x ∈ s, y ∈ t}` in
locale `Pointwise`. -/
@[to_additive
      "The pointwise addition of sets `s + t` is defined as `{x + y | x ∈ s, y ∈ t}` in locale
      `Pointwise`."]
protected def mul : Mul (Set α) :=
  ⟨image2 (· * ·)⟩

scoped[Pointwise] attribute [instance] Set.mul Set.add

@[to_additive (attr := simp)]
theorem image2_mul : image2 (· * ·) s t = s * t :=
  rfl

@[to_additive]
theorem mem_mul : a ∈ s * t ↔ ∃ x ∈ s, ∃ y ∈ t, x * y = a :=
  Iff.rfl

@[to_additive]
theorem mul_mem_mul : a ∈ s → b ∈ t → a * b ∈ s * t :=
  mem_image2_of_mem

@[to_additive add_image_prod]
theorem image_mul_prod : (fun x : α × α => x.fst * x.snd) '' s ×ˢ t = s * t :=
  image_prod _

@[to_additive (attr := simp)]
theorem empty_mul : ∅ * s = ∅ :=
  image2_empty_left

@[to_additive (attr := simp)]
theorem mul_empty : s * ∅ = ∅ :=
  image2_empty_right

@[to_additive (attr := simp)]
theorem mul_eq_empty : s * t = ∅ ↔ s = ∅ ∨ t = ∅ :=
  image2_eq_empty_iff

@[to_additive (attr := simp)]
theorem mul_nonempty : (s * t).Nonempty ↔ s.Nonempty ∧ t.Nonempty :=
  image2_nonempty_iff

@[to_additive]
theorem Nonempty.mul : s.Nonempty → t.Nonempty → (s * t).Nonempty :=
  Nonempty.image2

@[to_additive]
theorem Nonempty.of_mul_left : (s * t).Nonempty → s.Nonempty :=
  Nonempty.of_image2_left

@[to_additive]
theorem Nonempty.of_mul_right : (s * t).Nonempty → t.Nonempty :=
  Nonempty.of_image2_right

@[to_additive (attr := simp)]
theorem mul_singleton : s * {b} = (· * b) '' s :=
  image2_singleton_right

@[to_additive (attr := simp)]
theorem singleton_mul : {a} * t = (a * ·) '' t :=
  image2_singleton_left

@[to_additive]
theorem singleton_mul_singleton : ({a} : Set α) * {b} = {a * b} :=
  image2_singleton

@[to_additive (attr := mono, gcongr)]
theorem mul_subset_mul : s₁ ⊆ t₁ → s₂ ⊆ t₂ → s₁ * s₂ ⊆ t₁ * t₂ :=
  image2_subset

@[to_additive (attr := gcongr)]
theorem mul_subset_mul_left : t₁ ⊆ t₂ → s * t₁ ⊆ s * t₂ :=
  image2_subset_left

@[to_additive (attr := gcongr)]
theorem mul_subset_mul_right : s₁ ⊆ s₂ → s₁ * t ⊆ s₂ * t :=
  image2_subset_right

@[to_additive] instance : MulLeftMono (Set α) where elim _s _t₁ _t₂ := mul_subset_mul_left
@[to_additive] instance : MulRightMono (Set α) where elim _t _s₁ _s₂ := mul_subset_mul_right

@[to_additive]
theorem mul_subset_iff : s * t ⊆ u ↔ ∀ x ∈ s, ∀ y ∈ t, x * y ∈ u :=
  image2_subset_iff

@[to_additive]
theorem union_mul : (s₁ ∪ s₂) * t = s₁ * t ∪ s₂ * t :=
  image2_union_left

@[to_additive]
theorem mul_union : s * (t₁ ∪ t₂) = s * t₁ ∪ s * t₂ :=
  image2_union_right

@[to_additive]
theorem inter_mul_subset : s₁ ∩ s₂ * t ⊆ s₁ * t ∩ (s₂ * t) :=
  image2_inter_subset_left

@[to_additive]
theorem mul_inter_subset : s * (t₁ ∩ t₂) ⊆ s * t₁ ∩ (s * t₂) :=
  image2_inter_subset_right

@[to_additive]
theorem inter_mul_union_subset_union : s₁ ∩ s₂ * (t₁ ∪ t₂) ⊆ s₁ * t₁ ∪ s₂ * t₂ :=
  image2_inter_union_subset_union

@[to_additive]
theorem union_mul_inter_subset_union : (s₁ ∪ s₂) * (t₁ ∩ t₂) ⊆ s₁ * t₁ ∪ s₂ * t₂ :=
  image2_union_inter_subset_union

/-- The singleton operation as a `MulHom`. -/
@[to_additive "The singleton operation as an `AddHom`."]
def singletonMulHom : α →ₙ* Set α where
  toFun := singleton
  map_mul' _ _ := singleton_mul_singleton.symm

@[to_additive (attr := simp)]
theorem coe_singletonMulHom : (singletonMulHom : α → Set α) = singleton :=
  rfl

@[to_additive (attr := simp)]
theorem singletonMulHom_apply (a : α) : singletonMulHom a = {a} :=
  rfl

open MulOpposite

@[to_additive (attr := simp)]
theorem image_op_mul : op '' (s * t) = op '' t * op '' s :=
  image_image2_antidistrib op_mul

@[to_additive (attr := simp) prod_add_prod_comm]
lemma prod_mul_prod_comm [Mul β] (s₁ s₂ : Set α) (t₁ t₂ : Set β) :
   (s₁ ×ˢ t₁) * (s₂ ×ˢ t₂) = (s₁ * s₂) ×ˢ (t₁ * t₂) := by ext; simp [mem_mul]; aesop

@[deprecated (since := "2025-03-11")]
alias sum_add_sum_comm := prod_add_prod_comm

end Mul

/-! ### Set subtraction/division -/


section Div

variable {ι : Sort*} {κ : ι → Sort*} [Div α] {s s₁ s₂ t t₁ t₂ u : Set α} {a b : α}

/-- The pointwise division of sets `s / t` is defined as `{x / y | x ∈ s, y ∈ t}` in locale
`Pointwise`. -/
@[to_additive
      "The pointwise subtraction of sets `s - t` is defined as `{x - y | x ∈ s, y ∈ t}` in locale
      `Pointwise`."]
protected def div : Div (Set α) :=
  ⟨image2 (· / ·)⟩

scoped[Pointwise] attribute [instance] Set.div Set.sub

@[to_additive (attr := simp)]
theorem image2_div : image2 (· / ·) s t = s / t :=
  rfl

@[to_additive]
theorem mem_div : a ∈ s / t ↔ ∃ x ∈ s, ∃ y ∈ t, x / y = a :=
  Iff.rfl

@[to_additive]
theorem div_mem_div : a ∈ s → b ∈ t → a / b ∈ s / t :=
  mem_image2_of_mem

@[to_additive sub_image_prod]
theorem image_div_prod : (fun x : α × α => x.fst / x.snd) '' s ×ˢ t = s / t :=
  image_prod _

@[to_additive (attr := simp)]
theorem empty_div : ∅ / s = ∅ :=
  image2_empty_left

@[to_additive (attr := simp)]
theorem div_empty : s / ∅ = ∅ :=
  image2_empty_right

@[to_additive (attr := simp)]
theorem div_eq_empty : s / t = ∅ ↔ s = ∅ ∨ t = ∅ :=
  image2_eq_empty_iff

@[to_additive (attr := simp)]
theorem div_nonempty : (s / t).Nonempty ↔ s.Nonempty ∧ t.Nonempty :=
  image2_nonempty_iff

@[to_additive]
theorem Nonempty.div : s.Nonempty → t.Nonempty → (s / t).Nonempty :=
  Nonempty.image2

@[to_additive]
theorem Nonempty.of_div_left : (s / t).Nonempty → s.Nonempty :=
  Nonempty.of_image2_left

@[to_additive]
theorem Nonempty.of_div_right : (s / t).Nonempty → t.Nonempty :=
  Nonempty.of_image2_right

@[to_additive (attr := simp)]
theorem div_singleton : s / {b} = (· / b) '' s :=
  image2_singleton_right

@[to_additive (attr := simp)]
theorem singleton_div : {a} / t = (· / ·) a '' t :=
  image2_singleton_left

@[to_additive]
theorem singleton_div_singleton : ({a} : Set α) / {b} = {a / b} :=
  image2_singleton

@[to_additive (attr := mono, gcongr)]
theorem div_subset_div : s₁ ⊆ t₁ → s₂ ⊆ t₂ → s₁ / s₂ ⊆ t₁ / t₂ :=
  image2_subset

@[to_additive (attr := gcongr)]
theorem div_subset_div_left : t₁ ⊆ t₂ → s / t₁ ⊆ s / t₂ :=
  image2_subset_left

@[to_additive (attr := gcongr)]
theorem div_subset_div_right : s₁ ⊆ s₂ → s₁ / t ⊆ s₂ / t :=
  image2_subset_right

@[to_additive]
theorem div_subset_iff : s / t ⊆ u ↔ ∀ x ∈ s, ∀ y ∈ t, x / y ∈ u :=
  image2_subset_iff

@[to_additive]
theorem union_div : (s₁ ∪ s₂) / t = s₁ / t ∪ s₂ / t :=
  image2_union_left

@[to_additive]
theorem div_union : s / (t₁ ∪ t₂) = s / t₁ ∪ s / t₂ :=
  image2_union_right

@[to_additive]
theorem inter_div_subset : s₁ ∩ s₂ / t ⊆ s₁ / t ∩ (s₂ / t) :=
  image2_inter_subset_left

@[to_additive]
theorem div_inter_subset : s / (t₁ ∩ t₂) ⊆ s / t₁ ∩ (s / t₂) :=
  image2_inter_subset_right

@[to_additive]
theorem inter_div_union_subset_union : s₁ ∩ s₂ / (t₁ ∪ t₂) ⊆ s₁ / t₁ ∪ s₂ / t₂ :=
  image2_inter_union_subset_union

@[to_additive]
theorem union_div_inter_subset_union : (s₁ ∪ s₂) / (t₁ ∩ t₂) ⊆ s₁ / t₁ ∪ s₂ / t₂ :=
  image2_union_inter_subset_union

end Div

/-- Repeated pointwise addition (not the same as pointwise repeated addition!) of a `Set`. See
note [pointwise nat action]. -/
protected def NSMul [Zero α] [Add α] : SMul ℕ (Set α) :=
  ⟨nsmulRec⟩

/-- Repeated pointwise multiplication (not the same as pointwise repeated multiplication!) of a
`Set`. See note [pointwise nat action]. -/
@[to_additive existing]
protected def NPow [One α] [Mul α] : Pow (Set α) ℕ :=
  ⟨fun s n => npowRec n s⟩

/-- Repeated pointwise addition/subtraction (not the same as pointwise repeated
addition/subtraction!) of a `Set`. See note [pointwise nat action]. -/
protected def ZSMul [Zero α] [Add α] [Neg α] : SMul ℤ (Set α) :=
  ⟨zsmulRec⟩

/-- Repeated pointwise multiplication/division (not the same as pointwise repeated
multiplication/division!) of a `Set`. See note [pointwise nat action]. -/
@[to_additive existing]
protected def ZPow [One α] [Mul α] [Inv α] : Pow (Set α) ℤ :=
  ⟨fun s n => zpowRec npowRec n s⟩

scoped[Pointwise] attribute [instance] Set.NSMul Set.NPow Set.ZSMul Set.ZPow

/-- `Set α` is a `Semigroup` under pointwise operations if `α` is. -/
@[to_additive "`Set α` is an `AddSemigroup` under pointwise operations if `α` is."]
protected def semigroup [Semigroup α] : Semigroup (Set α) :=
  { Set.mul with mul_assoc := fun _ _ _ => image2_assoc mul_assoc }

section CommSemigroup

variable [CommSemigroup α] {s t : Set α}

/-- `Set α` is a `CommSemigroup` under pointwise operations if `α` is. -/
@[to_additive "`Set α` is an `AddCommSemigroup` under pointwise operations if `α` is."]
protected def commSemigroup : CommSemigroup (Set α) :=
  { Set.semigroup with mul_comm := fun _ _ => image2_comm mul_comm }

@[to_additive]
theorem inter_mul_union_subset : s ∩ t * (s ∪ t) ⊆ s * t :=
  image2_inter_union_subset mul_comm

@[to_additive]
theorem union_mul_inter_subset : (s ∪ t) * (s ∩ t) ⊆ s * t :=
  image2_union_inter_subset mul_comm

end CommSemigroup

section MulOneClass

variable [MulOneClass α]

/-- `Set α` is a `MulOneClass` under pointwise operations if `α` is. -/
@[to_additive "`Set α` is an `AddZeroClass` under pointwise operations if `α` is."]
protected def mulOneClass : MulOneClass (Set α) where
  __ := Set.one
  __ := Set.mul
  mul_one := image2_right_identity mul_one
  one_mul := image2_left_identity one_mul

scoped[Pointwise]
  attribute [instance]
    Set.mulOneClass Set.addZeroClass Set.semigroup Set.addSemigroup Set.commSemigroup
    Set.addCommSemigroup

@[to_additive]
theorem subset_mul_left (s : Set α) {t : Set α} (ht : (1 : α) ∈ t) : s ⊆ s * t := fun x hx =>
  ⟨x, hx, 1, ht, mul_one _⟩

@[to_additive]
theorem subset_mul_right {s : Set α} (t : Set α) (hs : (1 : α) ∈ s) : t ⊆ s * t := fun x hx =>
  ⟨1, hs, x, hx, one_mul _⟩

/-- The singleton operation as a `MonoidHom`. -/
@[to_additive "The singleton operation as an `AddMonoidHom`."]
def singletonMonoidHom : α →* Set α where
  __ := singletonMulHom
  __ := singletonOneHom

@[to_additive (attr := simp)]
theorem coe_singletonMonoidHom : (singletonMonoidHom : α → Set α) = singleton :=
  rfl

@[to_additive (attr := simp)]
theorem singletonMonoidHom_apply (a : α) : singletonMonoidHom a = {a} :=
  rfl

end MulOneClass

section Monoid

variable [Monoid α] {s t : Set α} {a : α} {m n : ℕ}

/-- `Set α` is a `Monoid` under pointwise operations if `α` is. -/
@[to_additive "`Set α` is an `AddMonoid` under pointwise operations if `α` is."]
protected def monoid : Monoid (Set α) where
  __ := Set.semigroup
  __ := Set.mulOneClass
  __ := @Set.NPow α _ _

scoped[Pointwise] attribute [instance] Set.monoid Set.addMonoid

-- `Set.pow_left_monotone` doesn't exist since it would syntactically be a special case of
-- `pow_left_mono`

@[to_additive]
protected lemma pow_right_monotone (hs : 1 ∈ s) : Monotone (s ^ ·) :=
  pow_right_monotone <| one_subset.2 hs

@[to_additive (attr := gcongr)]
lemma pow_subset_pow_left (hst : s ⊆ t) : s ^ n ⊆ t ^ n := pow_left_mono _ hst

@[to_additive (attr := gcongr)]
lemma pow_subset_pow_right (hs : 1 ∈ s) (hmn : m ≤ n) : s ^ m ⊆ s ^ n :=
  Set.pow_right_monotone hs hmn

@[to_additive (attr := gcongr)]
lemma pow_subset_pow (hst : s ⊆ t) (ht : 1 ∈ t) (hmn : m ≤ n) : s ^ m ⊆ t ^ n :=
  (pow_subset_pow_left hst).trans (pow_subset_pow_right ht hmn)

@[to_additive]
lemma subset_pow (hs : 1 ∈ s) (hn : n ≠ 0) : s ⊆ s ^ n := by
  simpa using pow_subset_pow_right hs <| Nat.one_le_iff_ne_zero.2 hn

@[deprecated (since := "2024-11-19")] alias pow_subset_pow_of_one_mem := pow_subset_pow_right

@[deprecated (since := "2024-11-19")]
alias nsmul_subset_nsmul_of_zero_mem := nsmul_subset_nsmul_right

@[to_additive]
lemma pow_subset_pow_mul_of_sq_subset_mul (hst : s ^ 2 ⊆ t * s) (hn : n ≠ 0) :
    s ^ n ⊆ t ^ (n - 1) * s := pow_le_pow_mul_of_sq_le_mul hst hn

@[to_additive (attr := simp) nsmul_empty]
lemma empty_pow (hn : n ≠ 0) : (∅ : Set α) ^ n = ∅ := match n with | n + 1 => by simp [pow_succ]

@[to_additive]
lemma Nonempty.pow (hs : s.Nonempty) : ∀ {n}, (s ^ n).Nonempty
  | 0 => by simp
  | n + 1 => by rw [pow_succ]; exact hs.pow.mul hs

set_option push_neg.use_distrib true in
@[to_additive (attr := simp)] lemma pow_eq_empty : s ^ n = ∅ ↔ s = ∅ ∧ n ≠ 0 := by
  constructor
  · contrapose!
    rintro (hs | rfl)
    · exact hs.pow
    · simp
  · rintro ⟨rfl, hn⟩
    exact empty_pow hn

@[to_additive (attr := simp) nsmul_singleton]
lemma singleton_pow (a : α) : ∀ n, ({a} : Set α) ^ n = {a ^ n}
  | 0 => by simp [singleton_one]
  | n + 1 => by simp [pow_succ, singleton_pow _ n]

@[to_additive] lemma pow_mem_pow (ha : a ∈ s) : a ^ n ∈ s ^ n := by
  simpa using pow_subset_pow_left (singleton_subset_iff.2 ha)

@[to_additive] lemma one_mem_pow (hs : 1 ∈ s) : 1 ∈ s ^ n := by simpa using pow_mem_pow hs

@[to_additive]
lemma inter_pow_subset : (s ∩ t) ^ n ⊆ s ^ n ∩ t ^ n := by apply subset_inter <;> gcongr <;> simp

@[to_additive]
theorem mul_univ_of_one_mem (hs : (1 : α) ∈ s) : s * univ = univ :=
  eq_univ_iff_forall.2 fun _ => mem_mul.2 ⟨_, hs, _, mem_univ _, one_mul _⟩

@[to_additive]
theorem univ_mul_of_one_mem (ht : (1 : α) ∈ t) : univ * t = univ :=
  eq_univ_iff_forall.2 fun _ => mem_mul.2 ⟨_, mem_univ _, _, ht, mul_one _⟩

@[to_additive (attr := simp)]
theorem univ_mul_univ : (univ : Set α) * univ = univ :=
  mul_univ_of_one_mem <| mem_univ _

@[to_additive (attr := simp) nsmul_univ]
theorem univ_pow : ∀ {n : ℕ}, n ≠ 0 → (univ : Set α) ^ n = univ
  | 0 => fun h => (h rfl).elim
  | 1 => fun _ => pow_one _
  | n + 2 => fun _ => by rw [pow_succ, univ_pow n.succ_ne_zero, univ_mul_univ]

@[to_additive]
protected theorem _root_.IsUnit.set : IsUnit a → IsUnit ({a} : Set α) :=
  IsUnit.map (singletonMonoidHom : α →* Set α)

@[to_additive nsmul_prod]
lemma prod_pow [Monoid β] (s : Set α) (t : Set β) : ∀ n, (s ×ˢ t) ^ n = (s ^ n) ×ˢ (t ^ n)
  | 0 => by simp
  | n + 1 => by simp [pow_succ, prod_pow _ _ n]

@[deprecated (since := "2025-02-17")] alias sum_nsmul := nsmul_prod

end Monoid

section IsLeftCancelMul
variable [Mul α] [IsLeftCancelMul α] {s t : Set α}

@[to_additive]
lemma Nontrivial.mul_left : t.Nontrivial → s.Nonempty → (s * t).Nontrivial := by
  rintro ⟨a, ha, b, hb, hab⟩ ⟨c, hc⟩
  exact ⟨c * a, mul_mem_mul hc ha, c * b, mul_mem_mul hc hb, by simpa⟩

@[to_additive]
lemma Nontrivial.mul (hs : s.Nontrivial) (ht : t.Nontrivial) : (s * t).Nontrivial :=
  ht.mul_left hs.nonempty

end IsLeftCancelMul

section IsRightCancelMul
variable [Mul α] [IsRightCancelMul α] {s t : Set α}

@[to_additive]
lemma Nontrivial.mul_right : s.Nontrivial → t.Nonempty → (s * t).Nontrivial := by
  rintro ⟨a, ha, b, hb, hab⟩ ⟨c, hc⟩
  exact ⟨a * c, mul_mem_mul ha hc, b * c, mul_mem_mul hb hc, by simpa⟩

end IsRightCancelMul

section CancelMonoid
variable [CancelMonoid α] {s t : Set α} {a : α} {n : ℕ}

@[to_additive]
lemma Nontrivial.pow (hs : s.Nontrivial) : ∀ {n}, n ≠ 0 → (s ^ n).Nontrivial
  | 1, _ => by simpa
  | n + 2, _ => by simpa [pow_succ] using (hs.pow n.succ_ne_zero).mul hs

end CancelMonoid

/-- `Set α` is a `CommMonoid` under pointwise operations if `α` is. -/
@[to_additive "`Set α` is an `AddCommMonoid` under pointwise operations if `α` is."]
protected def commMonoid [CommMonoid α] : CommMonoid (Set α) where
  __ := Set.monoid
  __ := Set.commSemigroup

scoped[Pointwise] attribute [instance] Set.commMonoid Set.addCommMonoid

open Pointwise

section DivisionMonoid

variable [DivisionMonoid α] {s t : Set α} {n : ℤ}

@[to_additive]
protected theorem mul_eq_one_iff : s * t = 1 ↔ ∃ a b, s = {a} ∧ t = {b} ∧ a * b = 1 := by
  refine ⟨fun h => ?_, ?_⟩
  · have hst : (s * t).Nonempty := h.symm.subst one_nonempty
    obtain ⟨a, ha⟩ := hst.of_image2_left
    obtain ⟨b, hb⟩ := hst.of_image2_right
    have H : ∀ {a b}, a ∈ s → b ∈ t → a * b = (1 : α) := fun {a b} ha hb =>
      h.subset <| mem_image2_of_mem ha hb
    refine ⟨a, b, ?_, ?_, H ha hb⟩ <;> refine eq_singleton_iff_unique_mem.2 ⟨‹_›, fun x hx => ?_⟩
    · exact (eq_inv_of_mul_eq_one_left <| H hx hb).trans (inv_eq_of_mul_eq_one_left <| H ha hb)
    · exact (eq_inv_of_mul_eq_one_right <| H ha hx).trans (inv_eq_of_mul_eq_one_right <| H ha hb)
  · rintro ⟨b, c, rfl, rfl, h⟩
    rw [singleton_mul_singleton, h, singleton_one]

/-- `Set α` is a division monoid under pointwise operations if `α` is. -/
@[to_additive "`Set α` is a subtraction monoid under pointwise operations if `α` is."]
protected def divisionMonoid : DivisionMonoid (Set α) where
  __ := Set.monoid
  __ := Set.involutiveInv
  __ := Set.div
  __ := @Set.ZPow α _ _ _
  mul_inv_rev s t := by
    simp_rw [← image_inv_eq_inv]
    exact image_image2_antidistrib mul_inv_rev
  inv_eq_of_mul s t h := by
    obtain ⟨a, b, rfl, rfl, hab⟩ := Set.mul_eq_one_iff.1 h
    rw [inv_singleton, inv_eq_of_mul_eq_one_right hab]
  div_eq_mul_inv s t := by
    rw [← image_id (s / t), ← image_inv_eq_inv]
    exact image_image2_distrib_right div_eq_mul_inv

scoped[Pointwise] attribute [instance] Set.divisionMonoid Set.subtractionMonoid

@[to_additive (attr := simp 500)]
theorem isUnit_iff : IsUnit s ↔ ∃ a, s = {a} ∧ IsUnit a := by
  constructor
  · rintro ⟨u, rfl⟩
    obtain ⟨a, b, ha, hb, h⟩ := Set.mul_eq_one_iff.1 u.mul_inv
    refine ⟨a, ha, ⟨a, b, h, singleton_injective ?_⟩, rfl⟩
    rw [← singleton_mul_singleton, ← ha, ← hb]
    exact u.inv_mul
  · rintro ⟨a, rfl, ha⟩
    exact ha.set

@[to_additive (attr := simp)]
lemma univ_div_univ : (univ / univ : Set α) = univ := by simp [div_eq_mul_inv]

@[to_additive] lemma subset_div_left (ht : 1 ∈ t) : s ⊆ s / t := by
  rw [div_eq_mul_inv]; exact subset_mul_left _ <| by simpa

@[to_additive] lemma inv_subset_div_right (hs : 1 ∈ s) : t⁻¹ ⊆ s / t := by
  rw [div_eq_mul_inv]; exact subset_mul_right _ hs

@[to_additive (attr := simp) zsmul_empty]
lemma empty_zpow (hn : n ≠ 0) : (∅ : Set α) ^ n = ∅ := by cases n <;> aesop

@[to_additive]
lemma Nonempty.zpow (hs : s.Nonempty) : ∀ {n : ℤ}, (s ^ n).Nonempty
  | (n : ℕ) => hs.pow
  | .negSucc n => by simpa using hs.pow

set_option push_neg.use_distrib true in
@[to_additive (attr := simp)] lemma zpow_eq_empty : s ^ n = ∅ ↔ s = ∅ ∧ n ≠ 0 := by
  constructor
  · contrapose!
    rintro (hs | rfl)
    · exact hs.zpow
    · simp
  · rintro ⟨rfl, hn⟩
    exact empty_zpow hn

@[to_additive (attr := simp) zsmul_singleton]
lemma singleton_zpow (a : α) (n : ℤ) : ({a} : Set α) ^ n = {a ^ n} := by cases n <;> simp

end DivisionMonoid

/-- `Set α` is a commutative division monoid under pointwise operations if `α` is. -/
@[to_additive subtractionCommMonoid
      "`Set α` is a commutative subtraction monoid under pointwise operations if `α` is."]
protected def divisionCommMonoid [DivisionCommMonoid α] : DivisionCommMonoid (Set α) where
  __ := Set.divisionMonoid
  __ := Set.commSemigroup

scoped[Pointwise] attribute [instance] Set.divisionCommMonoid Set.subtractionCommMonoid

section Group

variable [Group α] {s t : Set α} {a b : α}

/-! Note that `Set` is not a `Group` because `s / s ≠ 1` in general. -/