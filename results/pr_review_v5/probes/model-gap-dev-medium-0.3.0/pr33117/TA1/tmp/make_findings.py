import json, sys
D = sys.argv[1]
V_FULL = ("lean_verify_edit (line mode, lines 635-732 replaced by a revised block: `: Prop` on the def, "
          "backticked sentence docstrings, term proof of meromorphicOn_univ, `Meromorphic.id`/`const`/"
          "`meromorphicAt`/`meromorphicOn`/`smul`/`fun_smul`/`inv`/`fun_inv`, a `section` with "
          "`variable {f g : 𝕜 → 𝕜}`, explicit `(n : ℕ)`/`(n : ℤ)` in pow/zpow, `protected theorem deriv`, "
          "docstrings on sum/prod, term proofs of fun_sum/fun_prod, plus `example`s closed by `fun_prop`) "
          "-> outcome `compiled`, success true, no errors, no warnings.")
F = []
def add(target, claim, change, sev, ev, family):
    F.append({"target": target, "claim": claim, "requested_change": change, "severity": sev,
              "evidence": ev, "family": family})

add("Meromorphic",
    "`Meromorphic` is registered with `@[fun_prop]` but the PR gives it no identity or constant rule, so `fun_prop` cannot prove even `Meromorphic (fun x ↦ x)` or `Meromorphic (fun _ ↦ 1)`; the `fun_prop` API for the new predicate is unusable on any goal built from `id`/constants.",
    "Add, as for `MeromorphicAt.id`/`MeromorphicAt.const` and `MeromorphicOn.id`/`MeromorphicOn.const`:\n@[fun_prop]\nlemma id : Meromorphic (id : 𝕜 → 𝕜) := fun x ↦ .id x\n\n@[fun_prop]\nlemma const (e : E) : Meromorphic (fun _ : 𝕜 ↦ e) := fun x ↦ .const e x",
    "blocking",
    "lean_verify_edit on the PR file with `example : Meromorphic (fun x : 𝕜 ↦ x) := by fun_prop` appended -> error \"fun_prop was unable to prove `Meromorphic fun x => x` ... missing identity rule\"; with `example : Meromorphic (fun _ : 𝕜 ↦ (1 : 𝕜)) := by fun_prop` -> \"missing constant rule\". With the two lemmas added, `example : Meromorphic (fun x : 𝕜 ↦ x * x + 1) := by fun_prop` and `example (f : 𝕜 → 𝕜) (hf : Meromorphic f) : Meromorphic (fun x ↦ (f x)⁻¹ + 3 * x ^ 2) := by fun_prop` compile. " + V_FULL,
    "correctness")

add("Meromorphic",
    "The new predicate ships without the projections to the relativised notions: there is no `Meromorphic.meromorphicAt` or `Meromorphic.meromorphicOn` (the analogues of `Differentiable.differentiableAt`/`Differentiable.differentiableOn`, both `@[fun_prop]`), so `fun_prop` cannot use a hypothesis `hf : Meromorphic f` to prove a `MeromorphicAt` goal and users must unfold the definition by hand.",
    "Add\n@[fun_prop]\nlemma meromorphicAt (hf : Meromorphic f) {x : 𝕜} : MeromorphicAt f x := hf x\n\nlemma meromorphicOn (hf : Meromorphic f) {U : Set 𝕜} : MeromorphicOn f U := fun x _ ↦ hf x",
    "advisory",
    "lean_verify_edit on the PR file: `example (f : 𝕜 → 𝕜) (x : 𝕜) (hf : Meromorphic f) : MeromorphicAt (fun z ↦ f z * z + 1) x := by fun_prop` -> error \"No theorems found for `f` in order to prove `MeromorphicAt (fun a => f a) x`\". With the `@[fun_prop]` transition lemma added the same example compiles (outcome compiled, no warnings). FDeriv/Basic.lean:500-517 has `@[fun_prop] theorem Differentiable.differentiableAt` and `@[fun_prop] theorem Differentiable.differentiableOn`.",
    "generalization")

