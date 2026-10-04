import json
D = "/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/pipeline-overfit-review/results/pr_review_v5/probes/model-gap-val-small12/pr26185/X2"
findings = [
 {
  "target": "module_doc in Counterexamples/PeanoCurve.lean",
  "claim": "The module docstring of `Counterexamples/PeanoCurve.lean` has two typos (\"existsence\", \"sujrective\") and reads \"continuous sujrective map\" without an article; it also lacks the blank line after the `# Peano curve` heading and does not name the main result.",
  "requested_change": "Rewrite the module doc as: `# Peano curve` followed by a blank line, then \"This file proves the existence of a Peano curve, a continuous surjective map from the interval `[0, 1]` onto the square `[0, 1] × [0, 1]`.\" and a `## Main results` line listing `exists_peano_curve`.",
  "severity": "advisory",
  "evidence": "Read the added module doc in diff.patch / model.md: `This file proves the existsence of a Peano curve -- continuous sujrective map from the interval`. Pure text fix; no compile impact."
 },
 {
  "target": "exists_long_peano_curve",
  "claim": "The docstring of `exists_long_peano_curve` says the function \"maps the Cantor set to the square\", which every `f : C(ℝ, I × I)` does; the content of the statement (`Set.SurjOn f cantorSet Set.univ`) is that it maps the Cantor set ONTO the square.",
  "requested_change": "Change the docstring to \"There is a continuous function on `ℝ` that maps the Cantor set onto the square.\"",
  "severity": "advisory",
  "evidence": "Statement as the PR leaves it: `∃ f : C(ℝ, I × I), Set.SurjOn f cantorSet Set.univ`; docstring: `There is a continuous function on ℝ that maps the Cantor set to the square.` Checked by reading model.md/diff.patch."
 },
 {
  "target": "exists_peano_curve",
  "claim": "`exists_peano_curve` (and `exists_long_peano_curve`) are stated only for `I × I`, but the proof uses nothing about the square beyond `Nonempty`, compactness, metrizability and `TietzeExtension`; the same argument gives a continuous surjection from `I` onto e.g. `I^n` or the Hilbert cube `ℕ → I`.",
  "requested_change": "Generalize: state `exists_long_peano_curve (X : Type*) [TopologicalSpace X] [CompactSpace X] [TopologicalSpace.MetrizableSpace X] [Nonempty X] [TietzeExtension.{0} X] : ∃ f : C(ℝ, X), Set.SurjOn f cantorSet Set.univ` (using `letI := TopologicalSpace.metrizableSpaceMetric X` before `exists_nat_bool_continuous_surjective_of_compact X`), add `exists_continuous_surjective_of_tietzeExtension X : ∃ f : C(I, X), Function.Surjective f`, and derive `exists_peano_curve` as `exists_continuous_surjective_of_tietzeExtension (I × I)`.",
  "severity": "advisory",
  "evidence": "lean_verify_edit on Counterexamples/PeanoCurve.lean (line mode, lines 17-38 replaced by the generalized lemma, the general theorem, `exists_peano_curve := exists_continuous_surjective_of_tietzeExtension (I × I)`, and `example : ∃ f : C(I, ℕ → I), Function.Surjective f := exists_continuous_surjective_of_tietzeExtension (ℕ → I)`): success, no errors. A first attempt with `[MetricSpace X]` failed only on the Hilbert-cube example (`failed to synthesize MetricSpace (ℕ → ↑I)`), which is why the metrizable form is requested. The `TietzeExtension` instances for `Prod` and `Pi` exist in Mathlib/Topology/TietzeExtension.lean (lines 119-132)."
 },
 {
  "target": "exists_peano_curve",
  "claim": "The tactic proof of `exists_peano_curve` goes through `use`, a `rw` with `ContinuousMap.coe_restrict` and closes `Set.univ ⊆ Set.univ` with `(by rfl)`; it is a one-line term.",
  "requested_change": "Replace the proof after `obtain ⟨f, hf⟩ := exists_long_peano_curve` with `exact ⟨f.restrict I, Set.surjOn_iff_surjective.mp <| hf.mono cantorSet_subset_unitInterval subset_rfl⟩` (in any case replace `(by rfl)` with `subset_rfl`).",
  "severity": "advisory",
  "evidence": "lean_verify_edit on Counterexamples/PeanoCurve.lean with this proof for `exists_peano_curve` (together with the `exists_long_peano_curve` variant ending in `refine ⟨f, Set.surjOn_iff_surjective.mpr ?_⟩; exact (hf ▸ hg' : Function.Surjective (f.restrict cantorSet))`): success, no errors. `subset_rfl` also verified inside the generalized version."
 },
 {
  "target": "exists_long_peano_curve",
  "claim": "The continuity proof of `g'` in `exists_long_peano_curve` is written by hand as `Continuous.comp hg1 (Homeomorph.continuous _)`, where `fun_prop` is the standard discharger.",
  "requested_change": "Write `let g' : C(cantorSet, I × I) := ⟨g ∘ cantorSetHomeomorphNatToBool, by fun_prop⟩`.",
  "severity": "advisory",
  "evidence": "lean_verify_edit on Counterexamples/PeanoCurve.lean with `⟨g ∘ cantorSetHomeomorphNatToBool, by fun_prop⟩` (both in the generalized and in the non-generalized rewrite of lines 17-38): success."
 },
 {
  "target": "unitInterval.instTietzeExtension",
  "claim": "`unitInterval.instTietzeExtension` is proved by rewriting `I` into a closed ball (which needs the new `unitInterval.eq_closedBall` and the RCLike/finite-dimensional machinery of `Mathlib/Analysis/Complex/Tietze.lean`), but it is a special case of a fact available in `Mathlib/Topology/TietzeExtension.lean` itself: `ContinuousMap.exists_restrict_eq_forall_mem_of_closed` already extends maps into any nonempty `OrdConnected` subset of `ℝ`. The instance is stated at a too-specific level and sits in the wrong file.",
  "requested_change": "Replace it by a general instance in `Mathlib/Topology/TietzeExtension.lean` next to `Real.instTietzeExtension`: `instance Set.OrdConnected.instTietzeExtension {t : Set ℝ} [t.OrdConnected] [Nonempty t] : TietzeExtension t where exists_restrict_eq' s hs f := by obtain ⟨g, hg, hgf⟩ := (ContinuousMap.comp ⟨Subtype.val, continuous_subtype_val⟩ f) |>.exists_restrict_eq_forall_mem_of_closed (fun x ↦ (f x).2) (Set.nonempty_coe_sort.mp ‹_›) hs; exact ⟨⟨_, (map_continuous g).codRestrict hg⟩, by ext x; exact congr($hgf x)⟩`, and delete `unitInterval.instTietzeExtension` from `Mathlib/Analysis/Complex/Tietze.lean` (instance search then finds `TietzeExtension unitInterval`). If only the unit interval is wanted, at least prove it as a retract like `NNReal.instTietzeExtension`: `.of_retract ⟨Subtype.val, continuous_subtype_val⟩ ⟨Set.projIcc 0 1 zero_le_one, continuous_projIcc⟩ <| by ext; simp`.",
  "severity": "advisory",
  "evidence": "lean_verify_edit: (1) Mathlib/Topology/TietzeExtension.lean with the general instance inserted after `Real.instTietzeExtension` plus `example : TietzeExtension (Set.Icc (0 : ℝ) 1) := inferInstance`: success (no new imports needed; the file already has `exists_restrict_eq_forall_mem_of_closed` with `[OrdConnected t]`). (2) Mathlib/Analysis/Complex/Tietze.lean replacing `unitInterval.instTietzeExtension` by the general instance plus `example : TietzeExtension unitInterval := inferInstance`: success. (3) Tietze.lean replacing the instance body with the `.of_retract ... projIcc` proof: success. `NNReal.instTietzeExtension` (TietzeExtension.lean:518) is the sibling proved by `.of_retract`."
 },
 {
  "target": "ContinuousMap.coe_restrict",
  "claim": "This Counterexamples PR changes the right-hand side (and so the simp normal form) of the core Mathlib simp lemma `ContinuousMap.coe_restrict` from `f ∘ ((↑) : s → α)` to `s.restrict f`, forcing an edit to `ContinuousMap.liftCover_restrict` and making it inconsistent with the sibling `BoundedContinuousFunction.coe_restrict` (still `⇑(f.restrict s) = f ∘ (↑)`) and with the `restrict` definition's own `toFun := f ∘ ((↑) : s → α)`; the Peano-curve proofs do not need the change.",
  "requested_change": "Drop the `coe_restrict` restatement and the `liftCover_restrict` proof edit from this PR, and write the two PeanoCurve proofs without rewriting by `coe_restrict` (e.g. `refine ⟨f, Set.surjOn_iff_surjective.mpr ?_⟩; exact (hf ▸ hg' : Function.Surjective (f.restrict cantorSet))` and `exact ⟨f.restrict I, Set.surjOn_iff_surjective.mp <| hf.mono cantorSet_subset_unitInterval subset_rfl⟩`); if the new simp normal form is wanted, propose it in a separate Mathlib PR that also updates `BoundedContinuousFunction.coe_restrict`.",
  "severity": "advisory",
  "evidence": "content_search for `coe_restrict` in target/Mathlib: `BoundedContinuousFunction.coe_restrict (f : α →ᵇ β) (s : Set α) : ⇑(f.restrict s) = f ∘ (↑) := rfl` (Topology/ContinuousMap/Bounded/Basic.lean:353); `ContinuousMap.restrict` has `toFun := f ∘ ((↑) : s → α)` (ContinuousMap/Basic.lean:281). lean_verify_edit on Counterexamples/PeanoCurve.lean with both proofs rewritten to not mention `ContinuousMap.coe_restrict` (they rely only on the definitional equality `⇑(f.restrict s) = s.restrict ⇑f`): success. Zulip (Eric Wieser, 2025-02-06, `Set.incl` thread) notes `Set.restrict` is not generally the preferred simp-normal form, so the change is a Mathlib-wide API decision."
 },
 {
  "target": "Counterexamples/PeanoCurve.lean",
  "claim": "`exists_long_peano_curve` and `exists_peano_curve` are declared in the root namespace, while 24 of the 27 existing `Counterexamples/` files wrap their declarations in a namespace (mostly `namespace Counterexample`), so these generic names leak into the global namespace of everything importing `Counterexamples`.",
  "requested_change": "Wrap the declarations of `Counterexamples/PeanoCurve.lean` in `namespace Counterexample` ... `end Counterexample` (or `namespace PeanoCurve`).",
  "severity": "advisory",
  "evidence": "content_search `^namespace ` over target/Counterexamples: 24 files open a namespace (e.g. MapFloor, SorgenfreyLine, Phillips, Girard use `namespace Counterexample`; TopologistsSineCurve uses `namespace TopologistsSineCurve`); only DiscreteTopologyNonDiscreteUniformity, Motzkin and OrderedCancelAddCommMonoidWithBounds (and this new file) do not."
 }
]
json.dump(findings, open(f"{D}/findings.json","w"), ensure_ascii=False, indent=1)
print(len(findings))
