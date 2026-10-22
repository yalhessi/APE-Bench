# Decision context: fundamental discriminants

Twelve sources (S1-S12), grouped under nine decisions. A source that bears on more than one decision is
listed once and referred to by number elsewhere.

Searches that found nothing at the base commit:
- no occurrence of "fundamental discriminant" in any spelling;
- no `IsQuadraticField`, no `ℚ(√d)` type, and no use of `Squarefree` under
  `Mathlib/NumberTheory/NumberField` or `Mathlib/Algebra/QuadraticAlgebra`;
- no `Decidable` instance for `Squarefree` on ℤ;
- no ℤ statement of `Squarefree` through prime squares. The ℕ form is
  `Nat.squarefree_iff_prime_squarefree` (`Mathlib/Data/Nat/Squarefree.lean:47`).

## 1. Whether D = 1 counts

The same family of files also has `abs_discr_gt_two (h : 1 < finrank ℚ K)`
(`Mathlib/NumberTheory/NumberField/Discriminant/Basic.lean:273`), which treats ℚ separately from
nontrivial fields.

**S1 — `library_example`** — `Mathlib/NumberTheory/NumberField/Discriminant/Defs.lean:73`
```lean
/-- The absolute discriminant of the number field `ℚ` is 1. -/
@[simp]
theorem numberField_discr : discr ℚ = 1 := by
```
Mathlib's number-field discriminant already gives ℚ the value 1, which bears on reading (i), where 1 is
the discriminant of ℚ.

**S2 — `library_example`** — `Mathlib/Algebra/Squarefree/Basic.lean:40`
```lean
/-- An element of a monoid is squarefree if the only squares that
  divide it are the squares of units. -/
def Squarefree [Monoid R] (r : R) : Prop :=
  ∀ x : R, x * x ∣ r → IsUnit x

theorem IsRelPrime.of_squarefree_mul [CommMonoid R] {m n : R} (h : Squarefree (m * n)) :
    IsRelPrime m n := fun c hca hcb ↦ h c (mul_dvd_mul hca hcb)

@[simp]
theorem IsUnit.squarefree [CommMonoid R] {x : R} (h : IsUnit x) : Squarefree x := fun _ hdvd =>
  isUnit_of_mul_isUnit_left (isUnit_of_dvd_unit hdvd h)

theorem squarefree_one [CommMonoid R] : Squarefree (1 : R) :=
  isUnit_one.squarefree
```
`Squarefree (1 : ℤ)` holds and 1 ≡ 1 (mod 4), so a definition built on "squarefree and ≡ 1 (mod 4)"
includes D = 1 unless it is excluded explicitly.

**S3 — `earlier_decision`** — Zulip, #Is-there-code-for-X? > Zsqrtd and adjoin, Suzuka Yu, 2025-04-08
```
Sure! Thanks for reminding me, I'll exclude the situation where `d` is unit  ```Lean4 import Mathlib  open Zsqrtd  variable {d : ℤ} (hd : Squarefree d) (hunit : ¬ IsUnit d) -- or (hnon : Nonsquare d.natAbs)?  example : ℤ√d ≃+* Algebra.adjoin ℤ {(d : ℂ) ^ (1 / 2 : ℂ)} := by   sorry ```
```
Once reminded, a contributor working with squarefree `d` excluded the unit case through an extra
hypothesis (`¬ IsUnit d`) and left an alternative open (`Nonsquare`); the only reason given is the
reminder.

## 2. Which description serves as the definition

S2 bears here too: Mathlib's `Squarefree` is stated through units, while section 2 of the brief states
the excluded shape as `f²·E` with `f ≥ 2`.

**S4 — `library_example`** — `Mathlib/Algebra/Squarefree/Basic.lean:322`
```lean
namespace Int

@[simp]
theorem squarefree_natAbs {n : ℤ} : Squarefree n.natAbs ↔ Squarefree n := by
  simp_rw [Squarefree, natAbs_surjective.forall, ← natAbs_mul, natAbs_dvd_natAbs,
    isUnit_iff_natAbs_eq, Nat.isUnit_iff]

@[simp]
theorem squarefree_natCast {n : ℕ} : Squarefree (n : ℤ) ↔ Squarefree n := by
  rw [← squarefree_natAbs, natAbs_natCast]

end Int
```
These two simp lemmas are all the ℤ-specific `Squarefree` API that was found, which bears on how far a
definition over ℤ can lean on the ℕ API through `natAbs` rather than on ℤ lemmas.