add("Meromorphic",
    "The `Meromorphic` namespace omits the analogues of existing `MeromorphicAt`/`MeromorphicOn` API lemmas that the PR otherwise mirrors: `smul`/`fun_smul`, `inv`/`fun_inv`, and the `@[simp]` lemmas `neg_iff`/`inv_iff` (all present as `MeromorphicAt.smul`, `MeromorphicAt.inv`, `MeromorphicAt.neg_iff`, `MeromorphicAt.inv_iff`, `MeromorphicOn.smul`, `MeromorphicOn.inv`, `MeromorphicOn.neg_iff`, `MeromorphicOn.inv_iff`).",
    "Add `Meromorphic.smul`, `Meromorphic.fun_smul`, `Meromorphic.inv`, `Meromorphic.fun_inv` (each `@[fun_prop]`, proved pointwise, e.g. `lemma inv {f : 𝕜 → 𝕜} (hf : Meromorphic f) : Meromorphic f⁻¹ := fun x ↦ (hf x).inv`) and `@[simp] lemma neg_iff : Meromorphic (-f) ↔ Meromorphic f` / `@[simp] lemma inv_iff {f : 𝕜 → 𝕜} : Meromorphic f⁻¹ ↔ Meromorphic f`.",
    "advisory",
    "Base file Basic.lean:93-106 (smul, fun_smul), 174-177 (neg_iff), 257-292 (inv, fun_inv, inv_iff), 493-538 (MeromorphicOn versions). smul/fun_smul/inv/fun_inv added in the verified revision: " + V_FULL,
    "duplication")

add("Meromorphic",
    "The definition `def Meromorphic (f : 𝕜 → E) := ∀ x, MeromorphicAt f x` leaves its type to be inferred from the body, whereas the neighbouring `def MeromorphicOn (f : 𝕜 → E) (U : Set 𝕜) : Prop := ...` states it.",
    "State the type: `def Meromorphic (f : 𝕜 → E) : Prop := ∀ x, MeromorphicAt f x`.",
    "advisory",
    "Basic.lean:637 (PR) vs Basic.lean:420 `def MeromorphicOn ... : Prop`. The `: Prop` version is part of the verified revision: " + V_FULL,
    "style")

add("Meromorphic",
    "The docstring `/-- Meromorphy of a function on all of 𝕜. -/` writes the type variable `𝕜` without backticks, so it does not render as code.",
    "Write `𝕜` as `` `𝕜` `` (and name the function `` `f` ``), e.g. `/-- A function `f : 𝕜 → E` is meromorphic if it is meromorphic at every point of `𝕜`. -/`.",
    "advisory",
    "Basic.lean:635 `/-- Meromorphy of a function on all of 𝕜. -/`. Backticked docstring compiles in the verified revision: " + V_FULL,
    "documentation")

add("Meromorphic",
    "The docstring `Meromorphy of a function on all of 𝕜.` is a noun phrase ending with a full stop and does not say what the predicate means (that `f` is `MeromorphicAt` every point).",
    "Replace it with a complete sentence giving the definition: `/-- A function `f : 𝕜 → E` is meromorphic if it is meromorphic at every point of `𝕜`. -/` (or, if the noun phrase is kept, drop the final full stop).",
    "advisory",
    "Basic.lean:635. Revised docstring is in the verified revision: " + V_FULL,
    "documentation")

add("meromorphicOn_univ",
    "`meromorphicOn_univ` is proved by `by tauto`, a heavy search tactic, where a one-line anonymous-constructor term proves it (`Iff.rfl` does not, since `∀ x ∈ univ, _` and `∀ x, _` are not defeq).",
    "Replace `:= by tauto` with\n  ⟨fun h x ↦ h x (mem_univ x), fun h x _ ↦ h x⟩",
    "advisory",
    "lean_verify_edit: `example {f : 𝕜 → E} : MeromorphicOn f Set.univ ↔ Meromorphic f := Iff.rfl` -> Type mismatch (so a term other than Iff.rfl is needed). The term `⟨fun h x ↦ h x (mem_univ x), fun h x _ ↦ h x⟩` compiles in the verified revision: " + V_FULL,
    "proof-golf")

