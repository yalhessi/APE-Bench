# Reviewer notes: PR #34091 (E1)

## What I did

I read `brief.md`, `pr.md`, `model.md` and `diff.patch`. Using `ptool`, I read the whole
`target/Mathlib/SetTheory/Cardinal/Pigeonhole.lean` as the PR leaves it.

I ran `declaration_search` for:
- `Finite.exists_infinite_fiber`
- `exists_infinite_fiber`
- `exists_uncountable_fiber`
- `Cardinal.infinite_pigeonhole_card_lt`
- `union_finset_finite_of_range_finite`

I ran `content_search` over `target/Mathlib` for:
- callers of `exists_infinite_fiber`, `infinite_pigeonhole_card_lt` and `le_range_of_union_finset_*`;
- existing uncountable-fiber lemmas;
- existing countable-fiber and infinite-fiber lemmas;
- finite-fiber lemmas in `Data/`.

I also ran:
- `naming_norm` on the three new or renamed names. All three came back `subject_unresolved`, so naming is unmeasured.
- `zulip_search` and `precedent_search`. Neither returned anything that bears on this code.
- `lean_verify_edit`: six calls in all, listed under "Compile checks".

## Object by object

- **`Cardinal.infinite_pigeonhole_card_lt`** (modified).
  - The statement generalizes `ℵ₀ ≤ #α` to `ℵ₀ ≤ #β`. This is a genuine weakening, because `#α < #β`.
  - The new finite-codomain branch is correct and compiles.
  - Finding: the docstring compares the domain with "its domain's" instead of the codomain's. It
    also keeps the old typo "strictly great than".
  - Changing the hypothesis names from `w`/`w'` to `h`/`hβ` is fine.
- **`Cardinal.exists_infinite_fiber`** (modified). The hypothesis moves from `Infinite α` to
  `Infinite β`, which is a generalization. The proof is correct.
  - Finding: the docstring has the same "domain's ... domain's" error.
  - Finding: the class hypothesis `Infinite β` is taken explicitly. Both in-PR callers pass
    `(by infer_instance)`, so the binder should be `[Infinite β]`.
  - I tried deriving the finite-codomain case from `Finite.exists_infinite_fiber`. It is not
    imported into this file (`Unknown constant`), so I make no proof-golf ask. The existing
    one-line `infinite_pigeonhole_card f ℵ₀ ...` is fine.
  - The finite-case line is repeated in `infinite_pigeonhole_card_lt`. I found no restructuring
    that removes the repetition without circularity, so there is no finding.
- **`Cardinal.exists_infinite_fiber'`** (added). This is the old statement kept under a primed
  name for the StrongRankCondition caller, which is reasonable.
  - Finding: the binder should be `[Infinite α]`, so the caller can drop `(by infer_instance)`.
  - The docstring's "requires codomain" is missing an article. That is too minor to raise.
  - `naming_norm` did not measure the primed name, and I make no naming ask.
- **`Cardinal.exists_uncountable_fiber`** (added).
  - Finding: the docstring has the same "domain's ... domain's" error.
  - Finding: the binder should be `[Uncountable β]`.
  - Finding (advisory): the `Cardinal.` and `Order.` qualifiers are redundant inside
    `namespace Cardinal` with `open Order`.
  - I also checked an alternative proof whose countable-codomain case uses
    `Countable.of_preimage_singleton` (Data/Set/Countable.lean). It compiles, but it is no shorter
    than the PR's `infinite_pigeonhole_card f ℵ₁` argument, which parallels the infinite case. I
    would not request it.
  - No existing uncountable-fiber lemma exists in the base tree, so this is not duplication.
- **`Cardinal.le_range_of_union_finset_eq_univ`** (renamed from `_eq_top`, which resolves the old
  TODO). `⊤` is replaced by `Set.univ`, the deprecated alias is present with a date, and the
  now-unneeded `k : Infinite (range f)` is removed. The proof compiles.
  - The only change I ask for here is dropping `(by infer_instance)`, which is covered by the
    `exists_infinite_fiber` binder finding.
  - Side observation: removing the import `Mathlib.Data.Set.Finite.Lattice` still compiles. The
    PR removed the file's only use of `Set.union_finset_finite_of_range_finite`. I did not raise
    this, because whether downstream files rely on the import transitively is not checkable here.
- **`Cardinal.le_range_of_union_finset_eq_top`** (removed, replaced by the deprecated alias). OK.
- **`infinite_basis_le_maximal_linearIndependent'`** (Basis/Cardinality.lean). This only follows
  the rename. The file compiles as left. Nothing to ask.
- **`linearIndependent_le_infinite_basis`** (StrongRankCondition.lean). This switches to
  `exists_infinite_fiber'`. The file compiles as left. Its `(by infer_instance)` goes away under
  the `exists_infinite_fiber'` binder finding.

## Convention checks

- **Derive from existing library API.**
  - `exists_infinite_fiber'` is derived from `exists_infinite_fiber`, and the new lemmas are
    derived from `infinite_pigeonhole_card` and `infinite_pigeonhole_card_lt`. Nothing is
    rebuilt from first principles.
  - The one library lemma that would directly give a case, `Finite.exists_infinite_fiber`, is
    not imported here.
  - No finding.
- **Class hypotheses as instance arguments.** This is violated three times: `Infinite β`,
  `Infinite α` and `Uncountable β`. There are three findings.

## Compile checks

- **As-is check** on all three changed files: each compiles.
- **Line-mode replacement** of Pigeonhole.lean lines 67-125. The new text has:
  - the corrected docstrings;
  - the `[Infinite β]`, `[Infinite α]` and `[Uncountable β]` binders, with the adjusted proofs;
  - `exists_infinite_fiber u' h` in `le_range_of_union_finset_eq_univ`.

  Result: `compiled`.
- **`exists_uncountable_fiber` with unqualified names**: `compiled`.
- **`exists_uncountable_fiber` via `Countable.of_preimage_singleton`**: `compiled`. Not filed.
- **`exists_infinite_fiber` via `Finite.exists_infinite_fiber`**: unknown constant, because it is
  not imported.

I could not compile-check the StrongRankCondition caller edit, `Cardinal.exists_infinite_fiber' Φ h`,
because that file builds against the PR's Pigeonhole.lean.
