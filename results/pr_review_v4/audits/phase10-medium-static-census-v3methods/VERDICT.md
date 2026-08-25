# v3 methods: reach more than doubles, and the lint rescope changes nothing

*2026-08-06. Judge-free static census, third methods generation. Two changes: `lint_norm`
was rescoped from one hand-picked rule to a faithful reimplementation of Mathlib's own
text-style linters, and `naming_norm` — the subject-general naming operator built earlier
but never registered — became an executable implementation.*

## Result

| | v1 methods | v2 methods | **v3 methods** |
|---|---:|---:|---:|
| C1 (included) | 15/40 | 20/40 | **20/40** |
| C2 (included) | 5/40 | 8/40 | **13/40** |
| C1 outside dev PR | 9/26 | 14/26 | **14/26** |
| **C2 outside dev PR** | 0/26 | 3/26 | **8/26** |
| distinct PRs outside dev | 0 | 2 | **6** |
| distinct implementations outside dev | 0 | 2 | **3** |
| decision | rejected | authorized | **`authorized_for_paid_smoke`** |

C2 outside the development PR more than doubles, and the PR count triples. All five new
obligations are renames, all reached by `naming_norm.subject_prefix.v1`:

| PR | ask | subject inferred from |
|---|---|---|
| 33145 | rename `Dense.continuous_upperBounds` / `…_lowerBounds` | application head |
| 33294 | rename `isFundamentalSequence_of_isNormal` to dot-notation | application head |
| 33337 | rename `coe_starProjection_eq_isComplProjection` | projection |
| 33337 | rename `orthogonalProjection_coe_eq_linearProjOfIsCompl` → `toLinearMap_…` | coercion ascription |
| 33421 | rename `round_eq'` → `round_eq_div` | application head |

The 33337 coercion-ascription case is the one the frozen `encard`-specific operator could
not see at all; it was the motivating example for building a subject-general rule.

## The lint rescope: a principled scope, and no measured change

The previous `lint_norm.line_length.v1` implemented **one** rule. Mathlib enforces about
nineteen. A single rule chosen because the development PR happened to need it is not a
scope, so the checker was rebuilt as `lint_norm.text_style.v1` — a transcription of
Mathlib's own linters (`scripts/lint-style.py`, `Mathlib/Tactic/Linter/TextBased.lean`, and
the text-decidable rules in `Style.lean`), reporting Mathlib's own error codes:

`ERR_LIN` `ERR_WIN` `ERR_TWS` `ERR_SEM` `ERR_NSP` `ERR_ADN` `ERR_IBY` `ERR_IWH` `ERR_CLN`
`ERR_ARR` `ERR_LAM`

Six rules were deliberately **not** reimplemented (`setOption`, `missingEnd`,
`openClassical`, `show`, `cdotLinter`, `dollarSyntax`) because they need the parse tree —
`$` and `·` occur inside strings and docstrings — and `ERR_IND` because it needs to know
where a declaration begins, which hunk-level change targets do not record. Guessing at
these lexically would cost precision, which is this arm's entire differentiator.

**Effect on the corpus: none.** Eighteen rules over 472 reviewed targets across all 16 PRs
produce exactly one finding — the same long line in PR 33305 the one-rule version found.

That is a substantive result, not a null one. Two calibration measurements explain it:

| corpus | targets | findings |
|---|---:|---:|
| reviewed code (review-time state) | 472 | 1 |
| base code (already merged, CI-linted) | 192 | **0** |

Zero findings on merged Mathlib is the check that the rules are correctly transcribed
rather than silently broken — a rule set that over-fires would light up base code, and the
absence of any `←`/`by`/`where` false positives on 192 real targets is evidence the excusal
cases were ported correctly. Two apparent base findings during development turned out to be
a missing exemption (`Style.lean:441` exempts any line containing `http`, because a URL
cannot be wrapped); adding it took base to zero.

**The structural reason lint reach is capped: Mathlib runs these linters in CI, so by the
time a human reviews a PR the mechanically-detectable style violations are already gone.**
What remains in human style review is, by construction, the residue no linter catches. This
is a sharper version of the `convention-class-reach` finding: it is not that style asks are
merely hard to mechanize, it is that the mechanizable ones are *already* mechanized
upstream and therefore never appear as review comments. A style checker cannot recover the
37 style interventions in the corpus no matter how complete its rule set is.

## What C2 means for `naming_norm`, and why the number is weaker than it looks

`naming_norm`'s capability predicate accepts any target whose conclusion has a
high-confidence direct left-hand subject. It does **not** check whether the corpus actually
has a convention for that subject — that needs the snapshot population scan, which is too
expensive for gold-free assessment and is done by the runner instead.

So its C2 is a broader claim than the other implementations': 66 supported assessments
across 11 PRs, versus 1 for `lint_norm` and 19 for `repository_policy`, whose predicates are
near-exact. Two consequences:

- **C2 for `naming_norm` means "the shape is in scope", not "a rename would be proposed."**
  The `MIN_SUPPORT=20` / `MIN_SUPPORT_RATIO=0.80` / `MAX_CONFLICT_RATIO=0.05` filter runs at
  execution time, and a subject with no strong norm yields `checked_no_opportunity`.
- **Assessment-level control firing is no longer zero** for the new implementations:
  `naming_norm` is supported on 2 targets in control PR 33438. This does not by itself break
  control safety — `baseline_failure` has always been supported on all three controls (26
  assessments) without producing candidates — but it does mean the control-safety property
  can no longer be read off the census. It has to be measured at the executor.

That measurement has since been made, in
`audits/phase10-medium-executor-v3.2/VERDICT.md`, and it settles both points:

- **Control safety holds** — the arm produced **zero** opportunities on all three control
  PRs, including from `naming_norm`, whose norm-strength filter rejected both control
  targets its predicate had accepted.
- **C2 overstates `naming_norm`'s reach by about 4×** — 8 C2 obligations outside the dev PR,
  but **2** actual opportunities, both on PR 33145. Every other C2 target had a subject with
  no strong norm in the snapshot.

So the C2 column above is a **shape-coverage** number for `naming_norm`, not a reach number,
and the two are not comparable across implementations. The gate's conclusion is unaffected —
it was already cleared on `lint_norm` and `repository_policy`, whose predicates are
near-exact — but the metric needs repair before it can carry weight again. The fix is a
precomputed per-snapshot subject-norm index carried as a release artifact, letting the
predicate ask whether a strong norm exists for this subject cheaply and gold-free.

## Registry versions

| registry | was | now |
|---|---|---|
| methods | `systematic-opportunity-methods/2` | `systematic-opportunity-methods/3` |
| implementations | `implementation-capability-registry/2` | `implementation-capability-registry/3` |
| contracts | `method-expression-contracts/2` | `method-expression-contracts/3` |
| annotation protocol | `obligation-expression-class/3` | unchanged |

The annotation protocol is unchanged, so the three columns above are directly comparable:
only the methods moved. `lint_norm.line_length.v1` no longer exists; the v2 census remains
valid under registry /2 and stays at `phase10-medium-static-census-v2methods`.

Execution order is now declared once in `method_registry.EXECUTION_ORDER` rather than
duplicated between the registry and its validator, which is what let a seventh method be
added without the two drifting.

## Provenance

- Treatment: `inputs/pr_review_v4/treatments/systematic-opportunities-v3-medium`
- Census: `results/pr_review_v4/audits/phase10-medium-static-census-v3methods`
- 2,253 capability assessments (up from 2,041), 533 supported, 0 failed
