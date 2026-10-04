# Review notes: PR #33066

Inputs read: `brief.md`, `pr.md`, `model.md`, `diff.patch`. Tools were called only through `./ptool`. Scratch
edits for `lean_verify_edit` are in `tmp/` (`g1.lean`: minimal sqrt golf; `g2.lean`: aux-free main proof;
`g2_splice.lean`: aux section deleted; `g3.lean`: `ofAlgEquiv` reorder; `g4.lean`: named instance; `g5.lean`:
`conjStarAlgEquiv_trans`; `g6.lean`: import block).

Baseline: `lean_verify_edit` with no edit on `Mathlib/Analysis/Normed/Operator/ContinuousAlgEquiv.lean` returned
`compiles: true` with no errors or warnings.

## Mathlib/Analysis/InnerProductSpace/Adjoint.lean

- **Section restructure** (`section linearIsometryEquiv` wrapping the existing `namespace ContinuousLinearMap`
  plus a new `namespace LinearIsometryEquiv`, sharing the `K` variable). Fine.
- **`LinearIsometryEquiv.conjStarAlgEquiv`**: built with `StarAlgEquiv.ofAlgEquiv` on
  `e.toContinuousLinearEquiv.conjContinuousAlgEquiv`. The definition is correct and in the right place, since it needs
  star = adjoint. `Unitary.conjStarAlgAut` exists (Algebra/Star/UnitaryStarAlgAut.lean), but it is the
  unitary-group automorphism on one algebra, not this `H ≃ₗᵢ K` equivalence, so this is not a duplicate. Finding:
  the docstring wording "isometry linear equivalence" should be "linear isometric equivalence" (0 other uses
  against 14 files).
- **`conjStarAlgEquiv_apply_apply`, `symm_conjStarAlgEquiv_apply_apply`, `conjStarAlgEquiv_apply`,
  `symm_conjStarAlgEquiv`, `conjStarAlgEquiv_refl`**: these copy `ContinuousLinearEquiv.conjContinuousAlgEquiv_*`
  in Topology/Algebra/Module/StrongTopology.lean:807-829 exactly: same statements, same simp attributes, same
  names. No finding. `naming_norm` returned `insufficient_evidence` for these. The `lemma`/`theorem` keywords are
  mixed within the block (the sibling uses only `theorem`), but I did not treat that as worth an ask.
- **`conjStarAlgEquiv_trans`**: re-binds `{G} [NormedAddCommGroup G] [InnerProductSpace 𝕜 G]`, shadowing the
  file-level `G`. Verified that `[CompleteSpace G]` alone suffices. Filed as an advisory finding.

## Mathlib/Analysis/Normed/Operator/ContinuousAlgEquiv.lean

- **Imports**: the Adjoint public import and the Pow.Real import are redundant (both verified removable; the
  Central.Basic import is needed, as the control run showed). Finding.
- **Placement / scope**: this is the only file of 141 under `Analysis/Normed` that imports `InnerProductSpace`.
  Advisory finding: move the star-algebra half to `Analysis/InnerProductSpace/`. I could not compile a new file,
  so this finding is unverified by compilation.
- **Module docstring**: title and summary updated correctly and within 100 chars. The `### TODO:` heading should
  be `## TODO`. Finding.
- **`ContinuousAlgEquiv.eq_continuousLinearEquivConjContinuousAlgEquiv`**: its body is unchanged; the model lists
  it because of the file-level context. Nothing to ask.
- **Aux section** (`auxContinuousLinearEquiv`, `coe_auxContinuousLinearEquiv`, `auxIsometry`, `coe_auxIsometry`,
  `coe_symm_auxIsometry`): module-private, since it has no `public` in a `module` file, which matches the PR
  description. It duplicates `LinearEquiv.smulOfNeZero` + `LinearEquiv.isometryOfInner`. I verified deleting the
  whole section, with a 59-line replacement for the old 126 lines. Finding (duplication, advisory).
- **`StarAlgEquiv.eq_linearIsometryEquivConjStarAlgEquiv`**: correct statement; the name matches the sibling
  `eq_continuousLinearEquivConjContinuousAlgEquiv`. The `Continuous f` hypothesis is acknowledged in a TODO, so I
  made no ask there. Findings:
  - golf of the α-real/positivity/rpow bookkeeping (`RCLike.pos_iff_exists_ofReal`, `√`, `isPositive_smul_iff`),
    verified both as a full rewrite and as a minimal rpow→√ change;
  - proof-comment typo "endormorphisms" and the nonexistent `y.conjAlgEquiv`;
  - a double space in a `simp_rw` list.
  I did not file the hypothesis names `this1/this2/this10/thisα'` separately, because the golf finding replaces
  them.
- **`OrderIsoClass` instance**: correct. The TODO comment explains that it is temporary, and it is needed only
  until `StarOrderedRing (V →L[𝕜] V)` exists. `OrderIsoClass` is a Prop, so it cannot create a data diamond with
  `StarRingEquivClass.instOrderIsoClass`. Finding: it is anonymous, while its named precedent is not. A named
  version compiled.
- `open ComplexOrder` vs `open scoped ComplexOrder`: both spellings are common (15 vs 20 files), so no finding.

## Mathlib/LinearAlgebra/GeneralLinearGroup/AlgEquiv.lean

- The only change is a module-doc pointer to the continuous versions. It is accurate. No finding.

## Mathlib/Topology/Algebra/Algebra/Equiv.lean

- **`ContinuousAlgEquiv.ofAlgEquiv`**: its role matches `StarAlgEquiv.ofAlgEquiv`. The `declaration_search` hits
  in other namespaces are unrelated `ofAlgEquiv`s, and there is no `AlgEquiv.toContinuousAlgEquiv`. Findings:
  - the docstring omits that the inverse must also be continuous;
  - the adjacent `_root_.AlgEquiv.isUniformEmbedding` rebuilds the same structure inline and could use
    `ofAlgEquiv` once the block is moved above it (verified).
- **`coe_ofAlgEquiv`, `toAlgEquiv_ofAlgEquiv`, `ofAlgEquiv_toAlgEquiv`, `symm_ofAlgEquiv`,
  `ofAlgEquiv_trans_ofAlgEquiv`**: all `rfl`, with sensible simp attributes and consistent names, and
  `naming_norm` gave no opinion. The sibling `StarAlgEquiv` API spells two of them `ofAlgEquiv_apply` /
  `ofAlgEquiv_symm`, but this file itself uses `symm_toAlgEquiv`/`coe_toAlgEquiv`, so there is no clear
  convention to hold the PR to. No finding.

## Not raised

- Correctness: every file compiles as the PR leaves it, and I found no semantic or API error.
- Generalization: the `CompleteSpace` hypotheses are needed for `adjoint`, and the instance's
  `NonUnitalAlgEquivClass` is already the weaker class. Nothing to weaken beyond the acknowledged TODO.