**S5 — `library_example`** — `Mathlib/Algebra/QuadraticAlgebra/Discr.lean:39`
```lean
/-- The discriminant of the quadratic algebra `QuadraticAlgebra R a b`, that is, the
discriminant `b ^ 2 + 4 * a` of the polynomial `X ^ 2 - b * X - a`. -/
def discr [CommSemiring R] (a b : R) : R := b ^ 2 + 4 * a

theorem discr_def [CommSemiring R] (a b : R) : discr a b = b ^ 2 + 4 * a := rfl

/-- Under the change of generator `ω ↦ u • ω + k` (see `QuadraticAlgebra.changeGenerator`), the
discriminant is multiplied by `u ^ 2`. -/
theorem discr_changeGenerator [CommRing R] (a b u k : R) :
    discr (u ^ 2 * a - u * b * k - k ^ 2) (u * b + 2 * k) = u ^ 2 * discr a b := by
  rw [discr_def, discr_def]; ring
```
At base a discriminant `b² + 4a` (≡ 0 or 1 mod 4 over ℤ) already scales by a square under a change of
generator, which bears on the "not f²·E" description, read as minimality under such scaling.

## 3. Form of the statements: residue-class hypotheses versus `4m + 1` and `4m`

The `% 4` hypothesis form of S6 also appears at `NumberTheory/LegendreSymbol/QuadraticReciprocity.lean:133`
and at `NumberTheory/LegendreSymbol/JacobiSymbol.lean:330` (`a % 4 = 0`). No `[ZMOD 4]` or
`(n : ZMod 4) = r` hypothesis turned up in statements. ℤ versions of the S7 pattern exist, e.g.
`two_not_dvd_two_mul_add_one (n : ℤ)` (`Algebra/Group/Int/Even.lean:54`), but no `4 * m + 1` analogue
was found.

**S6 — `library_example`** — `Mathlib/NumberTheory/LegendreSymbol/ZModChar.lean:97`
```lean
/-- If `n % 4 = 1`, then `χ₄ n = 1`. -/
theorem χ₄_int_one_mod_four {n : ℤ} (hn : n % 4 = 1) : χ₄ n = 1 := by
```
Here a residue class mod 4 is a hypothesis `n % 4 = r` on an integer assumed to lie in the class.

**S7 — `counterexample`** — `Mathlib/Algebra/Ring/Parity.lean:128`
```lean
lemma odd_two_mul_add_one (a : α) : Odd (2 * a + 1) := ⟨_, rfl⟩
```
The competing pattern, for modulus 2, is a lemma about the expression `2 * a + 1` for arbitrary `a`.

**S8 — `written_guidance`** — `Mathlib/Data/Nat/Squarefree.lean:306` (a base file)
```lean
@[deprecated "Use `exists_sq_mul_squarefree` instead, which binds the witnesses in the order in \
which they appear." (since := "2026-08-17")]
protected theorem sq_mul_squarefree (n : ℕ) : ∃ a b : ℕ, b ^ 2 * a = n ∧ Squarefree a := by
  obtain ⟨b, a, h, hs⟩ := exists_sq_mul_squarefree n
  exact ⟨a, b, h, hs⟩
```
A recent stated preference to bind an existential's witnesses in the order they appear in `b ^ 2 * a`,
which bears on any `∃ f E, D = f ^ 2 * E` form, and on deprecation as this file's route for changing
an existing statement.

## 4. Linking to quadratic fields / number-field discriminants, or integer arithmetic alone

S1 (`NumberField.discr`) and S5 (`QuadraticAlgebra.discr`) are the two discriminant notions at base
that a link could target. No quadratic-field type or predicate exists at base (see the top of this
file).

