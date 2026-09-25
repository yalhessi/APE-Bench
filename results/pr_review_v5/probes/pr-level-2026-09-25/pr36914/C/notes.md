# PR 36914 review notes

- **PR overall:** an automated upload from Termux (a demo file, a restatement of `Nat.add_comm`, and the push script). A maintainer would close it. I list the concrete defects anyway, because each would be requested if the author engaged.
- **push_proofs.sh:** a personal git/gh script at the repository root that runs `git add .` and `gh pr create`. It is out of scope, so remove it.
- **MyNewProofs.lean / my_add_comm:** the proof is literally `Nat.add_comm a b`, so the lemma is pure duplication (core `Nat.add_comm`, generic `add_comm`). Delete the file. The imports are also unused.
- **MathlibDemo.lean imports:** `Mathlib.LinearAlgebra.LinearMap` does not exist at the base commit (checked with mlshow), so the file cannot build.
- **EndH/id_op/comp/O_k/S/Ω:** each is an existing operation on the ring/algebra `H →L[ℝ] H` (`one_def`, `mul_def`, `algebraMap`, `-1`, `^2`). They are also short root-namespace names. I requested deletion rather than renaming, so I did not raise naming, `Type` vs `Type*` or the unused `CompleteSpace` as separate findings.
- **A:** `A id_op` omits the explicit `H`, which is an elaboration error. Mathematically, `A` is just "scalar multiple of the identity", i.e. `⊥ : Subalgebra`. The `omega` constructor is redundant with `comp`, and the "Algebra" comment is wrong because `A` has no addition.
- **O_total:** `comp (O_k k) (comp S id_op)` passes operators and a scalar where the explicit `H` is expected, so it does not elaborate.
- **ϕ_example:** it is `sorry`. That is a policy violation, so remove it.
- **File-level:** there is no copyright header, `module`/`public import` or module docstring, and it sits in the wrong directory (Algebra rather than Analysis/InnerProductSpace). Neither file is registered in Mathlib.lean, so `mk_all --check` fails in CI.
