# Review notes: PR #33421, chore(Algebra/Order/Floor): review API about `round`

Inputs read: `pr.md`, `model.md`, `diff.patch`. Through `ptool` I read `Round.lean`, `Topology/Algebra/Order/Floor.lean`, the relevant parts of `Floor/Ring.lean` and the header of `Interval/Set/Group.lean`, all as the PR leaves them. Every edit I propose was compiled with `lean_verify_edit`. Findings: 9, all advisory.

## Mathlib/Algebra/Order/Floor/Ring.lean
- `ceil_intCast_add`, `ceil_natCast_add`, `ceil_ofNat_add`: these mirror the existing `floor_intCast_add`, `floor_natCast_add` and `floor_ofNat_add`, and are not duplicates. `declaration_search` finds none of them at the base. The proofs and `@[simp]` tags match the floor siblings. No ask.
- `ceil_one_add`: there is no `floor_one_add` at the base or in the PR, so the API is now asymmetric. **Finding:** add `floor_one_add` (verified, compiles).
- `two_mul_fract_eq_one_iff_exists_int`: the statement and proof are fine, and naming_norm cannot measure the name. It is a `fract` lemma placed in the `floor` section. **Finding:** move it into `section fract` after `fract_eq_fract` (the move compiles).

## Mathlib/Algebra/Order/Round.lean
- import: the PR demotes `Interval.Set.Group` to a private import, but deleting it outright compiles. **Finding:** delete it.
- `round_eq'`: the formula is correct (Int `/` is ediv by a positive divisor), and naming_norm says `conforms` for the `round_` prefix. I considered asking for a non-primed name but did not: `foo_eq'` variants are common and the census does not measure primes. I also considered golfing its 15-line proof. `linarith` is not available because α is only a (non-commutative) `Ring`, and I found no clearly shorter proof, so no golf ask. **Finding:** the docstring carries a speculative TODO; remove it or turn it into a `--` comment.
- `round_eq_half_ceil_two_mul`: it is correct, its docstring is fine, and I have no ask about the proof.
- `round_eq` (new short proof via `round_eq'`), `round_two_inv` and `round_neg_two_inv` (now `norm_num [round_eq_iff]`), `round_eq_zero_iff` (now `simp [round_eq_iff]`): all are improvements. No ask.
- `round_eq_iff`: I tested a conjunction form (`n - 1/2 ≤ x ∧ x < n + 1/2`), which compiles and would match `floor_eq_iff` / `ceil_eq_iff`. I did not report it, because the Ico form matches `round_eq_zero_iff` and `floor_eq_zero_iff`, so either is defensible.

## Downstream import-only files
`AddConstMap/Basic`, `Archimedean/Basic`, `ToIntervalMod`, `ApproximateUnit`, `Complex/Arctan`, `AkraBazzi/GrowsPolynomially`, `GroupTheory/Archimedean`, `IntervalIntegral/Basic`, `IntervalIntegral/DerivIntegrable`, `Liouville/Basic`, `AtTopBot/Archimedean`, `AddCircle/Defs`.
- All of these changes follow from Round no longer re-exporting `Interval.Set.Group`, which publicly imports `Order.Group.Basic`. Round is publicly imported by `Data/Rat/Floor`.
- I considered a "split this into its own PR" scope ask and did not report it: the change is consistent with the import tidy-up in Round.lean.

## Mathlib/Topology/Algebra/Order/Floor.lean
- Module docstring: **finding.** It omits `round` and the new continuity lemmas, and the `continuousOn_ceil` entry says `Ioc n (n + 1)` where the statement is `Ioc (n - 1) n`.
- `continuousOn_floor` / `continuousOn_ceil`: the codomain changes from α to ℤ, and the now-unneeded `IsStrictOrderedRing` is dropped from ceil. These are fine.
  - After the PR, `floor_eq_on_Ico'` and `ceil_eq_on_Ioc'` have no remaining uses, but they are still valid API. No ask.
- The section restructure (removing `omit ... in`, adding `section Ring`): fine.
- `continuousAt_floor`, `continuousOn_floor_compl_range`, `continuousOn_ceil_compl_range`: fine. I checked that `@[fun_prop]` elaborates on them, since the file compiles.
- `continuousAt_ceil`: two findings.
  - It is missing `@[fun_prop]`, unlike its floor sibling.
  - Its hypothesis is stated with `⌊x⌋` and converted by hand. `x ≠ ⌈x⌉` compiles, simplifies the proof, and keeps `continuousOn_ceil_compl_range` compiling.
- `continuousOn_fract` and `continuousAt_fract`: they were adapted correctly to the ℤ-valued floor. No ask.
- `tendsto_round_nhdsGE_pure` and `tendsto_round_nhdsLT_pure_half_ceil`:
  - The two proofs share a near-identical `have : Tendsto (2 * ·) ...`. I searched for an existing lemma for scaling on one-sided neighbourhoods and found none, so I made no duplication ask.
  - **Finding (naming):** `half_ceil` drops the `two_mul` that the sibling `round_eq_half_ceil_two_mul` uses for the same expression `⌈2 * x⌉ / 2`.
- `continuousAt_round` and `continuousOn_round`: correct. **Finding (style):** all four round lemmas repeat `[IsStrictOrderedRing α] [OrderClosedTopology α] [ContinuousAdd α]` directly above `variable [IsStrictOrderedRing α]`. Grouping them in a variable section compiles.
- `ContinuousOn.comp_fract''`: the model lists it as added, but it is unchanged apart from the trailing `end Ring`. No ask.

## Tool calls (summary)
- `declaration_search`: round_eq_iff, Int.ceil_intCast_add, Int.floor_intCast_add, Int.floor_one_add (absent), Int.floor_natCast_add, Int.floor_ofNat_add, continuousAt_floor, continuousAt_ceil, continuousAt_round, Int.two_mul_fract_eq_one_iff_exists_int.
- `naming_norm`:
  - `round_eq'` and `round_eq_half_ceil_two_mul`: conforms.
  - `tendsto_round_nhdsLT_pure_half_ceil`, `continuousOn_floor_compl_range` and `two_mul_fract_eq_one_iff_exists_int`: subject_unresolved.
- `zulip_search` and `precedent_search`: nothing applicable.
- `lean_verify_edit`, all `compiled`, no errors:
  - import removal
  - `continuousAt_ceil` with `@[fun_prop]` and the ceil hypothesis
  - round lemmas in a variable section
  - `round_eq_iff` conjunction form (not reported)
  - the move of `two_mul_fract_eq_one_iff_exists_int`
  - `floor_one_add` insertion
