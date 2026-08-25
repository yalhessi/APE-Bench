# Beyond the Proof Checker: A Maintainer-Reviewer in the Generation Loop

*Research design / ideation doc — v0.2 (2026-06-10). Living document; meant to be argued with and revised.*
*v0.2 pivots on two clarified constraints: (1) **no recruited human annotators** — ground truth comes
from naturally-occurring PR signals; (2) the **primary contribution is a reviewing agent plugged into
generation to produce more merge-ready code**. Built as a follow-up with the APE-Bench authors.*

---

## 0. TL;DR

**Primary claim (the method).**
> **A reviewing agent that emulates a Mathlib maintainer, inserted into the generation loop as an
> iterative critic, produces more *merge-ready* formal-math edits than compile-only feedback —
> measured against what maintainers actually required on real PRs.**

**Why this is a research result and not an engineering tweak (the framing).**
In formal math, correctness is *decidable* — Lean's kernel is a binary oracle — yet maintainers still
send a large fraction of *compiling* contributions back for changes. So the standard
generate→compile→done loop optimizes the wrong target: compilation is necessary but far from
sufficient for merge. Everything maintainers push back on is, by construction, the *residual* beyond
correctness — scope, generality, naming, API design, idiom, deprecation discipline, library
integration. The research question is whether that residual is *learnable and injectable*: can a
reviewer agent carrying Mathlib's standards steer a generator toward it?

**Why we can measure it without annotators (the key enabler).**
The diff between **what the author first pushed and what finally merged** is, by construction, "what
the maintainers required" — revealed preference, no human labeling needed, and **independent of any
LLM judge** (which is what breaks the usual judge-grades-judge circularity). Combined with the actual
maintainer comment text and the community guidelines we've already curated, this gives a natural,
scalable ground-truth substrate.

