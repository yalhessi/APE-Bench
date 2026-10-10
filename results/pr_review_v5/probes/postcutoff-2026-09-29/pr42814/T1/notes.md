# Review notes: PR #42814 (fundamental discriminants)

Inputs read: `brief.md`, `pr.md` (no description), `model.md`, `diff.patch`. All tool calls went through `./ptool`.
Baseline: `lean_verify_edit` with no edit on `Mathlib/NumberTheory/FundamentalDiscriminant.lean` compiled, with no errors or warnings.

## Mathlib.lean
- The import of `Mathlib.NumberTheory.FundamentalDiscriminant` is added in alphabetical order. Nothing to ask.

## Mathlib/Data/Nat/Prime/Basic.lean
- `Nat.forall_prime_iff_two_and_odd`:
  - Docstring: fine.
  - Placement: fine, next to `Prime.odd_of_ne_two` and `Prime.even_sub_one`.
  - Duplication: none. A content search for `forall_prime` and for `Prime → Odd p →` found no existing lemma.
  - Proof: re-derives the 2-or-odd split, which `Nat.Prime.eq_two_or_odd'` (line 45) already states. The term-mode golf compiled. **Finding 5 (advisory).**
  - Name: `naming_norm` could not resolve a subject. I found no sibling convention strong enough to ask for a rename.

## Mathlib/Data/Nat/Squarefree.lean
- `Int.squarefree_iff_prime_sq_not_dvd`:
  - Duplication: none. `Int.squarefree_*` at base has only `squarefree_natAbs` and `squarefree_natCast` (Algebra/Squarefree/Basic.lean:325,330).
  - Name: follows the general `squarefree_iff_irreducible_sq_not_dvd_of_*`.
  - Placement: reasonable. It needs `Nat.squarefree_iff_prime_squarefree` from this file, and Algebra/Squarefree/Basic cannot see `Nat.Prime`. Using `^ 2` rather than the Nat sibling's `x * x` is the better form.
  - Proof: a hand-built `bridge` iff plus an anonymous-constructor `exact`. A one-step `simp_rw [← Int.squarefree_natAbs, Nat.squarefree_iff_prime_squarefree, sq, ← Int.natCast_mul, Int.natCast_dvd]` compiled. **Finding 2 (advisory).**
- The `namespace Int` / `end Int` wrapper goes before the commented-out NormNum block. Fine.

## Mathlib/RingTheory/Coprime/Basic.lean
- `IsCoprime.dvd_mul_right_iff` and `IsCoprime.dvd_mul_left_iff`:
  - Statements and proofs: correct. They sit at the right level (CommSemiring section), with the side conventions of `dvd_of_dvd_mul_right/left`.
  - Duplication: none. Neither the base nor the PR declares `IsCoprime.dvd_mul_left/right`, and there is no IsRelPrime iff version.
  - Name: the identically shaped siblings `Nat.Coprime.dvd_mul_right/left`, `IsUnit.dvd_mul_right/left` and `Units.dvd_mul_right/left` carry no `_iff`. The rename compiled. **Finding 4 (advisory).**
- `Odd.isCoprime_two`:
  - Proof: correct.
  - Generality: needs CommRing (in ℕ, 3 and 2 are not `IsCoprime`), so it cannot be generalized to a semiring.
  - Name: the siblings mark the side. `Int.isCoprime_two_right : IsCoprime m 2 ↔ Odd m` and `Nat.coprime_two_right`/`Odd.coprime_two_right` do, but this name does not, and the `_left` version is missing.
  - Removal is not an option: replacing its use with `Int.isCoprime_two_right.2 hp` fails (`Unknown constant`; RingTheory/Int/Basic is not imported), so the general lemma is justified.
  - Renaming to `_right` and adding `_left` compiled. **Finding 3 (advisory).**

## Mathlib/NumberTheory/FundamentalDiscriminant.lean
- Header, `module`, `public import`, `@[expose] public section`: standard for a file with a definition.
- Module doc:
  - It claims fundamental discriminants are "exactly the discriminants of quadratic fields". I verified that `IsFundamentalDiscr 1` holds (`simp [isFundamentalDiscr_iff_squarefree]` compiles), so the sentence is false for D = 1. **Finding 1 (blocking).**
  - The rest of the module doc and the "Main results" list match the declarations.
- `Int.IsFundamentalDiscr`:
  - Correctness: I checked the definition by hand against the standard characterization (D ≡ 1 mod 4 squarefree, or D = 4m with m ≡ 2,3 mod 4 squarefree). It agrees. Checked values: D = 0 is excluded; -3, -4, -8, 5, 8 and 12 are included; 4 is excluded.
  - Docstring: matches the definition.
  - Style: the middle clause mixes `¬ 4 ∣ x` with `x % 4 ≠ 1`. I tried respelling it as `x % 4 = 2 ∨ x % 4 = 3` (definition and `_def` together, lines 39-46). `grind` in `isFundamentalDiscr_iff_squarefree` then hit the heartbeat limit, so the spelling carries the proof. No finding, because I have no working replacement.
- `Int.isFundamentalDiscr_def`: `Iff.rfl` unfolding lemma used by `grind`. Fine.
- `Int.IsFundamentalDiscr.ne_zero` and `Int.IsFundamentalDiscr.emod_four_eq_zero_or_one`: correct, and the names fit (`emod` for Int `%`). Nothing to ask.
- `Int.isFundamentalDiscr_iff_squarefree`:
  - Statement: correct.
  - Proof: two anonymous `have`s picked up by `grind`, with a comment explaining it. I considered asking for them to be named but left it, since it is documented and compiles.
  - Uses the new coprime lemmas, so it needs updating with Findings 3 and 4.
- `Int.isFundamentalDiscr_four_mul_add_one`: stated only for the syntactic form `4 * m + 1`. The hypothesis form (`D % 4 = 1 → (IsFundamentalDiscr D ↔ Squarefree D)`) compiled via `simp [isFundamentalDiscr_iff_squarefree, hD]`, and the original then follows by `omega`. **Finding 6 (advisory).**
- `Int.isFundamentalDiscr_four_mul`: correct, and the right form, since `D / 4` would be awkward. Nothing to ask.

## Tools with no actionable output
- `naming_norm`: `subject_unresolved` for most of the new names, and `population_too_small` for `emod_four_eq_zero_or_one`.
- `precedent_search` on the coprime lemmas: no applicable precedent.
- `zulip_search` for "fundamental discriminant": nothing about this definition.
