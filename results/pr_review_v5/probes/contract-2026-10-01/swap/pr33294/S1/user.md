# Pull request #33294

**Title:** refactor: deprecate `Ordinal.IsNormal` for `Order.IsNormal`

**Description:**
See issue #17033.

Moved from #28743.

**Changed files:**
  - `Mathlib/Order/IsNormal.lean`
  - `Mathlib/SetTheory/Cardinal/Aleph.lean`
  - `Mathlib/SetTheory/Cardinal/Cofinality.lean`
  - `Mathlib/SetTheory/Ordinal/Arithmetic.lean`
  - `Mathlib/SetTheory/Ordinal/Enum.lean`
  - `Mathlib/SetTheory/Ordinal/Exponential.lean`
  - `Mathlib/SetTheory/Ordinal/Family.lean`
  - `Mathlib/SetTheory/Ordinal/FixedPoint.lean`
  - `Mathlib/SetTheory/Ordinal/Principal.lean`
  - `Mathlib/SetTheory/Ordinal/Topology.lean`
  - `Mathlib/SetTheory/Ordinal/Veblen.lean`

**Tools available:** read files, grep the repo (content_search), find files by name (file_search), compile your edit against the reviewed workspace (lean_verify_edit)


---

## The PR model (pass 0)

# The PR model for #33294 (pass 0)

Built deterministically from the diff and the change graph, with no review text. Every entry is a **fact** unless marked `hypothesis`; a hypothesis is a question to check, not a premise. Not built, so not here: library candidates, the area's twin patterns and conventions, and other open PRs. Construct what you need of those with the tools.

## The PR

- title: refactor: deprecate `Ordinal.IsNormal` for `Order.IsNormal`
- description: See issue #17033.

Moved from #28743.
- changed files: Mathlib/Order/IsNormal.lean, Mathlib/SetTheory/Cardinal/Aleph.lean, Mathlib/SetTheory/Cardinal/Cofinality.lean, Mathlib/SetTheory/Ordinal/Arithmetic.lean, Mathlib/SetTheory/Ordinal/Enum.lean, Mathlib/SetTheory/Ordinal/Exponential.lean, Mathlib/SetTheory/Ordinal/Family.lean, Mathlib/SetTheory/Ordinal/FixedPoint.lean, Mathlib/SetTheory/Ordinal/Principal.lean, Mathlib/SetTheory/Ordinal/Topology.lean, Mathlib/SetTheory/Ordinal/Veblen.lean

## Objects

### `Order.IsNormal.monotone` (theorem, added) [a6b84bedeb]
- file: `Mathlib/Order/IsNormal.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
protected theorem monotone {f : α → β} (hf : IsNormal f) : Monotone f :=
  hf.strictMono.monotone
```

### `Ordinal.isNormal_omega` (theorem, modified) [2ff907eb75]
- file: `Mathlib/SetTheory/Cardinal/Aleph.lean`; changed: proof:modified
- before the PR:
```lean
theorem isNormal_omega : IsNormal omega :=
  isNormal_preOmega.trans (isNormal_add_right _)
```
- as the PR leaves it:
```lean
theorem isNormal_omega : IsNormal omega :=
  isNormal_preOmega.comp (isNormal_add_right _)
```

### `Ordinal.isNormal_preOmega` (theorem, modified) [b8fb78c72e]
- file: `Mathlib/SetTheory/Cardinal/Aleph.lean`; changed: proof:modified
- before the PR:
```lean
theorem isNormal_preOmega : IsNormal preOmega := by
  rw [isNormal_iff_strictMono_limit]
  refine ⟨preOmega_strictMono, fun o ho a ha ↦
    (preOmega_le_of_forall_lt (isInitial_ord _) fun b hb ↦ ?_).trans (ord_card_le a)⟩
  rw [← (isInitial_ord _).card_lt_card, card_ord]
  apply lt_of_lt_of_le _ (card_le_card <| ha _ (ho.succ_lt hb))
  rw [(isInitial_preOmega _).card_lt_card, preOmega_lt_preOmega]
  exact lt_succ b
```
- as the PR leaves it:
```lean
theorem isNormal_preOmega : IsNormal preOmega := by
  rw [isNormal_iff]
  refine ⟨preOmega_strictMono, fun o ho a ha ↦
    (preOmega_le_of_forall_lt (isInitial_ord _) fun b hb ↦ ?_).trans (ord_card_le a)⟩
  rw [← (isInitial_ord _).card_lt_card, card_ord]
  apply lt_of_lt_of_le _ (card_le_card <| ha _ (ho.succ_lt hb))
  rw [(isInitial_preOmega _).card_lt_card, preOmega_lt_preOmega]
  exact lt_succ b
```

### `Ordinal.preOmega_omega0` (theorem, modified) [ee6abd7573]
- file: `Mathlib/SetTheory/Cardinal/Aleph.lean`; changed: proof:modified
- before the PR:
```lean
@[simp]
theorem preOmega_omega0 : preOmega ω = ω := by
  simp_rw [← isNormal_preOmega.apply_omega0, preOmega_natCast, iSup_natCast]
```
- as the PR leaves it:
```lean
@[simp]
theorem preOmega_omega0 : preOmega ω = ω := by
  simp_rw [← apply_omega0_of_isNormal isNormal_preOmega, preOmega_natCast, iSup_natCast]
```

### `Ordinal.isFundamentalSequence_of_isNormal` (theorem, modified) [2642023d5d]
- file: `Mathlib/SetTheory/Cardinal/Cofinality.lean`; changed: attributes:removed, name:modified
- before the PR:
```lean
protected theorem IsNormal.isFundamentalSequence {f : Ordinal.{u} → Ordinal.{u}} (hf : IsNormal f)
    {a o} (ha : IsSuccLimit a) {g} (hg : IsFundamentalSequence a o g) :
    IsFundamentalSequence (f a) o fun b hb => f (g b hb) := by
  refine ⟨?_, @fun i j _ _ h => hf.strictMono (hg.2.1 _ _ h), ?_⟩
  · rcases exists_lsub_cof (f a) with ⟨ι, f', hf', hι⟩
    rw [← hg.cof_eq, ord_le_ord, ← hι]
    suffices (lsub.{u, u} fun i => sInf { b : Ordinal | f' i ≤ f b }) = a by
      rw [← this]
      apply cof_lsub_le
    have H : ∀ i, ∃ b < a, f' i ≤ f b := fun i => by
      have := lt_lsub.{u, u} f' i
      rw [hf', ← IsNormal.blsub_eq.{u, u} hf ha, lt_blsub_iff] at this
      simpa using this
    refine (lsub_le fun i => ?_).antisymm (le_of_forall_lt fun b hb => ?_)
    · rcases H i with ⟨b, hb, hb'⟩
      exact lt_of_le_of_lt (csInf_le' hb') hb
    · have := hf.strictMono hb
      rw [← hf', lt_lsub_iff] at this
      obtain ⟨i, hi⟩ := this
      rcases H i with ⟨b, _, hb⟩
      exact
        ((le_csInf_iff'' ⟨b, by exact hb⟩).2 fun c hc =>
          hf.strictMono.le_iff_le.1 (hi.trans hc)).trans_lt (lt_lsub _ i)
  · rw [@blsub_comp.{u, u, u} a _ (fun b _ => f b) (@fun i j _ _ h => hf.strictMono.monotone h) g
        hg.2.2]
    exact IsNormal.blsub_eq.{u, u} hf ha
```
- as the PR leaves it:
```lean
theorem isFundamentalSequence_of_isNormal {f : Ordinal.{u} → Ordinal.{u}} (hf : IsNormal f)
    {a o} (ha : IsSuccLimit a) {g} (hg : IsFundamentalSequence a o g) :
    IsFundamentalSequence (f a) o fun b hb => f (g b hb) := by
  refine ⟨?_, @fun i j _ _ h => hf.strictMono (hg.2.1 _ _ h), ?_⟩
  · rcases exists_lsub_cof (f a) with ⟨ι, f', hf', hι⟩
    rw [← hg.cof_eq, ord_le_ord, ← hι]
    suffices (lsub.{u, u} fun i => sInf { b : Ordinal | f' i ≤ f b }) = a by
      rw [← this]
      apply cof_lsub_le
    have H : ∀ i, ∃ b < a, f' i ≤ f b := fun i => by
      have := lt_lsub.{u, u} f' i
      rw [hf', ← IsNormal.blsub_eq.{u, u} hf ha, lt_blsub_iff] at this
      simpa using this
    refine (lsub_le fun i => ?_).antisymm (le_of_forall_lt fun b hb => ?_)
    · rcases H i with ⟨b, hb, hb'⟩
      exact lt_of_le_of_lt (csInf_le' hb') hb
    · have := hf.strictMono hb
      rw [← hf', lt_lsub_iff] at this
      obtain ⟨i, hi⟩ := this
      rcases H i with ⟨b, _, hb⟩
      exact
        ((le_csInf_iff'' ⟨b, by exact hb⟩).2 fun c hc =>
          hf.strictMono.le_iff_le.1 (hi.trans hc)).trans_lt (lt_lsub _ i)
  · rw [@blsub_comp.{u, u, u} a _ (fun b _ => f b) (@fun i j _ _ h => hf.strictMono.monotone h) g
        hg.2.2]
    exact IsNormal.blsub_eq.{u, u} hf ha
```

### `command in Cofinality.lean` (command, added) [35a7f809a6]
- file: `Mathlib/SetTheory/Cardinal/Cofinality.lean`; changed: value_or_body:modified
- as the PR leaves it:
```lean
@[deprecated (since := "2025-12-25")]
alias IsNormal.cof_le := cof_le_of_isNormal
```

### `command in Cofinality.lean` (command, added) [39f0caa30a]
- file: `Mathlib/SetTheory/Cardinal/Cofinality.lean`; changed: value_or_body:modified
- as the PR leaves it:
```lean
@[deprecated (since := "2025-12-25")]
alias IsNormal.isFundamentalSequence := isFundamentalSequence_of_isNormal
```

### `Ordinal.cof_add` (theorem, modified) [468abce02b]
- file: `Mathlib/SetTheory/Cardinal/Cofinality.lean`; changed: proof:modified
- before the PR:
```lean
@[simp]
theorem cof_add (a b : Ordinal) : b ≠ 0 → cof (a + b) = cof b := fun h => by
  rcases zero_or_succ_or_isSuccLimit b with (rfl | ⟨c, rfl⟩ | hb)
  · contradiction
  · rw [add_succ, cof_succ, cof_succ]
  · exact (isNormal_add_right a).cof_eq hb
```
- as the PR leaves it:
```lean
@[simp]
theorem cof_add (a b : Ordinal) : b ≠ 0 → cof (a + b) = cof b := fun h => by
  rcases zero_or_succ_or_isSuccLimit b with (rfl | ⟨c, rfl⟩ | hb)
  · contradiction
  · rw [add_succ, cof_succ, cof_succ]
  · exact cof_eq_of_isNormal (isNormal_add_right a) hb
```

### `Ordinal.cof_eq_of_isNormal` (theorem, added) [4fbdf6af72]
- file: `Mathlib/SetTheory/Cardinal/Cofinality.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem cof_eq_of_isNormal {f} (hf : IsNormal f) {a} (ha : IsSuccLimit a) : cof (f a) = cof a :=
  let ⟨_, hg⟩ := exists_fundamental_sequence a
  ord_injective (isFundamentalSequence_of_isNormal hf ha hg).cof_eq
```

### `command in Cofinality.lean` (command, added) [50d94ab7b5]
- file: `Mathlib/SetTheory/Cardinal/Cofinality.lean`; changed: value_or_body:modified
- as the PR leaves it:
```lean
@[deprecated (since := "2025-12-25")]
alias IsNormal.cof_eq := cof_eq_of_isNormal
```

### `Ordinal.IsNormal.cof_le` (theorem, removed) [641255bd15]
- file: `Mathlib/SetTheory/Cardinal/Cofinality.lean`; changed: name:removed, proof:removed, statement_or_type:removed
- before the PR:
```lean
theorem IsNormal.cof_le {f} (hf : IsNormal f) (a) : cof a ≤ cof (f a) := by
  rcases zero_or_succ_or_isSuccLimit a with (rfl | ⟨b, rfl⟩ | ha)
  · rw [cof_zero]
    exact zero_le _
  · rw [cof_succ, Cardinal.one_le_iff_ne_zero, cof_ne_zero, ← pos_iff_ne_zero]
    exact (zero_le (f b)).trans_lt (hf.strictMono (lt_succ b))
  · rw [hf.cof_eq ha]
```

### `Ordinal.cof_preOmega` (theorem, modified) [8bed5166ae]
- file: `Mathlib/SetTheory/Cardinal/Cofinality.lean`; changed: proof:modified
- before the PR:
```lean
@[simp]
theorem cof_preOmega {o : Ordinal} (ho : IsSuccPrelimit o) : (preOmega o).cof = o.cof := by
  by_cases h : IsMin o
  · simp [h.eq_bot]
  · exact isNormal_preOmega.cof_eq ⟨h, ho⟩
```
- as the PR leaves it:
```lean
@[simp]
theorem cof_preOmega {o : Ordinal} (ho : IsSuccPrelimit o) : (preOmega o).cof = o.cof := by
  by_cases h : IsMin o
  · simp [h.eq_bot]
  · exact cof_eq_of_isNormal isNormal_preOmega ⟨h, ho⟩
```

### `Ordinal.IsNormal.cof_eq` (theorem, removed) [b14caae1c6]
- file: `Mathlib/SetTheory/Cardinal/Cofinality.lean`; changed: name:removed, proof:removed, statement_or_type:removed
- before the PR:
```lean
theorem IsNormal.cof_eq {f} (hf : IsNormal f) {a} (ha : IsSuccLimit a) : cof (f a) = cof a :=
  let ⟨_, hg⟩ := exists_fundamental_sequence a
  ord_injective (hf.isFundamentalSequence ha hg).cof_eq
```

### `Ordinal.cof_omega` (theorem, modified) [d4a344228c]
- file: `Mathlib/SetTheory/Cardinal/Cofinality.lean`; changed: proof:modified
- before the PR:
```lean
@[simp]
theorem cof_omega {o : Ordinal} (ho : IsSuccLimit o) : (ω_ o).cof = o.cof :=
  isNormal_omega.cof_eq ho
```
- as the PR leaves it:
```lean
@[simp]
theorem cof_omega {o : Ordinal} (ho : IsSuccLimit o) : (ω_ o).cof = o.cof :=
  cof_eq_of_isNormal isNormal_omega ho
```

### `Ordinal.cof_le_of_isNormal` (theorem, modified) [fd2ab4d121]
- file: `Mathlib/SetTheory/Cardinal/Cofinality.lean`; changed: name:modified, proof:modified
- before the PR:
```lean
theorem IsNormal.cof_le {f} (hf : IsNormal f) (a) : cof a ≤ cof (f a) := by
  rcases zero_or_succ_or_isSuccLimit a with (rfl | ⟨b, rfl⟩ | ha)
  · rw [cof_zero]
    exact zero_le _
  · rw [cof_succ, Cardinal.one_le_iff_ne_zero, cof_ne_zero, ← pos_iff_ne_zero]
    exact (zero_le (f b)).trans_lt (hf.strictMono (lt_succ b))
  · rw [hf.cof_eq ha]
```
- as the PR leaves it:
```lean
theorem cof_le_of_isNormal {f} (hf : IsNormal f) (a) : cof a ≤ cof (f a) := by
  rcases zero_or_succ_or_isSuccLimit a with (rfl | ⟨b, rfl⟩ | ha)
  · rw [cof_zero]
    exact zero_le _
  · rw [cof_succ, Cardinal.one_le_iff_ne_zero, cof_ne_zero, ← pos_iff_ne_zero]
    exact (zero_le (f b)).trans_lt (hf.strictMono (lt_succ b))
  · rw [cof_eq_of_isNormal hf ha]
```

### `Ordinal.isNormal_iff_strictMono_limit` (theorem, modified) [003b997333]
- file: `Mathlib/SetTheory/Ordinal/Arithmetic.lean`; changed: attributes:added, statement_or_type:modified
- before the PR:
```lean
theorem isNormal_iff_strictMono_limit (f : Ordinal → Ordinal) :
    IsNormal f ↔ StrictMono f ∧ ∀ o, IsSuccLimit o → ∀ a, (∀ b < o, f b ≤ a) → f o ≤ a :=
  isNormal_iff
```
- as the PR leaves it:
```lean
@[deprecated isNormal_iff (since := "2025-12-25")]
theorem isNormal_iff_strictMono_limit (f : Ordinal → Ordinal) :
    Ordinal.IsNormal f ↔ StrictMono f ∧ ∀ o, IsSuccLimit o → ∀ a, (∀ b < o, f b ≤ a) → f o ≤ a :=
  isNormal_iff
```

### `Ordinal.IsNormal.inj` (theorem, modified) [00a06eef55]
- file: `Mathlib/SetTheory/Ordinal/Arithmetic.lean`; changed: attributes:added, proof:modified, statement_or_type:modified
- before the PR:
```lean
theorem IsNormal.inj {f} (H : IsNormal f) {a b} : f a = f b ↔ a = b := by
  simp only [le_antisymm_iff, H.le_iff]
```
- as the PR leaves it:
```lean
@[deprecated Injective.eq_iff (since := "2025-12-25")]
theorem IsNormal.inj {f} (H : Ordinal.IsNormal f) {a b} : f a = f b ↔ a = b :=
  H.strictMono.injective.eq_iff
```

### `command in Arithmetic.lean` (command, added) [046a33bc7a]
- file: `Mathlib/SetTheory/Ordinal/Arithmetic.lean`; changed: value_or_body:modified
- as the PR leaves it:
```lean
set_option linter.deprecated false in
```

### `Ordinal.IsNormal.le_iff` (theorem, modified) [171af0faaa]
- file: `Mathlib/SetTheory/Ordinal/Arithmetic.lean`; changed: attributes:added, proof:modified, statement_or_type:modified
- before the PR:
```lean
theorem IsNormal.le_iff {f} (H : IsNormal f) {a b} : f a ≤ f b ↔ a ≤ b :=
  le_iff_le_iff_lt_iff_lt.2 H.lt_iff
```
- as the PR leaves it:
```lean
@[deprecated StrictMono.le_iff_le (since := "2025-12-25")]
theorem IsNormal.le_iff {f} (H : Ordinal.IsNormal f) {a b} : f a ≤ f b ↔ a ≤ b :=
  H.strictMono.le_iff_le
```

### `Ordinal.IsNormal.isSuccLimit` (theorem, modified) [205fcf2985]
- file: `Mathlib/SetTheory/Ordinal/Arithmetic.lean`; changed: attributes:added, statement_or_type:modified
- before the PR:
```lean
theorem IsNormal.isSuccLimit {f} (H : IsNormal f) {o} (ho : IsSuccLimit o) : IsSuccLimit (f o) :=
  H.map_isSuccLimit ho
```
- as the PR leaves it:
```lean
@[deprecated IsNormal.map_isSuccLimit (since := "2025-12-25")]
theorem IsNormal.isSuccLimit {f} (H : Ordinal.IsNormal f) {o} (ho : IsSuccLimit o) :
    IsSuccLimit (f o) :=
  H.map_isSuccLimit ho
```

### `module_doc in Arithmetic.lean` (module_doc, removed) [2ba5abbe29]
- file: `Mathlib/SetTheory/Ordinal/Arithmetic.lean`; changed: documentation:removed
- before the PR:
```lean
/-! ### Normal ordinal functions -/
```

### `Ordinal.IsNormal.refl` (theorem, modified) [3ac3d43849]
- file: `Mathlib/SetTheory/Ordinal/Arithmetic.lean`; changed: attributes:added, statement_or_type:modified
- before the PR:
```lean
theorem IsNormal.refl : IsNormal id :=
  .id
```
- as the PR leaves it:
```lean
@[deprecated IsNormal.id (since := "2025-12-25")]
theorem IsNormal.refl : Ordinal.IsNormal id :=
  .id
```

### `Ordinal.IsNormal.lt_iff` (theorem, modified) [3dd2fec92d]
- file: `Mathlib/SetTheory/Ordinal/Arithmetic.lean`; changed: attributes:added, proof:modified, statement_or_type:modified
- before the PR:
```lean
theorem IsNormal.lt_iff {f} (H : IsNormal f) {a b} : f a < f b ↔ a < b :=
  StrictMono.lt_iff_lt <| H.strictMono
```
- as the PR leaves it:
```lean
@[deprecated StrictMono.lt_iff_lt (since := "2025-12-25")]
theorem IsNormal.lt_iff {f} (H : Ordinal.IsNormal f) {a b} : f a < f b ↔ a < b :=
  H.strictMono.lt_iff_lt
```

### `module_doc in Arithmetic.lean` (module_doc, modified) [3f44cf4a93]
- file: `Mathlib/SetTheory/Ordinal/Arithmetic.lean`; changed: documentation:modified
- before the PR:
```lean
/-!
# Ordinal arithmetic

Ordinals have an addition (corresponding to disjoint union) that turns them into an additive
monoid, and a multiplication (corresponding to the lexicographic order on the product) that turns
them into a monoid. One can also define correspondingly a subtraction, a division, a successor
function, a power function and a logarithm function.

We also define limit ordinals and prove the basic induction principle on ordinals separating
successor ordinals and limit ordinals, in `limitRecOn`.

## Main definitions and results

* `o₁ + o₂` is the order on the disjoint union of `o₁` and `o₂` obtained by declaring that
  every element of `o₁` is smaller than every element of `o₂`.
* `o₁ - o₂` is the unique ordinal `o` such that `o₂ + o = o₁`, when `o₂ ≤ o₁`.
* `o₁ * o₂` is the lexicographic order on `o₂ × o₁`.
* `o₁ / o₂` is the ordinal `o` such that `o₁ = o₂ * o + o'` with `o' < o₂`. We also define the
  divisibility predicate, and a modulo operation.
* `Order.succ o = o + 1` is the successor of `o`.
* `pred o` if the predecessor of `o`. If `o` is not a successor, we set `pred o = o`.

We discuss the properties of casts of natural numbers of and of `ω` with respect to these
operations.

Some properties of the operations are also used to discuss general tools on ordinals:

* `Order.IsSuccLimit o`: an ordinal is a limit ordinal if it is neither `0` nor a successor.
* `limitRecOn` is the main induction principle of ordinals: if one can prove a property by
  induction at successor ordinals and at limit ordinals, then it holds for all ordinals.
* `IsNormal`: a function `f : Ordinal → Ordinal` satisfies `IsNormal` if it is strictly increasing
  and order-continuous, i.e., the image `f o` of a limit ordinal `o` is the sup of `f a` for
  `a < o`.

Various other basic arithmetic results are given in `Principal.lean` instead.
-/
```
- as the PR leaves it:
```lean
/-!
# Ordinal arithmetic

Ordinals have an addition (corresponding to disjoint union) that turns them into an additive
monoid, and a multiplication (corresponding to the lexicographic order on the product) that turns
them into a monoid. One can also define correspondingly a subtraction, a division, a successor
function, a power function and a logarithm function.

We also define limit ordinals and prove the basic induction principle on ordinals separating
successor ordinals and limit ordinals, in `limitRecOn`.

## Main definitions and results

* `o₁ + o₂` is the order on the disjoint union of `o₁` and `o₂` obtained by declaring that
  every element of `o₁` is smaller than every element of `o₂`.
* `o₁ - o₂` is the unique ordinal `o` such that `o₂ + o = o₁`, when `o₂ ≤ o₁`.
* `o₁ * o₂` is the lexicographic order on `o₂ × o₁`.
* `o₁ / o₂` is the ordinal `o` such that `o₁ = o₂ * o + o'` with `o' < o₂`. We also define the
  divisibility predicate, and a modulo operation.
* `limitRecOn` is the main induction principle of ordinals: if one can prove a property by
  induction at successor ordinals and at limit ordinals, then it holds for all ordinals.

We discuss the properties of casts of natural numbers of and of `ω` with respect to these
operations.

Note that some basic functions and properties of ordinals have been generalized to other orders:

* `Order.succ o = o + 1` is the successor of `o`.
* `Order.IsSuccLimit o`: an ordinal is a limit ordinal if it is neither `0` nor a successor.
* `Order.IsNormal`: a function `f : Ordinal → Ordinal` is normal if it is strictly increasing and
  order-continuous, i.e., the image `f o` of a limit ordinal `o` is the supremum of `f a`
  for `a < o`.

Various other basic arithmetic results are given in `Principal.lean` instead.
-/
```

### `Ordinal.IsNormal.monotone` (theorem, modified) [40c2988647]
- file: `Mathlib/SetTheory/Ordinal/Arithmetic.lean`; changed: attributes:added, statement_or_type:modified
- before the PR:
```lean
theorem IsNormal.monotone {f} (H : IsNormal f) : Monotone f :=
  H.strictMono.monotone
```
- as the PR leaves it:
```lean
@[deprecated Order.IsNormal.strictMono (since := "2025-12-25")]
theorem IsNormal.monotone {f} (H : Ordinal.IsNormal f) : Monotone f :=
  H.strictMono.monotone
```

### `Ordinal.IsNormal.le_set'` (theorem, modified) [4334000b7b]
- file: `Mathlib/SetTheory/Ordinal/Arithmetic.lean`; changed: attributes:added, statement_or_type:modified
- before the PR:
```lean
theorem IsNormal.le_set' {f o} (H : IsNormal f) (p : Set α) (p0 : p.Nonempty) (g : α → Ordinal) (b)
    (H₂ : ∀ o, b ≤ o ↔ ∀ a ∈ p, g a ≤ o) : f b ≤ o ↔ ∀ a ∈ p, f (g a) ≤ o := by
  simpa [H₂] using H.le_set (g '' p) (p0.image g) b
```
- as the PR leaves it:
```lean
@[deprecated IsNormal.map_isLUB (since := "2025-12-25")]
theorem IsNormal.le_set' {f o} (H : Ordinal.IsNormal f) (p : Set α) (p0 : p.Nonempty)
    (g : α → Ordinal) (b) (H₂ : ∀ o, b ≤ o ↔ ∀ a ∈ p, g a ≤ o) :
    f b ≤ o ↔ ∀ a ∈ p, f (g a) ≤ o := by
  simpa [H₂] using H.le_set (g '' p) (p0.image g) b
```

