# Review notes: PR #36822, "feat(Order/Interval/Set/Disjoint): use `to_dual`"

## What I did

I read `pr.md`, `model.md` and `diff.patch`. I read both changed files as the PR leaves them (`file_read`), and compiled each file as it stands; both compile with no warnings.

I then ran `lean_verify_edit` probes. Their scratch inputs and outputs are in `tmp/`.

1. **Are the explicit names needed?** I removed every explicit `to_dual` name in both files and checked whether the old names still resolve.
   - They do not: `to_dual` translates `disjoint` to `codisjoint`, and it does not swap `right` and `left`.
   - Without explicit names, `iUnion_Ioc_right` would generate `iUnion_Ico_right`, which collides with an existing lemma.
   - So every explicit name in the PR is necessary. This agrees with the `linter.translateGenerateName` linter, which fires on my edits but not on the PR's file.
2. **Do the generated statements match the old ones?** I wrote positional `example`s for every removed name, in both files, using the removed statements verbatim. All compile, so nothing is lost by name or by statement, and no deprecations are needed.
3. **Did the PR change the simp set?** `by simp` on `Disjoint (Ioi a) (Iio a)`, on `Disjoint (Iio a) (Ioi a)`, and on the two `DenselyOrdered` iff statements fails in the PR state ("simp made no progress"). It succeeds once `(attr := simp)` is restored. Findings 1 and 2.
4. **Can `to_dual` replace the remaining hand-written duals in the file?**
   - It works for the iUnion/biUnion `_self_iff` pair (finding 3) and for the four `IsGLB`/`IsLUB` lemmas (finding 4).
   - It fails for `Ico_disjoint_Ico`/`Ioc_disjoint_Ioc`, because `Ico_inter_Ico` has no `to_dual`.
   - It fails for `iUnion_Ici_eq_Ioi_iInf` and `iUnion_Ici_eq_Ici_iInf`, because `isGLB_iInf` has no `to_dual`.
5. **Can the lemmas with no dual get one?** `to_dual` works for `Iic_disjoint_Ioc`, `Ioc_disjoint_Ioi` and `Ioc_disjoint_Ioi_same`, and `declaration_search` shows their duals do not exist yet (finding 5).
6. **Which lemmas are new?** `declaration_search` shows `Set.Ici_disjoint_Iio` and `Set.Ioi_disjoint_Iic` did not exist before the PR. So the PR adds two conditional simp lemmas (finding 6) and two new API lemmas that its title does not mention (finding 7).
7. **Precedents.** `precedent_search` on the to_dual code returned nothing that bears on this PR.

## Object by object

- `Filter.disjoint_atBot_principal_Ioi`, `disjoint_atTop_principal_Iic`, `disjoint_pure_atTop`, `disjoint_atBot_atTop`:
  - The `to_dual` names are needed, since the generated names would say `codisjoint`.
  - The generated duals have exactly the old statements (checked by example), and no attributes were lost (there were none).
  - Nothing to ask.
  - A possible golf: `(Iic_disjoint_Ioi le_rfl).symm` could become the new `Ioi_disjoint_Iic le_rfl`. I did not file it, because that proof line is untouched.
- `Set.Iic_disjoint_Ioi`, `Set.Iio_disjoint_Ici`: `(attr := simp)` is correct. Each now also generates a new conditional simp lemma (finding 6).
- `Set.Ici_disjoint_Iic`: generates `Iic_disjoint_Ici` with the old statement, and simp is kept. Fine.
- `Set.Ioi_disjoint_Iio_of_not_lt`, `Set.Ioi_disjoint_Iio_of_le`:
  - They were not simp before, and are not now.
  - The explicit names are needed (the generated ones would say `codisjoint`/`gt`/`ge`).
  - The old positional statements check out. One small change: the roles of the implicit `a`/`b` in the generated lemmas differ from the old hand-written ones. That only matters for named-argument calls, so I did not file it.
- `Set.Ioi_disjoint_Iio_same`: simp dropped (finding 1).
- `Set.Ioi_disjoint_Iio_iff`: simp dropped (finding 2).
- `Set.iUnion_Iic`, `Set.iUnion_Iio`: there are no explicit names, and the generated `iUnion_Ici`/`iUnion_Ioi` resolve. Fine.
- `Set.iUnion_Icc_right`, `iUnion_Ioc_right`, `iUnion_Ico_right`, `iUnion_Ioo_right`: the explicit `_left` names are needed (`right` is not translated). The old `_left` statements check out, and simp is kept. Fine.
- Untouched lemmas in the same file:
  - The LinearOrder `_self_iff` pairs: finding 3.
  - The `UnionIxx` IsGLB/IsLUB pairs: finding 4.
  - The Preorder lemmas with no dual: finding 5.

