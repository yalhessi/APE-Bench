# PR Review v4 scope-mapping review queue

Release: `0.6.1-scope-map`
Items requiring review: 14

Accept or correct the proposed primary targets. Revision-hunk resolutions are audit-only unless `contributes_to_scope` is true.

## pr33413_i01 (PR #33413)

Status: `unresolved` | Review reasons: `unresolved`

**Ask:** Optionally replace the pair of manually written deprecated aliases for the `to_dual`-generated lemmas with a single use of the `to_dual` attribute that generates both deprecated aliases at once (if compatible with automated deprecated-declaration removal).

**Proposed primary targets:**
- None

**Resolution evidence:**
- `unresolved` / `unresolved` / audit-only: `scope_exception` -> 0 target(s)

**Exceptions:** `no_review_time_source_anchor`, `no_scope_match`

## pr33305_i01 (PR #33305)

Status: `resolved` | Review reasons: `no_direct_source_anchor`

**Ask:** Wrap/split the overly long doc comment line in `Mathlib/GroupTheory/Submonoid/Inverses.lean` (around line 20) so it respects the project's maximum line length.

**Proposed primary targets:**
- `Mathlib/GroupTheory/Submonoid/Inverses.lean`: `module_doc` (`change:10636e03b07ca19727aa2b86d9c7ab7447c4f24b1247a68e34d6579114e188d5`)

**Resolution evidence:**
- `revision_span_overlap` / `inferred` / primary: `Mathlib/GroupTheory/Submonoid/Inverses.lean@1b304bb903` -> 1 target(s)
- `revision_span_overlap` / `inferred` / primary: `Mathlib/GroupTheory/Submonoid/Inverses.lean@68a3bb48b8` -> 1 target(s)

**Exceptions:** `no_review_time_source_anchor`

## pr33302_i01 (PR #33302)

Status: `resolved` | Review reasons: `no_direct_source_anchor`

**Ask:** Change `ShiftedHom` from a `def` to an `abbrev`, and consequently remove the `AddCommGroup` and `Module` instances currently defined on `ShiftedHom` (fixing any ensuing proof breaks, which should mostly become simpler via `dsimp` rather than needing explicit `erw [Iso.homToEquiv_apply]`).

**Proposed primary targets:**
- `Mathlib/CategoryTheory/Shift/ShiftedHom.lean`: `section` (`change:0713efa0d54c4cc5ad4ce983170587edb74f3622cfaf95cab75e0d9745ac194c`)
- `Mathlib/CategoryTheory/Shift/ShiftedHom.lean`: `section` (`change:3a30b3566ec76bb1e5174d5ac1b754a0be79102c49eaa77adbb141982d902ac9`)
- `Mathlib/CategoryTheory/Shift/ShiftedHom.lean`: `CategoryTheory.ShiftedHom.map_zero` (`change:3bdd070f6d2a705c80d754a2225bd9a22db21571cb5851f98e80e94644d58143`)
- `Mathlib/CategoryTheory/Shift/ShiftedHom.lean`: `CategoryTheory.ShiftedHom.map_add` (`change:b6705451767012b24e95b6df22106f3fdcbf71a89a824c85cb63060e11af43f8`)
- `Mathlib/CategoryTheory/Shift/ShiftedHom.lean`: `section` (`change:d22a0dc621cdf8445a1989a49b238bca162a8f293846c22db221758e98bce9ed`)

**Resolution evidence:**
- `unresolved` / `inferred` / audit-only: `Mathlib/CategoryTheory/Shift/ShiftedHom.lean@e0c9e59adc` -> 0 target(s)
- `unresolved` / `inferred` / audit-only: `Mathlib/CategoryTheory/Shift/ShiftedHom.lean@efe2041551` -> 0 target(s)
- `revision_span_overlap` / `inferred` / primary: `Mathlib/CategoryTheory/Shift/ShiftedHom.lean@13928aa227` -> 5 target(s)

**Exceptions:** `no_review_time_source_anchor`, `revision_anchor_unmapped`

## pr33296_i01 (PR #33296)

Status: `resolved` | Review reasons: `no_direct_source_anchor`

