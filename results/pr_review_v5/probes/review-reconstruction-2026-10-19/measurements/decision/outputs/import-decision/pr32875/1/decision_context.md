# Decision context: golfing eight existing proofs

Sources are from before the contribution: Mathlib at the base commit, and Zulip up to 2025-12-14.
Twelve sources, numbered across decisions.

## 1. The aim: shorter proofs, faster proofs, or both (and whether a shorter but slower proof is acceptable)

**[1] earlier_decision**: Zulip #mathlib4, topic "What's your workflow to review Mathlib PR's", Kevin Buzzard (maintainer), 2025-12-12. The search tool truncates the message at the ellipsis.

> In my opinion the best golfs are those that either (a) greatly decrease compilation time without sacrificing readability or (b) decrease the number of times lemmas are called explicitly (replacing calls to lemmas with calls to tactics). If you're getting into golfing then please don't just assume that because you've shaved 5 characters of a proof that this represents progress! Making a proof a bit…

Bears on the aim: a maintainer names speed (without loss of readability) and fewer explicit lemma calls as what makes a golf worthwhile, and says that a few characters shorter is not progress in itself.

**[2] earlier_decision**: Zulip #mathlib4, topic "`grind` is available. What should Mathlib users expect?", Kevin Buzzard (maintainer), 2025-07-02.

> @David Renshaw fancy trying `TryAtEachStep` on mathlib with `grind`? I guess one would have to be careful that we don't make the library shorter but slower...

Bears on whether a shorter but slower proof is acceptable: it names "shorter but slower" as the outcome to be careful about.

**[3] counterexample**: same Zulip topic, Kim Morrison (maintainer), 2025-07-02, two messages four minutes apart.

> I just want to give a shout out for some lovely golfs euprunin found using `grind` in #26622.

> (But I will say --- I am going to be arguing for allowing `grind` even when there is a small relative slow-down...)

Bears on the same question from the other side: another maintainer welcomes automated golfs and argues for accepting them despite a small slow-down, so the trade-off is not settled.

**[4] earlier_decision**: Zulip #mathlib4, topic "request: discourage squeezing terminal simps?", David Loeffler (maintainer) quoting Kim Morrison, 2025-01-29.

> Kim Morrison said:  I think my preference is for lots of comments: squeeze terminal simps whenever you feel there is a performance benefit (probably should be at least 10,000 heartbeats to bother?), but then leave a comment to that effect.

Bears on golfing for speed: a stated threshold for when a speed-motivated rewrite of a terminal `simp` is worth making, and a request that it be explained in a comment.

## 2. Proof technique: automation versus explicit lemma calls, and robustness

**[5] written_guidance** (the module docstring of a linter that runs on Mathlib): `Mathlib/Tactic/Linter/FlexibleLinter.lean:14-23, 42-44`.

```
The "flexible" linter makes sure that a "rigid" tactic (such as `rw`) does not act on the
output of a "flexible" tactic (such as `simp`).

For example, this ensures that, if you want to use `simp [...]` in the middle of a proof,
then you should replace `simp [...]` by one of
* a `suffices \"expr after simp\" by simpa` line;
* the output of `simp? [...]`, so that the final code contains `simp only [...]`;
* something else that does not involve `simp`!

Otherwise, the linter will complain.
...
* ❌️ [`flexible` --> `rigid`]
  A sequence `simp; rw [lemma]` is instead more likely to break, since the goal after `simp` is
  subject to change by even a small, likely, modification of the `simp` set.
