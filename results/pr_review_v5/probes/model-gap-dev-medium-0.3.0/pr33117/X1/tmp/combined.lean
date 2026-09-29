/-- A function is meromorphic iff it is meromorphic on `Set.univ`. -/
@[simp]
lemma meromorphicOn_univ {f : 𝕜 → E} : MeromorphicOn f Set.univ ↔ Meromorphic f :=
  ⟨fun h x ↦ h x trivial, fun h x _ ↦ h x⟩

namespace Meromorphic

variable
  {ι : Type*} {s : Finset ι}
  {f g : 𝕜 → E} {F : ι → 𝕜 → 𝕜} {G : ι → 𝕜 → E}

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

@[fun_prop]
theorem sum (h : ∀ σ, Meromorphic (G σ)) :
    Meromorphic (∑ n ∈ s, G n) := fun x ↦ MeromorphicAt.sum (h · x)

@[fun_prop]
theorem fun_sum (h : ∀ σ, Meromorphic (G σ)) :
    Meromorphic (fun x ↦ ∑ n ∈ s, G n x) := fun x ↦ MeromorphicAt.fun_sum (h · x)

@[fun_prop]
lemma sub (hf : Meromorphic f) (hg : Meromorphic g) :
    Meromorphic (f - g) := fun x ↦ (hf x).sub (hg x)

@[fun_prop]
lemma fun_sub (hf : Meromorphic f) (hg : Meromorphic g) :
    Meromorphic (fun x ↦ f x - g x) := hf.sub hg

@[fun_prop]
lemma mul {f g : 𝕜 → 𝕜} (hf : Meromorphic f) (hg : Meromorphic g) :
    Meromorphic (f * g) := fun x ↦ (hf x).mul (hg x)

@[fun_prop]
lemma fun_mul {f g : 𝕜 → 𝕜} (hf : Meromorphic f) (hg : Meromorphic g) :
    Meromorphic (fun x ↦ f x * g x) := hf.mul hg

@[fun_prop]
theorem prod (h : ∀ σ, Meromorphic (F σ)) :
    Meromorphic (∏ n ∈ s, F n) := fun x ↦ MeromorphicAt.prod (h · x)

@[fun_prop]
theorem fun_prod (h : ∀ σ, Meromorphic (F σ)) :
    Meromorphic (fun x ↦ ∏ n ∈ s, F n x) := fun x ↦ MeromorphicAt.fun_prod (h · x)

@[fun_prop]
lemma div {f g : 𝕜 → 𝕜} (hf : Meromorphic f) (hg : Meromorphic g) :
    Meromorphic (f / g) := fun x ↦ (hf x).div (hg x)

@[fun_prop]
lemma fun_div {f g : 𝕜 → 𝕜} (hf : Meromorphic f) (hg : Meromorphic g) :
    Meromorphic (fun x ↦ f x / g x) := hf.div hg

@[fun_prop]
lemma pow {f : 𝕜 → 𝕜} (hf : Meromorphic f) (n : ℕ) : Meromorphic (f ^ n) := fun x ↦ (hf x).pow n

@[fun_prop]
lemma fun_pow {f : 𝕜 → 𝕜} (hf : Meromorphic f) (n : ℕ) : Meromorphic (fun x ↦ f x ^ n) :=
  hf.pow n

@[fun_prop]
lemma zpow {f : 𝕜 → 𝕜} (hf : Meromorphic f) (n : ℤ) : Meromorphic (f ^ n) := fun x ↦ (hf x).zpow n

@[fun_prop]
lemma fun_zpow {f : 𝕜 → 𝕜} (hf : Meromorphic f) (n : ℤ) : Meromorphic (fun x ↦ f x ^ n) :=
  hf.zpow n

@[fun_prop]
protected lemma deriv [CompleteSpace E] (hf : Meromorphic f) : Meromorphic (deriv f) :=
  fun x ↦ (hf x).deriv

@[fun_prop]
lemma fun_deriv [CompleteSpace E] (hf : Meromorphic f) :
    Meromorphic (fun x ↦ deriv f x) := hf.deriv

@[fun_prop]
lemma iterated_deriv [CompleteSpace E] {n : ℕ} (hf : Meromorphic f) :
    Meromorphic (deriv^[n] f) := fun x ↦ (hf x).iterated_deriv

@[fun_prop]
lemma fun_iterated_deriv [CompleteSpace E] {n : ℕ} (hf : Meromorphic f) :
    Meromorphic (fun x ↦ deriv^[n] f x) := hf.iterated_deriv

example {f : 𝕜 → 𝕜} (hf : Meromorphic f) : Meromorphic (fun x ↦ f x ^ 3 * f x ^ (-2 : ℤ)) := by
  fun_prop
