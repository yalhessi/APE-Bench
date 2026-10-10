# Review notes: PR #30641 (`log⁺` elementary lemmas), reviewer TA1

## What I did

- Read `brief.md`, `pr.md`, `model.md` and `diff.patch`, then ran `ptool describe`.
- Read the whole file as the PR leaves it with `file_read` on
  `target/Mathlib/Analysis/SpecialFunctions/Log/PosLog.lean` (216 lines). Note that
  `posLog_norm_add_le` is base code (declaration_search: before the PR at line 170). The PR does not add it.
- Compiled the file as the PR leaves it with `lean_verify_edit` and no edit: `compiled`, no errors, no
  linter warnings.
- Ran `declaration_search` on `Real.posLog_zero`, `Real.posLog_one`, `Real.posLog_pow`,
  `Real.posLog_norm_add_le`, `Real.posLog_le_posLog`, `norm_sum_le`, `mul_max_of_nonneg`,
  `max_mul_of_nonneg` and `Real.log_pow`. None of the four new names existed at the base, so there is
  no duplication. `norm_sum_le` needs only `SeminormedAddCommGroup`. `Real.log_pow (x : ℝ) (n : ℕ)` takes
  explicit arguments.
- Ran `naming_norm` on the four new lemmas. It returned `emerging`, but it treated the subject as `log`
  and suggested `Real.log_pow` itself, so it does not bear on these names. The names follow their analogues
  (`log_zero`, `log_one`, `log_pow`) and the existing sibling `posLog_norm_add_le`.
- Ran `precedent_search` on two fragments and `zulip_search` on posLog. Neither turned up anything
  applicable.
- Edits checked with `lean_verify_edit`; all compiled unless marked:
  - `posLog_pow` with explicit `(x : ℝ) (n : ℕ)`, a one-line header, and the proof
    `rw [posLog_def, posLog_def, log_pow, mul_max_of_nonneg _ _ n.cast_nonneg, mul_zero]`.
  - `posLog_norm_sum_le` with only the instance changed to `[SeminormedAddCommGroup E]`.
  - `posLog_norm_sum_le` as the term
    `(monotoneOn_posLog (by simp) (by simp [Finset.sum_nonneg]) (norm_sum_le s f)).trans (posLog_sum s _)`.
  - `gcongr` for the monotonicity step on the file as is. This one fails: "gcongr did not make progress".
  - A new `@[gcongr] posLog_le_posLog` lemma, after which `gcongr; exact norm_sum_le s f` works.
  - Lines 182-214 together: the new docstring, the generalized `posLog_norm_sum_le` and
    `posLog_norm_add_le`, and the restored `posLog_add` docstring.
  - `posLog_zero` and `posLog_one` on adjacent lines.

## Object by object

- **`Real.posLog_zero`, `Real.posLog_one`**: correct, `@[simp]`, in simp-normal form, and new
  (declaration_search). They have no docstring, which is right for a lemma that would only restate its
  statement. Filed: remove the blank line between the parallel one-liners.
- **`Real.posLog_pow`**: correct. It is a sensible `@[simp]` lemma, the analogue of `Real.log_pow`, and the
  RHS `↑n * log⁺ a` is in simp-normal form. Filed:
  - the proof golf, which also removes the `by_cases` / `rw [not_le] at h₂a` pattern;
  - explicit binders;
  - the header, which fits on one line (74 characters), and inline `@[simp]` in front of a multi-line header;
  - the inaccurate docstring ("commutes with taking powers").
- **`Real.posLog_norm_sum_le`**: correct. Filed:
  - generalize to `SeminormedAddCommGroup`, together with the sibling `posLog_norm_add_le`;
  - inline the side goal, avoiding `apply … _` plus a separate line, and give a term proof;
  - add a `@[gcongr]` lemma so the step is `gcongr`;
  - the docstring: its layout, its framing by contrast and by proof method, the name without `Real.`, and an
    early line break;
  - the early header line break;
  - a question on whether it merely combines existing lemmas.

  The name parallels `posLog_norm_add_le`, and the argument order and explicitness match `posLog_sum`. I
  found no problem there.
- **Module docstring (top)**: filed the dotted module name (use the file path) and "Circle Average"
  capitalisation. Filed that the list of estimates omits `posLog_norm_sum_le`.
- **Section headers**: the PR adds blank lines after three section headers. Filed the remaining
  inconsistency at the first header (line 27/28).
- **`posLog_sum` and `posLog_add` docstrings**: content unchanged, only rewrapped into the `/--` / text / `-/`
  layout. Filed: revert both, since the edit is incidental and the convention puts the text on the `/--` line.

## Conventions: places filed and places left

1. *`@[simp]` on lemmas at canonical arguments.* Left: `posLog_zero` (line 56), `posLog_one` (line 58) and
   `posLog_pow` (line 102) already carry `@[simp]`. `posLog_norm_sum_le` is an inequality, not a rewrite.
2. *Drop or weaken unneeded hypotheses.* Filed at `posLog_norm_sum_le`: `NormedAddCommGroup` →
   `SeminormedAddCommGroup`, checked with a compile.
3. *`simp` does not list default simp lemmas.* Left: none of the PR's `simp` sets lists a default simp
   lemma. `pow_le_one₀`, `posLog_eq_zero_iff`, `posLog_eq_log`, `one_lt_pow₀` and `Finset.sum_nonneg` are
   not `@[simp]`, and `posLog` is the definition. The over-specified `Finset.sum_nonneg (fun …)` term is
   covered by the proof finding on `posLog_norm_sum_le`.
