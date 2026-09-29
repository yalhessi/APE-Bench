# Review notes: PR #41280 (C^n smoothness of `e.symmL` as a section of the hom bundle)

Inputs read: `brief.md`, `pr.md`, `model.md`, `diff.patch`. Tools were called only through `./ptool`.
Temporary argument and result files are in `tmp/`.

## Whole file: `Mathlib/Geometry/Manifold/VectorBundle/Hom.lean`
- `lean_verify_edit` with no edit: the file compiles as the PR leaves it, with no errors or warnings.
- `file_read` of lines 1-260 for context. The file's variable blocks use `{n : WithTop ℕ∞}` and
  `Trivialization F₁ (π F₁ E₁)`, and its statements use `CMDiffAt`/`CMDiff[s]` notation.
- `ℕ∞ω` is the common spelling elsewhere in Geometry/Manifold. It is scoped to `ContDiff`, which
  Hom.lean does not open, and the file's own blocks say `WithTop ℕ∞`, so the new block matches the
  file. No finding.
- The new `section symmL` redeclares a whole variable block. That is the file's existing pattern:
  the section at line 174 does the same, and the earlier section lacks the
  `IsTopologicalAddGroup (E₁ x)` / `ContinuousSMul 𝕜 (E₁ x)` instances. No finding.
- Line lengths: the longest added lines are exactly 100 characters, which is within the limit.

## `Bundle.Trivialization.contMDiffAt_symmL`
- **Hypotheses.** Dropping `[IsManifold IB n B]` still compiles (`lean_verify_edit`, success).
  `contMDiffAt_coordChangeL` and `contMDiffAt_totalSpace` do not need it. This is finding 1,
  blocking.
- **Linter probe.** `#lint only unusedArguments` reports nothing here. Under the module system it
  also missed an obviously unused explicit hypothesis, so the probe settles nothing either way.
- **Notation.** Tried `CMDiffAt n (T% (e.symmL 𝕜)) x`: `T%` fails, finding no `FiberBundle` instance
  on `fun b ↦ F₁ →L[𝕜] E₁ b`. Tried `CMDiffAt n (fun m ↦ TotalSpace.mk' ...)`: fails as a dependent
  function. The explicit `ContMDiffAt IB (IB.prod 𝓘(𝕜, F₁ →L[𝕜] F₁)) n` form is therefore justified,
  and there is no notation finding.
- **`π F₁ E₁`.** Writing `Trivialization F₁ (π F₁ E₁)` in place of the
  `(TotalSpace.proj : TotalSpace F₁ E₁ → B)` ascription compiles and matches line 46. This is
  finding 2, advisory.
- **Proof.**
  - `simp?` shows every supplied simp lemma is used; the reported `simp only` set is the same list
    plus a few default lemmas.
  - A restructured proof also compiles and is not materially shorter: `FiberBundle.mem_baseSet_trivializationAt'`,
    `refine` in place of `apply`, and a single `filter_upwards` on `(e.open_baseSet.inter ...).mem_nhds`.
  - No proof-golf finding.
- **Duplication.** `declaration_search` finds no existing `contMDiffAt_symmL` or `contMDiffOn_symmL`,
  and no `continuousOn_symmL` or `continuousAt_symmL` either.
  - The nearest existing lemmas are `Bundle.Trivialization.contMDiffOn_symm`, which is about
    `e.toOpenPartialHomeomorph.symm`, and `contMDiffAt_section_iff`. Neither states this.
  - The Zulip thread "Trivialization smoothness" has Patrick Massot asking whether this exists
    (June 2026), so it is new. No duplication finding.
- **Naming.** `naming_norm` could not resolve the subject, so naming is unmeasured.
  `contMDiffAt_<fn>` / `contMDiffOn_<fn>` in `Bundle.Trivialization` matches its siblings
  (`contMDiffAt_coordChangeL`, `Trivialization.contMDiffOn_symm`). No finding.
- **Docstring.** It says "a trivialization", but the lemma needs `[MemTrivializationAtlas e]`, and
  the claim is false for trivializations outside the atlas. This is finding 3, advisory.

## `Bundle.Trivialization.contMDiffOn_symmL`
- The proof `fun _ hx ↦ (e.contMDiffAt_symmL hx).contMDiffWithinAt` is idiomatic.
- The same `[IsManifold IB n B]` and `π` points apply: the edit without `IsManifold` and with `π`
  compiles together with the At lemma. They are covered by findings 1 and 2, whose requested change
  names both lemmas.
- Its docstring has the same atlas omission, covered by finding 3.

## The two docstrings and the section commands
- Apart from the atlas point, both docstrings describe the section correctly: it is a section of
  `fun b ↦ F₁ →L[𝕜] E₁ b`, and it is `C^n` at / on `e.baseSet`.
- `section symmL` / `end symmL` are well-formed. No findings.

## Considered and not raised
- **A `ContMDiffWithinAt` version.** It is trivial from the At version.
- **`MDifferentiable` versions.** Not needed.
- **A companion lemma for `continuousLinearMapAt`.** This is the second statement Patrick Massot
  asked for on Zulip. It is a scope extension, not a problem with this PR.
- **Precedent search.** It returned only unrelated hits in this file from PR #26112
  (`fun x =>` versus `↦`); the new code already uses `↦`.
