# Notes: PR #34091 (generalize infinite pigeonhole principle), reviewer A1

Inputs read: `brief.md`, `pr.md`, `model.md` and `diff.patch`. I also read the full
`Pigeonhole.lean` as the PR leaves it (`file_read`). Every tool call went through `ptool`.
The temporary argument files are in `tmp/`.

## Tools used
- declaration_search for `exists_infinite_fiber`, `exists_uncountable_fiber`,
  `Finite.exists_infinite_fiber`, `infinite_pigeonhole_card_lt` and
  `le_range_of_union_finset_eq_top`. `exists_uncountable_fiber` is new. `Finite.exists_infinite_fiber`
  is in `Data/Fintype/Pigeonhole.lean` and takes `[Infinite α] [Finite β]`.
- content_search for every use of the changed lemmas:
  - `exists_infinite_fiber'` is used once (StrongRankCondition:250, `(by infer_instance)`).
  - `exists_infinite_fiber` is used once in the file (`(by infer_instance)`).
  - `infinite_pigeonhole_card_lt` is used only inside the file.
  - `union_finset_finite_of_range_finite` has no remaining use after the PR, but it is existing
    public API, so I did not flag it.
- naming_norm on the three new or renamed names returned `subject_unresolved` each time, so naming
  is unmeasured.
- precedent_search and zulip_search returned nothing that bears on this code.
- lean_verify_edit, all with outcome `compiled` except the test noted below:
  1. the whole block, lines 67-122: corrected docstrings, instance-implicit `[Infinite β]`,
     `[Infinite α]` and `[Uncountable β]`, the `ℵ₁` split, the term proof of
     `exists_infinite_fiber'`, and the caller without `by infer_instance`;
  2. the `exists_uncountable_fiber` golf alone;
  3. `exists_uncountable_fiber` with only the prefixes removed;
  4. the one-line `exists_infinite_fiber'`;
  5. the general `exists_le_mk_fiber_of_isRegular` with both fiber lemmas as corollaries
     (lines 78-105);
  6. the rename to `mk_le_mk_range_of_iUnion_finset_eq_univ` with the alias retargeted.
  - An attempt to reuse `Finite.exists_infinite_fiber` in the finite branch of
    `exists_infinite_fiber` failed with `Unknown constant`: the file does not import
    `Data/Fintype/Pigeonhole`. I dropped that idea, since adding an import for it is not justified.

## Object by object
- **`infinite_pigeonhole_card_lt`** (modified): moving the hypothesis from `ℵ₀ ≤ #α` to `ℵ₀ ≤ #β` is
  a real generalisation. Without it the result fails for finite β (|α| = 2, |β| = 3), so it cannot
  be dropped. The proof's case split is sound. The new docstring says "greater than its domain's"
  where it should say codomain's, and it still has "great than" (blocking documentation finding).
  There are no other callers in Mathlib to update.
- **`exists_infinite_fiber`** (modified): `Infinite α` became `Infinite β`, which is strictly more
  general and minimal (if β is finite, every fiber is finite). It has the same docstring error
  (finding). The explicit `(hβ : Infinite β)` should be `[Infinite β]` (finding). Its proof's first
  branch is the same as the first branch of `infinite_pigeonhole_card_lt`; the regular-cardinal
  generalisation (finding, filed on `exists_uncountable_fiber`) would remove that duplication.
- **`exists_infinite_fiber'`** (added): it keeps the old statement under a primed name. Findings:
  - the docstring is defined by contrast with another lemma and is ungrammatical;
  - the prime should be replaced by a descriptive name;
  - the multi-line `by` block nested in an application can be a one-line term;
  - the hypothesis should be instance-implicit.

  I also considered asking for the lemma to be removed and its single call site inlined. I chose
  the rename instead, because the call site would become noticeably clunkier (it needs `Infinite κ`,
  derived from `#(Finset ι) < #κ`).
- **`exists_uncountable_fiber`** (added): the statement is correct and minimal; `#α < #β` is needed
  (take f = id). Findings:
  - the docstring has the same error, plus "domain's cardinality is uncountable";
  - `[Uncountable β]` should be an instance argument;
  - the split on `ℵ₁` instead of `ℵ₀` removes the `succ_le_succ_iff` rewriting and the
    `rw ...; exact` one-liner;
  - the redundant `Cardinal.` and `Order.` prefixes should go;
  - a regular-cardinal generalisation would cover it and `exists_infinite_fiber` together.

  It is unused in the PR, but it is clearly part of the PR's intended API (the title says
  "generalize"), so I did not flag it.
- **`le_range_of_union_finset_eq_univ`** (renamed from `..._eq_top`):
  - The rename carries out the old TODO, which is removed correctly because it is done.
  - The deprecated alias has a `since` date, as it should.
  - The `k : Infinite (range f)` block is gone because the new `exists_infinite_fiber` only needs
    `Infinite β`, which is an instance. That is a good simplification.
  - `Set.univ` is qualified on purpose: inside `namespace Cardinal`, plain `univ` would hit
    `Cardinal.univ` and `Ordinal.univ`. So it is not a redundant prefix.
  - The `[Infinite β]` hypothesis is needed.
  - Advisory finding: since the lemma is being renamed anyway, use the full spelling
    `mk_le_mk_range_of_iUnion_finset_eq_univ`.
- **Deprecated alias `le_range_of_union_finset_eq_top`**: fine. It has a dated `since` and the
  replacement is a drop-in.
- **`infinite_basis_le_maximal_linearIndependent'`** (Basis/Cardinality.lean): the change is only
  the call-site rename, and it is correct. Nothing to request beyond what follows from the rename
  finding.
- **`linearIndependent_le_infinite_basis`** (StrongRankCondition.lean): the call-site switch to
  `exists_infinite_fiber'` is correct. Using the general lemma here would need an `Infinite κ`
  proof, so the primed lemma does carry its weight. The `(by infer_instance)` goes away under the
  instance-implicit finding.
- **Module docstring**: the TODO "Generalize universes of results." still applies and is correctly
  kept. Universe generalisation is out of scope for this PR.

## Conventions checked and judged not to apply, or not worth a request
- `namespace` grouping: everything is already under `namespace Cardinal`.
- `variable` for shared binders: the four consecutive lemmas repeat
  `{β α : Type u} (f : β → α) (h : #α < #β)`. The file's existing style puts binders on each
  declaration, and changing that would rewrite untouched declarations, so I made no request.
- Deprecation conventions: satisfied. `exists_infinite_fiber` changed its statement without a
  deprecation, but that is a strict generalisation in place, and the old form is kept as the
  primed lemma.
- Hypothesis naming (`h`, `hβ`, `hα`) follows the variables. No incidental rewrites outside the
  PR's purpose. No `;` chains, apart from the one covered by the `exists_uncountable_fiber` golf
  finding.
