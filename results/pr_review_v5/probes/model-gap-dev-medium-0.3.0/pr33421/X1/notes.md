# Review notes: PR #33421, chore(Algebra/Order/Floor): review API about `round`

## Method

- Read `pr.md`, `model.md` and `diff.patch`.
- Read the reviewed files through `ptool file_read`. The workspace paths need a `target/` prefix: `target/Mathlib/...`.
- As-is compile of `Mathlib/Algebra/Order/Round.lean`: compiles, no warnings.
- Every edit proposed in `findings.json` was checked with `lean_verify_edit`, and every one succeeded. As a sanity check, a deliberately broken import was fed to the tool and it failed, so edits really are applied.
- Also used: `declaration_search`, `content_search`, `naming_norm`, `precedent_search` and `zulip_search`. The last three turned up nothing actionable.

## Mathlib/Algebra/Order/Floor/Ring.lean

- **`Int.ceil_intCast_add`, `Int.ceil_natCast_add`, `Int.ceil_ofNat_add`, `Int.ceil_one_add`**
  - These are the left-addition twins of the existing `ceil_add_*` lemmas. Names and `@[simp]` attributes match the floor/fract siblings.
  - `declaration_search` shows `Int.ceil_natCast_add` is otherwise declared only as `ENat.ceil_natCast_add` in Floor/Extended.lean. That is a different namespace, so there is no clash.
  - Found: no `Int.floor_one_add`, even though `fract_one_add` exists. This is finding 9, with the addition verified to compile.
  - Nothing else wrong.
- **`Int.two_mul_fract_eq_one_iff_exists_int`**: statement and proof are fine. It is used only by `round_eq_half_ceil_two_mul`. I considered asking to move or privatize it, and to rephrase it with `Odd`, but have no evidence a maintainer would require either. No finding.
- **Lemmas the PR stops using**: after the PR, `floor_eq_on_Ico'` and `ceil_eq_on_Ioc'` have no remaining users in Mathlib (content_search). I did not raise deprecating them; they are still valid lemmas.

## Mathlib/Algebra/Order/Round.lean

- **Import change (`public import` to `import` of Interval.Set.Group)**: removing the import entirely compiles, so the import is unused (finding 1). The imports added to downstream files are what the transitive loss requires, whether the import is demoted or removed. No finding on those files.
- **`round_eq'`**
  - The proof is long but its structure is reasonable. I did not find a clearly shorter canonical proof.
  - The prime name and the TODO in the docstring are acceptable by local conventions. No finding.
- **`round_eq_half_ceil_two_mul`**: statement and docstring are fine; the case split on `2 * x ∈ range Int.cast` is reasonable. Its `half_ceil_two_mul` spelling is used in finding 6, which asks the tendsto lemma to match it.
- **`round_eq`, `round_eq_iff`, `round_two_inv`, `round_neg_two_inv`, `round_eq_zero_iff`**
  - The new short proofs are good.
  - `round_eq_iff` uses `Ico`, like `round_eq_zero_iff`. `floor_eq_iff`/`ceil_eq_iff` use `∧`, but `floor_eq_zero_iff` also uses `Ico`, so there is no clear convention to enforce. No finding.
  - `round_eq_zero_iff` keeps `1 / 2` on its simp RHS. That predates this PR and was not raised.

## Mathlib/Topology/Algebra/Order/Floor.lean

- **`continuousOn_floor` / `continuousOn_ceil`**
  - The retyping to `α → ℤ` is sound. It has no other users in Mathlib (content_search), and the `[IsStrictOrderedRing α]` dropped from `continuousOn_ceil` is indeed not needed.
  - Found: the leftover eta-expanded lambda (findings 4 and 5).
- **`continuousAt_floor`, `continuousOn_floor_compl_range`**: fine.
- **`continuousAt_ceil`**
  - It is missing the `@[fun_prop]` its siblings carry (finding 2).
  - Its hypothesis is phrased with floor (finding 3).
- **`continuousOn_ceil_compl_range`**: fine. It still compiles after the finding-3 change.
- **`continuousOn_fract` / `continuousAt_fract`**: the new proofs through ℤ-valued floor are fine. No finding.
- **`tendsto_round_nhdsGE_pure`, `tendsto_round_nhdsLT_pure_half_ceil`, `continuousAt_round`, `continuousOn_round`**
  - The statements are correct, and `ContinuousAdd` is a reasonable assumption for `2 * ·`. The `nhdsGE`/`nhdsLT` naming follows the current library convention (`tendsto_inv_nhdsGT` and others).
  - Found: the naming mismatch with `round_eq_half_ceil_two_mul` (finding 6).
  - Found: the repeated instance binders; moving the lemmas under section variables compiles (finding 7).
  - Found: a term-mode golf of `continuousAt_round` (finding 10).
  - Adding `@[fun_prop]` to the round lemmas also compiles, but I am less confident a maintainer would ask for it, so I did not raise it.
  - The `have : Tendsto (2 * ·) ...` block is duplicated across the two tendsto lemmas. It could be factored, but I raised no finding.
- **Module docstring**: it does not mention `round` or the new pointwise continuity results, and its `continuousOn_ceil` interval is wrong (finding 8).
- **`section Ring` / `end Ring` wrapper and `ContinuousOn.comp_fract''`**: `comp_fract''` appears in the model as "added" only because of diff context; it is unchanged. No finding for either.

## The other changed files

AddConstMap/Basic, Archimedean/Basic, ToIntervalMod, ApproximateUnit, Arctan, GrowsPolynomially, GroupTheory/Archimedean, IntervalIntegral/Basic, DerivIntegrable, Liouville/Basic, AtTopBot/Archimedean and AddCircle/Defs each only add a private import, which the Round.lean import change requires. No finding.
