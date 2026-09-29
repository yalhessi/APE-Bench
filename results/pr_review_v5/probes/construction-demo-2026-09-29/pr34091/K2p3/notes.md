# Pass 3 notes: statements and the family (PR #34091)

The tool workspace is rooted at `target/`, so file tools take `target/Mathlib/...` paths.
`lean_verify_edit` takes `Mathlib/...`. Every example was inserted after
`exists_uncountable_fiber` (Pigeonhole.lean line 106) or after the alias (line 126), unless noted.

## Family 1: the fibre lemmas
Members: `infinite_pigeonhole_card_lt`, `exists_infinite_fiber`, `exists_infinite_fiber'` and
`exists_uncountable_fiber`. The model's hypothesis family (the three `exists_*_fiber`) is
confirmed as one API. All three have the shape `∃ a, P (f ⁻¹' {a})` from `h : #α < #β` and a size
hypothesis on the domain.

- **Usage (c1, c11).** Every client example compiles. A client with `[Infinite β]` or
  `[Uncountable β]` has to hand the class to the lemma as `inferInstance`. A client with a
  countable codomain derives `h` with `mk_le_aleph0.trans_lt aleph0_lt_mk`. The new
  `infinite_pigeonhole_card_lt` reaches the finite-codomain case. A client holding the old
  `ℵ₀ ≤ #α` adapts with one `trans`.
- **Generalised statements (c4-c7).**
  - `hβ` cannot be dropped from `infinite_pigeonhole_card_lt`. The proof needs it only in the
    finite-α branch.
  - `hβ` cannot be dropped from `exists_infinite_fiber`: Bool → PUnit is a compiled
    counterexample.
  - `h` cannot be dropped from either `exists_*_fiber`: `id` is a compiled counterexample.
  - So the PR's hypotheses are the weakest of their form. The PR's change of each size hypothesis
    from the codomain to the domain is a strict generalisation. The old statement follows in one
    step (c2, c11).
  - A universe-heterogeneous `exists_infinite_fiber_lift` follows via ULift (c4). This is the
    file's own "Generalize universes" TODO and is outside this PR. I raise no finding on it.
- **Closure (c2, c3, c10, c12).**
  - The new `exists_infinite_fiber` covers `Finite.exists_infinite_fiber` in one universe, but not
    across universes (c3 fails with a universe mismatch).
  - The countable-codomain twin of `exists_uncountable_fiber` is already in the library, as the
    contrapositive of `Set.Countable.of_preimage_singleton` (c10). The new lemma adds only the
    uncountable-codomain case.
  - `exists_infinite_fiber'` is a special case of `exists_infinite_fiber`. Its only caller
    compiles without it (c12). This is finding 2, advisory.
- **Automation (c16).** No fibre lemma in this file or in `Data/Fintype/Pigeonhole.lean` carries an
  attribute, and none is simp-shaped. The PR's lemmas match their siblings, so there is nothing to
  register.
- **Binders (c13-c15).** The three lemmas take `Infinite` or `Uncountable` as explicit hypotheses.
  - Library count: 155 instance-implicit `[Infinite` against explicit uses only here and in
    `Infinite.false`. For `Uncountable` it is 20 against 1, the 1 being this PR.
  - The twin and the same-file consumer take the class instance-implicit.
  - Both call sites pass `(by infer_instance)`.
  - The instance-implicit version compiles with the proofs unchanged (c13).

  This is finding 1, advisory. It is one decision for all three lemmas.

  `infinite_pigeonhole_card_lt` takes `ℵ₀ ≤ #β`, as its cardinal-form siblings
  (`infinite_pigeonhole`, `infinite_pigeonhole_card`) do. It is consistent and needs no change.

## Family 2: `le_range_of_union_finset_eq_univ` and the deprecated `_eq_top` alias
The model's hypothesis is confirmed: this is a rename with an alias, one API.
- **Usage (c8).** A client holding `= ⊤` applies the new name unchanged. A pointwise-cover client
  needs one `ext`/`simpa`. The old name compiles with a deprecation warning.
- **Generalised (c9).** `[Infinite β]` is needed (a counterexample compiles), and `α β : Type*` is
  already universe-polymorphic. The deleted `have k : Infinite (range f)` step shows the fibre
  lemma's generalisation was useful to this caller.
- **Form (c17).** In covering statements `= univ` outnumbers `= ⊤` by 104 to 11, and the one
  producer lemma concludes `= Set.univ`. The rename matches the area. No finding.
- **Automation.** No attribute is expected (c16).

## Family 3: `infinite_basis_le_maximal_linearIndependent'` and `linearIndependent_le_infinite_basis`
Both statements are unchanged, with one line of proof changed in each (c18), so this pass has
nothing to construct for them. The rank caller's view of `exists_infinite_fiber'` is c12.

Not reviewed here, left to later passes:
- The docstrings say "domain's … than its domain's" where "codomain's" is meant.
- The `'` name.
- The deprecation date.
- The duplicated finite-α case split across the three proofs.
