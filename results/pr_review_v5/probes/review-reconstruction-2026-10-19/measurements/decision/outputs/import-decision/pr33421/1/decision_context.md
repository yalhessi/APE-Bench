# Decision context: `round`, the integer-on-the-left ceiling identities, continuity of floor, ceiling and round

8 decisions, 12 sources. Locations are at the base commit unless a Zulip date is given. A
`library_example` shows only what the library does or can do. It is not a stated preference.

## 1. Names, argument order and simp status of the integer-on-the-left ceiling identities (item 1)

### Source 1: `library_example`
`Mathlib/Algebra/Order/Floor/Ring.lean:209-211`, `:222-229`, `:350-351`
```lean
@[simp]
theorem floor_intCast_add (z : ℤ) (a : R) : ⌊↑z + a⌋ = z + ⌊a⌋ := by
  simpa only [add_comm] using floor_add_intCast a z
```
```lean
@[simp]
theorem floor_natCast_add (n : ℕ) (a : R) : ⌊↑n + a⌋ = n + ⌊a⌋ := by
  rw [← Int.cast_natCast, floor_intCast_add]

@[simp]
theorem floor_ofNat_add (n : ℕ) [n.AtLeastTwo] (a : R) :
    ⌊ofNat(n) + a⌋ = ofNat(n) + ⌊a⌋ :=
  floor_natCast_add n a
```
```lean
@[simp]
theorem fract_one_add (a : R) : fract (1 + a) = fract a := mod_cast fract_natCast_add 1 a
```
Bears on: the floor neighbours of the new ceiling lemmas. They exist for integer, natural and
numeral, all `@[simp]`, with the integer argument first and proved from the right-hand form. The
`one_add` member exists for `fract` but not for floor. Floor has only `floor_add_one`, at `:194`.

### Source 2: `counterexample`
`Mathlib/Algebra/Order/Round.lean:101-112`
```lean
@[simp]
theorem round_intCast_add (x : α) (y : ℤ) : round ((y : α) + x) = y + round x := by
  rw [add_comm, round_add_intCast, add_comm]

@[simp]
theorem round_natCast_add (x : α) (y : ℕ) : round ((y : α) + x) = y + round x := by
  rw [add_comm, round_add_natCast, add_comm]

@[simp]
theorem round_ofNat_add (n : ℕ) [n.AtLeastTwo] (x : α) :
    round (ofNat(n) + x) = ofNat(n) + round x :=
  round_natCast_add x n
```
Bears on: the same family for `round` takes the real argument before the integer one, the reverse
of `floor_intCast_add`, so binder order in this family is not uniform at base. It also has no
`one_add` member.

## 2. A division-free expression of `round` (item 2), and the proof route for the four re-proved lemmas

### Source 3: `library_example`
`Mathlib/Algebra/Order/Round.lean:44-46`, `:142-143`
```lean
/-- `round` rounds a number to the nearest integer. `round (1 / 2) = 1` -/
def round (x : α) : ℤ :=
  if 2 * fract x < 1 then ⌊x⌋ else ⌈x⌉
```
```lean
theorem round_eq (x : α) : round x = ⌊x + 1 / 2⌋ := by
  simp_rw [round, (by simp only [lt_div_iff₀', two_pos] : 2 * fract x < 1 ↔ fract x < 1 / 2)]
```
Bears on: the definition is already free of division in α. It is a case split on `2 * fract x`
between `⌊x⌋` and `⌈x⌉`. The field lemma `round_eq` opens by turning that test into a test against
`1 / 2`. `round_two_inv`, `round_neg_two_inv`, `round_eq_zero_iff`, `abs_sub_round`,
`sub_half_lt_round`, `round_le_add_half` and `Int.map_round` are all proved by rewriting with
`round_eq` (`Round.lean:163-212`).

Nothing found on any other division-free formula. The base has no identity relating `round` or
`⌊x + 1/2⌋` to `⌊2 * x⌋`, and no integer-division formula for it: searches for `⌊2 * `,
`floor_two_mul` and `round … ⌊` outside the definition and `round_eq` returned nothing. The
ceiling–floor relation available is in Source 7.

## 3. The form of `round x = n ↔ …` (item 3), and whether a ring form accompanies it

