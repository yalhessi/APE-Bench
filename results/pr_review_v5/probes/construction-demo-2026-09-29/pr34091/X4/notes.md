# Review notes: PR #34091 (generalize infinite pigeonhole principle)

Inputs read: brief.md, pr.md, model.md, diff.patch. Tools used (all through `ptool`):
`describe`, `file_read`/`file_search`/`content_search` (reviewed files sit under `target/`),
`declaration_search`, `naming_norm`, `precedent_search`, `zulip_search` and `lean_verify_edit`.
As the PR leaves it, `Mathlib/SetTheory/Cardinal/Pigeonhole.lean` compiles cleanly, with no errors or
warnings (as-is check).

## Object by object

**`Cardinal.infinite_pigeonhole_card_lt`** (statement and proof modified). The PR generalises the
hypothesis from `ℵ₀ ≤ #α` to `ℵ₀ ≤ #β`. That is correct and strictly more general: with a finite
codomain the lemma still holds via cofinality ℵ₀. The case split on `#α < ℵ₀` is inherent,
because with `#β = ℵ₀` and a finite `α` no uniform `θ` works. I found no golf worth asking for. The
Pigeonhole file has no other callers. Finding: the rewritten docstring says "strictly greater than
its domain's" where it means codomain's, and keeps "strictly great than" (blocking, documentation).

**`Cardinal.exists_infinite_fiber`** (statement and proof modified; the hypothesis moves from
`Infinite α` to `Infinite β`). Mathematically correct, and the case split is needed. I tried
reusing `Finite.exists_infinite_fiber` for the finite-codomain case, but that constant is not
imported here (lean_verify_edit: "Unknown constant"), so I made no duplication ask. Findings:
- the docstring has the same "domain's ... than its domain's" error (blocking);
- the explicit `(hβ : Infinite β)` should be the instance binder `[Infinite β]`, and likewise in
  the primed lemma. Both callers pass `(by infer_instance)`. The joint edit compiled (advisory).
  The StrongRankCondition call site could not be compiled against an edited Pigeonhole.lean.

**`Cardinal.exists_infinite_fiber'`** (added; keeps the old signature for the one caller in
StrongRankCondition). Keeping it is reasonable, since dropping it would force a clumsy
`Infinite κ` proof at that call site, so I made no removal ask. Finding: its tactic block inside a
term can be a direct term, which compiled (advisory). Not filed: its docstring should read "requires
the codomain", a grammar nit.

**`Cardinal.exists_uncountable_fiber`** (added). The statement is correct. `naming_norm` returned
`subject_unresolved`, so naming is unmeasured; the name parallels `exists_infinite_fiber` and I
have no naming ask. Findings:
- docstring error (blocking);
- `[Uncountable β]` instead of an explicit argument, which compiled (advisory);
- a proof with no case split, via `infinite_pigeonhole_card` at `succ (max #α ℵ₀)`, compiled
  (advisory). A milder split on `#α ≤ ℵ₀` also compiled.
- Considered and not filed: universe generalisation with `lift`. It matches the file's TODO,
  but every lemma in the file is single-universe, so I have no concrete ask.

**`Cardinal.le_range_of_union_finset_eq_univ`** (renamed from `_eq_top`; `⊤` becomes `Set.univ`,
resolving the TODO). The PR drops the `k` block, now that `exists_infinite_fiber` takes
`Infinite β`, which here is the instance `[Infinite β]`. This is correct, and `[Infinite β]` is
still necessary: a 2-element `β` covered by a single finset is a counterexample without it. The
name matches the TODO. The deprecated alias `le_range_of_union_finset_eq_top` (since 2026-01-17)
has the standard form, and its date fits the review snapshot (as_of 2026-01-18). Finding:
`by_contra h; simp only [not_le] at h` becomes `by_contra! h`, which compiled (advisory).

**Docstring commands** (three modified or added "domain's ... domain's" docstrings, plus the
added docstring on the primed lemma). Covered in the findings above. The removed TODO comment was
correctly removed together with the rename.

**`Mathlib/SetTheory/Cardinal/Pigeonhole.lean` (file)**. After the PR,
`union_finset_finite_of_range_finite` (declared in `Mathlib.Data.Set.Finite.Lattice`) is no
longer used, and the file compiles with that import removed. Filed as advisory. Downstream files
were not rebuilt.

**`infinite_basis_le_maximal_linearIndependent'`** (`Basis/Cardinality.lean`). Only the rename
of the called lemma. `union_support_maximal_linearIndependent_eq_range_basis` already states
`= Set.univ`, so the `apply`/`exact` pair still lines up. Nothing to request in the changed line.

**`linearIndependent_le_infinite_basis`** (`Dimension/StrongRankCondition.lean`). It now calls
`exists_infinite_fiber'`, with the codomain `Finset ι` infinite by instance. Correct. The only
follow-up is the one tied to the instance-binder finding: drop `(by infer_instance)` there.

## Other checks
- `precedent_search` on the fiber lemma returned only unrelated comments.
- `zulip_search` on pigeonhole/exists_infinite_fiber turned up nothing bearing on this PR.
- Scope: the PR generalises the lemmas, adds `exists_uncountable_fiber` and does the TODO
  rename. That is coherent for one small PR, so I made no split request.