**The supporting result.** For the loop to be credible, the reviewer must be *good*: show it predicts
the feedback/changes that really happened on held-out PRs (this is where "reviewing as the core
component" lives). The acceptability-gap measurement (compile ≠ merge) is the motivating evidence
that the loop is attacking a real problem.

---

## 1. Where we are today (assets to build on)

**APE-Bench (the published base, arXiv:2504.19110).**
- *Dual verification*: syntactic (Lean compilation at a pinned toolchain/commit) + semantic
  LLM-as-judge over three dimensions — **requirement alignment, scope control, semantic
  correctness** — reported at 89–94% agreement with experts on 64 annotated solutions.
- Task-contract abstraction + APE-Harness; multi-version execute/retrieve services;
  scaffolds: APE-Agent, Claude Code, Codex.
- Headline empirical result: repository-scale proof *engineering* is much harder than theorem
  proving (APE-Bench 24–47% vs miniCTX-mathlib 92–100%).
- **Stated limitations we can exploit (Appendix B):** judges miss incompleteness, file truncation,
  and destructive/over-scope changes; inter-judge calibration is inconsistent on benign
  refactors. *These are precisely "acceptability beyond correctness" failures.*

**The `pr-review` branch (substantial, ~18k LOC) — our head start.**
- `lean_pr_review` task: snapshot-driven schema where **one data point = one maintainer review
  round** (a PR contributes multiple rounds). Carries conversation context, PR-head checkout hints,
  changed files, and the diff applied into a pinned workspace.
- 7-category finding taxonomy: `correctness, requirements_scope, integration_compatibility,
  robustness_performance, tests_ci, documentation_metadata, readability_maintainability`.
- **Evidence-grounded findings**: each finding must anchor to diff locations / referenced files /
  declarations; guide citations alone don't satisfy evidence. (Process-supervision-friendly.)
- Primary metric `review_quality_score = 0.65·decision_accuracy + 0.25·blocking_F1 +
  0.10·advisory_F1 + false-approve penalty`.
- Ground-truth derivation: `merge_ready` from maintainer review states
  (APPROVED/CHANGES_REQUESTED/comment-approval); blocking categories inferred from the round.
- Skill variants: `skilled_pr_review`, `skilled_policy_pr_review` inject curated Mathlib guides
  (`skills/mathlib-pr-review/` has official + reviewer-rewritten style/naming/PR-review/git guides).
- A companion `pr_split` task (decompose a large PR into mergeable units) — a second, orthogonal
  "maintainer skill."
- `needs_human_review` field already exists → a built-in hook for triage / selective prediction.
- Data pipeline (`src/datasets/pr_review/`) pulls real `leanprover-community/mathlib4` PRs via the
  GitHub API with rich filters; can tag LLM-generated PRs.

**The honest gap in what exists.** The current ground truth is a *heuristic proxy*: `merge_ready`
is read off review state, and blocking categories are *inferred* rather than read from what the
maintainer actually said. That is fine as a v0 signal but is **not yet defensible as a benchmark
label** for a top venue. Fixing label validity is the single highest-leverage research task (§5).

---

## 2. The central research question and three framings

**RQ (umbrella):** *When correctness is decidable, what governs expert acceptance of formal-math
contributions, how well can models predict and satisfy it, and can an acceptability signal be fed
back to improve generation?*

Given the clarified direction, the paper is **Framing B (method-centric)**, motivated by A and
supported by reviewer-quality evidence. A as a standalone is deprioritized (reads as a benchmark
paper); C (the full combination) is the fallback if the loop result turns out weak.

### Framing B (recommended) — "A maintainer-reviewer in the loop produces more merge-ready formal math"
One narrative, three results in priority order:
1. **(Method, headline)** Reviewer-in-the-loop generation beats compile-only feedback on
   merge-readiness, anchored to the real before→merged delta (§5) and APE-Bench dual verification.
2. **(Supporting)** The reviewer is trustworthy: it predicts the feedback/changes that actually
   occurred on held-out PRs better than baselines (T1/T2).
3. **(Motivation)** The acceptability gap is real and large: frontier models *and* the APE-Bench
   semantic judge over-accept compiling code relative to what maintainers required (T3 / E1).

### Framing A — "The Acceptability Gap" (motivation only, not standalone)
Quantify compile ≠ merge; leverages APE-Bench's own admitted judge blind spots (Appendix B). Lives
inside B as the motivating section, not as the paper.

### Framing C — fallback
If E4 (the loop) shows no clean win, fall back to the measurement-heavy combination: gap + reviewer
quality + judge autopsy, with the loop as a "promising but mixed" probe.

**Falsifiable core claim:** *starting from the author's initial PR state, reviewer-in-the-loop
revision lands semantically closer to the merged version (and clears more real maintainer-required
changes) than compile-only revision, at no cost to compilation.*

---

## 3. Why this is novel and ICML-relevant (positioning)

- **AI for formal math is hot, but the field over-indexes on theorem proving** (miniF2F, miniCTX,
  PutnamBench, etc.) where the goal is "find *a* proof that compiles." We pivot to *engineering and
  acceptance* — the bottleneck practitioners actually feel.
- **LLM-as-judge / reward modeling** is a central ICML topic. Our setting gives something rare: a
  *ground-truth correctness oracle that is independent of the judge*. We can therefore cleanly study
  **what judges add beyond the oracle, and where they fail** — a controlled probe of judge validity
  that most domains can't construct.
- **Human-preference learning beyond verifiable rewards.** The RLVR (RL-from-verifiable-rewards) line
  argues "use verifiable signals, avoid noisy human preference." Mathlib is the perfect counterexample
  setting: verifiable reward is *available but insufficient*. We can study what RLVR leaves on the
  table and whether expert-acceptability signal recovers it.
- **Code-review NLP** exists (CodeReviewer/CodeReview, review-comment generation, CriticBench-style
  critique benchmarks) but is on informal code with no correctness oracle and noisy "was the comment
  useful" labels. *No prior code-review benchmark sits on top of a decidable correctness oracle.* That
  is our defensible delta. (⚠ verify exact prior-work claims before submission, §9.)
- **Real-world impact hook:** Mathlib's review queue is a genuine, growing bottleneck (and now faces
  an influx of LLM-generated PRs). A reviewer/triage system is motivated, not contrived.

---

## 4. Proposed task suite (T4 is the headline; T1/T2 make the reviewer believable)

**Priority for this paper: T4 (the loop) is the result. T1/T2 (reviewer quality) is the supporting
evidence that makes T4 credible. T3 (the gap) is the motivation. T5 is optional/impact.**

### T1 — Merge-readiness review (the core; exists, needs hardening)
Input: PR snapshot at a review round (diff applied into pinned workspace, conversation context,
read-only Lean tooling + retrieval). Output: `merge_ready`, `needs_human_review`,
`decision_confidence`, evidence-grounded blocking/advisory findings.
- Keep evidence anchoring (it enables *faithfulness* analysis, §7).
- Two regimes: **compiles-clean** PRs (the interesting acceptability residual) vs **all** PRs.

