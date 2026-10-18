/-- A function `f : 𝕜 → E` is meromorphic if it is meromorphic at every point of `𝕜`. -/
@[fun_prop]
def Meromorphic (f : 𝕜 → E) : Prop := ∀ x, MeromorphicAt f x

@[simp]
lemma meromorphicOn_univ {f : 𝕜 → E} : MeromorphicOn f Set.univ ↔ Meromorphic f :=
  ⟨fun h x ↦ h x (mem_univ x), fun h x _ ↦ h x⟩

namespace Meromorphic

variable
  {ι : Type*} {s : Finset ι}
  {f g : 𝕜 → E} {F : ι → 𝕜 → 𝕜} {G : ι → 𝕜 → E}

@[fun_prop]
lemma meromorphicAt (hf : Meromorphic f) {x : 𝕜} : MeromorphicAt f x := hf x

lemma meromorphicOn (hf : Meromorphic f) {U : Set 𝕜} : MeromorphicOn f U := fun x _ ↦ hf x

@[fun_prop]
lemma id : Meromorphic (id : 𝕜 → 𝕜) := fun x ↦ .id x

@[fun_prop]
lemma const (e : E) : Meromorphic (fun _ : 𝕜 ↦ e) := fun x ↦ .const e x

@[fun_prop]
lemma neg (hf : Meromorphic f) : Meromorphic (-f) := fun x ↦ (hf x).neg

@[fun_prop]
lemma fun_neg (hf : Meromorphic f) : Meromorphic (fun x ↦ -f x) := hf.neg

@[fun_prop]
lemma add (hf : Meromorphic f) (hg : Meromorphic g) :
    Meromorphic (f + g) := fun x ↦ (hf x).add (hg x)

@[fun_prop]
lemma fun_add (hf : Meromorphic f) (hg : Meromorphic g) :
    Meromorphic (fun x ↦ f x + g x) := hf.add hg

/-- Finite sums of meromorphic functions are meromorphic. -/
@[fun_prop]
theorem sum (h : ∀ σ, Meromorphic (G σ)) :
    Meromorphic (∑ n ∈ s, G n) := fun x ↦ MeromorphicAt.sum (h · x)

/-- Finite sums of meromorphic functions are meromorphic. -/
@[fun_prop]
theorem fun_sum (h : ∀ σ, Meromorphic (G σ)) :
    Meromorphic (fun x ↦ ∑ n ∈ s, G n x) := fun x ↦ MeromorphicAt.fun_sum (h · x)

@[fun_prop]
lemma sub (hf : Meromorphic f) (hg : Meromorphic g) :
    Meromorphic (f - g) := fun x ↦ (hf x).sub (hg x)

@[fun_prop]
lemma fun_sub (hf : Meromorphic f) (hg : Meromorphic g) :
    Meromorphic (fun x ↦ f x - g x) := hf.sub hg

/-- Finite products of meromorphic functions are meromorphic. -/
@[fun_prop]
theorem prod (h : ∀ σ, Meromorphic (F σ)) :
    Meromorphic (∏ n ∈ s, F n) := fun x ↦ MeromorphicAt.prod (h · x)

/-- Finite products of meromorphic functions are meromorphic. -/
@[fun_prop]
theorem fun_prod (h : ∀ σ, Meromorphic (F σ)) :
    Meromorphic (fun x ↦ ∏ n ∈ s, F n x) := fun x ↦ MeromorphicAt.fun_prod (h · x)

section Field

variable {f g : 𝕜 → 𝕜}

@[fun_prop]
lemma smul {g : 𝕜 → E} (hf : Meromorphic f) (hg : Meromorphic g) :
    Meromorphic (f • g) := fun x ↦ (hf x).smul (hg x)

@[fun_prop]
lemma fun_smul {g : 𝕜 → E} (hf : Meromorphic f) (hg : Meromorphic g) :
    Meromorphic (fun x ↦ f x • g x) := hf.smul hg

@[fun_prop]
lemma mul (hf : Meromorphic f) (hg : Meromorphic g) :
    Meromorphic (f * g) := fun x ↦ (hf x).mul (hg x)

@[fun_prop]
lemma fun_mul (hf : Meromorphic f) (hg : Meromorphic g) :
    Meromorphic (fun x ↦ f x * g x) := hf.mul hg

@[fun_prop]
lemma inv (hf : Meromorphic f) : Meromorphic f⁻¹ := fun x ↦ (hf x).inv

@[fun_prop]
lemma fun_inv (hf : Meromorphic f) : Meromorphic (fun x ↦ (f x)⁻¹) := hf.inv

@[fun_prop]
lemma div (hf : Meromorphic f) (hg : Meromorphic g) :
    Meromorphic (f / g) := fun x ↦ (hf x).div (hg x)

@[fun_prop]
lemma fun_div (hf : Meromorphic f) (hg : Meromorphic g) :
    Meromorphic (fun x ↦ f x / g x) := hf.div hg

@[fun_prop]
lemma pow (hf : Meromorphic f) (n : ℕ) : Meromorphic (f ^ n) := fun x ↦ (hf x).pow n

@[fun_prop]
lemma fun_pow (hf : Meromorphic f) (n : ℕ) : Meromorphic (fun x ↦ f x ^ n) := hf.pow n

@[fun_prop]
lemma zpow (hf : Meromorphic f) (n : ℤ) : Meromorphic (f ^ n) := fun x ↦ (hf x).zpow n

@[fun_prop]
lemma fun_zpow (hf : Meromorphic f) (n : ℤ) : Meromorphic (fun x ↦ f x ^ n) := hf.zpow n

end Field

/-- Derivatives of meromorphic functions are meromorphic. -/
@[fun_prop]
protected theorem deriv [CompleteSpace E] (hf : Meromorphic f) : Meromorphic (deriv f) :=
  fun x ↦ (hf x).deriv

/-- Derivatives of meromorphic functions are meromorphic. -/
@[fun_prop]
theorem fun_deriv [CompleteSpace E] (hf : Meromorphic f) :
    Meromorphic (fun x ↦ _root_.deriv f x) := hf.deriv

/-- Iterated derivatives of meromorphic functions are meromorphic. -/
@[fun_prop]
theorem iterated_deriv [CompleteSpace E] {n : ℕ} (hf : Meromorphic f) :
    Meromorphic (_root_.deriv^[n] f) := fun x ↦ (hf x).iterated_deriv

/-- Iterated derivatives of meromorphic functions are meromorphic. -/
@[fun_prop]
theorem fun_iterated_deriv [CompleteSpace E] {n : ℕ} (hf : Meromorphic f) :
    Meromorphic (fun x ↦ _root_.deriv^[n] f x) := hf.iterated_deriv

end Meromorphic

example : Meromorphic (fun x : 𝕜 ↦ x) := by fun_prop

example : Meromorphic (fun x : 𝕜 ↦ x * x + 1) := by fun_prop

example (f : 𝕜 → 𝕜) (hf : Meromorphic f) : Meromorphic (fun x ↦ (f x)⁻¹ + 3 * x ^ 2) := by
  fun_prop

open Meromorphic in
example (f : 𝕜 → 𝕜) : deriv f = _root_.deriv f := rfl

example (f : 𝕜 → 𝕜) (x : 𝕜) (hf : Meromorphic f) : MeromorphicAt (fun z ↦ f z * z + 1) x := by
  fun_prop