### Source 4: `library_example`
`Mathlib/Algebra/Order/Floor/Ring.lean:148-163`
```lean
theorem floor_eq_iff : ⌊a⌋ = z ↔ ↑z ≤ a ∧ a < z + 1 := by
  rw [le_antisymm_iff, le_floor, ← Int.lt_add_one_iff, floor_lt, Int.cast_add, Int.cast_one,
    and_comm]

@[simp]
theorem floor_eq_zero_iff : ⌊a⌋ = 0 ↔ a ∈ Ico (0 : R) 1 := by simp [floor_eq_iff]

theorem floor_eq_on_Ico (n : ℤ) : ∀ a ∈ Set.Ico (n : R) (n + 1), ⌊a⌋ = n := fun _ ⟨h₀, h₁⟩ =>
  floor_eq_iff.mpr ⟨h₀, h₁⟩

theorem floor_eq_on_Ico' (n : ℤ) : ∀ a ∈ Set.Ico (n : R) (n + 1), (⌊a⌋ : R) = n := fun a ha =>
  congr_arg _ <| floor_eq_on_Ico n a ha

@[simp]
theorem preimage_floor_singleton (m : ℤ) : (floor : R → ℤ) ⁻¹' {m} = Ico (m : R) (m + 1) :=
  ext fun _ => floor_eq_iff
```
Bears on: the floor characterisation appears in three shapes side by side: a conjunction of
inequalities (`floor_eq_iff`, not `@[simp]`), membership in `Ico` (`floor_eq_zero_iff`, `@[simp]`;
`floor_eq_on_Ico`), and a preimage equation (`@[simp]`). The general `n` case uses the conjunction,
and the `0` case uses `Ico`.

### Source 5: `library_example`
`Mathlib/Algebra/Order/Round.lean:163-174`
```lean
@[simp]
theorem round_two_inv : round (2⁻¹ : α) = 1 := by
  simp only [round_eq, ← one_div, add_halves, floor_one]

@[simp]
theorem round_neg_two_inv : round (-2⁻¹ : α) = 0 := by
  simp only [round_eq, ← one_div, neg_add_cancel, floor_zero]

@[simp]
theorem round_eq_zero_iff {x : α} : round x = 0 ↔ x ∈ Ico (-(1 / 2)) ((1 : α) / 2) := by
  rw [round_eq, floor_eq_zero_iff, add_mem_Ico_iff_left]
  norm_num
```
Bears on: the existing special case of item 3 uses `Ico` membership and is `@[simp]`. The file
writes the half as `2⁻¹` in some statements and as `1 / 2` in others, so its spelling is not
uniform at base.

### Source 6: `earlier_decision`
Zulip `#mathlib4 > Missing simp lemma`, Michael Stoll (maintainer) and Bolton Bailey, 2025-06-22
````
Michael Stoll (2025-06-22T15:53:12Z):
Note the following:  ```Lean4 import Mathlib  example : (1 / 2 : ℚ) + (1 / 2) = 1 := by   simp -- leaves `2⁻¹ + 2⁻¹ = 1`   sorry  example : (1 / 2 : ℚ) + (1 / 2) = 1 := by   simp [-one_div] -- succeeds using `add_halves` ```  So it seems that we need `2⁻¹ + 2⁻¹ = 1` as a simp lemma.

Bolton Bailey (2025-06-22T17:15:59Z):
Anyway, I had thought it was cleaner to make `a⁻¹` simplify to `1 / a`, which would just remove expressions involving `⁻¹` from simp normal form entirely. I guess this would mean making inv_eq_one_div simp too
````
Bears on: how `1 / 2` behaves under simp, which matters if a statement with `1 / 2` is `@[simp]`
or is meant to fire after simp. `one_div` rewrites `1 / 2` to `2⁻¹`. Stoll argues for lemmas in
the `2⁻¹` form for that reason; Bailey prefers the opposite normal form.

For a ring form, the only division-free precedent found is the definition's test `2 * fract x < 1`
(Source 3). No `round`- or floor-characterisation stated with doubled inequalities was found.

## 4. How the non-integers and the exceptional set are expressed (hypotheses of items 4-6)

### Source 7: `counterexample`
`Mathlib/Algebra/Order/Floor/Ring.lean:388-389`, `:455`, `:698`, `:719`
```lean
/-- The fractional part of `a` is positive if and only if `a ≠ ⌊a⌋`. -/
lemma fract_pos : 0 < fract a ↔ a ≠ ⌊a⌋ :=
```
```lean
theorem fract_neg {x : R} (hx : fract x ≠ 0) : fract (-x) = 1 - fract x := by
```
```lean
lemma ceil_eq_floor_add_one_iff_notMem (a : R) : ⌈a⌉ = ⌊a⌋ + 1 ↔ a ∉ Set.range Int.cast := by
```
```lean
theorem ceil_eq_add_one_sub_fract (ha : fract a ≠ 0) : (⌈a⌉ : R) = a + 1 - fract a := by
```
Bears on: "a is not an integer" has three spellings at base: `a ≠ ⌊a⌋`, `fract a ≠ 0` and
`a ∉ Set.range Int.cast`. The topology file uses the first (`continuousAt_fract`, Source 9).

