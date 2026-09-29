# Review notes: PR #43192 (PresheafOfModulesOfCommRing abbrevs)

## Method
I read brief.md, pr.md, model.md and diff.patch. All tool calls went through `./ptool`. The
workspace paths for the base tree are `target/Mathlib/...`. I checked that the PR file compiles
as-is (`lean_verify_edit` with no edit: compiles, no errors, no warnings), and verified every edit
proposed in findings.json with `lean_verify_edit`. Scratch inputs are in `tmp/`.

Base-tree context I read:
- `Presheaf.lean`: the structure fields and their autoParams, `Hom`, `isoMk`, `homMk` and `unit`.
- `Presheaf/Pushforward.lean`: `pushforward₀`, `pushforward₀OfCommRingCat` and `pushforward`.
- `Presheaf/Pullback.lean`: its imports, and the general `IsRightAdjoint` instance for small
  categories.
- `Presheaf/PushforwardZeroMonoidal.lean`: the only use of `pushforward₀OfCommRingCat`.
- `Presheaf/ChangeOfRings.lean`: `restrictScalars`.

Zulip had no prior discussion of `PresheafOfModulesOfCommRing` or `pushforward₀OfCommRingCat`.
precedent_search surfaced erdOne asking for API lemmas on the original pushforward PR, which is
indirect support for finding 9.

## Object by object
- **Mathlib.lean import**: sits in the right alphabetical place (after `Monoidal`, before
  `Pullback`). Nothing to request.
- **Module doc**: typo in the title ("presheaves commutative rings"). Finding 1.
- **`@[expose] public section`, `universe` line**: standard, and all universes are used. The
  universe order (v first, from the `universe` command) makes `PresheafOfModulesOfCommRing.{v}`
  and `unit`'s `.{u}` correct, and the file compiles. Nothing to request.
- **`open CategoryTheory Functor Limits`**: `Limits` is unused, confirmed by recompiling without
  it. Finding 7.
- **`PresheafOfModulesOfCommRing` (abbrev)**: the definition and docstring are fine. It and the
  whole Basic section compile with only `Presheaf.ChangeOfRings` imported, but the file imports
  `Pullback`. That blocks adoption in `Pushforward.lean` (an import cycle) and in `Monoidal.lean`
  and similar files. Finding 6, a scope request to split the file. I considered asking for a
  different name and did not: I found no convention to cite.
- **`mk`**: the field statements match the structure with `CommRingCat.Hom.hom`, but the
  `cat_disch` autoParams are dropped. Finding 5, verified.
- **`obj`**: fine. It gives `ModuleCat (R.obj X)`, which is the stated point of the PR.
- **`map`**: the body `PresheafOfModules.map _ _` is fine. The new head symbol breaks `rw` with
  `PresheafOfModules.map_id` and `map_comp`; `simp` and term mode still work. I verified both
  failures and the fix. Finding 9. A body nit (`_ _` versus `F f`) was not worth a request.
- **`mkHom`**: two findings. Naming (finding 3): `homMk` has 19 definition sites in
  CategoryTheory against 4 for `mkHom`, and the same-named `PresheafOfModules.homMk` with a
  different signature is noted. The missing `cat_disch` autoParam on `naturality` (finding 4)
  was verified with an example that relies on the default.
- **`isoMk`**: mirrors `PresheafOfModules.isoMk`, including the `⦃⦄` binders and the autoParam.
  simps lemmas on the underlying `isoMk` apply through the reducible abbrev. Nothing to request.
- **`unit`**: rebinds `R`, shadowing the section variable. Finding 8 (`variable (R) in`),
  verified. `noncomputable` is needed because `PresheafOfModules.unit` is noncomputable. The
  docstring is fine.
- **`restrictScalars`**: correct whiskering, and `noncomputable` matches the underlying. Nothing
  to request.
- **`pushforward₀`**: reducibly equal to the existing `PresheafOfModules.pushforward₀OfCommRingCat`
  (verified by `with_reducible rfl`). Finding 2 asks to deprecate the old name. Its lack of
  `noncomputable` matches the underlying `def`.
- **`pushforward`**: correct, and `noncomputable` matches the underlying. Nothing to request.
- **`pullback`, `pullbackPushforwardAdjunction`**: mirror the originals, and the names match. I
  checked that the general small-category instance `(PresheafOfModules.pushforward.{u} φ).IsRightAdjoint`
  is found through the abbrev: a `noncomputable example` over `SmallCategory` built
  `pullbackPushforwardAdjunction φ'` without supplying the instance. Nothing to request.
- **Section and namespace structure**: well formed. Nothing to request beyond finding 6.

## Checked and not raised
- **Proof-golf**: nothing to golf; there are no proofs.
- **Generalization**: the abbrevs are specialisations by design.
- **Correctness**: the file compiles cleanly. Instance transfer through the abbrevs works, which
  I tested for `IsRightAdjoint`.
