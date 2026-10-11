# Review notes: PR #33438 (`arctan (√3) = π / 3` and `arctan (√3)⁻¹ = π / 6`)

## What I did

- Read `pr.md`, `model.md` and `diff.patch`. The PR adds two `@[simp]` theorems to
  `Mathlib/Analysis/SpecialFunctions/Trigonometric/Arctan.lean`, between `arctan_one` and
  `arctan_eq_pi_div_four`.
- Read the file as the PR leaves it (lines 1-299) and `Trigonometric/Basic.lean` lines 820-900, where
  `tan_pi_div_six : tan (π / 6) = 1 / √3` and `tan_pi_div_three : tan (π / 3) = √3` are declared.
- The file compiles as the PR leaves it, with no errors or warnings (`lean_verify_edit`, no edit).
- `naming_norm` on both names returns `conforms`, with `arctan_` at 26/26.
- `declaration_search` on `tan_pi_div_three/six/four` and `arctan_one`. A `content_search` for
  `arctan (√3`, `arctan_sqrt` and `sqrt_three` over the whole tree finds only the PR's two lemmas, so
  neither is a duplicate.
- `precedent_search` and `zulip_search` returned nothing that applies to this PR.
- `proof_profile` was unavailable: no declaration table was built for the base commit.

## Object by object

### `Real.arctan_sqrt_three`
- Statement: the LHS applies `arctan` to a canonical argument and the RHS `π / 3` is simpler, so
  `@[simp]` is right. The name conforms. The placement right after `arctan_one` is right.
- Proof: `rw [← tan_pi_div_three, arctan_tan]`, then `all_goals` with a focusing dot on the next line
  at the same indent, running `field_simp; norm_num`. This works but is oddly formatted, and it is a
  normaliser chain where `linarith [pi_pos]` suffices. Both of these compile:
  - the term `arctan_eq_of_tan_eq tan_pi_div_three <| by constructor <;> linarith [pi_pos]`, which
    is `arctan_one`'s form;
  - `rw [...] <;> linarith [pi_pos]`.

  Filed as finding 1.
- Missing iff companion: `arctan_eq_pi_div_three`, parallel to `arctan_eq_pi_div_four`. Filed as
  finding 3, with the `arctan_inv_sqrt_three` companion; the companions compile.
- It is a `theorem` with no docstring. Filed as finding 4, which covers both lemmas.

### `Real.arctan_inv_sqrt_three`
- Statement: the LHS `arctan (√3)⁻¹` is in simp-normal form. Both
  `example : arctan (1 / √3) = π / 6 := by simp` and
  `example : arctan (√(1 / 3)) = π / 6 := by simp` compile with the lemma in scope. `@[simp]` is
  right, and the name reads head-first (arctan, inv, sqrt, three) and conforms.
- Proof: the extra `inv_eq_one_div` rewrite exists only to match `tan_pi_div_six`'s `1 / √3` form,
  followed by the same `all_goals` / `field_simp; norm_num` block. These compile:
  - `arctan_eq_of_tan_eq (by simp) <| by constructor <;> linarith [pi_pos]`;
  - the same with `(tan_pi_div_six.trans (one_div _))` in place of `(by simp)`.

  Deriving it from the sibling with `rw [arctan_inv_of_pos (by positivity), arctan_sqrt_three]; ring`
  fails in place, because `arctan_inv_of_pos` is declared later at line 260. It compiles once the
  lemma is moved after `arctan_inv_of_pos`. Filed as finding 2.

### The file
- Nothing else changed. No module-docstring update is needed: the docstring describes the file's
  general content, not individual values.

## Conventions: where filed and where left

- **simp tag on canonical-argument lemmas.** Left: both lemmas already carry `@[simp]` (diff lines
  `+@[simp]` above each).
- **Finishing tactic, not hand-written steps.** Filed: findings 1 and 2. `linarith [pi_pos]` replaces
  `field_simp; norm_num`.
- **Derive from existing API.** Filed: finding 2 (`arctan_eq_of_tan_eq`, or `arctan_inv_of_pos` with
  the sibling) and finding 1 (`arctan_eq_of_tan_eq`).
- **Merge consecutive calls.** Filed within findings 1 and 2: `field_simp` then `norm_num` become one
  `linarith`.
- **Name built from the statement's declarations.** Left: `arctan`, `inv`, `sqrt` and `three` match
  `arctan (√3)⁻¹`, and `naming_norm` says `conforms`.
- **Automation only if not slower or less readable.** Left: no automation is being introduced. The
  suggestion goes the other way, to a short explicit term.
- **Characterisation in variant forms.** Filed: finding 3 (the iff forms).
- **Short tactic block as a term.** Filed: findings 1 and 2 (the term-mode proofs).
- **Head-first name order.** Left: `arctan_inv_sqrt_three` follows the term structure
  `arctan (Inv.inv (Real.sqrt 3))`.
- **No chain of flexible normalisers.** Filed in findings 1 and 2 (`field_simp` then `norm_num`).
- **No new declaration duplicating existing ones.** Left: `content_search` found no existing
  `arctan (√3 …)` lemma.
- **Sibling variants for every member of the family.** Filed: finding 3. The `arctan_one` family has
  `arctan_eq_pi_div_four` and `arctan_eq_neg_pi_div_four`.
- **Side goals inline in refine/apply.** Covered by findings 1 and 2: the side goals are discharged
  inline as `<| by constructor <;> linarith [pi_pos]`.
- **Remove unneeded steps.** Filed in finding 2: the `inv_eq_one_div` rewrite becomes unnecessary.
- **Squeeze a simp whose result is consumed.** Covered by findings 1 and 2, which remove the
  `field_simp`/`norm_num` pair altogether.
- **No lemma that merely instantiates or combines others.** Left: these are genuine special values,
  parallel to `arctan_one`, and not reshapings of an existing statement.
- **Iff and equation direction.** Left: in `arctan (√3) = π / 3` the compound side is on the left.
- **Sibling goals dispatched together.** Left: the PR already uses `all_goals`. The formatting is
  covered in findings 1 and 2.
- **Simp-normal form.** Left: `π / 3` and `π / 6` are normal. The `(√3)⁻¹` form is what simp
  produces from `1 / √3` and `√(1 / 3)`; both examples compiled.
- **Name and namespace follow the siblings.** Left: `Real.arctan_sqrt_three` parallels
  `Real.arctan_one`.
- **Values one by one versus a general mechanism.** Left: this convention concerns computable
  sequences such as Bernoulli numbers. The trig and arctan special values are a fixed small set, and
  the library states them one value per lemma (`tan_pi_div_six`, `tan_pi_div_three`, `arctan_one`).
- **Grouping by notion.** Left: the new lemmas sit directly after `arctan_one`, lines 201-217.
- **`theorem` versus `lemma`.** Filed: finding 4.
- **Prevailing spelling, with bridging lemmas.** Left for this PR: `(√3)⁻¹` is the simp-normal
  spelling. `tan_pi_div_six`'s `1 / √3` is the outlier, and it is not changed here.
- **No bare `_eq` suffix.** Left: neither name has an `_eq` suffix.
