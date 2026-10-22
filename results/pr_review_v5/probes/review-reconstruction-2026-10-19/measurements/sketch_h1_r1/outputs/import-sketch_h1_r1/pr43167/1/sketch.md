# Sketch: `⁅H ⊔ K, N⁆ = ⁅H, N⁆ ⊔ ⁅K, N⁆`, and moving the normalizer-of-join lemma

All Lean is unchecked.

## 1. Hypothesis of the new law
- **Choice:** a general lemma under normalizer hypotheses, then the normal case as a corollary:
  ```lean
  @[to_additive]
  theorem commutator_sup_left_of_le_normalizer (h₁ : H₁ ≤ normalizer K) (h₂ : H₂ ≤ normalizer K) :
      ⁅H₁ ⊔ H₂, K⁆ = ⁅H₁, K⁆ ⊔ ⁅H₂, K⁆
  @[to_additive]
  theorem commutator_sup_left [K.Normal] : ⁅H₁ ⊔ H₂, K⁆ = ⁅H₁, K⁆ ⊔ ⁅H₂, K⁆ :=
    commutator_sup_left_of_le_normalizer H₁ H₂ le_normalizer_of_normal le_normalizer_of_normal
  ```
  Binders follow the file's variables (`H₁ H₂` explicit since line 175, `K` implicit).
- **Alternatives:** only `[K.Normal]`, as the inputs state; one hypothesis `H₁ ⊔ H₂ ≤ normalizer K`.
- **References:** the pairs `coe_mul_of_right_le_normalizer_left`/`normal_mul` (`Pointwise.lean:289,302`) and `normalizer_le_normalizer_sup_of_normalizer_le_left`/`_normal` (`Pointwise.lean:352,365`); instance-implicit normality in `Commutator/Basic.lean:228-269`.
- **What would decide it:** the proof in 8 needs normality only through these two inclusions, so it costs nothing. A reviewer asking for the bare normal version would decide it the other way.

## 2. Names
- **Choice:** `commutator_sup_left`, `commutator_sup_right`, `_left`/`_right` naming the argument that is a join.
- **Alternatives:** `sup_commutator`/`commutator_sup`, the `sup_lie`/`lie_sup` and `sup_mul`/`mul_sup` scheme.
- **References:** `commutator_bot_left/right`, `commutator_center_left/right` (`Commutator/Basic.lean:200-260`); `sup_lie` and `sup_mul` (decision_context S2, S3, not in `base/`).
- **What would decide it:** open. The file's own convention points to the suffix, other bracket-like operations to the prefix.

## 3. Companion law
- **Choice:** include `commutator_sup_right : ⁅K, H₁ ⊔ H₂⁆ = ⁅K, H₁⁆ ⊔ ⁅K, H₂⁆` (and its `_of_le_normalizer` form), proved by `commutator_comm` three times.
- **Alternatives:** the left law only.
- **References:** `commutator_le_left` derived from `_right` through `commutator_comm` (`Commutator/Basic.lean:232`); both sides in S2 and S3.
- **What would decide it:** nothing against it. It is one line, and the file pairs every left/right statement.

## 4. Additive counterpart
- **Choice:** `@[to_additive]` on all of them.
- **Alternatives:** omit, as `commutator_eq_bot_of_disjoint` does (`:266`).
- **References:** the bracket instance and almost every lemma in the file (`:130`, S4).
- **What would decide it:** whether `to_additive` translates the proof. Only group operations are used, so it should.

## 5. Indexed joins
- **Choice:** not in this contribution.
- **Alternatives:** `commutator_iSup_left : ⁅⨆ i, H i, K⁆ = ⨆ i, ⁅H i, K⁆` as the main lemma, with the binary one derived from it. Possibly `biSup`/`sSup` too.
- **References:** the `sup`/`iSup`/`biSup`/`sSup` family (`Pointwise.lean:370-393`); S5 (maintainer asked for the full family) against S6 (boilerplate only on use).
- **What would decide it:** a consumer, or a reviewer request. Open.

## 6. `simp`
- **Choice:** no attribute.
- **Alternatives:** `@[simp]` on the `[K.Normal]` form, like `sup_lie`.
- **References:** `commutator_mono` and `commutator_comm` untagged (`:151,183`); `sup_mul` untagged (S3).
- **What would decide it:** whether distributing the bracket is wanted as a normal form. Open.

