# Review notes: PR #33321 (linear independence of indecomposable roots)

## Method

- Read `pr.md`, `model.md` and `diff.patch`. Read the changed files as the PR leaves them via `ptool file_read` (workspace root `target/`).
- Ran a baseline compile of `BaseExists.lean`: it compiles with no warnings.
- Tested every proposed edit with `lean_verify_edit`, using declaration mode or line mode. Helper scripts and argument files are in `tmp/`.
- One tool quirk: declaration mode drops the attribute when the new declaration omits it. With `@[to_additive]` included, the edit compiled. Declaration mode also cannot splice a def whose `to_additive` carries a docstring, so line mode was used there.
- Used `declaration_search`, `content_search`, `naming_norm` (no verdicts settled any name) and `precedent_search` (nothing specific).

## Object by object

### Mathlib.lean
- The new import `Mathlib.LinearAlgebra.RootSystem.BaseExists` is in sorted position (BaseChange < BaseExists < Basic). Nothing filed.

### Mathlib/Algebra/Group/Hom/Basic.lean
- `coe_invMonoidHom`, `invMonoidHom_apply`: these gain `to_additive`. `invMonoidHom` itself was already `to_additive`. No additive duplicates exist (`declaration_search` found none for `coe_negAddMonoidHom` or `negAddMonoidHom_apply`). Nothing filed. They are needed only by the long `Subgroup` proof (see below).
- `invMonoidHom_comp_invMonoidHom`: `by ext; simp` can be the term `MonoidHom.ext inv_inv` (compiled). Filed. This lemma is used only by `image_baseOf_inv_comp_eq`.

### Mathlib/Algebra/Group/Irreducible/Indecomposable.lean
- Imports. Lines 9 (`Subgroup.Lattice`), 13 (`Order.Group.Basic`) and 14 (`Order.Monoid.Defs`) can each be deleted and the file still compiles. A 4-import block compiles. The block is also unsorted (Defs before Basic). Filed two findings.
- `variable` line now carries `G S` with `[CommGroup G] [LinearOrder S]`. Checked; nothing wrong in itself.
- `IsMulIndecomposable.subset`: `aesop` can be `fun _ hi ↦ hi.1` (compiled). Filed.
- Namespace: four declarations are written with an `IsMulIndecomposable.` prefix outside the later `namespace IsMulIndecomposable`. A restructured block compiled. Filed.
- `IsMulIndecomposable.baseOf`: the docstring has a typo and does not say what the set is (filed). There is no membership lemma, so the definition is unfolded by hand at use sites; `mem_baseOf_iff := Iff.rfl` compiled (filed). It is defined as a predicate used as a `Set`; the setOf form compiled (filed).
- `baseOf_subset_one_lt`: fine apart from the redundant prefix, covered by the namespace finding.
- `image_baseOf_inv_comp_eq`: its name has a bare `_eq` and spells `inv` for `invMonoidHom`. Filed, advisory, and moot if the lemma is removed.
- `Submonoid.closure_image_isMulIndecomposable_baseOf`: renamed from `Submonoid.closure_image_one_lt_and_isMulIndecomposable` with no deprecation (blocking; the alias compiled). I also tried `let t := IsMulIndecomposable.baseOf v f` in its proof; that broke `grind`, so I did not file it. The pre-existing line `by_contra hk₂; exact ...` was left alone because the PR did not touch it.
- `Subgroup.closure_image_isMulIndecomposable_baseOf`: a 5-line proof from `mem_or_inv_mem_closure_baseOf` compiles, which makes `image_baseOf_inv_comp_eq` and the `Pointwise` import unnecessary (compiled with `Subgroup.Lattice`). Filed. This is the most substantive simplification.
- `pairwise_div_notMem_range`: filed `by_contra!` → `rintro`, a shorter golf without the duplicated `simp only`, and line breaks. All compiled.
- `pairwise_div_notMem_range'`: primed, and redundant given `pairwise_baseOf_div_notMem` plus `Pairwise.mono`. Removal compiled. Filed.
- `pairwise_baseOf_div_notMem`: the name lacks `_range`, unlike its sibling and the `Base` analogue. Filed, advisory.
- `mem_or_inv_mem_closure_baseOf`: doubled-space alignment; the single-line form compiled. Filed.
- Repeated binders across the namespace block: a `variable`/`include` form compiled. Filed, advisory.

