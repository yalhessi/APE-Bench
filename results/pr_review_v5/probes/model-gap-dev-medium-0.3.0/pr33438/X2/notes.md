# Review notes: PR #33438 (`arctan (√3) = π / 3`, `arctan (√3)⁻¹ = π / 6`)

## Setup
- I read `brief.md`, `pr.md`, `model.md` and `diff.patch`, then ran `ptool describe`.
- File tools need the `target/` prefix (for example `target/Mathlib/...`); `lean_verify_edit` takes the bare `Mathlib/...` path.
- `lean_verify_edit` with no edit: the PR file compiles, with no errors and no warnings.
- `proof_profile` is unavailable here ("no declaration table for 78ce485..."), so there is no tactic census.

## `Real.arctan_sqrt_three`
- **Proof-golf (finding 1).** The sibling `arctan_one`, directly above, proves itself in one line: `arctan_eq_of_tan_eq tan_pi_div_four <| by constructor <;> linarith [pi_pos]`.
  - The same shape with `tan_pi_div_three` (`tan (π / 3) = √3`, Basic.lean:890) compiles cleanly.
  - The PR's `rw [..., arctan_tan]` plus `all_goals` / `· field_simp; norm_num` is longer than that. Its layout is also unusual: `all_goals` sits on its own line with the bullet at the same indentation.
- **Naming.** `naming_norm` returns `arctan_` 26/26 for the subject `arctan`, verdict insufficient_evidence (prefix only). `sqrt_three` matches how `√3` is spelled in names. No finding.
- **`@[simp]`.**
  - `#lint only simpNF simpComm simpVarHead` over the file (spliced in with `lean_verify_edit`) reported "All linting checks passed" across 42 declarations.
  - The LHS `arctan √3` is in simp normal form. Its siblings `arctan_zero` and `arctan_one` are simp too. No finding.
- **Documentation.** The neighbouring special-value lemmas (`arctan_zero`, `arctan_one`) have no docstrings, and the module docstring needs no update. No finding.
- **Correctness.** It compiles and the linters pass. No finding.

## `Real.arctan_inv_sqrt_three`
- **Proof-golf (finding 2).** `tan_pi_div_six` is `tan (π / 6) = 1 / √3` (Basic.lean:885).
  - `arctan_eq_of_tan_eq (by rw [tan_pi_div_six, one_div]) <| by constructor <;> linarith [pi_pos]` compiles cleanly.
  - With `(tan_pi_div_six.trans (one_div _))` or `(by simp)` as the first argument it also compiles.
- **Deriving it from `arctan_sqrt_three` via `arctan_inv_of_pos`.** This fails: that lemma is declared later, at line 260 ("Unknown identifier"). I did not propose it.
- **Statement form.** It uses `(√3)⁻¹` rather than `1 / √3`.
  - This is right for a simp lemma: `one_div` normalises `1 / √3` to `(√3)⁻¹`.
  - I checked that `example : arctan (1 / √3) = π / 6 := by simp` closes after the lemma.
  - The simp linters pass. No finding.
- **Naming.** `inv_sqrt_three` names `(√3)⁻¹` accurately, and `naming_norm` agrees with the `arctan_` prefix. No finding.
- **Documentation and correctness.** Nothing to raise, as for the sibling.

## File / family level
- **Scope and generalization.** I considered asking for `arctan_eq_pi_div_three` / `arctan_eq_pi_div_six` iff versions to mirror `arctan_eq_pi_div_four`, and for placing the new lemmas after the `arctan_one` / `arctan_eq_pi_div_four` pair rather than between them. Both are optional extras rather than problems with the code as written, so I did not file them.
- **Other simp probes.**
  - `arctan (-√3)` does not simp at this position only because `arctan_neg` is declared later in the file. That is not a defect.
  - `arctan (√3 / 3)` is not handled, which is expected for a different spelling.
- **Duplication.** `declaration_search` finds no base-commit declaration for either name, and no `arcsin_one_half` / `arccos_one_half` style analogues. No finding.
- **Precedents and Zulip.**
  - `precedent_search` returned only unrelated trig-file comments (a `calc` layout nit, naming in geometry).
  - `zulip_search` found nothing about these lemmas.
  - Neither changed any conclusion.

## Output
`findings.json` has 2 advisory proof-golf findings, one per new theorem. I checked that it parses.
