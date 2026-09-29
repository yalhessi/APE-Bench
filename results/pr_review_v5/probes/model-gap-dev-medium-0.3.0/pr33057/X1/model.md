# The PR model for #33057 (pass 0)

Built deterministically from the diff and the change graph, with no review text. Every entry is a **fact** unless marked `hypothesis`; a hypothesis is a question to check, not a premise. Not built, so not here: library candidates, the area's twin patterns and conventions, and other open PRs. Construct what you need of those with the tools.

## The PR

- title: chore(RingTheory/PowerSeries/Expand): tidy up some proofs
- description: remove `erw`, `classical`, reduce to proofs about MvPowerSeries
- changed files: Mathlib/RingTheory/PowerSeries/Expand.lean

## Objects

### `PowerSeries.support_expand` (theorem, modified) [02556c2f8f]
- file: `Mathlib/RingTheory/PowerSeries/Expand.lean`; changed: proof:modified
- before the PR:
```lean
theorem support_expand (φ : PowerSeries R) :
    (expand p hp φ).support = φ.support.image (p • ·) := by
  classical
  erw [MvPowerSeries.support_expand]
```
- as the PR leaves it:
```lean
theorem support_expand (φ : PowerSeries R) :
    (expand p hp φ).support = φ.support.image (p • ·) := by
  rw [expand, MvPowerSeries.support_expand]
```

### `PowerSeries.expand_mul_eq_comp` (theorem, modified) [077fe4217e]
- file: `Mathlib/RingTheory/PowerSeries/Expand.lean`; changed: proof:modified
- before the PR:
```lean
theorem expand_mul_eq_comp (q : ℕ) (hq : q ≠ 0) :
    expand (p * q) (p.mul_ne_zero hp hq) = (expand p hp (R := R)).comp (expand q hq) := by
  ext1 i
  unfold expand
  erw [MvPowerSeries.expand_mul_eq_comp p hp q hq]
```
- as the PR leaves it:
```lean
theorem expand_mul_eq_comp (q : ℕ) (hq : q ≠ 0) :
    expand (p * q) (p.mul_ne_zero hp hq) = (expand p hp (R := R)).comp (expand q hq) := by
  ext1 i
  simp [expand, MvPowerSeries.expand_mul_eq_comp p hp q hq]
```

### `PowerSeries.coeff_expand_of_not_dvd` (theorem, modified) [0978d2da45]
- file: `Mathlib/RingTheory/PowerSeries/Expand.lean`; changed: proof:modified
- before the PR:
```lean
theorem coeff_expand_of_not_dvd (φ : PowerSeries R) {m : ℕ} (h : ¬ p ∣ m) :
    (expand p hp φ).coeff m = 0 := by
  classical
  erw [coeff, MvPowerSeries.coeff_expand_of_not_dvd p hp φ (i := ())]
  simpa
```
- as the PR leaves it:
```lean
theorem coeff_expand_of_not_dvd (φ : PowerSeries R) {m : ℕ} (h : ¬ p ∣ m) :
    (expand p hp φ).coeff m = 0 := by
  rw [coeff, expand, MvPowerSeries.coeff_expand_of_not_dvd (i := ())]
  simpa
```

### `PowerSeries.expand_monomial` (theorem, modified) [3b02246a52]
- file: `Mathlib/RingTheory/PowerSeries/Expand.lean`; changed: proof:modified
- before the PR:
```lean
@[simp]
theorem expand_monomial (d : ℕ) (r : R) :
    expand p hp (monomial d r) = monomial (p * d) r := by
  unfold expand
  erw [MvPowerSeries.expand_monomial]
  simp [monomial]
```
- as the PR leaves it:
```lean
@[simp]
theorem expand_monomial (d : ℕ) (r : R) :
    expand p hp (monomial d r) = monomial (p * d) r := by
  simp [expand, monomial, MvPowerSeries.expand_monomial]
```

### `PowerSeries.map_expand` (theorem, modified) [51c3beefa7]
- file: `Mathlib/RingTheory/PowerSeries/Expand.lean`; changed: proof:modified
- before the PR:
```lean
@[simp]
theorem map_expand (f : R →+* S) (φ : PowerSeries R) :
    map f (expand p hp φ) = expand p hp (map f φ) := by
  erw [expand_apply, map_subst (HasSubst.X_pow hp), map_pow, map_X, expand_apply]

/- TODO : In the original file of multi variate polynomial, there are two theorem about rename
here, but we don't have rename for multi variate power series. And for `eval₂Hom`, `eval₂`
and `aevel`, the expression does't look good. -/
```
- as the PR leaves it:
```lean
@[simp]
theorem map_expand (f : R →+* S) (φ : PowerSeries R) :
    map f (expand p hp φ) = expand p hp (map f φ) := by
  simp [map, expand, MvPowerSeries.map_expand]

/- TODO : In the original file of multi variate polynomial, there are two theorem about rename
here, but we don't have rename for multi variate power series. And for `eval₂Hom`, `eval₂`
and `aevel`, the expression does't look good. -/
```

