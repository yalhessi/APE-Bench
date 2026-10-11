# Review notes: PR #33117, `Meromorphic`

## What I did

- I read `brief.md`, `pr.md`, `model.md` and `diff.patch`, then read the whole reviewed file through `ptool file_read`. The PR's block is lines 635-732. The `MeromorphicAt` and `MeromorphicOn` siblings are at lines 59-417 and 419-633.
- Compiling the file as the PR leaves it gives `compiled`, with no warnings, so no lines are over 100 characters and no linter fires.
- Lean checks I ran with `lean_verify_edit`:
  - Appending `example : Meromorphic (fun x : 𝕜 ↦ x) := by fun_prop` fails with "missing identity rule". The same for `fun _ ↦ 1` fails with "missing constant rule".
  - `example ... (hf : Meromorphic f) : MeromorphicAt (fun z ↦ f z * z + 1) x := by fun_prop` fails because there is no transition from `Meromorphic` to `MeromorphicAt`.
  - Proving `MeromorphicOn f Set.univ ↔ Meromorphic f` with `Iff.rfl` gives a type mismatch, so the golf has to be the anonymous constructor.
  - A full revision of lines 635-732 **compiled** with no warnings. It contains:
    - `: Prop` on the def;
    - sentence docstrings with backticks;
    - the term proof of `meromorphicOn_univ`;
    - new lemmas `meromorphicAt` (`@[fun_prop]`), `meromorphicOn`, `id`, `const`, `smul`, `fun_smul`, `inv` and `fun_inv`;
    - a `section` with `variable {f g : 𝕜 → 𝕜}`;
    - explicit `(n : ℕ)` and `(n : ℤ)` in `pow` and `zpow`;
    - `protected theorem deriv`;
    - docstrings on `sum` and `prod`;
    - term proofs of `fun_sum` and `fun_prod`;
    - `example`s that `fun_prop` closes.
  - With the hypotheses of `sum` and `prod` weakened to `∀ σ ∈ s`, using `Finset.sum_attach` / `Finset.prod_attach`, it **compiled**.
- Zulip, in the thread "Introducing `Meromorphic`":
  - Gouëzel asked for the lemma to be named `meromorphicOn_univ`, tagged `simp` and with its sides reversed. The PR does all three.
  - He said the add-style lemmas should come first.
  - Loreaux suggested replacing `MeromorphicOn univ` across the library in separate PRs.
  - Nuccio and Loreaux asked for `fun_prop` support.
- Precedent: on PR #30587 in the same file, Eric Wieser suggested `∀ σ ∈ s` for `prod`.
- Library search: `MeromorphicOn _ (Set.)univ` hypotheses appear in 6 files, including this file's `countable_compl_analyticAt` and `measurable`.

## Object by object

- **`Meromorphic`** (def). The body is right and it is consistent with `Differentiable` and `AnalyticOnNhd`. Findings:
  - no `: Prop`;
  - the docstring leaves `𝕜` out of backticks;
  - the docstring is a noun phrase ending in a full stop that does not state the definition;
  - the `fun_prop` API has no `id`/`const` rule (blocking: `fun_prop` cannot prove even `Meromorphic id`);
  - there is no `meromorphicAt`/`meromorphicOn` projection;
  - `smul`, `inv`, `neg_iff` and `inv_iff` have no analogues;
  - the predicate is not applied to `MeromorphicOn.countable_compl_analyticAt` or `MeromorphicOn.measurable` in the same file (follow-up for the rest of the library).
- **`meromorphicOn_univ`**. The name, the side order and `@[simp]` already follow Gouëzel's request and the `continuousOn_univ` convention: the line `lemma meromorphicOn_univ {f : 𝕜 → E} : MeromorphicOn f Set.univ ↔ Meromorphic f`. Findings:
  - `by tauto` should be the term `⟨fun h x ↦ h x (mem_univ x), fun h x _ ↦ h x⟩`;
  - there is a doubled space before `:=`;
  - `Set.univ` is not in backticks in the docstring;
  - the docstring only restates the statement.
- **`Meromorphic.neg` / `add` / `fun_add` / `sub` / `fun_sub` / `div` / `fun_div`**. Nothing to request beyond the shared variable-block finding. The proofs are one-line pointwise terms and the names follow the `f + g` vs `fun x ↦ f x + g x` naming-guide pattern.
- **`Meromorphic.fun_neg`**. Stray space in `-f x )`.
- **`Meromorphic.mul` / `fun_mul`**. Target of the finding about repeated `{f g : 𝕜 → 𝕜}` binders, which also covers `div` and `pow`/`zpow`.
- **`Meromorphic.sum` / `fun_sum` / `prod` / `fun_prod`**. Findings:
  - they are `theorem`s without docstrings (`sum` and `prod` each filed);
  - `fun_sum` and `fun_prod` use a `simpa` proof where a pointwise term works (each filed);
  - the hypothesis can be weakened to `∀ σ ∈ s` (filed on `prod`, covering `sum`).
