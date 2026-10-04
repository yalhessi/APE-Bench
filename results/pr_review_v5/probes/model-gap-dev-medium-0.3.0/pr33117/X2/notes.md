# Review notes: PR #33117 (`Meromorphic` predicate)

## What I did

- Read `brief.md`, `pr.md`, `model.md`, `diff.patch`.
- Read the whole changed file at review time (`target/Mathlib/Analysis/Meromorphic/Basic.lean`, lines 1-732)
  with `file_read` to compare every new lemma with its `MeromorphicAt` / `MeromorphicOn` siblings.
- `lean_verify_edit` with no edit: the PR file compiles as-is, no warnings.
- `zulip_search` on the "Introducing `Meromorphic`" thread (before the PR). Gouëzel: call the lemma
  `meromorphicOn_univ`, make it `simp`, reverse its sides (the PR does this); no need to copy every
  `MeromorphicOn` lemma, but add "the main ones like `Meromorphic.add` and friends" from the start.
  Loreaux: split the work, and replace `MeromorphicOn _ univ` in a later PR.
- `precedent_search`: earlier comments on this file (Eric Wieser on `prod` taking `∀ σ ∈ s`, on the
  `F`/`G` variable block). Both were already on the `MeromorphicAt` siblings, which were merged
  unchanged, so I did not turn them into findings.
- `declaration_search` / `content_search` for `Differentiable.differentiableAt`/`differentiableOn`,
  `differentiableOn_univ`, `Meromorphic.meromorphicAt/On` and the `iterate(d)_deriv` names.
- `naming_norm` for `meromorphicOn_univ`, `Meromorphic.iterated_deriv`, `fun_iterated_deriv`,
  `fun_sum`: every answer was `subject_unresolved`, so naming was judged by hand.
- `proof_profile` was unavailable (no declaration table for the base commit).
- Every edit I propose was compiled with `lean_verify_edit`; the argument files are in `tmp/`.
  `tmp/t13.json` swaps in the whole revised block (lines 635-732) with every proposed change and two
  `fun_prop` examples. It compiles with no warnings.

## Object by object

- **`Meromorphic` (def).** The body and the `@[fun_prop]` tag are fine. The def has no `: Prop`
  annotation, but neither do `MeromorphicAt` nor `Differentiable`, so I did not ask for one. The
  docstring is acceptable; `𝕜` could go in backticks, too small to report. Two findings, both
  confirmed by failing `fun_prop` examples:
  (1) there is no transition lemma `Meromorphic.meromorphicAt` (with `@[fun_prop]`) and no
  `Meromorphic.meromorphicOn`, so `fun_prop` cannot use `hf : Meromorphic f`;
  (2) there are no identity or constant rules and no `inv` or `smul`, so `fun_prop` fails even on
  `fun x ↦ f x + e`.
- **`meromorphicOn_univ`.** The name, the `@[simp]` tag and the direction match the maintainer's
  Zulip advice and the `differentiableOn_univ` precedent. Findings: replace `by tauto` with a term or
  `simp` proof and remove the double space (both proofs verified); put `Set.univ` in the docstring in
  backticks.
- **The `variable` block.** It mirrors the `MeromorphicAt` block, including `F`/`G` having different
  types. That block was merged, so no finding.
- **`neg`, `add`, `fun_add`, `sub`, `fun_sub`, `mul`, `fun_mul`, `div`, `fun_div`.** These are
  correct, one-line, and match their siblings. The `{f g : 𝕜 → 𝕜}` rebinding copies
  `MeromorphicAt`. No finding.
- **`fun_neg`.** Correct. One style nit: the stray space in `-f x )`.
- **`sum`, `prod`.** Correct term proofs. `∀ σ ∈ s` would be a stronger hypothesis, but the siblings
  do not use it, so I did not ask.
- **`fun_sum`, `fun_prod`.** They use `simpa [← Finset.sum_apply/prod_apply] using (...)`. Findings:
  golf to `fun x ↦ MeromorphicAt.fun_sum (h · x)` / `fun_prod`. Both verified.
- **`pow`, `fun_pow`, `zpow`, `fun_zpow`.** The exponent is implicit, but explicit in
  `MeromorphicAt` and `MeromorphicOn`. I confirmed that `hf.pow 3` silently elaborates to
  `MeromorphicAt (f ^ ?n) 3`, i.e. the lemma evaluated at the point 3. One finding, on `pow`, for
  the whole family; the explicit version is verified.
- **`deriv`.** It is not `protected`, unlike both siblings. Inside the namespace a bare `deriv` then
  resolves to `Meromorphic.deriv` (confirmed), which forces `_root_.deriv` in the next three lemmas.
  Finding; the `protected` version with the `_root_` prefixes dropped is verified.
- **`fun_deriv`, `iterated_deriv`, `fun_iterated_deriv`.** Correct. The name `iterated_deriv`
  follows its local siblings (`AnalyticAt.iterated_deriv`, `MeromorphicAt.iterated_deriv`) rather
  than `ContDiff.iterate_deriv`, so no naming finding. The only change is the `_root_` cleanup
  covered by the `deriv` finding.
- **`namespace Meromorphic` / `end Meromorphic`, `end MeromorphicOn`.** Fine.
- **File / module docstring.** `Meromorphic` (and `MeromorphicOn`) are missing from the "Main
  statements" list. Advisory finding; the edit is verified.

## Considered and not reported

- Restating `MeromorphicOn.countable_compl_analyticAt` / `MeromorphicOn.measurable` for
  `Meromorphic f`. Since `meromorphicOn_univ` is `simp`, a simp-normalised hypothesis no longer
  admits `h.measurable` (confirmed: "Invalid field `measurable`"), and `Meromorphic.measurable` via
  `(meromorphicOn_univ.2 h).measurable` compiles. I left it out because the Zulip thread explicitly
  defers porting `MeromorphicOn _ univ` statements to a follow-up PR.
- The `theorem`/`lemma` keyword mix, and missing docstrings on the new lemmas: Mathlib does not
  require lemma docstrings, and the keyword mix is not something reviewers ask to change.
