# Review notes: PR #33066 (star-algebra equivalences between continuous endomorphisms are isometrically inner)

Inputs read: `brief.md`, `pr.md`, `model.md`, `diff.patch`. Tools: `ptool describe`, then `file_read`,
`file_search`, `content_search`, `declaration_search`, `naming_norm`, `precedent_search`,
`zulip_search` and `lean_verify_edit`. Scratch Lean snippets are in `tmp/`.

The PR file `Mathlib/Analysis/Normed/Operator/ContinuousAlgEquiv.lean` compiles as left: an as-is
`lean_verify_edit` returned `compiled` with no errors and no warnings. Each compile took about 25 s.

I wrote 9 findings, all advisory. Three are verified proof golfs (A, B, C), three are style or
documentation fixes in the main proof, one is a module-doc heading, one is a scope request, and one is
a docstring fix.

## Mathlib/Analysis/InnerProductSpace/Adjoint.lean

- `section linearIsometryEquiv` / `namespace` moves: the `K` variable is hoisted out of
  `namespace ContinuousLinearMap` so that `LinearIsometryEquiv` can share it. The section name is a
  little off, because the section also contains the `ContinuousLinearMap` lemmas, but it is harmless.
  No finding.
- `LinearIsometryEquiv.conjStarAlgEquiv` and its API (`_apply_apply`, `symm_..._apply_apply`,
  `_apply`, `symm_conjStarAlgEquiv`, `_refl`, `_trans`): checked against the base
  `ContinuousLinearEquiv.conjContinuousAlgEquiv` API in `Topology/Algebra/Module/StrongTopology.lean`
  (lines 807-829). The names, `@[simp]` choices and statement shapes mirror it one for one (simp on
  `apply_apply`, `symm` and `refl`; not on `apply` or `trans`). `naming_norm` on
  `symm_conjStarAlgEquiv` gave insufficient_evidence (`symm_` is a plurality). The docstring is
  slightly awkward ("isometry linear equivalence") but mirrors its sibling. No finding.

## Mathlib/Topology/Algebra/Algebra/Equiv.lean

- `ContinuousAlgEquiv.ofAlgEquiv` and its five lemmas. The structure is
  `extends A ≃ₐ[R] B, A ≃ₜ B`, so `ofAlgEquiv` is essentially the constructor. It does parallel
  `StarAlgEquiv.ofAlgEquiv`, though, and it is used in the main proof via `coe_ofAlgEquiv`, so I did not
  ask for its removal. `naming_norm` on `symm_ofAlgEquiv` and `ofAlgEquiv_trans_ofAlgEquiv` gave
  insufficient_evidence. (Base `StarAlgEquiv` uses `ofAlgEquiv_symm`, but the corpus has no dominant
  spelling.)
  - **Finding I**: the docstring says "when it is continuous", but the definition also needs the
    inverse to be continuous.

## Mathlib/LinearAlgebra/GeneralLinearGroup/AlgEquiv.lean

- The module doc gains a cross-reference to the continuous file. Fine. No finding.

## Mathlib/Analysis/Normed/Operator/ContinuousAlgEquiv.lean

- **Imports.**
  - `public import ...InnerProductSpace.Adjoint`: removing it alone still compiles, because
    `Positive` implies it. Too weak to ask for.
  - `import Mathlib.Algebra.Central.Basic`: needed. Removing it breaks
    `Algebra.IsCentral.center_eq_bot`.
  - `import ...SpecialFunctions.Pow.Real`: removable (it compiles without it). Folded into Finding C.
- **Scope (Finding H).** `content_search` shows no file under `Mathlib/Analysis/Normed/` imports
  `Mathlib/Analysis/InnerProductSpace/` at base. This PR adds the first such import, and only for
  the Hilbert-space half. Nothing imports `ContinuousAlgEquiv.lean`, so moving that half to a new file
  under `InnerProductSpace/` creates no cycle. Advisory: no directory linter fired.
