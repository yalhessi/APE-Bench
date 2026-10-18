# Review notes: PR #33066 (reviewer TA1)

## Method

I read `brief.md`, `pr.md`, `model.md` and `diff.patch`, then read the three changed Lean files and their siblings through `ptool file_read`:
- `StrongTopology.lean` (the `conjContinuousAlgEquiv` family);
- `StarAlgHom.lean` (`StarAlgEquiv.ofAlgEquiv`);
- `Positive.lean`, `Central/Basic.lean`, `SeparatingDual.lean` and `LinearIsometry.lean`.

I used `declaration_search`, `content_search`, `naming_norm`, `precedent_search` and repeated `lean_verify_edit` runs. Each proposed edit marked "verified" below compiled in the PR's workspace (outcome `compiled`). The file as the PR leaves it compiles with no warnings.

## Object by object

### `Mathlib/Analysis/Normed/Operator/ContinuousAlgEquiv.lean`

**Imports.**
- `public import ...Adjoint` is redundant: Positive -> Spectrum -> Rayleigh -> Adjoint. Verified by dropping it.
- `import ...SpecialFunctions.Pow.Real` is redundant. Verified by deleting it.
- `import Mathlib.Algebra.Central.Basic` is needed: removing it breaks the file.
- A blank line separates the public and private import blocks.
- Scope: Positive pulls Spectrum, Matrix.Hermitian and Matrix.PosDef into a Normed/Operator file. I filed a request to move the Hilbert-space half to a new file.

**Module docstring.** I filed one finding covering:
- `### TODO:` should be `## TODO`;
- the PR's two new TODOs sit outside the module docstring;
- "same idea as the non-continuous version" is now inaccurate;
- there is no Main results list.

The title line is 99 characters, so it is within the limit.

**`variable {𝕜 V W ...}` (line 89).** Exactly 100 characters, within the limit. Nothing filed.

**`section auxiliaryDefs` / `variable` / `include`.**
- Filed: no blank line after `section`.
- Filed: the `variable` line breaks early (included in the line-break finding).

**`auxContinuousLinearEquiv`, `auxIsometry`** (and `coe_auxContinuousLinearEquiv`, `coe_auxIsometry`, `coe_symm_auxIsometry`):
- *Duplication / golf.* I filed deleting the whole section in favour of `LinearIsometryEquiv.ofSurjective` inside the main proof. Verified: lines 92-217 replaced by a 60-line version, and the whole file, including the instance, compiles.
- *If kept:*
  - Placeholder names: filed as blocking.
  - `abbrev` → `def`: verified. It needs an explicit unfold in `coe_symm_auxIsometry`, which shows the abbrev was only there for simp.
  - The "certain properties" docstring is generic.
  - The `auxIsometry` docstring is a verb phrase.
  - Untyped `have :=` in `left_inv`/`right_inv`: verified with typed `have`s.
  - The signatures break where they fit on one line: verified.
  - `theorem` is used for undocumented coe lemmas.
- `naming_norm` could not resolve a subject for the coe lemmas, so I made no prefix claim.

**`StarAlgEquiv.eq_linearIsometryEquivConjStarAlgEquiv`.** I filed:
- (a) the `ofSurjective` restructuring;
- (b) `RCLike.pos_iff_exists_ofReal` plus `√` in place of the separate reality, positivity and rpow steps (verified);
- (c) `Algebra.IsCentral.mem_center_iff` for the center step (verified);
- (d) `▸` → `rw` at lines 172, 179, 196, 197 and 200 (verified, since the rewrite has none);
- (e) the doubled space at line 173;
- (f) hypothesis names and untyped `have`s;
- (g) the docstring defined by contrast;
- (h) errors in the proof comment;
- (i) extracting `IsUnit (adjoint e ∘L e)` as a lemma (none exists: `content_search` found nothing).

Checked and left alone:
- The `Subsingleton` case split is fine.
- `hf : Continuous f` with its TODO is fine.
- The theorem name matches the sibling `ContinuousAlgEquiv.eq_continuousLinearEquivConjContinuousAlgEquiv`. `naming_norm` gave `subject_unresolved`, so nothing was filed.

**`open ComplexOrder`.** Filed as `open scoped` (verified). The library census is 12 `open scoped` to 5 plain.

**Instance `OrderIsoClass F _ _`.**
- Filed: it has no docstring.
- Not filed: the instance argument structure. `𝕜` is reached through outParams of `NonUnitalAlgEquivClass`, and priority 100 is set, so I found no instance-search defect.
- Not filed: the auto-generated name, which no listed convention covers.
- The proof (`le_def`, `isPositive_toLinearMap_iff`, `isPositive_linearIsometryEquiv_conj_iff`) is short and canonical. No golf.

**Pre-existing `ContinuousAlgEquiv.eq_continuousLinearEquivConjContinuousAlgEquiv`.** The PR does not change it; it only appears in the model as context. Not reviewed for findings.

### `Mathlib/Analysis/InnerProductSpace/Adjoint.lean`