**Ask:** Replace the lemma `Module.End.exists_apply_eq_smul` (which assumes `hf : f ∈ Subsemiring.center (End R M)`) with a more general “mem_center_iff” characterization for `Set.center (End R M)` and then derive specialized iff-lemmas for `Submonoid.center`, `Subsemigroup.center`, `Subsemiring.center`, and `Subalgebra.center`; additionally, strengthen `Mathlib/Algebra/Central/End.lean`’s imports by adding `Mathlib.Algebra.Central.Basic`.

**Proposed primary targets:**
- `Mathlib/Algebra/Central/End.lean`: `Module.End.exists_apply_eq_smul` (`change:aa1c85317e13692918f1e48f1e4e85533bd2bc848fed4624f6f3fe254a6447c3`)

**Resolution evidence:**
- `identifier_exact` / `exact` / primary: `Module.End.exists_apply_eq_smul` -> 1 target(s)

**Exceptions:** `no_review_time_source_anchor`

## pr33200_i01 (PR #33200)

Status: `not_judgeable` | Review reasons: `broad_scope_over_10_targets`

**Ask:** Do not merge this PR as-is: remove the introduced axioms and all `sorry`s (i.e. supply full proofs) and drastically reduce/split the contribution into reviewable pieces written in Mathlib style; otherwise close/withdraw the PR.

