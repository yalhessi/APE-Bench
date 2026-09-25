# PR 29464 — reviewer H notes

This is a documentation-only PR: the only non-comment Lean change is a pair of in-proof comments. So the
definition, typeclass, API and generality questions have nothing to act on. The live questions were the
PR as a whole, sibling consistency, and location. The dossier does not identify its same-kind entries
individually (for example, five SumTransform module docs), so below I list the entries by file and kind
and match them to the hunks of diff.patch.

## Mathlib/Computability/AkraBazzi/SumTransform.lean

**module_doc x5 (dossier entries 1, 9, 12, 16, 21)**
- File header. Asked about location and PR-as-a-whole. Moving `asympBound` into this list and dropping
  `GrowsPolynomially` is a real location fix. The bullet's "as above" points at nothing in this file, and
  the parameters are only explained in downstream AkraBazzi.lean (imported at AkraBazzi.lean:7) -> finding 5.
- "Definition of Akra–Bazzi recurrences" section: only a TeX restyle. It is the anchor I propose for
  finding 5's pointer. Nothing filed on it alone.
- "Smoothing function" section: `1 ± ε n` became `$1 \pm \varepsilon\,n$`, which reads as a product.
  `local notation "ε"` at :270 and the def at :268 settle it -> finding 3, item 1.
- "Akra–Bazzi exponent p" section: the PR correctly removes the claim that this section defines
  `asympBound`. Nothing filed.
- "The sum transform" section: omits the `n ^ p *` factor that its siblings (bullet :25-26 and the def
  docstring :548-549) state. The PR re-spaced the line and left it wrong -> finding 4.

**doc_comment x4 (entries 5, 11, 19, 22)**: the structure docstring and the docstrings of `p`,
`sumTransform` and `asympBound`. Checked each formula against its def (:550-551, :560). All correct
apart from the en dash and spacing. Dropped: wording and formatting belong to the other reviewer.

**definition `AkraBazziRecurrence` (entry 15)**: only the field docs changed. Design and encoding
questions (the `n₀` data field, `T_gt_zero'` prime, parameters vs fields) are not raised: a docs PR
should not be asked to redesign. The field docs "nonzero" -> "positive" is a genuine correction. "The
coefficients `b i`" clashes with the PR's own "parameters $b_i$" -> finding 3, item 3. Also noticed but
dropped: `g_nonneg` is still documented as "`g` is nonnegative" although it holds only for x ≥ 0 (minor
wording, other reviewer), and the trailing-period changes are formatting.

## Mathlib/Computability/AkraBazzi/AkraBazzi.lean

**module_doc x3 modified (entries 4, 13, 17) + 1 removed (entry 7)**
- File header. The sum's `g(n)` -> `g(u)` is a real fix, and dropping the `asympBound` bullet matches
  where it is defined. The rest is TeX restyle and synonym swaps -> finding 2 (Zulip "LaTeX in
  docstrings": Wieser and Nash on unicode first). The en dash is fine: it matches docs/1000.yaml:414
  ("Akra–Bazzi theorem"), and no hyphenated spelling remains anywhere (content_search), so there is no
  sibling inconsistency. Dropped: `ε` reused in "$(\log n)^{1+ε}$" in a file where `ε` is local notation.
  That wording is pre-existing.
- "Technical lemmas" and "Main proof" section headers: `####` -> `###` and wording only. Formatting,
  dropped.
- Removed "Definition of Akra-Bazzi recurrences" section: correct removal, because it duplicated
  SumTransform.lean:42-49, where the structure actually lives. Nothing filed.

**doc_comment x5 (entries 2, 6, 8, 14, 23)**: the docstrings of `isBigO_asympBound`,
`isBigO_symm_asympBound`, `isTheta_asympBound` and the two main lemmas, plus the in-proof comments. The
theorem docstrings correctly change `∑_u^n` to `\sum_{u<n}`. Nothing beyond restyle. Noticed and dropped
as out of scope: docs/1000.yaml:415 cites `isBigO_asympBound` (upper bound only) for "Akra–Bazzi
theorem" rather than `isTheta_asympBound`. That file is not in this PR.

**theorem `T_isBigO_smoothingFn_mul_asympBound` (entry 18)** and **theorem
`smoothingFn_mul_asympBound_isBigO_T` (entry 3)**: only the docstring wording and comments changed. The
`b` -> `b'` comment fix is right (`b'` is bound in the proof). But the ratio comments (:496, :649), now
in Lean syntax, omit the `(1 ∓ ε n)` factor that the code at :500 and :652 has -> finding 3, item 2.
No statement change, so no generality, automation or sibling question applied. No compile call was
needed: nothing I filed asks for a Lean change.

## Mathlib/Computability/AkraBazzi/GrowsPolynomially.lean

**module_doc (entry 20)** and **doc_comment on `GrowsPolynomially` (entry 10)**: TeX restyle of the
module doc. The def docstring keeps the same inequality in backticks, which is part of the churn in
finding 2. Checked the math against the def: correct, though the "for any b" gloss hides that c₁ and c₂
depend on b. That imprecision predates the PR, so dropped.

## The PR as a whole
- Empty description, only "by way of LLM" in the title. The ask is to list the corrections and state
  the human check -> finding 1 (Zulip, Massot 2025-02-19). No in-tree AI policy file exists
  (content_search in target/ found none).
- It is one thing (docs in one directory), so no split is needed beyond trimming the restyle (finding 2).
- The precedent_search hits (Stirling, TuringDegrees) were about other matters and did not bear on this
  PR. Dropped.
- Tool calls used: about 17. No lean_verify_edit: nothing I filed asks for a Lean change.