4. *Docstring on its own terms, not by contrast.* Filed at the `posLog_norm_sum_le` docstring
   ("Variant of `posLog_sum` …").
5. *Binder kind follows inferability.* Filed at `posLog_pow`, whose `{n} {a}` nothing infers. Left:
   `posLog_norm_sum_le` takes `(s : Finset α) (f : α → E)` explicitly and `{E} {α}` implicitly (line 187);
   `E` and `α` are determined by `s` and `f`.
6. *Closing `-/` on the last text line.* Filed at the `posLog_norm_sum_le`, `posLog_sum` and `posLog_add`
   docstrings. Left: the module docstring (line 21), where `-/` on its own line directly after the text,
   with no blank line, is the module-doc form. The section-header `/-! … -/` blocks are unchanged in form.
7. *Module docstring kept in step.* Filed: add `posLog_norm_sum_le` to the list.
8. *Break a line only past 100 characters.* Filed at the `posLog_pow` header (74 characters on one line),
   the `posLog_norm_sum_le` header (broken at 59), and the `posLog_norm_sum_le` docstring (broken at 76).
   Left: the module-doc line 19 (95 characters; the next word would push it past 100) and the `posLog_sum` / `posLog_add` docstrings, where the
   one-line form would be 101 characters.
9. *Monotonicity via `gcongr`.* Filed at `posLog_norm_sum_le`. `gcongr` fails today (checked), so the
   finding asks for a `@[gcongr] posLog_le_posLog` lemma, which compiles and makes the step `gcongr`.
10. *Attribute on its own line above a multi-line header.* Filed at `posLog_pow`, in the same finding as
    joining its header. Left: `posLog_zero` and `posLog_one` are one-line declarations (lines 56 and 58).
11. *Variant also provided for siblings.* Filed inside the generalization finding: apply the same
    `SeminormedAddCommGroup` change to the sibling `posLog_norm_add_le` (compiles). Left: no
    `posLog_mul` / `posLog_prod` norm variant exists before or after the PR, so the PR introduces no variant
    in that family. A norm version of `posLog_pow` would need a normed ring; I do not ask for it.
12. *Side goals inline in `refine`/`apply`.* Filed at `posLog_norm_sum_le`: line 191 `apply … _` followed by
    line 192 closing the hole.
13. *Same construct spelled the same way throughout a file.*
    - Filed: the section-header spacing at line 27/28.
    - Filed, as part of the revert findings: the docstring layouts at `posLog_sum` and `posLog_add`.
    - Left: `lemma` vs `theorem`. The base file is already mixed (line 206, `lemma posLog_norm_add_le`, is base
      code), so the PR's `lemma`s do not depart from a single file spelling.
    - Left: attribute placement. The PR's inline `@[simp]` on one-liners matches lines 64 and 67.
14. *Marginal-benefit changes not made.* Filed at the `posLog_sum` and `posLog_add` docstring rewraps: the
    text is unchanged and the layout gets worse.
15. *`refine`, not `apply`, for terms with holes.* Filed with item 12 at `posLog_norm_sum_le` line 191, where
    `apply` is given an explicit `_` hole. The finding asks for `exact` with the hole filled inline, or the
    term proof.
16. *Do not add mere combinations of existing lemmas.* Filed as a question at `posLog_norm_sum_le`, whose
    whole proof is `(monotoneOn_posLog …).trans (posLog_sum s _)`. Left: `posLog_pow`, `posLog_zero` and
    `posLog_one` state new facts.
17. *Statements in simp-normal form.* Left: `log⁺ 0 = 0`, `log⁺ 1 = 0` and `log⁺ (a ^ n) = ↑n * log⁺ a` contain
    no subterm simp rewrites (`Nat.cast` times `posLog`; no `abs` or literal arithmetic left).
18. *Docstring states the result in words, not a restatement.* Filed at `posLog_pow` (its words are wrong).
    Left: `posLog_zero` and `posLog_one` have no docstring, which is the form the convention asks for when
    a docstring would only restate the statement.
19. *Case split that substitutes directly.* Filed inside the `posLog_pow` proof finding: the
    `by_cases h₂a : |a| ≤ 1` followed by `rw [not_le] at h₂a` disappears with the one-line `rw` proof.
20. *Cross-reference by file path.* Filed at the module docstring, line 19.
21. *Names follow siblings.* Left: `posLog_zero`, `posLog_one` and `posLog_pow` mirror `log_zero`,
    `log_one` and `log_pow`, and `posLog_norm_sum_le` mirrors `posLog_norm_add_le` (line 206).
22. *Names in docstrings in backticks and with full names.* Filed inside the `posLog_norm_sum_le` docstring
    finding (`posLog_sum` → `Real.…`). Left: the module docstring names `posLog_prod` and `posLog_sum`
    inside `theorem …` code spans, which is unchanged base text. The `posLog_pow` docstring uses `` `log⁺` ``.
23. *Parallel one-liners adjacent.* Filed at `posLog_zero` / `posLog_one`.
24. *Docstring text begins on the `/--` line.* Filed at the `posLog_norm_sum_le`, `posLog_sum` and
    `posLog_add` docstrings. Left: the `posLog_pow` docstring (line 101) already starts on the `/--` line.
25. *PR changes existing code only where needed.* Filed at the `posLog_sum` and `posLog_add` docstring
    rewraps. Left: the blank lines after section headers. They are part of the stated docstring tidy-up,
    and I filed their inconsistency under item 13 instead.
