# Where the reviewer had the topic but not the fix (2026-10-13, read by hand after the bars)

The 17 core asks that G's three reps reached only partly (matcher 1). Each entry: the maintainer's ask, the
partly-matching finding, the judge's note. Grouped by what the maintainer's fix needed:

- **A Mathlib tactic the reviewer did not try (4):** 5 `positivity`, 6 `gcongr`, 10 and 11 `grind` (with a
  `grind` attribute added). The reviewer tidied the existing `simp` proof instead, and its edits compiled.
- **Mathlib's own name, idiom or existing API (10):** 3 and 4 the `variable [...] in` idiom; 9 the existing
  constructor `ContinuousAlgEquiv.mk`; 12-15 the `ciSup`/`ciInf` names for conditionally complete lattices;
  16 which side of the equation the library puts the supremum; 17 `round_eq_div`; 8 a `HasProd` version, as
  the file does elsewhere. The reviewer's own proposals (`protected`, `_of_bddAbove`, a descriptive name, a
  section move) were sensible and not the library's.
- **The PR's history or the author's intent (3):** 1 and 2 how the PR relates to another PR and the plan for
  the definition; 7 why the old names were bad. Not in the code.

Reading: the reviewer had the topic and invented a fix; the maintainer's fix is the library's way. The open
question this leaves is whether a fix required to cite evidence that it is the library's way (a tactic the
harness ran, or an existing declaration of the same shape) reaches these. Not tested; 17 in-sample cases.

## 1. PR 29842 P14_val/v0053 (dropped)
MAINTAINER: How does this interact with #24163? When I tried something similar to this 8 months ago in #21065, I thought the consensus was to change the definition.

If you've changed your mind, could you explain why in the PR description?

REVIEWER (G1): PR #29842 has no description ("no description provided") and its title, `feat(TangentCone): generalize some lemmas to TVS`, describes only half of the diff: besides weakening the hypotheses of `tangentConeAt.lim_zero`, `tangentConeAt_mono_nhds`/`tangentConeAt_congr`/`tangentConeAt_inter_nhds` and the `UniqueDiffWithinAt.mono_nhds` family to `[ContinuousAdd E] [ContinuousSMul 𝕜 E]`, the change also moves the `end TVS`/`section Normed` boundaries a
  CHANGE: Write a PR description that says what moves where and which lemmas are generalized (and why the `section TVS`/`section Normed` split had to move with them), per the practice "The PR title and description say precisely what the change is (what moves where, what is renamed to what), kept accurate as the PR evolves."

JUDGE: Description findings ask what is generalized/moved, not how the PR relates to #24163 or the definition change.

## 2. PR 29842 P14_val/v0056 (dropped)
MAINTAINER: > but if I fail, then I would prefer to have one of the "generalize lemmas" PRs merged so that we can generalize downstream proofs here and there before generalizing the definition.

I'm fine with this, please just write something to this effect in the PR description.

REVIEWER (G1): PR #29842 has no description ("no description provided") and its title, `feat(TangentCone): generalize some lemmas to TVS`, describes only half of the diff: besides weakening the hypotheses of `tangentConeAt.lim_zero`, `tangentConeAt_mono_nhds`/`tangentConeAt_congr`/`tangentConeAt_inter_nhds` and the `UniqueDiffWithinAt.mono_nhds` family to `[ContinuousAdd E] [ContinuousSMul 𝕜 E]`, the change also moves the `end TVS`/`section Normed` boundaries a
  CHANGE: Write a PR description that says what moves where and which lemmas are generalized (and why the `section TVS`/`section Normed` split had to move with them), per the practice "The PR title and description say precisely what the change is (what moves where, what is renamed to what), kept accurate as the PR evolves."

JUDGE: Generic add-a-description findings; none asks to state the plan relative to changing the definition.

## 3. PR 30458 P14_val/v0060 (dropped)
MAINTAINER: you don't need to section these off
just keep things the same as before, collect the common variables, and then add variables as needed
so, in this case, instead of `variable [Group α]` at the start, change it to `[DivisionMonoid α]`, and keep the rest the same, and before this lemma add:
```suggestion
variable [IsLeftCancelMul α] in
@[to_additive] lemma card_le_card_div_left (hs : s.Nonempty) : #t ≤ #(s / t) := by
```

REVIEWER (G1): The `variable` block at lines 1264-1265 repeats `section LeftCancel`'s variable word for word and serves only `card_le_card_div_self`, which needs nothing beyond `[DivisionMonoid α] [IsLeftCancelMul α] [DecidableEq α]`, so the section structure now carries a duplicate variable.
  CHANGE: Move `card_le_card_div_self` (and its `to_additive` twin) into `section LeftCancel`, right after `card_le_card_div_left`, and delete the trailing `variable` block.