add("meromorphicOn_univ",
    "The statement line has a doubled space before `:=`: `MeromorphicOn f Set.univ ↔ Meromorphic f  := by tauto`.",
    "Use a single space: `... ↔ Meromorphic f :=`.",
    "advisory",
    "Basic.lean:641 as the PR leaves it: `lemma meromorphicOn_univ {f : 𝕜 → E} : MeromorphicOn f Set.univ ↔ Meromorphic f  := by tauto`.",
    "style")

add("meromorphicOn_univ",
    "The docstring `A function is meromorphic iff it is meromorphic on Set.univ.` writes the declaration `Set.univ` without backticks.",
    "If the docstring is kept, write `` `Set.univ` `` (and `` `MeromorphicOn` ``/`` `Meromorphic` ``) in backticks.",
    "advisory",
    "Basic.lean:639 `/-- A function is meromorphic iff it is meromorphic on Set.univ. -/`.",
    "documentation")

add("meromorphicOn_univ",
    "The docstring of `meromorphicOn_univ` only restates its statement `MeromorphicOn f Set.univ ↔ Meromorphic f` in words, adding nothing (compare `differentiableOn_univ`, which has none).",
    "Delete the docstring `/-- A function is meromorphic iff it is meromorphic on Set.univ. -/`.",
    "advisory",
    "Basic.lean:639-641; FDeriv/Basic.lean:511 `theorem differentiableOn_univ` carries no docstring.",
    "documentation")

add("Meromorphic.fun_neg",
    "The statement has a stray space before the closing parenthesis: `Meromorphic (fun x ↦ -f x )`.",
    "Write `Meromorphic (fun x ↦ -f x)`.",
    "advisory",
    "Basic.lean:653 as the PR leaves it. Fixed form compiles in the verified revision: " + V_FULL,
    "style")

add("Meromorphic.deriv",
    "`Meromorphic.deriv` is not `protected`, although its short name clashes with `_root_.deriv` when the namespace is open (the PR itself must write `_root_.deriv` in `fun_deriv`, `iterated_deriv` and `fun_iterated_deriv` right after it), and its siblings `MeromorphicAt.deriv` and `MeromorphicOn.deriv` are both `protected theorem`.",
    "Declare it `protected`: `@[fun_prop] protected lemma deriv [CompleteSpace E] (hf : Meromorphic f) : Meromorphic (deriv f) := fun x ↦ (hf x).deriv` (as `protected theorem` with the siblings' docstring if preferred).",
    "advisory",
    "Basic.lean:378 `protected theorem deriv` (MeromorphicAt), :562 `protected theorem deriv` (MeromorphicOn); PR lines 721-730 use `_root_.deriv`. `protected theorem deriv` compiles in the verified revision, and `open Meromorphic in example (f : 𝕜 → 𝕜) : deriv f = _root_.deriv f := rfl` compiles with it: " + V_FULL,
    "naming")

add("Meromorphic.sum",
    "`Meromorphic.sum` and `Meromorphic.fun_sum` are stated with `theorem` but carry no docstring, unlike the rest of the PR's undocumented results (all `lemma`) and unlike `MeromorphicAt.sum`/`MeromorphicOn.sum`, which are documented.",
    "Give both the siblings' docstring `/-- Finite sums of meromorphic functions are meromorphic. -/`, or turn them into `lemma`.",
    "advisory",
    "Basic.lean:663-670 (PR); siblings at :142-160 and :520-529 carry `/-- Finite sums of meromorphic functions are meromorphic. -/`. Docstrings added in the verified revision: " + V_FULL,
    "style")

add("Meromorphic.prod",
    "`Meromorphic.prod` and `Meromorphic.fun_prod` are stated with `theorem` but carry no docstring, unlike the PR's other undocumented results (all `lemma`) and unlike the documented `MeromorphicAt.prod`/`MeromorphicOn.prod`.",
    "Give both the siblings' docstring `/-- Finite products of meromorphic functions are meromorphic. -/`, or turn them into `lemma`.",
    "advisory",
    "Basic.lean:688-695 (PR); siblings at :122-140 and :508-518. Docstrings added in the verified revision: " + V_FULL,
    "style")

