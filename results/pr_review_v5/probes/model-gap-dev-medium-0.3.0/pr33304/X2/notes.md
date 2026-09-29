# PR #33304 review notes (X2)

This is a documentation-only PR. It rewrites file references in docstrings and comments in 13
CategoryTheory files to full `Mathlib/.../X.lean` paths. That is the spelling maintainers asked for
on Zulip (thread "Broken file references", Eric Wieser and Yaël Dillies, 2024-11). No declaration
statement, proof or name changes. So the proof-golf, generalization, duplication and naming items
do not apply. For each reference I checked that the new target exists at review time and that it
really contains what the text says it does. I checked that the old target is gone. I also checked
the added line lengths: the longest is 98 characters, under the 100 limit.

Workspace paths are under `target/`. `file_search` returned nothing for every glob I gave it, so I
checked existence with `file_read` on each path.

## Object by object

- **StrictPseudofunctor.lean module doc (TODO).** `Mathlib/CategoryTheory/Bicategory/Functor/Strict.lean`
  exists. It is a `deprecated_module (since := "2025-10-02")` that re-exports
  `Bicategory.Strict.Pseudofunctor`, so the TODO still makes sense. The full path appears twice,
  which reads a little heavily but is not wrong. No finding.
- **Bundled.lean module doc.** The old `HasForget/UnbundledHom.lean` and `HasForget/BundledHom.lean`
  do not exist. The new `ConcreteCategory/UnbundledHom.lean`, `ConcreteCategory/BundledHom.lean`
  and `ConcreteCategory/Basic.lean` do. BundledHom.lean does hold `instance category : Category (Bundled c)`.
  No finding.
- **`CategoryTheory.BundledHom` and `CategoryTheory.UnbundledHom` deprecation messages.** Only the
  path inside the string changes; the `\` line continuations are intact. No finding.
- **Functor/Basic.lean.** The line 65 fix is right: `Mathlib/Tactic/CategoryTheory/Reassoc.lean`
  exists and does `public import Mathlib.CategoryTheory.Functor.Basic`, and `Mathlib/Tactic/Reassoc.lean`
  is gone. **Finding:** line 130 still says `Whiskering.lean`. That is a short path, and the wrong
  file: `Functor.leftUnitor`, `Functor.rightUnitor` and `Functor.associator` are defined in
  `Mathlib/CategoryTheory/Functor/Category.lean`. The replacement comment compiles (lean_verify_edit
  succeeded).
- **Subgroupoid.lean module doc.** `Mathlib/GroupTheory/Subgroup/Basic.lean` is gone and
  `Mathlib/Algebra/Group/Subgroup/Basic.lean` exists. `SimpleGraph/Subgraph.lean` exists. No finding.
- **FunctorCategory/Filtered.lean and FunctorCategory/Finite.lean module docs.** The old
  `Limits/FunctorCategory.lean` is gone and `Limits/FunctorCategory/Basic.lean` exists. The
  unchanged references `Limits/Filtered.lean` and `Limits/Shapes/FiniteProducts.lean` exist. No finding.
- **HasLimits.lean docstring (line 709).** `Mathlib/Tactic/CategoryTheory/Reassoc.lean` is correct.
  The other references in the file (`Adjunction/Limits.lean`, `Limits/ConeCategory.lean` together
  with `hasLimitsOfShape_iff_isLeftAdjoint_const`) resolve. Something I noticed but did not submit,
  because it is a declaration-name issue outside this PR's file-reference remit: the comment at
  lines 446-447 names `hasLimitCompEquivalence` / `hasLimitOfCompEquivalence`. Neither exists; the
  actual declarations in `Adjunction/Limits.lean` are `hasLimit_comp_equivalence` /
  `hasLimit_of_comp_equivalence`.
- **Preserves/Limits.lean module doc.** The old `preserves/shapes.lean` is a mathlib3 path.
  `Limits/Preserves/Shapes/` is a real directory (for example `Shapes/Products.lean`). No finding.
- **Preserves/Over.lean module doc.** `Adjunction/Over.lean` is gone. `Comma/Over/Pullback.lean`
  holds `Over.forgetAdjStar : forget X ⊣ star X` and `instance : (forget X).IsLeftAdjoint`, which is
  the claim the doc makes. No finding.
- **Localization/Equivalence.lean module doc.** The path now points at
  `Mathlib/CategoryTheory/Localization/Predicate.lean`, and the paragraph is reflowed to fit 100
  columns. `Localization.of_equivalence_target` is declared there. No finding.
- **Monoidal/Mon_.lean section doc.** The old `Monoidal/Braided.lean` is gone. `Monoidal/Braided/Basic.lean`
  holds `tensorμ`, `associator_monoidal` and `leftUnitor_monoidal`. The other references in the file
  (`Tactic/Attr/Register.lean`, `Monoidal/Internal/Module.lean`) exist. No finding.

## Out of scope, not submitted

Other short or broken `.lean` references remain elsewhere in CategoryTheory, in files this PR does
not touch. Examples: `Limits/Cones.lean` "see `cone_category.lean`"; `Comma/Basic.lean` `Over.lean`
and `Arrow.lean`; `Sites/Grothendieck.lean` `Sheaf.lean` and `Plus.lean`; `Abelian/Basic.lean`
`NonPreadditiveAbelian.lean`. A partial cleanup PR like this one is normally accepted without
asking for these, so I did not raise them.

precedent_search returned unrelated comments.
