# Decision context: `round`, ceiling with the integer on the left, continuity of floor, ceiling and round

Twelve sources, numbered in order of first appearance. Paths are at the base commit. Where an
excerpt joins lines that are not adjacent, `…` marks the gap and the line ranges are listed.

## 1. Name, argument order and registration of the ceiling identity with the integer on the left (item 1)

**Source 1** (kind: `library_example`)
Where: `Mathlib/Algebra/Order/Floor/Ring.lean:209-228`
```lean
@[simp]
theorem floor_intCast_add (z : ℤ) (a : R) : ⌊↑z + a⌋ = z + ⌊a⌋ := by
  simpa only [add_comm] using floor_add_intCast a z

@[simp]
theorem floor_add_natCast (a : R) (n : ℕ) : ⌊a + n⌋ = ⌊a⌋ + n := by
  rw [← Int.cast_natCast, floor_add_intCast]

@[simp]
theorem floor_add_ofNat (a : R) (n : ℕ) [n.AtLeastTwo] :
    ⌊a + ofNat(n)⌋ = ⌊a⌋ + ofNat(n) :=
  floor_add_natCast a n

@[simp]
theorem floor_natCast_add (n : ℕ) (a : R) : ⌊↑n + a⌋ = n + ⌊a⌋ := by
  rw [← Int.cast_natCast, floor_intCast_add]

@[simp]
theorem floor_ofNat_add (n : ℕ) [n.AtLeastTwo] (a : R) :
    ⌊ofNat(n) + a⌋ = ofNat(n) + ⌊a⌋ :=
  floor_natCast_add n a
```
Bears on: the floor family already has the integer-on-the-left forms, named `floor_<cast>_add`,
with the cast argument first, each `@[simp]`, and the `natCast` and `ofNat` versions derived from
the more general one.

Search note: a search for `(ceil|floor)_one_add` found no declaration at base, so neither family
has a form for `z = 1` with the one on the left.

## 2. Expressing `round` through floor or ceiling in a ring (item 2), and the proof route of the four re-proved lemmas

No source gathered.

## 3. Form of the characterisation `round x = n` (item 3), a division-free form, and how one half is written

**Source 2** (kind: `library_example`)
Where: `Mathlib/Algebra/Order/Floor/Ring.lean:148-153`
```lean
theorem floor_eq_iff : ⌊a⌋ = z ↔ ↑z ≤ a ∧ a < z + 1 := by
  rw [le_antisymm_iff, le_floor, ← Int.lt_add_one_iff, floor_lt, Int.cast_add, Int.cast_one,
    and_comm]

@[simp]
theorem floor_eq_zero_iff : ⌊a⌋ = 0 ↔ a ∈ Ico (0 : R) 1 := by simp [floor_eq_iff]
```
Bears on: for `⌊a⌋ = z` the base has two forms side by side: a conjunction of two inequalities for
general `z`, and `Ico` membership (`@[simp]`) for `z = 0`, which is the form `round_eq_zero_iff`
uses.

**Source 3** (kind: `consumer`)
Where: `Mathlib/Analysis/Normed/Group/AddCircle.lean:102-105, 120-126`
```lean
theorem norm_half_period_eq : ‖(↑(p / 2) : AddCircle p)‖ = |p| / 2 := by
  rcases eq_or_ne p 0 with (rfl | hp); · simp
  rw [norm_eq, ← mul_div_assoc, inv_mul_cancel₀ hp, one_div, round_two_inv, Int.cast_one,
    one_mul, (by linarith : p / 2 - p = -(p / 2)), abs_neg, abs_div, abs_two]
…
  suffices round (p⁻¹ * x) = 0 by simp [norm_eq, this]
  rw [round_eq_zero_iff]
  obtain ⟨hx₁, hx₂⟩ := abs_le.mp hx
  replace hx₂ := Ne.lt_of_le hx' hx₂
  constructor
  · rwa [le_inv_mul_iff₀ hp, mul_neg, ← mul_div_assoc, mul_one]
  · rwa [inv_mul_lt_iff₀ hp, ← mul_div_assoc, mul_one]
```
Bears on: in use, `round_eq_zero_iff` is split into its two inequalities, which are then proved by
multiplying out, and `round_two_inv` is reached only after rewriting with `one_div` to the `2⁻¹`
spelling.

