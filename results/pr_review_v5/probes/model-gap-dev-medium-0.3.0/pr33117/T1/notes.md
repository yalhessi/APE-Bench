# Review notes: PR #33117 (introduce `Meromorphic`)

## What I did
- Read `brief.md`, `pr.md`, `model.md` and `diff.patch`, then the whole of
  `Mathlib/Analysis/Meromorphic/Basic.lean` as the PR leaves it (`file_read`), to compare the new
  `Meromorphic` namespace with its siblings `MeromorphicAt` (lines 32-417) and `MeromorphicOn` (419-633).
- `lean_verify_edit` with no edit: the PR file compiles, with no errors or warnings.
- `declaration_search`: neither `Meromorphic` nor `meromorphicOn_univ` existed before this PR.
- `naming_norm` on `meromorphicOn_univ`: subject unresolved, so naming was not measured. A manual
  check (`content_search`) finds `continuousOn_univ` and `differentiableOn_univ`, both
  `XOn f univ ↔ X f`, so the name and the `@[simp]` direction conform.
- `zulip_search`: the prior thread 'Introducing `Meromorphic`'. Gouëzel asked for exactly the name
  `meromorphicOn_univ`, simp and with the sides reversed (done), and for 'the main ones like
  `Meromorphic.add` and friends' from the start. Loreaux advised doing the replacement of
  `MeromorphicOn f univ` across Mathlib in later PRs, so I did not ask for that.
- `precedent_search`: PR #30587 on this file. A reviewer asked for `∀ σ ∈ s` in `prod`, and another
  objected to the F/G variable block.
- Every proposed edit was compiled with `lean_verify_edit`. The arguments are in `tmp/a*.json`.

## Object by object
- `Meromorphic` (def). The definition itself is fine: it matches `Differentiable`'s
  `∀ x, DifferentiableAt` shape, and `@[fun_prop]` is right. The fun_prop API around it is incomplete:
  - There is no identity or constant rule. `fun_prop` fails on `fun x ↦ x`, on constants and on
    `h x * x + 1` (finding 1, blocking).
  - There is no `Meromorphic → MeromorphicAt / MeromorphicOn` transition lemma (finding 2).
  - `inv` and `smul` are missing (finding 3).
  - All of these compiled once added, and the fun_prop examples then succeed.
- `meromorphicOn_univ`. The name and the simp direction are correct (see above). Two findings:
  - `by tauto` replaced by a term proof, which compiled; the double space goes too.
  - The docstring is reversed and has unformatted `Set.univ`.
- `neg`, `add`, `sub`, `mul`, `div` and their `fun_` versions. These are correct one-liners that
  mirror the siblings, so no finding, apart from the stray space in `fun_neg` (advisory nit).
- `sum` / `prod`. Correct. Two kinds of finding:
  - Generalization to `∀ σ ∈ s`, matching `Differentiable.sum`; compiled via
    `Finset.sum_induction` / `Finset.prod_induction`.
  - `fun_sum` / `fun_prod`: golfing the `simpa [← Finset.*_apply]` to a pointwise term, matching
    `MeromorphicOn.fun_*`; compiled.
  - These two pairs are alternatives. The golf applies to the hypothesis as stated, and under the
    generalization the `simpa` stays.
- `pow` / `zpow` (and the `fun_` versions). The exponent is implicit, unlike every sibling and
  `Differentiable.pow`. Verified that `hh.pow 2` silently means "at the point 2" (a type mismatch with
  `MeromorphicAt (h ^ ?n) 2`). Making it explicit compiled (one finding, which covers zpow too).
- `deriv`. Not `protected`, unlike `MeromorphicAt.deriv` and `MeromorphicOn.deriv`. Verified that
  `deriv f x` inside the namespace then resolves to `Meromorphic.deriv` and fails, which is why the
  PR writes `_root_.deriv`. The protected version compiled.
- `fun_deriv`, `iterated_deriv`, `fun_iterated_deriv`. These are correct and mirror the siblings. The
  `iterated_deriv` naming follows the existing `MeromorphicAt.iterated_deriv`, so there is no naming
  ask.
- The `variable` block (F for products, G for sums) mirrors the merged `MeromorphicAt` block, so no
  finding.
- The module docstring does not list the new definition (advisory documentation finding).
- Checked and not raised:
  - Leaving the existing `MeromorphicOn f Set.univ` statements (`countable_compl_analyticAt`,
    `measurable`, ValueDistribution files) unchanged is in line with the Zulip plan for follow-up
    PRs.
  - Missing docstrings on lemmas are optional in Mathlib.
  - `def Meromorphic` without `: Prop` matches `MeromorphicAt`.
