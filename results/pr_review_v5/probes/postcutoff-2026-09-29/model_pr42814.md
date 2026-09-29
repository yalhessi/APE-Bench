# The PR model for #42814 (pass 0)

Built deterministically from the diff and the change graph, with no review text. Every entry is a **fact** unless marked `hypothesis`; a hypothesis is a question to check, not a premise. Not built, so not here: library candidates, the area's twin patterns and conventions, and other open PRs. Construct what you need of those with the tools.

## The PR

- title: feat(NumberTheory/FundamentalDiscriminant): fundamental discriminants
- description: (not recoverable at review start)
- changed files: Mathlib.lean, Mathlib/Data/Nat/Prime/Basic.lean, Mathlib/Data/Nat/Squarefree.lean, Mathlib/NumberTheory/FundamentalDiscriminant.lean, Mathlib/RingTheory/Coprime/Basic.lean

## Objects

### `import in Mathlib.lean` (import, modified) [9dbdba232c]
- file: `Mathlib.lean`; changed: imports:added

### `doc_comment in Basic.lean` (command, added) [bae06b753c]
- file: `Mathlib/Data/Nat/Prime/Basic.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-- To prove a property of all primes, it is enough to prove it for `2` and for the odd primes. -/
```

### `Nat.forall_prime_iff_two_and_odd` (theorem, added) [c75498d05e]
- file: `Mathlib/Data/Nat/Prime/Basic.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem forall_prime_iff_two_and_odd {P : ℕ → Prop} :
    (∀ p, p.Prime → P p) ↔ P 2 ∧ ∀ p, p.Prime → Odd p → P p := by
  refine ⟨fun h ↦ ⟨h 2 prime_two, fun p hp _ ↦ h p hp⟩, fun h p hp ↦ ?_⟩
  obtain rfl | hne := eq_or_ne p 2
  · exact h.1
  · exact h.2 p hp (hp.odd_of_ne_two hne)
```

### `doc_comment in Squarefree.lean` (command, added) [3037c440c3]
- file: `Mathlib/Data/Nat/Squarefree.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-- An integer is squarefree iff no prime square divides it. -/
```

### `Int.squarefree_iff_prime_sq_not_dvd` (theorem, added) [3408b0e98b]
- file: `Mathlib/Data/Nat/Squarefree.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem squarefree_iff_prime_sq_not_dvd {n : ℤ} :
    Squarefree n ↔ ∀ p : ℕ, p.Prime → ¬ (p : ℤ) ^ 2 ∣ n := by
  have bridge : ∀ p : ℕ, (p : ℤ) ^ 2 ∣ n ↔ p * p ∣ n.natAbs := fun p => by
    rw [show ((p : ℤ) ^ 2) = ((p * p : ℕ) : ℤ) by push_cast; ring, Int.natCast_dvd]
  rw [← Int.squarefree_natAbs, Nat.squarefree_iff_prime_squarefree]
  exact ⟨fun h p hp hdvd => h p hp ((bridge p).mp hdvd),
         fun h x hx hdvd => h x hx ((bridge x).mpr hdvd)⟩
```

### `namespace in Squarefree.lean` (command, added) [742ffe2c2a]
- file: `Mathlib/Data/Nat/Squarefree.lean`; changed: namespace:added
- as the PR leaves it:
```lean
namespace Int
```

### `section in Squarefree.lean` (command, added) [c247f41ae7]
- file: `Mathlib/Data/Nat/Squarefree.lean`; changed: namespace:added
- as the PR leaves it:
```lean
end Int

-- Porting note: comment out NormNum tactic, to be moved to another file.
/-
```