## Message: conventions, with places filed and places left

- **simp on lemmas with a simpler RHS.** Every changed lemma that was simp keeps an LHS/RHS shape for which simp is right. Filed where simp was lost: findings 1 and 2.
- **Dual statement accompanies an order lemma.** Filed: finding 5 (`Iic_disjoint_Ioc`, `Ioc_disjoint_Ioi`, `Ioc_disjoint_Ioi_same`).
  - Left `Ioc_disjoint_Ioc_of_le` and `Ico_disjoint_Ico_same`: their `to_dual` images put the intervals in mirrored order (`Disjoint (Ioc b a) (Ioc c b)`), which is not a statement worth naming.
- **`fun ... ↦`, not `=>`.** Left. The `=>` lambdas in `Iic_disjoint_Ioi`, `Iio_disjoint_Ici`, `iUnion_Iic` and `Ico_disjoint_Ico_same` are on proof lines the PR does not change (diff context only). Rewriting them would go against the convention that a PR changes only what its purpose needs.
- **Names in head-first order.** Left. Every new name lists its sets in statement order, and `of_le`/`of_not_lt` match their hypotheses. Checked by reading the names against the generated statements.
- **Deprecate removed or moved declarations.** Left. No name disappears: every removed name is regenerated by `to_dual` with its old statement, which I checked with positional examples in both files.
- **Attribute applied to some siblings but not others.**
  - Filed: findings 3, 4 and 5, which cover the remaining hand-written duals in the file.
  - Finding 4 also asks for a comment on the pairs that cannot be converted (`isGLB_iInf` and `Ico_inter_Ico` lack `to_dual`; both verified by a failing compile).
- **Attributes kept exactly when moved or deduplicated.** Filed: findings 1 and 2. Left: every other lemma, where the before and after attributes match (`(attr := simp)` wherever simp was before, nothing where nothing was).
- **Attribute on its own line for multi-line headers.** Left: every `@[to_dual ...]` sits on its own line in the diff.
- **Variant extended to all members of a family.** Filed through findings 3, 4 and 5.
- **Equation in one direction only; use `.symm`.** Left. `disjoint_atTop_atBot` and `Iic_disjoint_Ici` are pre-existing symmetric twins, now generated by `to_dual` instead of being hand-proved by `.symm`/`disjoint_comm`. The PR removes no hand-written symmetric lemma that it should have kept, and adds none.
- **No simp on lemmas that merely trade notions.** Left: no changed simp lemma trades one notion for another (each RHS is `univ`, an interval, `¬ ≤`, or `True`-like).
- **No lemma that merely reshapes existing ones.** Left. The PR adds no hand-written lemma, and the generated `Ici_disjoint_Iio`/`Ioi_disjoint_Iic` are genuine duals, not reshapes.
- **Title and description precise.** Filed: finding 7 (the title names only one of the two files and omits the new lemmas).
- **`to_additive (attr := ...)` for attributes.** The analogue for `to_dual` is used everywhere simp is meant to apply. Filed where it is missing: findings 1 and 2.
- **Generate duals with the generator.** Filed: findings 3 and 4.
- **Conditional simp lemmas need a stated reason.** Filed: finding 6 (new `Ici_disjoint_Iio`, `Ioi_disjoint_Iic`).
- **Title follows `type(Area): description`.** Left: the title has the form `feat(Order/Interval/Set/Disjoint): ...`. Its scope problem is filed under finding 7.
- **Sibling naming patterns.**
  - Left. `Ici_disjoint_Iio` and `Ioi_disjoint_Iic` follow the pattern of `Iic_disjoint_Ioi` and `Iio_disjoint_Ici`.
  - The suggested new names in finding 5 follow the same pattern.
- **`_left`/`_right` suffixes.** Left: the `iUnion_*_left`/`_right` pairs already carry them.
- **Changes only where the purpose requires.** Left. The PR changes only attribute lines and deletes hand-written duals; no proofs are rewritten.
- **Order duals via `αᵒᵈ`, not a repeated proof.** Superseded by `to_dual` in this PR. The remaining `h.dual`/`OrderDual R` proofs are covered by finding 4.
- **Each added lemma used, tagged or API.** Left: the new `Ici_disjoint_Iio` and `Ioi_disjoint_Iic` are tagged `simp`.
- **Explicit generator names only when they differ from the generated one.** Left, because every explicit name is needed.
  - Checked: with the names removed, none of the old names resolve.
  - The `linter.translateGenerateName` warning does not fire on the PR file, though it does fire on my edits that use redundant names.
- **Docstrings on generator source and target.** Left: none of the changed lemmas has, or had, a docstring.