- **Module docstring (Finding D).** `### TODO:` should be `## TODO`: 641 files use `## TODO`, and this
  file is the only `### TODO:`. The title line is within 100 characters (no lint warning).
- **`ContinuousAlgEquiv.eq_continuousLinearEquivConjContinuousAlgEquiv`.** Unchanged by the PR. The
  model lists it because of the surrounding hunk. No finding.
- **`variable` block** (line 89): exactly 100 characters, so no long-line lint. All of its binders are
  needed.
- **`auxContinuousLinearEquiv` / `coe_auxContinuousLinearEquiv` (Finding A).** The inverse is defined
  as `α' • adjoint e`, which forces `he'` and makes the main proof build `thisU`. The existing
  `ContinuousLinearEquiv.smulLeft` (a group element acting as a continuous linear equivalence) gives
  `e.trans (.smulLeft (Units.mk0 α' _))` directly.
  - Verified in line mode (lines 92-217): `auxIsometry` rebuilt on `smulLeft`, and
    `auxContinuousLinearEquiv`, `coe_auxContinuousLinearEquiv`, `coe_auxIsometry`,
    `coe_symm_auxIsometry`, `he'`, `thisU` and `la` all deleted. Result `compiled`, no warnings.
  - It needs the surjectivity ending from Finding B. With the PR's original ending, the final `simp`
    cannot unfold `U.symm`.
- **`auxIsometry`, `coe_auxIsometry`, `coe_symm_auxIsometry`.**
  - `norm_map'` is fine as written; I kept its proof unchanged in A.
  - `coe_symm_auxIsometry` exists only for the final `simp`. Finding B removes the need for it.
  - These declarations are module-private (non-`public` in a `module` file), so their root-namespace
    names do not leak. No naming finding.
- **`StarAlgEquiv.eq_linearIsometryEquivConjStarAlgEquiv`.** The name mirrors the
  `ContinuousAlgEquiv` and `AlgEquiv` siblings. The hypotheses are needed (`hf` is covered by the
  TODO).
  - Finding B (verified): close the proof via `U.surjective` and `symm_apply_apply`. This deletes
    `la` and `coe_symm_auxIsometry`.
  - Finding C (verified): use `√(re α)` instead of `rpow (-(1/2))`, which shortens `αa2` and `la`,
    and drop the `Pow.Real` import.
  - Finding E: the double space at line 173.
  - Finding F: the comment says `y.conjAlgEquiv` where it should say `y.conjContinuousAlgEquiv`, and
    has the typo "endormorphisms" and the grammar slip "algebra ... are central".
  - Finding G: hypothesis names (`this` reused, `this10`, `this1`, `this2` changing meaning,
    `thisα`, `thisα'`, `thisU`).
  - Combined check: a polished version with B, C, E, F and G applied passed `lean_verify_edit` in
    declaration mode, `compiled` with no warnings.
  - Checked and left alone:
    - The `IsUnit`-based proof of `α ≠ 0`, the `ComplexOrder` positivity block and the
      subsingleton case. I found no clearly shorter, verified replacement.
- **The `OrderIsoClass` instance.** Its hypotheses
  (`NonUnitalAlgEquivClass` + `StarHomClass`) match the base convention of
  `StarAlgEquivClass.toStarAlgEquiv`. `OrderIsoClass` is a `Prop`, so overlapping with
  `StarRingEquivClass.instOrderIsoClass` (which already applies for `𝕜 = ℂ` via
  `ContinuousLinearMap.instStarOrderedRing`) creates no diamond. The TODO comment is accurate for
  general `RCLike 𝕜`. Possible asks I did not submit, because the evidence for either was weak:
  - name the instance;
  - split it into its own PR.

## Other tool use

- `precedent_search` on the rpow block, the instance, `ofAlgEquiv`, the aux definition and
  `conjStarAlgEquiv` returned only loosely related comments. One was kbuzzard on manual instance
  naming. None changed the findings.
- `zulip_search` found no prior discussion of this API.
