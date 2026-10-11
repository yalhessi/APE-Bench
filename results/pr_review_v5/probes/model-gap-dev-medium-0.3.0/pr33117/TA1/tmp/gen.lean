/-- Finite sums of meromorphic functions are meromorphic. -/
@[fun_prop]
theorem sum (h : ∀ σ ∈ s, Meromorphic (G σ)) :
    Meromorphic (∑ n ∈ s, G n) := fun x ↦ by
  simpa using MeromorphicAt.sum (s := s.attach) (fun σ ↦ h σ σ.2 x)

/-- Finite sums of meromorphic functions are meromorphic. -/
@[fun_prop]
theorem fun_sum (h : ∀ σ ∈ s, Meromorphic (G σ)) :
    Meromorphic (fun x ↦ ∑ n ∈ s, G n x) := by
  simpa [← Finset.sum_apply] using sum h

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

/-- Finite products of meromorphic functions are meromorphic. -/
@[fun_prop]
theorem prod (h : ∀ σ ∈ s, Meromorphic (F σ)) :
    Meromorphic (∏ n ∈ s, F n) := fun x ↦ by
  simpa using MeromorphicAt.prod (s := s.attach) (fun σ ↦ h σ σ.2 x)

/-- Finite products of meromorphic functions are meromorphic. -/
@[fun_prop]
theorem fun_prod (h : ∀ σ ∈ s, Meromorphic (F σ)) :
    Meromorphic (fun x ↦ ∏ n ∈ s, F n x) := by
  simpa [← Finset.prod_apply] using prod h