```

Bears on which tactic sequences a rewritten proof may use: non-terminal `simp` followed by rigid tactics is flagged. Several of the current proofs (for example `Portmanteau.lean:653-655`, `simp only [...] at h` then `rwa`) already sit on this boundary.

**[6] counterexample**: Zulip #mathlib4, topic "SetLike instance for Finset", Junyan Xu (maintainer), 2025-08-12.

> I had to revert one of the `grind` golfs back to  ```Lean4 rintro ⟨i, hi⟩; specialize h i hi; simp_rw [sets_t', dif_pos hi] at h; exact h ```  and `grind`'s output is Probability.Kernel grind failure.txt.  If anyone knows how to golf it again please do.

Bears on robustness: a `grind` golf in the probability kernel files stopped working after an unrelated refactor and was reverted to an explicit tactic proof.

**[7] library_example and counterexample**: `Mathlib/Data/Finset/Image.lean:68-83, 93-94` (the file of `Finset.mem_map_equiv`).

```
@[simp, grind =]
theorem mem_map {b : β} : b ∈ s.map f ↔ ∃ a ∈ s, f a = b :=
  Multiset.mem_map

-- Higher priority to apply before `mem_map`.
@[simp 1100]
theorem mem_map_equiv {f : α ≃ β} {b : β} : b ∈ s.map f.toEmbedding ↔ f.symm b ∈ s := by
  rw [mem_map]
  exact
    ⟨by
      rintro ⟨a, H, rfl⟩
      simpa, fun h => ⟨_, h, by simp⟩⟩

@[simp 1100]
theorem mem_map' (f : α ↪ β) {a} {s : Finset α} : f a ∈ s.map f ↔ a ∈ s :=
  mem_map_of_injective f.2
...
theorem forall_mem_map {f : α ↪ β} {s : Finset α} {p : ∀ a, a ∈ s.map f → Prop} :
    (∀ y (H : y ∈ s.map f), p y H) ↔ ∀ x (H : x ∈ s), p (f x) (mem_map_of_mem _ H) := by grind
```

Bears on technique: in the same file, neighbours are proved both as one-line terms from existing lemmas (`mem_map'`) and as bare `by grind` (`forall_mem_map`, also `coe_map`), and `mem_map` is registered with `grind`. Both styles coexist at base.

## 3. Proof route: existing lemmas the eight proofs could draw on

**[8] library_example**: `Mathlib/Probability/Kernel/Composition/MeasureCompProd.lean:69-72`.

```
lemma compProd_apply_prod [SFinite μ] [IsSFiniteKernel κ]
    {s : Set α} {t : Set β} (hs : MeasurableSet s) (ht : MeasurableSet t) :
    (μ ⊗ₘ κ) (s ×ˢ t) = ∫⁻ a in s, κ a t ∂μ := by
  simp [compProd, Kernel.compProd_apply_prod hs ht]
```

Bears on the two `setLIntegral_condKernel_eq_measure_prod` proofs: an existing lemma already states the product-set value of a composition product as a set integral (the kernel version is `Kernel.compProd_apply_prod` at `Mathlib/Probability/Kernel/Composition/CompProd.lean:137`). The current measure proof (`Disintegration/Integral.lean:152`) already rewrites with `compProd_apply` from the same `MeasureCompProd.lean` file, so that file is already in scope there.

**[9] library_example**: `Mathlib/Order/LiminfLimsup.lean:1120-1130` (`limsup_max`, the two-function sibling of `limsup_finset_sup'`, 25 lines above it).

```
    limsup (fun a ↦ max (u a) (v a)) f = max (limsup u f) (limsup v f) := by
  have bddmax := IsBoundedUnder.sup h₃ h₄
  have cobddmax := isCoboundedUnder_le_max (v := v) (Or.inl h₁)
  apply le_antisymm
  · refine (limsup_le_iff cobddmax bddmax).2 (fun b hb ↦ ?_)
    have hu := eventually_lt_of_limsup_lt (lt_of_le_of_lt (le_max_left _ _) hb) h₃
    have hv := eventually_lt_of_limsup_lt (lt_of_le_of_lt (le_max_right _ _) hb) h₄
    refine mem_of_superset (inter_mem hu hv) (fun _ ↦ by simp)
  · exact max_le (c := limsup (fun a ↦ max (u a) (v a)) f)
      (limsup_le_limsup (Eventually.of_forall (fun a : α ↦ le_max_left (u a) (v a))) h₁ bddmax)
      (limsup_le_limsup (Eventually.of_forall (fun a : α ↦ le_max_right (u a) (v a))) h₂ bddmax)
```

Bears on the route for `limsup_finset_sup'`: the sibling follows the same antisymmetry argument but closes the eventual bound with `mem_of_superset (inter_mem …)`, where the finset version uses `eventually_iff_exists_mem` with an explicit `⋂`. It is evidence of what the library does, not a preference.

For `Rat.inv_intCast_den_of_pos`, see [12]: the general `inv_intCast_den` sits a few lines below it and is proved `by simp`. For `tendsto_of_forall_isClosed_limsup_real_le'` and `Metric.exists_lt_mem_ball_of_mem_ball` I found no source bearing on the route. The metric file's other proofs of "a smaller radius exists" use `exists_between` (`Pseudo/Defs.lean:693`), but only in passing.

## 4. Whether to turn a declaration into an alias, deprecate it, or generalize it

**[10] library_example**: `Mathlib/MeasureTheory/Constructions/Pi.lean:724-731`.

```
theorem measurePreserving_piCongrLeft (f : ι' ≃ ι) :
    MeasurePreserving (MeasurableEquiv.piCongrLeft α f)
      (Measure.pi fun i' => μ (f i')) (Measure.pi μ) where
  measurable := (MeasurableEquiv.piCongrLeft α f).measurable
  map_eq := by
    refine (pi_eq fun s _ => ?_).symm
    rw [MeasurableEquiv.map_apply, MeasurableEquiv.coe_piCongrLeft f,
      Equiv.piCongrLeft_preimage_univ_pi, pi_pi _ _, f.prod_comp (fun i => μ i (s i))]
```

Bears on alias, deprecation and proof route for `pi_map_piCongrLeft` (line 446): the same push-forward fact already exists in `MeasurePreserving` form with a three-line `map_eq` proof via `Equiv.piCongrLeft_preimage_univ_pi`. It sits about 280 lines later in the same file, in a section with its own `variable` block (lines 702-705), so placement and file order matter for any reuse.

**[11] consumer**: `Mathlib/Probability/ProductMeasure.lean:92, 253, 316`.

```
  rw [piContent_cylinder _ (hs.preimage (by fun_prop)), ← Measure.pi_map_piCongrLeft e,
    ← pi_map_piCongrLeft (e.restrictPreimageFinset I), map_apply _ hS, coe_piCongrLeft]
    rw [A_eq, piContent_cylinder μ (mS n), ← pi_map_piCongrLeft (aux n),
```

Bears on what changing `pi_map_piCongrLeft` into an alias or deprecating it would touch: three downstream proofs rewrite right to left with the `map` form. The other seven declarations have few uses at base: `exists_lt_mem_ball_of_mem_ball` once (`MeasureTheory/Integral/CircleTransform.lean:127`), `inv_intCast_den_of_pos` only in `inv_natCast_den_of_pos`, and `limsup_finset_sup'` and the Portmanteau lemma only in their own files.

I found no Zulip discussion or review comment, dated before this contribution, on keeping both a `map` equation and a `MeasurePreserving` statement for the same fact, or on generalizing within a golf.

## 5. Scope: other proofs in the same files, and whole versus partial rewrites

**[12] written_guidance and library_example**: `Mathlib/Data/Rat/Lemmas.lean:316-324`.

```
theorem inv_ofNat_num (a : ℕ) [a.AtLeastTwo] : (ofNat(a) : ℚ)⁻¹.num = 1 := by
  -- This proof is quite unpleasant: golf / find better simp lemmas?
  have : 2 ≤ a := Nat.AtLeastTwo.prop
  simp only [num_inv, num_ofNat, den_ofNat, Nat.cast_one, mul_one, Int.sign_eq_one_iff_pos,
    gt_iff_lt]
  change 0 < (a : ℤ)
  lia

theorem inv_intCast_den (a : ℤ) : (a : ℚ)⁻¹.den = if a = 0 then 1 else a.natAbs := by simp
```

Bears on scope: in the file of `inv_intCast_den_of_pos`, an in-source comment invites a golf of a neighbouring proof that is not among the eight. The next lemma is the unconditional form of the denominator fact, proved by `simp`.

On rewriting a proof in whole or in part, and on how large or how bundled a series of golf PRs should be, I found no source specific to golfing. The Zulip results on splitting PRs concerned feature series, not golfs, and are left out.

## 6. Placement and imports

I found nothing beyond the facts already noted: [8] (the needed lemma's file is already used by the target file) and [10] (the related lemma comes later in the same file, in another section). No source discussed adding imports for a golf.
