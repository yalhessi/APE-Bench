# Review notes: PR #34091 (generalize infinite pigeonhole principle)

Inputs read: brief.md, pr.md, model.md, diff.patch. The full post-PR `Mathlib/SetTheory/Cardinal/Pigeonhole.lean` and the
StrongRankCondition call site came from `file_read`. Tools used: `declaration_search`, `content_search`, `naming_norm`,
`precedent_search`, `zulip_search` (neither returned anything relevant) and `lean_verify_edit` (three edits, listed below).

## Edits compiled
- editA (line mode, lines 78-122 of Pigeonhole.lean, `tmp/editA.lean`). It changes:
  - `exists_infinite_fiber` to take `[Infinite β]`;
  - `exists_infinite_fiber'` to take `[Infinite α]`;
  - `exists_uncountable_fiber` to take `[Uncountable β]`, without the `Cardinal.`/`Order.` qualifiers;
  - the "codomain's" wording in the docstrings;
  - the `le_range_of_union_finset_eq_univ` caller, which drops `(by infer_instance)`.

  Result: **compiled**, with no warnings.
- editB (`exists_infinite_fiber'` as the term `exists_infinite_fiber f h <| infinite_iff.2 <| (infinite_iff.1 hα).trans h.le`):
  **compiled**.
- editC (finite branch of `exists_infinite_fiber` through `Finite.exists_infinite_fiber`): **failed**, with
  `Unknown constant`. The file does not import `Mathlib.Data.Fintype.Pigeonhole`, so the idea was dropped and no finding
  was written for it.

## Object by object
Finding numbers are the order of the entries in `findings.json`.

- `Cardinal.infinite_pigeonhole_card_lt`
  - Generalising the hypothesis from `ℵ₀ ≤ #α` to `ℵ₀ ≤ #β` is sound.
  - `ℵ₀ ≤ #β` cannot be dropped. Finite counterexample: `#α = 2`, `#β = 3` gives no fibre of size > 2.
  - The docstring is wrong: it says "greater than its domain's" and keeps the "great than" typo. This is finding 1.
  - The `simp_rw [← succ_le_iff]` up front could move into the second branch, which would let the first branch close with
    `hα.trans_le ha`. That gain is marginal, so it is not filed.
  - The binder rename `w` → `h` sits inside a statement the PR changes anyway, so it is not filed.
- `Cardinal.exists_infinite_fiber`
  - Changing the hypothesis to `Infinite β` is a true generalisation, and both hypotheses are needed.
  - The docstring is wrong in the same way: finding 2.
  - The class hypothesis is explicit, and its caller passes `(by infer_instance)`: finding 5.
  - The duplicated ℵ₀ branch shared with `infinite_pigeonhole_card_lt` looked like a candidate for reuse. No shorter
    in-file derivation was found, and `Finite.exists_infinite_fiber` is not imported.
- `Cardinal.exists_infinite_fiber'`
  - It is the old statement under a primed name. A primed name for a variant, next to an existing unprimed sibling,
    follows convention, so the name is not filed.
  - The class hypothesis is explicit: finding 6.
  - The three-line tactic block can be a one-line term (verified): finding 7, which also fixes the grammar in the
    docstring.
  - Removing the lemma and inlining it at its single caller was considered and not filed, since it serves migration from
    the old statement.
- `Cardinal.exists_uncountable_fiber`
  - The statement is correct. `declaration_search` and `content_search` found no existing uncountable-fibre lemma, so it
    is not a duplicate.
  - The docstring is wrong: finding 3.
  - The class hypothesis `Uncountable β` is explicit: finding 4, verified within editA.
  - Not filed: the scope objection (the lemma is unused in the PR and fits the PR's topic) and universe generalisation
    (every lemma in the file is single-universe, and the module's TODO tracks that).
- `Cardinal.le_range_of_union_finset_eq_univ`, with the deprecated alias for `..._eq_top`
  - The rename resolves the file's own TODO.
  - Removing `k` is required, because `exists_infinite_fiber` now needs `Infinite β`, which is an instance there.
  - The deprecated alias is present and its date is plausible. Its two-line layout is needed: on one line it would exceed
    100 characters.
  - The new name keeps legacy `union` for `⋃`: an advisory `iUnion` finding (finding 8).
  - Splitting the rename into its own PR is small and entangled with the proof change, so it is not filed.
- `infinite_basis_le_maximal_linearIndependent'` (Basis/Cardinality.lean)
  - Only the call is updated to the new name, which is required to avoid the deprecation warning.
  - The `have w₁ := by apply …; exact …` structure is pre-existing, so no golf was requested.
- `linearIndependent_le_infinite_basis` (StrongRankCondition.lean)
  - It switches to `exists_infinite_fiber'`, which is needed because the unprimed lemma now asks for `Infinite κ`.
  - The `(by infer_instance)` it passes is covered by finding 6.

## Convention items dropped after checking
- `variable` for shared binders: the repetition of `{β α : Type u}` across lemmas predates the PR and is the file's
  existing style.
- Letters `β → α`: the whole file uses this order.
- Filling docstring lines up to 100 characters: this is not a Mathlib requirement.
- Module docstring: it lists no declarations, so nothing is out of step.
- `gcongr` instead of `succ_le_succ_iff`, and `simpa using` instead of backward `simp_rw`: neither is clearly better.
- Universe generalisation: file-wide, and tracked by the TODO.
- Scope split of the uncountable lemma: not filed.
- Restoring the old name at the Basis call site: the deprecated alias would warn.
- Weakening any hypothesis: each was checked and is necessary.