### `module_doc in FundamentalDiscriminant.lean` (module_doc, added) [41a8dafdcf]
- file: `Mathlib/NumberTheory/FundamentalDiscriminant.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-!
# Fundamental discriminants

A fundamental discriminant is an integer `D ≡ 0, 1 mod 4` that is primitive, i.e. not a proper
square multiple of a smaller discriminant. These are exactly the discriminants of quadratic fields.

The definition and the results below are elementary arithmetic on `ℤ`, so this file is kept
independent of the theory of quadratic fields.

## Main definitions

* `Int.IsFundamentalDiscr`: `D` is a fundamental discriminant.

## Main results

* `Int.isFundamentalDiscr_iff_squarefree`: the concrete squarefree characterization, `D ≡ 1 mod 4`
  squarefree or `D = 4m` with `m` squarefree and `m ≡ 2, 3 mod 4`.
* `Int.isFundamentalDiscr_four_mul_add_one`: `4m + 1` is a fundamental discriminant if and only if
  it is squarefree.
* `Int.isFundamentalDiscr_four_mul`: `4m` is a fundamental discriminant if and only if `m` is
  squarefree and `m ≡ 2, 3 mod 4`.
-/
```

### `section in FundamentalDiscriminant.lean` (command, added) [60d810a205]
- file: `Mathlib/NumberTheory/FundamentalDiscriminant.lean`; changed: namespace:added
- as the PR leaves it:
```lean
end Int
```

### `Int.IsFundamentalDiscr` (def, added) [795e06c697]
- file: `Mathlib/NumberTheory/FundamentalDiscriminant.lean`; changed: name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
def IsFundamentalDiscr (D : ℤ) : Prop :=
  (D % 4 = 0 ∨ D % 4 = 1) ∧ (∀ x, D = 4 * x → ¬ 4 ∣ x ∧ x % 4 ≠ 1) ∧
    ∀ p : ℕ, p.Prime → Odd p → ¬ (p : ℤ) ^ 2 ∣ D
```

### `namespace in FundamentalDiscriminant.lean` (command, added) [7d45dab206]
- file: `Mathlib/NumberTheory/FundamentalDiscriminant.lean`; changed: namespace:added
- as the PR leaves it:
```lean
namespace Int
```

### `Int.isFundamentalDiscr_iff_squarefree` (theorem, added) [7ef4afa562]
- file: `Mathlib/NumberTheory/FundamentalDiscriminant.lean`; changed: documentation:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem isFundamentalDiscr_iff_squarefree {D : ℤ} :
    IsFundamentalDiscr D ↔
      (D % 4 = 1 ∧ Squarefree D) ∨
        (D % 4 = 0 ∧ Squarefree (D / 4) ∧ (D / 4 % 4 = 2 ∨ D / 4 % 4 = 3)) := by
  -- The two `have`s below are picked up from the context by the `grind` calls at the end.
  have {m} : Squarefree m ↔ ¬ 4 ∣ m ∧ ∀ p : ℕ, p.Prime → Odd p → ¬ (p : ℤ) ^ 2 ∣ m := by
    rw [squarefree_iff_prime_sq_not_dvd, Nat.forall_prime_iff_two_and_odd]
    simp
  have {m p : ℤ} (hp : Odd p) : p ^ 2 ∣ 4 * m ↔ p ^ 2 ∣ m := by
    rw [show (4 : ℤ) = 2 ^ 2 by norm_num]
    exact (IsCoprime.pow hp.isCoprime_two).dvd_mul_left_iff
  by_cases h : 4 ∣ D
  · obtain ⟨d, rfl⟩ := h
    simp +contextual only [Int.mul_ediv_cancel_left d four_ne_zero]
    grind [isFundamentalDiscr_def]
  · grind [isFundamentalDiscr_def]
```

### `Int.IsFundamentalDiscr.emod_four_eq_zero_or_one` (theorem, added) [83a294b24e]
- file: `Mathlib/NumberTheory/FundamentalDiscriminant.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem IsFundamentalDiscr.emod_four_eq_zero_or_one {D : ℤ} (h : IsFundamentalDiscr D) :
    D % 4 = 0 ∨ D % 4 = 1 := h.1
```

