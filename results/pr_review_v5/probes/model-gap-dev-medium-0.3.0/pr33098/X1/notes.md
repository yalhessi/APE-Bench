# Review notes: PR #33098 (minimal covers and maximal separated sets)

## Process

I read `brief.md`, `pr.md`, `model.md` and `diff.patch`, then ran `ptool describe`. The file tools
only found files after the first `lean_verify_edit` call had materialised the workspace; files sit
under `target/`. I read the reviewed file in full (`target/Mathlib/Topology/MetricSpace/CoveringNumbers.lean`).
I also read `Cover.lean` for the `IsCover` API and `MetricSeparated.lean` for the `IsSeparated` API,
plus the `ENat` attainment lemmas in `Data/ENat/Lattice.lean` and the `encard` subset-equality
lemmas in `Data/Set/Card.lean`.

As the PR leaves it, the file compiles with no errors and no warnings (as-is check). I compiled
every change I propose with `lean_verify_edit`, recompiling the whole file each time, and all of
them succeeded. I ran `naming_norm` on five new names. `precedent_search` on the cover proof and
`zulip_search` on covering and packing numbers returned nothing relevant.

## Object by object

- **module doc**: the new "definitions" and "main statements" bullets match the declarations.
  The typo "extenal" was already there before the PR, so I did not raise it. If the
  `coveringNumber_subset_le` restatement or the unconditional `minimalCover` is adopted, the
  bullets need updating; those findings say so.
- **exists_set_encard_eq_coveringNumber**: the statement is correct. The proof is longer than
  needed, because `A` itself witnesses `Nonempty`. The deeper point: `h` is only needed for
  finiteness, which gives the generalization finding on `minimalCover`. Both versions verified.
- **minimalCover** (def): `open Classical in` is unnecessary; removing it compiled, and the sibling
  `maximalSeparatedSet` does not use it. The `∅` fallback is avoidable (generalization finding,
  verified by splicing the whole section). Docstring otherwise fine.
- **minimalCover_subset / finite_minimalCover / isCover_minimalCover / card_minimalCover**:
  correct. `card_minimalCover` should be `encard_minimalCover` (naming_norm: established, 84/88).
  The `simp only [..., ↓reduceDIte]` pattern is covered by the dif_pos finding. `finite_minimalCover`
  has a needless line break in its statement; too minor to file.
- **exists_set_encard_eq_packingNumber**: correct. The empty case split is unnecessary (`∅` is
  separated), and the neighbouring `exists_finite_isCover_of_totallyBounded` uses the
  bounded-binder form. Verified.
- **maximalSeparatedSet** (def): correct, but it lacks the `finite_maximalSeparatedSet` counterpart
  to `finite_minimalCover`; adding it verified. The fallback here is genuinely needed: a `⊤`
  supremum need not be attained.
- **maximalSeparatedSet_subset / isSeparated_maximalSeparatedSet**: correct. `split_ifs` golfs
  verified. `isSeparated_maximalSeparatedSet` has a redundant `(… : Set X)` ascription (removing
  it compiled). I did not file that separately; it is too minor.
- **card_maximalSeparatedSet**: correct. The name should be `encard_maximalSeparatedSet`
  (established). `dif_pos` golf verified.
- **card_le_of_isSeparated**: the name is generic and uses `card` for `encard` (established).
  The proof re-derives `IsSeparated.encard_le_packingNumber`. Rename plus one-line proof verified,
  together with the updated caller.
- **isCover_maximalSeparatedSet**: the main finding. It reproves the existing
  `IsCover.of_maximal_isSeparated` (Cover.lean:78) by hand in about 25 lines; a 6-line proof via
  `Maximal` verified.
- **packingNumber_two_mul_le_externalCoveringNumber**: only moved into `section Comparisons`.
  Nothing to ask.
- **coveringNumber_le_packingNumber**: correct (Vershynin 4.2.8). Golf via
  `IsCover.coveringNumber_le_encard` verified. No docstring (documentation finding).
- **coveringNumber_two_mul_le_externalCoveringNumber**: correct. The unused `rcases` on
  emptiness can go; the one-term proof verified.
- **coveringNumber_subset_le**: correct. Naming and `ε / 2` versus the siblings' `2 * ε`: the
  restated `coveringNumber_two_mul_le_coveringNumber_of_subset` verified. Separately, the calc
  indentation, the redundant two-step path through `packingNumber`, and `ring_nf` in place of
  `mul_div_cancel₀`: the reproof verified. The chain actually proves the stronger
  `coveringNumber ε A ≤ externalCoveringNumber (ε / 2) B`. I did not file that, since it is not
  clearly a statement maintainers would want.
- **section commands**: `MinimalCover`, `MaximalSeparatedSet` and `Comparisons` are properly
  opened and closed. Nothing to ask.

## Checked and not raised

- Correctness: every statement is mathematically right and the file builds clean. No
  linter warnings.
- Generalization of `PseudoEMetricSpace`: already the weakest reasonable class.
- Duplication: `declaration_search` finds `minimalCover` only in this PR. No prior
  maximal-separated-set definition exists; `IsCover.of_maximal_isSeparated` is only a property.
- Scope: everything is in the right file. The `exists_*` lemmas are reasonable public API, so I
  did not ask to privatise them.