### `PowerSeries.coeff_expand_mul` (theorem, modified) [529aecebaa]
- file: `Mathlib/RingTheory/PowerSeries/Expand.lean`; changed: proof:modified
- before the PR:
```lean
@[simp]
theorem coeff_expand_mul (φ : PowerSeries R) (m : ℕ) :
    (expand p hp φ).coeff (p * m) = φ.coeff m := by
  classical
  erw [coeff, ← smul_eq_mul, (Finsupp.smul_single p () m).symm, MvPowerSeries.coeff_expand_smul]
  rfl
```
- as the PR leaves it:
```lean
@[simp]
theorem coeff_expand_mul (φ : PowerSeries R) (m : ℕ) :
    (expand p hp φ).coeff (p * m) = φ.coeff m := by
  rw [coeff, coeff, expand, ← smul_eq_mul, ← Finsupp.smul_single, MvPowerSeries.coeff_expand_smul]
```

### `PowerSeries.expand_apply` (theorem, modified) [9ce69ee855]
- file: `Mathlib/RingTheory/PowerSeries/Expand.lean`; changed: proof:modified
- before the PR:
```lean
theorem expand_apply (f : PowerSeries R) : expand p hp f = subst (X ^ p) f := by
  simp only [expand, MvPowerSeries.expand, MvPowerSeries.substAlgHom_apply]
  rfl
```
- as the PR leaves it:
```lean
theorem expand_apply (f : PowerSeries R) : expand p hp f = subst (X ^ p) f := by
  simp only [expand, MvPowerSeries.expand, subst, X]
```

### `PowerSeries.support_expand_subset` (theorem, modified) [c7d4a9defe]
- file: `Mathlib/RingTheory/PowerSeries/Expand.lean`; changed: proof:modified
- before the PR:
```lean
theorem support_expand_subset (φ : PowerSeries R) :
    (expand p hp φ).support ⊆ φ.support.image (p • ·) := by
  erw [MvPowerSeries.support_expand]
```
- as the PR leaves it:
```lean
theorem support_expand_subset (φ : PowerSeries R) :
    (expand p hp φ).support ⊆ φ.support.image (p • ·) := by
  rw [expand, MvPowerSeries.support_expand]
```

## Removed or renamed

- none

## Families (declarations that may be one decision)

- [hypothesis] `PowerSeries.coeff_expand_mul`, `PowerSeries.coeff_expand_of_not_dvd` -- 2 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [hypothesis] `PowerSeries.expand_apply`, `PowerSeries.expand_monomial`, `PowerSeries.expand_mul_eq_comp` -- 3 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [exact] `PowerSeries.coeff_expand_mul`, `PowerSeries.coeff_expand_of_not_dvd`, `PowerSeries.support_expand`, `PowerSeries.support_expand_subset` -- 4 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [hypothesis] `PowerSeries.support_expand`, `PowerSeries.support_expand_subset` -- 2 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it

## Relations between changed declarations

- changed_siblings [high]: `PowerSeries.coeff_expand_mul` -> `PowerSeries.coeff_expand_of_not_dvd`
- changed_siblings [high]: `PowerSeries.coeff_expand_of_not_dvd` -> `PowerSeries.support_expand_subset`
- changed_siblings [high]: `PowerSeries.coeff_expand_of_not_dvd` -> `PowerSeries.coeff_expand_mul`
- changed_siblings [high]: `PowerSeries.support_expand` -> `PowerSeries.support_expand_subset`
- changed_siblings [high]: `PowerSeries.support_expand_subset` -> `PowerSeries.support_expand`
- changed_siblings [high]: `PowerSeries.support_expand_subset` -> `PowerSeries.coeff_expand_of_not_dvd`
- direct_use_of_changed_declaration [exact]: `PowerSeries.support_expand_subset` -> `PowerSeries.support_expand`
- name_family [high]: `PowerSeries.support_expand` -> `PowerSeries.support_expand_subset`
- name_family [high]: `PowerSeries.support_expand_subset` -> `PowerSeries.support_expand`