**`section linearIsometryEquiv` restructure.**
- Filed: the lowerCamel name, and that the section exists only to scope `K`. Verified alternative: declare `H K` together and drop the section.
- Filed separately: the missing blank lines after `section` and between the two `end`s.

**`LinearIsometryEquiv.conjStarAlgEquiv`.**
- Filed: the docstring is an "induces" sentence, not a noun phrase.
- The body (`.ofAlgEquiv ... fun x ↦ by simp [...]`) is a function application, not a structure instance, so the `where` convention does not apply. The 100-character `simp` line is within the limit.

**`conjStarAlgEquiv_apply_apply`, `symm_conjStarAlgEquiv_apply_apply`, `conjStarAlgEquiv_apply`, `symm_conjStarAlgEquiv`, `conjStarAlgEquiv_refl`, `conjStarAlgEquiv_trans`.**
- These mirror the `conjContinuousAlgEquiv` family in `StrongTopology.lean` exactly: same statements, same simp set.
- Filed: mixed `lemma`/`theorem` (verified with `lemma`).
- Filed: `@[simp]` on `_apply_apply` rather than the map-level `_apply`. Advisory, since the sibling does the same.
- Filed: `conjStarAlgEquiv_trans` re-binds `G`, which the file-level variable already provides. Verified.
- `symm_conjStarAlgEquiv_apply_apply` not being simp is correct (it is simp-provable through `symm_conjStarAlgEquiv`), so nothing filed there.
- `naming_norm` on `symm_conjStarAlgEquiv`: `insufficient_evidence` (no dominant prefix). Nothing filed.

**Compatibility with `Unitary.conjStarAlgAut`.** I tried a lemma relating `conjStarAlgEquiv` to `Unitary.conjStarAlgAut` when `H = K`. `conjStarAlgAut` is not visible in `Adjoint.lean` (compile error), so I did not file it.

### `Mathlib/Topology/Algebra/Algebra/Equiv.lean`

**`ContinuousAlgEquiv.ofAlgEquiv`.** Filed:
- `{ e with ... }` → `where` (verified);
- a docstring that is a verb phrase and is inaccurate (it omits the continuity of `e.symm`);
- reuse in `AlgEquiv.isUniformEmbedding`, which builds the same object inline (verified).

`declaration_search` finds no existing `AlgEquiv.toContinuousAlgEquiv`, so the definition itself is not a duplicate.

**`coe_ofAlgEquiv`, `toAlgEquiv_ofAlgEquiv`, `ofAlgEquiv_toAlgEquiv`, `symm_ofAlgEquiv`, `ofAlgEquiv_trans_ofAlgEquiv`.** Filed:
- untyped binders `(he he')` and `(hf hf' hg hg')`;
- `theorem` → `lemma`;
- missing `@[simp]` on the `trans` lemma, which four siblings have (verified: compiles, no linter warning).

Not filed: `naming_norm` gives `insufficient_evidence`/`subject_unresolved` for these names. The sibling `StarAlgEquiv.ofAlgEquiv` uses `ofAlgEquiv_apply`/`ofAlgEquiv_symm`, but the census does not settle the prefix.

### `Mathlib/LinearAlgebra/GeneralLinearGroup/AlgEquiv.lean`

The PR adds one cross-reference sentence to the module docstring. It is correct, and nothing is filed.

## Conventions: where filed and where left

