# Decision context: distributivity of the subgroup commutator over a join, and the normalizer-of-join lemma

Sources are numbered S1-S12. Each is listed once, under the decision it bears on most; other
decisions refer back to it by number.

## 1. Form of the new statement and its hypothesis (normality of N; weaker hypotheses)

**S1 — `library_example`** — `Mathlib/Algebra/Group/Subgroup/Pointwise.lean:351-367`

```lean
@[to_additive]
lemma normalizer_le_normalizer_sup_of_normalizer_le_left
    {H K : Subgroup G} (hHnK : normalizer H ≤ normalizer (K : Set G)) :
    normalizer H ≤ normalizer ((H ⊔ K : Subgroup G) : Set G) :=
  (inf_of_le_left hHnK).symm.trans_le (H.normalizer_inf_normalizer_le_normalizer_sup K)

@[to_additive]
lemma normalizer_le_normalizer_sup_of_normalizer_le_right {H K : Subgroup G}
    (hHnK : normalizer H ≤ normalizer (K : Set G)) :
    normalizer H ≤ normalizer ((K ⊔ H : Subgroup G) : Set G) := by
  rw [sup_comm]
  exact normalizer_le_normalizer_sup_of_normalizer_le_left hHnK

@[to_additive]
lemma normalizer_le_normalizer_sup_normal {H K : Subgroup G} [hK : K.Normal] :
    normalizer H ≤ normalizer ((H ⊔ K : Subgroup G) : Set G) :=
  normalizer_le_normalizer_sup_of_normalizer_le_left le_normalizer_of_normal
```

Bears on weaker hypotheses: in the same neighbourhood the library states a result under a
normalizer-inclusion hypothesis and then derives an instance-implicit `[K.Normal]` specialisation
from it (the same pairing appears at `Pointwise.lean:289-303`, `coe_mul_of_right_le_normalizer_left`
and `normal_mul`); it is also a consumer of the lemma being moved (line 355, called by dot notation).

See also S4 (the commutator file states normality as instance-implicit `[H₁.Normal]` arguments). The
commutator file also relates normalizer inclusion to commutator inclusion,
`le_normalizer_iff_commutator_le_right : H ≤ normalizer K ↔ ⁅H, K⁆ ≤ K` (line 245).

## 2. Whether the companion law (join in the second argument) is included, and the names of both

**S2 — `library_example`** — `Mathlib/Algebra/Lie/IdealOperations.lean:175-176, 190-191, 205, 209`

```lean
175  @[simp]
176  theorem lie_sup : ⁅I, N ⊔ N'⁆ = ⁅I, N⁆ ⊔ ⁅I, N'⁆ := by
190  @[simp]
191  theorem sup_lie : ⁅I ⊔ J, N⁆ = ⁅I, N⁆ ⊔ ⁅J, N⁆ := by
205  theorem lie_inf : ⁅I, N ⊓ N'⁆ ≤ ⁅I, N⁆ ⊓ ⁅I, N'⁆ := by
209  theorem inf_lie : ⁅I ⊓ J, N⁆ ≤ ⁅I, N⁆ ⊓ ⁅J, N⁆ := by
```

Bears on companion law and naming: the closest bracket-of-substructures analogue (Lie ideals acting on
Lie submodules) states both distributive laws as equalities, side by side, named by the
`sup_<op>` / `<op>_sup` pattern rather than a `_left`/`_right` suffix, and also gives the `inf`
inequalities.

**S3 — `library_example`** — `Mathlib/RingTheory/Ideal/Operations.lean:335-347`

```lean
theorem mul_sup : I * (J ⊔ K) = I * J ⊔ I * K :=
  Submodule.smul_sup I J K

theorem sup_mul : (I ⊔ J) * K = I * K ⊔ J * K :=
  Submodule.sup_smul I J K

theorem mul_iSup {ι : Sort*} (J : ι → Ideal R) :
    I * (⨆ i, J i) = ⨆ i, I * J i :=
  Submodule.smul_iSup

theorem iSup_mul {ι : Sort*} (J : ι → Ideal R) (I : Ideal R) :
    (⨆ i, J i) * I = ⨆ i, J i * I :=
  Submodule.iSup_smul
```

Bears on companion law, naming and indexed versions: ideal multiplication also carries both sides,
with the same `sup_mul`/`mul_sup` naming, and adds `iSup` versions on both sides.

