# Review notes: PR #42814 (fundamental discriminants)

I read `brief.md`, `pr.md`, `model.md` and `diff.patch`, then used `ptool` for these tools:
declaration_search, content_search, file_search, file_read, naming_norm, zulip_search,
precedent_search and lean_verify_edit. The temporary edit files are in `tmp/`. The new file
compiles as the PR leaves it (as-is check: `compiled`).

## Mathlib.lean
- The import line for `Mathlib.NumberTheory.FundamentalDiscriminant` is in alphabetical order
  (FunctionField < FundamentalDiscriminant < GaussSum). Nothing to ask.

## Mathlib/Data/Nat/Prime/Basic.lean: `Nat.forall_prime_iff_two_and_odd`
- Checked whether it already exists: content_search for `forall_prime` lemmas found no equivalent
  at base.
- It is used in the PR, in the first `have` of `isFundamentalDiscr_iff_squarefree`, so it is not
  dead API.
- A term-mode golf via `hp.eq_two_or_odd'.elim (· ▸ h.1) (h.2 p hp)` compiles (lean_verify_edit:
  `compiled`). The existing four-line proof is short and readable, so I did not ask for it.
- The docstring is fine, and the name is reasonable. No finding.

## Mathlib/Data/Nat/Squarefree.lean: `Int.squarefree_iff_prime_sq_not_dvd`
- Does not exist at base (declaration_search). Siblings: `Nat.squarefree_iff_prime_squarefree`,
  `squarefree_iff_irreducible_sq_not_dvd_of_*`. The `_sq_not_dvd` naming matches the generic
  lemmas.
- Placement: it depends on `Nat.squarefree_iff_prime_squarefree` (this file) and
  `Int.squarefree_natAbs` (Algebra/Squarefree/Basic, imported here). There is no
  `Data/Int/Squarefree` file. An Int section at the end of the Nat file is acceptable; no scope
  ask.
- Finding: the proof golfs to a single `simp_rw [...]` (verified `compiled`). That removes the
  `bridge` helper, the `=>` lambdas and the redundant `Int.` prefixes inside `namespace Int`.

## Mathlib/RingTheory/Coprime/Basic.lean
- `IsCoprime.dvd_mul_right_iff` / `IsCoprime.dvd_mul_left_iff`: new at base. The Nat analogues are
  `Nat.Coprime.dvd_mul_right/left`, which are iff lemmas without `_iff`. A bare `dvd_mul_left`
  would read as the LHS proposition, so the `_iff` suffix is defensible, and the two conventions
  conflict here. No finding. `dvd_mul_right_iff` is unused in the PR, but it is the natural
  counterpart of the used one. The proofs are one-liners with `↦`.
- `Odd.isCoprime_two`: `Int.isCoprime_two_right` exists, but the new file does not import it
  (lean_verify_edit: `Unknown constant`), so a general CommRing lemma is justified. Finding (naming):
  align it with `Odd.coprime_two_right` / `Int.isCoprime_two_right` and add the `_left`
  counterpart. Verified `compiled`.

## Mathlib/NumberTheory/FundamentalDiscriminant.lean
- Module doc. Finding: "exactly the discriminants of quadratic fields" is false for `D = 1`, which
  I verified satisfies `IsFundamentalDiscr`. The doc has no references.
- `@[expose] public section`. Finding: `public section` alone compiles (verified), and
  `isFundamentalDiscr_def` provides the unfolding API.
- `IsFundamentalDiscr` (def). I hand-checked the definition on D = 0, 1, -3, -4, -8, 8, 12, 16,
  20, 45, 72, 32, and it gives the right answers. Findings:
  1. the definition is a hybrid form. I propose the squarefree characterisation as the
     definition: the whole file recompiles with it (verified `compiled`, with the old form kept as
     `isFundamentalDiscr_iff_primitive`);
  2. the docstring should point to background reading.
- `isFundamentalDiscr_def`: `Iff.rfl` is fine. It is an undocumented `theorem`, which falls under
  the file-level theorem→lemma finding.
- `IsFundamentalDiscr.ne_zero` (grind) and `IsFundamentalDiscr.emod_four_eq_zero_or_one` (`h.1`):
  the proofs are fine. They are undocumented `theorem`s (the file-level finding).
- `isFundamentalDiscr_iff_squarefree`. Findings:
  1. extract the two anonymous `have`s, which grind uses only implicitly, as private lemmas
     (verified);
  2. `simp +contextual only [one lemma]` feeding grind → plain `simp` (verified). Deleting the
     line gave `environment_failure`, so some simplification step is needed.

  Grind alone, without the case split, fails (compile_errors). The current structure is otherwise
  reasonable.
- `isFundamentalDiscr_four_mul_add_one`. Findings: generalise to a hypothesis `D % 4 = 1`
  (verified), and add the missing docstring, since the module doc lists it as a main result.
- `isFundamentalDiscr_four_mul`: missing docstring, also a listed main result (finding). The
  `simp` proof is fine.
- The name `IsFundamentalDiscr` / `Discr`: Mathlib abbreviates discriminant as `discr`
  (`Algebra.discr`, `Polynomial.discr`, `NumberField.discr`), so the abbreviation is consistent.
  No finding.
- I considered but did not request: `@[simp]` / `@[grind =]` on the characterisation lemmas, since
  `isFundamentalDiscr_def` passed to grind makes the tagging question speculative, and splitting
  the PR, since the supporting lemmas are small and only make sense with their use.

## Tools that gave nothing usable
- naming_norm returned `subject_unresolved` for every new declaration, so naming is unmeasured by
  census.
- precedent_search for the def returned unrelated comments.
- zulip_search for "fundamental discriminant" found only unrelated discriminant threads.

Findings written: 12 (1 blocking, 11 advisory).