### Mathlib/LinearAlgebra/RootSystem/BaseExists.lean (new)
- Imports: `Submodule.Union` is unused (compiled without it). `OrzechProperty` and `QuadraticForm.Dual` are needed. Filed.
- Module docstring: the title overclaims existence (filed). The heading is "Implementation details" rather than "Implementation notes", there is no Main results section, and one phrase is garbled (filed).
- `open Function` is unused (compiled without it). Filed, advisory. `@[expose] public section` also compiles as plain `public section`, but I did not file it because I am unsure maintainers ask for that.
- Section variables `S`, `f` are shadowed by `linearIndepOn_root_baseOf'`. Moving them into `baseOf_pairwise_pairing_le_zero` compiled. Filed.
- `baseOf_pairwise_pairing_le_zero`: the name should spell `pairingIn` and put `pairwise` first; siblings are `pairingIn_le_zero_of_ne` and the like (filed). The docstring is only a citation (filed). The proof itself is fine.
- `linearIndepOn_root_baseOf'`: primed name (filed). The docstring works by contrast and never states the lemma (filed). `have : Fintype ι` should be `letI`; the instance is needed (filed). `;` in `hp` (filed). `by aesop : i ≠ j` can be `fun h ↦ hij (Subtype.ext h)` (filed). Removing `[Module S N] [IsScalarTower S R N]` breaks the build, so those hypotheses are needed. Nothing filed on them.
- `linearIndepOn_root_baseOf`: missing docstring (filed). `have : Fintype` should be `letI` (filed). Redundant `RootPairing.` and `Submodule.` prefixes (filed). `aesop` in `span_mono` can be a term (filed). Tactic-mode basis with `replace this` (filed). `[Module ℚ N]` is needed (removing it breaks the build). `Set.finrank` must keep its prefix.

### Mathlib/LinearAlgebra/RootSystem/IsValuedIn.lean
- `algebraMap_pairingIn'`: primed name next to `algebraMap_pairingIn`. Filed, advisory.
- `pairingIn_rat`: the shortened proof is good, and `[Nontrivial R]` is still needed for `FaithfulSMul ℚ R`. Nothing filed. Its binders `(T) [CommRing T] [Algebra T S] [Algebra T R] [IsScalarTower T S R]` repeat those of `IsValuedIn.trans`, but an instance sits between the two, so they are not consecutive. Not filed.

### Mathlib/LinearAlgebra/RootSystem/RootPositive.lean
- `posForm_apply_root_root_le_zero_iff`: the proof `simp [← not_lt]` also compiles, but the existing one-line `rw` is fine. Not filed. The name is consistent with neighbours (`zero_lt_posForm_apply_root`, `zero_lt_apply_root_root_iff`), and `naming_norm` is inconclusive. Not filed.

## Conventions: where filed, where left

