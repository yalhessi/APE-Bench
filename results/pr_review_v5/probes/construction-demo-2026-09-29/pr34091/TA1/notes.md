# Review notes: PR #34091, generalize the infinite pigeonhole principle

## What I did

- Read `pr.md`, `model.md` and `diff.patch`.
- Read `target/Mathlib/SetTheory/Cardinal/Pigeonhole.lean` in full as the PR leaves it, plus the changed regions of
  `LinearAlgebra/Dimension/StrongRankCondition.lean` and `LinearAlgebra/Basis/Cardinality.lean`, including their
  `open` and `namespace` lines.
- Searched the tree:
  - for every use of the changed lemmas;
  - for existing uncountable-fiber and countable-fiber lemmas;
  - for the library's naming of `⋃ … = univ` lemmas.
- Ran `naming_norm` on the three new or renamed names. All three came back `subject_unresolved`, so the tool did
  not measure them.
- Ran `precedent_search` and `zulip_search`. Neither returned anything that applies here.
- Ran `lean_verify_edit` on every change I propose. Two calls run in parallel collided in workspace setup, and one
  of them failed with a `FileExistsError`; I reran it on its own. Every other call ran in sequence.

The compile checks were:

- **Combined edit of lines 67-122 of Pigeonhole.lean:** compiled. It contains:
  - the fixed docstrings;
  - `[Infinite β]`, `[Infinite α]` and `[Uncountable β]` as instance arguments;
  - namespace prefixes removed;
  - the `;` replaced by a `trans_eq` term;
  - `exists_infinite_fiber u' h` at the call site.
- **The `▸` form for the cof argument:** failed, because it rewrote the wrong `ℵ₁`. I replaced it with `trans_eq`.
- **`exists_infinite_fiber'` as a one-line term** (`infinite_iff.2 ((aleph0_le_mk α).trans h.le)`): compiled.
- **`linearIndependent_le_infinite_basis` using `exists_infinite_fiber` directly**, without the primed lemma:
  compiled.
- **Unprefixed names in StrongRankCondition.lean:250 and Basis/Cardinality.lean:119:** both compiled.
- **The deprecated alias `le_range_of_union_finset_eq_top` used with a `= ⊤` hypothesis**, both as a term
  application and through `apply`/`exact`: compiled. Downstream uses keep working through the alias.
- **`Set.univ` written as `univ` in the statement of `le_range_of_union_finset_eq_univ`:** failed. Inside
  `namespace Cardinal`, `univ` resolves to `Cardinal.univ`, so the `Set.` prefix is needed. Nothing filed.
- **`Finite.exists_infinite_fiber` for the finite-codomain branch of `exists_infinite_fiber`:** failed with
  "Unknown constant". That file is not imported here, so I did not propose this golf.
- **Countable corollary `exists_uncountable_fiber_of_countable`:** compiled.
- **Rename to `le_range_of_iUnion_finset_eq_univ`, with the alias retargeted:** compiled.
- **`section` plus `variable {β α : Type u} (f : β → α)` around the four lemmas:** compiled.
- **One-line ending for `exists_uncountable_fiber`** (`succ_aleph0 ▸ succ_le_of_lt (hα.trans_lt ha)`): compiled.

## Object by object

- **`Cardinal.infinite_pigeonhole_card_lt` (modified).**
  - Generalizing `ℵ₀ ≤ #α` to `ℵ₀ ≤ #β` is correct, and both the case split and the proof are fine.
  - The docstring is wrong ("than its domain's", and "great") and is filed.
  - Hypothesis names: `hβ : ℵ₀ ≤ #β` is named after β. Fine.
  - The old statement (`ℵ₀ ≤ #α`) is not kept as a corollary. It is strictly weaker and does not simplify the
    statement, so I did not ask for it back. This is consistent with the "reshaping lemma" finding on
    `exists_infinite_fiber'`.
- **`Cardinal.exists_infinite_fiber` (modified).**
  - The generalization to `Infinite β` is right.
  - Filed: the docstring is wrong; the explicit class argument should be instance-implicit; the `Cardinal.` prefix
    is redundant.
  - Its first branch repeats the finite-codomain argument of `infinite_pigeonhole_card_lt`. The library lemma
    `Finite.exists_infinite_fiber` is not imported here, so I filed nothing.
