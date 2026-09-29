# The PR model for #43192 (pass 0)

Built deterministically from the diff and the change graph, with no review text. Every entry is a **fact** unless marked `hypothesis`; a hypothesis is a question to check, not a premise. Not built, so not here: library candidates, the area's twin patterns and conventions, and other open PRs. Construct what you need of those with the tools.

## The PR

- title: feat(Algebra/Category/ModuleCat): add abbrevs for Presheaves of Modules over commutative rings
- description: Currently in mathlib, to define a presheaf of modules over a commutative ring, one
writes
```
variable  {C : Type*} [Category* C] (R : Cᵒᵖ ⥤ CommRingCat.{u}) (F : PresheafOfModules.{v} (R ⋙ forget₂ _ _))
```

The problem with this formulation is that many operations do not preserve the shape of `(R ⋙ forget₂ _ _)`. For
example, [PresheafOfModules.pushforward₀](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Algebra/Category/ModuleCat/Presheaf/Pushforward.html#PresheafOfModules.pushforward%E2%82%80) has type `PresheafOfModules (R ⋙ forget₂ _ _) ⥤ PresheafOfModules (F.op ⋙ R ⋙ forget₂ _ _)` when applied directly. This is why [PresheafOfModules.pushforward₀OfCommRingCat](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Algebra/Category/ModuleCat/Presheaf/Pushforward.html#PresheafOfModules.pushforward%E2%82%80OfCommRingCat) was introduced. There are now around a dozen of these comm ring specific abbrevs in open PRs. In this PR, I introduce `PresheafOfModulesOfCommRing` with the goal of having a namespace to put all of these as well as making it easier to avoid making mistakes.

For an example of this being used, see #43193.
- changed files: Mathlib.lean, Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean

## Objects

### `import in Mathlib.lean` (import, modified) [d9381245e6]
- file: `Mathlib.lean`; changed: imports:added

### `PresheafOfModulesOfCommRing.isoMk` (abbrev, added) [0552ca4c14]
- file: `Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean`; changed: name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
abbrev isoMk {M₁ M₂ : PresheafOfModulesOfCommRing.{v} R}
    (app : ∀ (X : Cᵒᵖ), M₁.obj X ≅ M₂.obj X)
    (naturality : ∀ ⦃X Y : Cᵒᵖ⦄ (f : X ⟶ Y),
      M₁.map f ≫ (ModuleCat.restrictScalars (R.map f).hom).map (app Y).hom =
        (app X).hom ≫ M₂.map f := by cat_disch) : M₁ ≅ M₂ :=
  PresheafOfModules.isoMk app naturality
```

### `attribute in OfCommRing.lean` (command, added) [0b5e6407f0]
- file: `Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean`; changed: unknown:added
- as the PR leaves it:
```lean
@[expose] public section
```

### `doc_comment in OfCommRing.lean` (command, added) [15b0e18594]
- file: `Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-- The restriction map of a presheaf of modules over a presheaf of commutative rings. -/
```

### `PresheafOfModulesOfCommRing.pushforward` (abbrev, added) [17693c1242]
- file: `Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean`; changed: attributes:added, name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
noncomputable abbrev pushforward :
    PresheafOfModulesOfCommRing.{v} R ⥤ PresheafOfModulesOfCommRing.{v} S :=
  PresheafOfModules.pushforward (whiskerRight φ (forget₂ _ _))
```

### `section in OfCommRing.lean` (command, added) [20ff885e9f]
- file: `Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean`; changed: namespace:added
- as the PR leaves it:
```lean
variable {C : Type u₁} [Category.{v₁} C] {R : Cᵒᵖ ⥤ CommRingCat.{u}}
```

### `section in OfCommRing.lean` (command, added) [23362e851c]
- file: `Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean`; changed: namespace:added
- as the PR leaves it:
```lean
end Basic
```

### `PresheafOfModulesOfCommRing.obj` (abbrev, added) [243b185270]
- file: `Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean`; changed: name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
abbrev obj (F : PresheafOfModulesOfCommRing.{v} R) (X : Cᵒᵖ) : ModuleCat.{v} (R.obj X) :=
  PresheafOfModules.obj F X
```

### `doc_comment in OfCommRing.lean` (command, added) [2709a4f8ab]
- file: `Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-- Restriction of scalars along a morphism of presheaves of commutative rings. -/
```

### `PresheafOfModulesOfCommRing.pullbackPushforwardAdjunction` (abbrev, added) [2be1f070d4]
- file: `Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean`; changed: attributes:added, name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
noncomputable abbrev pullbackPushforwardAdjunction
    [(pushforward.{v} φ).IsRightAdjoint] :
    pullback.{v} φ ⊣ pushforward.{v} φ :=
  PresheafOfModules.pullbackPushforwardAdjunction _
```

### `doc_comment in OfCommRing.lean` (command, added) [361101dc80]
- file: `Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-- Construct a presheaf of modules over a presheaf of commutative rings. -/
```

### `section in OfCommRing.lean` (command, added) [3c53c26f34]
- file: `Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean`; changed: namespace:added
- as the PR leaves it:
```lean
section PushforwardPullback
```

### `namespace in OfCommRing.lean` (command, added) [42ef65cbbf]
- file: `Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean`; changed: namespace:added
- as the PR leaves it:
```lean
open CategoryTheory Functor Limits
```

### `doc_comment in OfCommRing.lean` (command, added) [448887c867]
- file: `Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-- The pullback functor induced by a morphism of presheaves of commutative rings. -/
```

### `command in OfCommRing.lean` (command, added) [4e0ee1f31b]
- file: `Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
universe v v₁ v₂ u₁ u₂ u
```

### `section in OfCommRing.lean` (command, added) [5df2f029cd]
- file: `Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean`; changed: namespace:added
- as the PR leaves it:
```lean
end PresheafOfModulesOfCommRing
```

### `section in OfCommRing.lean` (command, added) [61438e5e15]
- file: `Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean`; changed: namespace:added
- as the PR leaves it:
```lean
section Basic
```

### `PresheafOfModulesOfCommRing.map` (abbrev, added) [7bd20be71e]
- file: `Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean`; changed: name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
abbrev map (F : PresheafOfModulesOfCommRing.{v} R) {X Y : Cᵒᵖ} (f : X ⟶ Y) :
    F.obj X ⟶ (ModuleCat.restrictScalars (R.map f).hom).obj (F.obj Y) :=
  PresheafOfModules.map _ _
```

### `section in OfCommRing.lean` (command, added) [7c4a31b956]
- file: `Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean`; changed: namespace:added
- as the PR leaves it:
```lean
end PushforwardPullback
```

### `namespace in OfCommRing.lean` (command, added) [8275d16736]
- file: `Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean`; changed: namespace:added
- as the PR leaves it:
```lean
namespace PresheafOfModulesOfCommRing
```

### `doc_comment in OfCommRing.lean` (command, added) [8c84fc7f59]
- file: `Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-- Construct an isomorphism of presheaves of modules over a presheaf of commutative rings. -/
```

### `doc_comment in OfCommRing.lean` (command, added) [97f73151eb]
- file: `Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-- Construct a morphism of presheaves of modules over a presheaf of commutative rings. -/
```

### `PresheafOfModulesOfCommRing.restrictScalars` (abbrev, added) [98140447e3]
- file: `Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean`; changed: attributes:added, name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
noncomputable abbrev restrictScalars {S : Cᵒᵖ ⥤ CommRingCat.{u}} (φ : R ⟶ S) :
    PresheafOfModulesOfCommRing.{v} S ⥤ PresheafOfModulesOfCommRing.{v} R :=
  PresheafOfModules.restrictScalars (whiskerRight φ (forget₂ _ _))
```

### `PresheafOfModulesOfCommRing.pullback` (abbrev, added) [99852d03ee]
- file: `Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean`; changed: attributes:added, name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
noncomputable abbrev pullback [(pushforward.{v} φ).IsRightAdjoint] :
    PresheafOfModulesOfCommRing.{v} S ⥤ PresheafOfModulesOfCommRing.{v} R :=
  PresheafOfModules.pullback (whiskerRight φ (forget₂ _ _))
```

### `PresheafOfModulesOfCommRing.pushforward₀` (abbrev, added) [9b2675e380]
- file: `Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean`; changed: name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
abbrev pushforward₀ (F : C ⥤ D) (R : Dᵒᵖ ⥤ CommRingCat.{u}) :
    PresheafOfModulesOfCommRing.{v} R ⥤
      PresheafOfModulesOfCommRing.{v} (F.op ⋙ R) :=
  PresheafOfModules.pushforward₀ F (R ⋙ forget₂ _ _)
```

### `doc_comment in OfCommRing.lean` (command, added) [a3f7cd911e]
- file: `Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-- The free presheaf of modules of rank one over a presheaf of commutative rings. -/
```

### `doc_comment in OfCommRing.lean` (command, added) [a8725ca4e5]
- file: `Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-- The category of presheaves of modules over a presheaf of commutative rings. -/
```

### `PresheafOfModulesOfCommRing.unit` (abbrev, added) [b5fcbfa796]
- file: `Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean`; changed: attributes:added, name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
noncomputable abbrev unit (R : Cᵒᵖ ⥤ CommRingCat.{u}) :
    PresheafOfModulesOfCommRing.{u} R :=
  PresheafOfModules.unit (R ⋙ forget₂ _ _)
```

### `doc_comment in OfCommRing.lean` (command, added) [bc2dca5283]
- file: `Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-- The pushforward functor induced by a morphism of presheaves of commutative rings. -/
```

### `section in OfCommRing.lean` (command, added) [c168f8dd3d]
- file: `Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean`; changed: namespace:added
- as the PR leaves it:
```lean
variable {C : Type u₁} [Category.{v₁} C] {D : Type u₂} [Category.{v₂} D]
```

### `PresheafOfModulesOfCommRing` (abbrev, added) [e2e940c17b]
- file: `Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean`; changed: name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
abbrev PresheafOfModulesOfCommRing {C : Type u₁} [Category.{v₁} C]
    (R : Cᵒᵖ ⥤ CommRingCat.{u}) :=
  PresheafOfModules.{v} (R ⋙ forget₂ _ _)
```

### `doc_comment in OfCommRing.lean` (command, added) [e5fe33c87b]
- file: `Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-- Evaluate a presheaf of modules over a presheaf of commutative rings at an object. -/
```

### `PresheafOfModulesOfCommRing.mk` (abbrev, added) [f444128202]
- file: `Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean`; changed: name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
abbrev mk (obj : ∀ (X : Cᵒᵖ), ModuleCat.{v} (R.obj X)) (map : ∀ {X Y : Cᵒᵖ} (f : X ⟶ Y),
      obj X ⟶ (ModuleCat.restrictScalars (R.map f).hom).obj (obj Y))
    (map_id : ∀ (X : Cᵒᵖ), map (𝟙 X) = (ModuleCat.restrictScalarsId' (R.map (𝟙 X)).hom
      (congrArg CommRingCat.Hom.hom (R.map_id X))).inv.app _)
    (map_comp : ∀ {X Y Z : Cᵒᵖ} (f : X ⟶ Y) (g : Y ⟶ Z),
      map (f ≫ g) = map f ≫ (ModuleCat.restrictScalars _).map (map g) ≫
        (ModuleCat.restrictScalarsComp' (R.map f).hom (R.map g).hom (R.map (f ≫ g)).hom
          (congrArg CommRingCat.Hom.hom <| R.map_comp f g)).inv.app _) :
    PresheafOfModulesOfCommRing.{v} R where
  obj := obj
  map := map
  map_id := map_id
  map_comp := map_comp
```

### `PresheafOfModulesOfCommRing.mkHom` (abbrev, added) [f5aad1e2ff]
- file: `Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean`; changed: name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
abbrev mkHom {M₁ M₂ : PresheafOfModulesOfCommRing.{v} R}
    (app : ∀ (X : Cᵒᵖ), M₁.obj X ⟶ M₂.obj X)
    (naturality : ∀ {X Y : Cᵒᵖ} (f : X ⟶ Y),
      M₁.map f ≫ (ModuleCat.restrictScalars (R.map f).hom).map (app Y) =
        app X ≫ M₂.map f) : M₁ ⟶ M₂ where
  app := app
  naturality := naturality
```

### `section in OfCommRing.lean` (command, added) [f6d716ceef]
- file: `Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean`; changed: namespace:added
- as the PR leaves it:
```lean
variable {F : C ⥤ D} {R : Dᵒᵖ ⥤ CommRingCat.{u}}
  {S : Cᵒᵖ ⥤ CommRingCat.{u}} (φ : S ⟶ F.op ⋙ R)
```

### `module_doc in OfCommRing.lean` (module_doc, added) [fc107232ca]
- file: `Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-!
# Modules over presheaves commutative rings

This file provides short names for categories and functors obtained from a presheaf of commutative
rings by forgetting to rings. In particular, these names reduce the need for
repeatedly writing the relevant forgetful functor.
-/
```

### `doc_comment in OfCommRing.lean` (command, added) [fdd33dc7d1]
- file: `Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-- The adjunction between pullback and pushforward for modules over presheaves of
commutative rings. -/
```

### `doc_comment in OfCommRing.lean` (command, added) [fe929c8109]
- file: `Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-- The pushforward functor along `F` for modules over a presheaf of commutative rings. -/
```

## Removed or renamed

- none

## Families (declarations that may be one decision)

- [exact] `PresheafOfModulesOfCommRing.pullback`, `PresheafOfModulesOfCommRing.pullbackPushforwardAdjunction`, `PresheafOfModulesOfCommRing.pushforward`, `PresheafOfModulesOfCommRing.pushforward₀` -- 4 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings

## Relations between changed declarations

- declaration_dependency [exact]: `PresheafOfModulesOfCommRing.isoMk` -> `PresheafOfModulesOfCommRing.restrictScalars`
- declaration_dependency [exact]: `PresheafOfModulesOfCommRing.isoMk` -> `PresheafOfModulesOfCommRing`
- declaration_dependency [exact]: `PresheafOfModulesOfCommRing.map` -> `PresheafOfModulesOfCommRing`
- declaration_dependency [exact]: `PresheafOfModulesOfCommRing.map` -> `PresheafOfModulesOfCommRing.restrictScalars`
- declaration_dependency [exact]: `PresheafOfModulesOfCommRing.mk` -> `PresheafOfModulesOfCommRing.restrictScalars`
- declaration_dependency [exact]: `PresheafOfModulesOfCommRing.mk` -> `PresheafOfModulesOfCommRing`
- declaration_dependency [exact]: `PresheafOfModulesOfCommRing.mkHom` -> `PresheafOfModulesOfCommRing.restrictScalars`
- declaration_dependency [exact]: `PresheafOfModulesOfCommRing.mkHom` -> `PresheafOfModulesOfCommRing`
- declaration_dependency [exact]: `PresheafOfModulesOfCommRing.obj` -> `PresheafOfModulesOfCommRing`
- declaration_dependency [exact]: `PresheafOfModulesOfCommRing.pullback` -> `PresheafOfModulesOfCommRing`
- declaration_dependency [exact]: `PresheafOfModulesOfCommRing.pullback` -> `PresheafOfModulesOfCommRing.pushforward`
- declaration_dependency [exact]: `PresheafOfModulesOfCommRing.pullbackPushforwardAdjunction` -> `PresheafOfModulesOfCommRing.pullback`
- declaration_dependency [exact]: `PresheafOfModulesOfCommRing.pullbackPushforwardAdjunction` -> `PresheafOfModulesOfCommRing.pushforward`
- declaration_dependency [exact]: `PresheafOfModulesOfCommRing.pushforward` -> `PresheafOfModulesOfCommRing`
- declaration_dependency [exact]: `PresheafOfModulesOfCommRing.pushforward₀` -> `PresheafOfModulesOfCommRing`
- declaration_dependency [exact]: `PresheafOfModulesOfCommRing.restrictScalars` -> `PresheafOfModulesOfCommRing`
- declaration_dependency [exact]: `PresheafOfModulesOfCommRing.unit` -> `PresheafOfModulesOfCommRing`
- direct_use_of_changed_declaration [exact]: `PresheafOfModulesOfCommRing.pushforward₀` -> `PresheafOfModulesOfCommRing.pushforward`
- name_family [high]: `PresheafOfModulesOfCommRing.pullback` -> `PresheafOfModulesOfCommRing.pullbackPushforwardAdjunction`
- name_family [high]: `PresheafOfModulesOfCommRing.pullbackPushforwardAdjunction` -> `PresheafOfModulesOfCommRing.pushforward₀`
- name_family [high]: `PresheafOfModulesOfCommRing.pullbackPushforwardAdjunction` -> `PresheafOfModulesOfCommRing.pullback`
- name_family [high]: `PresheafOfModulesOfCommRing.pullbackPushforwardAdjunction` -> `PresheafOfModulesOfCommRing.pushforward`
- name_family [high]: `PresheafOfModulesOfCommRing.pushforward` -> `PresheafOfModulesOfCommRing.pushforward₀`
- name_family [high]: `PresheafOfModulesOfCommRing.pushforward` -> `PresheafOfModulesOfCommRing.pullbackPushforwardAdjunction`
- name_family [high]: `PresheafOfModulesOfCommRing.pushforward₀` -> `PresheafOfModulesOfCommRing.pushforward`
- name_family [high]: `PresheafOfModulesOfCommRing.pushforward₀` -> `PresheafOfModulesOfCommRing.pullbackPushforwardAdjunction`
