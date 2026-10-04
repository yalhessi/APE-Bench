# Review notes: PR #33098 (minimal covers and maximal separated sets)

## Method

- Read `brief.md`, `pr.md`, `model.md` and `diff.patch`.
- The file tools found no files until the first `lean_verify_edit` call materialised the workspace. After that the reviewed file was at
  `target/Mathlib/Topology/MetricSpace/CoveringNumbers.lean`.
- Compiled the file as the PR leaves it: it compiles, with no errors and no warnings.
- Read the whole reviewed file, the API of `Cover.lean` (proofs omitted) and the declaration list of `MetricSeparated.lean`.
  Looked up `ENat.exists_eq_iInf`, `ENat.exists_eq_iSup_of_lt_top` and `Set.Finite.eq_of_subset_of_encard_le`.
- Every proposed edit was checked with `lean_verify_edit`, and all of them compiled. The edits are saved as `tmp/a1.json` to `tmp/a17.json`.
- Ran `naming_norm` on the `card_*` lemmas and on `coveringNumber_subset_le`. Tried `precedent_search` on the `minimalCover` definition
  and on `card_le_of_isSeparated`; the hits were unrelated. A `zulip_search` on covering and packing numbers also found nothing relevant.

## Object by object

- **module_doc**: the new sections are accurate. The "extenal" typo in the `externalCoveringNumber` bullet is still there, in a docstring
  this PR rewrites (advisory finding).
- **exists_set_encard_eq_coveringNumber**
  - The proof detours through a finite cover `C'` only to get `Nonempty`, which `IsCover.rfl` gives for free (golf, verified).
  - The existential is spelled `∃ C, C ⊆ A ∧` rather than `∃ C ⊆ A,` (style).
  - The hypothesis is not needed except for finiteness; see the `minimalCover` generalization.
- **minimalCover**
  - `open Classical in` is unnecessary: it compiles without it, and the sibling definition has none.
  - Generalization: define it unconditionally, so that only finiteness needs `coveringNumber ε A ≠ ⊤`. This was verified by replacing
    the whole block.
  - The docstring is otherwise fine.
- **minimalCover_subset, finite_minimalCover, isCover_minimalCover, card_minimalCover**
  - All four are correct.
  - They repeat the `simp only [..., ↓reduceDIte]` pattern; `dif_pos` or `split_ifs` is shorter (verified).
  - `finite_minimalCover` has a needless line break (verified).
  - `card_minimalCover` should be named `encard_` (`naming_norm`: established, 84 of 88).
  - The name `finite_minimalCover` is fine: it follows the `Set.finite_*` style.
- **exists_set_encard_eq_packingNumber**
  - The empty-set case split is unnecessary, because `∅` gives `Nonempty` (golf, verified).
  - The hypothesis is genuinely needed: a packing number can be `⊤` without being attained. My counterexample is clusters of n points at
    pairwise distance 2, with distance 1 between clusters, and ε = 1.
- **maximalSeparatedSet**
  - The definition is correct.
  - The API has no `finite_maximalSeparatedSet`: `declaration_search` finds none, and adding one compiles.
  - No `open Classical` problem here.
- **maximalSeparatedSet_subset**: correct, with the same `dite` pattern (covered by the `dif_pos` finding). Nothing else.
- **isSeparated_maximalSeparatedSet**: correct. The redundant `(… : Set X)` ascription can go (verified).
- **card_maximalSeparatedSet**: correct. Should be named `encard_` (established).
- **card_le_of_isSeparated**
  - The name does not mention `encard` or `maximalSeparatedSet`. Proposed name: `IsSeparated.encard_le_encard_maximalSeparatedSet`,
    for dot notation (verified).
  - The proof re-unfolds `packingNumber` instead of using `IsSeparated.encard_le_packingNumber` (verified).
  - After the `isCover` rewrite it has no use in the file.
- **isCover_maximalSeparatedSet**
  - The main finding. The 30-line manual proof duplicates `Metric.IsCover.of_maximal_isSeparated` in `Cover.lean`, which this file
    already imports.
  - Proving maximality and applying that lemma compiles (verified in two variants).
  - That rewrite also removes the `by_contra`/`push_neg` pair (which would otherwise be `by_contra!`) and the needless `classical`.
- **coveringNumber_le_packingNumber**
  - The statement is correct and fully general: no hypothesis is needed.
  - The proof should use `IsCover.coveringNumber_le_encard` and split on `= ⊤` (verified).
  - It has no docstring, while its neighbour does (advisory).
- **coveringNumber_two_mul_le_externalCoveringNumber**: correct. The case split and the unused `h_nonempty` go; it becomes a one-line term
  proof (verified, 99 characters).
- **coveringNumber_subset_le**
  - The statement is correct.
  - The calc re-derives the PR's own `coveringNumber_two_mul_le_externalCoveringNumber`, uses `ring_nf` for `ε = 2 * (ε / 2)`, and has
    unindented steps (golf, verified).
  - I also checked restating it as `coveringNumber (2 * ε) A ≤ coveringNumber ε B`, which compiles (`tmp/a10.json`). I did not submit it:
    the module doc deliberately advertises the `ε / 2` form.
  - `naming_norm` is inconclusive on the name, so I made no naming finding.
- **section commands** (`MinimalCover`, `MaximalSeparatedSet`, `Comparisons`): balanced and sensibly placed. Nothing to request.

## Checked, nothing requested

- Correctness: the file compiles, and I found no semantic error in any statement.
- Generalization: the `PseudoEMetricSpace` setting is already the right level.
- Scope: everything belongs in this file. No move or split is needed.
