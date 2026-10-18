# Review notes, PR #34091 (generalize infinite pigeonhole principle)

## What I did

- Read `brief.md`, `pr.md`, `model.md` and `diff.patch`. Read `target/Mathlib/SetTheory/Cardinal/Pigeonhole.lean` in full as the PR leaves it (`file_read`).
- Compiled all three changed files as the PR leaves them (`lean_verify_edit` with no edit). Each one compiles, with no errors and no warnings.
- Ran `content_search` for every use of `infinite_pigeonhole_card_lt`, `exists_infinite_fiber` and `le_range_of_union_finset_eq_top`. Each changed lemma is used only inside this PR's files: Pigeonhole.lean, plus the two linear-algebra call sites.
- Ran `declaration_search` for `exists_uncountable_fiber` (new in this PR; no earlier copy exists), `Finite.exists_infinite_fiber`, `aleph0_le_mk`, `aleph0_lt_mk_iff` and `lt_aleph0_iff_finite`.
- Ran `naming_norm` on the three new or renamed names. All three came back `subject_unresolved`, so naming is unmeasured.
- Ran `precedent_search` and `zulip_search`. Nothing in the results applies to this code.
- Surveyed the library's binders with `content_search`. The library binds `Infinite` and `Uncountable` as instance arguments; explicit `(h : Infinite _)` binders appear only in this PR's lemmas and in `Infinite.false`.
- Verified edits:
  - The combined edit over Pigeonhole.lean lines 67-125 compiles: three docstring fixes, instance binders on the three fiber lemmas, and `(by infer_instance)` dropped at the internal caller.
  - The `[Uncountable β]` version of `exists_uncountable_fiber` compiles on its own in declaration mode.

## Object by object

- **`Cardinal.infinite_pigeonhole_card_lt`** (modified)
  - The statement now needs only `ℵ₀ ≤ #β`, which is weaker than the old `ℵ₀ ≤ #α`. The new case split on `#α < ℵ₀` is sound and compiles.
  - The hypothesis renames `w`/`w'` to `h`/`hβ` are fine.
  - Finding (docstring): "strictly greater than its domain's" should be "codomain's", and the old typo "great than" should be "greater than".
  - I found no worthwhile golf: the two branches need different θ.
- **`Cardinal.exists_infinite_fiber`** (modified)
  - Replacing `Infinite α` with `Infinite β` is a real generalization, since the old hypotheses imply the new one.
  - Finding (docstring): "domain's" should be "codomain's".
  - Finding (binder): `(hβ : Infinite β)` should be `[Infinite β]`.
  - I tried a golf of the finite branch through `Finite.exists_infinite_fiber`. Lean rejected it: that lemma is not imported by this file (Unknown constant), so I did not propose it.
- **`Cardinal.exists_infinite_fiber'`** (added)
  - This keeps the old signature as a convenience for `linearIndependent_le_infinite_basis`. Inlining the general lemma at that caller would make the call longer, so I did not ask to remove it.
  - Finding (binder): `(hα : Infinite α)` should be `[Infinite α]`, with `(by infer_instance)` dropped at the caller.
  - Docstring: "requires codomain" is missing "the". Too minor to file; it is fixed in my verified combined edit.
- **`Cardinal.exists_uncountable_fiber`** (added)
  - The statement is correct and compiles, and no copy exists in the base tree.
  - Finding (docstring): "domain's" should be "codomain's".
  - Finding (binder): `(hβ : Uncountable β)` should be `[Uncountable β]`.
  - Golf: splitting on `le_or_gt #α ℵ₀` (verified inside the combined edit) saves only the `succ_le_succ_iff` rewrite and needs a `succ_aleph0 ▸` instead. That is not enough to request.
  - Style: the redundant qualifiers `Cardinal.`/`Order.` inside `namespace Cardinal` with `open Order` are not worth a request.
- **`Cardinal.le_range_of_union_finset_eq_univ`** (renamed from `..._eq_top`)
  - The rename resolves the file's TODO, and the statement now uses `Set.univ`.
  - The deprecated alias is placed right after the declaration. Its date, 2026-01-17, is consistent with the precedent index's as-of date of 2026-01-18. The line break is needed because one line would be 111 characters.
  - Dropping the `k` lemma is correct, because the generalized `exists_infinite_fiber` only needs `Infinite β`.
  - The only change asked here is the caller simplification that goes with the binder finding.
- **`Cardinal.le_range_of_union_finset_eq_top`** (removed, deprecated alias kept): nothing to ask.
- **`infinite_basis_le_maximal_linearIndependent'`** (Basis/Cardinality.lean): a mechanical rename of the callee. It compiles; nothing to ask.
- **`linearIndependent_le_infinite_basis`** (Dimension/StrongRankCondition.lean): switches to `exists_infinite_fiber'` and compiles. The only ask is the follow-on drop of `(by infer_instance)` from the binder finding on `exists_infinite_fiber'`.
- **Module docstring**: the TODO "Generalize universes of results" remains. The PR does not claim to address it, so I left it out of scope.
- **Scope**: the rename of `le_range_of_union_finset_eq_top` sits in the same file and is tied to the generalization (the proof's `k` disappears), so I did not ask to split it.

## Findings written

Six findings in `findings.json`:
- three blocking docstring corrections, on `infinite_pigeonhole_card_lt`, `exists_infinite_fiber` and `exists_uncountable_fiber`;
- three advisory instance-binder requests, on `exists_infinite_fiber`, `exists_infinite_fiber'` and `exists_uncountable_fiber`.
