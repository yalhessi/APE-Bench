# PR #36914 review notes: the PR as a change

1. **Wanted?** No. `my_add_comm` is core `Nat.add_comm`, used 88 times in Mathlib, and the general
   `add_comm` also covers it (Algebra/Group/Defs.lean). The demo's defs rename `ContinuousLinearMap.id`/`1`,
   `.comp`, `k • 1`, `-1` and `O*O`, all available through the existing Ring/Algebra instances on `H →L[ℝ] H`
   (Topology/Algebra/Module/LinearMap.lean:343,351,936,1137). `A` is a closure predicate
   (`Submonoid.closure`, `Algebra.adjoin`). No theorem is proved, and `ψ_example` is a `sorry`. Request: close.
2. **Every hunk an improvement?** push_proofs.sh is a personal git/gh automation script with a hard-coded
   fork, `git add .` and `git push`. It is unrelated to the library, and no script lives at the repo root (tooling is in
   scripts/). Remove it.
3. **One thing?** No. It bundles three unrelated items (operator demo, Nat lemma, shell script). The title names only
   the demo, and the script would itself open a different PR, "Add MyNewProofs", which points to an accidental `git add .`.
4. **Description?** One line. No motivation, "SNAP" never explained, no design choice. It does not mention two of the three
   files and calls a sorry-only file a "proof file". Automation is disclosed, but AI generation of the content is not, and the code
   reads as generated. No discussion or downstream link.
5. **Finishes the job?** Neither file is in Mathlib.lean, and CI runs `lake exe mk_all --check`
   (.github/workflows/build_template.yml:416). The demo imports `Mathlib.LinearAlgebra.LinearMap`, which does
   not exist at base 5160b96e. The files lack the tree-wide `module`/`public import` header. There is no meta code, so the
   test-placement question does not apply.
6. **Right place?** Hilbert-space operators do not belong in Mathlib/Algebra/. Their home is Topology/Algebra/Module/ or
   Analysis/InnerProductSpace/ (e.g. Adjoint.lean:282 CStarRing). Demo and "MyNewProofs" files with unnamespaced
   top-level names belong in a downstream project, not Mathlib (advisory, since closing makes the point moot).
