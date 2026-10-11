# Review notes: PR #33098 (minimal covers and maximal separated sets)

## What I did

- I read `brief.md`, `pr.md`, `model.md` and `diff.patch`.
- I read the reviewed file as the PR leaves it with `ptool file_read`, on `target/Mathlib/Topology/MetricSpace/CoveringNumbers.lean`.
- I read the APIs it imports: `Cover.lean` (statements only) and `MetricSeparated.lean`, plus the relevant parts of `Data/Set/Card.lean` and `Data/ENat/Lattice.lean`.
- I compiled the file as-is. It compiles with no errors or warnings.
- I checked every proposed edit with `lean_verify_edit`. All of them reported `compiled` with no introduced errors or warnings; the edit files are in `tmp/e*.lean`.
- `naming_norm` was run on `card_maximalSeparatedSet`, `card_minimalCover`, `card_le_of_isSeparated`, `coveringNumber_subset_le` and `finite_minimalCover`.
- `precedent_search` and `zulip_search` gave nothing that bears on this code.

## Object by object

- **module doc**
  - It lists both new definitions and all four comparison results plus `coveringNumber_subset_le`, so it is in step with the code.
  - The three new bullet lists lack a blank line before them (filed).
- **`exists_set_encard_eq_coveringNumber`**
  - The statement is correct.
  - Filed:
    - The proof is roundabout: a `let` that is destructured immediately, a `Nonempty` witness obtained by unfolding `h` when `A` itself works, finiteness re-proved by a second simp, and a `Set.` prefix.
    - The statement form `∃ C, C ⊆ A ∧` should be the bounded binder.
  - The hypothesis is unnecessary (see `minimalCover`).
- **`minimalCover`**
  - Filed:
    - `open Classical in` is unused; deleting it compiles.
    - The `if`/`∅` design is unnecessary, because `ENat.exists_eq_iInf` always attains the infimum and `A` covers itself. The generalised section compiles.
    - Nothing in the PR uses the definition, and no motivation is given.
  - The docstring is accurate for the current definition.
  - `noncomputable` on its own line matches the three existing definitions (lines 69, 75 and 81), so I did not file it.
- **`minimalCover_subset`, `isCover_minimalCover`**
  - Correct; I filed nothing separately.
  - Their `simp only ...; exact` pattern disappears under the generalisation finding.
- **`finite_minimalCover`**
  - The unnecessary line break is filed.
- **`card_minimalCover`**
  - The rename to `encard_minimalCover` is filed (naming_norm: established).
- **`exists_set_encard_eq_packingNumber`**
  - The hypothesis `packingNumber ε A ≠ ⊤` is needed: a supremum of `ℕ∞` that equals `⊤` need not be attained.
  - Filed:
    - The `rcases` on emptiness is unneeded because `∅` is a witness.
    - The `let`/`specialize` chain is long-winded.
    - There are `Set.` prefixes, and the bounded binder applies here as in the covering version.
- **`maximalSeparatedSet`**
  - The definition is fine.
  - The missing `finite_maximalSeparatedSet` sibling is filed; the added lemma compiles.
- **`maximalSeparatedSet_subset`, `isSeparated_maximalSeparatedSet`**
  - Filed:
    - Both close the `⊤` branch with a terminal squeezed `simp only`, while the `minimalCover` lemmas use `simp [_, h]`.
    - `isSeparated_maximalSeparatedSet` has a redundant `: Set X` ascription and an unnecessary line break.
- **`card_maximalSeparatedSet`**
  - Filed:
    - The rename to `encard_maximalSeparatedSet` (established).
    - `simp only ...; exact` should be merged into one `simpa` or `rw [dif_pos]` call.
- **`card_le_of_isSeparated`**
  - Filed:
    - Its proof duplicates `IsSeparated.encard_le_packingNumber` (line 138).
    - Its name should be `IsSeparated.encard_le_encard_maximalSeparatedSet`.
  - If joined, the signature would be 103 characters, so the existing line break is justified.