- **`Cardinal.exists_infinite_fiber'` (added).** Its only use is in StrongRankCondition. Filed:
  - remove it, since it only reshapes `exists_infinite_fiber`;
  - if it is kept: drop the prime for a descriptive suffix, give it a standalone docstring, take `[Infinite α]`,
    replace the multi-line `by` argument with a term, and drop the redundant prefix.
- **`Cardinal.exists_uncountable_fiber` (added).**
  - Correct, and it is not a duplicate: no other lemma in the tree concludes `Uncountable (f ⁻¹' {a})`.
  - Filed:
    - the docstring is wrong;
    - `[Uncountable β]` should be an instance argument;
    - the `;` on line 102;
    - the redundant `Cardinal.` and `Order.` prefixes;
    - a small golf of the last two lines;
    - an optional `[Countable α]` corollary.
  - It is not used in the PR. I kept it as intended API, because the module docstring says "This file proves
    variants of the infinite pigeonhole principle".
- **`Cardinal.le_range_of_union_finset_eq_univ` (renamed from `_eq_top`).**
  - The proof simplification (dropping `k`) is correct.
  - The deprecated alias has `since`, is one line, and works for callers that still pass `= ⊤` (checked).
  - Filed: the name says `union` where the library says `iUnion`, and the rename is outside the PR's stated scope.
- **`le_range_of_union_finset_eq_top` (removed and re-added as an alias).** Covered under the alias checks above.
- **Docstring and TODO changes.** Removing `-- TODO: write Set.univ instead of ⊤ ...` is right, because that TODO
  is done. The module TODO "Generalize universes of results." still applies and is kept, which is correct.
- **`infinite_basis_le_maximal_linearIndependent'`** (Basis/Cardinality.lean, call-site rename only). The
  `Cardinal.` prefix is redundant under `open Cardinal` and is filed. `union_support_maximal_linearIndependent_eq_range_basis`
  already states `= Set.univ`, so the hypothesis matches the renamed lemma.
- **`linearIndependent_le_infinite_basis`** (StrongRankCondition.lean, call-site rename only). The `Cardinal.`
  prefix is redundant under `open Cardinal` and is filed. The alternative without `exists_infinite_fiber'` is
  verified.

## Conventions: places filed and places left

1. **Namespace grouping and redundant prefixes.**
   - Filed:
     - `exists_uncountable_fiber`, lines 99 and 104: `Cardinal.aleph0_lt_mk_iff`, `Order.succ_le_iff`,
       `Order.succ_le_succ_iff`;
     - `exists_infinite_fiber`, line 82, and `exists_infinite_fiber'`, line 92: `Cardinal.infinite_iff`;
     - StrongRankCondition.lean:250: `Cardinal.exists_infinite_fiber'`;
     - Basis/Cardinality.lean:119: `Cardinal.le_range_of_union_finset_eq_univ`.
   - Left: line 111, `= Set.univ`. Under `namespace Cardinal`, `univ` resolves to `Cardinal.univ` (checked: type
     mismatch), so the prefix is required.
   - Left: all declarations are already inside `namespace Cardinal` (lines 27 and 127).
2. **Drop unneeded hypotheses.**
   - Left: `infinite_pigeonhole_card_lt` needs `hβ` (counterexample: `#α = 2`, `#β = 3`).
   - Left: `exists_uncountable_fiber` needs `h` when α is uncountable (counterexample: the identity map).
   - Left: `exists_infinite_fiber`. This PR is itself the weakening.
3. **Name built from the statement's declarations.**
   - Filed: `le_range_of_union_finset_eq_univ` should say `iUnion`.
   - Left: `exists_uncountable_fiber` follows the existing sibling `exists_infinite_fiber` (line 80) and
     `Finite.exists_infinite_fiber`.