### Source 8: `library_example`
`Mathlib/Analysis/SpecialFunctions/Trigonometric/Complex.lean:265-266`;
`…/Trigonometric/Arctan.lean:68`, `:78`; `…/Trigonometric/ArctanDeriv.lean:46`
```lean
theorem cos_ne_zero_iff {θ : ℝ} : cos θ ≠ 0 ↔ ∀ k : ℤ, θ ≠ (2 * k + 1) * π / 2 :=
  mod_cast @Complex.cos_ne_zero_iff θ
```
```lean
theorem continuousOn_tan : ContinuousOn tan {x | cos x ≠ 0} := by
theorem continuousOn_tan_Ioo : ContinuousOn tan (Ioo (-(π / 2)) (π / 2)) := by
theorem continuousAt_tan {x : ℝ} : ContinuousAt tan x ↔ cos x ≠ 0 := by
```
Bears on two decisions. The first is the exceptional set: a set of odd half-multiples is written
as `∀ k : ℤ, θ ≠ (2 * k + 1) * …`, and the continuity lemmas themselves use another predicate,
`cos x ≠ 0`. The second is decision 5: a `ContinuousAt … ↔ …` lemma, a `ContinuousOn` on a set-builder
set, and a `ContinuousOn` on one interval coexist for the same function.

## 5. Maps into ℤ or their casts into α; what happens to `continuousOn_floor` and `continuousOn_ceil` (items 4 and 6)

### Source 9: `library_example`
`Mathlib/Topology/Algebra/Order/Floor.lean:22-23`, `:85-91`, `:98-100`, `:170-177`
```lean
* `continuousOn_floor`: `Int.floor` is continuous on `Ico n (n + 1)`, because constant.
* `continuousOn_ceil`: `Int.ceil` is continuous on `Ioc n (n + 1)`, because constant.
```
```lean
theorem continuousOn_floor (n : ℤ) :
    ContinuousOn (fun x => floor x : α → α) (Ico n (n + 1) : Set α) :=
  (continuousOn_congr <| floor_eq_on_Ico' n).mpr continuousOn_const

theorem continuousOn_ceil [IsStrictOrderedRing α] (n : ℤ) :
    ContinuousOn (fun x => ceil x : α → α) (Ioc (n - 1) n : Set α) :=
  (continuousOn_congr <| ceil_eq_on_Ioc' n).mpr continuousOn_const
```
```lean
theorem tendsto_floor_right_pure_floor (x : α) : Tendsto (floor : α → ℤ) (𝓝[≥] x) (pure ⌊x⌋) :=
  tendsto_pure.2 <| mem_of_superset (Ico_mem_nhdsGE <| lt_floor_add_one x) fun _y hy =>
    floor_eq_on_Ico _ _ ⟨(floor_le x).trans hy.1, hy.2⟩
```
```lean
theorem continuousOn_fract [IsTopologicalAddGroup α] (n : ℤ) :
    ContinuousOn (fract : α → α) (Ico n (n + 1) : Set α) :=
  continuousOn_id.sub (continuousOn_floor n)

theorem continuousAt_fract [OrderClosedTopology α] [IsTopologicalAddGroup α]
    {x : α} (h : x ≠ ⌊x⌋) : ContinuousAt fract x :=
  (continuousOn_fract ⌊x⌋).continuousAt <|
    Ico_mem_nhds ((floor_le _).lt_of_ne h.symm) (lt_floor_add_one _)
```
Bears on: at base, continuity is stated only for the casts into α, and only on unit intervals. The
ℤ-valued maps appear only as one-sided `Tendsto … (pure _)`. `continuousOn_floor` assumes only
`[TopologicalSpace α]`, with no link between topology and order. The one-sided limits assume
`[OrderClosedTopology α]`, and the `fract` lemmas add
`[IsTopologicalAddGroup α]`. `continuousOn_fract` consumes `continuousOn_floor`. The module
docstring gives `continuousOn_ceil` the interval `Ioc n (n + 1)` while the statement says
`Ioc (n - 1) n`. Pointwise continuity of `fract` is obtained from `continuousOn` on the unit
interval through `Ico_mem_nhds`.

Nothing found outside this file. A single-line search found no `Continuous*` statement about
`Int.floor`, `Int.ceil` or `round` elsewhere at base, in either the ℤ-valued or the cast form. The
lemmas above have consumers only inside this file. Source 8 shows the competing statement shapes.

## 6. The form of one-sided constancy (item 5), and the route from one-sided facts to continuity