### `attribute in FundamentalDiscriminant.lean` (command, added) [9494ef5316]
- file: `Mathlib/NumberTheory/FundamentalDiscriminant.lean`; changed: unknown:added
- as the PR leaves it:
```lean
@[expose] public section
```

### `Int.isFundamentalDiscr_def` (theorem, added) [9c492eaabf]
- file: `Mathlib/NumberTheory/FundamentalDiscriminant.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem isFundamentalDiscr_def {D : ℤ} :
    IsFundamentalDiscr D ↔
      (D % 4 = 0 ∨ D % 4 = 1) ∧ (∀ x, D = 4 * x → ¬ 4 ∣ x ∧ x % 4 ≠ 1) ∧
        ∀ p : ℕ, p.Prime → Odd p → ¬ (p : ℤ) ^ 2 ∣ D := Iff.rfl
```

### `Int.isFundamentalDiscr_four_mul` (theorem, added) [a2af8956df]
- file: `Mathlib/NumberTheory/FundamentalDiscriminant.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem isFundamentalDiscr_four_mul {m : ℤ} :
    IsFundamentalDiscr (4 * m) ↔ Squarefree m ∧ (m % 4 = 2 ∨ m % 4 = 3) := by
  simp [isFundamentalDiscr_iff_squarefree]
```

### `Int.IsFundamentalDiscr.ne_zero` (theorem, added) [ce611a8a6e]
- file: `Mathlib/NumberTheory/FundamentalDiscriminant.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem IsFundamentalDiscr.ne_zero {D : ℤ} (h : IsFundamentalDiscr D) : D ≠ 0 := by
  grind [isFundamentalDiscr_def]
```

### `Int.isFundamentalDiscr_four_mul_add_one` (theorem, added) [cf6b5882a8]
- file: `Mathlib/NumberTheory/FundamentalDiscriminant.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem isFundamentalDiscr_four_mul_add_one {m : ℤ} :
    IsFundamentalDiscr (4 * m + 1) ↔ Squarefree (4 * m + 1) := by
  simp [isFundamentalDiscr_iff_squarefree]
```

### `doc_comment in FundamentalDiscriminant.lean` (command, added) [e13ae5be7d]
- file: `Mathlib/NumberTheory/FundamentalDiscriminant.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-- `D` is a fundamental discriminant if and only if either `D ≡ 1 mod 4` and `D` is squarefree,
or `D = 4 * d` with `d` squarefree and `d ≡ 2, 3 mod 4`. -/
```

### `doc_comment in FundamentalDiscriminant.lean` (command, added) [fbc25f171a]
- file: `Mathlib/NumberTheory/FundamentalDiscriminant.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-- `D` is a fundamental discriminant: it is a discriminant (`D ≡ 0, 1 mod 4`) and primitive,
i.e. `D / 4 ≢ 0, 1 mod 4` when `4 ∣ D`, and no odd prime square divides `D`. -/
```

### `Odd.isCoprime_two` (theorem, added) [33db2e0dae]
- file: `Mathlib/RingTheory/Coprime/Basic.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem _root_.Odd.isCoprime_two {x : R} (h : Odd x) : IsCoprime x 2 := by
  obtain ⟨m, rfl⟩ := h
  exact add_one_left_of_dvd ⟨m, rfl⟩
```

### `IsCoprime.dvd_mul_left_iff` (theorem, added) [4478d03734]
- file: `Mathlib/RingTheory/Coprime/Basic.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem IsCoprime.dvd_mul_left_iff (H : IsCoprime x y) : x ∣ y * z ↔ x ∣ z :=
  ⟨H.dvd_of_dvd_mul_left, fun h ↦ h.mul_left y⟩
```