## 7. Placement of the new law
- **Choice:** `Mathlib/GroupTheory/Commutator/Basic.lean`, at the end of `section Normal` (before `:271`), after `le_normalizer_iff_commutator_le_right` (`:245`), which the proof uses.
- **Alternatives:** after `commutator_le_sup` (`:274`), with the other commutator-and-join facts.
- **References:** `Commutator/Basic.lean:208-293`.
- **What would decide it:** open. Either location compiles.

## 8. Proof route
- **Choice:** `le_antisymm`.
  - `≥`: `sup_le (commutator_mono le_sup_left le_rfl) (commutator_mono le_sup_right le_rfl)`.
  - `≤`: `commutator_le`, then `closure_induction` on `H₁ ⊔ H₂ = closure (H₁ ∪ H₂)` (recalled: `sup_eq_closure`). Write `L` for the right-hand side and take `P g := ∀ n ∈ K, ⁅g, n⁆ ∈ L`.
    - `mul`: `⁅xy,n⁆ = x⁅y,n⁆x⁻¹⁅x,n⁆` (`:78`) and `x z x⁻¹ = ⁅x,z⁆ z` (`:36`), where `z ∈ L ≤ K` by `le_normalizer_iff_commutator_le_right`.
    - `inv`: `⁅g⁻¹,n⁆ = n ⁅g, g⁻¹n⁻¹g⁆ n⁻¹`. This needs `K ≤ normalizer L`, which comes from `normalizer_commutator_ge_right` (`:286`) twice and the moved lemma. That makes the move a prerequisite.

  Close the element identities with `simp [commutatorElement_def, mul_assoc]`, not `group`.
- **Alternatives:** `closure_induction_left` (recalled), whose generating set is closed under inverses, so the moved lemma is not needed.
- **References:** S11 (`:169`); `normal_subgroupOf_commutator_sup` (`:291`).
- **What would decide it:** proof length once compiled.

## 9. Name and binders of the moved lemma
- **Choice:** `inf_normalizer_le_normalizer_sup`, with `H K` implicit.
- **Alternatives:** keep `H K` explicit, so that old explicit calls still type-check; keep the old name.
- **References:** `inf_normalizer_le_normalizer_inf` (`Basic.lean:525`) and `iInf_normalizer_le_normalizer_iSup` (`Pointwise.lean:340`) both already read "inf of normalizers ≤ normalizer of the join/meet"; implicit `{H K}` there (`Basic.lean:276,419`).
- **What would decide it:** consistency with `:525` favours implicit binders. The two consumers (`Pointwise.lean:349,355`) are rewritten anyway, the second leaving dot notation.

## 10. Placement of the moved lemma
- **Choice:** `Mathlib/Algebra/Group/Subgroup/Basic.lean`, between `:527` and `:529`, keeping its proof. `mem_normalizer_iff_map_conj_eq` (`:405`) and `map_sup` (`:320`) are already available there.
- **Alternatives:** move `iInf_normalizer_le_normalizer_iSup` along with it. Its `map_iSup` is available too (`:325`).
- **References:** the `Normalizer` section, `Basic.lean:385-547`.
- **What would decide it:** scope. The brief moves one lemma, and `iSup_normal` (`Pointwise.lean:380`) keeps its sibling in place. Open.

## 11. Old names
- **Choice:** next to the new lemma,
  ```lean
  @[deprecated (since := "<merge date>")]
  alias _root_.AddSubgroup.normalizer_inf_normalizer_le_normalizer_sup :=
    AddSubgroup.inf_normalizer_le_normalizer_sup
  @[to_additive existing, deprecated (since := "<merge date>")]
  alias normalizer_inf_normalizer_le_normalizer_sup := inf_normalizer_le_normalizer_sup
  ```
- **Alternatives:** `@[to_additive (attr := deprecated …)]`; deprecated theorems that keep the old explicit signature.
- **References:** `Finite.lean:94-98` (S9); S10, where a maintainer doubted the `attr := deprecated` form.
- **What would decide it:** whether downstream calls with explicit `H K` must keep compiling. That favours the theorem form.
