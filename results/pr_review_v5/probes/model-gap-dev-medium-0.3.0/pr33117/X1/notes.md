# Review notes, PR #33117 (`Meromorphic` predicate)

## What I did

- Read `brief.md`, `pr.md`, `model.md` and `diff.patch`. Read the whole of
  `target/Mathlib/Analysis/Meromorphic/Basic.lean` with `file_read`, so I could compare against the
  sibling `MeromorphicAt` (lines 59-417) and `MeromorphicOn` (lines 419-633) APIs.
- Searched Zulip for the "Introducing `Meromorphic`" thread. Maintainers there asked for:
  - the iff to be named `meromorphicOn_univ`, marked `simp`, with `MeromorphicOn` on the left
    (Gouëzel). The PR does this.
  - only basic API such as `add` "and friends" in this PR (Gouëzel).
  - the migration of `MeromorphicOn f univ` uses to happen in later PRs (Loreaux).

  Nuccio and Loreaux also asked for `fun_prop` support.
- Ran `precedent_search` on `pow` and on `meromorphicOn_univ`. One hit was Eric Wieser on PR #30587,
  proposing `∀ σ ∈ s` hypotheses for `MeromorphicAt.prod`. That suggestion was not adopted in the
  sibling (the base still has `∀ σ`), so I did not raise it here.
- Ran `naming_norm` on `meromorphicOn_univ` and `Meromorphic.iterated_deriv`. Both came back
  `subject_unresolved`, so naming was not measured. Judged by hand, `meromorphicOn_univ` matches
  `continuousOn_univ`, `analyticOn_univ` and `differentiableOn_univ`, and `iterated_deriv` matches the
  existing `MeromorphicAt/On.iterated_deriv`.
- Ran `lean_verify_edit` five times:
  1. `fun_prop` probes on the PR as it stands. Proving `Meromorphic (fun x ↦ x)`, `Meromorphic`
     of a constant, and `MeromorphicAt f x` from `Meromorphic f` all FAIL: "missing identity rule",
     "missing constant rule", "No theorems found for `f`".
  2. The missing API added (`meromorphicAt`, `meromorphicOn`, `id`, `const`, `smul`, `fun_smul`, `inv`,
     `fun_inv`) plus the same probes and `Meromorphic (fun x ↦ x ^ 2 + 1)` by `fun_prop`: success.
  3. A shadowing probe. On the PR as it stands, writing `deriv f x` inside `namespace Meromorphic`
     after the unprotected `Meromorphic.deriv` fails ("Application type mismatch ... expected to have
     type Meromorphic ?m ... in the application deriv f").
  4. One replacement of lines 639-730 with every proposed change: term proof and fixed docstring
     and spacing for `meromorphicOn_univ`; `fun_neg` spacing; direct proofs of `fun_sum`/`fun_prod`;
     explicit `(n : ℕ)`/`(n : ℤ)` on `pow`/`fun_pow`/`zpow`/`fun_zpow`; `protected` on `deriv` with
     plain `deriv` in the later lemmas; and a `fun_prop` example with ℕ and ℤ powers. Success.
     No line is over 100 characters.

## Object by object

- `Meromorphic` (def): the definition `∀ x, MeromorphicAt f x` matches the `Differentiable` pattern.
  It has a docstring and `@[fun_prop]`. Nothing wrong with the definition itself. Its API is missing
  pieces, which gives three findings:
  - no `meromorphicAt`/`meromorphicOn` transition lemmas;
  - no `id`/`const` `fun_prop` rules;
  - no `smul`/`inv` counterparts.
- `meromorphicOn_univ`: the name, `simp` attribute and orientation all follow Gouëzel's Zulip request.
  Two findings:
  - `tauto` should be the term `⟨fun h x ↦ h x trivial, fun h x _ ↦ h x⟩`;
  - `Set.univ` needs backticks in the docstring, and there is a double space before `:=`.
- `neg`, `add`, `fun_add`, `sub`, `fun_sub`, `mul`, `fun_mul`, `div`, `fun_div`: the statements and
  proofs are fine and match the siblings. No finding.
- `fun_neg`: one finding, the stray space in `-f x )`.
- `sum`, `prod`: fine. `∀ σ ∈ s` would be a stronger hypothesis, but the sibling
  `MeromorphicAt.sum/prod` uses `∀ σ` and that generalisation was already declined upstream, so no
  finding.
- `fun_sum`, `fun_prod`: one finding each. Replace the `simpa [← Finset.sum_apply/prod_apply]` proofs
  with the direct `fun x ↦ MeromorphicAt.fun_sum/fun_prod (h · x)`, as in `MeromorphicOn`.
- `pow`/`fun_pow` and `zpow`/`fun_zpow`: one finding each. The exponent is implicit here but explicit
  after the hypothesis in `MeromorphicAt` and `MeromorphicOn`.
- `deriv`: one blocking finding. It is not `protected`, unlike both siblings, so it shadows
  `_root_.deriv` (verified) and forces the `_root_.` prefixes in the later lemmas.
- `fun_deriv`, `iterated_deriv`, `fun_iterated_deriv`: fine apart from the `_root_.` prefixes, which
  the `deriv` finding covers.
- `namespace` / `variable` / `end` commands: fine.
- Scope: rewriting `MeromorphicOn.countable_compl_analyticAt` and `MeromorphicOn.measurable`, and the
  ValueDistribution files (content_search found about 30 `MeromorphicOn f univ` uses), in terms of
  `Meromorphic` belongs to a follow-up PR, as Loreaux planned on Zulip. No finding.
- Docstrings on the new lemmas: the `MeromorphicAt` versions of `sum`/`prod`/`deriv` have them, but
  Mathlib does not require docstrings on lemmas. No finding.
- The module docstring does not list `Meromorphic`, but it does not list `MeromorphicOn` either. No
  finding.
