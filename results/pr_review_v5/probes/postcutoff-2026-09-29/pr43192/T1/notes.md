# Review notes, PR #43192 (PresheafOfModulesOfCommRing)

Inputs read: brief.md, pr.md, model.md, diff.patch. Base context read through `ptool file_read`:
`ModuleCat/Presheaf.lean`, `Presheaf/ChangeOfRings.lean`, `Presheaf/Pushforward.lean`,
`Presheaf/Pullback.lean` (to line 119), `Presheaf/PushforwardZeroMonoidal.lean`, plus the import
lines of Monoidal, Generator, Free, Differentials/Presheaf and Stalk.

As-is compile check of `OfCommRing.lean`: compiled, no errors, no warnings.

## Object by object

- **`Mathlib.lean` import**: inserted in alphabetical order (Monoidal < OfCommRing < Pullback). Nothing to ask.
- **module doc**: title is missing "of" and the main abbrev is never named. Finding 5.
- **`@[expose] public section`, `universe` line**: standard for the module system; universes all used. Nothing.
- **`open CategoryTheory Functor Limits`**: `Limits` is unused; it compiles without it. Finding 6.
- **`PresheafOfModulesOfCommRing`**: the abbrev itself compiles and works. Universe order puts `v` first,
  so `PresheafOfModulesOfCommRing.{v} R` matches `PresheafOfModules.{v}`. I did not ask for a rename. The
  existing `pushforward₀OfCommRingCat` uses an `OfCommRingCat` suffix, but no rule picks one spelling
  over the other.
- **`mk`**: correct, and the `CommRingCat.Hom.hom` congrArg forms elaborate. It drops the `cat_disch`
  autoParams that the structure fields have; adding them compiles. Finding 4 (together with `mkHom`).
- **`obj`**: fine. `M.obj X` now has type `ModuleCat (R.obj X)`, which is the PR's purpose (checked by rfl).
- **`map`**: a new head symbol, so `rw [PresheafOfModules.map_comp]` fails on `M.map (f ≫ g)` and
  `simp only` rewrites into the `R ⋙ forget₂` form. `map_id`/`map_comp` restated in the `R.map` form
  compile, and `rw` then works. Finding 3. (A baseline check showed that plain `simp` leaves the same
  coercion goal on `PresheafOfModules (R ⋙ forget₂ _ _)` too, so I did not blame that on the abbrev.)
  The body `PresheafOfModules.map _ _` could spell out `F f`, but that is too minor to ask for.
- **`mkHom`**: missing the `cat_disch` default for `naturality`, which `isoMk` in the same file has
  (Finding 4). On naming: `homMk` is the dominant Mathlib spelling (28 files against about 6 for `mkHom`), but
  `PresheafOfModules.homMk` already exists with a different meaning (built from a morphism of abelian
  presheaves). Renaming this one to `homMk` would mislead, so I made no naming ask. `naming_norm`
  returned `subject_unresolved`.
- **`isoMk`**: wraps `PresheafOfModules.isoMk` with the same binders (strict-implicit, `cat_disch`
  default). Base `@[simps!]` lemmas apply through the reducible abbrev. Nothing to ask.
- **`unit`**: rebinds `R`, shadowing the section variable; the `variable (R) in` form compiles. Finding 7.
  Universe `.{u}` matches base `PresheafOfModules.unit`.
- **`restrictScalars`**: `noncomputable` is needed (the base is noncomputable); `whiskerRight φ (forget₂ _ _)`
  typechecks against `PresheafOfModules.restrictScalars`. Nothing.
- **`pushforward₀`**: equal by `rfl` to the existing `PresheafOfModules.pushforward₀OfCommRingCat`, with
  the same type. The Monoidal instance from PushforwardZeroMonoidal is found for the new name. Finding 1
  (deprecate the old name).
- **`pushforward`, `pullback`, `pullbackPushforwardAdjunction`**: the bodies are correct. For small
  categories at universe `u`, `pullback φ` finds the `IsRightAdjoint` instance through the abbrev (the
  test example failed only on `noncomputable`). Nothing to ask.
- **File scope / imports**: the Basic section compiles with only `Presheaf.ChangeOfRings` imported. The
  files that would use the abbrev (Monoidal, Differentials/Presheaf, Stalk, PushforwardZeroMonoidal) sit
  below `Pullback`. Finding 2 (split the file).

## Families checked with nothing found

- proof-golf: there are no proofs, only one-line abbrev bodies.
- generalization: the abbrevs mirror the base declarations' generality (universes `u₁ v₁ u₂ v₂`; `pullback`
  under the same `IsRightAdjoint` hypothesis as the base). Nothing to weaken.
- correctness: the file compiles with no linter warnings, and every abbrev unfolds to the intended base term.

## Tools used

lean_verify_edit (as-is check, plus 11 edit or example checks), declaration_search, file_read,
file_search, content_search, naming_norm, zulip_search (no relevant prior discussion), precedent_search
(none applicable).