add("Meromorphic.fun_sum",
    "`Meromorphic.fun_sum` is proved by `by simpa [← Finset.sum_apply] using (sum h)` where a one-line term proves it pointwise, as `MeromorphicOn.fun_sum` does.",
    "Replace the proof with `fun x ↦ MeromorphicAt.fun_sum (h · x)`.",
    "advisory",
    "Basic.lean:668-670 (PR); MeromorphicOn.fun_sum at :526-529 is `fun z hz ↦ MeromorphicAt.fun_sum (fun σ ↦ h σ z hz)`. The term compiles in the verified revision: " + V_FULL,
    "proof-golf")

add("Meromorphic.fun_prod",
    "`Meromorphic.fun_prod` is proved by `by simpa [← Finset.prod_apply] using (prod h)` where a one-line term proves it pointwise, as `MeromorphicOn.fun_prod` does.",
    "Replace the proof with `fun x ↦ MeromorphicAt.fun_prod (h · x)`.",
    "advisory",
    "Basic.lean:693-695 (PR); MeromorphicOn.fun_prod at :515-518 is `fun z hz ↦ MeromorphicAt.fun_prod (fun σ ↦ h σ z hz)`. The term compiles in the verified revision: " + V_FULL,
    "proof-golf")

add("Meromorphic.pow",
    "`Meromorphic.pow` and `Meromorphic.fun_pow` take the exponent as an implicit `{n : ℕ}` before `hf`, while `MeromorphicAt.pow`, `MeromorphicOn.pow` (and `AnalyticAt.pow`, `Continuous.pow`) take it explicitly after the hypothesis, so `hf.pow n` works for the siblings but not here.",
    "Make the exponent explicit after the hypothesis: `lemma pow {f : 𝕜 → 𝕜} (hf : Meromorphic f) (n : ℕ) : Meromorphic (f ^ n) := fun x ↦ (hf x).pow n` and `lemma fun_pow ... (hf : Meromorphic f) (n : ℕ) : Meromorphic (fun x ↦ f x ^ n) := hf.pow n`.",
    "advisory",
    "Basic.lean:307 `lemma pow {f : 𝕜 → 𝕜} (hf : MeromorphicAt f x) (n : ℕ)`, :547 `lemma pow (n : ℕ)`; PR :706-709 `{n : ℕ}`. Explicit-n version (with `@[fun_prop]`) compiles, and `fun_prop` still proves `Meromorphic (fun x ↦ (f x)⁻¹ + 3 * x ^ 2)`: " + V_FULL,
    "style")

add("Meromorphic.zpow",
    "`Meromorphic.zpow` and `Meromorphic.fun_zpow` take the exponent as an implicit `{n : ℤ}`, while `MeromorphicAt.zpow` and `MeromorphicOn.zpow` take `(n : ℤ)` explicitly after the hypothesis.",
    "Make the exponent explicit after the hypothesis: `lemma zpow {f : 𝕜 → 𝕜} (hf : Meromorphic f) (n : ℤ) : Meromorphic (f ^ n) := fun x ↦ (hf x).zpow n`, `fun_zpow ... (n : ℤ) ... := hf.zpow n`.",
    "advisory",
    "Basic.lean:320 `lemma zpow {f : 𝕜 → 𝕜} (hf : MeromorphicAt f x) (n : ℤ)`, :553 `lemma zpow (n : ℤ)`; PR :712-715 `{n : ℤ}`. Explicit version compiles in the verified revision: " + V_FULL,
    "style")

add("Meromorphic.mul",
    "The binders `{f g : 𝕜 → 𝕜}` are repeated in `mul`, `fun_mul`, `div`, `fun_div` and `{f : 𝕜 → 𝕜}` in `pow`, `fun_pow`, `zpow`, `fun_zpow` (eight consecutive signatures, shadowing the block's `{f g : 𝕜 → E}`), instead of being declared once as `MeromorphicOn` does with `variable {s t : 𝕜 → 𝕜}`.",
    "Group the 𝕜-valued lemmas in a `section` opened with `variable {f g : 𝕜 → 𝕜}` (or add `{u v : 𝕜 → 𝕜}` to the namespace's `variable` block) and drop the per-lemma `{f g : 𝕜 → 𝕜}`/`{f : 𝕜 → 𝕜}` binders.",
    "advisory",
    "PR lines 681-715; Basic.lean:428 `variable {s t : 𝕜 → 𝕜} {f g : 𝕜 → E}` in MeromorphicOn. A `section Field` / `variable {f g : 𝕜 → 𝕜}` version compiles with no warnings: " + V_FULL,
    "style")

