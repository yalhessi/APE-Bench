# The PR model for #33117 (pass 0)

Built deterministically from the diff and the change graph, with no review text. Every entry is a **fact** unless marked `hypothesis`; a hypothesis is a question to check, not a premise. Not built, so not here: library candidates, the area's twin patterns and conventions, and other open PRs. Construct what you need of those with the tools.

## The PR

- title: feat: introduce predicate `Meromorphic`
- description: Following a discussion of Zulip, introduce the predicate `Meromorphic` as a shorthand for functions that are `MeromorphicOn … Set.univ`

[#mathlib4 > Introducing &#96;Meromorphic&#96; @ 💬](https://leanprover.zulipchat.com/#narrow/channel/287929-mathlib4/topic/Introducing.20.60Meromorphic.60/near/564522177)
- changed files: Mathlib/Analysis/Meromorphic/Basic.lean

## Objects

### `Meromorphic.add` (lemma, added) [074bbf8ee0]
- file: `Mathlib/Analysis/Meromorphic/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[fun_prop]
lemma add (hf : Meromorphic f) (hg : Meromorphic g) :
    Meromorphic (f + g) := fun x ↦ (hf x).add (hg x)
```

### `section in Basic.lean` (command, added) [0901aa1ff9]
- file: `Mathlib/Analysis/Meromorphic/Basic.lean`; changed: namespace:added
- as the PR leaves it:
```lean
end Meromorphic
```

### `section in Basic.lean` (command, added) [141b38e85b]
- file: `Mathlib/Analysis/Meromorphic/Basic.lean`; changed: namespace:added
- as the PR leaves it:
```lean
end MeromorphicOn
```

### `Meromorphic.fun_deriv` (lemma, added) [29450b3e04]
- file: `Mathlib/Analysis/Meromorphic/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[fun_prop]
lemma fun_deriv [CompleteSpace E] (hf : Meromorphic f) :
    Meromorphic (fun x ↦ _root_.deriv f x) := hf.deriv
```

### `Meromorphic` (def, added) [367ff6247f]
- file: `Mathlib/Analysis/Meromorphic/Basic.lean`; changed: attributes:added, name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
@[fun_prop]
def Meromorphic (f : 𝕜 → E) := ∀ x, MeromorphicAt f x
```

### `Meromorphic.fun_neg` (lemma, added) [700358ee26]
- file: `Mathlib/Analysis/Meromorphic/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[fun_prop]
lemma fun_neg (hf : Meromorphic f) : Meromorphic (fun x ↦ -f x ) := hf.neg
```

### `Meromorphic.sub` (lemma, added) [798155ff74]
- file: `Mathlib/Analysis/Meromorphic/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[fun_prop]
lemma sub (hf : Meromorphic f) (hg : Meromorphic g) :
    Meromorphic (f - g) := fun x ↦ (hf x).sub (hg x)
```

### `command in Basic.lean` (command, added) [8ba9a3328b]
- file: `Mathlib/Analysis/Meromorphic/Basic.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- A function is meromorphic iff it is meromorphic on Set.univ. -/
```

### `Meromorphic.prod` (theorem, added) [8e0dd32c0c]
- file: `Mathlib/Analysis/Meromorphic/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[fun_prop]
theorem prod (h : ∀ σ, Meromorphic (F σ)) :
    Meromorphic (∏ n ∈ s, F n) := fun x ↦ MeromorphicAt.prod (h · x)
```

### `Meromorphic.fun_zpow` (lemma, added) [9c9f244d3f]
- file: `Mathlib/Analysis/Meromorphic/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[fun_prop]
lemma fun_zpow {f : 𝕜 → 𝕜} {n : ℤ} (hf : Meromorphic f) : Meromorphic (fun x ↦ f x ^ n) := hf.zpow
```

### `Meromorphic.div` (lemma, added) [a049f464ff]
- file: `Mathlib/Analysis/Meromorphic/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[fun_prop]
lemma div {f g : 𝕜 → 𝕜} (hf : Meromorphic f) (hg : Meromorphic g) :
    Meromorphic (f / g) := fun x ↦ (hf x).div (hg x)
```

### `meromorphicOn_univ` (lemma, added) [b047408fb1]
- file: `Mathlib/Analysis/Meromorphic/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[simp]
lemma meromorphicOn_univ {f : 𝕜 → E} : MeromorphicOn f Set.univ ↔ Meromorphic f  := by tauto
```

### `namespace in Basic.lean` (command, added) [b35679c4e9]
- file: `Mathlib/Analysis/Meromorphic/Basic.lean`; changed: namespace:added
- as the PR leaves it:
```lean
namespace Meromorphic
```

### `Meromorphic.fun_prod` (theorem, added) [bb9ce0f5b9]
- file: `Mathlib/Analysis/Meromorphic/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[fun_prop]
theorem fun_prod (h : ∀ σ, Meromorphic (F σ)) :
    Meromorphic (fun x ↦ ∏ n ∈ s, F n x) := by
  simpa [← Finset.prod_apply] using (prod h)
```

### `Meromorphic.fun_pow` (lemma, added) [c1590edd92]
- file: `Mathlib/Analysis/Meromorphic/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[fun_prop]
lemma fun_pow {f : 𝕜 → 𝕜} {n : ℕ} (hf : Meromorphic f) : Meromorphic (fun x ↦ f x ^ n) := hf.pow
```

### `Meromorphic.deriv` (lemma, added) [c5261da73e]
- file: `Mathlib/Analysis/Meromorphic/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[fun_prop]
lemma deriv [CompleteSpace E] (hf : Meromorphic f) : Meromorphic (deriv f) := fun x ↦ (hf x).deriv
```

### `Meromorphic.fun_sum` (theorem, added) [c77d707bfd]
- file: `Mathlib/Analysis/Meromorphic/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[fun_prop]
theorem fun_sum (h : ∀ σ, Meromorphic (G σ)) :
    Meromorphic (fun x ↦ ∑ n ∈ s, G n x) := by
  simpa [← Finset.sum_apply] using (sum h)
```

### `section in Basic.lean` (command, added) [c7d6f9e619]
- file: `Mathlib/Analysis/Meromorphic/Basic.lean`; changed: namespace:added
- as the PR leaves it:
```lean
variable
  {ι : Type*} {s : Finset ι}
  {f g : 𝕜 → E} {F : ι → 𝕜 → 𝕜} {G : ι → 𝕜 → E}
```

### `Meromorphic.fun_sub` (lemma, added) [c9377759b3]
- file: `Mathlib/Analysis/Meromorphic/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[fun_prop]
lemma fun_sub (hf : Meromorphic f) (hg : Meromorphic g) :
    Meromorphic (fun x ↦ f x - g x) := hf.sub hg
```

### `Meromorphic.iterated_deriv` (lemma, added) [ce54ffd2ae]
- file: `Mathlib/Analysis/Meromorphic/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[fun_prop]
lemma iterated_deriv [CompleteSpace E] {n : ℕ} (hf : Meromorphic f) :
    Meromorphic (_root_.deriv^[n] f) := fun x ↦ (hf x).iterated_deriv
```

### `Meromorphic.fun_iterated_deriv` (lemma, added) [d690004f26]
- file: `Mathlib/Analysis/Meromorphic/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[fun_prop]
lemma fun_iterated_deriv [CompleteSpace E] {n : ℕ} (hf : Meromorphic f) :
    Meromorphic (fun x ↦ _root_.deriv^[n] f x) := hf.iterated_deriv
```

### `Meromorphic.sum` (theorem, added) [d832d44817]
- file: `Mathlib/Analysis/Meromorphic/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[fun_prop]
theorem sum (h : ∀ σ, Meromorphic (G σ)) :
    Meromorphic (∑ n ∈ s, G n) := fun x ↦ MeromorphicAt.sum (h · x)
```

### `Meromorphic.fun_add` (lemma, added) [e1da91dccf]
- file: `Mathlib/Analysis/Meromorphic/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[fun_prop]
lemma fun_add (hf : Meromorphic f) (hg : Meromorphic g) :
    Meromorphic (fun x ↦ f x + g x) := hf.add hg
```

### `Meromorphic.fun_mul` (lemma, added) [e34141ea91]
- file: `Mathlib/Analysis/Meromorphic/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[fun_prop]
lemma fun_mul {f g : 𝕜 → 𝕜} (hf : Meromorphic f) (hg : Meromorphic g) :
    Meromorphic (fun x ↦ f x * g x) := hf.mul hg
```

### `Meromorphic.neg` (lemma, added) [e747d454a0]
- file: `Mathlib/Analysis/Meromorphic/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[fun_prop]
lemma neg (hf : Meromorphic f) : Meromorphic (-f) := fun x ↦ (hf x).neg
```

### `Meromorphic.pow` (lemma, added) [e80cfef275]
- file: `Mathlib/Analysis/Meromorphic/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[fun_prop]
lemma pow {f : 𝕜 → 𝕜} {n : ℕ} (hf : Meromorphic f) : Meromorphic (f ^ n) := fun x ↦ (hf x).pow n
```

### `Meromorphic.mul` (lemma, added) [e8d42a00f1]
- file: `Mathlib/Analysis/Meromorphic/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[fun_prop]
lemma mul {f g : 𝕜 → 𝕜} (hf : Meromorphic f) (hg : Meromorphic g) :
    Meromorphic (f * g) := fun x ↦ (hf x).mul (hg x)
```

### `command in Basic.lean` (command, added) [e966bd3290]
- file: `Mathlib/Analysis/Meromorphic/Basic.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- Meromorphy of a function on all of 𝕜. -/
```

### `Meromorphic.zpow` (lemma, added) [ebf51d6bd9]
- file: `Mathlib/Analysis/Meromorphic/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[fun_prop]
lemma zpow {f : 𝕜 → 𝕜} {n : ℤ} (hf : Meromorphic f) : Meromorphic (f ^ n) := fun x ↦ (hf x).zpow n
```

### `Meromorphic.fun_div` (lemma, added) [f51d981856]
- file: `Mathlib/Analysis/Meromorphic/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[fun_prop]
lemma fun_div {f g : 𝕜 → 𝕜} (hf : Meromorphic f) (hg : Meromorphic g) :
    Meromorphic (fun x ↦ f x / g x) := hf.div hg
```

## Removed or renamed

- none

## Families (declarations that may be one decision)

- [exact] `Meromorphic.fun_prod`, `Meromorphic.prod` -- 2 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [exact] `Meromorphic.fun_sum`, `Meromorphic.sum` -- 2 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [exact] `Meromorphic.deriv`, `Meromorphic.div`, `Meromorphic.fun_deriv`, `Meromorphic.fun_div`, `Meromorphic.fun_iterated_deriv`, `Meromorphic.fun_pow`, `Meromorphic.fun_zpow`, `Meromorphic.iterated_deriv`, `Meromorphic.pow`, `Meromorphic.zpow` -- 10 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [exact] `Meromorphic`, `meromorphicOn_univ` -- 2 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [hypothesis] `Meromorphic.fun_add`, `Meromorphic.fun_deriv`, `Meromorphic.fun_div`, `Meromorphic.fun_iterated_deriv`, `Meromorphic.fun_mul`, `Meromorphic.fun_neg`, `Meromorphic.fun_pow`, `Meromorphic.fun_prod`, `Meromorphic.fun_sub`, `Meromorphic.fun_sum`, `Meromorphic.fun_zpow` -- 11 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [exact] `Meromorphic.add`, `Meromorphic.fun_add`, `Meromorphic.fun_neg`, `Meromorphic.neg` -- 4 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [exact] `Meromorphic.fun_mul`, `Meromorphic.fun_sub`, `Meromorphic.mul`, `Meromorphic.sub` -- 4 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings

## Relations between changed declarations

- changed_siblings [high]: `Meromorphic.add` -> `Meromorphic.fun_neg`
- changed_siblings [high]: `Meromorphic.add` -> `Meromorphic.fun_add`
- changed_siblings [high]: `Meromorphic.deriv` -> `Meromorphic.fun_zpow`
- changed_siblings [high]: `Meromorphic.deriv` -> `Meromorphic.fun_deriv`
- changed_siblings [high]: `Meromorphic.div` -> `Meromorphic.fun_div`
- changed_siblings [high]: `Meromorphic.fun_add` -> `Meromorphic.add`
- changed_siblings [high]: `Meromorphic.fun_deriv` -> `Meromorphic.deriv`
- changed_siblings [high]: `Meromorphic.fun_deriv` -> `Meromorphic.iterated_deriv`
- changed_siblings [high]: `Meromorphic.fun_div` -> `Meromorphic.pow`
- changed_siblings [high]: `Meromorphic.fun_div` -> `Meromorphic.div`
- changed_siblings [high]: `Meromorphic.fun_iterated_deriv` -> `Meromorphic.iterated_deriv`
- changed_siblings [high]: `Meromorphic.fun_mul` -> `Meromorphic.mul`
- changed_siblings [high]: `Meromorphic.fun_neg` -> `Meromorphic.neg`
- changed_siblings [high]: `Meromorphic.fun_neg` -> `Meromorphic.add`
- changed_siblings [high]: `Meromorphic.fun_pow` -> `Meromorphic.zpow`
- changed_siblings [high]: `Meromorphic.fun_pow` -> `Meromorphic.pow`
- changed_siblings [high]: `Meromorphic.fun_prod` -> `Meromorphic.prod`
- changed_siblings [high]: `Meromorphic.fun_sub` -> `Meromorphic.sub`
- changed_siblings [high]: `Meromorphic.fun_sub` -> `Meromorphic.mul`
- changed_siblings [high]: `Meromorphic.fun_sum` -> `Meromorphic.sum`
- changed_siblings [high]: `Meromorphic.fun_zpow` -> `Meromorphic.zpow`
- changed_siblings [high]: `Meromorphic.fun_zpow` -> `Meromorphic.deriv`
- changed_siblings [high]: `Meromorphic.iterated_deriv` -> `Meromorphic.fun_deriv`
- changed_siblings [high]: `Meromorphic.iterated_deriv` -> `Meromorphic.fun_iterated_deriv`
- changed_siblings [high]: `Meromorphic.mul` -> `Meromorphic.fun_mul`
- changed_siblings [high]: `Meromorphic.mul` -> `Meromorphic.fun_sub`
- changed_siblings [high]: `Meromorphic.neg` -> `Meromorphic.fun_neg`
- changed_siblings [high]: `Meromorphic.pow` -> `Meromorphic.fun_div`
- changed_siblings [high]: `Meromorphic.pow` -> `Meromorphic.fun_pow`
- changed_siblings [high]: `Meromorphic.prod` -> `Meromorphic.fun_prod`
- changed_siblings [high]: `Meromorphic.sub` -> `Meromorphic.fun_sub`
- changed_siblings [high]: `Meromorphic.sum` -> `Meromorphic.fun_sum`
- changed_siblings [high]: `Meromorphic.zpow` -> `Meromorphic.fun_zpow`
- changed_siblings [high]: `Meromorphic.zpow` -> `Meromorphic.fun_pow`
- declaration_dependency [exact]: `Meromorphic.add` -> `Meromorphic`
- declaration_dependency [exact]: `Meromorphic.deriv` -> `Meromorphic`
- declaration_dependency [exact]: `Meromorphic.div` -> `Meromorphic`
- declaration_dependency [exact]: `Meromorphic.fun_add` -> `Meromorphic`
- declaration_dependency [exact]: `Meromorphic.fun_deriv` -> `Meromorphic`
- declaration_dependency [exact]: `Meromorphic.fun_div` -> `Meromorphic`
- declaration_dependency [exact]: `Meromorphic.fun_iterated_deriv` -> `Meromorphic`
- declaration_dependency [exact]: `Meromorphic.fun_mul` -> `Meromorphic`
- declaration_dependency [exact]: `Meromorphic.fun_neg` -> `Meromorphic`
- declaration_dependency [exact]: `Meromorphic.fun_pow` -> `Meromorphic`
- declaration_dependency [exact]: `Meromorphic.fun_prod` -> `Meromorphic`
- declaration_dependency [exact]: `Meromorphic.fun_sub` -> `Meromorphic`
- declaration_dependency [exact]: `Meromorphic.fun_sum` -> `Meromorphic`
- declaration_dependency [exact]: `Meromorphic.fun_zpow` -> `Meromorphic`
- declaration_dependency [exact]: `Meromorphic.iterated_deriv` -> `Meromorphic`
- declaration_dependency [exact]: `Meromorphic.mul` -> `Meromorphic`
- declaration_dependency [exact]: `Meromorphic.neg` -> `Meromorphic`
- declaration_dependency [exact]: `Meromorphic.pow` -> `Meromorphic`
- declaration_dependency [exact]: `Meromorphic.prod` -> `Meromorphic`
- declaration_dependency [exact]: `Meromorphic.sub` -> `Meromorphic`
- declaration_dependency [exact]: `Meromorphic.sum` -> `Meromorphic`
- declaration_dependency [exact]: `Meromorphic.zpow` -> `Meromorphic`
- declaration_dependency [exact]: `meromorphicOn_univ` -> `Meromorphic`
- direct_use_of_changed_declaration [exact]: `Meromorphic.fun_iterated_deriv` -> `Meromorphic.iterated_deriv`
- name_family [high]: `Meromorphic` -> `meromorphicOn_univ`
- name_family [high]: `Meromorphic.fun_iterated_deriv` -> `Meromorphic.iterated_deriv`
- name_family [high]: `Meromorphic.iterated_deriv` -> `Meromorphic.fun_iterated_deriv`
- name_family [high]: `meromorphicOn_univ` -> `Meromorphic`
