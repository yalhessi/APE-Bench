# PR 29464: reasoning notes

The PR changes only docstrings and comments (no statement or proof changes). That rules out
proof-golf, generalization, duplication and naming for every target. The review concentrated on
documentation correctness, style and consistency.

## Mathlib/Computability/AkraBazzi/AkraBazzi.lean

- **Module docstring.** Checked the corrected formula against `asympBound_def'` (SumTransform
  l.567-569: `n ^ p * (1 + ∑ u ∈ range n, g u / u ^ (p + 1))`). The fix from `g(n)` to `g(u)` is
  right. Dropping `asympBound` from "Main definitions" is right, since it is defined in
  SumTransform.lean. Asked for backticks on `T : ℕ → ℝ`, one consistent spelling of the sum, and a
  re-wrap of l.19-22. Evidence: Eric Wieser's convention via zulip_search. content_search shows
  inline `\sum` LaTeX in about 25 Mathlib files, so LaTeX itself was not flagged; `$$` display math
  occurs only in this file, but I found no rule against it.
- **Removed "Definition of Akra-Bazzi recurrences" block.** It was a stale copy; the structure lives
  in SumTransform.lean, which still has that section doc. The removal is correct, but it left three
  blank lines (file_read l.63-65), which I flagged.
- **`### Technical lemmas` / `### Main proof` headers, docstrings of `T_isBigO_smoothingFn_mul_asympBound`
  and `smoothingFn_mul_asympBound_isBigO_T`.** Wording only; the claims still match the
  statements. Nothing to ask.
- **Proof comments inside the two main lemmas.** The PR rewrote them in Lean syntax. The ratio
  omits the `(1 ∓ ε n)` factor that `base_max` / `base_min` actually use (file_read l.496-500 and
  l.649-652). The lower-bound comment also still says `g(n)` (l.654). Filed one finding per lemma.
  lean_verify_edit on the corrected l.496 comment compiled.
- **`isBigO_asympBound`, `isBigO_symm_asympBound`, `isTheta_asympBound` docstrings.** The new
  `\sum_{u < n}` matches `asympBound` (range n). The old backticked pseudo-code was neither Lean nor
  LaTeX, so under the Zulip convention the switch to LaTeX is fine. Nothing to ask.
- **TODO (`ℓ · T(r(n))`).** Correct simplification of the old `ℓT(r_i(n))`. Nothing to ask.
- Search: content_search found no hyphenated "Akra-Bazzi" left anywhere in the tree, and
  docs/1000.yaml already uses the en dash, so the dash change is consistent.

## Mathlib/Computability/AkraBazzi/GrowsPolynomially.lean

- **Module docstring.** Compared it against the definition (l.37-39). The LaTeX version drops "there
  exist c₁, c₂ > 0" and "for sufficiently large n", so it no longer states the condition. Filed
  as advisory. The implementation-notes paragraph is only reworded and is still accurate.
- **`GrowsPolynomially` docstring.** Only spacing changed (`b * n`, `(0, 1)`), and it keeps
  "roughly". Nothing to ask beyond the module-doc finding.

## Mathlib/Computability/AkraBazzi/SumTransform.lean

- **Module docstring.** Removing the `GrowsPolynomially` bullet (it is defined in the other file)
  and adding `smoothingFn`, `p` and `asympBound` bullets is correct, and I checked each against its
  definition (l.268, l.529, l.560). Flagged the dangling "as above" and the slash-fragment
  parentheticals (l.19-24).
- **"Definition" section doc, `AkraBazziRecurrence` docstring.** Fine.
- **`AkraBazziRecurrence` field docs.** The `a_pos` fix from "nonzero" to "positive" matches `0 < a i`,
  and the `dist_r_b` wording matches the statement. Periods were added to only some fields
  (l.55-75), so I asked for consistency.
- **"Smoothing function" section doc.** `$1 \pm \varepsilon\,n$` renders ε·n, whereas `ε n` is
  application of `smoothingFn` (l.268-270). This is the one blocking finding. lean_verify_edit with
  a backticked `1 ± ε n` compiled.
- **"Akra–Bazzi exponent `p`" section doc.** The old text said this section defines `asympBound`;
  the new text says it is defined in the next section, which is correct (asympBound is at l.560,
  after "The sum transform" header at l.538). Nothing to ask.
- **`p`, `sumTransform`, `asympBound` docstrings, "The sum transform" section doc.** Checked against
  the definitions (l.529, l.550-551, l.560, and asympBound_def' at l.567-569); all accurate.
  Nothing to ask.
- Not flagged: the untouched docstring of `injective_sumCoeffsExp` (l.521, unbackticked math),
  because it is outside the diff.

Tools that mattered: file_read (definitions next to docs), content_search (dash consistency,
`$$`/`\sum` prevalence), zulip_search (LaTeX-vs-backticks convention), and two lean_verify_edit
compile checks. precedent_search returned nothing applicable.
