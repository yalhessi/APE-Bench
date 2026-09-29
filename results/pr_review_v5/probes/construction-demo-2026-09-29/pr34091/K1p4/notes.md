# Pass 4 (proofs): PR #34091, infinite pigeonhole generalisation

Every construction below was compiled with `lean_verify_edit` against the PR's workspace. Ids refer
to `constructions.json`, and "pass-3 cN" refers to `constructions_pass3.json`.

## Family 1: `infinite_pigeonhole_card_lt`, `exists_infinite_fiber`, `exists_infinite_fiber'`, `exists_uncountable_fiber`

**`infinite_pigeonhole_card_lt`** (modified)
- Pre-PR proof against the new statement (c2) fails. `ℵ₀ ≤ #β` cannot feed `isRegular_succ`, which is
  about `succ #α`, so the PR's split on `#α < ℵ₀` is required.
- Idiom rewrite (c16): the only change available is `(by rwa [isRegular_aleph0.cof_eq])` →
  `hα.trans_le isRegular_aleph0.2`. That is cosmetic, so nothing is asked for.
- Derivation (c18): with the pre-PR statement and proof restored, all of the PR's proofs still compile by
  passing their branch's `hα : ℵ₀ ≤ #α`. No proof in the tree exercises the new `#α < ℵ₀` branch.
  Whether to generalise the statement is pass 3's question (pass-3 c15, c16), so this is recorded, not
  requested.

**`exists_infinite_fiber`** (modified)
- Pre-PR proof (c3) fails (`#α ≤ #fiber` given where `#β ≤ #fiber` is expected), so the new finite-codomain
  branch is needed.
- Library tool (c8): the finite case is exactly `Finite.exists_infinite_fiber`, but that lemma is not
  imported here (`Unknown constant`).
- Derivation (c9): with `Mathlib.Data.Fintype.Pigeonhole` imported, `exists_infinite_fiber'` keeps its pre-PR
  proof and `exists_infinite_fiber` becomes `finite_or_infinite` → finite twin / primed lemma. It compiles,
  but it costs an import for about one line, so the PR's in-file route through ℵ₀'s cofinality stands.
- Repetition (c12, c13): the first branch here is a verbatim copy of `infinite_pigeonhole_card_lt`'s first
  branch, and exists_uncountable_fiber repeats the same shape at ℵ₁. Extracting
  `exists_le_mk_fiber_of_isRegular` (pass-3 c11's statement) and replacing lines 78-105 compiles as a
  whole file (c12), with each fiber lemma reduced to 2 lines. Finding 1, advisory.

**`exists_infinite_fiber'`** (added)
- Idiom rewrite (c1): the tactic block building `Infinite β` is the term
  `infinite_iff.2 ((infinite_iff.1 hα).trans h.le)`. Finding 3, advisory.
- Derivation: the PR already derives it from the unprimed lemma, which is the right direction given the
  file's imports (see c9).

**`exists_uncountable_fiber`** (added)
- Idiom rewrite (c10): `rw [...] at hα` plus `exact` → `⟨a, succ_aleph0 ▸ succ_le_of_lt (hα.trans_lt ha)⟩`,
  and the redundant `Cardinal.`/`Order.` qualifiers dropped. 7 → 6 lines. Finding 2, advisory (moot under
  finding 1).
- Library tool (c11): the countable case via `Set.Countable.of_preimage_singleton` (pass-3 c8's argument)
  compiles but is no shorter, so it is not requested.

## Family 2: `le_range_of_union_finset_eq_univ` (renamed from `_eq_top`)

- Pre-PR proof (c4) fails: its `have k : Infinite (range f)` no longer matches the new hypothesis. With
  `exists_infinite_fiber'` it compiles unchanged (c5), but the PR's route, which drops `have k` and passes
  the `[Infinite β]` instance, is 5 lines shorter. The PR made the right call here.
- Idiom rewrite (c14): `by_contra!`, `choose … using iUnion_eq_univ_iff.1 w`, `Set.Finite.subset` and `‹_›`
  give 7 lines instead of 11, with no Prop-valued `let`, no `.choose_spec` and no `@Infinite.of_injective _ _`.
  Finding 4, advisory and explicitly optional, since those lines predate the PR.

## Family 3: `infinite_basis_le_maximal_linearIndependent'`, `linearIndependent_le_infinite_basis`

- `infinite_basis_le_maximal_linearIndependent'`: the pre-PR proof (c7) compiles only with the
  deprecation warning, so the PR's rename of the call is exactly the needed change. A single-term rewrite
  (c15) also compiles, but the structure predates the PR, so nothing is asked for.
- `linearIndependent_le_infinite_basis`: the pre-PR proof (c6) fails, because `Infinite κ` cannot be
  synthesised for the new unprimed lemma, so the switch to `exists_infinite_fiber'` is the minimal fix.
  `inferInstance` for `(by infer_instance)` (c17) compiles. That argument was already there, so nothing is
  asked for. Pass-3 c17 shows the unprimed alternative.

## Summary

The proofs are correct and the PR's changes to downstream proofs are minimal and right: c4-c7 show each
pre-PR proof needed exactly the change the PR made. The four requests are all advisory:
1. extract the regular-θ fiber lemma that the three case splits share;
2. tighten exists_uncountable_fiber's last step and its qualifiers;
3. make exists_infinite_fiber' a one-line term;
4. (optional) put le_range_of_union_finset_eq_univ's proof in the library's idiom.
