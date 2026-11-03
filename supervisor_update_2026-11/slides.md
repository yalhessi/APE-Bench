---
marp: true
theme: default
paginate: true
size: 16:9
math: katex
style: |
  section {
    font-size: 28px;
    padding: 48px 64px;
    line-height: 1.35;
  }
  section.lead h1 { font-size: 52px; }
  section.lead h2 { font-size: 30px; font-weight: normal; color: #555; }
  section.section-title { background: #1d2b53; color: white; }
  section.section-title h1 { color: white; font-size: 56px; }
  section.section-title p { color: #c7d0e8; font-size: 28px; }
  h1 { font-size: 40px; color: #1d2b53; margin-bottom: 18px; }
  h2 { font-size: 30px; color: #1d2b53; }
  table { font-size: 24px; }
  section.tbl table { font-size: 22px; }
  section.dense { font-size: 22px; }
  section.dense table { font-size: 19px; }
  section.dense h1 { font-size: 34px; margin-bottom: 10px; }
  section.dense li { margin: 2px 0; }
  .source { color: #666; font-size: 18px; margin-top: 12px; }
  .flow { display: flex; align-items: stretch; gap: 12px; margin: 24px 0; }
  .flow .box { flex: 1; font-size: 24px; }
  .flow .arrow { align-self: center; font-size: 30px; color: #1d2b53; }
  blockquote { border-left: 6px solid #e0a020; background: #fff8e6; padding: 8px 18px; font-style: normal; }
  pre { font-size: 20px; }
  .cols { display: grid; grid-template-columns: 1fr 1fr; gap: 32px; }
  .cols3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 24px; }
  .box { border: 2px solid #1d2b53; border-radius: 10px; padding: 12px 18px; }
  .take { border-left: 6px solid #1d2b53; background: #f3f5fa; padding: 10px 18px; margin-top: 18px; font-size: 26px; }
  .muted { color: #666; font-size: 22px; }
  .panel { border: 2px solid #d6dcea; border-radius: 12px; padding: 10px 16px; }
  .panel h2 { font-size: 26px; margin: 0 0 6px; }
  .panel pre { font-size: 18px; margin: 6px 0; }
  section.formulation pre { font-size: 16.5px; line-height: 1.32; }
  section.formulation.lg pre { font-size: 21px; line-height: 1.4; }
  section.formulation h1 { font-size: 36px; margin-bottom: 10px; }
  section.formulation .take { font-size: 22px; margin-top: 10px; }
  section.rules { font-size: 22px; }
  section.rules h1 { font-size: 36px; }
  section.rules .katex-display { margin: 6px 0; }
  section.rules .katex { font-size: 1.02em; }
  section.rules .take { font-size: 22px; margin-top: 10px; }
  .above { color: #1a7f37; font-weight: bold; }
  .below { color: #b3261e; font-weight: bold; }
  footer { font-size: 16px; color: #888; }
footer: "Mathlib PR review · Supervisor update · 4 November 2026"
---

<!-- _class: lead -->
<!-- _paginate: false -->
<!-- _footer: "" -->

# Reviewing Mathlib PRs: conventions and review decisions

## Supervisor update · 4 November 2026

**Yousef Alhessi** · University of Edinburgh

<!--
Fresh copy of the October update. This pass updates the empirical account through the
26 October experiments and 27 October assessment. The theoretical formulation is retained
for a second pass. Sources and qualifications for the new material are in evidence.md.
-->

---

<!-- _class: section-title -->

# 1 · The problem

What are we actually asking a reviewer to do?

---

<!-- _class: formulation lg -->

# The shared pieces

```text
Library     L = (C, P)          code C, and a purpose P        P is constant across years
PR          (δ, p)              a diff δ, and a purpose p      what this change is for

merge(C, δ)                     the code after δ               defined iff the patch applies
merge(C, δ) compiles            the kernel accepts it
δ realises p in C               the diff does what p says      decided by a judge

S(C, p)  =  { δ : merge(C, δ) compiles  ∧  δ realises p in C }      the solutions of a task
```

<div class="take">

Merging and compiling act on code; P stays fixed. Both tasks live in S; they differ in what is given and what is emitted.

</div>

---

<!-- _class: formulation lg -->

# APE-Bench

```text
given        (C_b, p)            p stated as an instruction, cut from a real commit
emit         δ
correct iff  δ ∈ S(C_b, p)       the kernel decides "compiles", a judge decides "realises"
```

<div class="take">

The specification is in the input. The performer's whole job is reaching S.

</div>

<!--
The paper (arXiv 2504.19110, Sections 3 and 4.1) gives this in prose: instruction, pinned
environment, boundaries, verification protocol; "compilation plus semantic validation". Best
evaluated agent: 47 of 100 tasks.
-->

---

<!-- _class: formulation -->

# Reviewing

```text
given        (C_b, δ, p)                          P in the background
emit         D, a set of requests

Preference   ≽_t  on S(C_b, p)                    P evaluated at the current code · unstated · drifts
Acceptable   A_t  ⊆ S(C_b, p)                     the region ≽_t does not require leaving

a request    a test on revised PRs: the submitted δ fails it, revisions ≽_t favours pass it
             witness?   one revision that passes it, compiles, and still realises p        kernel-checkable

correct iff  sound:     every test in D is one the community would set
             complete:  if δ ∉ A_t, some test in D is passed by every revision in A_t
merge   iff  δ ∈ A_t             next base (merge(C_b, δ), P)      one round: δ_{i+1} = author(C_b, p, δ_i, D_i)
```

<div class="take">

The specification is not in the input. Review predicts an unstated, drifting standard whose samples come from its own members.

</div>

<!--
From the 22 September session, with the purpose line from its last reply. The target is a preorder
over the solutions of this task, so legacy code is never asked to satisfy the standard. P is stable;
the preference drifts because the state it is evaluated against changes.
-->

---

# The formulation on four PRs

| PR | what the review said | in the formulation |
|---|---|---|
| **#33149** | three vacuous definitions; 19 axioms | δ ∉ S: "realises p" fails. "No axioms" is a test every revision in A_t passes |
| **#33305** | one doc-comment line too long | δ ∈ S, δ ∉ A_t: one test separates them |
| **#33304** | nothing | δ ∈ A_t: D is empty, correctly |
| **#33098** | make this proof one tactic call | δ ∈ A_t already; one test ≽_t favours, two witnesses (`grind`, `simpa`) |

<div class="take">

Of the convening's 23 tests, 4 separate the PR from A_t. The rest are preferences inside it: placement.

</div>

<!--
All four from the twelve December-2025 PRs in the convening talk. 33305's line was located by neither
reviewer in six runs. On 33098 the maintainer asked for grind, our reviewer chose simpa; both compile;
grind went from 0% of Mathlib files in January 2025 to 14.5% by May 2026.
-->

---

# What a reviewer has to do

1. **Membership.** Is δ in S? The kernel settles "compiles"; "realises p" needs a judge.
2. **Placement.** Where is δ under ≽_t? Judged against the tree, recent practice, and the alternative the reviewer would have written. **The wall.**
3. **Request.** The few tests worth setting: those that cut δ off from A_t, and the preferences that matter. Maintainers under-report on purpose.
4. **Update.** Merging moves C, so ≽_t moves; P does not.

<!--
The author's turn is the inverse: resample S subject to the tests until a draw lands in A_t. The Δ dead
end reads correctly here: the author's next draw is one point on the passing side and does not identify
the tests. Placement is where the agent fails: most gold sites had a candidate, and it cannot rank its
draws under ≽_t.
-->

---

# What the formulation does not settle

- **≽_t is never observed.** Each review is one sample of it, and partly constitutes it.
- **A_t is seen only through merges.** The gold is a lower bound.
- **Two witnesses in A_t** have no adjudicator yet.

<div class="take">

The task: from (C_b, δ, p) alone, emit the tests the community would set, with witnesses. Score soundness and completeness against the one sample on record.

</div>

---

<!-- _class: section-title -->

# 2 · The design space

What review systems have in common, and where they part

---

<!-- _class: dense -->

# The question each published formulation answers

| work | the question | in the formulation |
|---|---|---|
| MathlibPR | Is this PR merge-ready? | δ ∈ A_t ? |
| Tricorder, BitsAI-CR, AutoCommenter | Which written rules does it break? | which tests from the written part of ≽_t δ fails |
| Qodo, Greptile, Semgrep | Where does it depart from what we accepted lately? | tests read off recent points of ≽_t |
| ProofJudge | Of these two versions, which would the maintainer take? | ≽_t on a given pair (δ, δ'') |
| c-CRAB; resolution rates | Did the author act on the comment? | δ_{i+1} passes the test |
| SWR-Bench, SWE-PRBench, **ours** | What would the reviewer ask for? | the tests the community would set on δ, with witnesses |

<div class="take">

Only the last asks for the tests themselves. The others ask what an answer key can settle: membership, a written rule, a given pair, an outcome.

</div>

<!--
MathlibPR: models and agents cannot separate merge-ready from build-passing PRs. ProofJudge: recovers
reviewer preference on 63.5-80.8% of 218 before/after pairs. Sources in
docs/research/code-review-systems-survey-2026-09.md.
-->

---

<!-- _class: tbl -->

# What the literature suggests testing

| point | evidence | for us |
|---|---|---|
| **General guidelines alone can be insufficient.** | guidelines in the prompt: Atlassian +5% | test more specific, usable knowledge |
| **Evidence shows a finding is true, not wanted. Many evidenced findings; few get acted on.** | Atlassian: 4% of comments match a human one, 38.7% get resolved; a truth check did nothing, a gate trained on 50k resolved comments +15–20pp | evidence shows only the checkable part of ≽_t, which the kernel gives us free; nothing on record shows the rest |
| **Diversity can buy recall; voting can lose it.** | aggregating reviews +44% F1; an ensemble's union +83%; majority vote a "popularity trap" | measure union recall alongside comment burden |
| **Decomposition can lose recall.** | Di Biase: decomposed diffs found no more defects; Alibaba's file grouping cut recall 20% → 12.7% | compare each decomposition with a solo reviewer |
| **Restraint can suppress findings.** | Cursor needed "aggressive" prompts once restraint made it quiet | test the filing contract and measure output burden |

<!--
Sources: RovoDev, Atlassian (2601.01129); open-code-review's commit history (the filter fix, the grouping
regression); SWR-Bench (2509.01494); LLM ensembles for code (2510.21513); Di Biase et al. (1805.10978);
Cursor's Bugbot write-up. Our own evidence on each point is the last slide of Part 3.
-->

---

<!-- _class: section-title -->

# 3 · What we did, and where we stand

Historical baselines, then the convention experiments

---

# The thesis, and the baseline

<div class="box">

**Understand the review process, then decompose it.** That is what can make a harness more useful than one agent with tools. So one agent with tools is the baseline, always.

</div>

**The baseline:** one session, the whole PR, the brief, the tools, and compile-my-edit. Its numbers, by model, come with Q2.

**Questions.** Does decomposition beat it? Where do the misses occur? What does the community ask for? Can that knowledge transfer to another PR?

<!--
Instruments built since the convening: validation and test sets 2025-06..2026-03 (50 main + 10 AI
each), 1,000 validation PRs read by two blind readers, six post-cutoff PRs, blind matchers beside
the judge. The Opus row is the hygiene baseline (tools fixed); under the earlier project harness it
read 7, 7.
-->

---

<!-- _footer: "Mathlib PR review · Historical baselines · September–14 October 2026" -->

# Q1 · Decomposition by concern (GPT 5.2, reasoning off)

| held-out 12, three reps each | ten arms + a lead | one agent |
|---|---|---|
| asks hit per run | 7, 5, 6 | 4, 4, 1 |
| hit in all three runs | **5** | 0 |
| findings on the two clean PRs | 3, 4, 5 | **0** |
| billed per run | $14.59 | **$1.90** |

**Why it was a wall.** 21 of 23 asks were located by some run, 13 asked correctly: at the right declaration, the reviewer asked for something else. More structure moved volume, not the ask.

<div class="take">

The wall is what the reviewer concludes at a place it has reached. First suspect: the model's reasoning.

</div>

<!--
The generalist arm made 64 of the 71 matches; the specialists took 37% of spend for 10%; six arms
matched nothing. The admission gate discarded 71-83% of the asks the run had already found. Every
gpt-5.2 call before 30 September ran with reasoning off: 0 reasoning tokens in 2,857 of 2,857 arm
attempts.
-->

---

<!-- _class: dense -->

<!-- _footer: "Mathlib PR review · Historical baselines · September–14 October 2026" -->

# Q2 · Reasoning, harness, or model?

| model | harness | reasoning | dev, of 23 | post-cutoff reach |
|---|---|---|---|---|
| GPT 5.2 | ours | off | 2 | 0.02–0.17 |
| GPT 5.2 | ours · Claude Code · Codex | carried | 2–3 | 0.21 · 0.25 · 0.29 |
| GPT 5.5 | ours · Codex | carried | 3 | 0.31 · 0.25 |
| Opus 4.8 · Opus 5 · Opus 5.5 | ours | on | 3 · 8 · 7–9 | — |
| Opus 5.5 | its own shell | on | 11–12 | 0.47 |
| Qwen3.5-397B, self-hosted | ours | off | 2, 0, 2 | — |
| DeepSeek-V4.1-Flash, self-hosted | ours | off · high, carried | 5 · 8, 6, 9 | — |

- **Reasoning:** GPT 5.2 barely moves (2 → 2–3) though every session now finishes at a third of the cost. DeepSeek: 5 → 8, 6, 9, only with its thinking carried between turns.
- **Harness:** three harnesses with GPT 5.2 held reach the same. Ours costs Opus 5.5 about three asks against its own shell.
- **Model:** Opus 4.8 → 5 → 5.5 is 3 → 8 → 7–12. Not the prompt: Opus on GPT 5.2's exact messages reaches 10.

<!--
dev = twelve held-out PRs, 23 obligations, judge v9. post-cutoff = six PRs created after the Claude
models' cutoff, 16 asks, reach per session by blind matchers. "carried" = reasoning at high effort
with the reasoning items passed back between tool calls; "off" = no reasoning tokens. GPT 5.4 carried
reads 0.19 (ours) and 0.31 (Codex) on post-cutoff. Qwen's one reasoning-high run had its thinking
dropped by our client (defect found 7 October) and is not a reasoning reading.
-->

---

<!-- _footer: "Mathlib PR review · Historical baselines · September–14 October 2026" -->

# Q2 · What the strong model knows that the others lack

Of 67 asks GPT 5.2 never reaches and Opus 5.5 does, the reviewer had visited the object in 63.

| the miss, at a visited declaration | asks |
|---|---|
| a convention or a library mechanism it does not know (`@[to_fun]`, `toLinearMap_`, dot notation) | 25 |
| a compile nobody ran (`positivity`, `simpa`, the old proof, `grind`) | 19 |
| an analogue in the library not compared | 6 |

<div class="take">

This motivated knowledge supply. The newer experiments separate knowing a concern, generating an alternative, and deciding to request it.

</div>

<!--
Phase 1 residual mechanisms, two blind readers over the transcripts; the labels overlap. Only 4 of 67
were never attempted.
-->

---

# Q3 · What does a convention entry tell us?

A census entry describes a recurring concern: a situation and a preferred form.

Turning it into a review request requires more:

1. The rule and its scope describe the community's practice accurately.
2. This PR presents the relevant choice, and the alternative works here.
3. The benefit warrants requesting a change, given competing reasons.

<div class="take">

The October experiments often supplied the first two judgments. The follow-up asks which parts transfer without that assistance.

</div>

<!--
Evidence: E1, E3–E5 in evidence.md. This is a working decomposition of the empirical
problem, not a claim that we have identified the community's decision procedure.
-->

---

# Q3 · The census captures a long tail

**Starting point:** 1,833 first-round asks on 1,000 validation PRs. Two independent model readers summarized the principle behind each ask.

- **About 400 entries** at this grain; the two original readings produced 409 and 407.
- The top 10 cover about a fifth of asks; the top 50 about half.
- On 14 PRs outside the census, an entry describes **39 of 46 asks (85%)**.

<div class="take">

A useful inventory of concerns. Each entry's applicability and priority still need to be established.

</div>

<!--
Evidence: E1. Preserve the original census counts; subsequent merged/codebook views
have different counts (e.g. 399). These are sentences produced by model readers, not
400 independently validated community rules. Readers share a model family.
-->

---

<!-- _class: tbl -->

# Q3 · Supplying the right convention can help

**Conditional test:** choose the entries using the target PR's historical asks, then give them to the reviewer without locations.

| Reviewer | Unbriefed | Exact convention brief |
|---|---:|---:|
| Opus 5.5 | 0.46–0.49 | **0.74** |
| GPT 5.5 | about 0.19 | **0.41** |
| DeepSeek-V4.1-Flash | about 0.22 | **0.44** |
| DeepSeek, with examples and precedence | about 0.22 | **0.64** |

<div class="take">

The supplied knowledge matters. The selection also tells the reviewer which concerns matter on this PR.

</div>

<!--
Evidence: E1; knowledge-transfer-experiment-synthesis section B. In-census ask reach,
within each experiment's original comparison; do not pool the rows. These replace
the October deck's table, which mixed all-ask and in-census reporting views.
The oracle ladder at a known place also showed that a bare sentence often suffices;
examples did not uniformly help. This does not establish autonomous transfer.
-->

---

<!-- _class: tbl -->

# Q4 · Selecting conventions without the asks

| Intervention | Result in the tested comparison |
|---|---|
| Select 25 entries from the diff | Entry selected for 22 of 33 asks; Opus gain about **+0.03** |
| Add guarded rules and pinpoint places | Opus gain **0.00** |
| Add examples and precedence | DeepSeek gain on used validation PRs; **0.00** post-cutoff, **−0.01** dev |
| Same selected resource on Opus | Initial gain about +0.20; dev gains **+0.02–0.09**, intervals include zero |

<div class="take">

Relevant topics reached the reviewer. A reliable improvement on other PRs did not follow.

</div>

<!--
Evidence: E1; synthesis section C and conventions-assessment-2026-10-12.
These are distinct designs and samples, not a common causal estimate. Initial
selection-conditioned gains were followed by broader readings and extra repetitions.
Historical ask recovery is not a label of usefulness for every other finding.
-->

---

<!-- _class: tbl -->

# A positive the earlier summary missed

**GPT 5.5, exact convention supply held fixed:** change the filing instructions to require a disposition and use a request threshold.

| 13 other PRs; one run per condition | Before | After |
|---|---:|---:|
| In-census ask reach, 37 asks | 0.43 | **0.62** |
| Excluding one partly encountered PR, 32 asks | 0.44 | **0.56** |
| Findings per PR | 2.38 | 3.15 |

Seven asks became reached; two more became partial; none was lost.

<div class="take">

Instructions can change requests when the right conventions are supplied. Ask-free transfer remains a separate test.

</div>

<!--
Evidence: E2, generation-suppression stage W, run 6 October and brought back into
the later synthesis. Both matchers agree on the gains. Baseline was from the prior
day; one run per condition; the disposition and filing-bar changes are bundled.
32875 was partly encountered in development, hence the exclusion row. Exact briefs
are still target-ask-derived. Full finding usefulness was not established.
DeepSeek's separate forced-filing contract reached none of 32 previously unreached
asks and increased volume; neither result licenses a model-independent verdict.
-->

---

<!-- _class: tbl -->

# What changed after 14 October: the denominator

**Follow flagged places to merge, then check the rule against code and known fixes.**

| Convention | What the follow-up found |
|---|---|
| Predicate namespaces | **85–97%** of the relevant unasked survivors were not departures under the reconstructed rule; our detector preferred the wrong namespace in many cases |
| Dot-notation calls | **12–13 of 16** checked survivors were genuine departures that merged unasked |
| Primed names | Rewording the rule changed many verdicts; both new readers found only **4 of 6** known fixed departures, below calibration |

<div class="take">

Withdraw the single “≤5% of applicable places” claim. Rule error, scope, attention and genuine unasked departures were mixed together.

</div>

<!--
Evidence: E3. Use the final corrections in RESULTS.md, not the earlier 97% headline.
These are small, selected strata and model readings, not a population error rate.
The primes check failed twice: no stable rate can be reported from it. Survival
alone cannot distinguish conforming code from an unnoticed or tolerated departure.
-->

---

# Does a written rule describe actual practice?

**Six script-checkable rules, 973 PRs; compare authors, reviewers' code, suggestions and the library.**

- Two rule texts were broader than anyone's practice: theorem docstrings and placing term proofs on their own line.
- Several other forms were common, but their departures still mostly merged unasked: **under 2% were asked about**, per departure.
- Near a review comment, **57% of touched declarations changed** whatever they contained. A rewrite is weak evidence that a rule was enforced.

<div class="take">

We need a valid rule, a valid opportunity count, and evidence of the decision. Review silence supplies none of those on its own.

</div>

<!--
Evidence: E4, including review-4 corrections. These six form rules cover only 1.7%
of census asks with principles. Attention is proxied by round-1 comment proximity,
not observed reading. The stricter denominators turn line joins and one-tactic-per-
line into mixed practice; do not repeat the superseded three-versus-two headline.
The broad substantive rules were not tested by these scripts.
-->

---

# Can we recover the reasons behind requests?

The later source readings examined library mechanisms, comparison code and maintainers' stated grounds.

- Reasons include technical facts, generality, readability, practice and cost. Their presence does not establish that taste is a small residual.
- Library evidence sometimes settles a choice; often it supplies ingredients for a comparison that remains open.
- Supplying sources and a candidate can make an alternative get considered without making it the requested change.

<div class="take">

The open empirical question became whether reasons acquired from other PRs improve the choices made in ordinary review.

</div>

<!--
Evidence: E5 and E6. The stated-grounds verdict was corrected to mixed after review:
the favorable test depended on counting technical facts as evidence against taste.
The mechanism-grounds reading supports conditional duplication/cost-benefit reasons,
not a universal preference for library reuse or generated implementations. In the
reconstruction probes source/correspondence gains were model-specific; after the
symlink-search repair Opus considered to_fun but often declined it. Do not pool
those historical runs as though their search tools were identical.
-->

---

<!-- _class: tbl -->

# 23 October · More investigation, same recovery

**Two PRs, three repetitions; 12 preparations feeding 12 final reviews.** Compare ordinary preparation with investigation of conditional reasons, using the same Opus final reviewer.

| Measure | Ordinary preparation | Conditional reasons |
|---|---:|---:|
| Agreed asks recovered, across each paired repetition | **1 of 4** | **1 of 4** |
| Finalized findings, all six reviews per condition | 36 | 30 |
| Preparation + review tokens | 13.4M | 15.5M |

More sources were cited, but a relevant reason was sometimes applied to the wrong choice: `aesop` rule-set membership instead of safe/unsafe status.

<div class="source">No solo arm. All 24 edit checks on one PR failed environmentally; this limits the result. Usefulness labels remain pending.</div>

<!--
Evidence: E7. Each repetition contains one review of each PR; 37352's weaker-
typeclass ask is always reached and the other three raw asks are not. Both matchers
agree. Do not describe four asks as the denominator of a single-PR session.
The missing ELAN_HOME failure was repaired after the experiment. No finding was
lost between submission and finalization. Sources excluded some review channels,
so this is not a complete test of acquiring maintainers' reasons.
-->

---

# 24–25 October · Acquire knowledge before review

**A stronger content test:** six entries acquired from independent earlier sources, checked against reserved cases, repaired, then frozen.

| Arm | Same ordinary whole-PR reviewer receives |
|---|---|
| A | Ordinary inputs and tools |
| B | The same + compact notes |
| C | The same + full conditional notes |

**6 PRs × 3 arms × 3 repetitions = 54 final reviews**, Opus 5.5.

Every treatment review receives the same six entries. No target-specific assertion that a convention applies.

<!--
Evidence: E8 and E9. Compact and full notes are derived from the SAME sources;
arm B is not the old census. Six concerns include namespace, name order, grind
registration, to_additive, generality and simp/iff orientation. Three primary
opportunities plus three contrary targets, on already-used development cases.
Source selection was target-steered and disclosed; date gates and target exclusions
apply. Only generality has both a positive and a contrary whole-PR target under
the same entry. Reserved source checks are specification checks, not a no-note
controlled experiment. Repairs preserved unresolved priorities as uncertainty.
-->

---

<!-- _class: tbl -->

# The bank did not meet the primary requirement

| 54 retained final reviews | A: ordinary | B: compact | C: full |
|---|---:|---:|---:|
| Recovery of **each** primary concern | **0/3** | **0/3** | **0/3** |
| All-ask recovery, 30 asks; mean over reps | 35.6% | 34.4% | 41.1% |
| Finalized findings, 18 reviews per arm | 165 | 158 | 168 |

The required improvement on two primary concerns is absent. All notes were delivered; the primary requests were absent before finalization too.

<div class="take">

Close progression for this bank under the agreed rule. Overall usefulness is still unmeasured: the 491-item panel has no labels.

</div>

<!--
Evidence: E8, exported findings and both canonical matchers. All 54 retained reviews
succeeded; both matchers agree on reached/not-reached in all 270 cells. The primary
row means 0/3 for each of three concerns, including two parallel grind asks counted
as one concern. The +5.5 percentage-point all-ask difference for C is descriptive,
not a demonstrated population gain. The historical references include some later
declined or qualified suggestions. They are not an overall quality measure.
Retained tokens: A 39.49M, B 40.89M, C 43.30M, before acquisition and superseded work.
-->

---

<!-- _class: tbl -->

# What the whole reviews missed

| Primary opportunity | What happened in all nine reviews |
|---|---|
| **Namespace**, #33294 | Weighed hypothesis-namespace names; the intended conclusion-namespace comparison never became a request |
| **Automation**, #33098 | Accepted or simplified accessor proofs; never tried proving them with `grind [definition]` |
| **Generality**, #33421 | Inspected the theorem, but never proposed replacing the incidental numeric constant with a parameter |

<div class="take">

A relevant note can arrive, be read, and still fail to prompt the relevant alternative at an acceptable-looking declaration.

</div>

<!--
Evidence: E8, primary failure sections and observable tool calls. All nine = three
arms times three repetitions for each PR. No hidden reasoning was available;
claims are about delivered notes, requests and recorded actions. E3 mainly taught
registration, not how to discover a proof simplification; E5 sources/application
steps mostly concerned types and assumptions, not numeric constants. These are
specific transfer mismatches, not evidence that the model cannot generalize.
-->

---

<!-- _class: tbl -->

# 26 October · Is focus enough?

**72 sessions:** isolate a declaration and a concern; compare no note with the frozen relevant note, three repetitions, plus sibling cases.

| Target | Without note | With note |
|---|---|---|
| Namespace | Intended form absent in 3/3 | Formulated in **2/3**, declined both |
| Generality | **3/3** construct a generalization; one reached request, one partial | **3/3** construct one; all decline |
| Automation | No target proof by `grind` | Same; the question asks about **registration** |

<div class="take">

Focus can expose an alternative. Generating it and deciding to request it are distinct failures; the automation probe asked a neighboring question.

</div>

<!--
Evidence: E10 and E11. The table describes the target answers; 72 includes siblings
and two automation targets, not 72 independent PRs. Three selected PRs, one model,
three samples per cell; supplied concerns, so this is a conditional diagnostic.
All six generalizations have successful verified-edit records and preserve the
special lemma as a corollary, but they use different parameter domains/statements.
Namespace sibling renames also occurred; historical silence is not a wrong label.
The registered progression rule fails in every case: no autonomous step 2 ran.
-->

---

# Generality: constructed, then declined

**#33421:** a lemma about `2 * fract x = 1`.

**All six focused sessions compiled a generalization**, keeping the original as a corollary.

With the note, all three declined. One compiled essentially the maintainer's form, then wrote:

> “The constant 2 is what the lemma is about.”

The note favored generalizing proof artifacts. The reviewer used that condition to keep the specialization; the maintainer asked for generalization.

<div class="take">

A plausible rule can be too restrictive. Assess the suggestion's value independently.

</div>

<!--
Evidence: E10, generality results and answers; E11's audit. Without the note two
requests were made, one reached and one partial. This is a small conditional
comparison, not a stable causal estimate that notes worsen decisions. Lack of
another caller also appeared as a reason with and without the note. The next
question is whether such reasons distinguish useful additions from avoidable churn,
not how to force agreement with this one historical maintainer.
-->

---

# An exploratory gain still needs a usefulness reading

On **#33000**, the notes arms proposed a `dslope` factorization that removes a manual proof and avoids new derivative imports.

| Request delivered | Ordinary | Compact | Full |
|---|---:|---:|---:|
| `dslope` factorization | 0/3 | **2/3** | **2/3** |

Saved compile records support feasibility. The historical reference does not capture this request.

<div class="take">

The failed primary requirement stands. This is a concrete candidate for assessing useful reviewing beyond historical ask matching.

</div>

<!--
Evidence: E8, exploratory dslope requests in B1/B2/C2/C3. The results assessment
spot-checked compiled records for B1 and C2. This was not preregistered and cannot
replace a missing primary concern. Compare with ordinary reviewers' alternatives
at the same object. A bounded reading can characterize this case; it cannot stand
in for the full panel if an overall usefulness claim is wanted.
-->

---

# What we can now say about conventions

<div class="flow">
<div class="box"><strong>State the choice</strong><br>Rule, scope and competing reasons</div>
<div class="arrow">→</div>
<div class="box"><strong>Find an alternative</strong><br>Instantiate and check it at this object</div>
<div class="arrow">→</div>
<div class="box"><strong>Decide to ask</strong><br>Benefit, cost and purpose</div>
</div>

- Correcting a rule matters; richer notes alone did not meet the test.
- More focus helped generation on selected cases; choices still differed from history.
- A compiled edit establishes feasibility. Historical agreement and usefulness need their own evidence.

<!--
Evidence: E1–E11. This diagram organizes observed loss stages, not a validated
architecture. Exact supply remains a conditional positive, including the GPT
disposition result. No universal negative about knowledge, prompts, decomposition
or focus follows from the tested designs. No cross-PR autonomous gain is established
by the focused cases.
-->

---

# The next empirical question

**When a reviewer constructs a valid alternative, do its reasons for declining it distinguish a worthwhile suggestion from avoidable churn?**

Start with the generality case and nearby contrasting cases; construction is already demonstrated.

- Compare alternatives with purpose, hypotheses, client uses, proof and migration costs visible.
- Judge the suggestion independently of whether the historical reviewer asked for it.
- Before another whole-PR intervention, identify the specific failure it should change and freeze a fresh test.

<div class="take">

Finish the empirical closeout. Then expand the theoretical account around choice, value and what historical review can actually identify.

</div>

<!--
Evidence: E11, review-harness-next-question-2026-10-27. This is a recommendation,
not an executed study or a frozen protocol. Do not tune the bank to the three
familiar targets. The usefulness panel is unfinished; a smaller closeout must be
described as a narrower question, not completion of the whole planned evaluation.
The theoretical expansion is deliberately left for the second pass requested by
the user. The earlier formulation remains a working account, not a proven model.
-->

---

<!-- _class: dense -->

# Backup · What the stated reasons show

**246 asks with an agreed stated ground**, selected from the census and coded by two model readers:

| Primary ground | Share |
|---|---:|
| Technical fact | 32% |
| Principle: generality, readability, etc. | 27% |
| Preference | 16% |
| Scope's practice | 11% |
| Authority | 8% |
| Currency | 3% |
| Other | 3% |

**Limit:** the favorable “mostly reasoning, little taste” verdict depended on counting facts against taste. The corrected reading is **mixed**; these are stated reasons on a selected subset.

<!--
Evidence: E5, final corrections. Marker selection caught 318 of 1,833 asks; later
sampling estimated some ground is stated in about 37%, not just the original 17%.
The 246 agreed grounded asks are the table denominator; percentages round. Readers
share a model family, and repeated agreement is not independent human validation.
-->

---

# Backup · The experimental foundation also changed

**By 22 October:** shared tasks and stored handoffs for extraction, matching and reviewer context.

- Task inputs and outputs can be traced through preparation to final review.
- The reconstruction chain and a second existing probe were reproduced through the shared path.
- Transport and toolchain failures now have explicit coverage and preflight checks.

<div class="take">

This supports controlled experiments and diagnosis. It supplies no review-quality improvement by itself.

</div>

<!--
Evidence: E12. Task/dataflow integration at a9154196, reviewed at e13343c8; reproductions
include 954c6f9b and 68dea3b5. Sonnet smoke fcca6c76 exercised one extractor session
and one matcher batch, not an end-to-end quality test. Later pilot and bank comparisons
used these shared paths. These are completed infrastructure results; the proposed
comparison-session was not thereby validated as a review intervention.
-->

---

<!-- _class: dense -->

# Backup · Evidence and reading guide

**[Evidence register](evidence.md)** — each experiment's source, denominator, corrections and limits. IDs also appear in the speaker notes.

| IDs | Material |
|---|---|
| E1–E2 | Convention census, exact supply, ask-free transfer and GPT disposition |
| E3–E5 | Departure validity, actual practice and stated grounds |
| E6–E7 | Library evidence, reconstruction and conditional preparation |
| E8–E9 | 54 whole reviews and source-bank checks |
| E10–E11 | 72 focused sessions, audit and next question |
| E12 | Shared experimental foundation |

The 54-review and 72-session records are on **experiment branches**. The register records their revisions; they have not all been merged into `develop`.

---

<!-- _class: dense -->

# Backup · Earlier sources

**Historical baselines and convention synthesis:** [experiment synthesis](../docs/research/knowledge-transfer-experiment-synthesis-2026-10-23.md), [October conventions assessment](../docs/research/conventions-assessment-2026-10-12.md), [questions register](../docs/questions.md).

**Review systems and task framing:** [literature survey](../docs/research/code-review-systems-survey-2026-09.md), [living research overview](../docs/project-research-overview.md), [preserved October update](../supervisor_update_2026-10/slides.md).

**Published work in the earlier slides:** APE-Bench (2504.19110), MathlibPR (2605.07147), ProofJudge (2608.20432), Tricorder (ICSE'15), AutoCommenter (2405.13565), BitsAI-CR (2501.15134), RovoDev (2601.01129), SWR-Bench (2509.01494), Di Biase et al. (1805.10978), LLM ensembles for code (2510.21513).

<!--
This pass verifies local experiment records and their later corrections; it does
not perform a new literature search or update model capabilities/prices. The
pre-convention baseline slides retain their historical dates and instruments.
-->