- **`isCover_maximalSeparatedSet`**
  - The main finding is that the result exists as `IsCover.of_maximal_isSeparated` in `Cover.lean`. The four-line replacement compiles.
  - Filed in addition, in case the hand proof is kept:
    - `by_contra` + `push_neg` should be `by_contra!`.
    - `classical` is unneeded.
    - `hx_not_mem` is placed far before its use.
  - The inner `hb'`/`ha'` `have`s, the `{x} ∪ _` versus `insert`, and the trailing `simp only; rw; rwa` would all go with the replacement, so I did not file them separately.
- **`coveringNumber_le_packingNumber`**
  - Filed:
    - Manual `iInf_le`/`le_of_eq` instead of `IsCover.coveringNumber_le_encard`.
    - The `≠ ⊤` case split, which forces `simp only [ne_eq, Decidable.not_not] at h_top`.
    - `theorem` without a docstring.
- **`coveringNumber_two_mul_le_externalCoveringNumber`**
  - Filed:
    - The `rcases` on emptiness is unneeded, `h_nonempty` is unused, and the pattern has redundant parentheses; the term-mode one-liner is 99 characters and compiles.
    - `theorem` without a docstring.
- **`coveringNumber_subset_le`**
  - Filed:
    - The calc re-derives `coveringNumber_two_mul_le_externalCoveringNumber`, and `ring_nf` should be `mul_div_cancel₀`.
    - The calc indentation is inconsistent with lines 191-194, and the last step is broken although it fits.
    - The name should lead with the conclusion (advisory; naming_norm has too small a population to judge).
- **`section MinimalCover` / `MaximalSeparatedSet` / `Comparisons`**
  - These are fine.
  - `externalCoveringNumber_le_coveringNumber` sits outside `Comparisons` although the docstring lists it among the comparisons. This is minor and not filed.
- **Correctness:** the file compiles and every statement is true as stated, so I found no correctness error.

## Conventions: places filed and places left

1. **Namespace prefix already opened.**
   - Filed, as one file-level finding: `Set.` at lines 241, 284, 296, 310, 343 and 404.
   - Left: `ENat.exists_eq_iInf`, `ENat.exists_eq_iSup_of_lt_top` and `ENat.lt_add_one_iff` (`ENat` is not open), and `IsSeparated.empty` (not a redundant prefix).
2. **Definition comes with characterising lemmas.**
   - Filed: `finite_maximalSeparatedSet` is missing, at `maximalSeparatedSet`.
   - Left: `minimalCover` has subset, finite, isCover and card lemmas, and no use site unfolds either definition.
3. **Inline auxiliary `have`/`let`.**
   - Filed: `let h` in `exists_set_encard_eq_coveringNumber` and `let h_exists` in `exists_set_encard_eq_packingNumber`.
   - Left:
     - The `have : Nonempty ...` lines, which are instances consumed by typeclass search.
     - The `have`s inside `isCover_maximalSeparatedSet`, which the duplication finding removes.
4. **Terminal `simp` not squeezed.**
   - Filed: `maximalSeparatedSet_subset` and `isSeparated_maximalSeparatedSet`, each in its `⊤` branch.
   - The case-split finding removes `simp only [ne_eq, Decidable.not_not] at h_top` in `coveringNumber_le_packingNumber`.
   - Left:
     - Line 242 `simp only` feeds `exact`, which is rigid, and is removed by the golf finding.
     - Line 354 `simp only ... at h` feeds `rwa`.
     - Lines 356 and 359 feed `exact`/`rw`.
5. **Elaboration-supplied syntax.**
   - Filed: `(maximalSeparatedSet ε A : Set X)`.
   - Covered by the `coveringNumber_two_mul` finding: the `(h_empty | h_nonempty)` parentheses.
   - Left: `(C : Set X)` in the `ENat.exists_eq_*` functions, a needed subtype-to-set coercion.
6. **Merge consecutive calls.**
   - Filed:
     - `by_contra`/`push_neg` in `isCover_maximalSeparatedSet`.
     - `simp only; exact` in `card_maximalSeparatedSet` and its siblings.
     - `refine ?_; exact` in `coveringNumber_two_mul_le_externalCoveringNumber`.
   - Left: `rw [hC]; simp_rw [...]; rfl` in `exists_set_encard_eq_coveringNumber`, which I kept in my verified version and did not test merged.
7. **Name built from the statement's declarations.**
   - Filed: `card_maximalSeparatedSet`, `card_minimalCover` and `card_le_of_isSeparated` (all say `card` for `encard`).
   - Left: `exists_set_encard_eq_*`, which names `encard` and the number correctly.