JUDGE: All object to the new section/variable layout (duplicate variable, section names) but keep the subsections; none proposes `variable ... in`.

## 4. PR 30458 P14_val/v0061 (dropped)
MAINTAINER: following the above suggestion:
```suggestion
variable [IsRightCancel α] in
@[to_additive] lemma card_le_card_div_right (ht : t.Nonempty) : #s ≤ #(s / t) := by
```

REVIEWER (G3): In the new `section DivisionMonoid` the `variable` block written before `card_le_card_div_self` (lines 1264-1265) is a verbatim duplicate of the one already declared in `section LeftCancel` (line 1247), whereas the analogous `card_le_card_mul_self` sits inside `section IsLeftCancelMul` (line 1179) and shares its variables; moreover the new sections are named `LeftCancel`/`RightCancel` while the file's existing sections for exactly these two mixin
  CHANGE: Name the two inner sections `IsLeftCancelMul`/`IsRightCancelMul` and move `card_le_card_div_self` inside the left-cancel section right after `card_le_card_div_left`, deleting the duplicated `variable` line (compiles, no new warnings).

JUDGE: R2, R5 rename the RightCancel section; R3, R4 only weaken its hypothesis to DivInvMonoid, a different issue.

## 5. PR 30641 P14_val/v0067 (dropped)
MAINTAINER: Can `positivity` do this (untested)?

REVIEWER (G1): The monotonicity step is written `apply monotoneOn_posLog (by simp) _ (norm_sum_le s f)`, i.e. with a bare hole, whose side goal `0 ≤ ∑ t ∈ s, ‖f t‖` is then discharged by a separate `simp` tactic line. The sibling `Real.posLog_sum` discharges the identical side goal inline inside the same application (line 169: `apply monotoneOn_posLog (by simp) (by simp [Finset.sum_nonneg])`).
  CHANGE: Replace the two lines by a single application that discharges the side goal inline: `apply monotoneOn_posLog (by simp) (by simp [Finset.sum_nonneg]) (norm_sum_le s f)` (or use `refine monotoneOn_posLog (by simp) ?_ (norm_sum_le s f)` if the hole is kept).

JUDGE: positivity for side goal; R3/R5 inline the same side goal with simp, not positivity.

## 6. PR 30641 P14_val/v0068 (never reached)
MAINTAINER: Can `gcongr` do this (or do you need to provide the side condition manually)?

REVIEWER (G1): The monotonicity step is written `apply monotoneOn_posLog (by simp) _ (norm_sum_le s f)`, i.e. with a bare hole, whose side goal `0 ≤ ∑ t ∈ s, ‖f t‖` is then discharged by a separate `simp` tactic line. The sibling `Real.posLog_sum` discharges the identical side goal inline inside the same application (line 169: `apply monotoneOn_posLog (by simp) (by simp [Finset.sum_nonneg])`).
  CHANGE: Replace the two lines by a single application that discharges the side goal inline: `apply monotoneOn_posLog (by simp) (by simp [Finset.sum_nonneg]) (norm_sum_le s f)` (or use `refine monotoneOn_posLog (by simp) ?_ (norm_sum_le s f)` if the hole is kept).

JUDGE: gcongr for the monotonicity step; R3/R5 only fold the side condition inline.

## 7. PR 41930 P14_post/p0000 (never reached)
MAINTAINER: Can you explain why the old names are bad / wrong?

REVIEWER (G1): The description says 'Name the motive `motive` and name the minor premises according to their contents', but the diff renames no minor premise: `induction_on'`'s `one`, `inl_mul`, `inr_mul` and `induction_on`'s `inl`, `inr`, `mul` are identical before and after, and only the motive binder `C` became `motive`. The description therefore advertises a change the diff does not make, against the practice that the description states precisely what is re
  CHANGE: Reword the description to match the diff, e.g. 'Rename the motive argument of `Monoid.Coprod.induction_on'` and `Monoid.Coprod.induction_on` from `C` to `motive`', or, if renaming the minor premises was intended, actually rename them (they would then need updating in the proofs and in the `induction … with | …` case names used downstream, e.g. in `

JUDGE: Partials ask the description to state the rename accurately (only C->motive); none asks why the old names are bad.

## 8. PR 42184 P14_post/p0003 (never reached)
MAINTAINER: and maybe you can provide a HasProd version of this lemma (as this seems to be the convention in this file)