- **`Meromorphic.pow` / `fun_pow` / `zpow` / `fun_zpow`**. The exponent is implicit where the `MeromorphicAt`, `MeromorphicOn`, `AnalyticAt` and `Continuous` siblings take it explicitly. Filed on `pow` and on `zpow`.
- **`Meromorphic.deriv`**. Not `protected`, unlike `MeromorphicAt.deriv` and `MeromorphicOn.deriv`, and its name clashes with `_root_.deriv`: the PR itself has to write `_root_.deriv` in the next three lemmas.
- **`Meromorphic.fun_deriv` / `iterated_deriv` / `fun_iterated_deriv`**. Checked and nothing filed:
  - the names match `MeromorphicAt.iterated_deriv` and `AnalyticAt.iterated_deriv`;
  - `lemma` without a docstring is consistent with the theorem/lemma convention;
  - `{n : ℕ}` implicit matches `MeromorphicAt.iterated_deriv`.
- **File**. The module docstring does not mention `Meromorphic` (or `MeromorphicOn`).
- **`namespace` / `end` / `variable` commands**. Nothing wrong apart from the variable-binder finding.

## Conventions, place by place

1. **`@[simp]` on a definition applied to a canonical argument.** Filed nowhere new. `meromorphicOn_univ` already has `@[simp]` (line 640). The missing `neg_iff`/`inv_iff`, which would be `@[simp]`, are part of the API finding on `Meromorphic`.
2. **Drop or weaken unneeded hypotheses.** Filed on `Meromorphic.prod`, covering `sum` (`∀ σ ∈ s`, verified). The other lemmas use only what they need. `[CompleteSpace E]` is needed by `MeromorphicAt.deriv`.
3. **A name built from the declarations in the statement.** Nothing filed. `meromorphicOn_univ` matches `MeromorphicOn` + `univ`. The `add`/`fun_add`-style names match the siblings. `iterated_deriv` matches `MeromorphicAt.iterated_deriv` and `AnalyticAt.iterated_deriv` (content_search).
4. **`protected` against a root-name clash.** Filed on `Meromorphic.deriv`. No other short name in the block clashes with a root declaration, and the new `id` I proposed mirrors the unprotected `MeromorphicAt.id`.
5. **A term instead of a short tactic block.** Filed on `meromorphicOn_univ` (`by tauto`), `Meromorphic.fun_sum` and `Meromorphic.fun_prod`. All the other proofs are already terms.
6. **The module docstring covers the main results.** Filed on the file.
7. **Shared arguments declared with `variable`.** Filed on `Meromorphic.mul`, covering `fun_mul`, `div`, `fun_div` and the `pow`/`zpow` family. The `{ι} {s} {f g : 𝕜 → E} {F} {G}` block is already a `variable` (lines 645-647).
8. **Spacing.** Filed on `meromorphicOn_univ` (double space) and `Meromorphic.fun_neg` (space before `)`). Nothing else in lines 635-732 departs from it.
9. **No new declaration duplicating an existing one.** `declaration_search` was not needed: Zulip settled that `Meromorphic` is new and wanted, and nothing in base defines it. Nothing filed.
10. **A new definition ships with its basic API.** Filed on `Meromorphic`: `id`/`const` (blocking), the `meromorphicAt`/`meromorphicOn` projections, and the `smul`/`inv`/`neg_iff`/`inv_iff` analogues.
11. **No `@[simp]` on a lemma trading one notion for another.** `meromorphicOn_univ` simplifies to the absolute notion, as `continuousOn_univ` does, and the maintainer asked for `simp`. Not filed.
12. **The same construct spelled the same way.** Filed: the `pow`/`zpow` explicit exponent (two findings) and `protected deriv` (above). `lemma` vs `theorem` is covered under 18.
13. **An explicit type on a definition.** Filed on `Meromorphic` (`: Prop`).
14. **A lemma identifying the definition with an established object.** `meromorphicOn_univ` exists. Not filed.
15. **A docstring that says what the value means.** Filed on `Meromorphic` (rewrite as a sentence) and on `meromorphicOn_univ` (the docstring only restates the statement).
16. **Backticks in docstrings.** Filed on `Meromorphic` (`𝕜`) and `meromorphicOn_univ` (`Set.univ`).
17. **Apply the new notion to existing places.** Filed on `Meromorphic`: `countable_compl_analyticAt` and `measurable` in this file, the rest as a follow-up.
18. **`theorem` only when it carries a docstring.** Filed on `Meromorphic.sum` (with `fun_sum`) and `Meromorphic.prod` (with `fun_prod`). The `deriv` family uses `lemma`, as the convention asks.
19. **`fooOn_univ` with the relativised side on the left.** Already conforms: `lemma meromorphicOn_univ {f : 𝕜 → E} : MeromorphicOn f Set.univ ↔ Meromorphic f`. Not filed.
20. **A relativised notion comes with the absolute one.** That is what this PR adds. Not filed.
21. **A new notion comes with the analogues of the existing API.** Filed as part of the API findings on `Meromorphic`.
22. **`@[fun_prop]` on preservation lemmas.** Every new preservation lemma already carries `@[fun_prop]` (e.g. line 649 `@[fun_prop] lemma neg`). The missing identity/constant/transition rules are filed under 10.
23. **No full stop after a noun-phrase docstring.** Filed on `Meromorphic` ("Meromorphy of a function on all of 𝕜."). The `meromorphicOn_univ` docstring is a full sentence.
24. **A name or design settled on Zulip.** Already met: the Zulip thread "Introducing `Meromorphic`" agreed the name and the `meromorphicOn_univ` shape before the PR. Not filed.
25. **Naming of expanded and unexpanded forms.** Already conforms: `add` for `f + g` and `fun_add` for `fun x ↦ f x + g x`, and the same for every pair. Not filed.
