# Review notes: PR #33145 (`Mathlib/Topology/Order/IsLUB.lean`)

## What I did

- Read `brief.md`, `pr.md`, `model.md` and `diff.patch`.
- Read the reviewed file (lines 1-300) with `file_read`. This showed the local conventions:
  - every GLB lemma is proved from its LUB twin via `(α := αᵒᵈ)`;
  - `isLUB_iff_of_subset_of_subset_closure` uses `upperBounds_closure ▸ upperBounds_mono_set`;
  - the neighbouring `Dense.*` lemmas redeclare `{α : Type*}` because the section fixes `[LinearOrder α]`.
- Tools used:
  - `declaration_search` on `upperBounds_closure`, `bddAbove_closure`, `Continuous.range_subset_closure_image_dense`,
    `isLUB_ciSup(_set)`, `ciSup_subtype`, `ciSup_of_empty`, `continuous_sup`/`continuous_inf`,
    `Set.image_eq_range`, `Set.range_comp_subset_range`, `Dense.denseRange_val`, `Function.Surjective.iSup_comp`,
    `DenseRange.ciSup_comp`, `Dense.ciSup`, `csSup_closure_eq`, `closure_range_eq`.
  - `content_search` for existing `Dense.*`/`DenseRange.*` lemmas about sup, bounds or LUB, and for sSup/closure
    lemmas in `Topology/`. No existing lemma states the PR's results, so there is no duplication-of-library finding.
  - `naming_norm` on the three sup-side names.
  - `zulip_search` on the originating thread: Kevin Buzzard noted that `⨆ s ∈ S` is a gotcha in a conditionally
    complete lattice, which supports the PR's `⨆ s : S` form.
  - `precedent_search` on the lowerBounds proof: PR #11200 suggested a dual proof via `αᵒᵈ`.
  - `lean_verify_edit` on every proposed edit (all succeeded; one DenseRange attempt failed first, then passed).

## Object by object

- `Dense.continuous_upperBounds`:
  - Proof golf: the term proof via `upperBounds_closure` compiles.
  - Naming: `naming_norm` says `established`, 27/27 declarations use `upperBounds_`; renaming to `Dense.upperBounds_image` compiles.
  - Docstring: grammar ("is equal"), and "range of the universe".
  - Hypotheses (`Preorder`, `ClosedIicTopology`) are already minimal. No correctness issue.
- `Dense.continuous_lowerBounds`: copied dual. `hS.continuous_upperBounds (α := αᵒᵈ) hf` compiles. It shares the rename and
  docstring findings with its twin.
- `Dense.continuous_sup`:
  - Proof golf: `isLUB_ciSup` replaces `sSup_range` plus `isLUB_csSup`, and `image_subset_range` replaces `by grind`. Compiles.
  - Naming: `sup` means binary ⊔ and clashes with the root `continuous_sup`, so I propose `ciSup_eq_ciSup_subtype`.
  - Generalization: the `DenseRange g` form compiles and specializes back in one line.
  - The empty-type split is genuinely needed (`isLUB_ciSup` needs `Nonempty`).
  - The `⨆ s : S` form (not `⨆ s ∈ S`) is correct for conditionally complete lattices.
- `Dense.continuous_inf`: copied dual. `hS.continuous_sup (α := αᵒᵈ) hf h` compiles.
- `Dense.continuous_sup'`:
  - Duplicates `continuous_sup` in the bounded branch.
  - Its `h2` block, which uses a non-terminal `simp_all only`, is replaced by a `rwa` through `BddAbove` and `continuous_upperBounds`.
  - The replacement compiles and needs no empty-type split.
  - Statement check: in a `ConditionallyCompleteLinearOrder`, `csSup_of_not_bddAbove` makes both sides `sSup ∅`, so the
    statement is right. The prime suffix for the no-`BddAbove` linear-order variant is acceptable.
  - Its docstring is fine.
- `Dense.continuous_inf'`: copied dual. `hS.continuous_sup' (α := αᵒᵈ) hf` compiles.
- Docstring commands: covered by the documentation finding. The primed docstrings ("analogue of ... The assumption
  ... is not needed") are acceptable. Only their cross-references would change with the rename.

## Considered, not filed

- Binder order `{f : γ → α} [TopologicalSpace γ]`: the instance comes after the variable. I moved it in my compiled
  block but did not file it, because a maintainer is unlikely to ask for it on its own.
- The redeclared `{α : Type*}` matches the neighbouring lemmas, which need it because the section fixes `LinearOrder α`.
- File placement: IsLUB.lean already contains conditionally-complete material (`ConditionallyCompleteLinearOrder.isCompact_Icc`),
  and the imports suffice, so there is no scope issue.
- A `Dense.bddAbove_image_iff` helper: not needed once `sup'` uses `continuous_upperBounds` directly.

## Verification summary

- Full rewritten block (lines 169-261: renames, golfs, duals, docstrings): compiles.
- Each per-declaration edit under the PR's names: compiles.
- DenseRange generalization plus the `example` recovering the Dense version: compiles.
