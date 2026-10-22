# Sketch

Lean unchecked. Paths under `base/Mathlib/`; "Source n" is in `decision_context.md`.

## 1. Ceiling with the integer on the left
**Choice:** in `Int`, after `ceil_add_ofNat`, all `@[simp]`, cast argument first:
```lean
theorem ceil_intCast_add (z : ℤ) (a : R) : ⌈↑z + a⌉ = z + ⌈a⌉ := by
  simpa only [add_comm] using ceil_add_intCast a z
```
then `ceil_natCast_add`, `ceil_one_add` (`mod_cast`), `ceil_ofNat_add`, derived as in the floor family.
**Alternatives:** add `floor_one_add` for symmetry.
**References:** `Algebra/Order/Floor/Ring.lean:209-229` (floor family), `:626-641`, `:351` (`fract_one_add`).
**What would decide it:** `floor_one_add`: open.

## 2. Round in a ring, without division in α
**Choice:** in the ring section of `Round.lean`, before `abs_sub_round_eq_min`:
```lean
theorem round_eq_floor_two_mul_add_one_div_two (x : α) : round x = (⌊2 * x⌋ + 1) / 2
```
Proof: unfold `round`; `⌊2 * x⌋ = 2 * ⌊x⌋ + ⌊2 * fract x⌋` with `⌊2 * fract x⌋ ∈ {0, 1}`; `omega`.
**Alternatives:** `⌊2 * x⌋ - ⌊x⌋` (Hermite's identity, no integer division); `⌊x⌋ + ⌊2 * fract x⌋`.
**References:** `Algebra/Order/Round.lean:45-46`; `Floor/Ring.lean:292` (`floor_div_natCast`).
**What would decide it:** proof economy: the `/ 2` form gives `round_eq` by `floor_div_natCast` and round's one-sided limits from `⌊2 * y⌋`'s. Name open.

## 3. Proof route of the four re-proved lemmas
**Choice:** from decisions 2 and 4:
- `round_eq`: `⌊x + 1 / 2⌋ = ⌊(2 * x + 1) / 2⌋ = ⌊2 * x + 1⌋ / 2` (`floor_div_natCast`), then `floor_add_one`;
- `round_two_inv`, `round_neg_two_inv`: `simp` with decision 2, without the `← one_div` detour;
- `round_eq_zero_iff`: `simp [round_eq_iff]`, no longer using `add_mem_Ico_iff_left`.

**Alternatives:** keep the `fract` case split in `round_eq`.
**References:** `Round.lean:142-174`.
**What would decide it:** proof length; the import consequence is decision 9.

## 4. Characterisation of `round x = n`
**Choice:** after `round_eq`, not simp, conjunction as `floor_eq_iff` (proof: `round_eq`, `floor_eq_iff`, `linarith`):
```lean
theorem round_eq_iff {x : α} {n : ℤ} : round x = n ↔ n - 1 / 2 ≤ x ∧ x < n + 1 / 2
```
**Alternatives:** `Ico` membership; `2⁻¹`, the simp normal form (Source 4); also a ring form `2 * n - 1 ≤ 2 * x ∧ 2 * x < 2 * n + 1`.
**References:** `Floor/Ring.lean:148-153`; `Round.lean:172-199` (`1 / 2` throughout); Source 3.
**What would decide it:** spelling: whether users arrive after `simp`. Ring form: open, no ring consumer gathered.

## 5. Spelling the non-integers and the exceptional points
**Choice:** inline hypotheses through `fract`, no new definition: `fract x ≠ 0` and `2 * fract x ≠ 1`; sets `{x | fract x ≠ 0}`, `{x | 2 * fract x ≠ 1}`. Ring-valid; the second is `round`'s own test.
**Alternatives:** `x ∉ Set.range Int.cast`; `x ≠ ⌊x⌋`; field-only `x + 1 / 2 ∉ Set.range Int.cast`; a named set (Source 11).
**References:** `Floor/Ring.lean:389, 698, 719`; `Topology/Algebra/Order/Floor.lean:174-177`; `Round.lean:46`.
**What would decide it:** open; four spellings coexist. The `range` form saves a conversion in decision 6.

## 6. Floor and ceiling at non-integers
**Choice:** the ℤ-valued maps (ℤ is discrete, Source 7): `continuousAt_floor (h : fract x ≠ 0) : ContinuousAt (floor : α → ℤ) x`, likewise `continuousAt_ceil`, under `[OrderClosedTopology α]`. Proof: `nhds_discrete`, `nhdsLT_sup_nhdsGE`, the existing one-sided `tendsto_*_pure_*` lemmas, and `ceil_eq_floor_add_one_iff_notMem`. Set versions from pointwise ones. Casts: one composition, not stated.
**Alternatives:** also state the casts; agreement with a constant on `Ioo` (Source 8).
**References:** `Topology/Algebra/Order/Floor.lean:93-133, 212`.
**What would decide it:** a consumer needing the cast form; none gathered.

## 7. Round near a point
**Choice:** the form of the neighbouring floor limits, under `[OrderClosedTopology α] [ContinuousAdd α]`:
```lean
theorem tendsto_round_right_pure_round (x : α) : Tendsto round (𝓝[≥] x) (pure (round x))
theorem tendsto_round_left_pure_round (h : 2 * fract x ≠ 1) :
    Tendsto round (𝓝[<] x) (pure (round x))
theorem tendsto_round_left_pure_round_sub_one (h : 2 * fract x = 1) :
    Tendsto round (𝓝[<] x) (pure (round x - 1))
```
Proof: rewrite by decision 2; compose the floor limits at `2 * x` with `y ↦ y + y`; the left value `⌈2 * x⌉ / 2` is `round x` or `round x - 1` by cases. Then `continuousAt_round (h : 2 * fract x ≠ 1)` as in decision 6, and `continuousOn_round` on `{x | 2 * fract x ≠ 1}`.
**Alternatives:** one uniform left lemma with value `⌈2 * x⌉ / 2`, like `tendsto_floor_left_pure_ceil_sub_one`; `ContinuousWithinAt` on `Ici`/`Iic` (Source 12); `[OrderTopology α]`; field-only, via `continuousAt_floor` at `x + 1 / 2`.
**References:** `Topology/Algebra/Order/Floor.lean:98-133`; `Topology/Instances/AddCircle/Defs.lean:70-109`.
**What would decide it:** open; a ring α excludes the field-only route.

## 8. Existing `continuousOn_floor` / `continuousOn_ceil`
**Choice:** keep them (they cover the interval's closed end; the new lemmas do not); new set versions take other names, e.g. `continuousOn_floor_setOf_fract_ne_zero`. Fix its header entry (`Ioc n (n + 1)` for `Ioc (n - 1) n`).
**Alternatives:** rename them `continuousOn_floor_Ico` / `continuousOn_ceil_Ioc` (deprecated aliases), freeing the plain names, as `Real.continuousOn_tan` / `Real.continuousOn_tan_Ioo` (recalled).
**References:** `Topology/Algebra/Order/Floor.lean:22-23, 85-91`.
**What would decide it:** open; how much deprecation churn maintainers accept.

## 9. Placement and imports
**Choice:** items 4–6 at the end of the `OrderClosedTopology` section of `Topology/Algebra/Order/Floor.lean`, which imports `Mathlib.Algebra.Order.Round` and mentions round in its header. `Round.lean` drops `Mathlib.Algebra.Order.Interval.Set.Group` (unused after decision 3); files that reached it through `Round` import it where the build fails (e.g. `Algebra/Order/ToIntervalMod.lean:305`, `Topology/Instances/AddCircle/Defs.lean:80`).
**Alternatives:** a new `Topology/Algebra/Order/Round.lean`; keep the import, touching no other file; a separate import PR.
**References:** `Topology/Algebra/Order/Floor.lean:8-10`; `Round.lean:9, 173`.
**What would decide it:** open; whether import pruning belongs in an API-review PR.