### `Ordinal.IsNormal.le_set` (theorem, modified) [52e5b89398]
- file: `Mathlib/SetTheory/Ordinal/Arithmetic.lean`; changed: attributes:added, proof:modified, statement_or_type:modified
- before the PR:
```lean
theorem IsNormal.le_set {f o} (H : IsNormal f) (p : Set Ordinal) (p0 : p.Nonempty) (b)
    (H₂ : ∀ o, b ≤ o ↔ ∀ a ∈ p, a ≤ o) : f b ≤ o ↔ ∀ a ∈ p, f a ≤ o :=
  ⟨fun h _ pa => (H.le_iff.2 ((H₂ _).1 le_rfl _ pa)).trans h, fun h => by
    induction b using limitRecOn with
    | zero =>
      obtain ⟨x, px⟩ := p0
      rw [nonpos_iff_eq_zero.1 ((H₂ _).1 (zero_le _) _ px)] at px
      exact h _ px
    | succ S _ =>
      rcases not_forall₂.1 (mt (H₂ S).2 <| (lt_succ S).not_ge) with ⟨a, h₁, h₂⟩
      exact (H.le_iff.2 <| succ_le_of_lt <| not_le.1 h₂).trans (h _ h₁)
    | limit S L _ =>
      refine (H.le_iff_forall_le L).2 fun a h' => ?_
      rcases not_forall₂.1 (mt (H₂ a).2 h'.not_ge) with ⟨b, h₁, h₂⟩
      exact (H.le_iff.2 <| (not_le.1 h₂).le).trans (h _ h₁)⟩
```
- as the PR leaves it:
```lean
@[deprecated IsNormal.map_isLUB (since := "2025-12-25")]
theorem IsNormal.le_set {f o} (H : Ordinal.IsNormal f) (p : Set Ordinal) (p0 : p.Nonempty) (b)
    (H₂ : ∀ o, b ≤ o ↔ ∀ a ∈ p, a ≤ o) : f b ≤ o ↔ ∀ a ∈ p, f a ≤ o := by
  have hp := H.map_isLUB ⟨(H₂ b).1 le_rfl, fun a ↦ (H₂ _).2⟩ p0
  refine ⟨fun hb a ha ↦ (hp.1 (mem_image_of_mem _ ha)).trans hb, fun H ↦ hp.2 ?_⟩
  simpa [mem_upperBounds]
```

### `Ordinal.isNormal_mul_right` (theorem, modified) [6d008fff98]
- file: `Mathlib/SetTheory/Ordinal/Arithmetic.lean`; changed: proof:modified
- before the PR:
```lean
theorem isNormal_mul_right {a : Ordinal} (h : 0 < a) : IsNormal (a * ·) := by
  refine IsNormal.of_succ_lt (fun b ↦ ?_) fun hb ↦ ?_
  · simpa [mul_succ] using (add_lt_add_iff_left (a * b)).2 h
  · simpa [IsLUB, IsLeast, upperBounds, lowerBounds, mul_le_iff_of_isSuccLimit hb] using
      fun c hc ↦ mul_le_mul_right hc.le a
```
- as the PR leaves it:
```lean
theorem isNormal_mul_right {a : Ordinal} (h : 0 < a) : IsNormal (a * ·) := by
  refine .of_succ_lt (fun b ↦ ?_) fun hb ↦ ?_
  · simpa [mul_succ] using (add_lt_add_iff_left (a * b)).2 h
  · simpa [IsLUB, IsLeast, upperBounds, lowerBounds, mul_le_iff_of_isSuccLimit hb] using
      fun c hc ↦ mul_le_mul_right hc.le a
```

### `Ordinal.IsNormal.le_iff_eq` (theorem, modified) [8553f07c08]
- file: `Mathlib/SetTheory/Ordinal/Arithmetic.lean`; changed: attributes:added, statement_or_type:modified
- before the PR:
```lean
theorem IsNormal.le_iff_eq {f} (H : IsNormal f) {a} : f a ≤ a ↔ f a = a :=
  H.le_apply.ge_iff_eq'
```
- as the PR leaves it:
```lean
@[deprecated StrictMono.le_apply (since := "2025-12-25")]
theorem IsNormal.le_iff_eq {f} (H : Ordinal.IsNormal f) {a} : f a ≤ a ↔ f a = a :=
  H.le_apply.ge_iff_eq'
```

### `Ordinal.isSuccLimit_add` (theorem, modified) [ac40195131]
- file: `Mathlib/SetTheory/Ordinal/Arithmetic.lean`; changed: proof:modified
- before the PR:
```lean
theorem isSuccLimit_add (a : Ordinal) {b : Ordinal} : IsSuccLimit b → IsSuccLimit (a + b) :=
  (isNormal_add_right a).isSuccLimit
```
- as the PR leaves it:
```lean
theorem isSuccLimit_add (a : Ordinal) {b : Ordinal} : IsSuccLimit b → IsSuccLimit (a + b) :=
  (isNormal_add_right a).map_isSuccLimit
```

### `Ordinal.IsNormal` (def, modified) [b684301d44]
- file: `Mathlib/SetTheory/Ordinal/Arithmetic.lean`; changed: attributes:added
- before the PR:
```lean
def IsNormal (f : Ordinal → Ordinal) : Prop :=
  Order.IsNormal f
```
- as the PR leaves it:
```lean
@[deprecated Order.IsNormal (since := "2025-12-25")]
protected def IsNormal (f : Ordinal → Ordinal) : Prop :=
  Order.IsNormal f
```

### `Ordinal.IsNormal.strictMono` (theorem, modified) [b91203552d]
- file: `Mathlib/SetTheory/Ordinal/Arithmetic.lean`; changed: attributes:added, statement_or_type:modified
- before the PR:
```lean
theorem IsNormal.strictMono {f} (H : IsNormal f) : StrictMono f :=
  Order.IsNormal.strictMono H
```
- as the PR leaves it:
```lean
@[deprecated Order.IsNormal.strictMono (since := "2025-12-25")]
theorem IsNormal.strictMono {f} (H : Ordinal.IsNormal f) : StrictMono f :=
  Order.IsNormal.strictMono H
```

### `Ordinal.IsNormal.limit_lt` (theorem, modified) [bdca67b418]
- file: `Mathlib/SetTheory/Ordinal/Arithmetic.lean`; changed: attributes:added, statement_or_type:modified
- before the PR:
```lean
theorem IsNormal.limit_lt {f} (H : IsNormal f) {o} (h : IsSuccLimit o) {a} :
    a < f o ↔ ∃ b < o, a < f b :=
  H.lt_iff_exists_lt h
```
- as the PR leaves it:
```lean
@[deprecated IsNormal.lt_iff_exists_lt (since := "2025-12-25")]
theorem IsNormal.limit_lt {f} (H : Ordinal.IsNormal f) {o} (h : IsSuccLimit o) {a} :
    a < f o ↔ ∃ b < o, a < f b :=
  H.lt_iff_exists_lt h
```

### `Ordinal.isNormal_add_right` (theorem, modified) [cb68c2334b]
- file: `Mathlib/SetTheory/Ordinal/Arithmetic.lean`; changed: proof:modified
- before the PR:
```lean
theorem isNormal_add_right (a : Ordinal) : IsNormal (a + ·) := by
  rw [isNormal_iff_strictMono_limit]
  exact ⟨add_right_strictMono, fun _ l _ ↦ (add_le_iff_of_isSuccLimit l).2⟩
```
- as the PR leaves it:
```lean
theorem isNormal_add_right (a : Ordinal) : IsNormal (a + ·) := by
  rw [isNormal_iff]
  exact ⟨add_right_strictMono, fun _ l _ ↦ (add_le_iff_of_isSuccLimit l).2⟩
```

### `Ordinal.IsNormal.le_apply` (theorem, modified) [e40d07e7b0]
- file: `Mathlib/SetTheory/Ordinal/Arithmetic.lean`; changed: attributes:added, statement_or_type:modified
- before the PR:
```lean
theorem IsNormal.le_apply {f} (H : IsNormal f) {a} : a ≤ f a :=
  H.strictMono.le_apply
```
- as the PR leaves it:
```lean
@[deprecated StrictMono.le_apply (since := "2025-12-25")]
theorem IsNormal.le_apply {f} (H : Ordinal.IsNormal f) {a} : a ≤ f a :=
  H.strictMono.le_apply
```

### `Ordinal.IsNormal.limit_le` (theorem, modified) [e5d9d94e35]
- file: `Mathlib/SetTheory/Ordinal/Arithmetic.lean`; changed: attributes:added, statement_or_type:modified
- before the PR:
```lean
theorem IsNormal.limit_le {f} (H : IsNormal f) :
    ∀ {o}, IsSuccLimit o → ∀ {a}, f o ≤ a ↔ ∀ b < o, f b ≤ a :=
  H.le_iff_forall_le
```
- as the PR leaves it:
```lean
@[deprecated IsNormal.le_iff_forall_le (since := "2025-12-25")]
theorem IsNormal.limit_le {f} (H : Ordinal.IsNormal f) :
    ∀ {o}, IsSuccLimit o → ∀ {a}, f o ≤ a ↔ ∀ b < o, f b ≤ a :=
  H.le_iff_forall_le
```

### `command in Arithmetic.lean` (command, modified) [e60a0ed0bf]
- file: `Mathlib/SetTheory/Ordinal/Arithmetic.lean`; changed: value_or_body:modified
- before the PR:
```lean
/-- A normal ordinal function is a strictly increasing function which is
  order-continuous, i.e., the image `f o` of a limit ordinal `o` is the sup of `f a` for
  `a < o`.

  Todo: deprecate this in favor of `Order.IsNormal`. -/
```
- as the PR leaves it:
```lean
/-- A normal ordinal function is a strictly increasing function which is
  order-continuous, i.e., the image `f o` of a limit ordinal `o` is the sup of `f a` for
  `a < o`. -/
```

### `Ordinal.IsNormal.trans` (theorem, modified) [e845f739fb]
- file: `Mathlib/SetTheory/Ordinal/Arithmetic.lean`; changed: attributes:added, statement_or_type:modified
- before the PR:
```lean
theorem IsNormal.trans {f g} (H₁ : IsNormal f) (H₂ : IsNormal g) : IsNormal (f ∘ g) :=
  H₁.comp H₂
```
- as the PR leaves it:
```lean
@[deprecated IsNormal.comp (since := "2025-12-25")]
theorem IsNormal.trans {f g} (H₁ : Ordinal.IsNormal f) (H₂ : Ordinal.IsNormal g) :
    IsNormal (f ∘ g) :=
  H₁.comp H₂
```

### `Ordinal.isSuccLimit_mul` (theorem, modified) [f11ed4cf01]
- file: `Mathlib/SetTheory/Ordinal/Arithmetic.lean`; changed: proof:modified
- before the PR:
```lean
theorem isSuccLimit_mul {a b : Ordinal} (a0 : 0 < a) : IsSuccLimit b → IsSuccLimit (a * b) :=
  (isNormal_mul_right a0).isSuccLimit
```
- as the PR leaves it:
```lean
theorem isSuccLimit_mul {a b : Ordinal} (a0 : 0 < a) : IsSuccLimit b → IsSuccLimit (a * b) :=
  (isNormal_mul_right a0).map_isSuccLimit
```

### `Ordinal.IsNormal.id_le` (theorem, modified) [f8dc0d069b]
- file: `Mathlib/SetTheory/Ordinal/Arithmetic.lean`; changed: attributes:added, statement_or_type:modified
- before the PR:
```lean
theorem IsNormal.id_le {f} (H : IsNormal f) : id ≤ f :=
  H.strictMono.id_le
```
- as the PR leaves it:
```lean
@[deprecated StrictMono.id_le (since := "2025-12-25")]
theorem IsNormal.id_le {f} (H : Ordinal.IsNormal f) : id ≤ f :=
  H.strictMono.id_le
```

### `Ordinal.isNormal_enumOrd` (theorem, modified) [ca0de94b37]
- file: `Mathlib/SetTheory/Ordinal/Enum.lean`; changed: proof:modified
- before the PR:
```lean
theorem isNormal_enumOrd (H : ∀ t ⊆ s, t.Nonempty → BddAbove t → sSup t ∈ s) (hs : ¬ BddAbove s) :
    IsNormal (enumOrd s) := by
  refine (isNormal_iff_strictMono_limit _).2 ⟨enumOrd_strictMono hs, fun o ho a ha ↦ ?_⟩
  trans ⨆ b : Iio o, enumOrd s b
  · refine enumOrd_le_of_forall_lt ?_ (fun b hb ↦ (enumOrd_strictMono hs (lt_succ b)).trans_le ?_)
    · have : Nonempty (Iio o) := ⟨0, ho.bot_lt⟩
      apply H _ _ (range_nonempty _) (bddAbove_of_small _)
      rintro _ ⟨c, rfl⟩
      exact enumOrd_mem hs c
    · exact Ordinal.le_iSup _ (⟨_, ho.succ_lt hb⟩ : Iio o)
  · exact Ordinal.iSup_le fun x ↦ ha _ x.2
```
- as the PR leaves it:
```lean
theorem isNormal_enumOrd (H : ∀ t ⊆ s, t.Nonempty → BddAbove t → sSup t ∈ s) (hs : ¬ BddAbove s) :
    IsNormal (enumOrd s) := by
  refine isNormal_iff.2 ⟨enumOrd_strictMono hs, fun o ho a ha ↦ ?_⟩
  trans ⨆ b : Iio o, enumOrd s b
  · refine enumOrd_le_of_forall_lt ?_ (fun b hb ↦ (enumOrd_strictMono hs (lt_succ b)).trans_le ?_)
    · have : Nonempty (Iio o) := ⟨0, ho.bot_lt⟩
      apply H _ _ (range_nonempty _) (bddAbove_of_small _)
      rintro _ ⟨c, rfl⟩
      exact enumOrd_mem hs c
    · exact Ordinal.le_iSup _ (⟨_, ho.succ_lt hb⟩ : Iio o)
  · exact Ordinal.iSup_le fun x ↦ ha _ x.2
```

### `Ordinal.isNormal_opow` (theorem, modified) [2bc280e377]
- file: `Mathlib/SetTheory/Ordinal/Exponential.lean`; changed: statement_or_type:modified
- before the PR:
```lean
theorem isNormal_opow {a : Ordinal} (h : 1 < a) : IsNormal (a ^ ·) := by
  have ha : 0 < a := zero_lt_one.trans h
  refine IsNormal.of_succ_lt ?_ fun hl ↦ ?_
  · simpa only [mul_one, opow_succ] using fun b ↦ mul_lt_mul_of_pos_left h (opow_pos b ha)
  · simp [IsLUB, IsLeast, upperBounds, lowerBounds, ← opow_le_of_isSuccLimit ha.ne' hl]
```
- as the PR leaves it:
```lean
theorem isNormal_opow {a : Ordinal} (h : 1 < a) : IsNormal (a ^ · : Ordinal → Ordinal) := by
  have ha : 0 < a := zero_lt_one.trans h
  refine IsNormal.of_succ_lt ?_ fun hl ↦ ?_
  · simpa only [mul_one, opow_succ] using fun b ↦ mul_lt_mul_of_pos_left h (opow_pos b ha)
  · simp [IsLUB, IsLeast, upperBounds, lowerBounds, ← opow_le_of_isSuccLimit ha.ne' hl]
```

### `Ordinal.opow_lt_opow_iff_right` (theorem, modified) [3e4311eb44]
- file: `Mathlib/SetTheory/Ordinal/Exponential.lean`; changed: proof:modified
- before the PR:
```lean
@[simp]
theorem opow_lt_opow_iff_right {a b c : Ordinal} (a1 : 1 < a) : a ^ b < a ^ c ↔ b < c :=
  (isNormal_opow a1).lt_iff
```
- as the PR leaves it:
```lean
@[simp]
theorem opow_lt_opow_iff_right {a b c : Ordinal} (a1 : 1 < a) : a ^ b < a ^ c ↔ b < c :=
  (isNormal_opow a1).strictMono.lt_iff_lt
```

### `Ordinal.right_le_opow` (theorem, modified) [3e9f07cd44]
- file: `Mathlib/SetTheory/Ordinal/Exponential.lean`; changed: proof:modified
- before the PR:
```lean
theorem right_le_opow {a : Ordinal} (b : Ordinal) (a1 : 1 < a) : b ≤ a ^ b :=
  (isNormal_opow a1).le_apply
```
- as the PR leaves it:
```lean
theorem right_le_opow {a : Ordinal} (b : Ordinal) (a1 : 1 < a) : b ≤ a ^ b :=
  (isNormal_opow a1).strictMono.le_apply
```

### `Ordinal.opow_right_inj` (theorem, modified) [3fe7b89682]
- file: `Mathlib/SetTheory/Ordinal/Exponential.lean`; changed: proof:modified
- before the PR:
```lean
@[simp]
theorem opow_right_inj {a b c : Ordinal} (a1 : 1 < a) : a ^ b = a ^ c ↔ b = c :=
  (isNormal_opow a1).inj
```
- as the PR leaves it:
```lean
@[simp]
theorem opow_right_inj {a b c : Ordinal} (a1 : 1 < a) : a ^ b = a ^ c ↔ b = c :=
  (isNormal_opow a1).strictMono.injective.eq_iff
```

### `Ordinal.opow_add` (theorem, modified) [48f033a4ab]
- file: `Mathlib/SetTheory/Ordinal/Exponential.lean`; changed: proof:modified
- before the PR:
```lean
theorem opow_add (a b c : Ordinal) : a ^ (b + c) = a ^ b * a ^ c := by
  rcases eq_or_ne a 0 with (rfl | a0)
  · rcases eq_or_ne c 0 with (rfl | c0)
    · simp
    have : b + c ≠ 0 := ((pos_iff_ne_zero.2 c0).trans_le le_add_self).ne'
    simp only [zero_opow c0, zero_opow this, mul_zero]
  rcases eq_or_lt_of_le (one_le_iff_ne_zero.2 a0) with (rfl | a1)
  · simp only [one_opow, mul_one]
  induction c using limitRecOn with
  | zero => simp
  | succ c IH =>
    rw [add_succ, opow_succ, IH, opow_succ, mul_assoc]
  | limit c l IH =>
    refine
      eq_of_forall_ge_iff fun d =>
        (((isNormal_opow a1).trans (isNormal_add_right b)).limit_le l).trans ?_
    dsimp only [Function.comp_def]
    simp +contextual only [IH]
    exact
      (((isNormal_mul_right <| opow_pos b (pos_iff_ne_zero.2 a0)).trans
              (isNormal_opow a1)).limit_le
          l).symm
```
- as the PR leaves it:
```lean
theorem opow_add (a b c : Ordinal) : a ^ (b + c) = a ^ b * a ^ c := by
  obtain rfl | ha := eq_zero_or_pos a
  · obtain rfl | hc := eq_zero_or_pos c; · simp
    have : b + c ≠ 0 := (hc.trans_le le_add_self).ne'
    rw [zero_opow hc.ne', zero_opow, mul_zero]
    exact (hc.trans_le le_add_self).ne'
  obtain rfl | ha' := (one_le_iff_ne_zero.2 ha.ne').eq_or_lt; · simp
  induction c using limitRecOn with
  | zero => simp
  | succ c IH => rw [add_succ, opow_succ, IH, opow_succ, mul_assoc]
  | limit c l IH =>
    refine eq_of_forall_ge_iff fun d ↦
      (((isNormal_opow ha').comp (isNormal_add_right b)).le_iff_forall_le l).trans ?_
    simpa +contextual [IH] using
      (((isNormal_mul_right <| opow_pos b (pos_iff_ne_zero.2 ha.ne')).comp
        (isNormal_opow ha')).le_iff_forall_le l).symm
```

### `Ordinal.isSuccLimit_opow` (theorem, modified) [55d5fc12ed]
- file: `Mathlib/SetTheory/Ordinal/Exponential.lean`; changed: proof:modified
- before the PR:
```lean
theorem isSuccLimit_opow {a b : Ordinal} (a1 : 1 < a) : IsSuccLimit b → IsSuccLimit (a ^ b) :=
  (isNormal_opow a1).isSuccLimit
```
- as the PR leaves it:
```lean
theorem isSuccLimit_opow {a b : Ordinal} (a1 : 1 < a) : IsSuccLimit b → IsSuccLimit (a ^ b) :=
  (isNormal_opow a1).map_isSuccLimit
```

### `Ordinal.iSup_pow_natCast` (theorem, modified) [6276a8bba0]
- file: `Mathlib/SetTheory/Ordinal/Exponential.lean`; changed: name:modified, proof:modified
- before the PR:
```lean
theorem iSup_pow {o : Ordinal} (ho : 0 < o) : ⨆ n : ℕ, o ^ n = o ^ ω := by
  simp_rw [← opow_natCast]
  rcases (one_le_iff_pos.2 ho).lt_or_eq with ho₁ | rfl
  · exact (isNormal_opow ho₁).apply_omega0
  · rw [one_opow]
    refine le_antisymm (Ordinal.iSup_le fun n => by rw [one_opow]) ?_
    exact_mod_cast Ordinal.le_iSup _ 0
```
- as the PR leaves it:
```lean
theorem iSup_pow_natCast {o : Ordinal} (ho : 0 < o) : ⨆ n : ℕ, o ^ n = o ^ ω := by
  simp_rw [← opow_natCast]
  rcases (one_le_iff_pos.2 ho).lt_or_eq with ho₁ | rfl
  · exact apply_omega0_of_isNormal (isNormal_opow ho₁)
  · rw [one_opow]
    refine le_antisymm (Ordinal.iSup_le fun n => by rw [one_opow]) ?_
    exact_mod_cast Ordinal.le_iSup _ 0
```

### `command in Exponential.lean` (command, added) [8ce9acdbf7]
- file: `Mathlib/SetTheory/Ordinal/Exponential.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
@[deprecated (since := "2025-12-25")]
alias iSup_pow := iSup_pow_natCast
```

### `Ordinal.opow_mul` (theorem, modified) [afdbe1aab7]
- file: `Mathlib/SetTheory/Ordinal/Exponential.lean`; changed: proof:modified
- before the PR:
```lean
theorem opow_mul (a b c : Ordinal) : a ^ (b * c) = (a ^ b) ^ c := by
  by_cases b0 : b = 0; · simp only [b0, zero_mul, opow_zero, one_opow]
  by_cases a0 : a = 0
  · subst a
    by_cases c0 : c = 0
    · simp only [c0, mul_zero, opow_zero]
    simp only [zero_opow b0, zero_opow c0, zero_opow (mul_ne_zero b0 c0)]
  rcases eq_or_lt_of_le (one_le_iff_ne_zero.2 a0) with a1 | a1
  · subst a1
    simp only [one_opow]
  induction c using limitRecOn with
  | zero => simp only [mul_zero, opow_zero]
  | succ c IH =>
    rw [mul_succ, opow_add, IH, opow_succ]
  | limit c l IH =>
    refine
      eq_of_forall_ge_iff fun d =>
        (((isNormal_opow a1).trans (isNormal_mul_right (pos_iff_ne_zero.2 b0))).limit_le
              l).trans
          ?_
    dsimp only [Function.comp_def]
    simp +contextual only [IH]
    exact (opow_le_of_isSuccLimit (opow_ne_zero _ a0) l).symm
```
- as the PR leaves it:
```lean
theorem opow_mul (a b c : Ordinal) : a ^ (b * c) = (a ^ b) ^ c := by
  obtain rfl | hb := eq_zero_or_pos b; · simp
  obtain rfl | ha := eq_or_ne a 0
  · have := hb.ne'
    by_cases c = 0 <;> simp_all
  obtain rfl | ha' := (one_le_iff_ne_zero.2 ha).eq_or_lt; · simp
  induction c using limitRecOn with
  | zero => simp
  | succ c IH => rw [mul_succ, opow_add, IH, opow_succ]
  | limit c l IH =>
    refine eq_of_forall_ge_iff fun d ↦
      (((isNormal_opow ha').comp (isNormal_mul_right hb)).le_iff_forall_le l).trans ?_
    simpa +contextual [IH] using (opow_le_of_isSuccLimit (opow_ne_zero _ ha) l).symm
```

### `Ordinal.opow_le_opow_iff_right` (theorem, modified) [d72bc7e798]
- file: `Mathlib/SetTheory/Ordinal/Exponential.lean`; changed: proof:modified
- before the PR:
```lean
@[simp]
theorem opow_le_opow_iff_right {a b c : Ordinal} (a1 : 1 < a) : a ^ b ≤ a ^ c ↔ b ≤ c :=
  (isNormal_opow a1).le_iff
```
- as the PR leaves it:
```lean
@[simp]
theorem opow_le_opow_iff_right {a b c : Ordinal} (a1 : 1 < a) : a ^ b ≤ a ^ c ↔ b ≤ c :=
  (isNormal_opow a1).strictMono.le_iff_le
```

### `module_doc in Exponential.lean` (module_doc, modified) [f9e7681c7a]
- file: `Mathlib/SetTheory/Ordinal/Exponential.lean`; changed: documentation:modified
- before the PR:
```lean
/-! # Ordinal exponential

In this file we define the power function and the logarithm function on ordinals. The two are
related by the lemma `Ordinal.opow_le_iff_le_log : b ^ c ≤ x ↔ c ≤ log b x` for nontrivial inputs
`b`, `c`.
-/
```
- as the PR leaves it:
```lean
/-!
# Ordinal exponential

In this file we define the power function and the logarithm function on ordinals. The two are
related by the lemma `Ordinal.opow_le_iff_le_log : b ^ c ≤ x ↔ c ≤ log b x` for nontrivial inputs
`b`, `c`.
-/
```

### `Ordinal.IsNormal.map_sSup_of_bddAbove` (theorem, modified) [28f09e6294]
- file: `Mathlib/SetTheory/Ordinal/Family.lean`; changed: attributes:added, proof:modified, statement_or_type:modified
- before the PR:
```lean
theorem IsNormal.map_sSup_of_bddAbove {f : Ordinal.{u} → Ordinal.{v}} (H : IsNormal f)
    {s : Set Ordinal.{u}} (hs : BddAbove s) (hn : s.Nonempty) : f (sSup s) = sSup (f '' s) := by
  have := hn.to_subtype
  rw [sSup_eq_iSup', sSup_image', H.map_iSup_of_bddAbove]
  rwa [Subtype.range_coe_subtype, setOf_mem_eq]
```
- as the PR leaves it:
```lean
@[deprecated Order.IsNormal.map_sSup (since := "2025-12-25")]
theorem IsNormal.map_sSup_of_bddAbove {f : Ordinal.{u} → Ordinal.{v}} (H : Ordinal.IsNormal f)
    {s : Set Ordinal.{u}} (hs : BddAbove s) (hn : s.Nonempty) : f (sSup s) = sSup (f '' s) :=
  Order.IsNormal.map_sSup H hn hs
```

### `command in Family.lean` (command, added) [386357a3a5]
- file: `Mathlib/SetTheory/Ordinal/Family.lean`; changed: value_or_body:modified
- as the PR leaves it:
```lean
@[deprecated (since := "2025-12-25")]
alias iSup_add_nat := iSup_add_natCast
```

### `Ordinal.iSup_add_natCast` (theorem, added) [5bc8f2e98e]
- file: `Mathlib/SetTheory/Ordinal/Family.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[simp]
theorem iSup_add_natCast (o : Ordinal) : ⨆ n : ℕ, o + n = o + ω :=
  apply_omega0_of_isNormal (isNormal_add_right o)
```

