# PR 31984 review notes

The file tools (`file_read`, `file_search`, `content_search`) could not find any Mathlib path in this
workspace, so I rebuilt the new file from `diff.patch` to get line numbers. `declaration_search` and
`lean_verify_edit` worked. The verifier's first result took about 10 seconds, so I checked it was
really compiling: a misspelled import failed as it should.

## Mathlib.lean
- One import line, placed in alphabetical order (after Contraction, before Countable). Nothing to ask.

## Mathlib/LinearAlgebra/ConvexSpace.lean: header and imports
- lean_verify_edit with `Mathlib.Data.ZMod.Defs` and `Mathlib.Algebra.Module.Defs` removed compiled
  → finding: remove the unused imports. `Tactic.Bound` is used by `bound` in `comp`, so I kept it.
- The module docstring and TODO list are fine. The copyright line and `module` / `@[expose] public section` are standard.

## FiniteProbability (structure)
- `declaration_search FiniteProbability` / `ConvexSpace` found no earlier declaration of either name,
  so there is no duplication. `stdSimplex` and `PMF` are different objects (a set in `ι → 𝕜`; ENNReal
  masses). The binders `[LE R] [AddCommMonoid R] [One R]` are already minimal. The field names
  `nonneg` / `total` are unremarkable. I did not request a `Finsupp.degree`-style restatement, which would need a heavier import.
- A precedent_search on the structure returned only unrelated Finsupp.weight and HahnSeries comments.

## FiniteProbability section variables / generalization
- lean_verify_edit replacing every `IsStrictOrderedRing` with `IsOrderedRing` (lines 55-148) compiled
  cleanly → generalization finding, attached to the class because that is where the hypothesis matters for instances.

## FiniteProbability.single
- `open Classical in` on a def, used only inside a proof field, and `grind` for `0 ≤ 0`. Verified a
  replacement using the `classical` tactic and `split <;> simp` → style/golf finding.

## FiniteProbability.duple
- Docstring names `x`, `y` but the parameters are `s`, `t` → documentation finding. The question comment goes in the same finding.
- Non-terminal `simp; grind`. Verified `simp [Fin.forall_fin_two, hs, ht]` → golf finding.
- The name `duple`: naming_norm returned subject_unresolved and gave no evidence either way, so I asked for nothing.

## FiniteProbability.comp
- The `weights` definition is fine. `nonneg` has a non-terminal `simp [Finsupp.embDomain]` before `bound`. I did not verify a
  replacement, so I asked for nothing there.
- `total`: 25-line Aristotle proof. My first attempt with `Finsupp.sum_smul_index` failed (unknown
  constant; declaration_search shows it lives in Data/Finsupp/SMul, which is not imported). A second
  attempt with `sum_sum_index` + `sum_embDomain` + a `hg` helper built on `sum_of_support_subset`
  compiled → golf finding with the verified 8-line proof.

## ConvexSpace (class)
- Main result, from reasoning rather than a tool: the three axioms are satisfied by "linear combination
  plus Shannon entropy of the weights", because the entropy chain rule matches `comp` exactly. So
  idempotence fails and `proof_wanted convexCombo₂_same` is false for some instances. The missing
  axiom is naturality under reindexing, which would also subsume `ext` → blocking correctness finding.
  This is not machine-checked; building the counter-model in-file needs Real.log imports.
- Universe coupling (`ι : Type v` for the same `v` as `M`) is a deliberate design choice. I asked for nothing.
- zulip_search on convex-space / barycentric-algebra axioms found nothing relevant.

## ConvexSpace.ext (field)
- The name is misleading: `ext` names structure extensionality and would clash with `@[ext]`. This is an advisory
  rename, and moot if the naturality axiom replaces the field.

## convexCombo₂ and the three proof_wanted
- The definition is fine (`fun | 0 => x | 1 => y` elaborates). I did not raise the `Combo` vs `Combination`
  abbreviation because naming_norm had no evidence. `convexCombo₂_zero` / `_one` are provable from
  `single` + `ext` plus an equality `duple 0 1 = single 1` and hold in the counter-model. `_same` is covered by the class finding.
- `variable {R M}` with elided types works (the types come from `[ConvexSpace R M]`). It is minor, and I asked for nothing.