S4 (listed under decision 3) also bears here: the commutator file's own
left/right pairs (`commutator_bot_left`/`commutator_bot_right`) use a `_left`/`_right` suffix naming
the argument that is specialised, a different convention from S2/S3. Within the commutator file
`commutator_comm` (line 183) relates the two argument orders.

## 3. Whether an additive counterpart is provided

**S4 — `counterexample`** — `Mathlib/GroupTheory/Commutator/Basic.lean:254-269`

```lean
@[to_additive (attr := simp)]
theorem commutator_bot_left : ⁅(⊥ : Subgroup G), H₁⁆ = ⊥ :=
  le_bot_iff.mp (commutator_le_left ⊥ H₁)

@[to_additive (attr := simp)]
theorem commutator_bot_right : ⁅H₁, ⊥⁆ = (⊥ : Subgroup G) :=
  le_bot_iff.mp (commutator_le_right H₁ ⊥)

@[to_additive]
theorem commutator_le_inf [Normal H₁] [Normal H₂] : ⁅H₁, H₂⁆ ≤ H₁ ⊓ H₂ :=
  le_inf (commutator_le_left H₁ H₂) (commutator_le_right H₁ H₂)

variable {H₁ H₂} in
theorem commutator_eq_bot_of_disjoint [H₁.Normal] [H₂.Normal] (h : Disjoint H₁ H₂) :
    ⁅H₁, H₂⁆ = ⊥ := by
  grw [eq_bot_iff, commutator_le_inf, h.eq_bot.le]
```

Bears on the additive counterpart: nearly every subgroup-commutator lemma in this file carries
`@[to_additive]` (the bracket instance itself does, line 130), but `commutator_eq_bot_of_disjoint`
does not, so the file is not uniform; the excerpt also shows instance-implicit normality hypotheses.

## 4. Whether versions for an indexed join (`⨆`) are provided

**S5 — `earlier_decision`** — Zulip `#Is there code for X?` > "Additional Group Theory Lemmas",
2026-06-05 and 2026-06-06

```text
Eric Wieser [maintainer] — 2026-06-05T17:06:22Z
  Certainly that first one looks reasonable, and we should have the `sSup` and `sup` versions too.
Snir Broshi — 2026-06-06T01:49:29Z
  Eric Wieser said: Certainly that first one looks reasonable, and we should have the `sSup` and
  `sup` versions too.
  and biSup, to match docs#Subgroup.sup_normal / docs#Subgroup.iSup_normal /
  docs#Subgroup.biSup_normal / docs#Subgroup.sSup_normal
```

Bears on indexed versions: a maintainer asked for the binary and set-indexed forms alongside an
indexed subgroup lemma, and the contributor cited the full `sup`/`iSup`/`biSup`/`sSup` family
(present at base, `Pointwise.lean:369-393`) as the pattern to match.

**S6 — `earlier_decision`** — Zulip `#mathlib4` > "inf/sup lemmas for upwards/downwards closed
classes", 2026-01-22

```text
Violeta Hernández — 2026-01-22T09:02:06Z
  I feel like these lemmas set a bad precedent. Do we also want versions for `sInf`/`sSup`? Then
  surely we also want versions for `iInf`/`iSup`, as well as `biInf`/`biSup` and now we're writing
  substantial boilerplate for something that's entirely obvious.
Martin Winter — 2026-01-22T10:36:50Z
  To get around the precedent argument we say that these lemmas need to be justified by how often
  they get used. Then nei…   [message truncated in the search result]
```

Bears on indexed versions from the other side: an argument (in a different, order-theoretic setting)
against multiplying `sup`/`iSup`/`biSup`/`sSup` variants, and a reply tying their inclusion to use.

See also S3 (ideals have `iSup` versions on both sides). A search of `Mathlib/Algebra/Lie` found no
`iSup_lie`/`lie_iSup`, so the Lie analogue S2 stops at the binary join.

## 5. Registration with automation (`simp`)

No separate source. The two analogues differ: S2's `lie_sup`/`sup_lie` are `@[simp]`, S3's
`mul_sup`/`sup_mul` are not. In the commutator file the `⊥`/`center` evaluations are
`@[to_additive (attr := simp)]` (S4), while `commutator_mono` and `commutator_comm` are not tagged.

## 6. Name of the moved normalizer lemma