### `Ordinal.IsNormal.bsup` (theorem, modified) [8b3724e3b2]
- file: `Mathlib/SetTheory/Ordinal/Family.lean`; changed: proof:modified
- before the PR:
```lean
theorem IsNormal.bsup {f : Ordinal → Ordinal} (H : IsNormal f) {o : Ordinal} :
    ∀ (g : ∀ a < o, Ordinal), o ≠ 0 → f (bsup o g) = bsup o fun a h => f (g a h) :=
  inductionOn o fun α r _ g h => by
    haveI := type_ne_zero_iff_nonempty.1 h
    rw [← iSup'_eq_bsup r, IsNormal.map_iSup H, ← iSup'_eq_bsup r] <;> rfl
```
- as the PR leaves it:
```lean
theorem IsNormal.bsup {f : Ordinal → Ordinal} (H : IsNormal f) {o : Ordinal} :
    ∀ (g : ∀ a < o, Ordinal), o ≠ 0 → f (bsup o g) = bsup o fun a h => f (g a h) :=
  inductionOn o fun α r _ g h => by
    haveI := type_ne_zero_iff_nonempty.1 h
    rw [← iSup'_eq_bsup r, Order.IsNormal.map_iSup H (bddAbove_of_small _), ← iSup'_eq_bsup r] <;>
      rfl
```

### `Ordinal.IsNormal.apply_omega0` (theorem, removed) [8c227ac92a]
- file: `Mathlib/SetTheory/Ordinal/Family.lean`; changed: name:removed, proof:removed, statement_or_type:removed
- before the PR:
```lean
theorem IsNormal.apply_omega0 {f : Ordinal.{u} → Ordinal.{v}} (hf : IsNormal f) :
    ⨆ n : ℕ, f n = f ω := by rw [← iSup_natCast, hf.map_iSup]
```

### `Ordinal.IsNormal.apply_of_isSuccLimit` (theorem, modified) [8e76433d52]
- file: `Mathlib/SetTheory/Ordinal/Family.lean`; changed: attributes:added, proof:modified, statement_or_type:modified
- before the PR:
```lean
theorem IsNormal.apply_of_isSuccLimit {f : Ordinal.{u} → Ordinal.{v}} (H : IsNormal f) {o : Ordinal}
    (ho : IsSuccLimit o) : f o = ⨆ a : Iio o, f a := by
  have : Nonempty (Iio o) := ⟨0, ho.bot_lt⟩
  rw [← H.map_iSup, ho.iSup_Iio]
```
- as the PR leaves it:
```lean
@[deprecated Order.IsNormal.apply_of_isSuccLimit (since := "2025-12-25")]
theorem IsNormal.apply_of_isSuccLimit {f : Ordinal.{u} → Ordinal.{v}} (H : Ordinal.IsNormal f)
    {o : Ordinal} (ho : IsSuccLimit o) : f o = ⨆ a : Iio o, f a :=
  Order.IsNormal.apply_of_isSuccLimit H ho
```

### `Ordinal.iSup_mul_natCast` (theorem, modified) [954a7fd67d]
- file: `Mathlib/SetTheory/Ordinal/Family.lean`; changed: name:modified, proof:modified
- before the PR:
```lean
@[simp]
theorem iSup_mul_nat (o : Ordinal) : ⨆ n : ℕ, o * n = o * ω := by
  rcases eq_zero_or_pos o with (rfl | ho)
  · rw [zero_mul]
    exact iSup_eq_zero_iff.2 fun n => zero_mul (n : Ordinal)
  · exact (isNormal_mul_right ho).apply_omega0
```
- as the PR leaves it:
```lean
@[simp]
theorem iSup_mul_natCast (o : Ordinal) : ⨆ n : ℕ, o * n = o * ω := by
  rcases eq_zero_or_pos o with (rfl | ho)
  · rw [zero_mul]
    exact iSup_eq_zero_iff.2 fun n => zero_mul (n : Ordinal)
  · exact apply_omega0_of_isNormal (isNormal_mul_right ho)
```

### `Ordinal.IsNormal.map_iSup_of_bddAbove` (theorem, modified) [a10ec7be3c]
- file: `Mathlib/SetTheory/Ordinal/Family.lean`; changed: attributes:added, statement_or_type:modified
- before the PR:
```lean
theorem IsNormal.map_iSup_of_bddAbove {f : Ordinal.{u} → Ordinal.{v}} (H : IsNormal f)
    {ι : Type*} (g : ι → Ordinal.{u}) (hg : BddAbove (range g))
    [Nonempty ι] : f (⨆ i, g i) = ⨆ i, f (g i) :=
  Order.IsNormal.map_iSup H hg
```
- as the PR leaves it:
```lean
@[deprecated Order.IsNormal.map_iSup (since := "2025-12-25")]
theorem IsNormal.map_iSup_of_bddAbove {f : Ordinal.{u} → Ordinal.{v}} (H : Ordinal.IsNormal f)
    {ι : Type*} (g : ι → Ordinal.{u}) (hg : BddAbove (range g))
    [Nonempty ι] : f (⨆ i, g i) = ⨆ i, f (g i) :=
  Order.IsNormal.map_iSup H hg
```

### `Ordinal.apply_omega0_of_isNormal` (theorem, added) [b1d2ad6422]
- file: `Mathlib/SetTheory/Ordinal/Family.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem apply_omega0_of_isNormal {f : Ordinal.{u} → Ordinal.{v}} (hf : IsNormal f) :
    ⨆ n : ℕ, f n = f ω := by
  rw [← iSup_natCast, hf.map_iSup (bddAbove_of_small _)]
```

### `Ordinal.IsNormal.map_iSup` (theorem, modified) [b2901fc23b]
- file: `Mathlib/SetTheory/Ordinal/Family.lean`; changed: attributes:added, proof:modified, statement_or_type:modified
- before the PR:
```lean
theorem IsNormal.map_iSup {f : Ordinal.{u} → Ordinal.{v}} (H : IsNormal f)
    {ι : Type w} (g : ι → Ordinal.{u}) [Small.{u} ι] [Nonempty ι] :
    f (⨆ i, g i) = ⨆ i, f (g i) :=
  H.map_iSup_of_bddAbove g (bddAbove_of_small _)
```
- as the PR leaves it:
```lean
@[deprecated Order.IsNormal.map_iSup (since := "2025-12-25")]
theorem IsNormal.map_iSup {f : Ordinal.{u} → Ordinal.{v}} (H : Ordinal.IsNormal f)
    {ι : Type w} (g : ι → Ordinal.{u}) [Small.{u} ι] [Nonempty ι] :
    f (⨆ i, g i) = ⨆ i, f (g i) :=
  Order.IsNormal.map_iSup H (bddAbove_of_small _)
```

### `Ordinal.IsNormal.eq_iff_zero_and_succ` (theorem, added) [c92f6a252a]
- file: `Mathlib/SetTheory/Ordinal/Family.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[deprecated IsNormal.ext (since := "2025-12-25")]
theorem IsNormal.eq_iff_zero_and_succ {f g : Ordinal.{u} → Ordinal.{u}} (hf : IsNormal f)
    (hg : IsNormal g) : f = g ↔ f 0 = g 0 ∧ ∀ a, f a = g a → f (succ a) = g (succ a) :=
  Order.IsNormal.ext hf hg
```

### `Ordinal.IsNormal.map_sSup` (theorem, modified) [d19c0ebfe7]
- file: `Mathlib/SetTheory/Ordinal/Family.lean`; changed: attributes:added, proof:modified
- before the PR:
```lean
theorem IsNormal.map_sSup {f : Ordinal.{u} → Ordinal.{v}} (H : IsNormal f)
    {s : Set Ordinal.{u}} (hn : s.Nonempty) [Small.{u} s] : f (sSup s) = sSup (f '' s) :=
  H.map_sSup_of_bddAbove (bddAbove_of_small s) hn
```
- as the PR leaves it:
```lean
@[deprecated Order.IsNormal.map_sSup (since := "2025-12-25")]
theorem IsNormal.map_sSup {f : Ordinal.{u} → Ordinal.{v}} (H : IsNormal f)
    {s : Set Ordinal.{u}} (hn : s.Nonempty) [Small.{u} s] : f (sSup s) = sSup (f '' s) :=
  Order.IsNormal.map_sSup H hn (bddAbove_of_small _)
```

### `command in Family.lean` (command, added) [d8de93a81e]
- file: `Mathlib/SetTheory/Ordinal/Family.lean`; changed: value_or_body:modified
- as the PR leaves it:
```lean
@[deprecated (since := "2025-12-25")]
alias IsNormal.apply_omega0 := apply_omega0_of_isNormal
```

### `Ordinal.iSup_mul_nat` (theorem, removed) [db18344bba]
- file: `Mathlib/SetTheory/Ordinal/Family.lean`; changed: attributes:removed, name:removed, proof:removed, statement_or_type:removed
- before the PR:
```lean
@[simp]
theorem iSup_mul_nat (o : Ordinal) : ⨆ n : ℕ, o * n = o * ω := by
  rcases eq_zero_or_pos o with (rfl | ho)
  · rw [zero_mul]
    exact iSup_eq_zero_iff.2 fun n => zero_mul (n : Ordinal)
  · exact (isNormal_mul_right ho).apply_omega0
```

### `Ordinal.iSup_add_nat` (theorem, removed) [deff40f31f]
- file: `Mathlib/SetTheory/Ordinal/Family.lean`; changed: attributes:removed, name:removed, proof:removed, statement_or_type:removed
- before the PR:
```lean
@[simp]
theorem iSup_add_nat (o : Ordinal) : ⨆ n : ℕ, o + n = o + ω :=
  (isNormal_add_right o).apply_omega0
```

### `command in Family.lean` (command, added) [e46ef469f7]
- file: `Mathlib/SetTheory/Ordinal/Family.lean`; changed: value_or_body:modified
- as the PR leaves it:
```lean
set_option linter.deprecated false in
```

### `command in Family.lean` (command, modified) [eedbd90d4c]
- file: `Mathlib/SetTheory/Ordinal/Family.lean`; changed: value_or_body:modified
- before the PR:
```lean
@[deprecated (since := "2025-07-08")]
alias IsNormal.apply_of_isLimit := IsNormal.apply_of_isSuccLimit
```
- as the PR leaves it:
```lean
@[deprecated (since := "2025-07-08")]
alias IsNormal.apply_of_isLimit := Order.IsNormal.apply_of_isSuccLimit
```

### `command in Family.lean` (command, added) [f4a0d8d065]
- file: `Mathlib/SetTheory/Ordinal/Family.lean`; changed: value_or_body:modified
- as the PR leaves it:
```lean
@[deprecated (since := "2025-12-25")]
alias iSup_mul_nat := iSup_mul_natCast
```

### `Ordinal.IsNormal.apply_le_nfp` (theorem, removed) [0615d466ac]
- file: `Mathlib/SetTheory/Ordinal/FixedPoint.lean`; changed: name:removed, proof:removed, statement_or_type:removed
- before the PR:
```lean
theorem IsNormal.apply_le_nfp (H : IsNormal f) {a b} : f b ≤ nfp f a ↔ b ≤ nfp f a :=
  ⟨H.le_apply.trans, fun h => by simpa only [H.nfp_fp] using H.le_iff.2 h⟩
```

### `module_doc in FixedPoint.lean` (module_doc, modified) [0657ec149d]
- file: `Mathlib/SetTheory/Ordinal/FixedPoint.lean`; changed: documentation:modified
- before the PR:
```lean
/-!
# Fixed points of normal functions

We prove various statements about the fixed points of normal ordinal functions. We state them in
three forms: as statements about type-indexed families of normal functions, as statements about
ordinal-indexed families of normal functions, and as statements about a single normal function. For
the most part, the first case encompasses the others.

Moreover, we prove some lemmas about the fixed points of specific normal functions.

## Main definitions and results

* `nfpFamily`, `nfp`: the next fixed point of a (family of) normal function(s).
* `not_bddAbove_fp_family`, `not_bddAbove_fp`: the (common) fixed points of a (family of) normal
  function(s) are unbounded in the ordinals.
* `deriv_add_eq_mul_omega0_add`: a characterization of the derivative of addition.
* `deriv_mul_eq_opow_omega0_mul`: a characterization of the derivative of multiplication.
-/
```
- as the PR leaves it:
```lean
/-!
# Fixed points of normal functions

We prove various statements about the fixed points of normal ordinal functions. We state them in
two forms: as statements about indexed families of normal functions, and as statements about a
single normal function.

Moreover, we prove some lemmas about the fixed points of specific normal functions.

## Main definitions and results

* `nfpFamily`, `nfp`: the next fixed point of a (family of) normal function(s).
* `not_bddAbove_fp_family`, `not_bddAbove_fp`: the (common) fixed points of a (family of) normal
  function(s) are unbounded in the ordinals.
* `deriv_add_eq_mul_omega0_add`: a characterization of the derivative of addition.
* `deriv_mul_eq_opow_omega0_mul`: a characterization of the derivative of multiplication.
-/
```

### `Ordinal.le_iff_deriv` (theorem, added) [0c26365615]
- file: `Mathlib/SetTheory/Ordinal/FixedPoint.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem le_iff_deriv (H : IsNormal f) {a} : f a ≤ a ↔ ∃ o, deriv f o = a := by
  unfold deriv
  rw [← le_iff_derivFamily fun _ : Unit => H]
  exact ⟨fun h _ => h, fun h => h Unit.unit⟩
```

### `Ordinal.mem_range_deriv` (theorem, added) [13811fb9df]
- file: `Mathlib/SetTheory/Ordinal/FixedPoint.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem mem_range_deriv (H : IsNormal f) {a} : a ∈ Set.range (deriv f) ↔ f a = a := by
  rw [Set.mem_range, ← H.strictMono.le_apply.ge_iff_eq', le_iff_deriv H]
```

### `Ordinal.nfp_fp` (theorem, modified) [1d3b373303]
- file: `Mathlib/SetTheory/Ordinal/FixedPoint.lean`; changed: name:modified
- before the PR:
```lean
theorem IsNormal.nfp_fp (H : IsNormal f) : ∀ a, f (nfp f a) = nfp f a :=
  @nfpFamily_fp Unit (fun _ => f) _ () H
```
- as the PR leaves it:
```lean
theorem nfp_fp (H : IsNormal f) : ∀ a, f (nfp f a) = nfp f a :=
  @nfpFamily_fp Unit (fun _ => f) _ () H
```

### `Ordinal.deriv_mul_eq_opow_omega0_mul` (theorem, modified) [21e8763482]
- file: `Mathlib/SetTheory/Ordinal/FixedPoint.lean`; changed: proof:modified
- before the PR:
```lean
theorem deriv_mul_eq_opow_omega0_mul {a : Ordinal.{u}} (ha : 0 < a) (b) :
    deriv (a * ·) b = a ^ ω * b := by
  revert b
  rw [← funext_iff,
    IsNormal.eq_iff_zero_and_succ (isNormal_deriv _) (isNormal_mul_right (opow_pos ω ha))]
  refine ⟨?_, fun c h => ?_⟩
  · dsimp only; rw [deriv_zero_right, nfp_mul_zero, mul_zero]
  · rw [deriv_succ, h]
    exact nfp_mul_opow_omega0_add c ha zero_lt_one (one_le_iff_pos.2 (opow_pos _ ha))
```
- as the PR leaves it:
```lean
theorem deriv_mul_eq_opow_omega0_mul {a : Ordinal.{u}} (ha : 0 < a) (b) :
    deriv (a * ·) b = a ^ ω * b := by
  revert b
  rw [← funext_iff,
    IsNormal.ext (isNormal_deriv _) (isNormal_mul_right (opow_pos ω ha))]
  refine ⟨?_, fun c h => ?_⟩
  · rw [bot_eq_zero, deriv_zero_right, nfp_mul_zero, mul_zero]
  · rw [deriv_succ, h]
    exact nfp_mul_opow_omega0_add c ha zero_lt_one (one_le_iff_pos.2 (opow_pos _ ha))
```

### `Ordinal.mul_le_right_iff_opow_omega0_dvd` (theorem, modified) [3021fa611d]
- file: `Mathlib/SetTheory/Ordinal/FixedPoint.lean`; changed: proof:modified
- before the PR:
```lean
theorem mul_le_right_iff_opow_omega0_dvd {a b : Ordinal} (ha : 0 < a) :
    a * b ≤ b ↔ (a ^ ω) ∣ b := by
  rw [← mul_eq_right_iff_opow_omega0_dvd]
  exact (isNormal_mul_right ha).le_iff_eq
```
- as the PR leaves it:
```lean
theorem mul_le_right_iff_opow_omega0_dvd {a b : Ordinal} (ha : 0 < a) :
    a * b ≤ b ↔ (a ^ ω) ∣ b := by
  rw [← mul_eq_right_iff_opow_omega0_dvd]
  exact (isNormal_mul_right ha).strictMono.le_apply.ge_iff_eq'
```

### `Ordinal.deriv_eq_id_of_nfp_eq_id` (theorem, modified) [4296c0a067]
- file: `Mathlib/SetTheory/Ordinal/FixedPoint.lean`; changed: proof:modified
- before the PR:
```lean
theorem deriv_eq_id_of_nfp_eq_id (h : nfp f = id) : deriv f = id :=
  ((isNormal_deriv _).eq_iff_zero_and_succ IsNormal.refl).2 (by simp [h])
```
- as the PR leaves it:
```lean
theorem deriv_eq_id_of_nfp_eq_id (h : nfp f = id) : deriv f = id :=
  ((isNormal_deriv _).ext .id).2 (by simp [h])
```

### `Ordinal.derivFamily_fp` (theorem, modified) [5136696372]
- file: `Mathlib/SetTheory/Ordinal/FixedPoint.lean`; changed: proof:modified
- before the PR:
```lean
theorem derivFamily_fp [Small.{u} ι] {i} (H : IsNormal (f i)) (o : Ordinal) :
    f i (derivFamily f o) = derivFamily f o := by
  induction o using limitRecOn with
  | zero =>
    rw [derivFamily_zero]
    exact nfpFamily_fp H 0
  | succ =>
    rw [derivFamily_succ]
    exact nfpFamily_fp H _
  | limit o l IH =>
    have := l.nonempty_Iio.to_subtype
    rw [derivFamily_limit _ l, H.map_iSup]
    refine eq_of_forall_ge_iff fun c => ?_
    rw [Ordinal.iSup_le_iff, Ordinal.iSup_le_iff]
    refine forall_congr' fun a ↦ ?_
    rw [IH _ a.2]
```
- as the PR leaves it:
```lean
theorem derivFamily_fp [Small.{u} ι] {i} (H : IsNormal (f i)) (o : Ordinal) :
    f i (derivFamily f o) = derivFamily f o := by
  induction o using limitRecOn with
  | zero =>
    rw [derivFamily_zero]
    exact nfpFamily_fp H 0
  | succ =>
    rw [derivFamily_succ]
    exact nfpFamily_fp H _
  | limit o l IH =>
    have := l.nonempty_Iio.to_subtype
    rw [derivFamily_limit _ l, H.map_iSup (bddAbove_of_small _)]
    refine eq_of_forall_ge_iff fun c => ?_
    rw [Ordinal.iSup_le_iff, Ordinal.iSup_le_iff]
    refine forall_congr' fun a ↦ ?_
    rw [IH _ a.2]
```

### `Ordinal.IsNormal.nfp_le_apply` (theorem, removed) [5597c602c8]
- file: `Mathlib/SetTheory/Ordinal/FixedPoint.lean`; changed: name:removed, proof:removed, statement_or_type:removed
- before the PR:
```lean
theorem IsNormal.nfp_le_apply (H : IsNormal f) {a b} : nfp f a ≤ f b ↔ nfp f a ≤ b :=
  le_iff_le_iff_lt_iff_lt.2 H.apply_lt_nfp
```

### `Ordinal.apply_lt_nfpFamily_iff` (theorem, modified) [5b8a2f01c4]
- file: `Mathlib/SetTheory/Ordinal/FixedPoint.lean`; changed: proof:modified
- before the PR:
```lean
theorem apply_lt_nfpFamily_iff [Nonempty ι] [Small.{u} ι] (H : ∀ i, IsNormal (f i)) {a b} :
    (∀ i, f i b < nfpFamily f a) ↔ b < nfpFamily f a := by
  refine ⟨fun h ↦ ?_, apply_lt_nfpFamily H⟩
  let ⟨l, hl⟩ := lt_nfpFamily_iff.1 (h (Classical.arbitrary ι))
  exact lt_nfpFamily_iff.2 <| ⟨l, (H _).le_apply.trans_lt hl⟩
```
- as the PR leaves it:
```lean
theorem apply_lt_nfpFamily_iff [Nonempty ι] [Small.{u} ι] (H : ∀ i, IsNormal (f i)) {a b} :
    (∀ i, f i b < nfpFamily f a) ↔ b < nfpFamily f a := by
  refine ⟨fun h ↦ ?_, apply_lt_nfpFamily H⟩
  let ⟨l, hl⟩ := lt_nfpFamily_iff.1 (h (Classical.arbitrary ι))
  exact lt_nfpFamily_iff.2 <| ⟨l, (H _).strictMono.le_apply.trans_lt hl⟩
```

### `Ordinal.nfp_le_apply` (theorem, added) [6c738890c0]
- file: `Mathlib/SetTheory/Ordinal/FixedPoint.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem nfp_le_apply (H : IsNormal f) {a b} : nfp f a ≤ f b ↔ nfp f a ≤ b :=
  le_iff_le_iff_lt_iff_lt.2 (apply_lt_nfp H)
```

### `Ordinal.fp_iff_deriv` (theorem, added) [70f28ecac2]
- file: `Mathlib/SetTheory/Ordinal/FixedPoint.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[deprecated mem_range_deriv (since := "2025-10-25")]
theorem fp_iff_deriv (H : IsNormal f) {a} : f a = a ↔ ∃ o, deriv f o = a :=
  (mem_range_deriv H).symm
```

### `command in FixedPoint.lean` (command, modified) [71d3e988b0]
- file: `Mathlib/SetTheory/Ordinal/FixedPoint.lean`; changed: value_or_body:modified
- before the PR:
```lean
theorem IsNormal.mem_range_deriv (H : IsNormal f) {a} : a ∈ Set.range (deriv f) ↔ f a = a :=
  H.fp_iff_deriv.symm
```
- as the PR leaves it:
```lean
@[deprecated mem_range_deriv (since := "2025-10-25")]
alias IsNormal.fp_iff_deriv := fp_iff_deriv
```

### `Ordinal.deriv_add_eq_mul_omega0_add` (theorem, modified) [732a6391e8]
- file: `Mathlib/SetTheory/Ordinal/FixedPoint.lean`; changed: proof:modified
- before the PR:
```lean
theorem deriv_add_eq_mul_omega0_add (a b : Ordinal.{u}) : deriv (a + ·) b = a * ω + b := by
  revert b
  rw [← funext_iff, IsNormal.eq_iff_zero_and_succ (isNormal_deriv _) (isNormal_add_right _)]
  refine ⟨?_, fun a h => ?_⟩
  · rw [deriv_zero_right, add_zero]
    exact nfp_add_zero a
  · rw [deriv_succ, h, add_succ]
    exact nfp_eq_self (add_eq_right_iff_mul_omega0_le.2 (le_self_add.trans (le_succ _)))
```
- as the PR leaves it:
```lean
theorem deriv_add_eq_mul_omega0_add (a b : Ordinal.{u}) : deriv (a + ·) b = a * ω + b := by
  revert b
  rw [← funext_iff, IsNormal.ext (isNormal_deriv _) (isNormal_add_right _)]
  refine ⟨?_, fun a h => ?_⟩
  · rw [bot_eq_zero, deriv_zero_right, add_zero]
    exact nfp_add_zero a
  · rw [deriv_succ, h, add_succ]
    exact nfp_eq_self (add_eq_right_iff_mul_omega0_le.2 (le_self_add.trans (le_succ _)))
```

### `Ordinal.add_eq_right_iff_mul_omega0_le` (theorem, modified) [7a9f49b438]
- file: `Mathlib/SetTheory/Ordinal/FixedPoint.lean`; changed: proof:modified
- before the PR:
```lean
theorem add_eq_right_iff_mul_omega0_le {a b : Ordinal} : a + b = b ↔ a * ω ≤ b := by
  refine ⟨fun h => ?_, fun h => ?_⟩
  · rw [← nfp_add_zero a, ← deriv_zero_right]
    obtain ⟨c, hc⟩ := (isNormal_add_right a).fp_iff_deriv.1 h
    rw [← hc]
    exact (isNormal_deriv _).monotone (zero_le _)
  · have := Ordinal.add_sub_cancel_of_le h
    nth_rw 1 [← this]
    rwa [← add_assoc, ← mul_one_add, one_add_omega0]
```
- as the PR leaves it:
```lean
theorem add_eq_right_iff_mul_omega0_le {a b : Ordinal} : a + b = b ↔ a * ω ≤ b := by
  refine ⟨fun h => ?_, fun h => ?_⟩
  · rw [← nfp_add_zero a, ← deriv_zero_right]
    obtain ⟨c, hc⟩ := (mem_range_deriv (isNormal_add_right a)).2 h
    rw [← hc]
    exact (isNormal_deriv _).monotone (zero_le _)
  · have := Ordinal.add_sub_cancel_of_le h
    nth_rw 1 [← this]
    rwa [← add_assoc, ← mul_one_add, one_add_omega0]
```

### `Ordinal.nfp_mul_one` (theorem, modified) [7cf402ddf3]
- file: `Mathlib/SetTheory/Ordinal/FixedPoint.lean`; changed: proof:modified
- before the PR:
```lean
@[simp]
theorem nfp_mul_one {a : Ordinal} (ha : 0 < a) : nfp (a * ·) 1 = a ^ ω := by
  rw [← iSup_iterate_eq_nfp, ← iSup_pow ha]
  congr
  funext n
  induction n with
  | zero => rw [pow_zero, iterate_zero_apply]
  | succ n hn => rw [iterate_succ_apply', Nat.add_comm, pow_add, pow_one, hn]
```
- as the PR leaves it:
```lean
@[simp]
theorem nfp_mul_one {a : Ordinal} (ha : 0 < a) : nfp (a * ·) 1 = a ^ ω := by
  rw [← iSup_iterate_eq_nfp, ← iSup_pow_natCast ha]
  congr
  funext n
  induction n with
  | zero => rw [pow_zero, iterate_zero_apply]
  | succ n hn => rw [iterate_succ_apply', Nat.add_comm, pow_add, pow_one, hn]
```

### `command in FixedPoint.lean` (command, added) [8c29dc61f1]
- file: `Mathlib/SetTheory/Ordinal/FixedPoint.lean`; changed: value_or_body:modified
- as the PR leaves it:
```lean
@[deprecated (since := "2025-12-25")]
alias IsNormal.apply_lt_nfp := apply_lt_nfp
```

### `Ordinal.apply_le_nfpFamily` (theorem, modified) [8f0dbea813]
- file: `Mathlib/SetTheory/Ordinal/FixedPoint.lean`; changed: proof:modified
- before the PR:
```lean
theorem apply_le_nfpFamily [Small.{u} ι] [hι : Nonempty ι] (H : ∀ i, IsNormal (f i)) {a b} :
    (∀ i, f i b ≤ nfpFamily f a) ↔ b ≤ nfpFamily f a := by
  refine ⟨fun h => ?_, fun h i => ?_⟩
  · obtain ⟨i⟩ := hι
    exact (H i).le_apply.trans (h i)
  · rw [← nfpFamily_fp (H i)]
    exact (H i).monotone h
```
- as the PR leaves it:
```lean
theorem apply_le_nfpFamily [Small.{u} ι] [hι : Nonempty ι] (H : ∀ i, IsNormal (f i)) {a b} :
    (∀ i, f i b ≤ nfpFamily f a) ↔ b ≤ nfpFamily f a := by
  refine ⟨fun h => ?_, fun h i => ?_⟩
  · obtain ⟨i⟩ := hι
    exact (H i).strictMono.le_apply.trans (h i)
  · rw [← nfpFamily_fp (H i)]
    exact (H i).monotone h
```

