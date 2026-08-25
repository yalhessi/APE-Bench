# The Verifiability Rubric for Mathlib Review Findings (Step 3)

*v1, 2026-06-12. Rubric drafted from, and applied to, all 204 round-1 gold comments in
`inputs/pr_review_v2/mathlib_pr_review_v2_2025-09-01_to_2025-12-31_20260612102315.jsonl`
(137 PRs + 1, closed 2025-12; extract validated by the Step-2 audit). Annotations:
`inputs/pr_review_v2/annotations/stratum_round1_v1.jsonl` — single-annotator LLM first pass,
**pending spot-validation** (§6). Apply/report tool: `python -m src.datasets.pr_review_v2.annotate`.*

## 1. The question the rubric operationalizes

For each maintainer comment: **what kind of procedure could decide whether the concern is
valid?** Four strata, ordered by decreasing mechanizability, plus two non-finding tags.

| Tag | Name | Operational test |
|---|---|---|
| **V1** | Already decided | An oracle that *already runs* (compiler, CI, existing linters, mechanical greps: axioms, `sorry`, line length, unused binders) decides the claim. |
| **V2** | Checkable by computation | A terminating procedure using the Lean toolchain/library **on this instance** verifies the claim: the supplied/implied alternative compiles (golf, restatement, generalization), a search exhibits a duplicate (`exact?`, Loogle), removal of allegedly-unused code still builds, generated names can be produced and compared. |
| **V3** | Codifiable convention | The claim instantiates a **general rule statable without this PR's mathematical content** — naming conventions, formatting/indentation, docstring presence/format, simp-normal-form orientation, `protected abbrev` idioms, API-completeness patterns (companion `simp` lemmas, `Full`/`Faithful` instances), PR-metadata requirements. Enforceable in principle as a linter/checklist, whether or not one exists today. |
| **V4** | Genuine preference | Neither computation nor a statable rule decides it: design choices between workable alternatives, "is this wanted," scope-splitting judgment, readability taste, naming debates the community itself puts to a vote. |
| **P** | Process/meta (non-finding) | bors/`maintainer merge`/`!bench` commands, delegation, CI restarts, praise, moderation, pings, links. |
| **Q** | Pure question (non-finding) | Information-seeking with no implied change ("why does this use `isBinder := true`?"). If the thread reveals an underlying concern, classify that concern instead. |