**S7 — `library_example`** — `Mathlib/Algebra/Group/Subgroup/Basic.lean:524-532`

```lean
@[to_additive]
theorem inf_normalizer_le_normalizer_inf :
    normalizer H ⊓ normalizer K ≤ normalizer ((H ⊓ K :) : Set G) :=
  fun _ h g ↦ and_congr (h.1 g) (h.2 g)

@[to_additive]
theorem iInf_normalizer_le_normalizer_iInf {ι : Sort*} (H : ι → Subgroup G) :
    ⨅ i, normalizer (H i) ≤ normalizer ((⨅ i, H i : Subgroup G) : Set G) := by
  grind [le_normalizer_iff, mem_iInf, mem_normalizer_iff]
```

Bears on the name, argument binders and placement: the `⊓` neighbour of the moved lemma is named
`inf_normalizer_le_normalizer_inf` and takes `H K` implicitly (from `variable {H K}` at line 276 and
`variable {H}` at line 419), whereas the lemma to be moved names its left side
`normalizer_inf_normalizer` and takes `(H K : Subgroup G)` explicitly (S8).

**S8 — `consumer`** — `Mathlib/Algebra/Group/Subgroup/Pointwise.lean:333-349`

```lean
@[to_additive]
lemma normalizer_inf_normalizer_le_normalizer_sup (H K : Subgroup G) :
    normalizer H ⊓ normalizer K ≤ normalizer ((H ⊔ K : Subgroup G) : Set G) := by
  intro g hg
  simp_rw [mem_inf, mem_normalizer_iff_map_conj_eq, map_sup, hg.1, hg.2] at hg ⊢

@[to_additive]
theorem iInf_normalizer_le_normalizer_iSup {ι : Sort*} (H : ι → Subgroup G) :
    ⨅ i, normalizer (H i) ≤ normalizer ((⨆ i, H i : Subgroup G) : Set G) := by
  intro g hg
  simp_rw [mem_iInf, mem_normalizer_iff_map_conj_eq, map_iSup, hg] at hg ⊢

@[to_additive]
lemma conj_mem_sup_of_mem_inf_normalizer_of_mem_inf
    {H K : Subgroup G} {s : G} (hs : s ∈ normalizer H ⊓ normalizer K) (g : G) (hg : g ∈ H ⊔ K) :
    s * g * s⁻¹ ∈ H ⊔ K :=
  (normalizer_inf_normalizer_le_normalizer_sup H K hs g).mp hg
```

Bears on the name and scope: the indexed sibling is already named
`iInf_normalizer_le_normalizer_iSup` (it stays in `Pointwise.lean` and is used by `iSup_normal`,
line 380), and the two consumers pass `H K` explicitly (here, and by dot notation at line 355, S1).
A Mathlib-wide search found no other uses of the lemma.

## 7. Placement (of the moved lemma, and of the new law)

No separate source. Facts from the base files: `Subgroup/Basic.lean`'s `Normalizer` section (S7,
lines 385-547) holds the `⊓` and `⨅` neighbours; the moved lemma's proof uses
`mem_normalizer_iff_map_conj_eq` (`Basic.lean:405`) and `map_sup`, which `Basic.lean` already uses
(line 320). `Commutator/Basic.lean` uses `le_normalizer_iff` (line 246, declared at `Basic.lean:448`)
and `normal_subgroupOf_of_le_normalizer` (line 292, declared at `Basic.lean:1094`), so it builds on
`Subgroup/Basic.lean`; its direct imports are `Algebra.Group.Commutator`,
`GroupTheory.Subgroup.Centralizer` and `GroupTheory.QuotientGroup.Defs` (lines 8-10), whereas
`Pointwise.lean` is imported directly by `GroupTheory/QuotientGroup/Basic.lean` (not `Defs`). In the
commutator file, binary-commutator-versus-join results sit together after `section Normal`
(`commutator_le_sup`, line 274, then S12). Nothing was found on placement preferences beyond this.

## 8. Keeping the old names resolving (deprecation mechanics)

**S9 — `mechanism`** — `Mathlib/Algebra/Group/Subgroup/Finite.lean:94-98`

```lean
@[deprecated (since := "2026-04-08")]
alias _root_.AddSubgroup.val_finset_sum := _root_.AddSubgroup.val_finsetSum

@[to_additive existing, deprecated (since := "2026-04-08")]
alias val_finset_prod := val_finsetProd
```

