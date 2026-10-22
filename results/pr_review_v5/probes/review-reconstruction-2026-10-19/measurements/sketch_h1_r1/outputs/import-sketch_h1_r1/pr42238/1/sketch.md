# Sketch: scope the fourth-ring variables of `LinearIsometry.lean`

`L:n` is a line of `base/Mathlib/Analysis/Normed/Operator/LinearIsometry.lean`; `Sn` is a source in
`decision_context.md`. All Lean is unchecked.

## 1. Scope of the edit
**Choice:** Remove only the fourth-ring data from the file-wide block (L:35-47): `R₄`, `E₄`,
`σ₁₄ σ₄₁ σ₂₄ σ₄₂ σ₃₄ σ₄₃` and their 15 instances. Keep `F`, `𝓕` and the third ring. Do not flip
`trans_assoc` to the `(e₁.trans e₂).trans e₃ = …` form of `LinearEquiv.trans_assoc` (S3), add
attributes, or tidy anything else.
**Alternatives:** also scope `F` with its instances, or the third-ring data; add a sweep for unused binders.
**References:** `F` at L:138, 207, 234, 237, 951, 956; the third ring in `comp` (L:323) and `trans` (L:709); S12 (a separate sweep, #42214).
**What would decide it:** usage (the rest is widely used), plus a profile showing `F` or `R₃` also
costs time. Beyond the fourth ring: open.

## 2. Mechanism
**Choice:** Binders on each theorem, as `LinearMap.comp_assoc` (S1) and
`ContinuousLinearMap.comp_assoc` (S2) do, listing exactly what each theorem uses, so the
`unusedArguments` linter (recalled) guards the list.
**Alternatives:** `variable … in` before each theorem (S6; the file has `variable (R) in`, L:980);
a section per theorem; a `variable` midway through the file (S4), which would keep the data in
scope from L:338 to the end and defeat the goal.
**References:** S1, S2; declaration-local ring binders in this file at L:1083-1085; S8 prefers
per-lemma arguments; S6/S7 concern binder updates, not new variables.
**What would decide it:** maintainer taste; open. One point against `variable … in`: a copied
block before `comp_assoc` would declare σ₄ᵢ and inverse pairs that Lean silently drops, the
over-specification S12 targets.

## 3. Statement of `comp_assoc`
**Choice:**
```lean
theorem comp_assoc {R₄ E₄ : Type*} [Semiring R₄] [SeminormedAddCommGroup E₄] [Module R₄ E₄]
    {σ₁₄ : R →+* R₄} {σ₂₄ : R₂ →+* R₄} {σ₃₄ : R₃ →+* R₄}
    [RingHomCompTriple σ₁₂ σ₂₄ σ₁₄] [RingHomCompTriple σ₂₃ σ₃₄ σ₂₄]
    [RingHomCompTriple σ₁₃ σ₃₄ σ₁₄]
    (f : E₃ →ₛₗᵢ[σ₃₄] E₄) (g : E₂ →ₛₗᵢ[σ₂₃] E₃) (h : E →ₛₗᵢ[σ₁₂] E₂) :
    (f.comp g).comp h = f.comp (g.comp h) :=
  rfl
```
The σ₄ᵢ and the inverse pairs are omitted: `comp` needs only a triple (L:323), so Lean's
inclusion rule (recalled) already leaves them out of the current statement.
**Alternatives:** carry all the fourth-ring data, symmetric with `trans_assoc`; this adds
hypotheses and the linter flags it.
**References:** L:338-340; S1 has the same three triples.
**What would decide it:** `#check @LinearIsometry.comp_assoc` before and after shows the same
hypotheses.

## 4. Statement of `trans_assoc`
**Choice:** The same pattern with all the fourth-ring data. Each `trans` (L:709) needs both triples
of its three rings, and the type `≃ₛₗᵢ` needs both inverse pairs (L:416-417). So the binders are
`{R₄ E₄ : Type*} [Semiring R₄] [SeminormedAddCommGroup E₄] [Module R₄ E₄]`, then `σ₁₄ σ₄₁ σ₂₄ σ₄₂
σ₃₄ σ₄₃`, then the six `RingHomInvPair`s and six fourth-ring `RingHomCompTriple`s of L:40-44 as
instance binders. The three explicit equivalences and the equation stay unchanged.
**Alternatives:** implicit `{re₁₄ : RingHomInvPair σ₁₄ σ₄₁}` as in S3 and L:1056. That changes the
binder kinds.
**References:** L:774-776; S3.
**What would decide it:** the same `#check @…` comparison.

## 5. Argument order
**Choice:** Keep names, hypotheses and explicit arguments. The fourth-ring implicits and instances
now come after the file's variables. Inside the new binders, follow S1/S2: ring and module, then
σ's, then inverse pairs, then triples.
**Alternatives:** keep the exact order. No scoping can do that, because section variables always
come before a declaration's own binders, and `variable … in` adds at the end.
**References:** the users at L:345 and L:784 pass arguments by position or by unification; S11 is
a bare `rw`; there is no `@`-use in `Mathlib/Analysis` (S11 note).
**What would decide it:** an `@`- or named-implicit use elsewhere. As policy this is open, since
nothing is recorded; in practice nothing found breaks.

## 6. Placement
**Choice:** Both theorems stay at L:338 and L:774, beside `instMonoid` and `instGroup`, which use
them.
**Alternatives:** gather both into one end-of-file section with a single fourth-ring `variable`
(S7), with the instances proving `mul_assoc` by `rfl`.
**References:** L:342-347, L:778-785.
**What would decide it:** diff size and locality; moving declarations is beyond the brief.

## 7. Proof and automation
**Choice:** The proofs stay `rfl`; no attributes are added.
**Alternatives:** tag `trans_assoc` `@[simp]`, given S11's porting note.
**References:** L:340, L:776; S11.
**What would decide it:** that is a change of behaviour, so it belongs in a separate PR.

## 8. Evidence
**Choice:** (a) the types are unchanged: dump signatures before and after, or rely on downstream
building untouched; (b) the speed-up: Mathlib's benchmark bot on the PR (recalled), backed by
`set_option profiler` on the file.
**Alternatives:** local `lake build` wall-clock timing only.
**References:** brief §5 (the description measures elaboration time); decision_context §7 (no
earlier measurement of this cost).
**What would decide it:** whether maintainers expect a bench result on `perf` PRs (recalled, not
seen here).