- **`where` for structure instances.**
  - Filed: `ContinuousAlgEquiv.ofAlgEquiv`.
  - Left:
    - the `auxContinuousLinearEquiv`/`auxIsometry` bodies already use `where`;
    - the subsingleton case's `{ toLinearEquiv := 0, norm_map' ... }` is a term passed to `use`, not a definition;
    - `conjStarAlgEquiv` is an application of `.ofAlgEquiv`.
- **Blank line around `namespace`/`section`/`end`/`variable`.**
  - Filed: `Adjoint.lean` 643-644 and 713-714; `ContinuousAlgEquiv.lean` 92-93.
  - Left: `namespace LinearIsometryEquiv` (686) and the `namespace ContinuousLinearMap` move (646) already have blank lines around them.
- **`abbrev` only when needed.**
  - Filed: `auxIsometry` / `auxContinuousLinearEquiv`, verified as `def`.
- **Standalone docstring, not by contrast.**
  - Filed: `StarAlgEquiv.eq_linearIsometryEquivConjStarAlgEquiv`.
- **No unneeded or redundant imports.**
  - Filed: the `Adjoint` and `Pow.Real` imports.
  - Left: `Algebra.Central.Basic`. Removing it breaks the build.
- **Variables shared across declarations declared once.**
  - Filed: the `G` re-binding in `conjStarAlgEquiv_trans`.
  - Left:
    - the `e` binder repeated across the `conjStarAlgEquiv` lemmas matches the `StrongTopology` sibling;
    - the `(e : A ≃ₐ[R] B)` binder in `Equiv.lean` has a different type in `ofAlgEquiv_toAlgEquiv` (`A ≃A[R] B`), so one `variable` cannot cover them all.
- **Standard spacing.**
  - Filed: the doubled space at `ContinuousAlgEquiv.lean` line 173.
  - Left: a scan of all added lines found no trailing spaces, no space after an opening bracket, and no other doubled spaces.
- **Off-topic material or heavy imports go elsewhere.**
  - Filed: moving the Hilbert-space half of `ContinuousAlgEquiv.lean` to a new file.
- **Attribute applied to some siblings only.**
  - Filed: `@[simp]` missing on `ofAlgEquiv_trans_ofAlgEquiv`.
  - Left: in the `conjStarAlgEquiv` family, simp is absent on `symm_..._apply_apply` and `_trans`, as in the `conjContinuousAlgEquiv` sibling. `symm_apply_apply` follows from `symm_conjStarAlgEquiv` plus `_apply_apply`, so simp on it would be redundant. `_trans` expands rather than simplifies.
- **Line breaks only when over 100 characters.**
  - Filed: the `auxContinuousLinearEquiv` and `auxIsometry` signatures and the `variable (e ...)` line.
  - Left: every other multi-line form in the diff would exceed 100 characters if joined. I checked:
    - `toAlgEquiv_ofAlgEquiv` (about 109 characters joined);
    - `symm_ofAlgEquiv` (about 115);
    - the instance header;
    - the `thisU` statement;
    - the main theorem's docstring first line.
- **Definition docstring is a noun phrase.**
  - Filed: `conjStarAlgEquiv`, `auxIsometry` and `ofAlgEquiv`.
  - Left: the `auxContinuousLinearEquiv` docstring is already a noun phrase ("Scalar multiple of …"); its generic wording is filed under the next item but one.
- **Explicit types on a definition, or on a `have` whose statement is not evident.**
  - Filed:
    - the untyped `have :=` in `auxContinuousLinearEquiv`;
    - `this10` and `this1` in the main theorem, as part of the hypothesis finding.
  - Left:
    - `set αa := (((… : ℝ) : 𝕜)` carries its own ascription;
    - `set U := auxIsometry …` has an evident type;
    - all defs state their types.
- **Extract independent facts as lemmas.**
  - Filed: `IsUnit (adjoint y ∘L y)`.
- **Generic references named specifically.**
  - Filed: "given certain properties are satisfied" in the `auxContinuousLinearEquiv` docstring.
- **Descriptive names, not `aux`.**
  - Filed: `auxContinuousLinearEquiv` / `auxIsometry` and their coe lemmas.
- **Main results and TODO in the module docstring.**
  - Filed: the module-doc finding (`## TODO`, the stray TODOs, Main results).
- **Contiguous import block.**
  - Filed: the blank line at `ContinuousAlgEquiv.lean` line 13.
- **Explicit types for binders.**
  - Filed: `(he he')` and `(hf hf' hg hg')` in the `ofAlgEquiv` lemmas.
  - Left: all other new binders are typed.
- **`theorem` only for documented results.**
  - Filed:
    - `Adjoint.lean`: `symm_conjStarAlgEquiv_apply_apply`, `conjStarAlgEquiv_refl`, `conjStarAlgEquiv_trans`;
    - `Equiv.lean`: all five `ofAlgEquiv` lemmas;
    - `ContinuousAlgEquiv.lean`: three coe lemmas.
  - Left: `StarAlgEquiv.eq_linearIsometryEquivConjStarAlgEquiv` is a documented `theorem`.
- **Hypotheses named after what they constrain.**
  - Filed: `thisα`, `thisα'`, `this2`, `thisU`, `la`, `αa2` and related names in the main theorem.
  - Left: `hα`, `hα2`, `he`, `he'` and `hαa` in the aux section are named after their variables.
- **Section names spelled as the notion.**
  - Filed: `section linearIsometryEquiv`.
  - Left: `section auxiliaryDefs` is not about one notion. It is covered by the delete-the-section golf.
- **simp on map-level `_apply` vs `_apply_apply`.**
  - Filed: `conjStarAlgEquiv_apply_apply` / `conjStarAlgEquiv_apply`.
  - Left: the `ofAlgEquiv` family has no such pair, since `coe_ofAlgEquiv` is already the map-level form.
- **New notions carry docstrings.**
  - Filed: the `OrderIsoClass` instance.
  - Left: `conjStarAlgEquiv`, `ofAlgEquiv` and the aux defs all have docstrings.
- **`rw` rather than `▸`.**
  - Filed: the five `▸` uses in the main theorem (lines 172, 179, 196, 197, 200).
  - Left: the pre-existing `this ▸ T'.continuous` at line 85 is not changed by this PR.
- **`open scoped` for notation namespaces.**
  - Filed: `open ComplexOrder` at line 141.
  - Left: `open ContinuousLinearMap ContinuousLinearEquiv in` in `Adjoint.lean` opens declaration namespaces, not notation.

## Outputs

`findings.json` contains 35 findings: 2 blocking (the redundant imports and the placeholder aux names) and 33 advisory. Edits I tried during the review are in `tmp/`. `golf2_full.lean` is the verified replacement for the auxiliary section and the main theorem.