4. **Common special case as its own lemma.**
   - Filed: the `[Countable α]` corollary of `exists_uncountable_fiber`.
   - Left: the old statement of `infinite_pigeonhole_card_lt`. It does not simplify the statement (see convention 11).
5. **Docstring on its own terms.**
   - Filed: `exists_infinite_fiber'`, line 88.
6. **Shared arguments as `variable`.**
   - Filed: Pigeonhole.lean, for the four lemmas at lines 69, 80, 89 and 97.
7. **Deprecate rather than delete.**
   - Left: `le_range_of_union_finset_eq_top` is deprecated as an alias (lines 124-125).
8. **Deprecation names its replacement.**
   - Left: the alias form at line 124 names `le_range_of_union_finset_eq_univ` as its target.
9. **Deprecated declaration kept as a one-line derivation.**
   - Left: lines 124-125 are an alias with no proof.
10. **One tactic per line.**
    - Filed: line 102 (`rw ...; exact ...`).
    - Left: lines 49 and 65 also use `;`, but the PR does not touch them.
11. **No lemma that merely reshapes existing ones.**
    - Filed: `exists_infinite_fiber'` (remove it).
12. **Deprecated declaration with a differing statement keeps its own statement.**
    - Left: the alias `le_range_of_union_finset_eq_top` differs only in `⊤` vs `Set.univ`. A use with a `= ⊤`
      hypothesis compiled through both term application and `apply`/`exact`, so downstream uses keep working.
13. **Prime only beside an unprimed primary sibling.**
    - Left: `exists_infinite_fiber'` has the unprimed primary sibling `exists_infinite_fiber` (line 80). This
      convention is satisfied. The prime is filed under conventions 14 and 15.
14. **Variant named by the term that differs, not by a prime.**
    - Filed: `exists_infinite_fiber'`.
15. **General version has the plain name; special case has a suffix.**
    - Filed under the same finding as convention 14: `exists_infinite_fiber'` is the special case.
    - Left: `exists_infinite_fiber` is the general version and carries the plain name.
16. **Docstring terminology matches generality.**
    - Left: no docstring overstates or understates generality. The wrong docstrings are filed under convention 18.
17. **Rename with deprecation.**
    - Left: the rename `_top` → `_univ` comes with a deprecation.
    - Left: the further `iUnion` rename is filed under convention 3, with the alias retargeted.
18. **Comments and docstrings in step with the code.**
    - Filed: docstrings of `infinite_pigeonhole_card_lt` (lines 67-68), `exists_infinite_fiber` (78-79) and
      `exists_uncountable_fiber` (95-96).
    - Left: the removed TODO is done.
    - Left: the module TODO still applies and is kept.
19. **Only changes the purpose requires.**
    - Filed: the `⊤`→`univ` rename and its satellite edits.
    - Left: renaming the hypotheses `w`/`w'` → `h`/`hβ` happens together with the statement change, which is in scope.
20. **No multi-line `by` inside a constructor term.**
    - Filed: `exists_infinite_fiber'`, lines 91-93. The `by` block there is an argument to an application.
21. **Unused added lemma.**
    - Left: `exists_infinite_fiber'` is used (StrongRankCondition.lean:250).
    - Left: `exists_uncountable_fiber` is a pigeonhole variant in a file whose docstring (line 14) is "This file
      proves variants of the infinite pigeonhole principle".
22. **Spelling in the library's most common form.**
    - Left: `ℵ₀ ≤ #β` is the cardinal-file form used throughout Pigeonhole.lean.
    - Left: `= Set.univ` replaces `⊤`, as the TODO asked.
23. **Hypothesis named after its variable.**
    - Left: `hβ : ℵ₀ ≤ #β`, `hβ : Infinite β`, `hα : Infinite α`, `hβ : Uncountable β`, and `hα : #α < ℵ₀` in the
      proofs are all named after their variable.
24. **Class hypotheses instance-implicit.**
    - Filed: `exists_infinite_fiber` (`Infinite β`), `exists_infinite_fiber'` (`Infinite α`) and
      `exists_uncountable_fiber` (`Uncountable β`).
25. **Deprecation date in `since`.**
    - Left: line 124 has `(since := "2026-01-17")`.
