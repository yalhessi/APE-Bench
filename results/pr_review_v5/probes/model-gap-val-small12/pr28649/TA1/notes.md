# Review notes: PR #28649 "doc(Probability): miscellaneous typo fixes"

## What I did

I read `brief.md`, `pr.md`, `model.md` and `diff.patch`. Using `ptool` I read each changed file around
its hunks and the full docstrings the PR touches (`file_read`). I checked every declaration named in
the touched docstrings (`declaration_search`) and counted how the library spells the contested words
and headings (`content_search`). I also ran `precedent_search` on the Popoviciu docstring and
`zulip_search` on "liminfs"; neither turned up anything that applies. Every edit I propose was compiled
with `lean_verify_edit`, and all of them returned `outcome: compiled` with no errors or warnings.
I found nothing to raise on proof-golf, generalization, duplication, naming or scope, because the PR
changes no code.

This file has no `message` field, so the convention-by-convention listing the brief asks for is
given below.

## Object by object

- **Gaussian/Real.lean, 7 docstrings ("gaussian" → "Gaussian").** The fix is correct. Searching the
  file for `gaussian [a-z]|gaussians` returns nothing, so after the PR "Gaussian" is consistent across
  the file. Two findings remain:
  - The edited docstrings still say "pdf" (identifier-style abbreviation). Filed.
  - Line 43 is a noun phrase ending in a full stop. Filed under the noun-phrase convention.
  - Lines 100 and 118 carry identical docstrings for the `lintegral` and `integral` lemmas. This
    predates the PR, so not filed.
- **CompNotation.lean ("compostition" → "composition").** The fix is correct and the title is
  accurate. The `/- ... -/` comment before `assert_not_exists` refers to "the `MeasureComp` file"
  rather than a path. Filed (cross-reference convention).
  - The `## Notations` heading is left: in Probability, 7 files use `## Notations` and 2 use
    `## Notation`, and it is the style guide's notation section.
  - The docstring of the `∘ₘ` notation ("Notation for `MeasureTheory.Measure.bind`") has no period,
    but the PR does not touch it. Not filed.
- **IntegralCompProd.lean ("measurablity" → "measurability").** The fix is correct. The same module
  docstring has three more problems, all filed:
  - The main-statement item names the nonexistent `ProbabilityTheory.integral_comp` (the real name
    is `ProbabilityTheory.Kernel.integral_comp`) and writes `∫⁻` for a Bochner statement. This one
    is backed by `declaration_search` and the file's namespace structure.
  - The title says "composition-products".
  - The heading is `## Implementation details` where the style guide has "Implementation notes".
  - The referenced names `ProbabilityTheory.Kernel.lintegral_comp`, `...lintegral_compProd` and
    `ProbabilityTheory.integral_compProd` exist, and `Mathlib/MeasureTheory/Integral/Prod.lean`
    exists.
- **Martingale/Convergence.lean.**
  - "Implementationwise" → "In terms of implementation": not filed. "Implementationwise" is a
    non-dictionary coinage used nowhere else in Mathlib (`content_search` found 0 hits), so
    replacing it is a spelling fix rather than a purely stylistic rewording.
  - "liminfs" → "limit inferiors": filed as a revert. "liminfs" is the library's spelling
    (`Order/LiminfLimsup.lean` title), and "limit inferiors" is an awkward plural.
  - The section docstring has a blank line before `-/`. Filed.
  - The module docstring's "part b the" / "part c the" (×2) are typos the pass missed. Filed.
  - Line 106, "has bounded upcrossing" (should be "upcrossings"), is another missed typo in an
    untouched docstring. Noted, not filed.
  - The touched lines are all within 100 columns (line 133 is 97).
- **Martingale/Upcrossing.lean ("left hand side" → "left-hand side").** The fix is correct: it is a
  compound-adjective hyphenation, and no other "hand side" occurs in `Martingale/`. In the same
  section docstring, the displayed identity `U_N = Σ 1_{U_N < N}` and the claim that `U_N` "is a
  stopping time" contradict `upcrossingsBefore_eq_sum` and `Adapted.measurable_upcrossingsBefore`,
  which sum the indicators of `{upperCrossingTime ... < N}`. Filed, with a corrected display. The
  blank line before `-/` is also filed.
