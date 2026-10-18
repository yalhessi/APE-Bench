# Review notes: PR #42814, fundamental discriminants

I read `pr.md`, `model.md` and `diff.patch`. With `ptool` I read the changed files in the workspace
(`target/Mathlib/...`), searched for existing declarations, and checked every edit I propose with
`lean_verify_edit`. As the PR leaves it, `FundamentalDiscriminant.lean` compiles with no errors and no warnings.

## Object by object

- **`Mathlib.lean`**: one import line, in sorted position. Nothing to ask.
- **`Nat.forall_prime_iff_two_and_odd`** (Data/Nat/Prime/Basic.lean)
  - It has a docstring, sits next to `Prime.odd_of_ne_two`, and is used once.
  - Filed:
    - destructure `h` instead of using `h.1` and `h.2`;
    - case-split with `hp.eq_two_or_odd'` instead of `eq_or_ne p 2` followed by `odd_of_ne_two`. Both compiled.
    - strict-implicit `p` (advisory).
  - Duplicate search: content_search for `forall_prime` and `eq_two_or_odd` found no existing equivalent.
- **`Int.squarefree_iff_prime_sq_not_dvd`** (Data/Nat/Squarefree.lean)
  - Correct, documented. Its name matches the sibling `squarefree_iff_irreducible_sq_not_dvd_of_exists_irreducible`.
  - Filed:
    - the golf to a `simp_rw` one-liner (compiled);
    - `=>` changed to `↦` (compiled);
    - strict-implicit `p`. This compiled, and a downstream check showed the `rw` in the fundamental-discriminant file still works.
  - Placement: the file's module doc says "natural numbers". But the lemma needs `Nat.squarefree_iff_prime_squarefree` (same file, line 47) and `Int.squarefree_natAbs` (Algebra/Squarefree/Basic.lean:325, imported). So this file is the lowest place both are available, and I did not ask for a move.
- **`IsCoprime.dvd_mul_right_iff` / `IsCoprime.dvd_mul_left_iff`** (RingTheory/Coprime/Basic.lean)
  - Correct. They are new: `declaration_search` found nothing, and there is no `IsRelPrime` iff version.
  - The right-hand lemma is unused in the PR, but it is the natural companion, so it counts as API.
  - Filed:
    - `theorem` → `lemma` (compiled);
    - align the names with `Nat.Coprime.dvd_mul_left/right`, which have the same shape and no `_iff` (advisory; the conflict with the `_iff` convention is noted below).
- **`Odd.isCoprime_two`** (RingTheory/Coprime/Basic.lean)
  - Correct. It generalises the forward direction of `Int.isCoprime_two_right` (RingTheory/Int/Basic.lean:123) to any `CommRing`.
  - The new file does not import RingTheory/Int/Basic, so I did not ask to use the Int lemma instead.
  - Filed:
    - rename to `Odd.isCoprime_two_right` and add a `_left` companion. The siblings are `Odd.coprime_two_right/left` and `Int.isCoprime_two_right/left`. The rename compiled.
    - `theorem` → `lemma`.
- **`Int.IsFundamentalDiscr`**
  - The definition is mathematically correct. I checked by hand that the three clauses are equivalent to the squarefree characterisation, which the PR proves.
  - D = 1 satisfies it (checked with Lean). So the module doc's "exactly the discriminants of quadratic fields" is wrong; filed.
  - Also filed:
    - a background reference;
    - making the squarefree form the definition (advisory, a design question);
    - strict-implicit binders (compiled).
  - The name `Discr` matches the library's abbreviation (`NumberField.discr`). content_search found no existing fundamental-discriminant notion.
- **`Int.isFundamentalDiscr_def`**: `Iff.rfl`, fine as API. Filed `lemma` (shared with `ne_zero` and `emod_four_eq_zero_or_one`).
- **`Int.IsFundamentalDiscr.ne_zero`**: correct. Filed: replace `grind` with a two-line explicit proof (compiled).
- **`Int.IsFundamentalDiscr.emod_four_eq_zero_or_one`**: projection `h.1`. Its name matches `Int.emod_two_eq_zero_or_one` (Data/Int/Init.lean:279). Only the `lemma` keyword was filed.
- **`Int.isFundamentalDiscr_iff_squarefree`**
  - Correct, documented. Filed:
    - `simp +contextual only [one lemma]` → `rw` (compiled);
    - dot notation `hp.isCoprime_two.pow` (compiled);
    - extract the two anonymous `have`s as lemmas and pass them to `grind` explicitly (compiled).
  - Dropping the case split and running plain `grind` gave `environment_failure`, so I did not propose it.
  - Dot notation for `Int.mul_ediv_cancel_left d four_ne_zero` fails to elaborate: `d.mul_ediv_cancel_left four_ne_zero` binds `d` to the wrong argument. So that line stays.