### `IsCoprime.dvd_mul_right_iff` (theorem, added) [bf8cec1083]
- file: `Mathlib/RingTheory/Coprime/Basic.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem IsCoprime.dvd_mul_right_iff (H : IsCoprime x z) : x ∣ y * z ↔ x ∣ y :=
  ⟨H.dvd_of_dvd_mul_right, fun h ↦ h.mul_right z⟩
```

## Removed or renamed

- none

## Families (declarations that may be one decision)

- [exact] `Int.IsFundamentalDiscr`, `Int.IsFundamentalDiscr.emod_four_eq_zero_or_one`, `Int.IsFundamentalDiscr.ne_zero`, `Int.isFundamentalDiscr_def`, `Int.isFundamentalDiscr_four_mul`, `Int.isFundamentalDiscr_four_mul_add_one`, `Int.isFundamentalDiscr_iff_squarefree`, `Int.squarefree_iff_prime_sq_not_dvd` -- 8 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [hypothesis] `Int.IsFundamentalDiscr`, `Int.isFundamentalDiscr_def`, `Int.isFundamentalDiscr_four_mul`, `Int.isFundamentalDiscr_four_mul_add_one`, `Int.isFundamentalDiscr_iff_squarefree` -- 5 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [exact] `IsCoprime.dvd_mul_left_iff`, `IsCoprime.dvd_mul_right_iff` -- 2 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings

## Relations between changed declarations

