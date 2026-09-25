# PR 28728: notes from the whole-PR review

1. **Wanted / duplicate / trivial.** Base Mathlib has no strong connectivity for quivers and no matrix irreducibility or primitivity (grep of Mathlib for StronglyConnected, and of LinearAlgebra/Matrix, Data/Matrix and Combinatorics for Irreducible/Primitive/Perron: no hits), so the core material is wanted. The duplicates:
   - `List.exists_mem_split` is core `List.append_of_mem`.
   - Five new Vertices lemmas restate `vertices_head_eq`, `vertices_getLast_eq` and `vertices_comp_get_length_eq`, or restate each other.
   - The private sum/product helpers restate `Finset.sum_pos_iff_of_nonneg` / `sum_pos'`.
2. **Every hunk an improvement?** No:
   - The Vertices.lean edits to existing proofs only strip `List.` (the file already has `open List` at line 20) and turn `simp only` into `simp`.
   - The import line picks up the debris `Path--.Decomposition`.
   - An Authors-line edit to the 2014 Data/List/Basic.lean accompanies a duplicate lemma.
   All of these should be reverted.
3. **One thing?** No. The matrix file uses nothing from the roughly 320 new Vertices.lean lines, and cannot even import them, because Decomposition.lean does not import Vertices. The SCC quotient and the List lemma have no use in the PR either. Split into path decomposition / strongly connected quivers / matrix irreducibility.
4. **Description.** It is empty: no motivation, no design choices (ℝ-only; positive-length strong connectivity against the reflexive SCC setoid; the name overlap with `_root_.Irreducible`), no links, and no AI disclosure, although parts of the proofs look machine-generated. The title scope `PerronFrobenius` is not a path, and the title leaves out the quiver and List changes.
5. **Finishes the job?** There is no meta code or automation, so no tests are needed. I found no analogous places that the change should also update; the nearest analogue is `SimpleGraph.adjMatrix_pow_apply_eq_card_walk` (AdjMatrix.lean:233), and it needs no change. No finding.
6. **Right place?** The SCC quotient mirrors `WeaklyConnectedComponent` in Quiver/ConnectedComponent.lean and should sit with it, not under Path/. The split-at-vertex lemmas belong in Path/Decomposition.lean and could follow the SimpleGraph WalkDecomp.lean design (`takeUntil`/`dropUntil`). Matrix/Irreducible/Defs.lean is a reasonable home for the matrix part.
