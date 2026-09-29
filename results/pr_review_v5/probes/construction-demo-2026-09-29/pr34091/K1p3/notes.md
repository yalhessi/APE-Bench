# Pass 3 notes: PR #34091, statements and the family

All compiles are `lean_verify_edit` runs on the PR's reviewed workspace. Pigeonhole.lean compiles as
the PR leaves it. Examples were inserted at line 106, after `exists_uncountable_fiber`, or at line 126,
after the deprecated alias. Construction ids refer to `constructions.json`.

## Family A: `infinite_pigeonhole_card_lt`, `exists_infinite_fiber`, `exists_infinite_fiber'`, plus the hypothesis member `exists_uncountable_fiber`

The statements confirm the hypothesis family. All four have the shape `f : β → α`, `h : #α < #β`, a
largeness hypothesis on the domain, and a conclusion about some fiber. It is one API.

- **Usage (c1, c2, c6, c7).** With the instance in scope, a client can use each lemma only by passing
  `‹_›`. `exists_infinite_fiber f h` alone leaves an `Infinite β →` argument (c2). Both call sites in
  the tree pass `(by infer_instance)`. The headline use of `exists_uncountable_fiber`, an uncountable
  β mapping to ℕ, fails when β is not in `Type` (c6: universe mismatch). In one universe with a
  countable codomain, the client must build `#α < #β` by hand (c7).
- **Generalised statements (c9–c14).** Each hypothesis is tight. Dropping `hβ` from
  `infinite_pigeonhole_card_lt`, or weakening `Uncountable β` to `Infinite β`, breaks the proof, and
  either change makes the statement false (my own counterexamples: Fin 3 → Fin 2; ℕ → Unit).
  Independent universes do not compile with the PR's proof (c9). A ULift derivation from the PR's
  lemma does compile in 8 lines and serves the ℕ client (c10). The main positive result is c11: one
  lemma for regular θ ≤ #β, `∃ a, θ ≤ #(f ⁻¹' {a})`, proved in 4 lines. Both new fiber lemmas are its
  θ = ℵ₀ and θ = ℵ₁ cases, each derived in 2 lines.
- **Closure (c8, c15–c18).** `exists_infinite_fiber'` restates the old `exists_infinite_fiber` under a
  primed name, as a special case. Its only consumer compiles without it (c17). The same treatment is
  missing for `infinite_pigeonhole_card_lt`, whose third hypothesis also moves from codomain to
  domain under the same name. Old callers break (c16), and the twin is one term (c15). The
  countable-codomain uncountable-fiber lemma already follows in 3 lines from the base lemma
  `Set.Countable.of_preimage_singleton`, across universes (c8). `exists_uncountable_fiber` has no
  consumer in the tree.
- **Automation (c22).** None of the 34 `exists_*fiber` declarations in Mathlib carries an attribute.
  The file's only attribute is the deprecation. The conclusions are existentials, so registering
  nothing is correct, and there is no finding.
- **Binders and form (c3, c4, c5).** Taking `Infinite` or `Uncountable` as an explicit hypothesis is
  unique to these three lemmas in Mathlib, apart from the dot-notation `Infinite.false`. The rest of
  the library, including `Finite.exists_infinite_fiber`, uses `[Infinite _]`. The instance-binder
  version compiles with the proofs unchanged (c3). The conclusion form `Infinite (f ⁻¹' {a})` matches
  the finite twin. The `{β α : Type u}` order and the `h`/`hβ` hypothesis names match the rest of the
  file.

Findings 1–4 come from this family, all advisory.

## Family B: `le_range_of_union_finset_eq_univ` and the deprecated alias `le_range_of_union_finset_eq_top`

The statements confirm the hypothesis: this is a rename plus `⊤ → Set.univ` in the hypothesis, which
carries out the removed TODO.

- **Usage (c19).** The lemma applies directly to a `= Set.univ` cover, and to a pointwise cover
  through `Set.eq_univ_of_forall`. The deprecated alias still accepts an old caller's `= ⊤`
  hypothesis, because the two are defeq. The one consumer's feeding lemma already concludes
  `= Set.univ` (c20).
- **Generalised statement (c14).** `[Infinite β]` is needed, both by the proof and by a
  counterexample (Fin 2, a single cover set).
- **Form (c21).** No other SetTheory hypothesis spells `= Set.univ` or `= univ`, so there is no local
  convention. `open Set` would let it read `univ`; that is left to the layout pass.
- No finding.

## Family C: `infinite_basis_le_maximal_linearIndependent'` and `linearIndependent_le_infinite_basis`

Their statements are unchanged; only the proofs switch to the renamed or primed lemma. Both files
compile as the PR leaves them (c23), so nothing here is for this pass. c17 compiles
`linearIndependent_le_infinite_basis` with the unprimed lemma, which bears on Family A.

## Left to later passes

- The docstrings of `infinite_pigeonhole_card_lt`, `exists_infinite_fiber` and
  `exists_uncountable_fiber` read "strictly greater than its domain's", where the codomain is meant
  (prose pass).
- The name `exists_infinite_fiber'` (naming pass).
- The silent statement change of `infinite_pigeonhole_card_lt` and `exists_infinite_fiber` under
  unchanged names (PR-as-change pass). Here it appears only as the closure asymmetry.
