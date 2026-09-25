# PR 26308 review notes (Normalized.lean)

About 17 tool calls. Every proof change proposed in findings.json was compiled with `lean_verify_edit` and succeeded. A deliberately broken edit (`exact rfl`) did fail, which confirms the tool reports errors.

**Mathlib.lean**: the import is inserted alphabetically between `MultipliableUniformlyOn` and `OperatorNorm.*`. Nothing to ask.

**File header and imports**: the copyright year is 2020 on a file this PR creates, so I asked for 2025. Replacing `Mathlib.Analysis.RCLike.Basic` with `Mathlib.Analysis.Normed.Module.Basic` compiled the file unchanged. Its `field_simp` and `linarith` still resolve. So the import finding rests on a compile, not on a guess.
I also considered asking to move the file to `Analysis/Normed/Module/` (where Basic.lean and Ray.lean live). I did not ask: `Analysis/NormedSpace/` still takes new files (e.g. MultipliableUniformlyOn), and nothing I found says new files must go elsewhere.

**Module docstring**: ungrammatical, and it does not name `normalized`. This one is advisory only.

**`normalized` (def)**: I checked for duplicates by content_search for `‖x‖⁻¹ • x`: 8 files use it inline (Ray.lean `sameRay_iff_inv_norm_smul_eq`, SphereNormEquiv, Real.lean `inv_norm_smul_mem_unitClosedBall`, Tietze, Convex/Uniform, ...). None defines it as a def, so it is not a duplicate. `norm_smul_inv_norm` (NormedSpace/RCLike.lean) gives the norm-one fact over RCLike 𝕜. Using it would mean importing NormedSpace/RCLike, which works against the import finding, so I did not ask for it. Staying with ℝ is fine: a complex normed space gets `NormedSpace ℝ` through the existing instance.
I weighed three other asks and made none of them: a root-namespace clash with GCDMonoid's `normalize`, generalizing to `SeminormedAddCommGroup` (only the iff lemma needs Normed), and folding the pos/neg lemmas into one `sign`-based lemma. Each is plausible but has no evidence behind it here.
I did ask for the missing `‖x‖ • normalized x = x` (verified appended lemma compiles).

**`normalized_zero_eq_zero`**: naming_norm returned no_population. The sibling `normalize_zero` (GCDMonoid) and `norm_zero` use `f_zero`, and a grep for `_zero_eq_zero` shows it is rare. So I made the rename advisory, not blocking. The proof is fine.

**`norm_normalized_eq_one_iff`**: the name matches the statement. The simp tag is fine, since the LHS `‖normalized x‖ = 1` is in normal form. The `constructor`/`contrapose!` proof shortens to `rcases eq_or_ne x 0 ... simp [normalized, norm_smul, hx]` (compiles).

**`normalized_eq_self_of_norm_eq_one`**: the name, the conditional `@[simp]` and the one-line proof are all fine. Nothing to ask.

**`normalized_normalized`**: the `f_f` idempotence name is fine (`abs_abs`, `norm_norm`; `normalize_idem` is the only competing sibling). `by_cases hx : x = 0 <;> simp [hx]` replaces the backwards `rw ... at hx` (compiles).

**`normalized_smul_of_pos`**: the hypothesis `0 < r` is sharp, since r = 0 fails. The proof shortens to one `simp [normalized, norm_smul, smul_smul, abs_of_pos hr, hr.ne']` (compiles).

**`normalized_neg`**: the case split is unnecessary and `(- x)` has non-Mathlib spacing. It should be `@[simp]`: tagged, the whole file still compiles, including the downstream lemma.

**`normalized_smul_of_neg`**: the final `field_simp` only closes `normalized (r • x) = normalized (-r • -x)`, which is `neg_smul_neg`. The `rw [← normalized_neg, ← neg_smul_neg, normalized_smul_of_pos (neg_pos.2 hr)]` version compiles.

Tools that mattered: lean_verify_edit (all proof and import findings), content_search (duplicate check, naming siblings, `neg_smul_neg`), naming_norm (no census, so naming stays advisory). precedent_search and zulip_search turned up nothing on-point.