- **Moments/Basic.lean ("mgfs/cgfs" → "MGFs/CGFs").** The capitalisation now conflicts with "the
  cgf exists" two lines below and with the lowercase "mgf" used across `Probability/Moments`. Filed
  as: write the terms out consistently. Also filed:
  - the unspaced formulas and the missing space after the colon;
  - list items without periods.
  - All referenced lemmas exist.
- **Moments/Variance.lean ("Popoviciu's inequality on variance" → "...variances").** The fix is
  correct: it matches the standard name of the inequality, and the docstring states what the
  inequality says. The module docstring's entry for this lemma has "at most`((b - a) / 2) ^ 2`"
  (missing space). Filed.
  - The sibling heading "**The Bhatia-Davis inequality on variance**" is not wrong, since that
    inequality's name has no "on variances". Not filed.

## Conventions: places filed and places left

1. **Title states precisely what the file proves.**
   - Filed: the IntegralCompProd title typo ("composition-products").
   - Left: the CompNotation title "Notation for the composition of a measure and a kernel", which
     matches the file's single notation. Also left: the Moments/Basic title "Moments and moment
     generating function", which the PR does not change.
2. **Closing `-/` directly after the text, no blank line before it.**
   - Filed: the Convergence section docstring (lines 101-103) and the Upcrossing section docstring
     (lines 706-708).
   - Left, because they already conform:
     - all touched one-line declaration docstrings (for example "/-- The Gaussian pdf is
       nonnegative. -/");
     - Variance "`((b - a) / 2) ^ 2`. -/";
     - Convergence:137 "to change `<` to `≠` under binders. -/";
     - Basic.lean "of `cgf`.\n-/";
     - IntegralCompProd "while the composition does not.\n-/";
     - CompNotation "for `κ` a kernel.\n-/".
   - Gaussian module docstring (lines 31-33) and Convergence top module docstring (lines 40-42): not
     touched by the PR. Noted only.
3. **Module docstring covers every main result.**
   - Filed: the IntegralCompProd Main statements entry that misnames `Kernel.integral_comp`.
   - Left: Basic.lean, whose six listed names all resolve (`declaration_search`), and Variance,
     whose Main results lists `variance_le_sq_of_bounded`.
4. **Cleanup leaves out hunks that cost readability.** Filed: the "liminfs" → "limit inferiors"
   hunk.
5. **Standard spacing.**
   - Filed: Basic.lean `μ[X^p]`, `μ[(X - μ[X])^p]`, `μ[exp(t*X)]`, `exp(- t*ε + ...)`, and
     "`...μ`:`p`th".
   - Left: the changed lines of the other files have no formulas, except Variance
     `((b - a) / 2) ^ 2`, which is already spaced.
   - Gaussian `c^2`, `(x - μ)^2` (lines 18, 31, 375, 384) are in untouched docstrings. Noted only.
6. **Full sentences ending in a period.**
   - Filed: the Basic.lean list items.
   - Left, already ending in a period: the touched Gaussian docstrings, the Convergence:133-134
     docstring and the IntegralCompProd items.
   - Left: the Variance bold title line "**Popoviciu's inequality on variances**", a heading noun
     phrase followed by a full sentence ending "`((b - a) / 2) ^ 2`."
7. **Same construct spelled the same way throughout a file.**
   - Filed: Basic.lean MGFs/CGFs against "cgf" (inside finding 4).
   - Left: Gaussian "Gaussian", which is consistent after the PR (`content_search` shows 0 lowercase
     prose hits).
8. **Only standard section headings.**
   - Filed: IntegralCompProd `## Implementation details`.
   - Left: CompNotation `## Notations` (the library's majority spelling in Probability, 7 to 2, and
     a style-guide section). Also left: the `###` headings in the Convergence and Upcrossing section
     docstrings, which title in-file sections rather than module docstrings.
9. **Changes of marginal benefit not made.** Left. The PR corrects real misspellings
   ("compostition", "measurablity") and a misnamed theorem ("on variance" → "on variances"), which
   is the exception the example names. The one hunk with negative value is filed under 4.
10. **PR title and description accurate.** Left. The title "doc(Probability): miscellaneous typo
    fixes" matches a docs-only diff confined to `Mathlib/Probability`. The description is not
    recoverable, so it could not be checked.
11. **Stylistic changes to existing prose left to the author.**
    - Filed: the "limit inferiors" revert (same finding as 4).
    - Left: "Implementationwise", because the old word was a non-dictionary coinage with 0 other
      uses in Mathlib.
    - Left: "left hand side" → "left-hand side", a hyphenation correction.
12. **Docstring naming a theorem states what it says.** Left. The Variance Popoviciu docstring
    states "The variance of a random variable `X` satisfying `a ≤ X ≤ b` almost everywhere is at
    most `((b - a) / 2) ^ 2`."
13. **List continuation lines indented two spaces.** Left. All touched lists (Basic.lean,
    IntegralCompProd, Convergence) indent their continuations by two spaces, for example
    "  and their MGFs are defined at `t`, ...".
14. **Docstring says what the value is, not a restatement of the type.** Left. The touched Gaussian
    docstrings ("... is positive when the variance is not zero") are short, but they paraphrase the
    lemma rather than restate its type. They predate the PR, which changes only capitalisation.
15. **Eponym spelled and capitalised as the name.** Left. The PR's own "Gaussian" fix makes
    Real.lean consistent (0 lowercase prose hits), and "Popoviciu", "Chernoff", "Fatou" and "Lévy"
    are already correct. "Bhatia-Davis" (hyphen rather than en dash, Variance:419) is untouched.
    Noted only.
16. **Cross-reference by file path.**
    - Filed: CompNotation "the `MeasureComp` file".
    - Left: IntegralCompProd "`Mathlib/MeasureTheory/Integral/Prod.lean`", which is already a path
      and exists.
17. **PR title `type(Area): description`.** Left: "doc(Probability): miscellaneous typo fixes"
    conforms.
18. **Notation follows the literature.** Left. "Popoviciu's inequality on variances" is the standard
    name of the inequality. The PR introduces no notation.
19. **Code names in backticks with full names.** Left. Touched docstrings backtick their
    declaration names (`tendsto_of_no_upcrossings`, `Filtration.limitProcess`, `limitProcess`,
    `mgf`, `cgf`). They sit inside `namespace MeasureTheory` / `ProbabilityTheory`, so the short
    forms resolve. "liminfs" (finding 3) is the mathematical word, not the Lean name.
20. **Full words, not identifier abbreviations.**
    - Filed: Gaussian "pdf" in the six edited docstrings, and Basic.lean "MGFs/CGFs/cgf" (inside
      finding 4).
21. **Results and TODOs in the module docstring, not in a separate comment.** Left. The CompNotation
    `/- ... -/` before `assert_not_exists` explains that assert's scope rule, not the file's results.
    The `/-! ### ... -/` blocks in Convergence and Upcrossing are section expositions placed before
    the section's lemmas, the standard use of sectioning docstrings.
22. **Unicode and backticks over LaTeX.** Left. The PR adds no LaTeX, and the changed lines
    (Convergence:90, Upcrossing:698) contain none. The surrounding expositions are built on display
    formulas unicode cannot express (`\limsup_{n \to \infty}`, `\mathbb{E}`,
    `\sum_{i = 1}^N \mathbf{1}_{...}`). Converting their inline symbols would be a stylistic rewrite
    of the author's prose (convention 11) and would mix two styles in one exposition (convention 7).
    My Upcrossing correction keeps the section's existing LaTeX style.
23. **Changes only where the purpose requires.** Left. Every hunk is a doc-only change of the kind
    the title announces. The one doubtful hunk is filed under 4.
24. **No "adapted from" comments.** Left. None appear in the touched docstrings. The "This file is to
    a large extent a copy of part of `Mathlib/MeasureTheory/Integral/Prod.lean`" note in
    IntegralCompProd's Implementation section predates the PR and explains the proof architecture,
    not a single declaration's provenance.
25. **Noun-phrase docstring without a full stop.**
    - Filed: Gaussian `gaussianPDFReal` (line 43).
    - Left: the other touched docstrings, which are sentences ("The Gaussian pdf is measurable.",
      "A realization ... is convergent.").
    - Left: the Variance bold title line, which already has no full stop.