Bears on keeping both names: at base, a renamed `@[to_additive]` lemma keeps its old names through a
separately declared additive `deprecated alias` followed by `to_additive existing` on the
multiplicative one. Other forms at base: two independent aliases (`Ker.lean:100-102`, and
`Basic.lean:409-411` for an additive-only rename) and `@[to_additive (attr := deprecated …)]`
(`Defs.lean:716`, `720`).

**S10 — `earlier_decision`** — review on PR #22650, `Mathlib/Algebra/Group/Subgroup/Basic.lean`,
2025-03-18 (eric-wieser), on the line
`@[to_additive (attr := deprecated le_normalizer_of_normal_subgroupOf (since := "2025-03-06"))] alias le_normalizer_of_normal := …`

```text
I worry this does the wrong thing, and deprecates the additive version in favor of the
multiplicative version. Perhaps @YaelDillies knows how `to_additive` interacts with `deprecated.
```

Bears on the deprecation form: a maintainer questioned whether `to_additive (attr := deprecated …)`
on an alias produces the right additive deprecation, a concern that separate additive aliases (S9)
sidestep.

## 9. Proof route

**S11 — `written_guidance`** — `Mathlib/GroupTheory/Commutator/Basic.lean:167-173`

```lean
  intro x hx y hy z hz
  trans x * z * ⁅y, ⁅z⁻¹, x⁻¹⁆⁆⁻¹ * z⁻¹ * y * ⁅x⁻¹, ⁅y⁻¹, z⁆⁆⁻¹ * y⁻¹ * x⁻¹
  -- We avoid `group` here to minimize imports while low in the hierarchy;
  -- typically it would be better to invoke the tactic.
  · simp [commutatorElement_def, mul_assoc]
  · rw [h1 _ (H₂.inv_mem hy) _ hz _ (H₁.inv_mem hx), h2 _ (H₃.inv_mem hz) _ (H₁.inv_mem hx) _ hy]
    simp [mul_assoc]
```

Bears on proof tactics and imports: the file states a preference for not importing heavier tactics
(`group`) at this point in the hierarchy, proving element identities by `simp [commutatorElement_def,
mul_assoc]` instead.

**S12 — `library_example`** — `Mathlib/GroupTheory/Commutator/Basic.lean:277-293`

```lean
@[to_additive]
theorem normalizer_commutator_ge_left : H₁ ≤ normalizer (⁅H₁, H₂⁆ : Subgroup G) := by
  apply le_normalizer_closure_iff.mpr
  rintro g hg _ ⟨g₁, hg₁, g₂, hg₂, rfl⟩
  apply (mul_mem_cancel_right <| commutator_mem_commutator hg hg₂).mp
  rw [← commutatorElement_mul_left_eq_conj_mul g g₁ g₂]
  exact commutator_mem_commutator (mul_mem hg hg₁) hg₂

@[to_additive]
theorem normalizer_commutator_ge_right : H₂ ≤ normalizer (⁅H₁, H₂⁆ : Subgroup G) := by
  rw [commutator_comm]
  apply normalizer_commutator_ge_left

@[to_additive]
instance normal_subgroupOf_commutator_sup : (⁅H₁, H₂⁆.subgroupOf <| H₁ ⊔ H₂).Normal :=
  normal_subgroupOf_of_le_normalizer <| sup_le
    (normalizer_commutator_ge_left H₁ H₂) (normalizer_commutator_ge_right H₁ H₂)
```

Bears on what is available for a proof: the file already has the element identity
`⁅a * b, c⁆ = a * ⁅b, c⁆ * a⁻¹ * ⁅a, c⁆` (`commutatorElement_mul_left_eq_conj_mul`, line 78),
normalizer facts about `⁅H₁, H₂⁆`, and a pattern that reasons about a join through `sup_le` on
normalizer inclusions; the two-sided Lie proofs (S2, lines 176-203) go instead by `le_antisymm` with
monotonicity for one inclusion and a spanning-set argument for the other.

## 10. Scope of edits

No separate source. The only uses of the moved lemma at base are the two Pointwise consumers
(S8 line 349, S1 line 355); `commutator_le_sup` (line 274) and `commutator_mono` (line 151) are the
existing join- and monotonicity-facts for subgroup commutators. No consumer of a commutator of a join
(`⁅… ⊔ …⁆`) was found in `Mathlib/GroupTheory`.
