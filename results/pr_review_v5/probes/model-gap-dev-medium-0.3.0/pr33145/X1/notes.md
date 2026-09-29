# Review notes: PR #33145 (`Mathlib/Topology/Order/IsLUB.lean`)

## What I did

- Read `brief.md`, `pr.md`, `model.md`, `diff.patch`; ran `ptool describe`.
- Workspace paths use the `target/` prefix (`target/Mathlib/...`) for file tools. `lean_verify_edit` takes
  the bare `Mathlib/...` path.
- `file_read` of the PR file (lines 1-320) to get the surrounding context. The new lemmas sit inside
  `section OrderTopology` next to `isLUB_iff_of_subset_of_subset_closure` and `Dense.isLUB_inter_iff`,
  and the file uses `variable {α γ : Type*}`.
- `lean_verify_edit` with no edit: the file as the PR leaves it compiles, with no errors or warnings.
- `zulip_search`: in the prior "Is there code for X?" thread, maintainer Jireh Loreaux suggested
  `isLUB_iff_of_subset_of_subset_closure` plus `Continuous.range_subset_closure_image_dense`, with
  glue from `iSup` to `IsLUB`. Kevin Buzzard pointed out the `⨆ s ∈ S` gotcha, which is why `⨆ s : S`
  is the right form. It is used here, so there is no finding on it.
- `precedent_search` on `Dense.continuous_sup`: the hits were unrelated (topology/uniform-space
  golfs), so I discarded them.
- Candidate proofs are in `tmp/a1.lean` … `tmp/a6.lean`. `tmp/renamed.lean` has all the proofs with
  the proposed names.

## Object by object

### `Dense.continuous_upperBounds`
- Correct. `ClosedIicTopology` plus `Preorder` is the right generality, the same as
  `upperBounds_closure`.
- Proof golf / duplication: the manual `mem_closure_iff_frequently`/`isClosed_Iic` argument
  re-derives `upperBounds_closure`. The term proof in the style of
  `isLUB_iff_of_subset_of_subset_closure` compiles (lean_verify_edit success). Finding.
- Naming: naming_norm returned `established`, 27/27 `upperBounds_`. Proposed `Dense.upperBounds_image`,
  which is free: only `OrderIso.upperBounds_image` exists, and declaration_search matches without the
  namespace. Finding (blocking).
- Docstring: bad grammar and "range of the universe". Finding (advisory).
- Placement: fine next to `isLUB_iff_of_subset_of_subset_closure`. No scope ask.

### `Dense.continuous_lowerBounds`
- Correct. It is a line-for-line copy of the upper version. The `(α := αᵒᵈ)` dual compiles. Finding.
- Naming is covered by the upperBounds naming finding (naming_norm `established`, 25/25 `lowerBounds_`).

### `Dense.continuous_sup`
- Correct. `BddAbove (range f)` is genuinely needed in a `ConditionallyCompleteLattice`, where the
  junk value of `sSup` on unbounded sets is not determined, so there is no generalization ask.
- Proof golf: the `sSup_range` detour can go (use `isLUB_ciSup`), and `by grind` should be
  `image_subset_range f S`. A bare `simp` in the empty case failed; `simp [iSup_of_empty']` works.
  The verified version is in the finding.
- Naming: `sup` means binary `⊔`. This should be `ciSup`, and the name should not lead with a
  hypothesis. naming_norm could not resolve the subject, so this is judged from the neighbouring
  `ciSup` API in `Order/ConditionallyCompleteLattice/Indexed.lean`. Finding (blocking, covers
  inf/sup'/inf').

### `Dense.continuous_inf`
- Correct. It copies the sup proof, and the `OrderDual` derivation compiles. Finding.

### `Dense.continuous_sup'`
- Correct. The linear-order version drops the boundedness assumption via `csSup_of_not_bddAbove`.
- The bounded branch repeats `Dense.continuous_sup`, and `h2` is a long detour. A version that uses
  `hS.continuous_sup`, `rwa [← image_eq_range, BddAbove, hS.continuous_upperBounds hf]` and
  `ciSup_of_not_bddAbove` compiles. Finding.
- The prime for the linear-order variant is standard Mathlib practice, so I made no separate naming
  ask beyond the `ciSup` rename.

### `Dense.continuous_inf'`
- Correct. It is a 16-line copy of `sup'`, and the `OrderDual` derivation compiles. Finding.

### Docstring commands
- The upper/lowerBounds docstrings are covered by the documentation finding.
- The `sup`/`inf` docstrings ("equal to the supremum on the universe") are awkward but understandable.
  I folded them into the same documentation finding as an optional reword.
- The `'` docstrings are accurate. They will need their cross-references updated if the rename is taken.

### Whole-file check
- Every proposed proof, spliced together over lines 171-261, compiles: lean_verify_edit success.
  Adding the full rename on top also compiles.
- Style points I did not raise separately:
  - binder order `{f : γ → α} [TopologicalSpace γ]`, and re-declaring `{α : Type*}`. The neighbouring
    lemmas re-declare `α` too, because the section fixes `[LinearOrder α]`.
  - `Set.image_subset_range` written with its `Set.` prefix although `Set` is open.
  - the `obtain (_ | _)` form. This one is folded into the golf finding.
- I considered generalizing to `DenseRange g` (`⨆ i, f (g i) = ⨆ x, f x`) and did not raise it,
  because nothing in the code or the discussion shows it is needed.
- No correctness or build problems.