### Source 10: `library_example`
`Mathlib/Topology/Instances/AddCircle/Defs.lean:70`, `:96-97`, `:104-109`
```lean
theorem continuous_right_toIcoMod : ContinuousWithinAt (toIcoMod hp a) (Ici x) x := by
```
```lean
theorem toIcoMod_eventuallyEq_toIocMod (hx : (x : 𝕜 ⧸ zmultiples p) ≠ a) :
    toIcoMod hp a =ᶠ[𝓝 x] toIocMod hp a :=
```
```lean
theorem continuousAt_toIcoMod (hx : (x : 𝕜 ⧸ zmultiples p) ≠ a) : ContinuousAt (toIcoMod hp a) x :=
  let h := toIcoMod_eventuallyEq_toIocMod hp a hx
  continuousAt_iff_continuous_left_right.2 <|
    ⟨(continuous_left_toIocMod hp a x).congr_of_eventuallyEq (h.filter_mono nhdsWithin_le_nhds)
        h.eq_of_nhds,
      continuous_right_toIcoMod hp a x⟩
```
Bears on: a floor-like reduction map whose one-sided behaviour is stated as `ContinuousWithinAt`
on `Ici x`/`Iic x`, not as `Tendsto … (pure _)` as in Source 9. Its exceptional points are excluded
by a quotient hypothesis. Two-sided continuity is assembled from the two sides with
`continuousAt_iff_continuous_left_right`. Source 9's `tendsto_floor_right_pure_floor` shows the
other one-sided form, built from an `Ico` in `𝓝[≥] x`.

## 7. Registration with automation

### Source 11: `mechanism`
`Mathlib/Data/Rat/Floor.lean:292-298`, `:304-306`, `:317-318`
```lean
/-!
### `norm_num` extension for `round`
-/

theorem isNat_round {R : Type*} [Ring R] [LinearOrder R] [IsStrictOrderedRing R] [FloorRing R]
    (r : R) (m : ℕ) : IsNat r m → IsNat (round r) m := by
  rintro ⟨⟨⟩⟩; exact ⟨by simp⟩
```
```lean
theorem IsRat.isInt_round {R : Type*} [Field R] [LinearOrder R] [IsStrictOrderedRing R]
    [FloorRing R] (r : R) (n : ℤ) (d : ℕ) (res : ℤ) (hres : round (n / d : ℚ) = res) :
    IsRat r n d → IsInt (round r) res := by
```
```lean
/-- `norm_num` extension for `round` -/
@[norm_num round _]
```
Bears on: `round` of a numeral or rational literal is already evaluated by `norm_num`, downstream
of `Round.lean`, so it is not available inside `Round.lean`. The `@[simp]` pattern of the
neighbouring lemmas is in Sources 1, 2 and 5.

## 8. Placement, and which import edits the work needs

### Source 12: `consumer`
`Mathlib/Algebra/Order/Round.lean:8-9`, `:173`; `Mathlib/Data/Rat/Floor.lean:8`;
`Mathlib/Algebra/Order/Archimedean/Basic.lean:12`; `Mathlib/Algebra/Order/ToIntervalMod.lean:305`;
`Mathlib/Topology/Algebra/Order/Floor.lean:8-10`, `:65`
```lean
public import Mathlib.Algebra.Order.Floor.Ring
public import Mathlib.Algebra.Order.Interval.Set.Group
  rw [round_eq, floor_eq_zero_iff, add_mem_Ico_iff_left]
public import Mathlib.Algebra.Order.Round
public import Mathlib.Data.Rat.Floor
  rw [← sub_right_comm, Set.sub_mem_Ico_iff_left, add_right_comm]
public import Mathlib.Algebra.Order.Floor.Ring
public import Mathlib.Order.Filter.AtTopBot.Floor
public import Mathlib.Topology.Algebra.Order.Group
-- TODO: move to `Mathlib/Order/Filter/AtTopBot/Floor.lean`
```
Bears on: within its own file, `Round.lean` uses its import of `Interval/Set/Group` only in
`round_eq_zero_iff` (`add_mem_Ico_iff_left`). Other files reach that file through `Round.lean`:
`ToIntervalMod.lean` uses `sub_mem_Ico_iff_left` (`Interval/Set/Group.lean:86`), and its chain is
`Archimedean/Basic` → `Data/Rat/Floor` → `Round`. At base, only `Round.lean` and
`Analysis/Convex/Between.lean` import `Interval/Set/Group` directly. `Round.lean` is imported
directly only by `Data/Rat/Floor.lean`. The topology floor file does not import `Round.lean`, and it
carries a TODO to move its `tendsto_*` lemmas elsewhere. Other packet files use lemmas of
`Interval/Set/Group` without importing it directly: `AddCircle/Defs.lean:80` uses
`sub_mem_Ioo_iff_left` (`Group.lean:92`), and `IntervalIntegral/Basic.lean:1318` uses
`pairwise_disjoint_Ioc_add_intCast` (`Group.lean:213`). Nothing found in written guidance or on
Zulip that bears on which import adjustments to make.
