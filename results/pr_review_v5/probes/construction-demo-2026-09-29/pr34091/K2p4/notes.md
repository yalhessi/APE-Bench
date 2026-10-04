# Pass 4 (proofs): PR #34091

All compiles use `lean_verify_edit` against the PR's reviewed workspace. Declaration mode was used for single proofs. Whole-file line mode (lines 1-127 of Pigeonhole.lean) was used for edits that touch imports, declaration order or several declarations. Two deliberately broken edits, one per mode, were rejected with the expected errors, so the tool really recompiles. They are not recorded as constructions. `proof_profile` was unavailable ("no declaration table" for the base commit), so no ranked-tactic census stands behind any request. The library evidence here comes from compiles, `declaration_search`/`content_search`, one `precedent_search` and one `zulip_search`.

## Family A: `infinite_pigeonhole_card_lt`, `exists_infinite_fiber`, `exists_infinite_fiber'`, plus the related `exists_uncountable_fiber`

The PR weakens the codomain hypothesis to a domain hypothesis. All three rewritten proofs now split on `#α < ℵ₀` and call `infinite_pigeonhole_card` with a regular θ (ℵ₀, succ #α, ℵ₁). The finite-branch text `infinite_pigeonhole_card f ℵ₀ hβ le_rfl (by rwa [isRegular_aleph0.cof_eq])` appears twice.

**`infinite_pigeonhole_card_lt`.**
- The pre-PR proof does not survive (c2). It needs ℵ₀ ≤ #α both for θ = succ #α and for `isRegular_succ`, so a rewrite is forced.
- The library's fibre-sum bound `mk_le_mk_mul_of_mk_preimage_le` plus `mul_lt_of_lt` proves it in two lines, with no case split and no cofinality (c1).
- This is the main request (advisory). It removes the duplicated finite branch and the `isRegular_*` dependencies. It also extends verbatim to different universes through `lift_mk_le_lift_mk_mul_of_lift_mk_preimage_le` (c26), which bears on the file's TODO.

**`exists_uncountable_fiber`** (added).
- The same bound gives a uniform three-line proof (c4; c3 was a failed first attempt with a superfluous `simp`). It replaces the ℵ₁/`succ_aleph0`/`isRegular_aleph_one`/`Order.succ_le_succ_iff` case split.
- Pass 3's countable twin (`Set.Countable.of_preimage_singleton`) supports a derivation (c6; c5 failed on a nonexistent `countable_or_uncountable`), but it is 7 lines, so it is not the route.
- A c-general extraction `exists_lt_mk_preimage_singleton` (c25) makes both this lemma and `infinite_pigeonhole_card_lt` one-liners. c1/c4 already remove the repetition, so I do not ask for the new lemma.

**`exists_infinite_fiber`.**
- The pre-PR proof fails on the new statement (c10). The finite-codomain branch is intrinsic, because the fibres of a finite-codomain map are not uniformly bounded.
- The library's `Finite.exists_infinite_fiber` is exactly that branch. It is not imported (c7), and it works only with `Mathlib.Data.Fintype.Pigeonhole` added (c8, c9). An import for one line is not worth it, so the PR's in-file branch stands.
- The `.imp` form of the other branch (c12) changes nothing material.
- With c1 in place, this is the only place the new lemmas still use the regularity API.
- No request.

**`exists_infinite_fiber'`** (added).
- The PR derives it from the unprimed lemma. The reverse derivation (c13) and the pre-PR proof ported onto this statement (c11) both compile and are no shorter, so the direction is right.
- The three-line `by rw … at hα ⊢; exact …` argument is one term (c14). The embedding route (c15) is no shorter.
- Minor advisory.

## Family B: `le_range_of_union_finset_eq_univ` (renamed from `_eq_top`)

- The pre-PR proof fails only at the call (c16), because the lemma now wants `Infinite β`. It survives verbatim on the primed lemma (c17).
- So deleting the five-line `have k` is the simplification the generalisation buys, and it is right.
- The rest of the proof keeps older idioms, and the PR writes the new call as `(by infer_instance)`.
  - A minimal pass compiles (c18): `by_contra!`, `have` for the Prop, `inferInstance`.
  - With the hypothesis now `= Set.univ`, `iUnion_eq_univ_iff.mp w` is the cover, and `Set.Infinite.mono` with `Finset.finite_toSet` closes the proof (c19).
  - With `choose`, the proof is 7 lines instead of 11 (c20).
- Advisory, and flagged as 'while you are here', since most of those steps predate the PR.

## Family C: `infinite_basis_le_maximal_linearIndependent'`, `linearIndependent_le_infinite_basis`

- Each changes one name in a pre-existing proof.
- The first's pre-PR proof still compiles through the deprecated alias, with a deprecation warning (c23). A term-mode version compiles (c24), but its structure predates the PR, so there is no request.
- The second's pre-PR proof fails ("failed to synthesize Infinite κ", c21), so the switch to `exists_infinite_fiber'` is necessary. Pass 3's c12 already showed the unprimed lemma also serves.
- The only proof-level point is `(by infer_instance)` → `inferInstance` (c22). It is advisory, and moot if pass 3's instance-implicit binders (c13) are adopted. The census shows only a preference: 34 `(by infer_instance)` against 133 ` inferInstance)`.

## Whole file

- c27 applies c1, c12, c14, c4 and c18 together; c28 applies them with c20 in place of c18. Both compile.
- Pigeonhole.lean goes from 127 to 112 lines, all lines are at most 97 characters, and there are no warnings.
- None of the findings is blocking: every PR proof compiles and none is wrong. The requests are shorter proofs, which also depend less on the cofinality API.