- changed_siblings [high]: `Int.IsFundamentalDiscr.emod_four_eq_zero_or_one` -> `Int.IsFundamentalDiscr.ne_zero`
- changed_siblings [high]: `Int.IsFundamentalDiscr.ne_zero` -> `Int.isFundamentalDiscr_def`
- changed_siblings [high]: `Int.IsFundamentalDiscr.ne_zero` -> `Int.IsFundamentalDiscr.emod_four_eq_zero_or_one`
- changed_siblings [high]: `Int.isFundamentalDiscr_def` -> `Int.IsFundamentalDiscr.ne_zero`
- changed_siblings [high]: `Int.isFundamentalDiscr_four_mul` -> `Int.isFundamentalDiscr_four_mul_add_one`
- changed_siblings [high]: `Int.isFundamentalDiscr_four_mul_add_one` -> `Int.isFundamentalDiscr_four_mul`
- changed_siblings [high]: `Int.isFundamentalDiscr_four_mul_add_one` -> `Int.isFundamentalDiscr_iff_squarefree`
- changed_siblings [high]: `Int.isFundamentalDiscr_iff_squarefree` -> `Int.isFundamentalDiscr_four_mul_add_one`
- changed_siblings [high]: `IsCoprime.dvd_mul_left_iff` -> `IsCoprime.dvd_mul_right_iff`
- changed_siblings [high]: `IsCoprime.dvd_mul_right_iff` -> `IsCoprime.dvd_mul_left_iff`
- declaration_dependency [exact]: `Int.IsFundamentalDiscr.emod_four_eq_zero_or_one` -> `Int.IsFundamentalDiscr`
- declaration_dependency [exact]: `Int.IsFundamentalDiscr.ne_zero` -> `Int.IsFundamentalDiscr`
- declaration_dependency [exact]: `Int.isFundamentalDiscr_def` -> `Int.IsFundamentalDiscr`
- declaration_dependency [exact]: `Int.isFundamentalDiscr_four_mul` -> `Int.IsFundamentalDiscr`
- declaration_dependency [exact]: `Int.isFundamentalDiscr_four_mul_add_one` -> `Int.IsFundamentalDiscr`
- declaration_dependency [exact]: `Int.isFundamentalDiscr_iff_squarefree` -> `Int.IsFundamentalDiscr`
- direct_use_of_changed_declaration [exact]: `Int.IsFundamentalDiscr.ne_zero` -> `Int.isFundamentalDiscr_def`
- direct_use_of_changed_declaration [exact]: `Int.isFundamentalDiscr_four_mul` -> `Int.isFundamentalDiscr_iff_squarefree`
- direct_use_of_changed_declaration [exact]: `Int.isFundamentalDiscr_four_mul_add_one` -> `Int.isFundamentalDiscr_iff_squarefree`
- direct_use_of_changed_declaration [exact]: `Int.isFundamentalDiscr_iff_squarefree` -> `IsCoprime.dvd_mul_left_iff`
- direct_use_of_changed_declaration [exact]: `Int.isFundamentalDiscr_iff_squarefree` -> `Int.isFundamentalDiscr_def`
- direct_use_of_changed_declaration [exact]: `Int.isFundamentalDiscr_iff_squarefree` -> `Int.squarefree_iff_prime_sq_not_dvd`
- direct_use_of_changed_declaration [exact]: `Int.isFundamentalDiscr_iff_squarefree` -> `Nat.forall_prime_iff_two_and_odd`
- direct_use_of_changed_declaration [exact]: `Int.isFundamentalDiscr_iff_squarefree` -> `Odd.isCoprime_two`
- name_family [high]: `Int.IsFundamentalDiscr` -> `Int.isFundamentalDiscr_iff_squarefree`
- name_family [high]: `Int.IsFundamentalDiscr` -> `Int.isFundamentalDiscr_four_mul_add_one`
- name_family [high]: `Int.IsFundamentalDiscr` -> `Int.isFundamentalDiscr_four_mul`
- name_family [high]: `Int.IsFundamentalDiscr` -> `Int.isFundamentalDiscr_def`
- name_family [high]: `Int.isFundamentalDiscr_def` -> `Int.IsFundamentalDiscr`
- name_family [high]: `Int.isFundamentalDiscr_def` -> `Int.isFundamentalDiscr_four_mul`
- name_family [high]: `Int.isFundamentalDiscr_def` -> `Int.isFundamentalDiscr_four_mul_add_one`
- name_family [high]: `Int.isFundamentalDiscr_def` -> `Int.isFundamentalDiscr_iff_squarefree`
- name_family [high]: `Int.isFundamentalDiscr_four_mul` -> `Int.isFundamentalDiscr_four_mul_add_one`
- name_family [high]: `Int.isFundamentalDiscr_four_mul` -> `Int.IsFundamentalDiscr`
- name_family [high]: `Int.isFundamentalDiscr_four_mul` -> `Int.isFundamentalDiscr_iff_squarefree`
- name_family [high]: `Int.isFundamentalDiscr_four_mul` -> `Int.isFundamentalDiscr_def`
- name_family [high]: `Int.isFundamentalDiscr_four_mul_add_one` -> `Int.isFundamentalDiscr_four_mul`
- name_family [high]: `Int.isFundamentalDiscr_four_mul_add_one` -> `Int.isFundamentalDiscr_iff_squarefree`
- name_family [high]: `Int.isFundamentalDiscr_four_mul_add_one` -> `Int.isFundamentalDiscr_def`
- name_family [high]: `Int.isFundamentalDiscr_four_mul_add_one` -> `Int.IsFundamentalDiscr`
- name_family [high]: `Int.isFundamentalDiscr_iff_squarefree` -> `Int.isFundamentalDiscr_def`
- name_family [high]: `Int.isFundamentalDiscr_iff_squarefree` -> `Int.IsFundamentalDiscr`
- name_family [high]: `Int.isFundamentalDiscr_iff_squarefree` -> `Int.isFundamentalDiscr_four_mul`
- name_family [high]: `Int.isFundamentalDiscr_iff_squarefree` -> `Int.squarefree_iff_prime_sq_not_dvd`
- name_family [high]: `Int.isFundamentalDiscr_iff_squarefree` -> `Int.isFundamentalDiscr_four_mul_add_one`
- name_family [high]: `Int.squarefree_iff_prime_sq_not_dvd` -> `Int.isFundamentalDiscr_iff_squarefree`