8. **Motivation.**
   - Filed: `minimalCover` is unused in the PR.
   - Left: `maximalSeparatedSet`, which the comparison theorems motivate.
9. **Module doc in step.**
   - Left: lines 32-48 cover both new definitions and every main result.
10. **Unused `open`.**
    - Filed: `open Classical in` at `minimalCover`. Deleting it compiles.
11. **Dot notation.**
    - Filed: the rename to `IsSeparated.encard_le_encard_maximalSeparatedSet`, so that it is used as `h_sep.…`.
    - Left: the other qualified calls (`ENat.*`, `encard_insert_of_notMem`) do not apply a namespace function to a term of that namespace's type.
12. **Direct lemma.**
    - Filed:
      - `.trans (le_of_eq ?_)` with manual `iInf_le`, which should be `IsCover.coveringNumber_le_encard`, in `coveringNumber_le_packingNumber`.
      - `ring_nf`, which should be `mul_div_cancel₀`, in `coveringNumber_subset_le`.
13. **Line breaks only past 100 characters.**
    - Filed:
      - `finite_minimalCover` (59 characters joined).
      - `isSeparated_maximalSeparatedSet` (joined, without the ascription).
      - The last calc step of `coveringNumber_subset_le` (84 characters).
    - Left:
      - The `card_le_of_isSeparated` signature (103 characters joined).
      - The calc step `_ ≤ externalCoveringNumber (ε / 2) A := packingNumber_two_mul_…` (101 characters at the correct indent).
      - `noncomputable` on its own line, which matches the file's three existing definitions (lines 69, 75 and 81) under convention 16.
14. **Sibling variants.**
    - Filed: `finite_maximalSeparatedSet` (the sibling of `finite_minimalCover`).
15. **Unneeded step.**
    - Filed:
      - The `rcases` in `coveringNumber_two_mul_le_externalCoveringNumber`.
      - The `rcases` in `exists_set_encard_eq_packingNumber`.
      - `classical` in `isCover_maximalSeparatedSet`.
16. **Consistent spelling.**
    - Filed:
      - The calc indentation in `coveringNumber_subset_le`.
      - The `⊤`-branch `simp only` versus `simp`, in two findings.
      - `open Classical` on only one of the two parallel definitions, folded into the unused-open finding.
      - `Set.eq_empty_or_nonempty` versus line 207, in the prefix finding.
17. **Name states the conclusion.**
    - Filed: `coveringNumber_subset_le` and `card_le_of_isSeparated`.
18. **Extract an independent fact.**
    - The separated-insert argument in `isCover_maximalSeparatedSet` already exists (`IsSeparated.insert`, `isSeparated_insert_of_notMem`). It is filed under the duplication finding rather than as an extraction.
19. **Unused bound variable.**
    - `h_nonempty` in `coveringNumber_two_mul_le_externalCoveringNumber` is covered by the `rcases`-removal finding.
    - Left: every other binder is used.
20. **Case-split form.**
    - Filed: `by_cases h_top : … ≠ ⊤` in `coveringNumber_le_packingNumber`.
    - Left: the `by_cases h : … ≠ ⊤` in the API lemmas, whose `⊤` branch closes by `simp [_, h]` without rewriting `h` (for `minimalCover` it is also removed by the generalisation).
21. **Sibling naming pattern.**
    - Filed: `encard` versus `card`, in three findings, and the `IsSeparated.` namespace for `card_le_of_isSeparated`.
22. **Blank line before bulleted lists.**
    - Filed: the module doc, at lines 32, 38 and 47.
23. **`theorem` needs a docstring.**
    - Filed: `coveringNumber_le_packingNumber` and `coveringNumber_two_mul_le_externalCoveringNumber`.
    - Left: `packingNumber_two_mul_le_externalCoveringNumber`, which has a docstring.
24. **Canonical witness as a definition.**
    - Left: the witnesses (a minimal cover, a maximum separated set) are not canonical. The PR already defines them via `choose` and derives an API.
25. **`have` before first use.**
    - Filed: `hx_not_mem` in `isCover_maximalSeparatedSet`.
    - Left: `have : Nonempty ...` sits directly before the `ENat` lemma that consumes it.
