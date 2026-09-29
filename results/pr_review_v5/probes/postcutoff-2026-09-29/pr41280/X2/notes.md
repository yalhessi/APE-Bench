# Review notes: PR #41280 (C^n smoothness of `e.symmL` as a hom-bundle section)

## Process
- Read `brief.md`, `pr.md`, `model.md` and `diff.patch`, then ran `ptool describe`.
- `file_read` and `content_search` only started working after the first `lean_verify_edit` call
  had materialised `target/`. From then on, the file under review was
  `target/Mathlib/Geometry/Manifold/VectorBundle/Hom.lean`.
- An as-is compile of the PR file (`lean_verify_edit` with no edit) succeeds with no errors or
  warnings.
- Read all of Hom.lean up to line 319, and lines 1-420 of VectorBundle/Basic.lean
  (`contMDiffAt_totalSpace`, `contMDiffAt_section`, `ContMDiffVectorBundle`,
  `contMDiffAt_coordChangeL` and the `coordChangeL` family).
- `declaration_search`: `continuousOn_symmL`, `continuousAt_symmL`, `mdifferentiableAt_symmL`,
  `contMDiff{At,On}_continuousLinearMapAt` do not exist. `contMDiffOn_symmL` exists only in this
  PR. `Bundle.Trivialization.symmL` is in Topology/VectorBundle/Basic.lean.
- `content_search` for `symmL` under `target/Mathlib/Geometry`: the only other results are the
  tangent-bundle identities `TangentBundle.symmL_trivializationAt`,
  `symmL_trivializationAt_eq_core` and `symmL_model_space`. There is no smoothness statement for
  `symmL`, so the lemmas are not duplicates.
- `naming_norm` for both lemmas: `subject_unresolved`, so naming was not measured by the tool.
- `precedent_search`: nearest hits are Patrick Massot's suggestions on PR #26112/#25383 in the same
  file (notation and binder spelling for the `hom_bundle` lemmas). None applied directly.
- `zulip_search`: the statement comes from the #mathlib4 thread "Trivialization smoothness".
  Patrick Massot asked for it there (2026-06-26) and Jack McCarthy gave an MWE (2026-07-02) with
  the same `[IsManifold IB k B]` binder and `TotalSpace.proj` spelling that the PR uses.

## Object by object

### `section symmL` / variable block / `end symmL`
- The variable block redeclares a subset of the first section's variables and adds
  `[∀ x, IsTopologicalAddGroup (E₁ x)] [∀ x, ContinuousSMul 𝕜 (E₁ x)]`. These two are needed:
  they give the hom bundle `fun b ↦ F₁ →L[𝕜] E₁ b` its topology and charted-space structure.
  The other sections of this file also declare their own blocks, so this one follows the file's
  pattern. No finding.

### `Bundle.Trivialization.contMDiffAt_symmL`
- Generalization, finding 1: `[IsManifold IB n B]` is not needed. The lemma compiles with the
  binder removed and the proof unchanged, checked for this lemma alone and for both lemmas
  together. An in-file `#lint only unusedArguments` reports nothing, but it also did not flag a
  plainly unused `(h : x = x)` in a calibration lemma, so it is not a reliable probe here and I
  claim no CI failure. Filed as advisory.
- Style, finding 2: the file uses `CMDiffAt`/`CMDiff[s]` everywhere else. The notation needs
  `(E := fun b ↦ F₁ →L[𝕜] E₁ b)`, the same device as line 302. Verified that the statement
  compiles in that form and that it closes the PR's original form. `T% (e.symmL 𝕜 ·)` does not
  elaborate.
- Style, finding 3: `Trivialization F₁ (TotalSpace.proj : TotalSpace F₁ E₁ → B)` should be
  `Trivialization F₁ (π F₁ E₁)`, as in the rest of the file. Verified.
- Documentation, finding 4: the docstring omits the atlas-membership hypothesis that the
  statement needs.
- Proof: checked, no finding. Replacing `refine contMDiffAt_totalSpace.mpr ⟨contMDiffAt_id, ?_⟩`
  with `rw [contMDiffAt_section]` compiles. It saves nothing substantive, and in that variant the
  `unusedSimpArgs` linter reports `e.mk_symm hb` as unused, yet removing it makes the proof fail.
  I would not ask for it. Dropping `e.mk_symm hb` from the original proof also fails. The proof
  is short and uses the canonical `congr_of_eventuallyEq` + `filter_upwards` pattern (compare
  `contMDiff_zeroSection` in Basic.lean).
- Naming: `contMDiffAt_symmL` / `contMDiffOn_symmL` follow `contMDiffAt_coordChangeL` /
  `contMDiffOn_coordChangeL` and name the function by its head, `symmL`. No finding.
- Line lengths: all added lines are at most 100 characters; the two lemma header lines are
  exactly 100.

### `Bundle.Trivialization.contMDiffOn_symmL`
- The proof `fun _ hx ↦ (e.contMDiffAt_symmL hx).contMDiffWithinAt` is canonical. The same
  `IsManifold`, notation, `π` and docstring points apply; findings 1-4 cover them, since each asks
  for the change in both lemmas.

### Doc comments
- Both docstrings describe the section clearly, apart from the missing atlas hypothesis
  (finding 4). "bundle of continuous linear maps `F₁ →L[𝕜] E₁`" is loose, since formally it is
  the hom bundle from the trivial bundle `B × F₁`, but it is understandable. No separate finding.

## Considered and not filed
- The companion lemma for `e.continuousLinearMapAt`, which Patrick Massot also asked for on
  Zulip. That is scope expansion or follow-up work, not a change to this PR's code.
- `ContMDiffWithinAt`/composed-with-`f : M → B` variants, like the `coordChangeL` family. These
  are simple compositions and not needed.
- `mdifferentiable` versions: follow-up, not a defect.

## Verified edit (all four findings applied together; compiles cleanly)
```lean
lemma Bundle.Trivialization.contMDiffAt_symmL [ContMDiffVectorBundle n F₁ E₁ IB]
    (e : Trivialization F₁ (π F₁ E₁)) [MemTrivializationAtlas e] {x : B} (hx : x ∈ e.baseSet) :
    CMDiffAt n
      (fun m ↦ TotalSpace.mk' (F₁ →L[𝕜] F₁) (E := fun b ↦ F₁ →L[𝕜] E₁ b) m (e.symmL 𝕜 m)) x := by
  -- proof unchanged

lemma Bundle.Trivialization.contMDiffOn_symmL [ContMDiffVectorBundle n F₁ E₁ IB]
    (e : Trivialization F₁ (π F₁ E₁)) [MemTrivializationAtlas e] :
    CMDiff[e.baseSet] n
      (fun m ↦ TotalSpace.mk' (F₁ →L[𝕜] F₁) (E := fun b ↦ F₁ →L[𝕜] E₁ b) m (e.symmL 𝕜 m)) :=
  fun _ hx ↦ (e.contMDiffAt_symmL hx).contMDiffWithinAt
```
