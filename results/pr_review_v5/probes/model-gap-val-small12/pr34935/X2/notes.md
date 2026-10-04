# Review notes: PR #34935 (Semiring structure on ideal sheaves)

I read pr.md, model.md and diff.patch. I read the PR's version of IdealSheaf/Basic.lean (lines
1-640) and of Scheme.lean (the ZeroLocus section) with `file_read`. As a baseline,
`lean_verify_edit` with no edit reports that Basic.lean compiles as the PR leaves it, with no
warnings.

## Scheme.lean
- `zeroLocus_setMul`: the statement is right and the proof is short. The `setMul` spelling for
  pointwise set products has precedent (`toAdd_image_setMul`). There is no duplicate in RingedSpace
  or Scheme: content_search finds `zeroLocus_mul` lemmas only in PrimeSpectrum and
  ProjectiveSpectrum, and those are the ideal versions. No finding.
- `zeroLocus_mul`: it matches `PrimeSpectrum.zeroLocus_mul` in name and shape. The proof needs
  `open scoped Pointwise` for `↑I * ↑J`. No finding.

## IdealSheaf/Basic.lean
- `mem_supportSet_iff_mem_support` (simp, `.rfl`): it points simp from `supportSet` to `support`,
  as the `supportSet` field docstring recommends. The `Mul` instance's `simp` call relies on it.
  No finding.
- `variable (I J K ...)`: `I` is already a namespace-level variable (line 204). Dropping it
  compiles. **Finding (advisory, style).**
- `Zero`/`One`/`Add` instances: fine, and they follow the Submodule pattern.
- `Mul` and `Pow` instances: correct, and support is handled through `mkOfMemSupportIff`.
  The `by` blocks sit at the same indentation as the continuation line. I considered this as a
  formatting nit and did not submit it.
- `ideal_mul`, `ideal_pow`, `support_mul`, `support_pow_succ` (rfl, simp), `support_pow`
  (with `hn`): consistent. No finding.
- `top_mul`, `mul_top`, `bot_mul`, `mul_bot`: match the `Ideal` names. No finding.
- `mul_inf`, `inf_mul`: both state distributivity over `⊔`, so they are misnamed. `Ideal.mul_sup`
  and `Ideal.sup_mul` have the same statements. The rename to `mul_sup`/`sup_mul`, with the
  instance fields updated, compiles. **Two findings (blocking, naming).**
- `IdemCommSemiring` instance: I checked whether `nsmul := nsmulRec` can be dropped. It cannot:
  removing it gives the error "Fields missing: nsmul". The rest is fine. No finding.
- `IsOrderedRing ... where` (empty): this is the same pattern as `IsOrderedRing (Submodule R A)`
  in Algebra/Algebra/Operations.lean. Kleene.lean has no generic
  `IdemSemiring -> IsOrderedRing` instance, so the declaration is not redundant. No finding.
- `zero_eq_bot`, `one_eq_top`, `add_eq_sup` and the `/-! ... -/` comment: these match
  `Ideal.zero_eq_bot` / `one_eq_top` / `add_eq_sup` in Ideal/Operations.lean. No finding.
- `equivOfIsAffine` (`≃o` becomes `≃+*o`, `@[simps]` removed): I tried
  `@[simps! apply symm_apply]`. It fails because OrderRingIso has no `apply` simps projection
  (no `initialize_simps_projections OrderRingIso`). So the hand-written
  `equivOfIsAffine_apply`/`_symm_apply` lemmas are justified, and they keep the names and
  statements `@[simps]` used to generate. The docstring and the module header still say
  "bijection". **Finding (advisory, documentation).**
- `equivOfIsAffine_apply`, `equivOfIsAffine_symm_apply`: correct, rfl. No finding.
- `radical_inf`: the change only drops redundant parentheses. No finding.
- `radical_mul`: matches `Ideal.radical_mul`, and the proof style matches its sibling
  `radical_inf`. No finding.

## Tools used
file_read, file_search, content_search (Ideal/Operations, Kleene, Algebra/Operations,
Order/Hom/Ring, zeroLocus lemmas), declaration_search, naming_norm (it measures prefixes only, so
it was inconclusive for the inf/sup suffix), precedent_search (nothing relevant), zulip_search
(nothing relevant), and lean_verify_edit (baseline, rename, nsmul removal, simps attempt,
variable change, docstring).