REVIEWER (G3): Where is the additive counterpart of `tprod_nonneg`? Every other multiplicative declaration in this file is paired with its additive twin by `@[to_additive]`, but here no attribute (and no comment explaining its absence) is present — and none can be attached: `@[to_additive]` fails with '`to_additive` validation failed: expected ... [CommMonoidWithZero α] ... [PosMulMono α] ... 0 ≤ ∑'[L] (x : ι), f x but `tsum_nonneg` has type ... [AddCommMonoid 
  CHANGE: Provide the additive counterpart, written by hand since `to_additive` cannot translate this signature. This compiles: `theorem tsum_nonneg' [AddCommMonoid α] [TopologicalSpace α] [Preorder α] [AddLeftMono α] [ClosedIciTopology α] [L.NeBot] {f : ι → α} (hf : ∀ i, 0 ≤ f i) : 0 ≤ ∑'[L] x, f x`, proved by the same case split with `Finset.sum_nonneg` an

JUDGE: No HasProd version asked; R5 asks a missing companion (additive) per file convention. le_hasProd_of_le_prod proof rewrites are not it.

## 9. PR 33066 D12/d0002 (never reached)
MAINTAINER: This is just the pre-existing constructor for `ContinuousAlgEquiv`:
```
ContinuousAlgEquiv.mk.{u_1, u_2, u_3} {R : Type u_1} {A : Type u_2} {B : Type u_3} [CommSemiring R] [Semiring A]
  [TopologicalSpace A] [Semiring B] [TopologicalSpace B] [Algebra R A] [Algebra R B] (toAlgEquiv : A ≃ₐ[R] B)
  (continuous_toFun : Continuous toAlgEquiv.toFun := by fun_prop)
  (continuous_invFun : Continuous toAlgEquiv.invFun := by fun_prop) : A ≃A[R]
```
(up to some defeqs involving `toAlgEquiv.invFun`, `AlgEqu

REVIEWER (G2): `ofAlgEquiv` supersedes the hand-rolled construction in `_root_.AlgEquiv.isUniformEmbedding`, thirty lines above it, which builds the same object with `{ e with continuous_toFun := h₁, continuous_invFun := by dsimp; fun_prop }`, re-deriving the inverse continuity even though `h₂ : Continuous e.symm` is a hypothesis; because the definition is placed after that lemma, the reuse is not possible.
  CHANGE: Move `def ofAlgEquiv` above `_root_.AlgEquiv.isUniformEmbedding` and replace that lemma's proof with `ContinuousAlgEquiv.isUniformEmbedding (ofAlgEquiv e h₁ h₂)` (checked to compile for the lemma's exact hypotheses).

JUDGE: No one says ofAlgEquiv is just mk; R4 flags ofAlgEquiv duplicating a hand-built construction but keeps it.

## 10. PR 33098 D12/d0008 (dropped)
MAINTAINER: This and the next three lemmas can be proven with this, although for it to work on `finite_minimalCover`, you have to add
```lean
attribute [grind .] finite_empty
```
but I think we should do that anyway.
```suggestion
lemma minimalCover_subset : minimalCover ε A ⊆ A := by
  grind [minimalCover]
```

REVIEWER (G3): `minimalCover` is a new definition with no lemma characterising its value: its four lemmas all unfold it by hand, e.g. `minimalCover_subset` uses `simp only [minimalCover, ne_eq, h, not_false_eq_true, ↓reduceDIte]`, which is why the internal lemma `↓reduceDIte` appears in the reviewed code.
  CHANGE: Add characterising lemmas, e.g. `lemma minimalCover_eq_empty (h : coveringNumber ε A = ⊤) : minimalCover ε A = ∅` and `lemma minimalCover_of_ne_top (h : coveringNumber ε A ≠ ⊤) : minimalCover ε A = (exists_set_encard_eq_coveringNumber h).choose` (both are `by simp [minimalCover, h]`, which I compiled), mark them `@[simp]`, and replace the hand-unfo

JUDGE: R4 (dif_pos) and R5 (characterising lemmas) simplify minimalCover proofs differently; no grind.

## 11. PR 33098 D12/d0009 (dropped)
MAINTAINER: This and the next two lemmas can be proven with this, although for it to work on `isSeparated_maximalSeparatedSet`, you have to add
```lean
attribute [grind .] IsSeparated.empty
```
but I think we should do that anyway.

```suggestion
lemma maximalSeparatedSet_subset : maximalSeparatedSet ε A ⊆ A := by
  by grind [maximalSeparatedSet]
```

REVIEWER (G2): The `⊤` branch is a terminal `simp only [maximalSeparatedSet, h, dite_false, Set.empty_subset]`, and it is spelled differently from the identical branch of the sibling `minimalCover_subset` (`simp [minimalCover, h]`).
  CHANGE: Write the terminal branch as `simp [maximalSeparatedSet, h]` (verified to compile).

JUDGE: Different simplifications of maximalSeparatedSet lemma proofs; none proposes grind.

## 12. PR 33145 D12/d0022 (dropped)
MAINTAINER: ```suggestion
theorem Dense.ciSup {α : Type*} [TopologicalSpace α]
```

REVIEWER (G1): `Dense.continuous_sup`'s short name `continuous_sup` clashes with the root-namespace declaration `continuous_sup` in `Mathlib/Topology/Order/Lattice.lean:87` (about `Continuous fun p : L × L => p.1 ⊔ p.2`), so the declaration must be `protected` so that `open Dense` cannot shadow the root name; it is not `protected` at present.
  CHANGE: Declare it as `protected theorem Dense.continuous_sup ...` (dot notation still resolves protected namespaced lemmas).

JUDGE: Name of continuous_sup questioned (clash, or _of_bddAbove), never renamed to ciSup.

## 13. PR 33145 D12/d0023 (dropped)
MAINTAINER: ```suggestion
theorem Dense.ciInf {α : Type*} [TopologicalSpace α]
```

REVIEWER (G1): `Dense.continuous_inf`'s short name `continuous_inf` clashes with the root-namespace declaration `continuous_inf` in `Mathlib/Topology/Order/Lattice.lean:78`, so the declaration must be `protected`; it is not `protected` at present.
  CHANGE: Declare it as `protected theorem Dense.continuous_inf ...`.

JUDGE: R2 flags continuous_inf name clash, proposes protected, not ciInf.

## 14. PR 33145 D12/d0025 (dropped)
MAINTAINER: ```suggestion
theorem Dense.ciSup' {α : Type*} [TopologicalSpace α]
```

REVIEWER (G2): `Dense.continuous_sup'` differs from `Dense.continuous_sup` only by a prime; the term of its statement that differs is the `ConditionallyCompleteLinearOrder` codomain, equivalently the missing `BddAbove (range f)` hypothesis, and the name does not say it. Could you say what the primed name is meant to convey, and rename so that the differing term appears in the name (e.g. naming the version that has the hypothesis `Dense.continuous_sup_of_bddAbov
  CHANGE: Rename so that the difference is in the name rather than a prime; note that the version with the hypothesis `BddAbove (range f)` is the one the naming practice gives a `_of_...` suffix.

JUDGE: Prime name criticised with different proposals; ciSup' absent.

## 15. PR 33145 D12/d0027 (dropped)
MAINTAINER: ```suggestion
theorem Dense.ciInf' {α : Type*} [TopologicalSpace α]
```

REVIEWER (G2): As with `Dense.continuous_sup'`, `Dense.continuous_inf'` records the variant only by a prime; nothing in the name says that the codomain is a conditionally complete *linear* order and that no boundedness hypothesis is needed. Once the declaration is the dual of `Dense.continuous_sup'`, the pair should be named as a dual pair.
  CHANGE: Rename together with `Dense.continuous_sup'` so that the differing hypothesis/instance appears in the name instead of a prime.

JUDGE: Prime name of continuous_inf' criticised with different proposals; ciInf' absent.

## 16. PR 33145 D12/d0029 (never reached)
MAINTAINER: I suggest turning the declarations involving `iSup` and `iInf` around so that they read:
```lean
    ⨆ s : S, f s = ⨆ i, f i := by
```
instead.

REVIEWER (G1): The docstring of `Dense.continuous_sup` describes the equality with its two sides in the opposite order to the statement (the statement is `⨆ i, f i = ⨆ s : S, f s`, with the supremum over the whole space on the left) and says "the supremum on the universe", which is not how the library refers to `univ`.
  CHANGE: Reword to follow the statement, e.g. "The supremum of a bounded above continuous function over a dense set equals its supremum over `univ`."

JUDGE: R2 and R4 note the docstring order opposes the statement but fix the docstring, not the statement.

## 17. PR 33421 D12/d0048 (dropped)
MAINTAINER: How about `round_eq_div`?

REVIEWER (G1): `round_eq'` is a bare prime: it states a different formula from `round_eq` (`(⌊2 * x⌋ + 1) / 2` versus `⌊x + 1 / 2⌋`), and the practice asks a variant to name the term of its statement that differs rather than append a prime - the sibling added in this same PR, `round_eq_half_ceil_two_mul`, does exactly that.
  CHANGE: Rename `round_eq'` to a name spelling its right-hand side, e.g. `round_eq_half_floor_two_mul_add_one` (mirroring `round_eq_half_ceil_two_mul`), and update the four use sites (`round_eq_half_ceil_two_mul`, `round_eq`, and the two `tendsto_round_*` proofs).

JUDGE: Four say the primed round_eq' name is uninformative but propose different names, not round_eq_div.
