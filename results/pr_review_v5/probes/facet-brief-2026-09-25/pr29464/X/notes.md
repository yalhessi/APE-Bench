# PR 29464 review notes (condition X)

Documentation-only PR over three files. No proofs, statements or names change, so proof-golf, generalization, duplication and naming asks do not apply to any declaration. The review is of documentation, style, scope and the correctness of the prose and math.

## Mathlib/Computability/AkraBazzi/AkraBazzi.lean

- **Module docstring.** Fixing `g(n)` to `g(u)` in the main formula is a real correction (base :29, :37). Moving the `asympBound` bullet out is right: `asympBound` is defined in SumTransform.lean:556. En dashes are acceptable: docs/1000.yaml:414 already writes "Akra–Bazzi theorem", and Mathlib mixes both dashes elsewhere (Cauchy–Schwarz 9, Cauchy-Schwarz 29). LaTeX in docstrings is normal in Mathlib (e.g. Algebra/Field/GeomSum.lean). Asked only that the Lean type `T : ℕ → ℝ` stay in backticks and that `\sum` be used consistently (finding 2).
- **Removed "Definition of Akra-Bazzi recurrences" block.** It duplicated SumTransform.lean:39-46, where the structure is actually defined, so removing it is correct. It leaves three blank lines (finding 3).
- **Section headers `####` to `###`.** Consistent across both files after the change; nothing to ask.
- **`T_isBigO_smoothingFn_mul_asympBound` / `smoothingFn_mul_asympBound_isBigO_T`.** The docstring edits ("upper-bound", "but it is") are harmless. The edited in-proof comments still drop the `(1 ∓ ε n)` factor in the ratio (lines 503, 656 against 507, 659), and the lower-bound proof keeps `g(n)` where its twin was changed (findings 4 and 5). `b'` is the local `let` at :468, so the new `[b' * n₀, n₀)` is right.
- **`isBigO_asympBound`, `isBigO_symm_asympBound`, `isTheta_asympBound`.** The new LaTeX `\sum_{u < n}` matches `asympBound_def'` (SumTransform.lean:563-565, `range n`), and fixes the old `∑_u^n`. Nothing to ask.
- **TODO bullet** `ℓ · T(r(n))`. An improvement on `ℓT(r_i(n))`; nothing to ask.

## Mathlib/Computability/AkraBazzi/GrowsPolynomially.lean

- **Module docstring.** Only wording and LaTeX changes. The claim "equivalent to requiring it only for b = 1/2" was already there before this PR, and no lemma proves it (checked the declaration list). Not raised, since the PR only rewords it.
- **`GrowsPolynomially` docstring.** Rewritten, but still speaks of `g` and `n` while the definition binds `f` and `x` (:37-39). Finding 9.

## Mathlib/Computability/AkraBazzi/SumTransform.lean

- **Module docstring.** Removing the `GrowsPolynomially` bullet is correct: it is defined in GrowsPolynomially.lean. Adding `smoothingFn`, `p` and `asympBound` is correct: all three are defined here (:265, :526, :556), and the `asympBound` formula matches `asympBound_def'`. Asked to fix the dangling "as above" (finding 6) and to drop the vague parentheticals (finding 8).
- **"Definition of Akra–Bazzi recurrences" section and `AkraBazziRecurrence` field docs.** "nonzero" becoming "positive" for `a_pos`/`b_pos` is a genuine fix. Punctuation is now mixed, and `g_nonneg`'s docstring overstates its field (finding 10).
- **"Smoothing function" section.** `$1 \pm \varepsilon\,n$` is typeset as a product, not as `ε` applied to `n`; this one is blocking (finding 1).
- **"Akra–Bazzi exponent `p`" section.** Moving the `asympBound` sentence to "the next section" is accurate: `asympBound` is defined after "The sum transform" header at :535. Nothing to ask.
- **`p` docstring.** Dash change only; nothing to ask.
- **"The sum transform" section and `sumTransform` docstring.** The docstring matches the definition. The section doc omits the `n ^ p *` factor (finding 7).
- **`asympBound` docstring.** The LaTeX matches `asympBound_def'`; nothing to ask.

## PR level

- No description, and the title calls the changes LLM-generated. Asked for a description that separates the real corrections from the rewording (finding 11). Did not ask to split the PR; the change is small enough to review as one.
