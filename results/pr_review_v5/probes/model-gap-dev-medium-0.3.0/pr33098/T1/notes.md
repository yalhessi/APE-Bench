# Review notes: PR #33098 (minimal covers and maximal separated sets)

Inputs read: `pr.md`, `model.md`, `diff.patch`. I read the whole file as the PR leaves it
(`target/Mathlib/Topology/MetricSpace/CoveringNumbers.lean`, 422 lines) and the imported API in
`target/Mathlib/Topology/MetricSpace/Cover.lean`. The as-is compile check: compiled, no errors or
warnings. Every edit proposed in `findings.json` was compiled with `lean_verify_edit`. Temporary edit
files are in `tmp/` (`e1.lean` to `e12.lean`, plus the helper `v.py`).

## Tools used
- `lean_verify_edit`: the as-is check, then about 12 edits. All proposed edits compiled with no warnings.
  The one expected failure was the rename span (e9), which failed only at an out-of-span use of the old name.
- `naming_norm` on `card_minimalCover`, `card_maximalSeparatedSet` and `card_le_of_isSeparated`:
  `established`, `encard_` 84/88. On `coveringNumber_subset_le`: insufficient_evidence (population 9).
- `declaration_search`: `Metric.IsCover.of_maximal_isSeparated` (Cover.lean:78, base),
  `ENat.exists_eq_iInf` (ENat/Lattice.lean:109, base).
- `content_search` in Data/Set/Card.lean for `Finite.eq_of_subset_of_encard_le` and `encard_ne_top_iff`.
- `precedent_search` (on `minimalCover`) and `zulip_search` (covering/packing): nothing applicable.

## Object by object

- **Module docstring**: the new "Main definitions" and "Main statements" entries match the
  declarations and their statements. The typo "extenal" predates this PR, so I did not raise it. Nothing requested.
- **`section MinimalCover` / `MaximalSeparatedSet` / `Comparisons`**: the sections are well placed, and
  `packingNumber_two_mul_le_externalCoveringNumber` was moved into `Comparisons` sensibly. Nothing requested.
- **`exists_set_encard_eq_coveringNumber`**: correct. Generalization finding: the `≠ ⊤` hypothesis is
  unnecessary, because `A` covers itself and ℕ∞ infima are attained. The finding also covers the `let h`
  that shadows `h`. Verified as a whole-section replacement (lines 233-276).
- **`minimalCover`**: `open Classical in` is redundant (verified by deleting it). The docstring is
  otherwise accurate. Whether `minimalCover` is needed at all is open, since nothing in the PR uses it. The PR
  title names it as a goal, so I did not ask to remove it.
- **`minimalCover_subset`, `finite_minimalCover`, `isCover_minimalCover`**: correct. Under the current
  design the names conform (`finite_` / `isCover_` / `_subset` match the file's own siblings). The
  `simp only [..., ↓reduceDIte]` pattern could be `rw [minimalCover, dif_pos h]`. That is a minor nit,
  and the generalization finding removes the `dite` anyway, so it is not raised separately.
- **`card_minimalCover`**: naming finding, `encard_minimalCover`.
- **`exists_set_encard_eq_packingNumber`**: correct. Proof-golf/style finding: the empty case split is
  unnecessary because `∅` witnesses the instance, and the `let`/`specialize` chain plus the binder form
  should be simplified. Verified.
- **`maximalSeparatedSet`**: the definition is fine, and the junk value `∅` is consistent with
  `isSeparated_maximalSeparatedSet` and `maximalSeparatedSet_subset` holding unconditionally. Finding: add
  `finite_maximalSeparatedSet`. The `Finite` conjunct of the exists-lemma is otherwise unused. Verified.
- **`maximalSeparatedSet_subset`**: correct, nothing requested.
- **`isSeparated_maximalSeparatedSet`**: correct. Style nit about the redundant `: Set X` ascription. Verified.
- **`card_maximalSeparatedSet`**: naming finding, `encard_maximalSeparatedSet`.
- **`card_le_of_isSeparated`**: correct, and the hypothesis `packingNumber ε A ≠ ⊤` is genuinely needed
  (with `⊤` the set is `∅`). The naming finding renames it to
  `IsSeparated.encard_le_encard_maximalSeparatedSet`; the term proof goes via `IsSeparated.encard_le_packingNumber`.
- **`isCover_maximalSeparatedSet`**: the mathematics is correct, given `IsSeparated` = pairwise
  `ε < edist` and `IsCover` = `edist ≤ ε`. Duplication finding: replace the 28-line hand proof with
  `IsCover.of_maximal_isSeparated` (7 lines, verified). The docstring should mention the hypothesis.
- **`coveringNumber_le_packingNumber`**: correct, and it matches Vershynin 4.2.8. Proof-golf via
  `IsCover.coveringNumber_le_encard` (verified). Documentation finding: the three new main theorems lack docstrings.
- **`coveringNumber_two_mul_le_externalCoveringNumber`**: correct. Proof-golf: the case split is dead,
  and a term one-liner works (verified).
- **`coveringNumber_subset_le`**: correct. Proof-golf: reuse `coveringNumber_two_mul_le_externalCoveringNumber`
  and indent the calc (verified). The division-free restatement `coveringNumber (2 * ε) A ≤ coveringNumber ε B`
  also compiles, and I mention it only as an option. The naming census gives no convention to hold the name to.

## Checked and found nothing to request
- **Correctness of statements**: all four comparisons are true as stated and compile. There are no `sorry`s and no linter warnings.
- **Imports**: unchanged and sufficient.
- **Variable binders**: the new declarations use the section variables `{A B C} {ε}` consistently with the
  existing lemmas. The explicit `(ε) (A)` on the comparison theorems matches their sibling
  `packingNumber_two_mul_le_externalCoveringNumber`.
