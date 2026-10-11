# Review notes -- PR #33145 (Mathlib/Topology/Order/IsLUB.lean)

Inputs read: brief.md, pr.md, model.md, diff.patch; the file itself via `file_read`
(target/Mathlib/Topology/Order/IsLUB.lean, lines 1-329) and `OrderClosed.lean` lines 100-160.

Tools used: declaration_search (upperBounds_closure, lowerBounds_closure, bddAbove_closure,
Continuous.range_subset_closure_image_dense, image_closure_subset_closure_image, isLUB_closure_iff,
Set.image_eq_range, ciSup_of_not_bddAbove, isLUB_ciSup_set, sSup_image', upperBounds_mono_set,
Set.range_comp_subset_range, ciSup_subtype'), naming_norm (three new names), content_search
(existing Dense.* sup/inf lemmas -- none; ciSup/iSup subtype naming), precedent_search (nothing
relevant), zulip_search (the motivating thread: Jireh Loreaux suggested
`isLUB_iff_of_subset_of_subset_closure` + `Continuous.range_subset_closure_image_dense`; Kevin
Buzzard's `⨆ s ∈ S` suggestion was withdrawn as a conditional-completeness gotcha, so the subtype
form is right), lean_verify_edit (6 edits, all compiled).

## Object by object

- `Dense.continuous_upperBounds`: statement correct and at a reasonable level (Preorder +
  ClosedIicTopology, matching `isLUB_iff_of_subset_of_subset_closure`). Findings: name (naming_norm
  `established`, 27/27 use `upperBounds_`), docstring ("is equal", "range of the universe"),
  proof re-derives `upperBounds_closure` (golf verified), and binder style (`S`, instance order),
  verified compiling.
- `Dense.continuous_lowerBounds`: dual; proof by `hS.continuous_upperBounds (α := αᵒᵈ) hf`
  compiles. Docstring has the same errors. Rename folded into the upperBounds naming finding.
- `Dense.continuous_sup`: statement and hypotheses fine (BddAbove is needed in a non-linear
  conditionally complete lattice; empty-γ case handled). Naming finding (`sup` vs `ciSup`).
  Proof checked: the `by grind` for `range (f ∘ val) ⊆ range f` could be `range_comp_subset_range`,
  but I would not ask for it. An `IsLUB`-level variant (`IsLUB (f '' S) x ↔ IsLUB (range f) x`,
  sibling of `Dense.isLUB_inter_iff`) was considered and not requested.
- `Dense.continuous_inf`: dual proof `hS.continuous_sup (α := αᵒᵈ) hf h` compiles.
- `Dense.continuous_sup'`: correct (unbounded case: both sides are `sSup ∅` in a CCLO). Proof
  golfed to reuse `Dense.continuous_sup` and `Dense.continuous_upperBounds` with
  `ciSup_of_not_bddAbove`; compiles with no warnings.
- `Dense.continuous_inf'`: dual proof `hS.continuous_sup' (α := αᵒᵈ) hf` compiles.
- Docstrings of the sup/inf lemmas ("supremum on the universe") are understandable; not flagged
  beyond the naming cross-references. The primed lemmas' docstrings are fine.
- Scope/placement: the lemmas sit after `Dense.isLUB_inter_iff` and redeclare `{α : Type*}`
  inside `section OrderTopology`, as the neighbouring Dense lemmas already do; no move requested.
  No duplication of an existing library lemma found (no `sSup (closure ...)`/`Dense.*iSup*`
  declarations in the base).
- Correctness: file compiles as left by the PR (every verified edit reported no pre-existing
  errors); no semantic issue found.

10 findings written to findings.json (2 blocking naming, 8 advisory).
