# PR #33066: feat(Analysis/Normed/Operator): star-algebra equivalences between continuous endomorphisms are isometrically inner

## Description

This is the star-algebra equivalence version of [AlgEquiv.eq_linearEquivConjAlgEquiv](https://leanprover-community.github.io/mathlib4_docs/Mathlib/LinearAlgebra/GeneralLinearGroup/AlgEquiv.html#AlgEquiv.eq_linearEquivConjAlgEquiv) and [ContinuousAlgEquiv.eq_continuousLinearEquivConjContinuousAlgEquiv](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Analysis/Normed/Operator/ContinuousAlgEquiv.html#ContinuousAlgEquiv.eq_continuousLinearEquivConjContinuousAlgEquiv). So we now have a characterization of algebra, continuous algebra, and star-algebra equivalences between endomorphisms.

The proof follows the same idea as the one in #28972.

The proof of this is much longer than the `ContinuousAlgEquiv` and the `AlgEquiv` versions. Please feel free to golf!

The proof has private auxiliary lemmas and definitions because otherwise the proof gets too long and slow.

- [x] depends on: #33017
- [x] depends on: #33022

## Changed files

- `Mathlib/Analysis/InnerProductSpace/Adjoint.lean`
- `Mathlib/Analysis/Normed/Operator/ContinuousAlgEquiv.lean`
- `Mathlib/LinearAlgebra/GeneralLinearGroup/AlgEquiv.lean`
- `Mathlib/Topology/Algebra/Algebra/Equiv.lean`