### `command in FixedPoint.lean` (command, added) [91ce8fa8b2]
- file: `Mathlib/SetTheory/Ordinal/FixedPoint.lean`; changed: value_or_body:modified
- as the PR leaves it:
```lean
@[deprecated (since := "2025-12-25")]
alias IsNormal.apply_le_nfp := apply_le_nfp
```

### `Ordinal.fp_iff_derivFamily` (theorem, modified) [92d831618b]
- file: `Mathlib/SetTheory/Ordinal/FixedPoint.lean`; changed: proof:modified
- before the PR:
```lean
theorem fp_iff_derivFamily [Small.{u} ι] (H : ∀ i, IsNormal (f i)) {a} :
    (∀ i, f i a = a) ↔ ∃ o, derivFamily f o = a :=
  Iff.trans ⟨fun h i => le_of_eq (h i), fun h i => (H i).le_iff_eq.1 (h i)⟩ (le_iff_derivFamily H)
```
- as the PR leaves it:
```lean
theorem fp_iff_derivFamily [Small.{u} ι] (H : ∀ i, IsNormal (f i)) {a} :
    (∀ i, f i a = a) ↔ ∃ o, derivFamily f o = a :=
  Iff.trans ⟨fun h i => le_of_eq (h i), fun h i => (H i).strictMono.le_apply.ge_iff_eq'.1 (h i)⟩
    (le_iff_derivFamily H)
```

### `Ordinal.apply_lt_nfp` (theorem, modified) [93bbbe84df]
- file: `Mathlib/SetTheory/Ordinal/FixedPoint.lean`; changed: name:modified
- before the PR:
```lean
theorem IsNormal.apply_lt_nfp (H : IsNormal f) {a b} : f b < nfp f a ↔ b < nfp f a := by
  unfold nfp
  rw [← @apply_lt_nfpFamily_iff Unit (fun _ => f) _ _ (fun _ => H) a b]
  exact ⟨fun h _ => h, fun h => h Unit.unit⟩
```
- as the PR leaves it:
```lean
theorem apply_lt_nfp (H : IsNormal f) {a b} : f b < nfp f a ↔ b < nfp f a := by
  unfold nfp
  rw [← @apply_lt_nfpFamily_iff Unit (fun _ => f) _ _ (fun _ => H) a b]
  exact ⟨fun h _ => h, fun h => h Unit.unit⟩
```

### `command in FixedPoint.lean` (command, added) [a3ec3f1774]
- file: `Mathlib/SetTheory/Ordinal/FixedPoint.lean`; changed: value_or_body:modified
- as the PR leaves it:
```lean
@[deprecated (since := "2025-10-25")]
alias IsNormal.deriv_fp := deriv_fp
```

### `Ordinal.add_le_right_iff_mul_omega0_le` (theorem, modified) [a55b6ffa23]
- file: `Mathlib/SetTheory/Ordinal/FixedPoint.lean`; changed: proof:modified
- before the PR:
```lean
theorem add_le_right_iff_mul_omega0_le {a b : Ordinal} : a + b ≤ b ↔ a * ω ≤ b := by
  rw [← add_eq_right_iff_mul_omega0_le]
  exact (isNormal_add_right a).le_iff_eq
```
- as the PR leaves it:
```lean
theorem add_le_right_iff_mul_omega0_le {a b : Ordinal} : a + b ≤ b ↔ a * ω ≤ b := by
  rw [← add_eq_right_iff_mul_omega0_le]
  exact (isNormal_add_right a).strictMono.le_apply.ge_iff_eq'
```

### `command in FixedPoint.lean` (command, added) [a68f89ae99]
- file: `Mathlib/SetTheory/Ordinal/FixedPoint.lean`; changed: value_or_body:modified
- as the PR leaves it:
```lean
@[deprecated (since := "2025-12-25")]
alias IsNormal.nfp_le_apply := nfp_le_apply
```

### `Ordinal.nfp_add_zero` (theorem, modified) [aa5b33491f]
- file: `Mathlib/SetTheory/Ordinal/FixedPoint.lean`; changed: proof:modified
- before the PR:
```lean
@[simp]
theorem nfp_add_zero (a) : nfp (a + ·) 0 = a * ω := by
  simp_rw [← iSup_iterate_eq_nfp, ← iSup_mul_nat]
  congr; funext n
  induction n with
  | zero => rw [Nat.cast_zero, mul_zero, iterate_zero_apply]
  | succ n hn => rw [iterate_succ_apply', Nat.add_comm, Nat.cast_add, Nat.cast_one, mul_one_add, hn]
```
- as the PR leaves it:
```lean
@[simp]
theorem nfp_add_zero (a) : nfp (a + ·) 0 = a * ω := by
  simp_rw [← iSup_iterate_eq_nfp, ← iSup_mul_natCast]
  congr; funext n
  induction n with
  | zero => rw [Nat.cast_zero, mul_zero, iterate_zero_apply]
  | succ n hn => rw [iterate_succ_apply', Nat.add_comm, Nat.cast_add, Nat.cast_one, mul_one_add, hn]
```

### `Ordinal.nfp_mul_opow_omega0_add` (theorem, modified) [bbe7c79320]
- file: `Mathlib/SetTheory/Ordinal/FixedPoint.lean`; changed: proof:modified
- before the PR:
```lean
theorem nfp_mul_opow_omega0_add {a c : Ordinal} (b) (ha : 0 < a) (hc : 0 < c)
    (hca : c ≤ a ^ ω) : nfp (a * ·) (a ^ ω * b + c) = a ^ ω * succ b := by
  apply le_antisymm
  · apply nfp_le_fp (isNormal_mul_right ha).monotone
    · rw [mul_succ]
      gcongr
    · dsimp only; rw [← mul_assoc, ← opow_one_add, one_add_omega0]
  · obtain ⟨d, hd⟩ :=
      mul_eq_right_iff_opow_omega0_dvd.1 ((isNormal_mul_right ha).nfp_fp ((a ^ ω) * b + c))
    rw [hd]
    apply mul_le_mul_right
    have := le_nfp (a * ·) (a ^ ω * b + c)
    rw [hd] at this
    have := (add_lt_add_right hc (a ^ ω * b)).trans_le this
    rw [add_zero, mul_lt_mul_iff_right₀ (opow_pos ω ha)] at this
    rwa [succ_le_iff]
```
- as the PR leaves it:
```lean
theorem nfp_mul_opow_omega0_add {a c : Ordinal} (b) (ha : 0 < a) (hc : 0 < c)
    (hca : c ≤ a ^ ω) : nfp (a * ·) (a ^ ω * b + c) = a ^ ω * succ b := by
  apply le_antisymm
  · apply nfp_le_fp (isNormal_mul_right ha).monotone
    · rw [mul_succ]
      gcongr
    · dsimp only; rw [← mul_assoc, ← opow_one_add, one_add_omega0]
  · obtain ⟨d, hd⟩ :=
      mul_eq_right_iff_opow_omega0_dvd.1 (nfp_fp (isNormal_mul_right ha) (a ^ ω * b + c))
    rw [hd]
    apply mul_le_mul_right
    have := le_nfp (a * ·) (a ^ ω * b + c)
    rw [hd] at this
    have := (add_lt_add_right hc (a ^ ω * b)).trans_le this
    rw [add_zero, mul_lt_mul_iff_right₀ (opow_pos ω ha)] at this
    rwa [succ_le_iff]
```

### `Ordinal.IsNormal.le_iff_deriv` (theorem, removed) [ca374de9fe]
- file: `Mathlib/SetTheory/Ordinal/FixedPoint.lean`; changed: name:removed, proof:removed, statement_or_type:removed
- before the PR:
```lean
theorem IsNormal.le_iff_deriv (H : IsNormal f) {a} : f a ≤ a ↔ ∃ o, deriv f o = a := by
  unfold deriv
  rw [← le_iff_derivFamily fun _ : Unit => H]
  exact ⟨fun h _ => h, fun h => h Unit.unit⟩
```

### `Ordinal.nfpFamily_fp` (theorem, modified) [d657faf9ad]
- file: `Mathlib/SetTheory/Ordinal/FixedPoint.lean`; changed: proof:modified
- before the PR:
```lean
theorem nfpFamily_fp [Small.{u} ι] {i} (H : IsNormal (f i)) (a) :
    f i (nfpFamily f a) = nfpFamily f a := by
  rw [nfpFamily, H.map_iSup]
  apply le_antisymm <;> refine Ordinal.iSup_le fun l => ?_
  · exact Ordinal.le_iSup _ (i::l)
  · exact H.le_apply.trans (Ordinal.le_iSup _ _)
```
- as the PR leaves it:
```lean
theorem nfpFamily_fp [Small.{u} ι] {i} (H : IsNormal (f i)) (a) :
    f i (nfpFamily f a) = nfpFamily f a := by
  rw [nfpFamily, H.map_iSup (bddAbove_of_small _)]
  apply le_antisymm <;> refine Ordinal.iSup_le fun l => ?_
  · exact Ordinal.le_iSup _ (i::l)
  · exact H.strictMono.le_apply.trans (Ordinal.le_iSup _ _)
```

### `command in FixedPoint.lean` (command, added) [e01edc8253]
- file: `Mathlib/SetTheory/Ordinal/FixedPoint.lean`; changed: value_or_body:modified
- as the PR leaves it:
```lean
@[deprecated (since := "2025-10-25")]
alias IsNormal.le_iff_deriv := le_iff_deriv
```

### `Ordinal.IsNormal.fp_iff_deriv` (theorem, removed) [efa5299a1d]
- file: `Mathlib/SetTheory/Ordinal/FixedPoint.lean`; changed: name:removed, proof:removed, statement_or_type:removed
- before the PR:
```lean
theorem IsNormal.fp_iff_deriv (H : IsNormal f) {a} : f a = a ↔ ∃ o, deriv f o = a := by
  rw [← H.le_iff_eq, H.le_iff_deriv]
```

### `Ordinal.deriv_fp` (theorem, modified) [f22bfb59ba]
- file: `Mathlib/SetTheory/Ordinal/FixedPoint.lean`; changed: name:modified
- before the PR:
```lean
theorem IsNormal.deriv_fp (H : IsNormal f) : ∀ o, f (deriv f o) = deriv f o :=
  derivFamily_fp (i := ⟨⟩) H
```
- as the PR leaves it:
```lean
theorem deriv_fp (H : IsNormal f) : ∀ o, f (deriv f o) = deriv f o :=
  derivFamily_fp (i := ⟨⟩) H
```

### `Ordinal.le_iff_derivFamily` (theorem, modified) [f3b7808e88]
- file: `Mathlib/SetTheory/Ordinal/FixedPoint.lean`; changed: proof:modified
- before the PR:
```lean
theorem le_iff_derivFamily [Small.{u} ι] (H : ∀ i, IsNormal (f i)) {a} :
    (∀ i, f i a ≤ a) ↔ ∃ o, derivFamily f o = a :=
  ⟨fun ha => by
    suffices ∀ (o), a ≤ derivFamily f o → ∃ o, derivFamily f o = a from
      this a (isNormal_derivFamily _).le_apply
    intro o
    induction o using limitRecOn with
    | zero =>
      intro h₁
      refine ⟨0, le_antisymm ?_ h₁⟩
      rw [derivFamily_zero]
      exact nfpFamily_le_fp (fun i => (H i).monotone) (zero_le _) ha
    | succ o IH =>
      intro h₁
      rcases le_or_gt a (derivFamily f o) with h | h
      · exact IH h
      refine ⟨succ o, le_antisymm ?_ h₁⟩
      rw [derivFamily_succ]
      exact nfpFamily_le_fp (fun i => (H i).monotone) (succ_le_of_lt h) ha
    | limit o l IH =>
      intro h₁
      rcases eq_or_lt_of_le h₁ with h | h
      · exact ⟨_, h.symm⟩
      rw [derivFamily_limit _ l, ← not_le, Ordinal.iSup_le_iff, not_forall] at h
      obtain ⟨o', h⟩ := h
      exact IH o' o'.2 (le_of_not_ge h),
    fun ⟨_, e⟩ i => e ▸ (derivFamily_fp (H i) _).le⟩
```
- as the PR leaves it:
```lean
theorem le_iff_derivFamily [Small.{u} ι] (H : ∀ i, IsNormal (f i)) {a} :
    (∀ i, f i a ≤ a) ↔ ∃ o, derivFamily f o = a :=
  ⟨fun ha => by
    suffices ∀ (o), a ≤ derivFamily f o → ∃ o, derivFamily f o = a from
      this a (isNormal_derivFamily _).strictMono.le_apply
    intro o
    induction o using limitRecOn with
    | zero =>
      intro h₁
      refine ⟨0, le_antisymm ?_ h₁⟩
      rw [derivFamily_zero]
      exact nfpFamily_le_fp (fun i => (H i).monotone) (zero_le _) ha
    | succ o IH =>
      intro h₁
      rcases le_or_gt a (derivFamily f o) with h | h
      · exact IH h
      refine ⟨succ o, le_antisymm ?_ h₁⟩
      rw [derivFamily_succ]
      exact nfpFamily_le_fp (fun i => (H i).monotone) (succ_le_of_lt h) ha
    | limit o l IH =>
      intro h₁
      rcases eq_or_lt_of_le h₁ with h | h
      · exact ⟨_, h.symm⟩
      rw [derivFamily_limit _ l, ← not_le, Ordinal.iSup_le_iff, not_forall] at h
      obtain ⟨o', h⟩ := h
      exact IH o' o'.2 (le_of_not_ge h),
    fun ⟨_, e⟩ i => e ▸ (derivFamily_fp (H i) _).le⟩
```

### `command in FixedPoint.lean` (command, added) [f62c9af82a]
- file: `Mathlib/SetTheory/Ordinal/FixedPoint.lean`; changed: value_or_body:modified
- as the PR leaves it:
```lean
@[deprecated (since := "2025-12-25")]
alias IsNormal.nfp_fp := nfp_fp
```

### `Ordinal.apply_le_nfp` (theorem, added) [fac78f8ead]
- file: `Mathlib/SetTheory/Ordinal/FixedPoint.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem apply_le_nfp (H : IsNormal f) {a b} : f b ≤ nfp f a ↔ b ≤ nfp f a :=
  ⟨H.strictMono.le_apply.trans, fun h => by simpa only [nfp_fp H] using H.monotone h⟩
```

### `Ordinal.add_omega0_opow` (theorem, modified) [02a69cc936]
- file: `Mathlib/SetTheory/Ordinal/Principal.lean`; changed: proof:modified
- before the PR:
```lean
theorem add_omega0_opow (h : a < ω ^ b) : a + ω ^ b = ω ^ b := by
  refine le_antisymm ?_ le_add_self
  induction b using limitRecOn with
  | zero =>
    rw [opow_zero, ← succ_zero, lt_succ_iff, nonpos_iff_eq_zero] at h
    rw [h, zero_add]
  | succ =>
    rw [opow_succ] at h
    rcases (lt_mul_iff_of_isSuccLimit isSuccLimit_omega0).1 h with ⟨x, xo, ax⟩
    grw [ax, opow_succ, ← mul_add, add_omega0 xo]
  | limit b l IH =>
    rcases (lt_opow_of_isSuccLimit omega0_ne_zero l).1 h with ⟨x, xb, ax⟩
    apply (((isNormal_add_right a).trans <| isNormal_opow one_lt_omega0).limit_le l).2
    intro y yb
    calc a + ω ^ y ≤ a + ω ^ max x y := by gcongr; exacts [omega0_pos, le_max_right ..]
    _ ≤ ω ^ max x y :=
      IH _ (max_lt xb yb) <| ax.trans_le <| opow_le_opow_right omega0_pos <| le_max_left x y
    _ ≤ ω ^ b :=
      opow_le_opow_right omega0_pos <| (max_lt xb yb).le
```
- as the PR leaves it:
```lean
theorem add_omega0_opow (h : a < ω ^ b) : a + ω ^ b = ω ^ b := by
  refine le_antisymm ?_ le_add_self
  induction b using limitRecOn with
  | zero =>
    rw [opow_zero, ← succ_zero, lt_succ_iff, nonpos_iff_eq_zero] at h
    rw [h, zero_add]
  | succ =>
    rw [opow_succ] at h
    rcases (lt_mul_iff_of_isSuccLimit isSuccLimit_omega0).1 h with ⟨x, xo, ax⟩
    grw [ax, opow_succ, ← mul_add, add_omega0 xo]
  | limit b l IH =>
    rcases (lt_opow_of_isSuccLimit omega0_ne_zero l).1 h with ⟨x, xb, ax⟩
    apply (((isNormal_add_right a).comp <| isNormal_opow one_lt_omega0).le_iff_forall_le l).2
    intro y yb
    calc a + ω ^ y ≤ a + ω ^ max x y := by gcongr; exacts [omega0_pos, le_max_right ..]
    _ ≤ ω ^ max x y :=
      IH _ (max_lt xb yb) <| ax.trans_le <| opow_le_opow_right omega0_pos <| le_max_left x y
    _ ≤ ω ^ b :=
      opow_le_opow_right omega0_pos <| (max_lt xb yb).le
```

### `Ordinal.mul_lt_omega0_opow` (theorem, modified) [4d01e28bd2]
- file: `Mathlib/SetTheory/Ordinal/Principal.lean`; changed: proof:modified
- before the PR:
```lean
theorem mul_lt_omega0_opow (c0 : 0 < c) (ha : a < ω ^ c) (hb : b < ω) : a * b < ω ^ c := by
  rcases zero_or_succ_or_isSuccLimit c with (rfl | ⟨c, rfl⟩ | l)
  · exact (lt_irrefl _).elim c0
  · rw [opow_succ] at ha
    obtain ⟨n, hn, an⟩ :=
      ((isNormal_mul_right <| opow_pos _ omega0_pos).limit_lt isSuccLimit_omega0).1 ha
    grw [an, opow_succ, mul_assoc]
    gcongr
    exacts [opow_pos _ omega0_pos, principal_mul_omega0 hn hb]
  · rcases ((isNormal_opow one_lt_omega0).limit_lt l).1 ha with ⟨x, hx, ax⟩
    refine (mul_le_mul' (le_of_lt ax) (le_of_lt hb)).trans_lt ?_
    rw [← opow_succ, opow_lt_opow_iff_right one_lt_omega0]
    exact l.succ_lt hx
```
- as the PR leaves it:
```lean
theorem mul_lt_omega0_opow (c0 : 0 < c) (ha : a < ω ^ c) (hb : b < ω) : a * b < ω ^ c := by
  rcases zero_or_succ_or_isSuccLimit c with (rfl | ⟨c, rfl⟩ | l)
  · exact (lt_irrefl _).elim c0
  · rw [opow_succ] at ha
    obtain ⟨n, hn, an⟩ :=
      ((isNormal_mul_right <| opow_pos _ omega0_pos).lt_iff_exists_lt isSuccLimit_omega0).1 ha
    grw [an, opow_succ, mul_assoc]
    gcongr
    exacts [opow_pos _ omega0_pos, principal_mul_omega0 hn hb]
  · rcases ((isNormal_opow one_lt_omega0).lt_iff_exists_lt l).1 ha with ⟨x, hx, ax⟩
    refine (mul_le_mul' (le_of_lt ax) (le_of_lt hb)).trans_lt ?_
    rw [← opow_succ, opow_lt_opow_iff_right one_lt_omega0]
    exact l.succ_lt hx
```

### `Ordinal.op_eq_self_of_principal` (theorem, modified) [ee5d13b94b]
- file: `Mathlib/SetTheory/Ordinal/Principal.lean`; changed: proof:modified
- before the PR:
```lean
theorem op_eq_self_of_principal (hao : a < o) (H : IsNormal (op a))
    (ho : Principal op o) (ho' : IsSuccLimit o) : op a o = o := by
  apply H.le_apply.antisymm'
  rw [H.apply_of_isSuccLimit ho', Ordinal.iSup_le_iff]
  exact fun ⟨b, hbo⟩ ↦ (ho hao hbo).le
```
- as the PR leaves it:
```lean
theorem op_eq_self_of_principal (hao : a < o) (H : IsNormal (op a))
    (ho : Principal op o) (ho' : IsSuccLimit o) : op a o = o := by
  apply H.strictMono.le_apply.antisymm'
  rw [H.apply_of_isSuccLimit ho', Ordinal.iSup_le_iff]
  exact fun ⟨b, hbo⟩ ↦ (ho hao hbo).le
```

### `Ordinal.enumOrd_isNormal_iff_isClosed` (theorem, modified) [373a1413c2]
- file: `Mathlib/SetTheory/Ordinal/Topology.lean`; changed: proof:modified
- before the PR:
```lean
theorem enumOrd_isNormal_iff_isClosed (hs : ¬ BddAbove s) :
    IsNormal (enumOrd s) ↔ IsClosed s := by
  have Hs := enumOrd_strictMono hs
  refine
    ⟨fun h => isClosed_iff_iSup.2 fun {ι} hι f hf => ?_, fun h =>
      (isNormal_iff_strictMono_limit _).2 ⟨Hs, fun a ha o H => ?_⟩⟩
  · let g : ι → Ordinal.{u} := fun i => (enumOrdOrderIso s hs).symm ⟨_, hf i⟩
    suffices enumOrd s (⨆ i, g i) = ⨆ i, f i by
      rw [← this]
      exact enumOrd_mem hs _
    rw [IsNormal.map_iSup h g]
    congr
    ext x
    change (enumOrdOrderIso s hs _).val = f x
    rw [OrderIso.apply_symm_apply]
  · rw [isClosed_iff_bsup] at h
    suffices enumOrd s a ≤ bsup.{u, u} a fun b (_ : b < a) => enumOrd s b from
      this.trans (bsup_le H)
    obtain ⟨b, hb⟩ := enumOrd_surjective hs (h ha.ne_bot (fun b _ => enumOrd s b)
      fun b _ => enumOrd_mem hs b)
    rw [← hb]
    apply Hs.monotone
    by_contra! hba
    apply (Hs (lt_succ b)).not_ge
    rw [hb]
    exact le_bsup.{u, u} _ _ (ha.succ_lt hba)
```
- as the PR leaves it:
```lean
theorem enumOrd_isNormal_iff_isClosed (hs : ¬ BddAbove s) :
    IsNormal (enumOrd s) ↔ IsClosed s := by
  have Hs := enumOrd_strictMono hs
  refine
    ⟨fun h => isClosed_iff_iSup.2 fun {ι} hι f hf => ?_, fun h =>
      isNormal_iff.2 ⟨Hs, fun a ha o H => ?_⟩⟩
  · let g : ι → Ordinal.{u} := fun i => (enumOrdOrderIso s hs).symm ⟨_, hf i⟩
    suffices enumOrd s (⨆ i, g i) = ⨆ i, f i by
      rw [← this]
      exact enumOrd_mem hs _
    rw [Order.IsNormal.map_iSup h (bddAbove_of_small _)]
    congr
    ext x
    change (enumOrdOrderIso s hs _).val = f x
    rw [OrderIso.apply_symm_apply]
  · rw [isClosed_iff_bsup] at h
    suffices enumOrd s a ≤ bsup.{u, u} a fun b (_ : b < a) => enumOrd s b from
      this.trans (bsup_le H)
    obtain ⟨b, hb⟩ := enumOrd_surjective hs (h ha.ne_bot (fun b _ => enumOrd s b)
      fun b _ => enumOrd_mem hs b)
    rw [← hb]
    apply Hs.monotone
    by_contra! hba
    apply (Hs (lt_succ b)).not_ge
    rw [hb]
    exact le_bsup.{u, u} _ _ (ha.succ_lt hba)
```

### `command in Veblen.lean` (command, added) [0a2d2cb52a]
- file: `Mathlib/SetTheory/Ordinal/Veblen.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
@[deprecated (since := "2025-12-25")]
alias IsNormal.veblenWith_zero := isNormal_veblenWith_zero
```

### `Ordinal.veblen_gamma_zero` (theorem, modified) [1cd5114c7a]
- file: `Mathlib/SetTheory/Ordinal/Veblen.lean`; changed: proof:modified
- before the PR:
```lean
@[simp]
theorem veblen_gamma_zero (o : Ordinal) : veblen (Γ_ o) 0 = Γ_ o :=
  isNormal_veblen_zero.deriv_fp o
```
- as the PR leaves it:
```lean
@[simp]
theorem veblen_gamma_zero (o : Ordinal) : veblen (Γ_ o) 0 = Γ_ o :=
  deriv_fp isNormal_veblen_zero o
```

### `command in Veblen.lean` (command, added) [34e32ee5b8]
- file: `Mathlib/SetTheory/Ordinal/Veblen.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
@[deprecated (since := "2025-12-25")]
protected alias IsNormal.veblenWith := isNormal_veblenWith
```

### `Ordinal.isNormal_veblen` (theorem, modified) [4a903658d7]
- file: `Mathlib/SetTheory/Ordinal/Veblen.lean`; changed: proof:modified
- before the PR:
```lean
theorem isNormal_veblen (o : Ordinal) : IsNormal (veblen o) :=
  (isNormal_opow one_lt_omega0).veblenWith o
```
- as the PR leaves it:
```lean
theorem isNormal_veblen (o : Ordinal) : IsNormal (veblen o) :=
  isNormal_veblenWith (isNormal_opow one_lt_omega0) o
```

### `Ordinal.veblenWith_right_strictMono` (theorem, modified) [64a9ae8a9d]
- file: `Mathlib/SetTheory/Ordinal/Veblen.lean`; changed: proof:modified
- before the PR:
```lean
theorem veblenWith_right_strictMono (o : Ordinal) : StrictMono (veblenWith f o) :=
  (hf.veblenWith o).strictMono
```
- as the PR leaves it:
```lean
theorem veblenWith_right_strictMono (o : Ordinal) : StrictMono (veblenWith f o) :=
  (isNormal_veblenWith hf o).strictMono
```

### `Ordinal.isNormal_veblen_zero` (theorem, modified) [9b14ea4c72]
- file: `Mathlib/SetTheory/Ordinal/Veblen.lean`; changed: proof:modified
- before the PR:
```lean
theorem isNormal_veblen_zero : IsNormal (veblen · 0) :=
  (isNormal_opow one_lt_omega0).veblenWith_zero (by simp)
```
- as the PR leaves it:
```lean
theorem isNormal_veblen_zero : IsNormal (veblen · 0) :=
  isNormal_veblenWith_zero (isNormal_opow one_lt_omega0) (by simp)
```