- **`Int.isFundamentalDiscr_four_mul_add_one` / `Int.isFundamentalDiscr_four_mul`**
  - Correct; both proved by `simp [isFundamentalDiscr_iff_squarefree]`.
  - Filed:
    - the `_iff` suffix;
    - docstrings, since both are listed as main results;
    - `@[grind =]` (compiled, and `grind` uses them).
- **The file as a whole**: filed `@[expose]` (drop it, since `_def` is provided) and `variable {D m : ℤ}`. Both compiled as part of one rewrite of lines 33-81.
- **PR scope**: filed splitting the general prerequisite lemmas in three foundational files into their own PR (advisory).

## Conventions: what I filed and what I left

1. **Terminal `simp` / `simp only` feeding a flexible tactic.**
   - Filed: `isFundamentalDiscr_iff_squarefree`, `simp +contextual only [...]` before `grind` → `rw`.
   - Left:
     - the `have` in the same proof ends `rw [...]; simp`, which is already an unsqueezed terminal `simp`;
     - the four_mul lemmas use `simp [isFundamentalDiscr_iff_squarefree]`, also unsqueezed.
2. **Automation only when the explicit proof is not short.**
   - Filed: `IsFundamentalDiscr.ne_zero` (`grind` → `rintro rfl; exact (h.2.1 0 rfl).1 (dvd_zero 4)`).
   - Left: the `grind` calls in `isFundamentalDiscr_iff_squarefree`. An explicit case analysis over the residues mod 4 would be long, not short and readable.
3. **PR cut at its seams.** Filed: split the prerequisite lemmas (Coprime/Basic, Nat/Prime/Basic, Nat/Squarefree) into their own PR.
4. **`fun` with `↦`.**
   - Filed: `Int.squarefree_iff_prime_sq_not_dvd` (three `=>`).
   - Left (code already uses `↦`):
     - `forall_prime_iff_two_and_odd`: `fun h ↦ ⟨h 2 prime_two, fun p hp _ ↦ h p hp⟩`;
     - the `IsCoprime` pair: `fun h ↦ h.mul_right z`.
5. **Shared arguments as `variable`.**
   - Filed: FundamentalDiscriminant.lean (`{D : ℤ}` ×4, `{m : ℤ}` ×2).
   - Left:
     - RingTheory/Coprime/Basic.lean already declares `variable {x y z w}` (line 48), and the new lemmas use it;
     - `forall_prime_iff_two_and_odd` has a single `{P}` binder shared with nothing.
6. **Dot notation.**
   - Filed: `(IsCoprime.pow hp.isCoprime_two)` → `hp.isCoprime_two.pow`.
   - Left: `Int.mul_ediv_cancel_left d four_ne_zero`. The check ran `rw [d.mul_ediv_cancel_left four_ne_zero]`, which fails ("argument four_ne_zero has type 4 ≠ 0 but is expected to have type ℤ"), so dot notation does not apply to `d` there.
7. **Head-first naming.** Left. Each name already reads in the order of its statement and matches its siblings:
   - `emod_four_eq_zero_or_one` matches `Int.emod_two_eq_zero_or_one`;
   - `squarefree_iff_prime_sq_not_dvd` matches `squarefree_iff_irreducible_sq_not_dvd_of_exists_irreducible`;
   - `forall_prime_iff_two_and_odd` spells the left side and then the right side in order.
8. **Off-topic material placement.** Left:
   - each prerequisite sits next to its closest relatives (`forall_prime_iff_two_and_odd` after `Prime.odd_of_ne_two`; `Odd.isCoprime_two` after `add_one_sub_one_of_two_dvd`; the `IsCoprime` iffs after `dvd_of_dvd_mul_left/right`);
   - the Int squarefree lemma needs `Nat.squarefree_iff_prime_squarefree`, which is in the same file;
   - the new file imports only `Mathlib.Data.Nat.Squarefree`, deliberately avoiding the quadratic-field theory (module doc lines 16-17).
9. **No new declaration when one exists.** Left:
   - content_search found no existing fundamental-discriminant notion;
   - `IsCoprime.dvd_mul_{left,right}_iff` and `Odd.isCoprime_*` are not in the base.
   - `Int.isCoprime_two_right` exists, but it is Int-only, in RingTheory/Int/Basic, and not imported. The PR's lemma generalises it, so instead I filed the sibling rename (item 14).
