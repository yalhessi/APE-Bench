# Review notes: PR #33421 (review API about `round`)

Inputs read: pr.md, model.md, diff.patch. Files read through ptool: `target/Mathlib/Algebra/Order/Round.lean` in full, `target/Mathlib/Topology/Algebra/Order/Floor.lean` in full, `target/Mathlib/Algebra/Order/Floor/Ring.lean` lines 150-290 plus a listing of its add/sub lemmas, and the header of `Algebra/Order/Interval/Set/Group.lean`.

Tool setup: workspace paths are prefixed with `target/`. As a control, lean_verify_edit rejects a deliberately wrong proof, so its success results are meaningful. The file as the PR leaves it compiles cleanly.

## Mathlib/Algebra/Order/Floor/Ring.lean
- `Int.ceil_intCast_add`, `Int.ceil_natCast_add`, `Int.ceil_ofNat_add`: these match the existing `floor_*_add` twins in form, simp attribute and argument order. Nothing to ask.
- `Int.ceil_one_add`: fine in itself. There is no floor counterpart, though (`Int.floor_one_add` exists neither at the base nor in the PR, while `fract_one_add` does). Finding: add `floor_one_add` (verified).
- `Int.two_mul_fract_eq_one_iff_exists_int`: statement and proof are fine, and declaration_search found no duplicate (`Int.fract_eq_half_iff` does not exist either). Minor points not raised: it binds its own `{x : R}` although the section has `{a b : R}`, and it is used only once.

## Mathlib/Algebra/Order/Round.lean
- Import: the demoted `import Mathlib.Algebra.Order.Interval.Set.Group` is now unused; the file compiles without it. Finding. The downstream import additions (10 files adding `Interval.Set.Group` or `Order.Group.Basic`) are the necessary fallout of Round.lean no longer re-exporting it, so I have no request on them.
- `round_eq'`: the proof is long, but I found no clearly shorter proof. A `ring`-based rewrite would fail because α is only a `Ring`. Finding on the TODO sitting in the docstring. I considered asking for a descriptive name instead of the prime, but did not raise it: `round_eq` is itself non-descriptive, and the TODO says the formula may become the definition.
- `round_eq_half_ceil_two_mul`: the docstring is accurate, and the hypothesis `2 * fract x ≠ 1` suits the ring generality. I sketched an `omega`-based alternative proof; it is no shorter, so not raised.
- `round_eq` (new proof via `cast_mul_floor_div_cancel_of_pos` + `round_eq'`): a good simplification. Nothing to ask.
- `round_eq_iff`: new, no duplicate, and its `Ico` form is consistent with `round_eq_zero_iff`. Nothing to ask.
- `round_two_inv`, `round_neg_two_inv`, `round_eq_zero_iff`: new proofs via `round_eq_iff`. Fine.

## Mathlib/Topology/Algebra/Order/Floor.lean
- `continuousOn_floor` / `continuousOn_ceil`: the statements changed from α-valued to ℤ-valued, and `continuousOn_ceil` drops `IsStrictOrderedRing`, which is a good generalization. content_search finds no users outside this file, so the breaking change costs nothing in Mathlib. Finding: eta-reduce to `(floor : α → ℤ)` / `(ceil : α → ℤ)` and drop the `: Set α` ascriptions (verified).
- `continuousAt_floor`: fine.
- `continuousAt_ceil`: two findings, both verified. It is missing `@[fun_prop]`, which its twin has. Its hypothesis could be the dual `x ≠ ⌈x⌉`, which gives a direct proof.
- `continuousOn_floor_compl_range` / `continuousOn_ceil_compl_range`: finding for a term-mode one-liner golf (verified for both). I also considered whether `@[fun_prop]` on a ContinuousOn lemma with a fixed set is useful. It compiles, so not raised.
- `continuousOn_fract`, `continuousAt_fract`: the new proofs through `continuous_of_discreteTopology` are fine.
- `tendsto_round_nhdsGE_pure`, `tendsto_round_nhdsLT_pure_half_ceil`, `continuousAt_round`, `continuousOn_round`: all correct and compiling. Findings:
  - style: move them under the existing `variable [IsStrictOrderedRing α]` in a section with `[OrderClosedTopology α] [ContinuousAdd α]` (verified);
  - naming: `..._half_ceil` should be `..._half_ceil_two_mul`, matching `round_eq_half_ceil_two_mul` (verified).
  - Not raised: the duplicated `have : Tendsto (2 * ·) ...` block. The alternatives I found (`ContinuousWithinAt.tendsto_nhdsWithin`) save at most a line.
  - Not raised: the `nhdsGE`/`nhdsLT` naming versus the file's legacy `right`/`left` naming. `nhdsGE` is the current convention.
- `section Ring` / `end Ring` wrapper and `ContinuousOn.comp_fract''`: unchanged content, only the wrapper is new. Nothing to ask.
- Module docstring: out of date (no `round`, no `continuousAt_*`) and gives the wrong interval for `continuousOn_ceil`. Finding (verified).

## Other changed files (import-only)
AddConstMap/Basic, Archimedean/Basic, ToIntervalMod, CStarAlgebra/ApproximateUnit, Complex/Arctan, AkraBazzi/GrowsPolynomially, GroupTheory/Archimedean, IntervalIntegral/Basic, IntervalIntegral/DerivIntegrable, Liouville/Basic, Filter/AtTopBot/Archimedean, AddCircle/Defs. Each adds a private import that it used to get through Round.lean. These are consistent and I have no request.

## Tool results summary
- naming_norm: `insufficient_evidence` for every new name (`round_` prefix 22/23; subject unresolved for the topology names).
- zulip_search and precedent_search: nothing bearing on these changes.
- lean_verify_edit: every proposed edit succeeded (import removal, fun_prop on continuousAt_ceil, `x ≠ ⌈x⌉` hypothesis, eta-reduced continuousOn statements, section refactor, floor_one_add, module doc, compl_range golfs, rename, TODO move).
