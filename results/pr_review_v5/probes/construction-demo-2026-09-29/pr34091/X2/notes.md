# Review notes: PR #34091 (generalize infinite pigeonhole principle)

Inputs read: `brief.md`, `pr.md`, `model.md`, `diff.patch`. I read the PR's version of
`Mathlib/SetTheory/Cardinal/Pigeonhole.lean` in full and the two call-site contexts through
`ptool file_read`. Tools used: `file_read`, `content_search`, `declaration_search`,
`naming_norm` (it returned subject_unresolved for all three new or renamed names, so naming is
unmeasured), `precedent_search`, `zulip_search` (nothing relevant), `file_search` and
`lean_verify_edit`. Every edit proposed in `findings.json` was compiled with `lean_verify_edit`,
and each one succeeded, with the exceptions stated in the evidence: the cross-file call sites
could not be compiled jointly.

## Object by object

- **`Cardinal.infinite_pigeonhole_card_lt`** (statement and proof modified). The hypothesis moved
  from `ℵ₀ ≤ #α` to `ℵ₀ ≤ #β`, which is a genuine generalization. The docstring is wrong: it
  compares the domain to "its domain's", and the "great than" typo remains (finding, blocking).
  The proof can be two lines using `mk_le_mk_mul_of_mk_preimage_le` and `mul_lt_of_lt`
  (verified; finding, advisory). I also verified a general `exists_lt_mk_fiber` (any `c < #β`),
  of which this lemma and `exists_uncountable_fiber` are one-line corollaries. I recorded it as an
  alternative in the evidence rather than as a separate ask.
- **`Cardinal.exists_infinite_fiber`** (statement and proof modified). The hypothesis changed
  from `Infinite α` to `Infinite β`, which is a correct generalization. The case split on
  `#α < ℵ₀` is needed, because for finite α the strict-`<` lemma does not give an infinite fiber.
  I tried `Finite.exists_infinite_fiber` for the finite branch, but it is not imported here
  (Unknown constant), so I did not propose it. Findings: the docstring has the domain/codomain
  error (blocking), and the explicit `(hβ : Infinite β)` should be `[Infinite β]`, together with
  the `'` and uncountable variants, because both call sites pass `(by infer_instance)`
  (advisory; verified in Pigeonhole.lean).
- **`Cardinal.exists_infinite_fiber'`** (added). This keeps the old signature for the one caller
  whose `Infinite κ` is not an instance. The API is reasonable and the proof is correct.
  Findings: the docstring is missing an article (advisory), and it is covered by the binder
  finding above.
- **`Cardinal.exists_uncountable_fiber`** (added). The statement is correct. There is no existing
  uncountable-fiber lemma in the base (content_search). Findings: the docstring has the
  domain/codomain error (blocking), and the proof golfs to three lines, which also removes the
  redundant `Cardinal.`/`Order.` prefixes (verified; advisory).
- **`Cardinal.le_range_of_union_finset_eq_univ`** (renamed from `..._eq_top`, with a proof
  change). Dropping the `k : Infinite (range f)` block is correct now that
  `exists_infinite_fiber` takes `Infinite β`. The deprecated alias is well-formed and dated
  2026-01-17, which is consistent with the review snapshot of 2026-01-18. Finding: since the
  rename is happening, use `iUnion` per the `_of_iUnion_eq_univ` convention (advisory; verified).
  I checked that `Set.univ` cannot be shortened to `univ`: inside `namespace Cardinal` it
  elaborates as `Cardinal.univ` (compile error), so nothing was requested there.
- **`Cardinal.le_range_of_union_finset_eq_top`** (removed, replaced by the deprecated alias).
  Fine.
- **The docstring comments and the removed TODO**: they are covered by the docstring findings.
  The removed TODO was resolved by the rename.
- **`Mathlib/SetTheory/Cardinal/Pigeonhole.lean` imports**. With the old proof gone, the file
  compiles without `Mathlib.Data.Set.Finite.Lattice` (verified), and its sole use of that module
  was `union_finset_finite_of_range_finite`. I did not check whether the module is reached
  transitively (advisory finding).
- **`infinite_basis_le_maximal_linearIndependent'`** (Basis/Cardinality.lean; call-site rename
  only). Nothing wrong. It would pick up the `iUnion` rename if that is adopted. The misplaced
  pre-existing comment at lines 124-125 is not touched by this PR, so nothing is requested.
- **`linearIndependent_le_infinite_basis`** (Dimension/StrongRankCondition.lean; switched to
  `exists_infinite_fiber'`). The switch is correct, because `Infinite κ` is not available as an
  instance there. It would drop `(by infer_instance)` under the binder finding.

## Checked, nothing requested

- The correctness of the generalized statements: the whole file compiles as the PR leaves it,
  and every verified edit recompiled the whole file.
- `infinite_pigeonhole`, `infinite_pigeonhole_card` and `infinite_pigeonhole_set` are unchanged.
- The hypothesis renames (`w`/`w'` to `h`/`hβ`) break no in-tree named-argument users
  (content_search).
- The module docstring's "Generalize universes" TODO is outside this PR's scope.
- `precedent_search` gave one relevant hint (an explicit versus instance-implicit class hypothesis)
  and nothing else applicable. `zulip_search` gave nothing relevant.