10. **Extract general facts from proofs.**
    - Filed: the two `have`s in `isFundamentalDiscr_iff_squarefree`.
    - Left: `bridge` in `squarefree_iff_prime_sq_not_dvd`. It is about that proof's specific `n`, and the filed `simp_rw` golf removes it.
11. **Destructure hypotheses used only by projection.**
    - Filed: `forall_prime_iff_two_and_odd` (`h.1`, `h.2`).
    - Left: `ne_zero`'s new proof uses `h.2.1` once; `emod_four_eq_zero_or_one := h.1` is a projection lemma.
12. **Strict-implicit binders.** Filed: `IsFundamentalDiscr` (and `_def`), `Int.squarefree_iff_prime_sq_not_dvd`, `Nat.forall_prime_iff_two_and_odd`.
13. **Case split that substitutes directly.**
    - Filed: `forall_prime_iff_two_and_odd` → `hp.eq_two_or_odd'`.
    - Left: `isFundamentalDiscr_iff_squarefree` already does `obtain ⟨d, rfl⟩ := h`.
14. **Library abbreviation in names.** Left: `Discr` matches `NumberField.discr` (Discriminant/Defs.lean:36).
15. **Sibling naming pattern.** Filed:
    - `Odd.isCoprime_two` → `Odd.isCoprime_two_right`;
    - `IsCoprime.dvd_mul_{left,right}_iff` vs `Nat.Coprime.dvd_mul_{left,right}`. This conflicts with item 17, which favours the current `_iff`; it is filed advisory so the maintainer can pick.
16. **Parallel one-liners kept adjacent.** Left. The candidates are not one-liners:
    - the `IsCoprime` pair is two lines each, e.g. `theorem IsCoprime.dvd_mul_right_iff (H : IsCoprime x z) : x ∣ y * z ↔ x ∣ y :=` / `  ⟨H.dvd_of_dvd_mul_right, fun h ↦ h.mul_right z⟩`;
    - the four_mul pair is three lines each.
17. **`_iff` suffix.**
    - Filed: `isFundamentalDiscr_four_mul` and `isFundamentalDiscr_four_mul_add_one`.
    - Left (already carry `_iff`): `isFundamentalDiscr_iff_squarefree`, `squarefree_iff_prime_sq_not_dvd`, `IsCoprime.dvd_mul_*_iff`.
18. **`@[grind =]` on characterisations.**
    - Filed: the four_mul pair (verified that `grind` uses them).
    - Left:
      - `isFundamentalDiscr_iff_squarefree`: tagging it would rewrite every `IsFundamentalDiscr D` into a disjunction with `/` and `%`, and would compete with the specific rules;
      - `squarefree_iff_prime_sq_not_dvd`: it would unfold every `Squarefree` on ℤ into a ∀;
      - `forall_prime_iff_two_and_odd`: its left side is a higher-order schema in `P`, not a usable pattern;
      - the `IsCoprime` iffs: their `Nat.Coprime` analogues (GCD/Basic.lean:101,104) carry no attribute, and the rewrite is conditional on coprimality.
19. **`theorem` only with a docstring.**
    - Filed: `isFundamentalDiscr_def` / `ne_zero` / `emod_four_eq_zero_or_one` → `lemma`; the four_mul pair → add docstrings; `Odd.isCoprime_two` → `lemma`; the `IsCoprime` pair → `lemma`.
    - Left (have docstrings): `forall_prime_iff_two_and_odd`, `squarefree_iff_prime_sq_not_dvd`, `isFundamentalDiscr_iff_squarefree`.
20. **Easiest formulation as the definition.** Filed: `IsFundamentalDiscr` → the squarefree characterisation.
21. **Every added lemma is used or is API.** Left. `dvd_mul_right_iff`, `ne_zero`, `emod_four_eq_zero_or_one` and the four_mul pair are unused in the PR but are evident API: the iff companion, basic projections, and lemmas listed as main results.
22. **Background reference in the docstring.** Filed: `IsFundamentalDiscr` / module doc.
23. **`@[expose]` on individual definitions.** Filed: FundamentalDiscriminant.lean's `@[expose] public section`. Left: the pre-existing `@[expose]` in Coprime/Basic.lean and Nat/Squarefree.lean, which this PR does not touch.

Also filed: the module-doc correctness issue (D = 1 is included, but it is not a quadratic-field discriminant).