### `Ordinal.isNormal_veblenWith_zero` (theorem, modified) [a8045db396]
- file: `Mathlib/SetTheory/Ordinal/Veblen.lean`; changed: name:modified, proof:modified
- before the PR:
```lean
theorem IsNormal.veblenWith_zero (hp : 0 < f 0) : IsNormal (veblenWith f · 0) := by
  rw [isNormal_iff_strictMono_limit]
  refine ⟨veblenWith_zero_strictMono hf hp, fun o ho a IH ↦ ?_⟩
  rw [veblenWith_of_ne_zero f ho.ne_bot, derivFamily_zero]
  apply nfpFamily_le fun l ↦ ?_
  suffices ∃ b < o, List.foldr _ 0 l ≤ veblenWith f b 0 by
    obtain ⟨b, hb, hb'⟩ := this
    exact hb'.trans (IH b hb)
  induction l with
  | nil => use 0; simpa using ho.bot_lt
  | cons a l IH =>
    obtain ⟨b, hb, hb'⟩ := IH
    refine ⟨_, ho.succ_lt (max_lt a.2 hb), ((veblenWith_right_strictMono hf _).monotone <|
      hb'.trans <| veblenWith_left_monotone hf _ <|
        (le_max_right a.1 b).trans (le_succ _)).trans ?_⟩
    rw [veblenWith_veblenWith_of_lt hf]
    rw [lt_succ_iff]
    exact le_max_left _ b
```
- as the PR leaves it:
```lean
theorem isNormal_veblenWith_zero (hp : 0 < f 0) : IsNormal (veblenWith f · 0) := by
  rw [isNormal_iff]
  refine ⟨veblenWith_zero_strictMono hf hp, fun o ho a IH ↦ ?_⟩
  rw [veblenWith_of_ne_zero f ho.ne_bot, derivFamily_zero]
  apply nfpFamily_le fun l ↦ ?_
  suffices ∃ b < o, List.foldr _ 0 l ≤ veblenWith f b 0 by
    obtain ⟨b, hb, hb'⟩ := this
    exact hb'.trans (IH b hb)
  induction l with
  | nil => use 0; simpa using ho.bot_lt
  | cons a l IH =>
    obtain ⟨b, hb, hb'⟩ := IH
    refine ⟨_, ho.succ_lt (max_lt a.2 hb), ((veblenWith_right_strictMono hf _).monotone <|
      hb'.trans <| veblenWith_left_monotone hf _ <|
        (le_max_right a.1 b).trans (le_succ _)).trans ?_⟩
    rw [veblenWith_veblenWith_of_lt hf]
    rw [lt_succ_iff]
    exact le_max_left _ b
```

### `Ordinal.veblenWith_succ` (theorem, modified) [b7cb6db2b8]
- file: `Mathlib/SetTheory/Ordinal/Veblen.lean`; changed: proof:modified
- before the PR:
```lean
theorem veblenWith_succ (o : Ordinal) : veblenWith f (succ o) = deriv (veblenWith f o) := by
  rw [deriv_eq_enumOrd (hf.veblenWith o), veblenWith_of_ne_zero f (succ_ne_zero _),
    derivFamily_eq_enumOrd]
  · apply congr_arg
    ext a
    rw [mem_iInter]
    use fun ha ↦ ha ⟨o, lt_succ o⟩
    rintro (ha : _ = _) ⟨b, hb : b < _⟩
    obtain rfl | hb := lt_succ_iff_eq_or_lt.1 hb
    · rw [Function.mem_fixedPoints_iff, ha]
    · rw [← ha]
      exact veblenWith_veblenWith_of_lt hf hb _
  · exact fun o ↦ hf.veblenWith o.1
```
- as the PR leaves it:
```lean
theorem veblenWith_succ (o : Ordinal) : veblenWith f (succ o) = deriv (veblenWith f o) := by
  rw [deriv_eq_enumOrd (isNormal_veblenWith hf o), veblenWith_of_ne_zero f (succ_ne_zero _),
    derivFamily_eq_enumOrd]
  · apply congr_arg
    ext a
    rw [mem_iInter]
    use fun ha ↦ ha ⟨o, lt_succ o⟩
    rintro (ha : _ = _) ⟨b, hb : b < _⟩
    obtain rfl | hb := lt_succ_iff_eq_or_lt.1 hb
    · rw [Function.mem_fixedPoints_iff, ha]
    · rw [← ha]
      exact veblenWith_veblenWith_of_lt hf hb _
  · exact fun o ↦ isNormal_veblenWith hf o.1
```

### `Ordinal.omega0_opow_epsilon` (theorem, modified) [c1228446e0]
- file: `Mathlib/SetTheory/Ordinal/Veblen.lean`; changed: proof:modified
- before the PR:
```lean
@[simp]
theorem omega0_opow_epsilon (o : Ordinal) : ω ^ ε_ o = ε_ o := by
  rw [epsilon_eq_deriv, (isNormal_opow one_lt_omega0).deriv_fp]
```
- as the PR leaves it:
```lean
@[simp]
theorem omega0_opow_epsilon (o : Ordinal) : ω ^ ε_ o = ε_ o := by
  rw [epsilon_eq_deriv, deriv_fp (isNormal_opow one_lt_omega0)]
```

### `Ordinal.mem_range_gamma` (theorem, modified) [e37ef5cefd]
- file: `Mathlib/SetTheory/Ordinal/Veblen.lean`; changed: proof:modified
- before the PR:
```lean
theorem mem_range_gamma : o ∈ range Γ_ ↔ veblen o 0 = o :=
  isNormal_veblen_zero.mem_range_deriv
```
- as the PR leaves it:
```lean
theorem mem_range_gamma : o ∈ range Γ_ ↔ veblen o 0 = o :=
  mem_range_deriv isNormal_veblen_zero
```

## Removed or renamed

- `Ordinal.IsNormal.cof_le`
- `Ordinal.IsNormal.cof_eq`
- `module_doc in Arithmetic.lean`
- `Ordinal.IsNormal.apply_omega0`
- `Ordinal.iSup_mul_nat`
- `Ordinal.iSup_add_nat`
- `Ordinal.IsNormal.apply_le_nfp`
- `Ordinal.IsNormal.nfp_le_apply`
- `Ordinal.IsNormal.le_iff_deriv`
- `Ordinal.IsNormal.fp_iff_deriv`

## Families (declarations that may be one decision)

- [hypothesis] `Ordinal.opow_add`, `Ordinal.opow_le_opow_iff_right`, `Ordinal.opow_lt_opow_iff_right`, `Ordinal.opow_mul`, `Ordinal.opow_right_inj` -- 5 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [hypothesis] `Ordinal.le_iff_deriv`, `Ordinal.le_iff_derivFamily` -- 2 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [hypothesis] `Ordinal.fp_iff_deriv`, `Ordinal.fp_iff_derivFamily` -- 2 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [hypothesis] `Ordinal.IsNormal.apply_le_nfp`, `Ordinal.IsNormal.apply_of_isSuccLimit`, `Ordinal.IsNormal.apply_omega0` -- 3 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [hypothesis] `Ordinal.IsNormal`, `Ordinal.isNormal_add_right`, `Ordinal.isNormal_enumOrd`, `Ordinal.isNormal_iff_strictMono_limit`, `Ordinal.isNormal_mul_right`, `Ordinal.isNormal_omega`, `Ordinal.isNormal_opow`, `Ordinal.isNormal_preOmega`, `Ordinal.isNormal_veblen`, `Ordinal.isNormal_veblenWith_zero`, `Ordinal.isNormal_veblen_zero` -- 11 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [exact] `Ordinal.add_eq_right_iff_mul_omega0_le`, `Ordinal.add_le_right_iff_mul_omega0_le`, `Ordinal.deriv_add_eq_mul_omega0_add` -- 3 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [hypothesis] `Ordinal.IsNormal.limit_le`, `Ordinal.IsNormal.limit_lt` -- 2 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [hypothesis] `Ordinal.IsNormal.le_apply`, `Ordinal.IsNormal.le_iff`, `Ordinal.IsNormal.le_iff_deriv`, `Ordinal.IsNormal.le_iff_eq`, `Ordinal.IsNormal.le_set`, `Ordinal.IsNormal.le_set'` -- 6 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [exact] `Ordinal.fp_iff_deriv`, `Ordinal.mem_range_deriv` -- 2 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [hypothesis] `Ordinal.nfp_add_zero`, `Ordinal.nfp_fp`, `Ordinal.nfp_le_apply`, `Ordinal.nfp_mul_one`, `Ordinal.nfp_mul_opow_omega0_add` -- 5 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [hypothesis] `Ordinal.IsNormal.cof_eq`, `Ordinal.IsNormal.cof_le` -- 2 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [hypothesis] `Ordinal.cof_add`, `Ordinal.cof_eq_of_isNormal`, `Ordinal.cof_le_of_isNormal`, `Ordinal.cof_omega`, `Ordinal.cof_preOmega` -- 5 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [hypothesis] `Ordinal.mul_le_right_iff_opow_omega0_dvd`, `Ordinal.mul_lt_omega0_opow` -- 2 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [hypothesis] `Ordinal.iSup_add_nat`, `Ordinal.iSup_add_natCast`, `Ordinal.iSup_mul_nat`, `Ordinal.iSup_mul_natCast`, `Ordinal.iSup_pow_natCast` -- 5 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [hypothesis] `Ordinal.mem_range_deriv`, `Ordinal.mem_range_gamma` -- 2 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [exact] `Ordinal.isNormal_opow`, `Ordinal.isSuccLimit_opow`, `Ordinal.opow_le_opow_iff_right`, `Ordinal.opow_lt_opow_iff_right`, `Ordinal.opow_right_inj` -- 5 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [exact] `Ordinal.apply_le_nfpFamily`, `Ordinal.nfpFamily_fp` -- 2 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [exact] `Ordinal.veblenWith_right_strictMono`, `Ordinal.veblenWith_succ` -- 2 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [exact] `Ordinal.deriv_mul_eq_opow_omega0_mul`, `Ordinal.mul_le_right_iff_opow_omega0_dvd`, `Ordinal.nfp_mul_opow_omega0_add` -- 3 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [hypothesis] `Ordinal.IsNormal.map_iSup`, `Ordinal.IsNormal.map_iSup_of_bddAbove`, `Ordinal.IsNormal.map_sSup`, `Ordinal.IsNormal.map_sSup_of_bddAbove` -- 4 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [exact] `Ordinal.derivFamily_fp`, `Ordinal.fp_iff_derivFamily`, `Ordinal.le_iff_derivFamily` -- 3 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [hypothesis] `Ordinal.deriv_add_eq_mul_omega0_add`, `Ordinal.deriv_eq_id_of_nfp_eq_id`, `Ordinal.deriv_fp`, `Ordinal.deriv_mul_eq_opow_omega0_mul` -- 4 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [exact] `Ordinal.isNormal_add_right`, `Ordinal.isSuccLimit_add` -- 2 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [hypothesis] `Ordinal.add_eq_right_iff_mul_omega0_le`, `Ordinal.add_le_right_iff_mul_omega0_le`, `Ordinal.add_omega0_opow` -- 3 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [exact] `Ordinal.cof_omega`, `Ordinal.cof_preOmega` -- 2 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [hypothesis] `Ordinal.apply_le_nfp`, `Ordinal.apply_le_nfpFamily`, `Ordinal.apply_lt_nfp`, `Ordinal.apply_lt_nfpFamily_iff`, `Ordinal.apply_omega0_of_isNormal` -- 5 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [hypothesis] `Ordinal.isSuccLimit_add`, `Ordinal.isSuccLimit_mul`, `Ordinal.isSuccLimit_opow` -- 3 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it

## Relations between changed declarations

- changed_siblings [high]: `Ordinal.add_eq_right_iff_mul_omega0_le` -> `Ordinal.add_le_right_iff_mul_omega0_le`
- changed_siblings [high]: `Ordinal.add_le_right_iff_mul_omega0_le` -> `Ordinal.deriv_add_eq_mul_omega0_add`
- changed_siblings [high]: `Ordinal.add_le_right_iff_mul_omega0_le` -> `Ordinal.add_eq_right_iff_mul_omega0_le`
- changed_siblings [high]: `Ordinal.apply_le_nfpFamily` -> `Ordinal.nfpFamily_fp`
- changed_siblings [high]: `Ordinal.cof_omega` -> `Ordinal.cof_preOmega`
- changed_siblings [high]: `Ordinal.cof_preOmega` -> `Ordinal.cof_omega`
- changed_siblings [high]: `Ordinal.derivFamily_fp` -> `Ordinal.le_iff_derivFamily`
- changed_siblings [high]: `Ordinal.deriv_add_eq_mul_omega0_add` -> `Ordinal.add_le_right_iff_mul_omega0_le`
- changed_siblings [high]: `Ordinal.deriv_mul_eq_opow_omega0_mul` -> `Ordinal.nfp_mul_opow_omega0_add`
- changed_siblings [high]: `Ordinal.fp_iff_deriv` -> `Ordinal.mem_range_deriv`
- changed_siblings [high]: `Ordinal.fp_iff_derivFamily` -> `Ordinal.le_iff_derivFamily`
- changed_siblings [high]: `Ordinal.isNormal_add_right` -> `Ordinal.isSuccLimit_add`
- changed_siblings [high]: `Ordinal.isNormal_opow` -> `Ordinal.opow_lt_opow_iff_right`
- changed_siblings [high]: `Ordinal.isSuccLimit_add` -> `Ordinal.isNormal_add_right`
- changed_siblings [high]: `Ordinal.isSuccLimit_opow` -> `Ordinal.opow_right_inj`
- changed_siblings [high]: `Ordinal.le_iff_derivFamily` -> `Ordinal.fp_iff_derivFamily`
- changed_siblings [high]: `Ordinal.le_iff_derivFamily` -> `Ordinal.derivFamily_fp`
- changed_siblings [high]: `Ordinal.mem_range_deriv` -> `Ordinal.fp_iff_deriv`
- changed_siblings [high]: `Ordinal.mul_le_right_iff_opow_omega0_dvd` -> `Ordinal.nfp_mul_opow_omega0_add`
- changed_siblings [high]: `Ordinal.nfpFamily_fp` -> `Ordinal.apply_le_nfpFamily`
- changed_siblings [high]: `Ordinal.nfp_mul_opow_omega0_add` -> `Ordinal.deriv_mul_eq_opow_omega0_mul`
- changed_siblings [high]: `Ordinal.nfp_mul_opow_omega0_add` -> `Ordinal.mul_le_right_iff_opow_omega0_dvd`
- changed_siblings [high]: `Ordinal.opow_le_opow_iff_right` -> `Ordinal.opow_lt_opow_iff_right`
- changed_siblings [high]: `Ordinal.opow_le_opow_iff_right` -> `Ordinal.opow_right_inj`
- changed_siblings [high]: `Ordinal.opow_lt_opow_iff_right` -> `Ordinal.opow_le_opow_iff_right`
- changed_siblings [high]: `Ordinal.opow_lt_opow_iff_right` -> `Ordinal.isNormal_opow`
- changed_siblings [high]: `Ordinal.opow_right_inj` -> `Ordinal.isSuccLimit_opow`
- changed_siblings [high]: `Ordinal.opow_right_inj` -> `Ordinal.opow_le_opow_iff_right`
- changed_siblings [high]: `Ordinal.veblenWith_right_strictMono` -> `Ordinal.veblenWith_succ`
- changed_siblings [high]: `Ordinal.veblenWith_succ` -> `Ordinal.veblenWith_right_strictMono`
- declaration_dependency [exact]: `Order.IsNormal.monotone` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.IsNormal.apply_le_nfp` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.IsNormal.apply_of_isSuccLimit` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.IsNormal.apply_omega0` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.IsNormal.bsup` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.IsNormal.cof_eq` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.IsNormal.cof_le` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.IsNormal.eq_iff_zero_and_succ` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.IsNormal.fp_iff_deriv` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.IsNormal.id_le` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.IsNormal.inj` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.IsNormal.isSuccLimit` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.IsNormal.le_apply` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.IsNormal.le_iff` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.IsNormal.le_iff_deriv` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.IsNormal.le_iff_eq` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.IsNormal.le_set` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.IsNormal.le_set'` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.IsNormal.limit_le` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.IsNormal.limit_lt` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.IsNormal.lt_iff` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.IsNormal.map_iSup` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.IsNormal.map_iSup_of_bddAbove` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.IsNormal.map_sSup` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.IsNormal.map_sSup_of_bddAbove` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.IsNormal.monotone` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.IsNormal.nfp_le_apply` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.IsNormal.refl` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.IsNormal.strictMono` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.IsNormal.trans` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.apply_le_nfp` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.apply_le_nfpFamily` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.apply_lt_nfp` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.apply_lt_nfpFamily_iff` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.apply_omega0_of_isNormal` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.cof_eq_of_isNormal` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.cof_le_of_isNormal` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.derivFamily_fp` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.deriv_fp` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.enumOrd_isNormal_iff_isClosed` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.fp_iff_deriv` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.fp_iff_derivFamily` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.isFundamentalSequence_of_isNormal` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.isNormal_add_right` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.isNormal_enumOrd` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.isNormal_iff_strictMono_limit` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.isNormal_mul_right` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.isNormal_omega` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.isNormal_opow` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.isNormal_preOmega` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.isNormal_veblen` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.isNormal_veblenWith_zero` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.isNormal_veblen_zero` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.le_iff_deriv` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.le_iff_derivFamily` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.mem_range_deriv` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.nfpFamily_fp` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.nfp_fp` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.nfp_le_apply` -> `Ordinal.IsNormal`
- declaration_dependency [exact]: `Ordinal.op_eq_self_of_principal` -> `Ordinal.IsNormal`
- direct_use_of_changed_declaration [exact]: `Order.IsNormal.monotone` -> `Ordinal.IsNormal.monotone`
- direct_use_of_changed_declaration [exact]: `Order.IsNormal.monotone` -> `Ordinal.IsNormal.strictMono`
- direct_use_of_changed_declaration [exact]: `Ordinal.IsNormal.apply_le_nfp` -> `Ordinal.IsNormal.le_apply`
- direct_use_of_changed_declaration [exact]: `Ordinal.IsNormal.apply_of_isSuccLimit` -> `Ordinal.IsNormal`
- direct_use_of_changed_declaration [exact]: `Ordinal.IsNormal.apply_omega0` -> `Ordinal.IsNormal.map_iSup`
- direct_use_of_changed_declaration [exact]: `Ordinal.IsNormal.bsup` -> `Ordinal.IsNormal`
- direct_use_of_changed_declaration [exact]: `Ordinal.IsNormal.bsup` -> `Ordinal.IsNormal.map_iSup`
- direct_use_of_changed_declaration [exact]: `Ordinal.IsNormal.cof_le` -> `Ordinal.IsNormal.strictMono`
- direct_use_of_changed_declaration [exact]: `Ordinal.IsNormal.eq_iff_zero_and_succ` -> `Ordinal.IsNormal`
- direct_use_of_changed_declaration [exact]: `Ordinal.IsNormal.fp_iff_deriv` -> `Ordinal.IsNormal.le_iff_deriv`
- direct_use_of_changed_declaration [exact]: `Ordinal.IsNormal.fp_iff_deriv` -> `Ordinal.IsNormal.le_iff_eq`
- direct_use_of_changed_declaration [exact]: `Ordinal.IsNormal.fp_iff_deriv` -> `Ordinal.le_iff_deriv`
- direct_use_of_changed_declaration [exact]: `Ordinal.IsNormal.id_le` -> `Ordinal.IsNormal.strictMono`
- direct_use_of_changed_declaration [exact]: `Ordinal.IsNormal.inj` -> `Ordinal.IsNormal.strictMono`
- direct_use_of_changed_declaration [exact]: `Ordinal.IsNormal.le_apply` -> `Ordinal.IsNormal.strictMono`
- direct_use_of_changed_declaration [exact]: `Ordinal.IsNormal.le_iff` -> `Ordinal.IsNormal.strictMono`
- direct_use_of_changed_declaration [exact]: `Ordinal.IsNormal.le_iff_deriv` -> `Ordinal.le_iff_derivFamily`
- direct_use_of_changed_declaration [exact]: `Ordinal.IsNormal.le_iff_eq` -> `Ordinal.IsNormal.le_apply`
- direct_use_of_changed_declaration [exact]: `Ordinal.IsNormal.lt_iff` -> `Ordinal.IsNormal.strictMono`
- direct_use_of_changed_declaration [exact]: `Ordinal.IsNormal.map_iSup` -> `Ordinal.IsNormal`
- direct_use_of_changed_declaration [exact]: `Ordinal.IsNormal.map_iSup_of_bddAbove` -> `Ordinal.IsNormal.map_iSup`
- direct_use_of_changed_declaration [exact]: `Ordinal.IsNormal.map_iSup_of_bddAbove` -> `Ordinal.IsNormal`
- direct_use_of_changed_declaration [exact]: `Ordinal.IsNormal.map_sSup` -> `Ordinal.IsNormal`
- direct_use_of_changed_declaration [exact]: `Ordinal.IsNormal.map_sSup_of_bddAbove` -> `Ordinal.IsNormal`
- direct_use_of_changed_declaration [exact]: `Ordinal.IsNormal.map_sSup_of_bddAbove` -> `Ordinal.IsNormal.map_sSup`
- direct_use_of_changed_declaration [exact]: `Ordinal.IsNormal.monotone` -> `Ordinal.IsNormal.strictMono`
- direct_use_of_changed_declaration [exact]: `Ordinal.IsNormal.monotone` -> `Order.IsNormal.monotone`
- direct_use_of_changed_declaration [exact]: `Ordinal.IsNormal.nfp_le_apply` -> `Ordinal.apply_lt_nfp`
- direct_use_of_changed_declaration [exact]: `Ordinal.IsNormal.strictMono` -> `Ordinal.IsNormal`
- direct_use_of_changed_declaration [exact]: `Ordinal.add_eq_right_iff_mul_omega0_le` -> `Ordinal.mem_range_deriv`
- direct_use_of_changed_declaration [exact]: `Ordinal.add_eq_right_iff_mul_omega0_le` -> `Ordinal.isNormal_add_right`
- direct_use_of_changed_declaration [exact]: `Ordinal.add_eq_right_iff_mul_omega0_le` -> `Ordinal.nfp_add_zero`
- direct_use_of_changed_declaration [exact]: `Ordinal.add_eq_right_iff_mul_omega0_le` -> `Order.IsNormal.monotone`
- direct_use_of_changed_declaration [exact]: `Ordinal.add_eq_right_iff_mul_omega0_le` -> `Ordinal.IsNormal.monotone`
- direct_use_of_changed_declaration [exact]: `Ordinal.add_le_right_iff_mul_omega0_le` -> `Ordinal.IsNormal.strictMono`
- direct_use_of_changed_declaration [exact]: `Ordinal.add_le_right_iff_mul_omega0_le` -> `Ordinal.isNormal_add_right`
- direct_use_of_changed_declaration [exact]: `Ordinal.add_le_right_iff_mul_omega0_le` -> `Ordinal.add_eq_right_iff_mul_omega0_le`
- direct_use_of_changed_declaration [exact]: `Ordinal.add_le_right_iff_mul_omega0_le` -> `Ordinal.IsNormal.le_apply`
- direct_use_of_changed_declaration [exact]: `Ordinal.add_omega0_opow` -> `Ordinal.isNormal_add_right`
- direct_use_of_changed_declaration [exact]: `Ordinal.add_omega0_opow` -> `Ordinal.isNormal_opow`
- direct_use_of_changed_declaration [exact]: `Ordinal.apply_le_nfp` -> `Ordinal.IsNormal.le_apply`
- direct_use_of_changed_declaration [exact]: `Ordinal.apply_le_nfp` -> `Order.IsNormal.monotone`
- direct_use_of_changed_declaration [exact]: `Ordinal.apply_le_nfp` -> `Ordinal.IsNormal.strictMono`
- direct_use_of_changed_declaration [exact]: `Ordinal.apply_le_nfp` -> `Ordinal.IsNormal.monotone`
- direct_use_of_changed_declaration [exact]: `Ordinal.apply_le_nfpFamily` -> `Ordinal.IsNormal.le_apply`
- direct_use_of_changed_declaration [exact]: `Ordinal.apply_le_nfpFamily` -> `Ordinal.IsNormal.strictMono`
- direct_use_of_changed_declaration [exact]: `Ordinal.apply_le_nfpFamily` -> `Ordinal.IsNormal.monotone`
- direct_use_of_changed_declaration [exact]: `Ordinal.apply_le_nfpFamily` -> `Ordinal.nfpFamily_fp`
- direct_use_of_changed_declaration [exact]: `Ordinal.apply_le_nfpFamily` -> `Order.IsNormal.monotone`
- direct_use_of_changed_declaration [exact]: `Ordinal.apply_lt_nfp` -> `Ordinal.apply_lt_nfpFamily_iff`
- direct_use_of_changed_declaration [exact]: `Ordinal.apply_lt_nfpFamily_iff` -> `Ordinal.IsNormal.strictMono`
- direct_use_of_changed_declaration [exact]: `Ordinal.apply_lt_nfpFamily_iff` -> `Ordinal.IsNormal.le_apply`
- direct_use_of_changed_declaration [exact]: `Ordinal.apply_omega0_of_isNormal` -> `Ordinal.IsNormal.map_iSup`
- direct_use_of_changed_declaration [exact]: `Ordinal.cof_add` -> `Ordinal.isNormal_add_right`
- direct_use_of_changed_declaration [exact]: `Ordinal.cof_add` -> `Ordinal.cof_eq_of_isNormal`
- direct_use_of_changed_declaration [exact]: `Ordinal.cof_eq_of_isNormal` -> `Ordinal.isFundamentalSequence_of_isNormal`
- direct_use_of_changed_declaration [exact]: `Ordinal.cof_le_of_isNormal` -> `Ordinal.cof_eq_of_isNormal`
- direct_use_of_changed_declaration [exact]: `Ordinal.cof_le_of_isNormal` -> `Ordinal.IsNormal.strictMono`
- direct_use_of_changed_declaration [exact]: `Ordinal.cof_omega` -> `Ordinal.cof_eq_of_isNormal`
- direct_use_of_changed_declaration [exact]: `Ordinal.cof_omega` -> `Ordinal.isNormal_omega`
- direct_use_of_changed_declaration [exact]: `Ordinal.cof_preOmega` -> `Ordinal.isNormal_preOmega`
- direct_use_of_changed_declaration [exact]: `Ordinal.cof_preOmega` -> `Ordinal.cof_eq_of_isNormal`
- direct_use_of_changed_declaration [exact]: `Ordinal.derivFamily_fp` -> `Ordinal.IsNormal.map_iSup`
- direct_use_of_changed_declaration [exact]: `Ordinal.derivFamily_fp` -> `Ordinal.nfpFamily_fp`
- direct_use_of_changed_declaration [exact]: `Ordinal.deriv_add_eq_mul_omega0_add` -> `Ordinal.add_eq_right_iff_mul_omega0_le`
- direct_use_of_changed_declaration [exact]: `Ordinal.deriv_add_eq_mul_omega0_add` -> `Ordinal.IsNormal`
- direct_use_of_changed_declaration [exact]: `Ordinal.deriv_add_eq_mul_omega0_add` -> `Ordinal.nfp_add_zero`
- direct_use_of_changed_declaration [exact]: `Ordinal.deriv_add_eq_mul_omega0_add` -> `Ordinal.isNormal_add_right`
- direct_use_of_changed_declaration [exact]: `Ordinal.deriv_fp` -> `Ordinal.derivFamily_fp`
- direct_use_of_changed_declaration [exact]: `Ordinal.deriv_mul_eq_opow_omega0_mul` -> `Ordinal.nfp_mul_opow_omega0_add`
- direct_use_of_changed_declaration [exact]: `Ordinal.deriv_mul_eq_opow_omega0_mul` -> `Ordinal.IsNormal`
- direct_use_of_changed_declaration [exact]: `Ordinal.deriv_mul_eq_opow_omega0_mul` -> `Ordinal.isNormal_mul_right`
- direct_use_of_changed_declaration [exact]: `Ordinal.enumOrd_isNormal_iff_isClosed` -> `Ordinal.IsNormal`
- direct_use_of_changed_declaration [exact]: `Ordinal.enumOrd_isNormal_iff_isClosed` -> `Ordinal.IsNormal.map_iSup`
- direct_use_of_changed_declaration [exact]: `Ordinal.enumOrd_isNormal_iff_isClosed` -> `Ordinal.IsNormal.monotone`
- direct_use_of_changed_declaration [exact]: `Ordinal.enumOrd_isNormal_iff_isClosed` -> `Order.IsNormal.monotone`
- direct_use_of_changed_declaration [exact]: `Ordinal.fp_iff_deriv` -> `Ordinal.mem_range_deriv`
- direct_use_of_changed_declaration [exact]: `Ordinal.fp_iff_derivFamily` -> `Ordinal.le_iff_derivFamily`
- direct_use_of_changed_declaration [exact]: `Ordinal.fp_iff_derivFamily` -> `Ordinal.IsNormal.le_apply`
- direct_use_of_changed_declaration [exact]: `Ordinal.fp_iff_derivFamily` -> `Ordinal.IsNormal.strictMono`
- direct_use_of_changed_declaration [exact]: `Ordinal.iSup_add_nat` -> `Ordinal.IsNormal.apply_omega0`
- direct_use_of_changed_declaration [exact]: `Ordinal.iSup_add_nat` -> `Ordinal.isNormal_add_right`
- direct_use_of_changed_declaration [exact]: `Ordinal.iSup_add_natCast` -> `Ordinal.isNormal_add_right`
- direct_use_of_changed_declaration [exact]: `Ordinal.iSup_add_natCast` -> `Ordinal.apply_omega0_of_isNormal`
- direct_use_of_changed_declaration [exact]: `Ordinal.iSup_mul_nat` -> `Ordinal.isNormal_mul_right`
- direct_use_of_changed_declaration [exact]: `Ordinal.iSup_mul_nat` -> `Ordinal.IsNormal.apply_omega0`
- direct_use_of_changed_declaration [exact]: `Ordinal.iSup_mul_natCast` -> `Ordinal.isNormal_mul_right`
- direct_use_of_changed_declaration [exact]: `Ordinal.iSup_mul_natCast` -> `Ordinal.apply_omega0_of_isNormal`
- direct_use_of_changed_declaration [exact]: `Ordinal.iSup_pow_natCast` -> `Ordinal.apply_omega0_of_isNormal`
- direct_use_of_changed_declaration [exact]: `Ordinal.iSup_pow_natCast` -> `Ordinal.isNormal_opow`
- direct_use_of_changed_declaration [exact]: `Ordinal.isFundamentalSequence_of_isNormal` -> `Ordinal.IsNormal.monotone`
- direct_use_of_changed_declaration [exact]: `Ordinal.isFundamentalSequence_of_isNormal` -> `Ordinal.IsNormal.strictMono`
- direct_use_of_changed_declaration [exact]: `Ordinal.isFundamentalSequence_of_isNormal` -> `Ordinal.IsNormal`
- direct_use_of_changed_declaration [exact]: `Ordinal.isFundamentalSequence_of_isNormal` -> `Order.IsNormal.monotone`
- direct_use_of_changed_declaration [exact]: `Ordinal.isNormal_omega` -> `Ordinal.isNormal_add_right`
- direct_use_of_changed_declaration [exact]: `Ordinal.isNormal_omega` -> `Ordinal.isNormal_preOmega`
- direct_use_of_changed_declaration [exact]: `Ordinal.isNormal_opow` -> `Ordinal.IsNormal`
- direct_use_of_changed_declaration [exact]: `Ordinal.isNormal_veblen` -> `Ordinal.isNormal_opow`
- direct_use_of_changed_declaration [exact]: `Ordinal.isNormal_veblenWith_zero` -> `Order.IsNormal.monotone`
- direct_use_of_changed_declaration [exact]: `Ordinal.isNormal_veblenWith_zero` -> `Ordinal.IsNormal.monotone`
- direct_use_of_changed_declaration [exact]: `Ordinal.isNormal_veblenWith_zero` -> `Ordinal.veblenWith_right_strictMono`
- direct_use_of_changed_declaration [exact]: `Ordinal.isNormal_veblen_zero` -> `Ordinal.isNormal_veblenWith_zero`
- direct_use_of_changed_declaration [exact]: `Ordinal.isNormal_veblen_zero` -> `Ordinal.isNormal_opow`
- direct_use_of_changed_declaration [exact]: `Ordinal.isSuccLimit_add` -> `Ordinal.isNormal_add_right`
- direct_use_of_changed_declaration [exact]: `Ordinal.isSuccLimit_mul` -> `Ordinal.isNormal_mul_right`
- direct_use_of_changed_declaration [exact]: `Ordinal.isSuccLimit_opow` -> `Ordinal.isNormal_opow`
- direct_use_of_changed_declaration [exact]: `Ordinal.le_iff_deriv` -> `Ordinal.le_iff_derivFamily`
- direct_use_of_changed_declaration [exact]: `Ordinal.le_iff_derivFamily` -> `Ordinal.IsNormal.monotone`
- direct_use_of_changed_declaration [exact]: `Ordinal.le_iff_derivFamily` -> `Ordinal.derivFamily_fp`
- direct_use_of_changed_declaration [exact]: `Ordinal.le_iff_derivFamily` -> `Order.IsNormal.monotone`
- direct_use_of_changed_declaration [exact]: `Ordinal.le_iff_derivFamily` -> `Ordinal.IsNormal.le_apply`
- direct_use_of_changed_declaration [exact]: `Ordinal.le_iff_derivFamily` -> `Ordinal.IsNormal.strictMono`
- direct_use_of_changed_declaration [exact]: `Ordinal.mem_range_deriv` -> `Ordinal.IsNormal.le_apply`
- direct_use_of_changed_declaration [exact]: `Ordinal.mem_range_deriv` -> `Ordinal.IsNormal.strictMono`
- direct_use_of_changed_declaration [exact]: `Ordinal.mem_range_deriv` -> `Ordinal.IsNormal.le_iff_deriv`
- direct_use_of_changed_declaration [exact]: `Ordinal.mem_range_deriv` -> `Ordinal.le_iff_deriv`
- direct_use_of_changed_declaration [exact]: `Ordinal.mem_range_gamma` -> `Ordinal.mem_range_deriv`
- direct_use_of_changed_declaration [exact]: `Ordinal.mem_range_gamma` -> `Ordinal.isNormal_veblen_zero`
- direct_use_of_changed_declaration [exact]: `Ordinal.mul_le_right_iff_opow_omega0_dvd` -> `Ordinal.IsNormal.strictMono`
- direct_use_of_changed_declaration [exact]: `Ordinal.mul_le_right_iff_opow_omega0_dvd` -> `Ordinal.isNormal_mul_right`
- direct_use_of_changed_declaration [exact]: `Ordinal.mul_le_right_iff_opow_omega0_dvd` -> `Ordinal.IsNormal.le_apply`
- direct_use_of_changed_declaration [exact]: `Ordinal.mul_lt_omega0_opow` -> `Ordinal.opow_lt_opow_iff_right`
- direct_use_of_changed_declaration [exact]: `Ordinal.mul_lt_omega0_opow` -> `Ordinal.isNormal_mul_right`
- direct_use_of_changed_declaration [exact]: `Ordinal.mul_lt_omega0_opow` -> `Ordinal.isNormal_opow`
- direct_use_of_changed_declaration [exact]: `Ordinal.nfpFamily_fp` -> `Ordinal.IsNormal.le_apply`
- direct_use_of_changed_declaration [exact]: `Ordinal.nfpFamily_fp` -> `Ordinal.IsNormal.strictMono`
- direct_use_of_changed_declaration [exact]: `Ordinal.nfpFamily_fp` -> `Ordinal.IsNormal.map_iSup`
- direct_use_of_changed_declaration [exact]: `Ordinal.nfp_add_zero` -> `Ordinal.iSup_mul_natCast`
- direct_use_of_changed_declaration [exact]: `Ordinal.nfp_fp` -> `Ordinal.nfpFamily_fp`
- direct_use_of_changed_declaration [exact]: `Ordinal.nfp_le_apply` -> `Ordinal.apply_lt_nfp`
- direct_use_of_changed_declaration [exact]: `Ordinal.nfp_mul_one` -> `Ordinal.iSup_pow_natCast`
- direct_use_of_changed_declaration [exact]: `Ordinal.nfp_mul_opow_omega0_add` -> `Ordinal.IsNormal.monotone`
- direct_use_of_changed_declaration [exact]: `Ordinal.nfp_mul_opow_omega0_add` -> `Ordinal.isNormal_mul_right`
- direct_use_of_changed_declaration [exact]: `Ordinal.nfp_mul_opow_omega0_add` -> `Order.IsNormal.monotone`
- direct_use_of_changed_declaration [exact]: `Ordinal.omega0_opow_epsilon` -> `Ordinal.deriv_fp`
- direct_use_of_changed_declaration [exact]: `Ordinal.omega0_opow_epsilon` -> `Ordinal.isNormal_opow`
- direct_use_of_changed_declaration [exact]: `Ordinal.op_eq_self_of_principal` -> `Ordinal.IsNormal.le_apply`
- direct_use_of_changed_declaration [exact]: `Ordinal.op_eq_self_of_principal` -> `Ordinal.IsNormal.strictMono`
- direct_use_of_changed_declaration [exact]: `Ordinal.op_eq_self_of_principal` -> `Ordinal.IsNormal.apply_of_isSuccLimit`
- direct_use_of_changed_declaration [exact]: `Ordinal.opow_add` -> `Ordinal.isNormal_opow`
- direct_use_of_changed_declaration [exact]: `Ordinal.opow_add` -> `Ordinal.isNormal_add_right`
- direct_use_of_changed_declaration [exact]: `Ordinal.opow_add` -> `Ordinal.isNormal_mul_right`
- direct_use_of_changed_declaration [exact]: `Ordinal.opow_le_opow_iff_right` -> `Ordinal.IsNormal.strictMono`
- direct_use_of_changed_declaration [exact]: `Ordinal.opow_le_opow_iff_right` -> `Ordinal.isNormal_opow`
- direct_use_of_changed_declaration [exact]: `Ordinal.opow_lt_opow_iff_right` -> `Ordinal.isNormal_opow`
- direct_use_of_changed_declaration [exact]: `Ordinal.opow_lt_opow_iff_right` -> `Ordinal.IsNormal.strictMono`
- direct_use_of_changed_declaration [exact]: `Ordinal.opow_mul` -> `Ordinal.isNormal_mul_right`
- direct_use_of_changed_declaration [exact]: `Ordinal.opow_mul` -> `Ordinal.isNormal_opow`
- direct_use_of_changed_declaration [exact]: `Ordinal.opow_mul` -> `Ordinal.opow_add`
- direct_use_of_changed_declaration [exact]: `Ordinal.opow_right_inj` -> `Ordinal.IsNormal.strictMono`
- direct_use_of_changed_declaration [exact]: `Ordinal.opow_right_inj` -> `Ordinal.isNormal_opow`
- direct_use_of_changed_declaration [exact]: `Ordinal.preOmega_omega0` -> `Ordinal.apply_omega0_of_isNormal`
- direct_use_of_changed_declaration [exact]: `Ordinal.preOmega_omega0` -> `Ordinal.isNormal_preOmega`
- direct_use_of_changed_declaration [exact]: `Ordinal.right_le_opow` -> `Ordinal.IsNormal.le_apply`
- direct_use_of_changed_declaration [exact]: `Ordinal.right_le_opow` -> `Ordinal.IsNormal.strictMono`
- direct_use_of_changed_declaration [exact]: `Ordinal.right_le_opow` -> `Ordinal.isNormal_opow`
- direct_use_of_changed_declaration [exact]: `Ordinal.veblenWith_right_strictMono` -> `Ordinal.IsNormal.strictMono`
- direct_use_of_changed_declaration [exact]: `Ordinal.veblen_gamma_zero` -> `Ordinal.deriv_fp`
- direct_use_of_changed_declaration [exact]: `Ordinal.veblen_gamma_zero` -> `Ordinal.isNormal_veblen_zero`

