# PR 26308 review notes (hard brief)

## Dossier objects

**section x3 (namespace:added) in Normalized.lean.** Questions: location and namespace. The file has no namespace, so `normalized` sits at root, next to the root `normalize` in Algebra/GCDMonoid/Basic.lean. Dropped: that is naming, the other reviewer's area. The file-placement question is folded into the imports finding.

**doc_comment / module_doc.** Wording belongs to the other reviewer. I only used them to check the stated design (junk value 0, "unit length vector"). No finding.

**import in Mathlib.lean.** The entry is correctly placed and alphabetised. The real issue is the new file's own import: `Mathlib.Analysis.RCLike.Basic` is unused and heavy. Swapping it for `Mathlib.Analysis.Normed.Module.Basic` compiled (lean_verify_edit, line 6). Filed, advisory. Also offered Real.lean as an alternative home (exhibit: `inv_norm_smul_mem_unitClosedBall`).

**def `normalized`.**
- Library: exhibit. The concept exists only unfolded (11 files: Ray.lean, Real.lean, SphereNormEquiv.lean, RCLike.lean, Tietze.lean, ...). No existing def. Filed the missing bridge to that API.
- Encoding: a total function with junk 0 is standard Mathlib style, and `homeomorphUnitSphereProd` already provides the sphere-valued version on `{0}ᶜ`. No problem, dropped.
- Generality: considered `RCLike 𝕜` like `norm_smul_inv_norm`. Dropped, since ℝ scalars also cover complex spaces through their real structure. The seminormed generalisation compiled for the whole file. Filed.
- API: `norm_smul_normalized`, `normalized_eq_zero_iff`, `norm_normalized_le_one` and `normalized_mem_sphere` compiled. Filed.

**`normalized_zero_eq_zero`.** simp, fine. It holds under Seminormed, which is covered by the generality finding.

**`norm_normalized_eq_one_iff`.** Its reverse direction is one step from `norm_smul_inv_norm` (NormedSpace/RCLike.lean:40) at 𝕜 = ℝ, but that is not a duplicate. The iff with `x ≠ 0` needs NormedAddCommGroup. In the seminormed version it becomes a primed `‖x‖ ≠ 0` lemma plus this one (compiled). No separate finding.

**`normalized_eq_self_of_norm_eq_one`.** A conditional simp lemma is fine. It holds under Seminormed. No finding.

**`normalized_normalized`.** simp, fine. It holds under Seminormed when the proof case-splits on `‖x‖ = 0` (compiled). No separate finding.

**`normalized_smul_of_pos` / `normalized_smul_of_neg`.**
- Siblings: tried to unify them as `normalized_smul : normalized (r • x) = (SignType.sign r : ℝ) • normalized x`. The compile failed only because `SignType.sign` is not imported under this file's imports. Dropped: adding `Mathlib.Data.Sign` for a convenience lemma is not clearly worth asking for.
- Both hold under Seminormed (compiled).

**`normalized_neg`.** The only unconditional equational lemma without `@[simp]`. Its direction matches `smul_neg`. Filed as an advisory automation finding (judgment). The redundant `by_cases` in its proof belongs to the other reviewer.

**Removed declarations.** None, so there are no deprecated aliases to check.

## PR as a whole
There is no description: no motivation, no design rationale, no AI disclosure, and no link to prior work (the 2020 copyright suggests there is some). Filed, advisory. The PR is one coherent thing, so no split is needed, and it contains no meta code. Zulip found no prior thread about the definition. Precedent search returned nothing that applies (the nearest hits were abbrev/readability and normalizedTrace comments), so it was dropped.