- Namespace grouping / no redundant prefix. Filed: the Indecomposable.lean namespace block, and the `RootPairing.`/`Submodule.` prefixes in `linearIndepOn_root_baseOf`. Left: `IsMulIndecomposable.subset _ _` inside the namespace. It is `protected`, so the qualifier is required.
- Reuse existing variables. Filed: the BaseExists section variables shadowed by `linearIndepOn_root_baseOf'`. Left: the `Submonoid` lemma now uses the file variable `S` (line 25), which is already the preferred form.
- Characterising lemmas for a new def. Filed: `IsMulIndecomposable.mem_baseOf_iff`.
- Name built from the statement's declarations. Filed: `baseOf_pairwise_pairing_le_zero` (`pairing` vs `pairingIn`), `image_baseOf_inv_comp_eq` (`inv` vs `invMonoidHom`), `pairwise_baseOf_div_notMem` (missing `range`).
- Module title states what is proved. Filed: BaseExists. Left: Indecomposable.lean's title, "# Indecomposable elements of monoids" (line 18), which is accurate and unchanged.
- Docstring standalone, not by contrast. Filed: `linearIndepOn_root_baseOf'`.
- No unneeded or redundant imports. Filed: Indecomposable.lean (Subgroup.Lattice, Order.Group.Basic, and the now-implied Monoid.Defs and Submonoid.Basic) and BaseExists (Submodule.Union).
- Shared arguments via `variable`. Filed: the `IsMulIndecomposable` namespace block. Left: `algebraMap_pairingIn'` against `IsValuedIn.trans`, which are not consecutive (an instance sits between them).
- Standard spacing. Filed: `mem_or_inv_mem_closure_baseOf`. A scan of all added lines found no other doubled or trailing spaces.
- Head-first name order. Filed: `baseOf_pairwise_pairing_le_zero` → `pairwise_baseOf_...`.
- Deprecate removed or renamed declarations. Filed: `Submonoid.closure_image_one_lt_and_isMulIndecomposable` (blocking).
- Break lines only past 100 characters. Filed: `pairwise_div_notMem_range`, plus a file-level finding for the other Indecomposable.lean signatures. Left: BaseExists signatures, where each line holds a group that would exceed or come near the limit if joined (e.g. lines 72-76).
- One tactic per line, no `;`. Filed: `hp` in `linearIndepOn_root_baseOf'` and `ext; simp` in `invMonoidHom_comp_invMonoidHom`. Left: the `by_contra hk₂; exact ...` line in the `Submonoid` lemma, which is pre-existing and unchanged by this PR.
- No primes for variants. Filed: `pairwise_div_notMem_range'`, `linearIndepOn_root_baseOf'`, `algebraMap_pairingIn'`.
- Standard module-doc headings. Filed: BaseExists "Implementation details". Left: "## TODO", a widely used Mathlib heading.
- `refine` rather than `apply` with `?_`. Checked `pairwise_div_notMem_range'`, which uses `apply ... fun i ↦ ?_`. It is covered by the finding that removes that lemma, whose replacement uses `refine`. In `linearIndepOn_root_baseOf`, `apply le_antisymm (...) (span_le.mpr ?_)` also uses `apply` with `?_`. I did not file it separately; it could equally be `refine`.
- No lemma that merely instantiates others. Filed: `pairwise_div_notMem_range'`, and `image_baseOf_inv_comp_eq` via the `Subgroup` proof finding.
- Accurate PR title and description. Filed: the description omits the rename and the API additions.
- Lighter tactic instead of grind/aesop. Filed: `IsMulIndecomposable.subset`, `linearIndepOn_root_baseOf'` (`i ≠ j`) and `linearIndepOn_root_baseOf` (`span_mono`). Left: the trailing `aesop` in `image_baseOf_inv_comp_eq` (moot if that lemma is removed), `convert this; aesop` in `linearIndepOn_root_baseOf` (`simp` there fails, so no lighter replacement was verified), and the pre-existing `grind [IsMulIndecomposable]` in the `Submonoid` lemma.
- `let`/`letI` for data. Filed: the `Fintype` haves in both linear-independence lemmas. Left: `have : CharZero R`, which is a Prop.
- Sibling naming patterns. Filed: `pairwise_baseOf_div_notMem` and `baseOf_pairwise_pairing_le_zero`.
- Sorted imports. Filed: Indecomposable.lean. Left: Mathlib.lean (sorted) and BaseExists (sorted: Algebra.Group, Algebra.Module, LinearAlgebra.Dimension, LinearAlgebra.QuadraticForm, LinearAlgebra.RootSystem).
- `rintro` rather than `by_contra` for negations. Filed: `pairwise_div_notMem_range`. Left: `baseOf_pairwise_pairing_le_zero` uses `contrapose!` on a `≤` goal, which is not a negation goal.
- Common step before a case split. Not applicable to anything filed. The two branches of `pairwise_div_notMem_range` run their `simp only` on different goals; the golf finding removes both copies.
- No bare `_eq` suffix. Filed: `image_baseOf_inv_comp_eq`.