**S9 — `earlier_decision`** — Zulip, #mathlib4 > quadratic number fields, Frankie F.-C. Wang, 2026-03-10
```
I have a modelling question about the `d % 4 ≠ 1` case.  For the `d % 4 = 1` case there seems to be no issue: one can model  `ℤ[(1+√d)/2]` using  `abbrev ZOnePlusSqrtOverTwo (d : ℤ) : Type := QuadraticAlgebra ℤ d 1`.  The difficulty arises in the other case (`d % 4 ≠ 1`), where the ring of  integers is `ℤ[√d]`. In mathlib this is represented by the type  `Zsqrtd`, which historically predates `Quad…
```
Quadratic-field work in flight before this contribution split on `d % 4 = 1` or not, and left the
second case unsettled between two competing types (`QuadraticAlgebra`, `Zsqrtd`), which bears on what
a link could attach to.

## 5. Names and their relation to neighbours

Nothing was found about naming this notion. The neighbouring predicates follow two patterns: the bare
adjective `Squarefree` (S2) and the `Is`-prefixed `IsCoprime` (S11). The discriminant definitions are
lower-case `discr` functions (S1, S5).

## 6. API and registration with automation

**S10 — `mechanism`** — `Mathlib/Data/Nat/Squarefree.lean:235` (a base file)
```lean
instance : DecidablePred (Squarefree : ℕ → Prop) := fun _ =>
  decidable_of_iff' _ squarefree_iff_minSqFac
```
Only ℕ has a decidability instance for `Squarefree`, which bears on whether a ℤ predicate built from
`Squarefree` can be checked by `decide` for concrete D, and on whether an instance is added.

**S11 — `mechanism`** — `Mathlib/RingTheory/Coprime/Basic.lean:41` (a base file)
```lean
/-- The proposition that `x` and `y` are coprime, defined to be the existence of `a` and `b` such
that `a * x + b * y = 1`. Note that elements with no common divisors are not necessarily coprime,
e.g., the multivariate polynomials `x₁` and `x₂` are not coprime. -/
@[wikidata Q104752]
def IsCoprime : Prop :=
  ∃ a b, a * x + b * y = 1
```
A predicate definition in a base file, registered with an external cross-reference through the
`wikidata` attribute (the file imports `Mathlib.Tactic.CrossRefAttribute`), which bears on
registration and, through its `Is` prefix and its docstring that contrasts a neighbouring notion, on
naming and documentation.

## 7. Placement, and which supporting facts belong in the base files

S4 shows that the ℤ lemmas on `Squarefree` live in `Mathlib/Algebra/Squarefree/Basic.lean`, not in
`Mathlib/Data/Nat/Squarefree.lean`, whose header (line 15) reads "Lemmas about squarefreeness of
natural numbers".

**S12 — `written_guidance`** — `Mathlib/Data/Nat/Squarefree.lean:322` (a base file)
```lean
/-- `Squarefree` is multiplicative. Note that the → direction does not require `hmn`
and generalizes to arbitrary commutative monoids. See `Squarefree.of_mul_left` and
`Squarefree.of_mul_right` above for auxiliary lemmas. -/
theorem squarefree_mul {m n : ℕ} (hmn : m.Coprime n) :
    Squarefree (m * n) ↔ Squarefree m ∧ Squarefree n := by
  simp [squarefree_mul_iff, Nat.coprime_iff_isRelPrime.mp hmn]
```
The docstring points ℕ users to monoid-general lemmas for the direction that needs no coprimality,
which bears on whether a supporting fact (e.g. squarefreeness of `4 * m` or of a product) goes in an
ℕ file, an ℤ section, or in general form.

## 8. Proof route

The tools found are S12 (multiplicativity of `Squarefree`, with the general `squarefree_mul_iff`) and
S4 (moving between ℤ and ℕ through `natAbs`). A Zulip exchange on reasoning modulo 4 with the
`mod_cases` tactic (#general > Elegance in Lean proofs, Riccardo Brasca and Michael Stoll, 2026-03-20)
was seen but is not included within the source limit. Nothing else was gathered.

## 9. Scope of edits

S8 shows how this base file handled a changed statement: deprecation, not alteration. Nothing else was
found that bears on edits to the three base files.
