# Review notes: PR #43192 (PresheafOfModulesOfCommRing abbrevs)

Inputs read: brief.md, pr.md, model.md and diff.patch. Every tool call went through `./ptool`, and
temporary argument files are in `tmp/`.

## Baseline
- `lean_verify_edit` with no edit: the file compiles as the PR leaves it, with no errors and no warnings.

## Object by object

- **`Mathlib.lean` import.** It is in the right alphabetical place (between `Presheaf.Monoidal` and
  `Presheaf.Pullback`). Nothing to request.
- **Module docstring.** The title is missing "of" ("presheaves commutative rings"), so I filed a
  documentation finding. Apart from that the body is adequate.
- **`@[expose] public section`.** Every declaration is an abbrev, and the section matches the
  sibling files (Pushforward.lean and Pullback.lean both use `@[expose] public section`). Nothing
  to request.
- **`universe` line.** All the universes are used. Nothing to request.
- **`open CategoryTheory Functor Limits`.** `Limits` is unused. I removed it and the file compiled
  cleanly, so I filed a style finding. `Functor` is needed for `whiskerRight`.
- **`PresheafOfModulesOfCommRing` (the core abbrev).** Its definition is fine. `naming_norm` could
  not resolve its subject, and I found no Zulip discussion of the name, so I make no naming request.
  Its placement behind the `Pullback` import is the file-level scope finding: the Basic section
  compiles importing only `Presheaf.ChangeOfRings`, and Monoidal, Differentials/Presheaf, Stalk and
  PushforwardZeroMonoidal all work over `R ⋙ forget₂ _ _` without importing Pullback.
- **`mk`.** The field shapes match the `PresheafOfModules` structure, but `mk` drops the
  `by cat_disch` defaults on `map_id` and `map_comp`. The version with the defaults compiled, and so
  did `mk M.obj M.map` with no proofs given. Filed as a style finding.
- **`obj` and `map`.** These shadow the structure projections under dot notation. With them in
  place, `rw [PresheafOfModules.map_comp]` and `rw [PresheafOfModules.map_id]` fail on `M.map ...`.
  With them deleted, the rest of the file still compiles, both rewrites succeed, and the
  `R.obj X`-action on `M.obj X` is still found through the existing instance in Presheaf.lean.
  Filed as one finding on `map`, which also asks to delete `obj`.
- **`mkHom`.** Two findings:
  - Naming: the library uses `homMk` in 29 files against `mkHom` in 8, and it pairs with the
    `isoMk` right next to it. The rename compiles.
  - Style: `naturality` has no `by cat_disch` default, unlike `Hom.naturality` and `isoMk`. Adding
    one compiles.
- **`isoMk`.** It mirrors `PresheafOfModules.isoMk` exactly: the same strict-implicit binders and
  the same `cat_disch` default. Nothing to request.
- **`unit`.** The universe `{u}` matches `PresheafOfModules.unit`. The explicit `R` binder shadows
  the section's `{R}`, which works; I considered asking for `variable (R) in` but judged it too minor
  to request. It is correctly `noncomputable`.
- **`restrictScalars`.** It is correctly `noncomputable`, and `whiskerRight φ (forget₂ _ _)` is
  right. Nothing to request.
- **`pushforward₀`.** This duplicates `PresheafOfModules.pushforward₀OfCommRingCat`: I checked that
  they are equal by `with_reducible rfl`, and that the `Monoidal` instance from
  PushforwardZeroMonoidal is found for the new abbrev. Filed as a duplication finding asking for the
  old name to be deprecated. `pushforward₀` is rightly left computable, since the underlying
  `PresheafOfModules.pushforward₀` is computable.
- **`pushforward`, `pullback`, `pullbackPushforwardAdjunction`.** I checked a usability risk: in
  small categories, does instance search find `IsRightAdjoint` for the new `pushforward` even though
  it is stated through `whiskerRight` and `(F.op ⋙ R) ⋙ forget₂`? It does:
  `(pushforward.{u} φ).IsRightAdjoint := inferInstance` and `pullback φ` both elaborate. The
  hypotheses match those of the `PresheafOfModules` originals, and the docstrings are fine. Nothing
  to request.
- **Section and namespace structure, and the other docstrings.** Consistent. Nothing to request.

## Tools that gave nothing usable
- `zulip_search` found no prior discussion of `pushforward₀OfCommRingCat` or of this abbrev pattern.
- `precedent_search` returned unrelated comments only.
- `naming_norm` returned `subject_unresolved` for `PresheafOfModulesOfCommRing` and for `mkHom`, so
  I counted `homMk` against `mkHom` by hand with `content_search`.
- `file_search` returned empty results on the workspace; `file_read` and `content_search` under
  `target/` worked.