### T2 — Issue localization & matching (the harder, more defensible signal)
Instead of (only) category-F1 against derived labels, score whether the model's findings **match the
actual maintainer comments** of that round: align predicted findings ↔ real reviewer comments
(embedding + LLM-match, human-validated on a subset). Metric: comment-level precision/recall + a
"caught the blocking issue" rate. This grounds the benchmark in *what experts actually flagged*.

### T3 — The Acceptability-Gap probe (the scientific core; new)
Controlled set of **compiling** contributions partitioned into *accepted* vs *rejected-for-non-
correctness*. Ask: models, the APE-Bench semantic judge, and humans — how do their accept rates
diverge? Produces the headline figure (the "gap") and the rejection-reason taxonomy.

### T4 — Generate–review–revise (THE headline result)
Two substrates:
- **(a) APE-Bench tasks** (you're already reproducing these): generate edit → compile (oracle) →
  reviewer critiques → revise → repeat. The actual merged commit is the gold target.
- **(b) Real-PR replay** (the stronger, more on-thesis substrate): start from the author's *initial*
  pushed head, run the loop, and ask whether it reaches something closer to *merged* head than
  compile-only does — i.e., does the agent reviewer substitute for the maintainer round?

Treatment = reviewer-in-loop. Controls = compile-only feedback, and reviewer-without-guides.
Primary outcome = merge-readiness (§5 anchors); guard outcomes = scope/diff-size & deletion count
(Goodhart). The reviewer is held *separate* from the metric to avoid grading-yourself (§5).

### T5 — PR triage / selective prediction (impact + calibration; partly exists)
Use `needs_human_review` + `decision_confidence` for a **defer-to-human** policy. Metric:
risk–coverage / selective accuracy; "how much expert time saved at target precision." Directly
addresses the user's motivating pain (slow queue). Also a clean calibration story (ECE, abstention).

*(Optional T6 — PR-split as a maintainer skill: already prototyped; can be an appendix/ablation rather
than a headline, to keep scope sane.)*

---

## 5. Ground truth without annotators: revealed preference from PR traces

We do **not** recruit annotators. Ground truth comes from signals already present in the PR history.
The thesis-critical property: these anchors are **produced by humans and independent of any LLM
judge**, so a "reviewer-in-loop helped" result cannot be an artifact of one LLM agreeing with another.

**The four natural signals:**

1. **Revealed-preference delta (primary anchor).** `Δ = diff(first_pushed_head, merged_head)` is, by
   construction, the set of changes the maintainers caused. It needs no labeling and defines a
   concrete *target* for T4 and a *label* for the reviewer ("did you flag what Δ changed?").
2. **Feedback ↔ commit linkage.** Map each maintainer comment to the author commit(s) that addressed
   it (file/line overlap + temporal order + resolved-thread markers + commit messages). Yields
   (issue, resolving-edit) pairs — supervision for both "what to flag" (T2) and "what a good revision
   looks like" (T4). Self-validating: a thread going quiet/resolved is weak confirmation the edit
   addressed it.
3. **Outcome & process labels.** merged vs closed-unmerged; #rounds; #CHANGES_REQUESTED; time-to-merge
   — difficulty/contentiousness proxies, free from the timeline.
4. **Standards corpus.** Curated community guidelines (already in `skills/mathlib-pr-review/`) **plus**
   a mined rulebook: cluster recurring maintainer comments into de-facto rules. *Deriving the implicit
   rulebook from feedback at scale is itself a contribution and needs no annotators.*

**How metrics use these (anchored, non-circular):**
- *Reviewer quality (T1/T2):* does the predicted finding set match the real maintainer comments / the
  real Δ on **held-out** PRs? (precision/recall over linked comments; "caught the change that Δ made").
- *Merge-readiness in the loop (T4):* **semantic/behavioral proximity to `merged_head`** + count of
  real maintainer-required changes still outstanding + APE-Bench dual verification. Proximity is to
  the human-merged artifact, not to an LLM's opinion.

**Threats specific to revealed-preference labels, and mitigations:**

| Threat | Why it biases | Mitigation |
|---|---|---|
| Δ conflates maintainer-required changes with author's own iteration, rebases, merge-conflict noise | Inflates/dilutes "what review caused" | Attribute commits to feedback via thread linkage (signal 2); strip pure rebases/format-only commits; report results both on full-Δ and feedback-attributed-Δ |
| The merged version is *one* acceptable point, not the only one | Exact-match penalizes valid alternatives | Never string-match: use semantic proximity + dual verification + "does it clear the *specific* issues Δ addressed," allowing different-but-acceptable solutions |
| Some rejections are latent correctness (`sorry`, truncation, deletions) not "taste" | Muddies the compile≠merge claim | Full compile + lint oracle (`shake`, `lint-style`); bucket Δ-changes into correctness/completeness vs taste so the gap claim is about the residual |
| Round verdict/comments leak if shown to the model | Trivializes T1/T2 | Snapshot hygiene: model sees the PR *as the maintainer did*; never that round's verdict — audit the existing snapshot builder |
| Contamination — merged PRs in pretraining | Inflated proximity/scores | **Post-cutoff temporal holdout** (APE-Bench already leans on this); report time-sliced; prefer recent PRs for the headline split |
| Selection bias — we only see PRs that reached review; abandoned-pre-review PRs invisible | Population skew | Scope claims to "PRs that entered maintainer review"; report the filtering funnel explicitly |

**Concrete deliverable:** a *Ground-Truth Construction* section documenting the Δ extraction +
feedback-linkage heuristics, the filtering funnel, and a small **self-consistency audit** (e.g., do
linked edits actually touch the commented lines? what fraction of threads resolve?) in place of an
inter-annotator κ. This is the v0.2 replacement for the recruited-annotator plan.

**De-risk first:** sanity-check signal 1+2 on ~30 PRs by hand (us, not annotators) to confirm the
linkage heuristics are decent before scaling — a few hours, not a recruitment effort.

---

## 6. Experiments & ablations (what would make reviewers believe it)

**E1 — The gap (motivation figure).** On *compiling* PRs, compare accept rates: ground truth
(merged-with-no-further-required-changes) vs frontier models (zero-shot reviewer) vs APE-Bench
semantic judge vs naive "compiles ⇒ merge." Expect large over-acceptance by models/judge → motivates
the loop.

**E2 — Reviewer quality.** T1/T2 on held-out PRs for several frontier models: do predicted findings
match real maintainer comments / the real Δ? Report against the self-consistency audit baseline (§5),
plus calibration (E5). This is the "is the reviewer any good" evidence the loop depends on.

**E3 — What helps a reviewer?** Ablations: ± curated Mathlib guides (we have them as skills),
± retrieval, ± Lean tool access (compile/inspect), ± conversation context, free-form vs
evidence-grounded findings. Hypothesis: *standards-as-context (guides) + grounding* matters more than
raw model size — a tidy, useful finding.

**E4 — Closing the loop (headline).** T4 outcome — proximity-to-merged + real-required-changes-cleared
+ dual verification — across: compile-only feedback vs reviewer-critic vs reviewer-critic + guides.
On the real-PR-replay substrate (4b) the merged head is the independent anchor that rules out
judge-grades-judge gaming. Track diff size / deletions / scope to catch Goodharting (silencing
findings by shrinking or deleting code).

**E5 — Calibration & triage (T5).** ECE, risk–coverage curves, expert-time-saved at fixed precision.

**E6 — Judge autopsy.** Where exactly does the APE-Bench semantic judge over-accept? Map failures to
the rejection-reason taxonomy → directly extends APE-Bench Appendix B with quantified categories.

**Models:** a spread of frontier models (incl. the latest Claude) as reviewers/generators; the
existing APE-Agent/Claude Code/Codex scaffolds give us scaffold controls "for free."

---

## 7. Secondary research threads (pick 1–2 to deepen, not all)

- **Faithfulness of grounded review.** Do required evidence anchors actually correspond to the issue?
  Auto-check that cited diff lines/declarations exist and are relevant → a *grounding-precision*
  metric. Connects to LLM-judge faithfulness literature.
- **Reward hacking under reviewer optimization.** Characterize failure modes when generation is
  optimized against a learned reviewer (scope-shrinking, comment-silencing, over-deletion). A small
  but pointed contribution to the RLVR-vs-preference debate.
- **Longitudinal / next-round prediction.** Predict the *next* maintainer round's feedback from the
  current state — a dynamic task richer than final-outcome, exploiting the multi-round snapshot design.
- **Standards transfer.** Train/prompt a reviewer on Mathlib standards; test zero-shot on another Lean
  library (Carleson/FLT — already in miniCTX subsets) to ask whether "taste" is library-specific.

---

## 8. Mapping to the codebase (what to reuse vs build)

| Need | Reuse | Build/extend |
|---|---|---|
| PR data @ review rounds | `src/datasets/pr_review/` collector | add confound filters; LLM-generated tagging already present |
| Review task + scoring | `pr_review/{core,scoring,findings,models}.py` | swap headline metric → T2 comment-matching; add gold-label path |
| Standards-as-context | `skills/mathlib-pr-review/` (official + reviewer guides) | the E3 guide ablation is basically free |
| Compile + lint oracle | execute service (`toolkits/execute/lean`) | wire `shake`/`lint-style`; separate correctness vs taste bucketing |
| Retrieval ablation | `toolkits/retrieve/lean` | on/off switch for E3 |
| Generate–review–revise (T4) | `proof_engineering` task + scaffolds + reviewer | orchestrate the loop; held-out expert eval harness |
| Triage (T5) | `needs_human_review`, `decision_confidence` | calibration + risk–coverage reporting |
| Expert annotation | — | annotation UI/protocol + reason-code schema (critical path) |

Net: the *engineering* is largely done. The *research* deltas are label validity (§5), the
comment-matching metric (T2), the acceptability-gap probe (T3), and the closed loop (T4).

---

## 9. Risks, open questions, and things to verify

**Research risks**
- *Benchmark-paper perception.* Mitigate by leading with the gap *insight* + the T4 *method*, not the
  leaderboard. ICML wants a claim, not a dataset.
- *Label noise dominates.* If κ is low even among experts, the construct is shaky — run a small
  annotation pilot **before** committing to the framing.
- *Gap might be small / model-dependent.* Pilot E1 on ~50 compiling PRs early to confirm the gap is
  real and large before scaling.
- *Goodharting in T4.* Pre-register the held-out expert eval and scope-change tracking.

**Open questions for you (let's resolve before scaling):**
1. **T4 substrate** — lead with APE-Bench tasks (4a, reuses your reproduction, gold = merged commit)
   or real-PR-replay (4b, more on-thesis, harder plumbing)? I lean: pilot on 4a, headline on 4b.
2. **Reviewer↔generator independence** — to avoid grading-yourself, the in-loop reviewer and the
   metric/judge should differ. Use different models? An ensemble metric? The real-Δ anchor sidesteps
   most of this but we should commit to a protocol.
3. **Generation loop reach** — prompt/critic-loop only, or any RL/finetuning of the generator against
   the reviewer? Loop-only is far cheaper and likely enough for a first paper; RL is a v2.
4. **Mined rulebook scope** — do we invest in *deriving* the implicit Mathlib rulebook from clustered
   feedback (a contribution in itself), or just use the curated guides we already have?
5. **Division of labor with APE-Bench authors** — who owns data pipeline vs reviewer vs eval harness?
   What of theirs (judge, dual-verification, contamination window) do we adopt vs. extend?
6. **Compute/budget & timeline** — target deadline drives #models × #PRs × #loop-iterations.
7. **LLM-generated PRs** — treat AI-authored Mathlib PRs as a first-class subpopulation (timely) or a tag?

**To verify before writing related work (don't trust from memory):**
- Exact claims/coverage of prior code-review datasets/benchmarks (CodeReviewer, CodeReview, CriticBench,
  RealCritic, SWE-bench-review-style work) — confirm none combine review with a correctness oracle.
- Current state of formal-math acceptance/quality work beyond APE-Bench (avoid being scooped).
- Whether APE-Bench II / follow-ups exist (the repo cites "APE-Bench I").

---

## 10. Suggested phasing

- **Phase 0 (days, no recruitment): de-risk.** (a) Hand-check Δ-extraction + feedback↔commit linkage
  on ~30 PRs. (b) E1 mini gap study on ~50 compiling PRs. (c) A *single* T4 loop run end-to-end on a
  handful of APE-Bench tasks. Three gates: are labels usable? is the gap real? does the loop run?
- **Phase 1: substrate.** Δ/feedback-linkage extractor + filtering funnel + self-consistency audit;
  full compile+lint oracle; temporal holdout; reviewer↔metric independence protocol.
- **Phase 2: reviewer quality (supporting).** E2 (T1/T2) + E5 calibration; E6 judge autopsy.
- **Phase 3: the loop (headline).** T4 on 4a then 4b + E4 + E3 ablations (guides/retrieval/tools);
  Goodhart guards.
- **Phase 4: write-up,** related-work verification (§9), reproducibility package.

*Note: reviewer quality (Phase 2) can run in parallel with loop plumbing (Phase 3) — the loop only
needs a "good enough" reviewer to start showing signal.*

---

## Appendix — naming ideas (placeholder)
*MERIT* (Merge-Readiness In formal-math Tasks), *ACCEPT-Bench*, *BeyondCompile*, *TasteBench*,
*MathlibReview*. Decide late.