**Tie-breaks.**
- *V2 vs V3*: if a general rule decides it → V3 ("rename for consistency with
  `continuousWithinAt_of_notMem_closure`", 33065); if only instance-level computation decides
  it → V2 ("this duplicates `whiskeringLeft`", 33201). A rename whose target is dictated by
  convention is V3 even though checking it involves computation.
- *V3 vs V4*: ask "could a linter with full context decide this without a human?" Name
  violates the naming scheme → V3; "I couldn't guess what this name means" → V4 (33395).
- *Suggestion blocks classify by underlying claim*, not by delivery: a ```suggestion``` block
  may carry a golf (V2), a rename (V3), or a docstring rewrite (V3).
- *Mixed comments*: classify the dominant actionable claim; process tokens inside an
  otherwise substantive comment are ignored (the 33305 "bors r- … line too long" comment is
  V1 for the CI finding).

**Severity** (per comment): **blocking** = a change to the PR the author was expected to
apply before merge (imperative or suggestion, not explicitly waived); **advisory** =
explicitly optional, "pre-existing:", out-of-scope notes, future-PR material, "I don't want
to block on this" (33283). P/Q carry no severity.

## 2. Worked examples (one per recurring family)

| Family | Example (PR/comment) | Stratum |
|---|---|---|
| CI/lint finding | "There's a line that's too long" + CI link (33305) | V1 |
| Policy mechanicals | "you have introduced 4× as many axioms as all of Mathlib" (33200) | V1 |
| Golf, fix supplied | "here's an even better golf" + suggestion (33285) | V2 |
| Use-existing/duplicate | "Mathlib already has Parseval's identity. Please use that" (33149) | V2 |
| Generalization | "Is this not something very general that should exist as a lemma?" (33421) | V2 |
| Unused in PR | "you're not using it for this PR, right?" (33376) | V2 |
| Simplification verified by reviewer | "make `ShiftedHom` an abbrev … I have tried this" (33302) | V2 |
| Naming convention | "call this `continuousWithinAt_of_not_accPt` … consistent with …" (33065) | V3 |
| Style guide | "otherwise style guidelines would require to indent…" (33098) | V3 |
| Docstring | "(Please add the missing doc-string, though.)" (33156) | V3 |
| API-completeness pattern | "Please add the corresponding `Full` and `Faithful` instances" (33201) | V3 |
| PR metadata | "Could you add a description to the PR message?" (31342) | V3 |
| Design judgment | "we should refactor `LinearMap.range`/`ker` … ask on Zulip" (33107) | V4 |
| Community vote | "I think there should be a Zulip vote for this" (33056) | V4 |
| Scope judgment | "maybe they can be left to another PR" (33328) | V4 |

## 3. Results: stratum distribution (n = 204 comments, 153 findings)

Non-findings: **P = 40** (19.6% of comments), **Q = 11** (5.4%).

| Stratum | n | % of findings | blocking | advisory | blocking share |
|---|---:|---:|---:|---:|---:|
| V1 | 7 | 4.6% | 7 | 0 | 100% |
| V2 | 67 | **43.8%** | 60 | 7 | 89.6% |
| V3 | 60 | **39.2%** | 49 | 11 | 81.7% |
| V4 | 19 | 12.4% | 7 | 12 | 36.8% |

**Headline: V1+V2+V3 = 87.6% of findings are mechanically decided, computation-checkable,
or rule-codifiable. Only 12.4% are genuine preference.**

Within V2, the dominant sub-families (from annotation notes): supplied golfs/proof
rewrites (~25), statement/signature reformulations (~18), duplication / use-existing
pointers (~10), tooling/attribute corrections (~6), generalizations (~4), unused-code
removals (~4). 107/153 findings carry outcome-validated linkage to the resolving edit.

Two further observations with research value:

1. **Severity tracks verifiability.** Blocking share falls monotonically V1→V4. Maintainers
   block on what they can defend mechanically; preference comments are usually offered, not
   imposed. This independently corroborates the rubric's ordering and previews the
   D2-evaluation asymmetry: a reviewer that nails V1–V3 captures ~94% of blocking findings
   (116/123 blocking findings are V1–V3).
2. **V4 has a behavioral signature: escalation.** In 5 of 19 V4 findings the reviewer
   *themselves* routed the question to a Zulip poll, vote, or second opinion (33056, 33198,
   33107, 33065, 33333). The community already treats the preference residual as requiring
   aggregation — almost a direct empirical echo of Project C's framing.
3. **The two AI-authored PR rejections in the window (33149, 33200) were rejected on V1/V2
   grounds** — axioms, sorries, size, duplicating existing results — not on taste. The
   mechanical strata are exactly where current AI contributions fail.

## 4. Gate decision (per `step-by-step.md` Step 3)

The distribution is **V2+V3-heavy (83%)** → **D2 (findings) + D3 (revision spec) with
verification is the primary task definition**, and the speculative/proof-carrying-review
direction (Project B) is the indicated method: nearly half of all findings (V2) are claims
whose validity is *demonstrated by constructing the fix* — which is literally how Mathlib
reviewers deliver them (```suggestion``` blocks). The distributional-verdict framing
(Project C) is scoped to the small V4 residual, where the escalation signature gives a
natural gold signal.

Checker priorities implied by the V2 sub-family counts, in order of coverage:
1. **Speculative golf/restatement** (compile the suggested alternative) — ~⅔ of V2 arrives
   with the fix already written, so the checker is "apply and build."
2. **Duplication / use-existing** (`exact?`/Loogle over the pinned workspace).
3. **Unused-in-PR detection** (remove and rebuild).
4. **Speculative generalization** (fewer instances than expected in this window — revisit on
   a larger sample before downgrading its priority).

## 5. Caveats

- **Single-annotator LLM first pass.** All 204 labels were assigned by one pass (tagged
  `claude-fable-5/first-pass` in the sidecar). The Step-3 protocol requires the researcher
  to spot-validate a stratified sample (§6) before any number is frozen for a paper.
- Comments were classified from bodies truncated at 400 chars; ~15 long comments may hide
  secondary concerns.
- The population is *comments on PRs that received comments*, closed Dec 2025, after the
  Step-2 funnel (10–800 changed lines, ≤30 files); approval-without-comment PRs (the
  merge-ready control class) contribute no comments by construction.
- Severity for unlinked, question-phrased comments defaults to advisory; linkage evidence
  was used as a supporting signal, not a rule.
- One window, 138 PRs. The V2-internal mix (golf-heavy) may reflect December's review
  culture (e.g., the `grind`-adoption wave visible in 33098); re-run on a second window
  before claiming stability.

## 6. Validation protocol (next action for the researcher)

1. Take a stratified sample of ~40: 10 per stratum (all 7 V1 + 3 borderline), drawn with
   the sidecar `note` hidden.
2. Re-classify independently using §1's tests; compute agreement with the first pass.
3. Disagreements adjudicate the *rubric text* first (tighten the tie-breaks), the labels
   second; bump the sidecar to `v2` with an `annotator: human-validated` tag on corrected
   rows.
4. Agreement ≥80% on strata → freeze the distribution for the write-up; below that, the
   V2/V3 boundary is the likely culprit (see tie-break 1) and the rubric needs a revision
   pass before scaling to a second window.
