# PR 28728: notes from the PR-as-a-whole review

**Q1: Is it wanted, and does it duplicate?**
- Mathlib has no matrix irreducibility, primitivity or strong connectivity yet, so the core content is new. A TODO at LinearAlgebra/RootSystem/GeckConstruction/Semisimple.lean:346 wants Perron-Frobenius.
- Several additions duplicate what exists:
  - `List.exists_mem_split` is core's `List.append_of_mem`.
  - Three new Vertices.lean lemmas restate `vertices_head_eq`, `vertices_getLast_eq` and `vertices_comp_get_length_eq`, which are already in that file.
  - The two private sum helpers are `Finset.sum_pos_iff_of_nonneg`.
  - The StronglyConnected wrapper lemmas are trivial and unused.

**Q2: Is every hunk an improvement?**
- About ten hunks in the existing Vertices.lean proofs only drop `List.` prefixes or change `simp only` to `simp`. That is style churn; the file already has `open List`.
- The import line was turned into `...Quiver.Path--.Decomposition`, a leftover comment.
- The Authors line of Data/List/Basic.lean was edited for a single duplicate lemma.

**Q3: Is it one thing?**
- No. There are four independent pieces: a List lemma, Vertices.lean decomposition (about 320 lines), quiver strong connectivity, and matrix irreducibility.
- The matrix file imports neither Vertices.lean nor the List lemma. It uses only the existing Decomposition lemma plus `eq_of_length_zero` and `length_cons`. The split should happen.

**Q4: Does the description do its job?**
- The description is empty. It has no motivation, no design choices (ℝ-only, Quiver vs Digraph, positive-length strong connectivity vs the nil-allowing setoid), no links to the downstream Perron-Frobenius work or its dependencies, and no AI disclosure.
- The title scope "PerronFrobenius" is not a Mathlib path, and the title leaves out the List and Vertices changes.

**Q5: Does it finish the job?**
- There is no automation or meta code, so no tests are needed.
- `StronglyConnectedComponent` has only `mk` and `eq`, with nothing linking it to `IsStronglyConnected`. I folded this into the Q1 StronglyConnected finding.
- `pow_entry_pos_iff_exists_path` parallels `SimpleGraph.adjMatrix_pow_apply_eq_card_walk` (SimpleGraph/AdjMatrix.lean:233). A cross-reference would be nice, but I filed no finding.

**Q6: Is it in the right place?**
- The strongly connected component construction mirrors `zigzagSetoid`/`WeaklyConnectedComponent` in Quiver/ConnectedComponent.lean:28-46 and belongs beside it, not under Quiver/Path/.
- Irreducible/Defs.lean imports Analysis.RCLike.Basic without needing it. Data/Matrix/DoublyStochastic.lean handles nonnegative matrices over a generic ordered semiring.
