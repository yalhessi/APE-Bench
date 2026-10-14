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
footer: "Mathlib PR review · progress since the AI for Math convening · October 2026"
---

<!-- _class: lead -->
<!-- _paginate: false -->
<!-- _footer: "" -->

# Reviewing Mathlib PRs: progress since the convening

## Supervisor update · October 2026

**Yousef Alhessi** · University of Edinburgh

<!--
Three parts: the problem as we now state it; the design space of review systems; what we did
since 17 September and where it stands. Speaker notes carry the numbers that are not on screen.
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

<!-- _class: tbl -->

# Each other approach pins one part, and pays for it

| approach | what it pins | what it gives up |
|---|---|---|
| verdict | the output: only "is δ acceptable" | everything but one bit; models cannot beat "it builds" |
| written rules | the standard: the documented rules | every convention that is not written down |
| recent practice | the standard: what was accepted nearby | the first asks of a convention in motion |
| preferred alternative | the output: a fix only | questions, scope, PR-level asks |
| consequential | correctness: the author's next revision is acceptable | needs an acceptance oracle; confounds reviewer and author |
| **request emission, ours** | nothing | the answer key: only one maintainer's review, a lower bound |

<div class="take">

We kept the whole task: hence recall against a lower bound, not precision and F1.

</div>

<!--
Who does what: verdict is MathlibPR; written rules are Tricorder, BitsAI-CR, AutoCommenter; recent
practice is Qodo, Greptile, Semgrep memories; preferred alternative is ProofJudge; consequential is
c-CRAB and the resolution rates at Atlassian and Cursor; request emission is SWR-Bench, SWE-PRBench and
ours. MathlibPR: models and agents cannot separate merge-ready from build-passing PRs. ProofJudge:
recovers reviewer preference on 63.5-80.8% of 218 before/after pairs.
-->

---

# One pipeline; precision from the soundness gate

```text
generators     →   truth gate         →   soundness gate            →   dedup   →   acted-on
propose tests      the witness            would the community           one test    the author
                   compiles; the          set this test?                once        passed it
                   claim is grounded      learned from outcomes
```

**We have** generators, the truth gate (the compile receipt) and dedup.
**We lack** the soundness gate and the acted-on signal. Both are learned from outcomes, at a scale Mathlib does not have.

<!--
ByteDance, Google, Atlassian, Uber, Cursor, OpenAI, Anthropic and Alibaba arrived at the same five parts
independently. Evidence for "soundness, not truth" is on the next slide.
-->

---

<!-- _class: tbl -->

# Five points the evidence settles

| point | literature | our experiments |
|---|---|---|
| **≽_t cannot be told as text.** | guidelines in the prompt: Atlassian +5% | June injection null at N=115; the catalogue as a list +0.03, the same sentences asserted at the place +0.26 |
| **Truth gates do not buy precision; soundness gates do.** | Atlassian: factual judge minimal, actionability gate +15–20pp; Alibaba: refutation-only filter 36% → 88% | every artifact-only selector at chance, AUC 0.49–0.52; nothing adjudicates the 90% of findings off gold |
| **Diversity buys recall; voting loses it.** | aggregation +44% F1; ensemble union +83%, majority vote a "popularity trap" | solo reps never hit the same ask twice; four passes unioned 12 of 23, at 7 findings per clean PR |
| **Decomposition changes effort, not recall.** | Di Biase: no more defects found; Alibaba grouping 20% → 12.7% | arms against one agent: neither wins; specialists 10% of matches for 37% of spend |
| **Restraint is the enemy.** | Cursor needed "aggressive" prompts | arms refused silence: 0.20 → 0.50, and the clean PR 1 → 36 findings |

<!--
Literature: RovoDev (2601.01129), open-code-review's commit history, SWR-Bench (2509.01494), LLM
ensembles for code (2510.21513), Di Biase et al. (1805.10978), Cursor's Bugbot write-up. Ours:
dead-ends.md "statute", conventions-ceiling stages F and exact, selection-signal.md, ensemble-union
reading, the A/B spine, forbid_abstention on the fanout four.
-->

---

# What formal mathematics changes

- **The witness is kernel-checkable.** Truth is free: the strongest filter the industry trains for.
- **Soundness is the whole problem.** The compiler neither finds the test nor picks among witnesses. MathlibPR: models cannot tell δ ∈ A_t from δ ∈ S.
- **The outcome data is small, and moves.** About 30 people merge; 0.7% of review comments cite a norm; `grind` went 0% → 14.5% of files in a year.

<div class="take">

The wall is placement. Part 3 says what moved it.

</div>

---

<!-- _class: section-title -->

# 3 · What we did, and where we stand