**Source 4** (kind: `mechanism`)
Where: `Mathlib/Algebra/Group/Defs.lean:1050-1052`
```lean
@[to_additive (attr := simp)]
theorem one_div (a : G) : 1 / a = a⁻¹ :=
  (inv_eq_one_div a).symm
```
Bears on: `simp` rewrites `1 / 2` to `2⁻¹`, while `Round.lean` at base mixes the two spellings
(`round_eq`, `round_eq_zero_iff`, `abs_sub_round` use `1 / 2`; `round_two_inv` and
`round_neg_two_inv` use `2⁻¹`).

**Source 5** (kind: `earlier_decision`)
Where: review of PR #14964 by Command-Master, 2024-07-21, on `Mathlib/Algebra/Order/Floor.lean`
````
On this code:
+@[simp]
+theorem round_half_bot [HSub α ℝ α] : x - (1 / 2 : ℝ) < round x := by
+  rw [round_eq x, show (x - 1 / 2 : ℝ) = (x + 1 / 2) - 1 by ring]

Comment:
```suggestion
@[simp]
theorem round_half_bot (x : α) : x - (1 / 2 : ℚ) < round x := by
  rw [round_eq x, show x - (1 / 2 : ℚ) = x + 1 / 2 - 1 by ring]
```
You shouldn't use `HSub α ℝ α`, the subtraction it defines is unconnected to `α`'s field
structure, you should use the coercion from `ℚ` to `α` (which is part of `α`'s field structure).
Additionally I'm not sure it should be a `simp` lemma
````
Bears on: a reviewer's reasons for typing the half in a bound on `round` through a coercion that
is part of α's field structure rather than `HSub α ℝ α`, and for doubting `simp` on such bounds; at
base the lemmas with these statements (`sub_half_lt_round`, `round_le_add_half`,
`Round.lean:191-199`) carry `@[bound]`, not `@[simp]`, and write `1 / 2` in α.

## 4. Maps into ℤ, casts into α, and the existing `continuousOn_floor` / `continuousOn_ceil` (items 4 and 6)

**Source 6** (kind: `library_example`)
Where: `Mathlib/Topology/Algebra/Order/Floor.lean:22-23, 83-91, 95-100`
```lean
* `continuousOn_floor`: `Int.floor` is continuous on `Ico n (n + 1)`, because constant.
* `continuousOn_ceil`: `Int.ceil` is continuous on `Ioc n (n + 1)`, because constant.
…
variable [TopologicalSpace α]

theorem continuousOn_floor (n : ℤ) :
    ContinuousOn (fun x => floor x : α → α) (Ico n (n + 1) : Set α) :=
  (continuousOn_congr <| floor_eq_on_Ico' n).mpr continuousOn_const

theorem continuousOn_ceil [IsStrictOrderedRing α] (n : ℤ) :
    ContinuousOn (fun x => ceil x : α → α) (Ioc (n - 1) n : Set α) :=
  (continuousOn_congr <| ceil_eq_on_Ioc' n).mpr continuousOn_const
…
variable [IsStrictOrderedRing α] [OrderClosedTopology α]

omit [IsStrictOrderedRing α] in
theorem tendsto_floor_right_pure_floor (x : α) : Tendsto (floor : α → ℤ) (𝓝[≥] x) (pure ⌊x⌋) :=
  tendsto_pure.2 <| mem_of_superset (Ico_mem_nhdsGE <| lt_floor_add_one x) fun _y hy =>
    floor_eq_on_Ico _ _ ⟨(floor_le x).trans hy.1, hy.2⟩
```
Bears on: the file states continuity only for the casts into α, as `ContinuousOn` on one unit
interval with just `[TopologicalSpace α]`, and treats the ℤ-valued maps only through one-sided
`Tendsto … (pure …)` under `[OrderClosedTopology α]`; the header entry for `continuousOn_ceil`
names `Ioc n (n + 1)` while the statement uses `Ioc (n - 1) n`.

**Source 7** (kind: `library_example`)
Where: `Mathlib/Topology/Order.lean:510-511`
```lean
instance : TopologicalSpace ℤ := ⊥
instance : DiscreteTopology ℤ := ⟨rfl⟩
```
Bears on: ℤ carries the discrete topology at base, so continuity of `floor : α → ℤ` and
`ceil : α → ℤ` themselves can be stated, as well as of their casts into α.

**Source 8** (kind: `library_example`)
Where: `Mathlib/Topology/Instances/Sign.lean:20-24, 30-35, 46-49`
```lean
instance : TopologicalSpace SignType :=
  ⊥

instance : DiscreteTopology SignType :=
  ⟨rfl⟩
…
variable [PartialOrder α] [DecidableLT α] [OrderTopology α]

theorem continuousAt_sign_of_pos {a : α} (h : 0 < a) : ContinuousAt SignType.sign a := by
  refine (continuousAt_const : ContinuousAt (fun _ => (1 : SignType)) a).congr ?_
  rw [Filter.EventuallyEq, eventually_nhds_iff]
  exact ⟨{ x | 0 < x }, fun x hx => (sign_pos hx).symm, isOpen_lt' 0, h⟩
…
variable [LinearOrder α] [OrderTopology α]

theorem continuousAt_sign_of_ne_zero {a : α} (h : a ≠ 0) : ContinuousAt SignType.sign a := by
  rcases h.lt_or_gt with (h_neg | h_pos)
```
Bears on: a step function into a discrete type whose continuity is stated for the map itself at
points away from its jump, with the condition as an explicit hypothesis, an `_of_<condition>`
name, `[OrderTopology α]`, and a proof by agreement with a constant on an open set.

## 5. Exact hypotheses for items 4-6

No further source. The sources above show several typeclass sets for the same kind of statement:
only `[TopologicalSpace α]` (Source 6, `continuousOn_floor`), `[OrderClosedTopology α]` (Source 6,
one-sided limits), `[OrderClosedTopology α] [IsTopologicalAddGroup α]` (Source 9),
`[OrderTopology α]` (Sources 8 and 12).

## 6. How the non-integers and the exceptional set are expressed

**Source 9** (kind: `library_example`)
Where: `Mathlib/Topology/Algebra/Order/Floor.lean:174-177`
```lean
theorem continuousAt_fract [OrderClosedTopology α] [IsTopologicalAddGroup α]
    {x : α} (h : x ≠ ⌊x⌋) : ContinuousAt fract x :=
  (continuousOn_fract ⌊x⌋).continuousAt <|
    Ico_mem_nhds ((floor_le _).lt_of_ne h.symm) (lt_floor_add_one _)
```
Bears on: the topology file's only pointwise continuity result writes "x is not an integer" as
`x ≠ ⌊x⌋` and derives `ContinuousAt` from `ContinuousOn` on a unit interval.

**Source 10** (kind: `counterexample`)
Where: `Mathlib/Algebra/Order/Floor/Ring.lean:388-389, 698, 719`
```lean
/-- The fractional part of `a` is positive if and only if `a ≠ ⌊a⌋`. -/
lemma fract_pos : 0 < fract a ↔ a ≠ ⌊a⌋ :=
…
lemma ceil_eq_floor_add_one_iff_notMem (a : R) : ⌈a⌉ = ⌊a⌋ + 1 ↔ a ∉ Set.range Int.cast := by
…
theorem ceil_eq_add_one_sub_fract (ha : fract a ≠ 0) : (⌈a⌉ : R) = a + 1 - fract a := by
```
Bears on: the floor file itself writes the same condition three other ways (`0 < fract a`,
`a ∉ Set.range Int.cast`, `fract a ≠ 0`), so the spelling is not settled one way.

**Source 11** (kind: `counterexample`)
Where: `Mathlib/Analysis/Complex/IntegerCompl.lean:22-31`
```lean
/-- The complement of the integers in `ℂ` -/
def Complex.integerComplement := (Set.range ((↑) : ℤ → ℂ))ᶜ

namespace Complex

local notation "ℂ_ℤ" => integerComplement

lemma integerComplement_eq : ℂ_ℤ = {z : ℂ | ¬ ∃ (n : ℤ), n = z} := rfl

lemma integerComplement.mem_iff {x : ℂ} : x ∈ ℂ_ℤ ↔ ¬ ∃ (n : ℤ), n = x := Iff.rfl
```
Bears on: a competing pattern in which the set of non-integers is a named definition with its own
membership lemmas rather than a hypothesis spelled out inline.

**Source 12** (kind: `library_example`)
Where: `Mathlib/Topology/Instances/AddCircle/Defs.lean:66-68, 70, 87, 96-109`
```lean
variable [AddCommGroup 𝕜] [LinearOrder 𝕜] [IsOrderedAddMonoid 𝕜] [Archimedean 𝕜]
  [TopologicalSpace 𝕜] [OrderTopology 𝕜]
  {p : 𝕜} (hp : 0 < p) (a x : 𝕜)
…
theorem continuous_right_toIcoMod : ContinuousWithinAt (toIcoMod hp a) (Ici x) x := by
…
theorem continuous_left_toIocMod : ContinuousWithinAt (toIocMod hp a) (Iic x) x := by
…
theorem toIcoMod_eventuallyEq_toIocMod (hx : (x : 𝕜 ⧸ zmultiples p) ≠ a) :
    toIcoMod hp a =ᶠ[𝓝 x] toIocMod hp a :=
  IsOpen.mem_nhds
      (by
        rw [Ico_eq_locus_Ioc_eq_iUnion_Ioo]
        exact isOpen_iUnion fun i => isOpen_Ioo) <|
    (not_modEq_iff_toIcoMod_eq_toIocMod hp).1 <| not_modEq_iff_ne_mod_zmultiples.2 hx.symm

theorem continuousAt_toIcoMod (hx : (x : 𝕜 ⧸ zmultiples p) ≠ a) : ContinuousAt (toIcoMod hp a) x :=
  let h := toIcoMod_eventuallyEq_toIocMod hp a hx
  continuousAt_iff_continuous_left_right.2 <|
    ⟨(continuous_left_toIocMod hp a x).congr_of_eventuallyEq (h.filter_mono nhdsWithin_le_nhds)
        h.eq_of_nhds,
      continuous_right_toIcoMod hp a x⟩
```
Bears on: another jump function whose exceptional points (a coset of a lattice) are excluded by an
inequality in a quotient, with one-sided continuity stated as `ContinuousWithinAt` on `Ici`/`Iic`,
local agreement as `=ᶠ[𝓝 x]`, and two-sided continuity assembled from the two sides.

Search note: I did not look for an existing name for the points where `2 * x` is an odd integer;
none was gathered.

## 7. Form of the one-sided statements (item 5) and the proof route of the continuity results

No further source. Two base forms appear above for "constant on one side of x": `Tendsto f (𝓝[≥] x)
(pure c)` (Source 6) and `ContinuousWithinAt f (Ici x) x` together with `=ᶠ[𝓝 x]` (Source 12).
Proof routes shown: agreement with a constant through `continuousOn_congr` (Source 6) or
`ContinuousAt.congr` (Source 8), `ContinuousOn.continuousAt` on an interval neighbourhood
(Source 9), and `continuousAt_iff_continuous_left_right` (Source 12).

## 8. Scope of edits (imports)

No source gathered.