---

## The diff

```diff
diff --git a/Mathlib/Order/IsNormal.lean b/Mathlib/Order/IsNormal.lean
--- a/Mathlib/Order/IsNormal.lean
+++ b/Mathlib/Order/IsNormal.lean
@@ -50,6 +50,9 @@ namespace IsNormal
 section LinearOrder
 variable [LinearOrder α] [LinearOrder β] [LinearOrder γ]
 
+protected theorem monotone {f : α → β} (hf : IsNormal f) : Monotone f :=
+  hf.strictMono.monotone
+
 theorem isLUB_image_Iio_of_isSuccLimit {f : α → β} (hf : IsNormal f) {a : α} (ha : IsSuccLimit a) :
     IsLUB (f '' Iio a) (f a) := by
   refine ⟨?_, hf.2 ha⟩
diff --git a/Mathlib/SetTheory/Cardinal/Aleph.lean b/Mathlib/SetTheory/Cardinal/Aleph.lean
--- a/Mathlib/SetTheory/Cardinal/Aleph.lean
+++ b/Mathlib/SetTheory/Cardinal/Aleph.lean
@@ -158,7 +158,7 @@ theorem preOmega_le_of_forall_lt {o a : Ordinal} (ha : IsInitial a) (H : ∀ b <
   enumOrd_le_of_forall_lt ha H
 
 theorem isNormal_preOmega : IsNormal preOmega := by
-  rw [isNormal_iff_strictMono_limit]
+  rw [isNormal_iff]
   refine ⟨preOmega_strictMono, fun o ho a ha ↦
     (preOmega_le_of_forall_lt (isInitial_ord _) fun b hb ↦ ?_).trans (ord_card_le a)⟩
   rw [← (isInitial_ord _).card_lt_card, card_ord]
@@ -177,7 +177,7 @@ alias ⟨_, IsInitial.mem_range_preOmega⟩ := mem_range_preOmega_iff
 
 @[simp]
 theorem preOmega_omega0 : preOmega ω = ω := by
-  simp_rw [← isNormal_preOmega.apply_omega0, preOmega_natCast, iSup_natCast]
+  simp_rw [← apply_omega0_of_isNormal isNormal_preOmega, preOmega_natCast, iSup_natCast]
 
 @[simp]
 theorem omega0_le_preOmega_iff {x : Ordinal} : ω ≤ preOmega x ↔ ω ≤ x := by
@@ -247,7 +247,7 @@ theorem omega0_lt_omega_one : ω < ω₁ := by
 alias omega0_lt_omega1 := omega0_lt_omega_one
 
 theorem isNormal_omega : IsNormal omega :=
-  isNormal_preOmega.trans (isNormal_add_right _)
+  isNormal_preOmega.comp (isNormal_add_right _)
 
 @[simp]
 theorem range_omega : range omega = {x | ω ≤ x ∧ IsInitial x} := by
diff --git a/Mathlib/SetTheory/Cardinal/Cofinality.lean b/Mathlib/SetTheory/Cardinal/Cofinality.lean
--- a/Mathlib/SetTheory/Cardinal/Cofinality.lean
+++ b/Mathlib/SetTheory/Cardinal/Cofinality.lean
@@ -532,7 +532,7 @@ theorem cof_cof (a : Ordinal.{u}) : cof (cof a).ord = cof a := by
   obtain ⟨g, hg⟩ := exists_fundamental_sequence a.cof.ord
   exact ord_injective (hf.trans hg).cof_eq.symm
 
-protected theorem IsNormal.isFundamentalSequence {f : Ordinal.{u} → Ordinal.{u}} (hf : IsNormal f)
+theorem isFundamentalSequence_of_isNormal {f : Ordinal.{u} → Ordinal.{u}} (hf : IsNormal f)
     {a o} (ha : IsSuccLimit a) {g} (hg : IsFundamentalSequence a o g) :
     IsFundamentalSequence (f a) o fun b hb => f (g b hb) := by
   refine ⟨?_, @fun i j _ _ h => hf.strictMono (hg.2.1 _ _ h), ?_⟩
@@ -559,24 +559,33 @@ protected theorem IsNormal.isFundamentalSequence {f : Ordinal.{u} → Ordinal.{u
         hg.2.2]
     exact IsNormal.blsub_eq.{u, u} hf ha
 
-theorem IsNormal.cof_eq {f} (hf : IsNormal f) {a} (ha : IsSuccLimit a) : cof (f a) = cof a :=
+@[deprecated (since := "2025-12-25")]
+alias IsNormal.isFundamentalSequence := isFundamentalSequence_of_isNormal
+
+theorem cof_eq_of_isNormal {f} (hf : IsNormal f) {a} (ha : IsSuccLimit a) : cof (f a) = cof a :=
   let ⟨_, hg⟩ := exists_fundamental_sequence a
-  ord_injective (hf.isFundamentalSequence ha hg).cof_eq
+  ord_injective (isFundamentalSequence_of_isNormal hf ha hg).cof_eq
+
+@[deprecated (since := "2025-12-25")]
+alias IsNormal.cof_eq := cof_eq_of_isNormal
 
-theorem IsNormal.cof_le {f} (hf : IsNormal f) (a) : cof a ≤ cof (f a) := by
+theorem cof_le_of_isNormal {f} (hf : IsNormal f) (a) : cof a ≤ cof (f a) := by
   rcases zero_or_succ_or_isSuccLimit a with (rfl | ⟨b, rfl⟩ | ha)
   · rw [cof_zero]
     exact zero_le _
   · rw [cof_succ, Cardinal.one_le_iff_ne_zero, cof_ne_zero, ← pos_iff_ne_zero]
     exact (zero_le (f b)).trans_lt (hf.strictMono (lt_succ b))
-  · rw [hf.cof_eq ha]
+  · rw [cof_eq_of_isNormal hf ha]
+
+@[deprecated (since := "2025-12-25")]
+alias IsNormal.cof_le := cof_le_of_isNormal
 
 @[simp]
 theorem cof_add (a b : Ordinal) : b ≠ 0 → cof (a + b) = cof b := fun h => by
   rcases zero_or_succ_or_isSuccLimit b with (rfl | ⟨c, rfl⟩ | hb)
   · contradiction
   · rw [add_succ, cof_succ, cof_succ]
-  · exact (isNormal_add_right a).cof_eq hb
+  · exact cof_eq_of_isNormal (isNormal_add_right a) hb
 
 theorem aleph0_le_cof {o} : ℵ₀ ≤ cof o ↔ IsSuccLimit o := by
   rcases zero_or_succ_or_isSuccLimit o with (rfl | ⟨o, rfl⟩ | l)
@@ -599,11 +608,11 @@ theorem aleph0_le_cof {o} : ℵ₀ ≤ cof o ↔ IsSuccLimit o := by
 theorem cof_preOmega {o : Ordinal} (ho : IsSuccPrelimit o) : (preOmega o).cof = o.cof := by
   by_cases h : IsMin o
   · simp [h.eq_bot]
-  · exact isNormal_preOmega.cof_eq ⟨h, ho⟩
+  · exact cof_eq_of_isNormal isNormal_preOmega ⟨h, ho⟩
 
 @[simp]
 theorem cof_omega {o : Ordinal} (ho : IsSuccLimit o) : (ω_ o).cof = o.cof :=
-  isNormal_omega.cof_eq ho
+  cof_eq_of_isNormal isNormal_omega ho
 
 @[simp]
 theorem cof_omega0 : cof ω = ℵ₀ :=
diff --git a/Mathlib/SetTheory/Ordinal/Arithmetic.lean b/Mathlib/SetTheory/Ordinal/Arithmetic.lean
--- a/Mathlib/SetTheory/Ordinal/Arithmetic.lean
+++ b/Mathlib/SetTheory/Ordinal/Arithmetic.lean
@@ -29,20 +29,19 @@ successor ordinals and limit ordinals, in `limitRecOn`.
 * `o₁ * o₂` is the lexicographic order on `o₂ × o₁`.
 * `o₁ / o₂` is the ordinal `o` such that `o₁ = o₂ * o + o'` with `o' < o₂`. We also define the
   divisibility predicate, and a modulo operation.
-* `Order.succ o = o + 1` is the successor of `o`.
-* `pred o` if the predecessor of `o`. If `o` is not a successor, we set `pred o = o`.
+* `limitRecOn` is the main induction principle of ordinals: if one can prove a property by
+  induction at successor ordinals and at limit ordinals, then it holds for all ordinals.
 
 We discuss the properties of casts of natural numbers of and of `ω` with respect to these
 operations.
 
-Some properties of the operations are also used to discuss general tools on ordinals:
+Note that some basic functions and properties of ordinals have been generalized to other orders:
 
+* `Order.succ o = o + 1` is the successor of `o`.
 * `Order.IsSuccLimit o`: an ordinal is a limit ordinal if it is neither `0` nor a successor.
-* `limitRecOn` is the main induction principle of ordinals: if one can prove a property by
-  induction at successor ordinals and at limit ordinals, then it holds for all ordinals.
-* `IsNormal`: a function `f : Ordinal → Ordinal` satisfies `IsNormal` if it is strictly increasing
-  and order-continuous, i.e., the image `f o` of a limit ordinal `o` is the sup of `f a` for
-  `a < o`.
+* `Order.IsNormal`: a function `f : Ordinal → Ordinal` is normal if it is strictly increasing and
+  order-continuous, i.e., the image `f o` of a limit ordinal `o` is the supremum of `f a`
+  for `a < o`.
 
 Various other basic arithmetic results are given in `Principal.lean` instead.
 -/
@@ -348,79 +347,101 @@ theorem lift_pred (o : Ordinal.{v}) : lift.{u} (pred o) = pred (lift.{u} o) := b
   · simp
   · rwa [ho.ordinalPred_eq, eq_comm, pred_eq_iff_isSuccPrelimit, isSuccPrelimit_lift]
 
-/-! ### Normal ordinal functions -/
-
 /-- A normal ordinal function is a strictly increasing function which is
   order-continuous, i.e., the image `f o` of a limit ordinal `o` is the sup of `f a` for
-  `a < o`.
-
-  Todo: deprecate this in favor of `Order.IsNormal`. -/
-def IsNormal (f : Ordinal → Ordinal) : Prop :=
+  `a < o`. -/
+@[deprecated Order.IsNormal (since := "2025-12-25")]
+protected def IsNormal (f : Ordinal → Ordinal) : Prop :=
   Order.IsNormal f
 
-theorem IsNormal.limit_le {f} (H : IsNormal f) :
+set_option linter.deprecated false in
+@[deprecated IsNormal.le_iff_forall_le (since := "2025-12-25")]
+theorem IsNormal.limit_le {f} (H : Ordinal.IsNormal f) :
     ∀ {o}, IsSuccLimit o → ∀ {a}, f o ≤ a ↔ ∀ b < o, f b ≤ a :=
   H.le_iff_forall_le
 
-theorem IsNormal.limit_lt {f} (H : IsNormal f) {o} (h : IsSuccLimit o) {a} :
+set_option linter.deprecated false in
+@[deprecated IsNormal.lt_iff_exists_lt (since := "2025-12-25")]
+theorem IsNormal.limit_lt {f} (H : Ordinal.IsNormal f) {o} (h : IsSuccLimit o) {a} :
     a < f o ↔ ∃ b < o, a < f b :=
   H.lt_iff_exists_lt h
 
-theorem IsNormal.strictMono {f} (H : IsNormal f) : StrictMono f :=
+set_option linter.deprecated false in
+@[deprecated Order.IsNormal.strictMono (since := "2025-12-25")]
+theorem IsNormal.strictMono {f} (H : Ordinal.IsNormal f) : StrictMono f :=
   Order.IsNormal.strictMono H
 
-theorem IsNormal.monotone {f} (H : IsNormal f) : Monotone f :=
+set_option linter.deprecated false in
+@[deprecated Order.IsNormal.strictMono (since := "2025-12-25")]
+theorem IsNormal.monotone {f} (H : Ordinal.IsNormal f) : Monotone f :=
   H.strictMono.monotone
 
+set_option linter.deprecated false in
+@[deprecated isNormal_iff (since := "2025-12-25")]
 theorem isNormal_iff_strictMono_limit (f : Ordinal → Ordinal) :
-    IsNormal f ↔ StrictMono f ∧ ∀ o, IsSuccLimit o → ∀ a, (∀ b < o, f b ≤ a) → f o ≤ a :=
+    Ordinal.IsNormal f ↔ StrictMono f ∧ ∀ o, IsSuccLimit o → ∀ a, (∀ b < o, f b ≤ a) → f o ≤ a :=
   isNormal_iff
 
-theorem IsNormal.lt_iff {f} (H : IsNormal f) {a b} : f a < f b ↔ a < b :=
-  StrictMono.lt_iff_lt <| H.strictMono
+set_option linter.deprecated false in
+@[deprecated StrictMono.lt_iff_lt (since := "2025-12-25")]
+theorem IsNormal.lt_iff {f} (H : Ordinal.IsNormal f) {a b} : f a < f b ↔ a < b :=
+  H.strictMono.lt_iff_lt
 
-theorem IsNormal.le_iff {f} (H : IsNormal f) {a b} : f a ≤ f b ↔ a ≤ b :=
-  le_iff_le_iff_lt_iff_lt.2 H.lt_iff
+set_option linter.deprecated false in
+@[deprecated StrictMono.le_iff_le (since := "2025-12-25")]
+theorem IsNormal.le_iff {f} (H : Ordinal.IsNormal f) {a b} : f a ≤ f b ↔ a ≤ b :=
+  H.strictMono.le_iff_le
 
-theorem IsNormal.inj {f} (H : IsNormal f) {a b} : f a = f b ↔ a = b := by
-  simp only [le_antisymm_iff, H.le_iff]
+set_option linter.deprecated false in
+@[deprecated Injective.eq_iff (since := "2025-12-25")]
+theorem IsNormal.inj {f} (H : Ordinal.IsNormal f) {a b} : f a = f b ↔ a = b :=
+  H.strictMono.injective.eq_iff
 
-theorem IsNormal.id_le {f} (H : IsNormal f) : id ≤ f :=
+set_option linter.deprecated false in
+@[deprecated StrictMono.id_le (since := "2025-12-25")]
+theorem IsNormal.id_le {f} (H : Ordinal.IsNormal f) : id ≤ f :=
   H.strictMono.id_le
 
-theorem IsNormal.le_apply {f} (H : IsNormal f) {a} : a ≤ f a :=
+set_option linter.deprecated false in
+@[deprecated StrictMono.le_apply (since := "2025-12-25")]
+theorem IsNormal.le_apply {f} (H : Ordinal.IsNormal f) {a} : a ≤ f a :=
   H.strictMono.le_apply
 
-theorem IsNormal.le_iff_eq {f} (H : IsNormal f) {a} : f a ≤ a ↔ f a = a :=
+set_option linter.deprecated false in
+@[deprecated StrictMono.le_apply (since := "2025-12-25")]
+theorem IsNormal.le_iff_eq {f} (H : Ordinal.IsNormal f) {a} : f a ≤ a ↔ f a = a :=
   H.le_apply.ge_iff_eq'
 
-theorem IsNormal.le_set {f o} (H : IsNormal f) (p : Set Ordinal) (p0 : p.Nonempty) (b)
-    (H₂ : ∀ o, b ≤ o ↔ ∀ a ∈ p, a ≤ o) : f b ≤ o ↔ ∀ a ∈ p, f a ≤ o :=
-  ⟨fun h _ pa => (H.le_iff.2 ((H₂ _).1 le_rfl _ pa)).trans h, fun h => by
-    induction b using limitRecOn with
-    | zero =>
-      obtain ⟨x, px⟩ := p0
-      rw [nonpos_iff_eq_zero.1 ((H₂ _).1 (zero_le _) _ px)] at px
-      exact h _ px
-    | succ S _ =>
-      rcases not_forall₂.1 (mt (H₂ S).2 <| (lt_succ S).not_ge) with ⟨a, h₁, h₂⟩
-      exact (H.le_iff.2 <| succ_le_of_lt <| not_le.1 h₂).trans (h _ h₁)
-    | limit S L _ =>
-      refine (H.le_iff_forall_le L).2 fun a h' => ?_
-      rcases not_forall₂.1 (mt (H₂ a).2 h'.not_ge) with ⟨b, h₁, h₂⟩
-      exact (H.le_iff.2 <| (not_le.1 h₂).le).trans (h _ h₁)⟩
-
-theorem IsNormal.le_set' {f o} (H : IsNormal f) (p : Set α) (p0 : p.Nonempty) (g : α → Ordinal) (b)
-    (H₂ : ∀ o, b ≤ o ↔ ∀ a ∈ p, g a ≤ o) : f b ≤ o ↔ ∀ a ∈ p, f (g a) ≤ o := by
+set_option linter.deprecated false in
+@[deprecated IsNormal.map_isLUB (since := "2025-12-25")]
+theorem IsNormal.le_set {f o} (H : Ordinal.IsNormal f) (p : Set Ordinal) (p0 : p.Nonempty) (b)
+    (H₂ : ∀ o, b ≤ o ↔ ∀ a ∈ p, a ≤ o) : f b ≤ o ↔ ∀ a ∈ p, f a ≤ o := by
+  have hp := H.map_isLUB ⟨(H₂ b).1 le_rfl, fun a ↦ (H₂ _).2⟩ p0
+  refine ⟨fun hb a ha ↦ (hp.1 (mem_image_of_mem _ ha)).trans hb, fun H ↦ hp.2 ?_⟩
+  simpa [mem_upperBounds]
+
+set_option linter.deprecated false in
+@[deprecated IsNormal.map_isLUB (since := "2025-12-25")]
+theorem IsNormal.le_set' {f o} (H : Ordinal.IsNormal f) (p : Set α) (p0 : p.Nonempty)
+    (g : α → Ordinal) (b) (H₂ : ∀ o, b ≤ o ↔ ∀ a ∈ p, g a ≤ o) :
+    f b ≤ o ↔ ∀ a ∈ p, f (g a) ≤ o := by
   simpa [H₂] using H.le_set (g '' p) (p0.image g) b
 
-theorem IsNormal.refl : IsNormal id :=
+set_option linter.deprecated false in
+@[deprecated IsNormal.id (since := "2025-12-25")]
+theorem IsNormal.refl : Ordinal.IsNormal id :=
   .id
 
-theorem IsNormal.trans {f g} (H₁ : IsNormal f) (H₂ : IsNormal g) : IsNormal (f ∘ g) :=
+set_option linter.deprecated false in
+@[deprecated IsNormal.comp (since := "2025-12-25")]
+theorem IsNormal.trans {f g} (H₁ : Ordinal.IsNormal f) (H₂ : Ordinal.IsNormal g) :
+    IsNormal (f ∘ g) :=
   H₁.comp H₂
 
-theorem IsNormal.isSuccLimit {f} (H : IsNormal f) {o} (ho : IsSuccLimit o) : IsSuccLimit (f o) :=
+set_option linter.deprecated false in
+@[deprecated IsNormal.map_isSuccLimit (since := "2025-12-25")]
+theorem IsNormal.isSuccLimit {f} (H : Ordinal.IsNormal f) {o} (ho : IsSuccLimit o) :
+    IsSuccLimit (f o) :=
   H.map_isSuccLimit ho
 
 /-! ### Subtraction on ordinals -/
@@ -524,11 +545,11 @@ theorem add_le_iff_of_isSuccLimit {a b c : Ordinal} (hb : IsSuccLimit b) :
 alias add_le_of_limit := add_le_iff_of_isSuccLimit
 
 theorem isNormal_add_right (a : Ordinal) : IsNormal (a + ·) := by
-  rw [isNormal_iff_strictMono_limit]
+  rw [isNormal_iff]
   exact ⟨add_right_strictMono, fun _ l _ ↦ (add_le_iff_of_isSuccLimit l).2⟩
 
 theorem isSuccLimit_add (a : Ordinal) {b : Ordinal} : IsSuccLimit b → IsSuccLimit (a + b) :=
-  (isNormal_add_right a).isSuccLimit
+  (isNormal_add_right a).map_isSuccLimit
 
 @[deprecated (since := "2025-07-09")]
 alias isLimit_add := isSuccLimit_add
@@ -707,7 +728,7 @@ theorem mul_le_iff_of_isSuccLimit {a b c : Ordinal} (h : IsSuccLimit b) :
 alias mul_le_of_limit := mul_le_iff_of_isSuccLimit
 
 theorem isNormal_mul_right {a : Ordinal} (h : 0 < a) : IsNormal (a * ·) := by
-  refine IsNormal.of_succ_lt (fun b ↦ ?_) fun hb ↦ ?_
+  refine .of_succ_lt (fun b ↦ ?_) fun hb ↦ ?_
   · simpa [mul_succ] using (add_lt_add_iff_left (a * b)).2 h
   · simpa [IsLUB, IsLeast, upperBounds, lowerBounds, mul_le_iff_of_isSuccLimit hb] using
       fun c hc ↦ mul_le_mul_right hc.le a
@@ -751,7 +772,7 @@ theorem mul_right_inj {a b c : Ordinal} (a0 : 0 < a) : a * b = a * c ↔ b = c :
   mul_left_cancel_iff_of_pos a0
 
 theorem isSuccLimit_mul {a b : Ordinal} (a0 : 0 < a) : IsSuccLimit b → IsSuccLimit (a * b) :=
-  (isNormal_mul_right a0).isSuccLimit
+  (isNormal_mul_right a0).map_isSuccLimit
 
 @[deprecated (since := "2025-07-09")]
 alias isLimit_mul := isSuccLimit_mul
diff --git a/Mathlib/SetTheory/Ordinal/Enum.lean b/Mathlib/SetTheory/Ordinal/Enum.lean
--- a/Mathlib/SetTheory/Ordinal/Enum.lean
+++ b/Mathlib/SetTheory/Ordinal/Enum.lean
@@ -128,7 +128,7 @@ theorem enumOrd_range {f : Ordinal → Ordinal} (hf : StrictMono f) : enumOrd (r
 See also `enumOrd_isNormal_iff_isClosed`. -/
 theorem isNormal_enumOrd (H : ∀ t ⊆ s, t.Nonempty → BddAbove t → sSup t ∈ s) (hs : ¬ BddAbove s) :
     IsNormal (enumOrd s) := by
-  refine (isNormal_iff_strictMono_limit _).2 ⟨enumOrd_strictMono hs, fun o ho a ha ↦ ?_⟩
+  refine isNormal_iff.2 ⟨enumOrd_strictMono hs, fun o ho a ha ↦ ?_⟩
   trans ⨆ b : Iio o, enumOrd s b
   · refine enumOrd_le_of_forall_lt ?_ (fun b hb ↦ (enumOrd_strictMono hs (lt_succ b)).trans_le ?_)
     · have : Nonempty (Iio o) := ⟨0, ho.bot_lt⟩
diff --git a/Mathlib/SetTheory/Ordinal/Exponential.lean b/Mathlib/SetTheory/Ordinal/Exponential.lean
--- a/Mathlib/SetTheory/Ordinal/Exponential.lean
+++ b/Mathlib/SetTheory/Ordinal/Exponential.lean
@@ -7,7 +7,8 @@ module
 
 public import Mathlib.SetTheory.Ordinal.Family
 
-/-! # Ordinal exponential
+/-!
+# Ordinal exponential
 
 In this file we define the power function and the logarithm function on ordinals. The two are
 related by the lemma `Ordinal.opow_le_iff_le_log : b ^ c ≤ x ↔ c ≤ log b x` for nontrivial inputs
@@ -118,26 +119,26 @@ theorem opow_natCast (a : Ordinal) (n : ℕ) : a ^ (n : Ordinal) = a ^ n := by
   | zero => rw [Nat.cast_zero, opow_zero, pow_zero]
   | succ n IH => rw [Nat.cast_succ, add_one_eq_succ, opow_succ, pow_succ, IH]
 
-theorem isNormal_opow {a : Ordinal} (h : 1 < a) : IsNormal (a ^ ·) := by
+theorem isNormal_opow {a : Ordinal} (h : 1 < a) : IsNormal (a ^ · : Ordinal → Ordinal) := by
   have ha : 0 < a := zero_lt_one.trans h
   refine IsNormal.of_succ_lt ?_ fun hl ↦ ?_
   · simpa only [mul_one, opow_succ] using fun b ↦ mul_lt_mul_of_pos_left h (opow_pos b ha)
   · simp [IsLUB, IsLeast, upperBounds, lowerBounds, ← opow_le_of_isSuccLimit ha.ne' hl]
 
 @[simp]
 theorem opow_lt_opow_iff_right {a b c : Ordinal} (a1 : 1 < a) : a ^ b < a ^ c ↔ b < c :=
-  (isNormal_opow a1).lt_iff
+  (isNormal_opow a1).strictMono.lt_iff_lt
 
 @[simp]
 theorem opow_le_opow_iff_right {a b c : Ordinal} (a1 : 1 < a) : a ^ b ≤ a ^ c ↔ b ≤ c :=
-  (isNormal_opow a1).le_iff
+  (isNormal_opow a1).strictMono.le_iff_le
 
 @[simp]
 theorem opow_right_inj {a b c : Ordinal} (a1 : 1 < a) : a ^ b = a ^ c ↔ b = c :=
-  (isNormal_opow a1).inj
+  (isNormal_opow a1).strictMono.injective.eq_iff
 
 theorem isSuccLimit_opow {a b : Ordinal} (a1 : 1 < a) : IsSuccLimit b → IsSuccLimit (a ^ b) :=
-  (isNormal_opow a1).isSuccLimit
+  (isNormal_opow a1).map_isSuccLimit
 
 @[deprecated (since := "2025-07-08")]
 alias isLimit_opow := isSuccLimit_opow
@@ -188,34 +189,28 @@ theorem left_lt_opow {a b : Ordinal} (ha : 1 < a) (hb : 1 < b) : a < a ^ b := by
   rwa [opow_lt_opow_iff_right ha]
 
 theorem right_le_opow {a : Ordinal} (b : Ordinal) (a1 : 1 < a) : b ≤ a ^ b :=
-  (isNormal_opow a1).le_apply
+  (isNormal_opow a1).strictMono.le_apply
 
 theorem opow_lt_opow_left_of_succ {a b c : Ordinal} (ab : a < b) : a ^ succ c < b ^ succ c := by
   rw [opow_succ, opow_succ]
   exact mul_lt_mul_of_le_of_lt_of_nonneg_of_pos (by gcongr) ab (zero_le _) (opow_pos _ ab.bot_lt)
 
 theorem opow_add (a b c : Ordinal) : a ^ (b + c) = a ^ b * a ^ c := by
-  rcases eq_or_ne a 0 with (rfl | a0)
-  · rcases eq_or_ne c 0 with (rfl | c0)
-    · simp
-    have : b + c ≠ 0 := ((pos_iff_ne_zero.2 c0).trans_le le_add_self).ne'
-    simp only [zero_opow c0, zero_opow this, mul_zero]
-  rcases eq_or_lt_of_le (one_le_iff_ne_zero.2 a0) with (rfl | a1)
-  · simp only [one_opow, mul_one]
+  obtain rfl | ha := eq_zero_or_pos a
+  · obtain rfl | hc := eq_zero_or_pos c; · simp
+    have : b + c ≠ 0 := (hc.trans_le le_add_self).ne'
+    rw [zero_opow hc.ne', zero_opow, mul_zero]
+    exact (hc.trans_le le_add_self).ne'
+  obtain rfl | ha' := (one_le_iff_ne_zero.2 ha.ne').eq_or_lt; · simp
   induction c using limitRecOn with
   | zero => simp
-  | succ c IH =>
-    rw [add_succ, opow_succ, IH, opow_succ, mul_assoc]
+  | succ c IH => rw [add_succ, opow_succ, IH, opow_succ, mul_assoc]
   | limit c l IH =>
-    refine
-      eq_of_forall_ge_iff fun d =>
-        (((isNormal_opow a1).trans (isNormal_add_right b)).limit_le l).trans ?_
-    dsimp only [Function.comp_def]
-    simp +contextual only [IH]
-    exact
-      (((isNormal_mul_right <| opow_pos b (pos_iff_ne_zero.2 a0)).trans
-              (isNormal_opow a1)).limit_le
-          l).symm
+    refine eq_of_forall_ge_iff fun d ↦
+      (((isNormal_opow ha').comp (isNormal_add_right b)).le_iff_forall_le l).trans ?_
+    simpa +contextual [IH] using
+      (((isNormal_mul_right <| opow_pos b (pos_iff_ne_zero.2 ha.ne')).comp
+        (isNormal_opow ha')).le_iff_forall_le l).symm
 
 theorem opow_one_add (a b : Ordinal) : a ^ (1 + b) = a * a ^ b := by rw [opow_add, opow_one]
 
@@ -230,28 +225,18 @@ theorem opow_dvd_opow_iff {a b c : Ordinal} (a1 : 1 < a) : a ^ b ∣ a ^ c ↔ b
     opow_dvd_opow _⟩
 
 theorem opow_mul (a b c : Ordinal) : a ^ (b * c) = (a ^ b) ^ c := by
-  by_cases b0 : b = 0; · simp only [b0, zero_mul, opow_zero, one_opow]
-  by_cases a0 : a = 0
-  · subst a
-    by_cases c0 : c = 0
-    · simp only [c0, mul_zero, opow_zero]
-    simp only [zero_opow b0, zero_opow c0, zero_opow (mul_ne_zero b0 c0)]
-  rcases eq_or_lt_of_le (one_le_iff_ne_zero.2 a0) with a1 | a1
-  · subst a1
-    simp only [one_opow]
+  obtain rfl | hb := eq_zero_or_pos b; · simp
+  obtain rfl | ha := eq_or_ne a 0
+  · have := hb.ne'
+    by_cases c = 0 <;> simp_all
+  obtain rfl | ha' := (one_le_iff_ne_zero.2 ha).eq_or_lt; · simp
   induction c using limitRecOn with
-  | zero => simp only [mul_zero, opow_zero]
-  | succ c IH =>
-    rw [mul_succ, opow_add, IH, opow_succ]
+  | zero => simp
+  | succ c IH => rw [mul_succ, opow_add, IH, opow_succ]
   | limit c l IH =>
-    refine
-      eq_of_forall_ge_iff fun d =>
-        (((isNormal_opow a1).trans (isNormal_mul_right (pos_iff_ne_zero.2 b0))).limit_le
-              l).trans
-          ?_
-    dsimp only [Function.comp_def]
-    simp +contextual only [IH]
-    exact (opow_le_of_isSuccLimit (opow_ne_zero _ a0) l).symm
+    refine eq_of_forall_ge_iff fun d ↦
+      (((isNormal_opow ha').comp (isNormal_mul_right hb)).le_iff_forall_le l).trans ?_
+    simpa +contextual [IH] using (opow_le_of_isSuccLimit (opow_ne_zero _ ha) l).symm
 
 theorem opow_mul_add_pos {b v : Ordinal} (hb : b ≠ 0) (u : Ordinal) (hv : v ≠ 0) (w : Ordinal) :
     0 < b ^ u * v + w :=
@@ -532,14 +517,17 @@ theorem natCast_opow (m : ℕ) : ∀ n : ℕ, ↑(m ^ n : ℕ) = (m : Ordinal) ^
   | n + 1 => by
     rw [pow_succ, natCast_mul, natCast_opow m n, Nat.cast_succ, add_one_eq_succ, opow_succ]
 
-theorem iSup_pow {o : Ordinal} (ho : 0 < o) : ⨆ n : ℕ, o ^ n = o ^ ω := by
+theorem iSup_pow_natCast {o : Ordinal} (ho : 0 < o) : ⨆ n : ℕ, o ^ n = o ^ ω := by
   simp_rw [← opow_natCast]
   rcases (one_le_iff_pos.2 ho).lt_or_eq with ho₁ | rfl
-  · exact (isNormal_opow ho₁).apply_omega0
+  · exact apply_omega0_of_isNormal (isNormal_opow ho₁)
   · rw [one_opow]
     refine le_antisymm (Ordinal.iSup_le fun n => by rw [one_opow]) ?_
     exact_mod_cast Ordinal.le_iSup _ 0
 
+@[deprecated (since := "2025-12-25")]
+alias iSup_pow := iSup_pow_natCast
+
 end Ordinal
 
 -- Porting note (https://github.com/leanprover-community/mathlib4/issues/11215): TODO: Port this meta code.
diff --git a/Mathlib/SetTheory/Ordinal/Family.lean b/Mathlib/SetTheory/Ordinal/Family.lean
--- a/Mathlib/SetTheory/Ordinal/Family.lean
+++ b/Mathlib/SetTheory/Ordinal/Family.lean
@@ -238,33 +238,40 @@ theorem unbounded_range_of_le_iSup {α β : Type u} (r : α → α → Prop) [Is
       (Ordinal.iSup_le fun y => ((typein_lt_typein r).2 <| hx _ <| mem_range_self y).le)
       (typein_lt_type r x)
 
-theorem IsNormal.map_iSup_of_bddAbove {f : Ordinal.{u} → Ordinal.{v}} (H : IsNormal f)
+set_option linter.deprecated false in
+@[deprecated Order.IsNormal.map_iSup (since := "2025-12-25")]
+theorem IsNormal.map_iSup_of_bddAbove {f : Ordinal.{u} → Ordinal.{v}} (H : Ordinal.IsNormal f)
     {ι : Type*} (g : ι → Ordinal.{u}) (hg : BddAbove (range g))
     [Nonempty ι] : f (⨆ i, g i) = ⨆ i, f (g i) :=
   Order.IsNormal.map_iSup H hg
 
-theorem IsNormal.map_iSup {f : Ordinal.{u} → Ordinal.{v}} (H : IsNormal f)
+set_option linter.deprecated false in
+@[deprecated Order.IsNormal.map_iSup (since := "2025-12-25")]
+theorem IsNormal.map_iSup {f : Ordinal.{u} → Ordinal.{v}} (H : Ordinal.IsNormal f)
     {ι : Type w} (g : ι → Ordinal.{u}) [Small.{u} ι] [Nonempty ι] :
     f (⨆ i, g i) = ⨆ i, f (g i) :=
-  H.map_iSup_of_bddAbove g (bddAbove_of_small _)
+  Order.IsNormal.map_iSup H (bddAbove_of_small _)
 
-theorem IsNormal.map_sSup_of_bddAbove {f : Ordinal.{u} → Ordinal.{v}} (H : IsNormal f)
-    {s : Set Ordinal.{u}} (hs : BddAbove s) (hn : s.Nonempty) : f (sSup s) = sSup (f '' s) := by
-  have := hn.to_subtype
-  rw [sSup_eq_iSup', sSup_image', H.map_iSup_of_bddAbove]
-  rwa [Subtype.range_coe_subtype, setOf_mem_eq]
+set_option linter.deprecated false in
+@[deprecated Order.IsNormal.map_sSup (since := "2025-12-25")]
+theorem IsNormal.map_sSup_of_bddAbove {f : Ordinal.{u} → Ordinal.{v}} (H : Ordinal.IsNormal f)
+    {s : Set Ordinal.{u}} (hs : BddAbove s) (hn : s.Nonempty) : f (sSup s) = sSup (f '' s) :=
+  Order.IsNormal.map_sSup H hn hs
 
+set_option linter.deprecated false in
+@[deprecated Order.IsNormal.map_sSup (since := "2025-12-25")]
 theorem IsNormal.map_sSup {f : Ordinal.{u} → Ordinal.{v}} (H : IsNormal f)
     {s : Set Ordinal.{u}} (hn : s.Nonempty) [Small.{u} s] : f (sSup s) = sSup (f '' s) :=
-  H.map_sSup_of_bddAbove (bddAbove_of_small s) hn
+  Order.IsNormal.map_sSup H hn (bddAbove_of_small _)
 
-theorem IsNormal.apply_of_isSuccLimit {f : Ordinal.{u} → Ordinal.{v}} (H : IsNormal f) {o : Ordinal}
-    (ho : IsSuccLimit o) : f o = ⨆ a : Iio o, f a := by
-  have : Nonempty (Iio o) := ⟨0, ho.bot_lt⟩
-  rw [← H.map_iSup, ho.iSup_Iio]
+set_option linter.deprecated false in
+@[deprecated Order.IsNormal.apply_of_isSuccLimit (since := "2025-12-25")]
+theorem IsNormal.apply_of_isSuccLimit {f : Ordinal.{u} → Ordinal.{v}} (H : Ordinal.IsNormal f)
+    {o : Ordinal} (ho : IsSuccLimit o) : f o = ⨆ a : Iio o, f a :=
+  Order.IsNormal.apply_of_isSuccLimit H ho
 
 @[deprecated (since := "2025-07-08")]
-alias IsNormal.apply_of_isLimit := IsNormal.apply_of_isSuccLimit
+alias IsNormal.apply_of_isLimit := Order.IsNormal.apply_of_isSuccLimit
 
 theorem sSup_ord (s : Set Cardinal) : (sSup s).ord = sSup (ord '' s) := by
   obtain rfl | hn := s.eq_empty_or_nonempty
@@ -373,7 +380,8 @@ theorem IsNormal.bsup {f : Ordinal → Ordinal} (H : IsNormal f) {o : Ordinal} :
     ∀ (g : ∀ a < o, Ordinal), o ≠ 0 → f (bsup o g) = bsup o fun a h => f (g a h) :=
   inductionOn o fun α r _ g h => by
     haveI := type_ne_zero_iff_nonempty.1 h
-    rw [← iSup'_eq_bsup r, IsNormal.map_iSup H, ← iSup'_eq_bsup r] <;> rfl
+    rw [← iSup'_eq_bsup r, Order.IsNormal.map_iSup H (bddAbove_of_small _), ← iSup'_eq_bsup r] <;>
+      rfl
 
 theorem lt_bsup_of_ne_bsup {o : Ordinal.{u}} {f : ∀ a < o, Ordinal.{max u v}} :
     (∀ i h, f i h ≠ bsup.{_, v} o f) ↔ ∀ i h, f i h < bsup.{_, v} o f :=
@@ -801,6 +809,7 @@ theorem isNormal_iff_lt_succ_and_blsub_eq {f : Ordinal.{u} → Ordinal.{max u v}
   constructor <;> intro H o ho <;> have := H o ho <;>
     rwa [← bsup_eq_blsub_of_lt_succ_limit ho fun a _ => h a] at *
 
+@[deprecated IsNormal.ext (since := "2025-12-25")]
 theorem IsNormal.eq_iff_zero_and_succ {f g : Ordinal.{u} → Ordinal.{u}} (hf : IsNormal f)
     (hg : IsNormal g) : f = g ↔ f 0 = g 0 ∧ ∀ a, f a = g a → f (succ a) = g (succ a) :=
   Order.IsNormal.ext hf hg
@@ -853,18 +862,28 @@ namespace Ordinal
 theorem iSup_natCast : iSup Nat.cast = ω :=
   (Ordinal.iSup_le fun n => (nat_lt_omega0 n).le).antisymm <| omega0_le.2 <| Ordinal.le_iSup _
 
-theorem IsNormal.apply_omega0 {f : Ordinal.{u} → Ordinal.{v}} (hf : IsNormal f) :
-    ⨆ n : ℕ, f n = f ω := by rw [← iSup_natCast, hf.map_iSup]
+theorem apply_omega0_of_isNormal {f : Ordinal.{u} → Ordinal.{v}} (hf : IsNormal f) :
+    ⨆ n : ℕ, f n = f ω := by
+  rw [← iSup_natCast, hf.map_iSup (bddAbove_of_small _)]
+
+@[deprecated (since := "2025-12-25")]
+alias IsNormal.apply_omega0 := apply_omega0_of_isNormal
 
 @[simp]
-theorem iSup_add_nat (o : Ordinal) : ⨆ n : ℕ, o + n = o + ω :=
-  (isNormal_add_right o).apply_omega0
+theorem iSup_add_natCast (o : Ordinal) : ⨆ n : ℕ, o + n = o + ω :=
+  apply_omega0_of_isNormal (isNormal_add_right o)
+
+@[deprecated (since := "2025-12-25")]
+alias iSup_add_nat := iSup_add_natCast
 
 @[simp]
-theorem iSup_mul_nat (o : Ordinal) : ⨆ n : ℕ, o * n = o * ω := by
+theorem iSup_mul_natCast (o : Ordinal) : ⨆ n : ℕ, o * n = o * ω := by
   rcases eq_zero_or_pos o with (rfl | ho)
   · rw [zero_mul]
     exact iSup_eq_zero_iff.2 fun n => zero_mul (n : Ordinal)
-  · exact (isNormal_mul_right ho).apply_omega0
+  · exact apply_omega0_of_isNormal (isNormal_mul_right ho)
+
+@[deprecated (since := "2025-12-25")]
+alias iSup_mul_nat := iSup_mul_natCast
 
 end Ordinal
diff --git a/Mathlib/SetTheory/Ordinal/FixedPoint.lean b/Mathlib/SetTheory/Ordinal/FixedPoint.lean
--- a/Mathlib/SetTheory/Ordinal/FixedPoint.lean
+++ b/Mathlib/SetTheory/Ordinal/FixedPoint.lean
@@ -13,9 +13,8 @@ public import Mathlib.SetTheory.Ordinal.Exponential
 # Fixed points of normal functions
 
 We prove various statements about the fixed points of normal ordinal functions. We state them in
-three forms: as statements about type-indexed families of normal functions, as statements about
-ordinal-indexed families of normal functions, and as statements about a single normal function. For
-the most part, the first case encompasses the others.
+two forms: as statements about indexed families of normal functions, and as statements about a
+single normal function.
 
 Moreover, we prove some lemmas about the fixed points of specific normal functions.
 
@@ -83,7 +82,7 @@ theorem apply_lt_nfpFamily_iff [Nonempty ι] [Small.{u} ι] (H : ∀ i, IsNormal
     (∀ i, f i b < nfpFamily f a) ↔ b < nfpFamily f a := by
   refine ⟨fun h ↦ ?_, apply_lt_nfpFamily H⟩
   let ⟨l, hl⟩ := lt_nfpFamily_iff.1 (h (Classical.arbitrary ι))
-  exact lt_nfpFamily_iff.2 <| ⟨l, (H _).le_apply.trans_lt hl⟩
+  exact lt_nfpFamily_iff.2 <| ⟨l, (H _).strictMono.le_apply.trans_lt hl⟩
 
 theorem nfpFamily_le_apply [Nonempty ι] [Small.{u} ι] (H : ∀ i, IsNormal (f i)) {a b} :
     (∃ i, nfpFamily f a ≤ f i b) ↔ nfpFamily f a ≤ b := by
@@ -98,16 +97,16 @@ theorem nfpFamily_le_fp (H : ∀ i, Monotone (f i)) {a b} (ab : a ≤ b) (h : 
 
 theorem nfpFamily_fp [Small.{u} ι] {i} (H : IsNormal (f i)) (a) :
     f i (nfpFamily f a) = nfpFamily f a := by
-  rw [nfpFamily, H.map_iSup]
+  rw [nfpFamily, H.map_iSup (bddAbove_of_small _)]
   apply le_antisymm <;> refine Ordinal.iSup_le fun l => ?_
   · exact Ordinal.le_iSup _ (i::l)
-  · exact H.le_apply.trans (Ordinal.le_iSup _ _)
+  · exact H.strictMono.le_apply.trans (Ordinal.le_iSup _ _)
 
 theorem apply_le_nfpFamily [Small.{u} ι] [hι : Nonempty ι] (H : ∀ i, IsNormal (f i)) {a b} :
     (∀ i, f i b ≤ nfpFamily f a) ↔ b ≤ nfpFamily f a := by
   refine ⟨fun h => ?_, fun h i => ?_⟩
   · obtain ⟨i⟩ := hι
-    exact (H i).le_apply.trans (h i)
+    exact (H i).strictMono.le_apply.trans (h i)
   · rw [← nfpFamily_fp (H i)]
     exact (H i).monotone h
 
@@ -172,7 +171,7 @@ theorem derivFamily_fp [Small.{u} ι] {i} (H : IsNormal (f i)) (o : Ordinal) :
     exact nfpFamily_fp H _
   | limit o l IH =>
     have := l.nonempty_Iio.to_subtype
-    rw [derivFamily_limit _ l, H.map_iSup]
+    rw [derivFamily_limit _ l, H.map_iSup (bddAbove_of_small _)]
     refine eq_of_forall_ge_iff fun c => ?_
     rw [Ordinal.iSup_le_iff, Ordinal.iSup_le_iff]
     refine forall_congr' fun a ↦ ?_
@@ -182,7 +181,7 @@ theorem le_iff_derivFamily [Small.{u} ι] (H : ∀ i, IsNormal (f i)) {a} :
     (∀ i, f i a ≤ a) ↔ ∃ o, derivFamily f o = a :=
   ⟨fun ha => by
     suffices ∀ (o), a ≤ derivFamily f o → ∃ o, derivFamily f o = a from
-      this a (isNormal_derivFamily _).le_apply
+      this a (isNormal_derivFamily _).strictMono.le_apply
     intro o
     induction o using limitRecOn with
     | zero =>
@@ -208,7 +207,8 @@ theorem le_iff_derivFamily [Small.{u} ι] (H : ∀ i, IsNormal (f i)) {a} :
 
 theorem fp_iff_derivFamily [Small.{u} ι] (H : ∀ i, IsNormal (f i)) {a} :
     (∀ i, f i a = a) ↔ ∃ o, derivFamily f o = a :=
-  Iff.trans ⟨fun h i => le_of_eq (h i), fun h i => (H i).le_iff_eq.1 (h i)⟩ (le_iff_derivFamily H)
+  Iff.trans ⟨fun h i => le_of_eq (h i), fun h i => (H i).strictMono.le_apply.ge_iff_eq'.1 (h i)⟩
+    (le_iff_derivFamily H)
 
 theorem mem_range_derivFamily [Small.{u} ι] (H : ∀ i, IsNormal (f i)) {a} :
     a ∈ Set.range (derivFamily f) ↔ ∀ i, f i a = a :=
@@ -288,22 +288,34 @@ theorem iterate_lt_nfp (hf : StrictMono f) {a} (h : a < f a) (n : ℕ) : f^[n] a
   rw [← iterate_succ_apply]
   exact iterate_le_nfp ..
 
-theorem IsNormal.apply_lt_nfp (H : IsNormal f) {a b} : f b < nfp f a ↔ b < nfp f a := by
+theorem apply_lt_nfp (H : IsNormal f) {a b} : f b < nfp f a ↔ b < nfp f a := by
   unfold nfp
   rw [← @apply_lt_nfpFamily_iff Unit (fun _ => f) _ _ (fun _ => H) a b]
   exact ⟨fun h _ => h, fun h => h Unit.unit⟩
 
-theorem IsNormal.nfp_le_apply (H : IsNormal f) {a b} : nfp f a ≤ f b ↔ nfp f a ≤ b :=
-  le_iff_le_iff_lt_iff_lt.2 H.apply_lt_nfp
+@[deprecated (since := "2025-12-25")]
+alias IsNormal.apply_lt_nfp := apply_lt_nfp
+
+theorem nfp_le_apply (H : IsNormal f) {a b} : nfp f a ≤ f b ↔ nfp f a ≤ b :=
+  le_iff_le_iff_lt_iff_lt.2 (apply_lt_nfp H)
+
+@[deprecated (since := "2025-12-25")]
+alias IsNormal.nfp_le_apply := nfp_le_apply
 
 theorem nfp_le_fp (H : Monotone f) {a b} (ab : a ≤ b) (h : f b ≤ b) : nfp f a ≤ b :=
   nfpFamily_le_fp (fun _ => H) ab fun _ => h
 
-theorem IsNormal.nfp_fp (H : IsNormal f) : ∀ a, f (nfp f a) = nfp f a :=
+theorem nfp_fp (H : IsNormal f) : ∀ a, f (nfp f a) = nfp f a :=
   @nfpFamily_fp Unit (fun _ => f) _ () H
 
-theorem IsNormal.apply_le_nfp (H : IsNormal f) {a b} : f b ≤ nfp f a ↔ b ≤ nfp f a :=
-  ⟨H.le_apply.trans, fun h => by simpa only [H.nfp_fp] using H.le_iff.2 h⟩
+@[deprecated (since := "2025-12-25")]
+alias IsNormal.nfp_fp := nfp_fp
+
+theorem apply_le_nfp (H : IsNormal f) {a b} : f b ≤ nfp f a ↔ b ≤ nfp f a :=
+  ⟨H.strictMono.le_apply.trans, fun h => by simpa only [nfp_fp H] using H.monotone h⟩
+
+@[deprecated (since := "2025-12-25")]
+alias IsNormal.apply_le_nfp := apply_le_nfp
 
 theorem nfp_eq_self {a} (h : f a = a) : nfp f a = a :=
   nfpFamily_eq_self fun _ => h
@@ -341,24 +353,34 @@ theorem deriv_strictMono (f) : StrictMono (deriv f) :=
   derivFamily_strictMono _
 
 theorem deriv_eq_id_of_nfp_eq_id (h : nfp f = id) : deriv f = id :=
-  ((isNormal_deriv _).eq_iff_zero_and_succ IsNormal.refl).2 (by simp [h])
+  ((isNormal_deriv _).ext .id).2 (by simp [h])
 
 @[deprecated (since := "2025-10-25")]
 alias deriv_id_of_nfp_id := deriv_eq_id_of_nfp_eq_id
 
-theorem IsNormal.deriv_fp (H : IsNormal f) : ∀ o, f (deriv f o) = deriv f o :=
+theorem deriv_fp (H : IsNormal f) : ∀ o, f (deriv f o) = deriv f o :=
   derivFamily_fp (i := ⟨⟩) H
 
-theorem IsNormal.le_iff_deriv (H : IsNormal f) {a} : f a ≤ a ↔ ∃ o, deriv f o = a := by
+@[deprecated (since := "2025-10-25")]
+alias IsNormal.deriv_fp := deriv_fp
+
+theorem le_iff_deriv (H : IsNormal f) {a} : f a ≤ a ↔ ∃ o, deriv f o = a := by
   unfold deriv
   rw [← le_iff_derivFamily fun _ : Unit => H]
   exact ⟨fun h _ => h, fun h => h Unit.unit⟩
 
-theorem IsNormal.fp_iff_deriv (H : IsNormal f) {a} : f a = a ↔ ∃ o, deriv f o = a := by
-  rw [← H.le_iff_eq, H.le_iff_deriv]
+@[deprecated (since := "2025-10-25")]
+alias IsNormal.le_iff_deriv := le_iff_deriv
+
+theorem mem_range_deriv (H : IsNormal f) {a} : a ∈ Set.range (deriv f) ↔ f a = a := by
+  rw [Set.mem_range, ← H.strictMono.le_apply.ge_iff_eq', le_iff_deriv H]
+
+@[deprecated mem_range_deriv (since := "2025-10-25")]
+theorem fp_iff_deriv (H : IsNormal f) {a} : f a = a ↔ ∃ o, deriv f o = a :=
+  (mem_range_deriv H).symm
 
-theorem IsNormal.mem_range_deriv (H : IsNormal f) {a} : a ∈ Set.range (deriv f) ↔ f a = a :=
-  H.fp_iff_deriv.symm
+@[deprecated mem_range_deriv (since := "2025-10-25")]
+alias IsNormal.fp_iff_deriv := fp_iff_deriv
 
 /-- `Ordinal.deriv` enumerates the fixed points of a normal function. -/
 theorem deriv_eq_enumOrd (H : IsNormal f) : deriv f = enumOrd (Function.fixedPoints f) := by
@@ -392,7 +414,7 @@ end
 
 @[simp]
 theorem nfp_add_zero (a) : nfp (a + ·) 0 = a * ω := by
-  simp_rw [← iSup_iterate_eq_nfp, ← iSup_mul_nat]
+  simp_rw [← iSup_iterate_eq_nfp, ← iSup_mul_natCast]
   congr; funext n
   induction n with
   | zero => rw [Nat.cast_zero, mul_zero, iterate_zero_apply]
@@ -407,7 +429,7 @@ theorem nfp_add_eq_mul_omega0 {a b} (hba : b ≤ a * ω) : nfp (a + ·) b = a *
 theorem add_eq_right_iff_mul_omega0_le {a b : Ordinal} : a + b = b ↔ a * ω ≤ b := by
   refine ⟨fun h => ?_, fun h => ?_⟩
   · rw [← nfp_add_zero a, ← deriv_zero_right]
-    obtain ⟨c, hc⟩ := (isNormal_add_right a).fp_iff_deriv.1 h
+    obtain ⟨c, hc⟩ := (mem_range_deriv (isNormal_add_right a)).2 h
     rw [← hc]
     exact (isNormal_deriv _).monotone (zero_le _)
   · have := Ordinal.add_sub_cancel_of_le h
@@ -416,13 +438,13 @@ theorem add_eq_right_iff_mul_omega0_le {a b : Ordinal} : a + b = b ↔ a * ω 
 
 theorem add_le_right_iff_mul_omega0_le {a b : Ordinal} : a + b ≤ b ↔ a * ω ≤ b := by
   rw [← add_eq_right_iff_mul_omega0_le]
-  exact (isNormal_add_right a).le_iff_eq
+  exact (isNormal_add_right a).strictMono.le_apply.ge_iff_eq'
 
 theorem deriv_add_eq_mul_omega0_add (a b : Ordinal.{u}) : deriv (a + ·) b = a * ω + b := by
   revert b
-  rw [← funext_iff, IsNormal.eq_iff_zero_and_succ (isNormal_deriv _) (isNormal_add_right _)]
+  rw [← funext_iff, IsNormal.ext (isNormal_deriv _) (isNormal_add_right _)]
   refine ⟨?_, fun a h => ?_⟩
-  · rw [deriv_zero_right, add_zero]
+  · rw [bot_eq_zero, deriv_zero_right, add_zero]
     exact nfp_add_zero a
   · rw [deriv_succ, h, add_succ]
     exact nfp_eq_self (add_eq_right_iff_mul_omega0_le.2 (le_self_add.trans (le_succ _)))
@@ -431,7 +453,7 @@ theorem deriv_add_eq_mul_omega0_add (a b : Ordinal.{u}) : deriv (a + ·) b = a *
 
 @[simp]
 theorem nfp_mul_one {a : Ordinal} (ha : 0 < a) : nfp (a * ·) 1 = a ^ ω := by
-  rw [← iSup_iterate_eq_nfp, ← iSup_pow ha]
+  rw [← iSup_iterate_eq_nfp, ← iSup_pow_natCast ha]
   congr
   funext n
   induction n with
@@ -487,7 +509,7 @@ theorem mul_eq_right_iff_opow_omega0_dvd {a b : Ordinal} : a * b = b ↔ a ^ ω
 theorem mul_le_right_iff_opow_omega0_dvd {a b : Ordinal} (ha : 0 < a) :
     a * b ≤ b ↔ (a ^ ω) ∣ b := by
   rw [← mul_eq_right_iff_opow_omega0_dvd]
-  exact (isNormal_mul_right ha).le_iff_eq
+  exact (isNormal_mul_right ha).strictMono.le_apply.ge_iff_eq'
 
 theorem nfp_mul_opow_omega0_add {a c : Ordinal} (b) (ha : 0 < a) (hc : 0 < c)
     (hca : c ≤ a ^ ω) : nfp (a * ·) (a ^ ω * b + c) = a ^ ω * succ b := by
@@ -497,7 +519,7 @@ theorem nfp_mul_opow_omega0_add {a c : Ordinal} (b) (ha : 0 < a) (hc : 0 < c)
       gcongr
     · dsimp only; rw [← mul_assoc, ← opow_one_add, one_add_omega0]
   · obtain ⟨d, hd⟩ :=
-      mul_eq_right_iff_opow_omega0_dvd.1 ((isNormal_mul_right ha).nfp_fp ((a ^ ω) * b + c))
+      mul_eq_right_iff_opow_omega0_dvd.1 (nfp_fp (isNormal_mul_right ha) (a ^ ω * b + c))
     rw [hd]
     apply mul_le_mul_right
     have := le_nfp (a * ·) (a ^ ω * b + c)
@@ -510,9 +532,9 @@ theorem deriv_mul_eq_opow_omega0_mul {a : Ordinal.{u}} (ha : 0 < a) (b) :
     deriv (a * ·) b = a ^ ω * b := by
   revert b
   rw [← funext_iff,
-    IsNormal.eq_iff_zero_and_succ (isNormal_deriv _) (isNormal_mul_right (opow_pos ω ha))]
+    IsNormal.ext (isNormal_deriv _) (isNormal_mul_right (opow_pos ω ha))]
   refine ⟨?_, fun c h => ?_⟩
-  · dsimp only; rw [deriv_zero_right, nfp_mul_zero, mul_zero]
+  · rw [bot_eq_zero, deriv_zero_right, nfp_mul_zero, mul_zero]
   · rw [deriv_succ, h]
     exact nfp_mul_opow_omega0_add c ha zero_lt_one (one_le_iff_pos.2 (opow_pos _ ha))
 
diff --git a/Mathlib/SetTheory/Ordinal/Principal.lean b/Mathlib/SetTheory/Ordinal/Principal.lean
--- a/Mathlib/SetTheory/Ordinal/Principal.lean
+++ b/Mathlib/SetTheory/Ordinal/Principal.lean
@@ -90,7 +90,7 @@ theorem Principal.iterate_lt (hao : a < o) (ho : Principal op o) (n : ℕ) : (op
 
 theorem op_eq_self_of_principal (hao : a < o) (H : IsNormal (op a))
     (ho : Principal op o) (ho' : IsSuccLimit o) : op a o = o := by
-  apply H.le_apply.antisymm'
+  apply H.strictMono.le_apply.antisymm'
   rw [H.apply_of_isSuccLimit ho', Ordinal.iSup_le_iff]
   exact fun ⟨b, hbo⟩ ↦ (ho hao hbo).le
 
@@ -202,7 +202,7 @@ theorem add_omega0_opow (h : a < ω ^ b) : a + ω ^ b = ω ^ b := by
     grw [ax, opow_succ, ← mul_add, add_omega0 xo]
   | limit b l IH =>
     rcases (lt_opow_of_isSuccLimit omega0_ne_zero l).1 h with ⟨x, xb, ax⟩
-    apply (((isNormal_add_right a).trans <| isNormal_opow one_lt_omega0).limit_le l).2
+    apply (((isNormal_add_right a).comp <| isNormal_opow one_lt_omega0).le_iff_forall_le l).2
     intro y yb
     calc a + ω ^ y ≤ a + ω ^ max x y := by gcongr; exacts [omega0_pos, le_max_right ..]
     _ ≤ ω ^ max x y :=
@@ -340,11 +340,11 @@ theorem mul_lt_omega0_opow (c0 : 0 < c) (ha : a < ω ^ c) (hb : b < ω) : a * b
   · exact (lt_irrefl _).elim c0
   · rw [opow_succ] at ha
     obtain ⟨n, hn, an⟩ :=
-      ((isNormal_mul_right <| opow_pos _ omega0_pos).limit_lt isSuccLimit_omega0).1 ha
+      ((isNormal_mul_right <| opow_pos _ omega0_pos).lt_iff_exists_lt isSuccLimit_omega0).1 ha
     grw [an, opow_succ, mul_assoc]
     gcongr
     exacts [opow_pos _ omega0_pos, principal_mul_omega0 hn hb]
-  · rcases ((isNormal_opow one_lt_omega0).limit_lt l).1 ha with ⟨x, hx, ax⟩
+  · rcases ((isNormal_opow one_lt_omega0).lt_iff_exists_lt l).1 ha with ⟨x, hx, ax⟩
     refine (mul_le_mul' (le_of_lt ax) (le_of_lt hb)).trans_lt ?_
     rw [← opow_succ, opow_lt_opow_iff_right one_lt_omega0]
     exact l.succ_lt hx
diff --git a/Mathlib/SetTheory/Ordinal/Topology.lean b/Mathlib/SetTheory/Ordinal/Topology.lean
--- a/Mathlib/SetTheory/Ordinal/Topology.lean
+++ b/Mathlib/SetTheory/Ordinal/Topology.lean
@@ -178,12 +178,12 @@ theorem enumOrd_isNormal_iff_isClosed (hs : ¬ BddAbove s) :
   have Hs := enumOrd_strictMono hs
   refine
     ⟨fun h => isClosed_iff_iSup.2 fun {ι} hι f hf => ?_, fun h =>
-      (isNormal_iff_strictMono_limit _).2 ⟨Hs, fun a ha o H => ?_⟩⟩
+      isNormal_iff.2 ⟨Hs, fun a ha o H => ?_⟩⟩
   · let g : ι → Ordinal.{u} := fun i => (enumOrdOrderIso s hs).symm ⟨_, hf i⟩
     suffices enumOrd s (⨆ i, g i) = ⨆ i, f i by
       rw [← this]
       exact enumOrd_mem hs _
-    rw [IsNormal.map_iSup h g]
+    rw [Order.IsNormal.map_iSup h (bddAbove_of_small _)]
     congr
     ext x
     change (enumOrdOrderIso s hs _).val = f x
diff --git a/Mathlib/SetTheory/Ordinal/Veblen.lean b/Mathlib/SetTheory/Ordinal/Veblen.lean
--- a/Mathlib/SetTheory/Ordinal/Veblen.lean
+++ b/Mathlib/SetTheory/Ordinal/Veblen.lean
@@ -91,6 +91,7 @@ theorem isNormal_veblenWith (o : Ordinal) : IsNormal (veblenWith f o) := by
   · rwa [veblenWith_zero]
   · exact isNormal_veblenWith' f h
 
+@[deprecated (since := "2025-12-25")]
 protected alias IsNormal.veblenWith := isNormal_veblenWith
 
 theorem mem_range_veblenWith (h : o ≠ 0) :
@@ -116,7 +117,7 @@ theorem veblenWith_mem_range : veblenWith f o a ∈ range f := by
     simp
 
 theorem veblenWith_succ (o : Ordinal) : veblenWith f (succ o) = deriv (veblenWith f o) := by
-  rw [deriv_eq_enumOrd (hf.veblenWith o), veblenWith_of_ne_zero f (succ_ne_zero _),
+  rw [deriv_eq_enumOrd (isNormal_veblenWith hf o), veblenWith_of_ne_zero f (succ_ne_zero _),
     derivFamily_eq_enumOrd]
   · apply congr_arg
     ext a
@@ -127,10 +128,10 @@ theorem veblenWith_succ (o : Ordinal) : veblenWith f (succ o) = deriv (veblenWit
     · rw [Function.mem_fixedPoints_iff, ha]
     · rw [← ha]
       exact veblenWith_veblenWith_of_lt hf hb _
-  · exact fun o ↦ hf.veblenWith o.1
+  · exact fun o ↦ isNormal_veblenWith hf o.1
 
 theorem veblenWith_right_strictMono (o : Ordinal) : StrictMono (veblenWith f o) :=
-  (hf.veblenWith o).strictMono
+  (isNormal_veblenWith hf o).strictMono
 
 @[simp]
 theorem veblenWith_lt_veblenWith_iff_right : veblenWith f o a < veblenWith f o b ↔ a < b :=
@@ -186,8 +187,8 @@ theorem left_le_veblenWith (hp : 0 < f 0) (o a : Ordinal) : o ≤ veblenWith f o
   (veblenWith_zero_strictMono hf hp).le_apply.trans <|
     (veblenWith_right_strictMono hf _).monotone (zero_le _)
 
-theorem IsNormal.veblenWith_zero (hp : 0 < f 0) : IsNormal (veblenWith f · 0) := by
-  rw [isNormal_iff_strictMono_limit]
+theorem isNormal_veblenWith_zero (hp : 0 < f 0) : IsNormal (veblenWith f · 0) := by
+  rw [isNormal_iff]
   refine ⟨veblenWith_zero_strictMono hf hp, fun o ho a IH ↦ ?_⟩
   rw [veblenWith_of_ne_zero f ho.ne_bot, derivFamily_zero]
   apply nfpFamily_le fun l ↦ ?_
@@ -205,6 +206,9 @@ theorem IsNormal.veblenWith_zero (hp : 0 < f 0) : IsNormal (veblenWith f · 0) :
     rw [lt_succ_iff]
     exact le_max_left _ b
 
+@[deprecated (since := "2025-12-25")]
+alias IsNormal.veblenWith_zero := isNormal_veblenWith_zero
+
 theorem veblenWith_veblenWith_eq_veblenWith_iff (h : o₂ ≤ o₁) :
     veblenWith f o₁ (veblenWith f o₂ a) = veblenWith f o₂ a ↔ veblenWith f o₁ a = a := by
   grind [veblenWith_inj, → veblenWith_eq_self_of_le]
@@ -288,7 +292,7 @@ theorem veblen_of_ne_zero (h : o ≠ 0) : veblen o = derivFamily fun x : Iio o 
   veblenWith_of_ne_zero _ h
 
 theorem isNormal_veblen (o : Ordinal) : IsNormal (veblen o) :=
-  (isNormal_opow one_lt_omega0).veblenWith o
+  isNormal_veblenWith (isNormal_opow one_lt_omega0) o
 
 theorem mem_range_veblen (h : o ≠ 0) : a ∈ range (veblen o) ↔ ∀ b < o, veblen b a = a :=
   mem_range_veblenWith (isNormal_opow one_lt_omega0) h
@@ -352,7 +356,7 @@ theorem left_le_veblen (o a : Ordinal) : o ≤ veblen o a :=
   left_le_veblenWith (isNormal_opow one_lt_omega0) (by simp) o a
 
 theorem isNormal_veblen_zero : IsNormal (veblen · 0) :=
-  (isNormal_opow one_lt_omega0).veblenWith_zero (by simp)
+  isNormal_veblenWith_zero (isNormal_opow one_lt_omega0) (by simp)
 
 theorem veblen_veblen_eq_veblen_iff (h : o₂ ≤ o₁) :
     veblen o₁ (veblen o₂ a) = veblen o₂ a ↔ veblen o₁ a = a :=
@@ -549,7 +553,7 @@ theorem epsilon0_le_of_omega0_opow_le (h : ω ^ o ≤ o) : ε₀ ≤ o := by
 
 @[simp]
 theorem omega0_opow_epsilon (o : Ordinal) : ω ^ ε_ o = ε_ o := by
-  rw [epsilon_eq_deriv, (isNormal_opow one_lt_omega0).deriv_fp]
+  rw [epsilon_eq_deriv, deriv_fp (isNormal_opow one_lt_omega0)]
 
 /-- `ε₀` is the limit of `0`, `ω ^ 0`, `ω ^ ω ^ 0`, … -/
 theorem lt_epsilon0 : o < ε₀ ↔ ∃ n : ℕ, o < (fun a ↦ ω ^ a)^[n] 0 := by
@@ -596,7 +600,7 @@ theorem isNormal_gamma : IsNormal gamma :=
   isNormal_deriv _
 
 theorem mem_range_gamma : o ∈ range Γ_ ↔ veblen o 0 = o :=
-  isNormal_veblen_zero.mem_range_deriv
+  mem_range_deriv isNormal_veblen_zero
 
 theorem strictMono_gamma : StrictMono gamma :=
   isNormal_gamma.strictMono
@@ -618,7 +622,7 @@ theorem gamma_inj : Γ_ a = Γ_ b ↔ a = b :=
 
 @[simp]
 theorem veblen_gamma_zero (o : Ordinal) : veblen (Γ_ o) 0 = Γ_ o :=
-  isNormal_veblen_zero.deriv_fp o
+  deriv_fp isNormal_veblen_zero o
 
 theorem gamma0_eq_nfp : Γ₀ = nfp (veblen · 0) 0 :=
   deriv_zero_right _

```

---

When you have reviewed the PR as the brief asks, call `submit_findings`. For each finding, give:

- `path` and `line_start` -- where in the reviewed file the problem is, so the finding can be located. Give the line of the declaration your claim is about.
- `claim` -- name the declaration and say what is wrong with it.
- `suggested_fix` -- what to do instead.
- `severity` -- `blocking` if the change is needed for correctness or policy; `advisory` for every other change you would request. Advisory findings count in full.

Also give `notes`: your account of the review, with an entry for every changed declaration in the PR model (declarations of one family may share an entry). In each entry, say what you checked for that declaration under each concern that applies to it -- its proof, its statement and how general it is, whether the library already has it, its name, its docstring, its attributes and placement -- and close it with what you concluded, "nothing to ask" included.

Finish by calling `submit_findings` once. If there is nothing to ask, call it with an empty `findings` list and your `notes`.