Four questions, five weeks

---

# The thesis, and the baseline

<div class="box">

**Understand the review process, then decompose it.** That is what can make a harness more useful than one agent with tools. So one agent with tools is the baseline, always.

</div>

**The baseline, frozen.** One session, the whole PR, the brief, the tools, compile-my-edit.
On the twelve dev PRs: Opus 5.5 **9, 9, 7** of 23 · self-hosted DeepSeek **8, 6, 9** · GPT 5.5 **2–5**.

**Four questions.** Does decomposition by concern beat it? Where is the wall?
What does the community actually ask for? Can a reviewer be given that knowledge?

<!--
Instruments built since the convening: validation and test sets 2025-06..2026-03 (50 main + 10 AI
each), 1,000 validation PRs read by two blind readers, six post-cutoff PRs, blind matchers beside
the judge.
-->

---

# Q1 · Decomposition by concern: the specialist arms

| held-out 12, three reps | arms + lead | one agent |
|---|---|---|
| asks hit per rep | 7, 5, 6 | 4, 4, 1 |
| hit in all three | **5** | 0 |
| findings on the clean PRs | 3, 4, 5 | **0** |
| billed per rep | $14.59 | **$1.90** |

- The generalist did the work: 64 of 71 matches. The arms withheld. The gate discarded what was found.

<div class="take">

21 of 23 asks were *located* by somebody; 13 *asked* correctly. We had decomposed the output by concern. The gap was knowledge at the place, not attention.

</div>

<!--
Specialists: 37% of spend, 10% of matches, six arms matched nothing. Forced to answer: 0.20 → 0.50
on four PRs, clean PR 1 → 36 findings. The admission gate discarded 71-83% of found asks.
-->

---

<!-- _class: tbl -->

# Q2 · Where is the wall: harness, prompt, or model?

| reviewer | of 23 | settles |
|---|---|---|
| GPT 5.2 / 5.5, three harnesses | 2–5 | the harness does not limit GPT |
| Opus 5.5 on GPT's exact messages | 10 | the prompt text does not limit GPT |
| Opus 4.8 / Opus 5 / Opus 5.5 | 3 / 8 / 7–12 | the model moves the wall |
| Qwen3.5-397B, self-hosted | 2, 0, 2 | the floor |
| **DeepSeek-V4.1-Flash, self-hosted** | **8, 6, 9** | a free iteration tier |

<div class="take">

The misses are judgement at a *visited* declaration: a convention or mechanism the reviewer does not know, or a compile nobody ran. So: what does the strong model know that the others lack?

</div>

<!--
Of 67 asks the weaker reviewers never reach, 63 had the object visited: unknown convention or mechanism
25, compile not run 19, analogue not compared 6. Our harness costs Claude volume: 22% fewer findings
at the same hit rate than the probe harness (11-12).
-->

---

# Q3 · A convention, in the formulation

```text
trigger_c holds at a place in δ     (area, date) ∈ scope_c     no defeater
──────────────────────────────────────────────────────────────────────────
a test at that place: revisions with the form are the ones ≽_t favours
```

- No trigger fires: silence is correct.
- Several accepted forms: a question, not a change.
- The trigger is decided by syntax, execution, lookup, or judgement.

<div class="take">

The next slides measure each premise: how many such rules there are, what happens when the reviewer is told which fire, and how often a firing trigger is a maintainer's test.

</div>

---

# Q3 · What does the community ask for? The census

**How:** the 1,833 first-round asks on 1,000 validation PRs. Two blind readers each wrote the principle behind every ask as one sentence, keeping a running codebook.

- **409 and 407 principles**, two apart. Not saturated: one ask in ten still brings a new one.
- **Small head, long tail:** top 10 cover 22%, top 50 cover 55%, 370 in the tail.
- On fresh PRs the census never read, an entry sits behind **85%** of the asks.

<div class="take">

Review is not a hundred rules. Four deterministic detectors for the head cover 2.9% of asks. Recall is in the tail.

</div>

---

# Q3 · Does knowing the convention help? The ceiling

Tell the reviewer *which* census conventions the maintainers invoked on this PR, as general sentences, no location. Compare with the same reviewer unbriefed.

| reviewer | unbriefed | briefed | gain |
|---|---|---|---|
| Opus 5.5 | 0.47 | 0.74 | **+0.27** |
| GPT 5.5 | 0.24 | 0.46 | **+0.22** |
| DeepSeek, three reps | 0.28 | 0.50 | **+0.22** |
| DeepSeek, with precedence and an example | 0.28 | 0.70 | **+0.42** |

<div class="take">

Knowledge is the lever, for the free model as much as the paid ones. But this is the answer key. Can the reviewer be given it without the key?

