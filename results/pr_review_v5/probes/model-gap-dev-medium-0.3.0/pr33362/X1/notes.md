# Review notes: PR #33362 (weaken assumptions in Schwarz lemma)

Inputs read: `pr.md`, `model.md`, `diff.patch`, and the reviewed file
`target/Mathlib/Analysis/Complex/Schwarz.lean` read in full through `ptool file_read`, with proofs shown.

As the PR leaves it, the file compiles with no errors or warnings (`lean_verify_edit` as-is check).
Downstream use (`content_search` over the tree): no file other than Schwarz.lean uses any lemma in
this file. `Mathlib.lean` imports it, and `docs/overview.yaml` names
`Complex.norm_le_norm_of_mapsTo_ball_self`, which still exists. So removing the `hc` argument, changing
the conclusion of `dist_le_dist_of_mapsTo_ball_self`, and making `schwarz_aux` private break nothing
in Mathlib.

## Object by object

- **Module docstring**
  - Findings 1 and 2.
  - The bullets for `norm_deriv_le_one_of_mapsTo_ball` and `dist_le_dist_of_mapsTo_ball_self` were
    rewritten by the PR, and they still describe a fixed-point, `ℂ → ℂ` version. The
    `dist_le_dist_of_mapsTo_ball_self` bullet also gives the old conclusion.
  - The `norm_le_norm_of_mapsTo_ball_self` bullet was not updated at all.
  - Two cited names (`abs_deriv_le_div/one_of_mapsTo_ball`) do not exist (`declaration_search`: 0/0).
  - A corrected text for lines 16-34 compiles.
  - Removing the TODO "strict unless affine" is fine. The equality case is already
    `affine_of_mapsTo_ball_of_exists_norm_dslope_eq_div`, under `[StrictConvexSpace ℝ E]`. Without
    strict convexity the TODO is false: for example `z ↦ (z, z²)` into ℂ² with the sup norm has
    equality and is not affine. No finding.
- **`open scoped Topology ComplexConjugate`**
  - Finding 7.
  - `conj` is never used. Reverting to `open scoped Topology` compiles cleanly.
- **`variable` block** (adds `R`, merges the two sections): fine. `R` is used by the same-radius
  lemmas.
- **`Complex.schwarz_aux`** (now `private`, moved before `@[expose] public section`)
  - Statement and proof changes are correct (`← mem_closedBall_iff_norm`, direct `h_maps`).
  - Privatizing it breaks nothing: it has no users outside the file.
  - I considered asking to keep the old layout, with `public section` at the top and only `private`
    added. The current layout is valid and I had no evidence that maintainers prefer the other, so no
    finding.
  - I also tried to generalize the aux lemma to `f : ℂ → E` and drop the dual-vector reduction in
    `norm_dslope_le_div_of_mapsTo_ball`. `lean_verify_edit` fails: `differentiableOn_dslope` needs
    `CompleteSpace E`. The dual-vector detour is what avoids that assumption, so no golf is available.
    No finding.
- **`Complex.norm_dslope_le_div_of_mapsTo_ball`**: `hR₂ : 0 ≤ R₂` via `nonempty_closedBall`, and the
  `mapsTo_closedBall` switch lets `hg₀` go. Correct and minimal. The minor `.1`/`.mp` inconsistency is
  not worth an ask.
- **`Complex.affine_of_mapsTo_ball_of_exists_norm_dslope_eq_div`** and **`...'`**
  - Weakened hypothesis; the dropped `by_cases h : z = c` was redundant. The file compiles.
  - `Set.MapsTo` is written with `Set` open. This is pre-existing and a nit, so not raised.
  - The primed lemma has no docstring. This is pre-existing and out of scope.
- **`Complex.norm_deriv_le_div_of_mapsTo_ball`**
  - Finding 3: the docstring still says "open ball".
  - `h₀ : 0 < R₁` is still needed: an empty ball makes the hypotheses vacuous.
- **`Complex.dist_le_div_mul_dist_of_mapsTo_ball`**: the docstring was updated. The proof did not
  change. Nothing to raise.
- **`Complex.norm_deriv_le_one_of_mapsTo_ball`**
  - Finding 4: the docstring is stale (`ℂ → ℂ`, fixed point).
  - The generalization and its proof are fine.
- **`Complex.dist_le_dist_of_mapsTo_ball_self`**
  - Finding 5: the docstring is stale, including its conclusion.
  - The proof (`simpa` with `R ≠ 0`) is fine.
  - I considered a rename, since `_self` no longer means "to itself". Renaming would need a
    deprecation for a marginal gain, and I had no evidence a maintainer would ask. Not raised.
- **`Complex.norm_le_norm_of_mapsTo_ball_self`**
  - Finding 6: the rewritten docstring omits `f 0 = 0`, and without it the statement is false.
  - The hypothesis `h₀` is still needed.
  - The proof is fine.

## Tool log

- `file_read`: the whole file.
- `content_search`: users of each lemma, and the stale names.
- `declaration_search`: the two stale names.
- `precedent_search`: the aux lemma. No applicable precedent.
- `lean_verify_edit`:
  - as-is check;
  - `ComplexConjugate` removal;
  - the four docstring edits and the module-doc edit;
  - the E-valued `norm_dslope` proof, which failed on `CompleteSpace E`.