add("Mathlib/Analysis/Meromorphic/Basic.lean",
    "The module docstring's 'Main statements' list still names only `MeromorphicAt` and `MeromorphicAt.iff_eventuallyEq_zpow_smul_analyticAt`; it omits the new main definition `Meromorphic` (and the existing `MeromorphicOn`).",
    "Add entries such as `* `MeromorphicOn`: meromorphy on a set` and `* `Meromorphic`: meromorphy at every point of `𝕜`` to the module docstring.",
    "advisory",
    "file_read Basic.lean:12-21: module doc lists `MeromorphicAt` and `MeromorphicAt.iff_eventuallyEq_zpow_smul_analyticAt` only.",
    "documentation")

add("Meromorphic",
    "The new predicate is not applied where the same file spells it by hand: `MeromorphicOn.countable_compl_analyticAt` and `MeromorphicOn.measurable` take `(h : MeromorphicOn f Set.univ)`, which is exactly `Meromorphic f` (and the library has ~30 more such hypotheses, e.g. `MeromorphicOn.Gamma : MeromorphicOn Gamma univ` and the ValueDistribution files).",
    "Move `Meromorphic` and `meromorphicOn_univ` above those lemmas and add `Meromorphic.countable_compl_analyticAt` / `Meromorphic.measurable` taking `(h : Meromorphic f)` (deprecating or re-proving the `MeromorphicOn f Set.univ` versions from them); replace the remaining `MeromorphicOn f univ` hypotheses in a follow-up PR, as planned on Zulip.",
    "advisory",
    "file_read Basic.lean:614-631 (`(h : MeromorphicOn f Set.univ)` in both). content_search for `MeromorphicOn ... (Set.)?univ` over target/Mathlib: 6 files, incl. Meromorphic/Complex.lean:23, Complex/ValueDistribution/{CountingFunction,CharacteristicFunction,ProximityFunction,FirstMainTheorem}.lean. zulip_search: the author proposed to 'replace all instances of `MeromorphicOn f Set.univ` by `Meromorphic f`'; Jireh Loreaux suggested doing so in separate PRs.",
    "scope")

add("Meromorphic.prod",
    "`Meromorphic.prod` (and `Meromorphic.sum`, `fun_prod`, `fun_sum`) assume every member of the family is meromorphic (`h : ∀ σ, Meromorphic (F σ)`), but only the indices in `s` are needed.",
    "Weaken the hypothesis to `h : ∀ σ ∈ s, Meromorphic (F σ)`, proving e.g. `rw [← Finset.prod_attach]; exact fun x ↦ MeromorphicAt.prod (fun σ ↦ h σ σ.2 x)` (likewise `Finset.sum_attach` for `sum`), and derive `fun_prod`/`fun_sum` from them.",
    "advisory",
    "lean_verify_edit replacing PR lines 663-695 with `theorem sum (h : ∀ σ ∈ s, Meromorphic (G σ)) ... := by rw [← Finset.sum_attach]; exact fun x ↦ MeromorphicAt.sum (fun σ ↦ h σ σ.2 x)`, the analogous `prod`, and `fun_sum`/`fun_prod` via `simpa [← Finset.sum_apply] using sum h` -> outcome compiled, no errors, no warnings. precedent_search: on PR #30587 (same file) eric-wieser suggested `theorem prod (h : ∀ σ ∈ s, MeromorphicAt (F σ) x)` 'would be a stronger result'.",
    "generalization")

for f in F:
    f.pop("family")
json.dump(F, open(D + "/findings.json", "w"), ensure_ascii=False, indent=1)
print(len(F))
