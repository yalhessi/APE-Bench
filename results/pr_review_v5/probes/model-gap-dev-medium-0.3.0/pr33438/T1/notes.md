# Review notes: PR #33438 (`arctan (√3) = π / 3` and `arctan (√3)⁻¹ = π / 6`)

Inputs: I read pr.md (no description), model.md (two added `@[simp]` theorems in one family) and diff.patch (one hunk in
`Mathlib/Analysis/SpecialFunctions/Trigonometric/Arctan.lean`, inserted after `arctan_one`).

## Whole file
- `file_read` on lines 1-300 of the PR's Arctan.lean gave me the context: the module doc, `arctan_tan`,
  `arctan_eq_of_tan_eq`, `arctan_one`, `arctan_eq_pi_div_four`, `arctan_neg`, `arctan_eq_neg_pi_div_four`
  and `arctan_inv_of_pos`.
- `lean_verify_edit` with no edit: the file compiles with no errors and no linter warnings.
- Module docstring: it describes the file's themes (inequalities, identities, the OrderIso, `arctan_add`). Special
  values are not listed there, and `arctan_one` is not either, so no doc update is needed.

## `Real.arctan_sqrt_three`
- Statement: `tan_pi_div_three : tan (π / 3) = √3` is at Basic.lean:890. The LHS `arctan (√3)` is simp-normal:
  `simp?` closes it with `simp only [arctan_sqrt_three]`.
- Proof: the `rw` plus `all_goals · field_simp; norm_num` proof works, but the sibling `arctan_one` uses
  `arctan_eq_of_tan_eq tan_pi_div_four <| by constructor <;> linarith [pi_pos]`. The same term-mode proof with
  `tan_pi_div_three` compiles cleanly. This is finding 1 (proof-golf and style, advisory).
- Naming: `naming_norm` says `conforms` (`arctan_` is used by 26/26 declarations). The `_sqrt_three` suffix reads
  `arctan √3` in order, so there is nothing to ask.
- Duplication: `declaration_search` and a regex `content_search` over all 7,440 Mathlib files found no existing
  `arctan` lemma about `√3`. Nothing duplicated.
- Generalization: a closed-form constant has nothing to generalize. The sibling pattern suggests iff companions
  (finding 3).
- Docstring: the neighbouring `arctan_one` has none. I did not request one.

## `Real.arctan_inv_sqrt_three`
- Statement: `tan_pi_div_six : tan (π / 6) = 1 / √3` (Basic.lean:885). The PR states the LHS as `(√3)⁻¹`, which is
  the right simp-normal form: `simp?` on `arctan (1 / √3) = π / 6` uses `one_div` and then `arctan_inv_sqrt_three`, and
  `arctan (tan (π / 6))` also reaches it by simp. The statement and the `@[simp]` attribute are fine.
- Naming: `conforms`. `inv_sqrt_three` matches the reading of `(√3)⁻¹` (compare `Real.sqrt_inv` for `√x⁻¹`).
- Proof: the same roundabout `rw` plus `all_goals` structure. `arctan_eq_of_tan_eq (by simp) <| by constructor <;>
  linarith [pi_pos]` compiles cleanly, and so does `(by rw [tan_pi_div_six, one_div])`. This is finding 2
  (advisory). I also considered deriving it from `arctan_sqrt_three` through `arctan_inv_of_pos`, but the direct
  form matches `arctan_one` better.

## Family-level
- `arctan_one` has an `@[simp]` iff partner, `arctan_eq_pi_div_four`, and the PR inserts the new lemmas between the
  two. `arctan_eq_pi_div_three` and `arctan_eq_pi_div_six`, both via `arctan_injective.eq_iff'`, compile with `@[simp]`
  and no warnings. This is finding 3, advisory: it is an API-completeness ask and could reasonably be left to a
  follow-up.

## Tools that did not help
- `precedent_search`: the nearest hit was a nit on calc layout in Trigonometric/Basic.lean (#25009). It does not
  apply here.
- `zulip_search`: found a thread on naming trig special values (`2 * π / 3` vs `π * 2 / 3`). The new names use
  plain `π / 3` and `π / 6`, as the existing `tan_pi_div_three` and `tan_pi_div_six` do, so it does not apply.
- `proof_profile`: unavailable (no declaration table for the base commit).

## Correctness
- Both lemmas are true and the file builds without warnings. There are no correctness or build findings.