</div>

<!--
Fourteen held-out PRs, 46 asks, blind matchers. Qwen at the floor: +0.05. Of 17 asks no unbriefed
session of any model reaches, briefed sessions reach 11.
-->

---

<!-- _class: tbl -->

# Q4 · Getting the knowledge in without the answer key

| delivery, least to most assertive | result |
|---|---|
| guides and the catalogue as prompt text | null |
| the applicable entries, picked from the diff | +0.03 |
| pinpointed at the place, "check whether it applies" | 0.00: overridden at 9 of 21 places |
| asserted as applying, with precedence | +0.20 on the PRs it was built on; 0.00 on fresh ones |
| deterministic detectors as facts | valid, 2.9% of asks |
| a filing contract: no withholding | 14 of 37, at 4.9 findings per clean PR |
| dossiers and exams per convention | not built: the bare sentence already works at the place |

<div class="take">

And maintainers raise a convention at **5% or fewer** of the places it applies. Predicting which: ~7% precision.

</div>

---

# The mechanism, on one PR

PR #42814. The maintainer asked for `variable {D}` declared once. The reviewer held that exact convention at that exact declaration, and wrote:

> "Mathlib does not require these, so I would not request them."

- **The assertion, not the content, carries the gain.** Stated as *applying here*, the reviewer acts. Offered to verify, it overrides.
- **Asserting without the key means asserting wrongly.** A pick of 25 holds about 3 true asks; the reviewer files the other 22 too.

<div class="take">

The model acts on a convention it is told applies: solved. Which of the hundreds that apply would *this* maintainer raise *here*: open.

</div>

---

# Where we stand, 14 October

| layer | status |
|---|---|
| **knowledge** — the census holds what maintainers ask; a reviewer acts on it when told | supported, replicated |
| **delivery without the asks** — pick the applicable conventions from the PR | not supported off-sample |
| **understanding** — dossiers and exams | not supported; drop rule met |

- A third of asks escape every unbriefed session of every model, spread thin across kinds: the tail.
- Of 41 the free reviewer never reaches, the library *decides* 7 and *points to* 19: the ask is a choice among the library's options.

<!--
Publishable now, as a result about the task: the census with its saturation curve; knowledge,
selection and filing separated by experiment; demand as a small unpredictable subset of
applicability; the assertion mechanism.
-->

---

# What this says about the next design

<div class="box">

A maintainer's decision to raise a convention, or not, is **reasoning on evidence that can be reconstructed**: the trigger, the library's precedent, the PR's intent; against it, an exception, a deliberate deviation, a cost. Taste is a small residual.

</div>

So the harness should gather and weigh that evidence, not learn a preference.

| option | ceiling | cost |
|---|---|---|
| the harness for the free model | ~+0.10 | $0, a day |
| analogue retrieval for the design asks | ~0.075 of asks | a measurement first |
| a closer battery as packet facts | ~0.065 of asks | compute |
| the per-place engine | 0.40–0.55 in-census | 25× filings; needs adjudication |

<!--
Dense.ciSup: the statement is a supremum, the library names such lemmas ciSup, the lemma is not about
continuity, so continuous_ goes. All ceilings on 93 asks over 26 PRs used to develop the designs;
the fresh 40-PR set has built workspaces and has never been read.
-->

---

<!-- _class: tbl -->

# Backup · sources

**Deployed reviewers.** BitsAI-CR, ByteDance (2501.15134) · AutoCommenter, Google (2405.13565) · RovoDev, Atlassian (2601.01129), HalluJudge (2601.19072) · uReview, Uber · Bugbot, Cursor · Codex reviewer, OpenAI · Anthropic Code Review and the open plugin · open-code-review, Alibaba, with AACR-Bench · Qodo 2.0 · CodeRabbit (2607.03316) · Greptile v4 · Semgrep Assistant. Tricorder (ICSE'15), Infer (CACM'19).

**Benchmarks and studies.** SWR-Bench (2509.01494) · SWE-PRBench (2603.26130) · c-CRAB (2603.23448) · CodeReviewer (2203.09095) · Code Review Bench, Martian · Adversarial Review (2608.18167) · LLM ensembles for code (2510.21513) · Harness Engineering (2609.00006) · Di Biase et al. (1805.10978) · Kamalı et al. (2605.17548).

**Mathlib.** MathlibPR (2605.07147) · ProofJudge (2608.20432) · Growing Mathlib (2508.21593) · APE-Bench (2504.19110).

**Ours.** `docs/research/code-review-systems-survey-2026-09.md`, `open-code-review-comparison-2026-09.md`, `conventions-assessment-2026-10-12.md`.