**Proposed primary targets:**
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `sobolev_embedding` (`change:032ebf237e9004f8f351fdc3cd6478c5a1fa1515bc0fd2cd86e2afe54f90b245`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `fourier_inversion` (`change:083220bad34985c1bddc6913c091f37842d445af88cb140ca88ab74115ee0e0f`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `parseval_orthonormal` (`change:2300d607945251c1f1a6340ea2e8bb20590b06ccd00900e128b11fa90c7f92c9`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cMoser` (`change:2648f0e7f7139bfc06d6bde9deca922ff824148c20f5db9a6dfa59380e51f6e7`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `fubini_torus3` (`change:3c7dfcc095aed75602100b3b2d158088eac379f3bff2955ca1e45857867e7752`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `hs_gronwall_bound` (`change:4b1c3f72fef67b167bf1d4d4225dde20c8f03203dad991aba5524b22e074015a`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `fourier_ortho_integral` (`change:542f48f383f3215b9b5b42a88cf01e86f64c51d91b31cb8a6d00966b367fc961`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `smooth_initial_hs_finite` (`change:5dbebc4de40fde8ada20ee15600fbc55e020905c27fa2076b618a1c5791737bb`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `fourierCoeff_summable` (`change:625655419c4863753cfbd6d20588b1172e5a6da009f807f7c13bdc323f2d6e6e`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cSobolev` (`change:6b39b5ddc64a93fa5b4c3e6161538f4228ba2885793b9f680ae79acf9f3006a3`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cMoser_pos` (`change:7be0ecaf33ef7d3512fcf01737e3f5a0a37b5955429785516f3222ef39276675`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `moser_estimate` (`change:7eebf4be21ed0ca4641f93eb17f0afb1841a13bd19b5e8b2cfa30c8a08a6b040`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `vorticity_integrable` (`change:82fb3f974be0895ba839da3132175af5733ca9b4ed325fac88a86b4dc74b78f0`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cGronwall` (`change:856d994230f120bacf7145f3be595ce0690127a7a45f4848fdcf99ea6db2774e`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `integral_le_const_mul_length` (`change:8a93d1917c29ecf7300cd3fa50887b99960638ca2b0824832bf336b7163fa56f`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `bkm_implies_regularity` (`change:9367d435d213da321c5168ed693d5e505ff59300e51b9fdae33bf6f59a2e7332`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `vorticity_hs_bound` (`change:e79904be928faffbdbfd9dd36c57c27e5662dabb9b65b6267ea19401b6caa9d5`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cGronwall_pos` (`change:f20e1525f661f09656c498c392cb3d0d4690581df95b7084509642a8828627b5`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cSobolev_pos` (`change:f278625b1d9105c9f5059c117fdf554f6a9cc1593454869d294026f996a194a7`)

**Resolution evidence:**
- `axiom_declaration_kind` / `exact` / primary: `axiom` -> 19 target(s)

**Exceptions:** `no_review_time_source_anchor`

## pr33156_i01 (PR #33156)

Status: `unresolved` | Review reasons: `unresolved`

**Ask:** Add the missing doc-string for the newly introduced `optAttrArg` syntax in `Mathlib/Util/AddRelatedDecl.lean`.

**Proposed primary targets:**
- None

**Resolution evidence:**
- `unresolved` / `unresolved` / audit-only: `scope_exception` -> 0 target(s)

**Exceptions:** `no_review_time_source_anchor`, `no_scope_match`

## pr33152_i01 (PR #33152)

Status: `resolved` | Review reasons: `no_direct_source_anchor`

**Ask:** Remove the new lemma `Meromorphic.meromorphicOn_univ`; instead use the existing lemma `Meromorphic.meromorphicOn` (supplying `s := Set.univ` explicitly when needed), rather than adding a dedicated `univ` specialization (and do not add it unprotected).

**Proposed primary targets:**
- `Mathlib/Analysis/Meromorphic/Basic.lean`: `Meromorphic.meromorphicOn_univ` (`change:1e9a6f14531aa03c86e75b049a41861f7d2ad8f531a16d1b581fba23c5a0f350`)

**Resolution evidence:**
- `identifier_exact` / `exact` / primary: `Meromorphic.meromorphicOn_univ` -> 1 target(s)
- `revision_span_overlap` / `inferred` / audit-only: `Mathlib/Analysis/Meromorphic/Basic.lean@6ae67fe4c3` -> 1 target(s)

**Exceptions:** `no_review_time_source_anchor`

## pr33151_i01 (PR #33151)

Status: `resolved` | Review reasons: `no_direct_source_anchor`

**Ask:** Update `Mathlib/Tactic/Translate/ToDual.lean`’s `GuessName.abbreviationDict` (or equivalently `fixAbbreviations`) to map the unwanted dual-name pieces so that `to_dual` produces `SuccLimit`/`PredLimit` rather than `succColimit`/`predColimit` (i.e. add abbreviation entries translating `succColimit → SuccLimit` and `predColimit → PredLimit`, and use the dictionary to ‘un-translate’ `colimit` back to `limit` in these succ/pred contexts).

**Proposed primary targets:**
- `Mathlib/Tactic/Translate/ToDual.lean`: `Mathlib.Tactic.ToDual.nameDict` (`change:d468a1792b9738ba71f837a8b69728ca900eae72558e70517c29fa8382269108`)

**Resolution evidence:**
- `revision_span_overlap` / `inferred` / primary: `Mathlib/Tactic/Translate/ToDual.lean@9ab100f08d` -> 1 target(s)

**Exceptions:** `no_review_time_source_anchor`

## pr33149_i01 (PR #33149)

Status: `resolved` | Review reasons: `broad_scope_over_10_targets`

**Ask:** Remove the newly introduced `axiom` declarations (and any reliance on them), replacing them with proved lemmas or existing Mathlib results so the file adds no new axioms.

**Proposed primary targets:**
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `bkm_implies_regularity` (`change:0ab9322b7c6e2e8d70e5f82823ed023bc04ef84caeb56f9cf568a1c6a6828e01`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cSobolev_pos` (`change:1208e7f5b853f2b5c83fdaaef78d9849975f75ff4f0508af79989217331d80c5`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `fourier_ortho_integral` (`change:43caf038a1851cf4e0825b67eaa30f8cf5288396a96935dbddd4ac4f61e52f32`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `vorticity_hs_bound` (`change:567e8713e1fab0587a9bf74b29759b992e4f968347b36a15521bd77e331ceb19`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cSobolev` (`change:56b96be8d6d94634a3c570cd12fbefb3897dea940572d3d0a532c8d55e4f64a7`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cMoser` (`change:58660f102e532d4cd249b1a6093bfcf7a95370e719021a3d9dfdf999957e3774`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `fourierCoeff_summable` (`change:5f8b0c67d6184a05baf57dfec137a26020872adb53afa66bff42d8ae6bee0e35`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `hs_gronwall_bound` (`change:61ed160f65ee4cd325864e9c2cd049a8de8659c7b105df8e64355ff4d2553128`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `smooth_initial_hs_finite` (`change:751880a545f03ce6785eeb95139957a7782c27a2eca900774250bbce1f9ec698`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cGronwall_pos` (`change:83ea1c981cd1cc1080ec8ecdf0a52f1504cf4655d89a9c4d03c7131f88493202`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cMoser_pos` (`change:960d382089ec7ab37f97e7ec049fa4deebddef68465d86f913a33c5d5f407014`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `fubini_torus3` (`change:9791fc8dddcbf6ccdf86350963b1c4b98a7dafc13e52b5bce288bd919ea790c0`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `moser_estimate` (`change:a739a981dc37d945c2fd6f063d658ab3c5e74c2743173c348826d55558cec9b5`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `parseval_orthonormal` (`change:a85efd34ab923c26c3c915a83e1ac618a07c1db876a4474a152390dcc88c5b0e`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `sobolev_embedding` (`change:e4590fbb0d46e61d193c3d8d3fc4be70d15225706b2d09ef791971575008e9c6`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `integral_le_const_mul_length` (`change:e68da314bed3b4c75e8f4c15531319492cf7e9075225b61bea938ea2f78a58c2`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `vorticity_integrable` (`change:ed973f3bfd357fce58a627f9c745c29a547273155d0ac8d5bbe57cf26ec4d103`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `fourier_inversion` (`change:fd27a90a726d1651073481b175e87821bd68cb5b87b3e4d58839e8ef612889cb`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cGronwall` (`change:fece1fe682dcae34a3edb347fe8915a17a1adc2887a40b9d246c95806deee883`)

**Resolution evidence:**
- `review_line_entity` / `exact` / primary: `rc_2637723625` -> 1 target(s)
- `axiom_declaration_kind` / `exact` / primary: `axiom` -> 19 target(s)

## pr33149_i03 (PR #33149)

Status: `resolved` | Review reasons: `no_direct_source_anchor`, `broad_scope_over_10_targets`

**Ask:** Remove the newly introduced axioms (e.g. `cMoser`, `cGronwall`, `cSobolev`, `fourier_ortho_integral`, `fubini_torus3`, etc.) and replace them with actual definitions/lemmas proved from existing mathlib results; when introducing new definitions/structures, also add basic supporting lemmas so the additions are maintainable.

**Proposed primary targets:**
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `bkm_implies_regularity` (`change:0ab9322b7c6e2e8d70e5f82823ed023bc04ef84caeb56f9cf568a1c6a6828e01`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cSobolev_pos` (`change:1208e7f5b853f2b5c83fdaaef78d9849975f75ff4f0508af79989217331d80c5`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `fourier_ortho_integral` (`change:43caf038a1851cf4e0825b67eaa30f8cf5288396a96935dbddd4ac4f61e52f32`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `vorticity_hs_bound` (`change:567e8713e1fab0587a9bf74b29759b992e4f968347b36a15521bd77e331ceb19`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cSobolev` (`change:56b96be8d6d94634a3c570cd12fbefb3897dea940572d3d0a532c8d55e4f64a7`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cMoser` (`change:58660f102e532d4cd249b1a6093bfcf7a95370e719021a3d9dfdf999957e3774`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `fourierCoeff_summable` (`change:5f8b0c67d6184a05baf57dfec137a26020872adb53afa66bff42d8ae6bee0e35`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `hs_gronwall_bound` (`change:61ed160f65ee4cd325864e9c2cd049a8de8659c7b105df8e64355ff4d2553128`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `smooth_initial_hs_finite` (`change:751880a545f03ce6785eeb95139957a7782c27a2eca900774250bbce1f9ec698`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cGronwall_pos` (`change:83ea1c981cd1cc1080ec8ecdf0a52f1504cf4655d89a9c4d03c7131f88493202`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cMoser_pos` (`change:960d382089ec7ab37f97e7ec049fa4deebddef68465d86f913a33c5d5f407014`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `fubini_torus3` (`change:9791fc8dddcbf6ccdf86350963b1c4b98a7dafc13e52b5bce288bd919ea790c0`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `moser_estimate` (`change:a739a981dc37d945c2fd6f063d658ab3c5e74c2743173c348826d55558cec9b5`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `parseval_orthonormal` (`change:a85efd34ab923c26c3c915a83e1ac618a07c1db876a4474a152390dcc88c5b0e`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `sobolev_embedding` (`change:e4590fbb0d46e61d193c3d8d3fc4be70d15225706b2d09ef791971575008e9c6`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `integral_le_const_mul_length` (`change:e68da314bed3b4c75e8f4c15531319492cf7e9075225b61bea938ea2f78a58c2`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `vorticity_integrable` (`change:ed973f3bfd357fce58a627f9c745c29a547273155d0ac8d5bbe57cf26ec4d103`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `fourier_inversion` (`change:fd27a90a726d1651073481b175e87821bd68cb5b87b3e4d58839e8ef612889cb`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cGronwall` (`change:fece1fe682dcae34a3edb347fe8915a17a1adc2887a40b9d246c95806deee883`)

**Resolution evidence:**
- `identifier_exact` / `exact` / primary: `cMoser` -> 1 target(s)
- `identifier_exact` / `exact` / primary: `cGronwall` -> 1 target(s)
- `identifier_exact` / `exact` / primary: `cSobolev` -> 1 target(s)
- `identifier_exact` / `exact` / primary: `fourier_ortho_integral` -> 1 target(s)
- `identifier_exact` / `exact` / primary: `fubini_torus3` -> 1 target(s)
- `axiom_declaration_kind` / `exact` / primary: `axiom` -> 19 target(s)

**Exceptions:** `no_review_time_source_anchor`

## pr33149_i04 (PR #33149)

Status: `not_judgeable` | Review reasons: `broad_scope_over_10_targets`

**Ask:** Rewrite the file to meet mathlib standards by (1) eliminating all `axiom`s (replace with actual definitions/lemmas derived from Mathlib, or mark gaps with `sorry` during development), (2) removing/ inlining local wrapper definitions that merely rename existing Mathlib notions (optionally keep as `abbrev` only if truly needed), and (3) fixing definitions like `fourierDecay` and `spectralNSResidual` (and anything depending on them such as `SolvesNavierStokes`) so they are not vacuously true.

**Proposed primary targets:**
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `bkm_implies_regularity` (`change:0ab9322b7c6e2e8d70e5f82823ed023bc04ef84caeb56f9cf568a1c6a6828e01`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cSobolev_pos` (`change:1208e7f5b853f2b5c83fdaaef78d9849975f75ff4f0508af79989217331d80c5`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `fourierDecay` (`change:14d670db44d54eb378f34d69ff9e2d46979a296ea175846aaec471effbe01f2a`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `SolvesNavierStokes` (`change:39f2ffb5fb009d5e3602e9e208a0e750781775646705b04da06085f9acb193e4`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `fourier_ortho_integral` (`change:43caf038a1851cf4e0825b67eaa30f8cf5288396a96935dbddd4ac4f61e52f32`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `vorticity_hs_bound` (`change:567e8713e1fab0587a9bf74b29759b992e4f968347b36a15521bd77e331ceb19`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cSobolev` (`change:56b96be8d6d94634a3c570cd12fbefb3897dea940572d3d0a532c8d55e4f64a7`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cMoser` (`change:58660f102e532d4cd249b1a6093bfcf7a95370e719021a3d9dfdf999957e3774`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `fourierCoeff_summable` (`change:5f8b0c67d6184a05baf57dfec137a26020872adb53afa66bff42d8ae6bee0e35`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `hs_gronwall_bound` (`change:61ed160f65ee4cd325864e9c2cd049a8de8659c7b105df8e64355ff4d2553128`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `smooth_initial_hs_finite` (`change:751880a545f03ce6785eeb95139957a7782c27a2eca900774250bbce1f9ec698`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cGronwall_pos` (`change:83ea1c981cd1cc1080ec8ecdf0a52f1504cf4655d89a9c4d03c7131f88493202`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cMoser_pos` (`change:960d382089ec7ab37f97e7ec049fa4deebddef68465d86f913a33c5d5f407014`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `fubini_torus3` (`change:9791fc8dddcbf6ccdf86350963b1c4b98a7dafc13e52b5bce288bd919ea790c0`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `spectralNSResidual` (`change:a43e79cc5be00cf825f20b473f05a278f9c4dcd36ade0d78f1bf7bdbf7db13e1`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `moser_estimate` (`change:a739a981dc37d945c2fd6f063d658ab3c5e74c2743173c348826d55558cec9b5`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `parseval_orthonormal` (`change:a85efd34ab923c26c3c915a83e1ac618a07c1db876a4474a152390dcc88c5b0e`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `sobolev_embedding` (`change:e4590fbb0d46e61d193c3d8d3fc4be70d15225706b2d09ef791971575008e9c6`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `integral_le_const_mul_length` (`change:e68da314bed3b4c75e8f4c15531319492cf7e9075225b61bea938ea2f78a58c2`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `vorticity_integrable` (`change:ed973f3bfd357fce58a627f9c745c29a547273155d0ac8d5bbe57cf26ec4d103`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `fourier_inversion` (`change:fd27a90a726d1651073481b175e87821bd68cb5b87b3e4d58839e8ef612889cb`)
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cGronwall` (`change:fece1fe682dcae34a3edb347fe8915a17a1adc2887a40b9d246c95806deee883`)

**Resolution evidence:**
- `identifier_exact` / `exact` / primary: `fourierDecay` -> 1 target(s)
- `identifier_exact` / `exact` / primary: `spectralNSResidual` -> 1 target(s)
- `identifier_exact` / `exact` / primary: `SolvesNavierStokes` -> 1 target(s)
- `axiom_declaration_kind` / `exact` / primary: `axiom` -> 19 target(s)

**Exceptions:** `no_review_time_source_anchor`

## pr33145_i05 (PR #33145)

Status: `unresolved` | Review reasons: `unresolved`

**Ask:** Swap the sides of the `iSup`/`iInf` equalities so they are stated with the dense-set supremum/infimum on the left and the universe/index supremum/infimum on the right, e.g. change `⨆ i, f i = ⨆ s : S, f s` to `⨆ s : S, f s = ⨆ i, f i` (and similarly for `iInf`).

**Proposed primary targets:**
- None

**Resolution evidence:**
- `unresolved` / `unresolved` / audit-only: `scope_exception` -> 0 target(s)

**Exceptions:** `no_review_time_source_anchor`, `no_scope_match`

## pr33144_i01 (PR #33144)

Status: `resolved` | Review reasons: `no_direct_source_anchor`

**Ask:** Remove the redundant eta-expanded `fun_` lemmas `fun_deriv` and `fun_iterated_deriv` (both in the `MeromorphicAt` section and the `MeromorphicOn` section), keeping only the non-eta-expanded `deriv`/`iterated_deriv` lemmas.

**Proposed primary targets:**
- `Mathlib/Analysis/Meromorphic/Basic.lean`: `MeromorphicAt.fun_deriv` (`change:405ee0bff33b652bbae64e8a0505a8701f6df3c8f5150eb2b60cf2096905f273`)
- `Mathlib/Analysis/Meromorphic/Basic.lean`: `MeromorphicOn.fun_deriv` (`change:5357e0b10c5cac2a6e88d373ac1cca50f15a07a68c996e9c66ab873ce46d3f47`)
- `Mathlib/Analysis/Meromorphic/Basic.lean`: `MeromorphicOn.iterated_deriv` (`change:8fb9ec21fde7d8eeceb3154a63c02875f1f0a7ff72bd455578ba325a6c2fb1de`)
- `Mathlib/Analysis/Meromorphic/Basic.lean`: `MeromorphicOn.deriv` (`change:b8b23fcd905feee03da4627e6358a8af767aabe676937c3999037c2fa9b9b0fe`)
- `Mathlib/Analysis/Meromorphic/Basic.lean`: `MeromorphicAt.fun_iterated_deriv` (`change:c0032690f2bb426bddf46fc8403be8732c424100ff471732b8443007e6e767b4`)
- `Mathlib/Analysis/Meromorphic/Basic.lean`: `MeromorphicOn.fun_iterated_deriv` (`change:f1cf3894a773effcdc69ac6301d2f279543c96fd9f16613ce881b32b471c795c`)

**Resolution evidence:**
- `identifier_exact` / `exact` / primary: `fun_deriv` -> 2 target(s)
- `identifier_exact` / `exact` / primary: `fun_iterated_deriv` -> 2 target(s)
- `identifier_exact` / `exact` / primary: `deriv` -> 1 target(s)
- `identifier_exact` / `exact` / primary: `iterated_deriv` -> 1 target(s)

**Exceptions:** `no_review_time_source_anchor`

## pr33117_i01 (PR #33117)

Status: `resolved` | Review reasons: `broad_scope_over_10_targets`

**Ask:** Import `Mathlib.Tactic.ToFun` and replace the duplicated `fun_*` lemmas for `Meromorphic` closure properties with `@[to_fun (attr := fun_prop)]` on the main lemmas (`neg`, `add`, `sum`, `sub`, `mul`, `prod`, `div`, `pow`, `zpow`, `deriv`, `iterated_deriv`) so the corresponding `fun x ↦ …` versions are generated automatically.

**Proposed primary targets:**
- `Mathlib/Analysis/Meromorphic/Basic.lean`: `Meromorphic.add` (`change:074bbf8ee0d604ed222901e30dac293f6adad88ad81721ff3de153d0a1e622dd`)
- `Mathlib/Analysis/Meromorphic/Basic.lean`: `Meromorphic` (`change:367ff6247f11a3116973efa77f6b27a34a90f18bd5790623f4f8552ddc4b44c5`)
- `Mathlib/Analysis/Meromorphic/Basic.lean`: `Meromorphic.sub` (`change:798155ff7486aaeeeacb387fb24678655c77d4ade4ab9a3d80f748aa833fe1fa`)
- `Mathlib/Analysis/Meromorphic/Basic.lean`: `Meromorphic.prod` (`change:8e0dd32c0ca2ff78860a874d38ec6592d8d860a9c92957904311bc29938cf954`)
- `Mathlib/Analysis/Meromorphic/Basic.lean`: `Meromorphic.div` (`change:a049f464ffc45da9e7922882169c13dcb12c228bf17098c97856a15ff5f49458`)
- `Mathlib/Analysis/Meromorphic/Basic.lean`: `Meromorphic.deriv` (`change:c5261da73e1d66bde6a7d143bc813b102a019d232c3a3027c8fdc35ba2c29b5f`)
- `Mathlib/Analysis/Meromorphic/Basic.lean`: `Meromorphic.iterated_deriv` (`change:ce54ffd2aef431d179595d292574401f08815891e2f84eb250298f38236426e3`)
- `Mathlib/Analysis/Meromorphic/Basic.lean`: `Meromorphic.fun_iterated_deriv` (`change:d690004f266a8a8bed47f77c81d78df10075fee0ca1dc962e1d96e4cf6fc14e9`)
- `Mathlib/Analysis/Meromorphic/Basic.lean`: `Meromorphic.sum` (`change:d832d4481757c38effadc22080f0b5736799278f7daf1696a4ec8380cd731b67`)
- `Mathlib/Analysis/Meromorphic/Basic.lean`: `Meromorphic.neg` (`change:e747d454a048ce3fd402130e66ce78f4039ebdad5d7e49c345be272dc4f2e71e`)
- `Mathlib/Analysis/Meromorphic/Basic.lean`: `Meromorphic.pow` (`change:e80cfef275485b461e7fba0e29b7a34d8a3a5b4e809cd54e1254b52ac016b694`)
- `Mathlib/Analysis/Meromorphic/Basic.lean`: `Meromorphic.mul` (`change:e8d42a00f11f0d913c6a323dada709d79e2f10aca367686f1ae13049147e9ae4`)
- `Mathlib/Analysis/Meromorphic/Basic.lean`: `Meromorphic.zpow` (`change:ebf51d6bd9e1c5148b63898738cf8e6a30814b8a440f297862789dd5fd2c67f3`)

**Resolution evidence:**
- `review_line_entity` / `exact` / primary: `rc_2636917003` -> 1 target(s)
- `identifier_exact` / `exact` / primary: `Meromorphic` -> 1 target(s)
- `identifier_exact` / `exact` / primary: `neg` -> 1 target(s)
- `identifier_exact` / `exact` / primary: `add` -> 1 target(s)
- `identifier_exact` / `exact` / primary: `sum` -> 1 target(s)
- `identifier_exact` / `exact` / primary: `sub` -> 1 target(s)
- `identifier_exact` / `exact` / primary: `mul` -> 1 target(s)
- `identifier_exact` / `exact` / primary: `prod` -> 1 target(s)
- `identifier_exact` / `exact` / primary: `div` -> 1 target(s)
- `identifier_exact` / `exact` / primary: `pow` -> 1 target(s)
- `identifier_exact` / `exact` / primary: `zpow` -> 1 target(s)
- `identifier_exact` / `exact` / primary: `deriv` -> 1 target(s)
- `identifier_exact` / `exact` / primary: `iterated_deriv` -> 1 target(s)
- `revision_span_overlap` / `overlap` / audit-only: `Mathlib/Analysis/Meromorphic/Basic.lean@30bed5185d` -> 30 target(s)
- `unresolved` / `inferred` / audit-only: `Mathlib/Analysis/Meromorphic/Basic.lean@b9bb4bcc0a` -> 0 target(s)

**Exceptions:** `revision_anchor_too_broad`, `revision_anchor_unmapped`
