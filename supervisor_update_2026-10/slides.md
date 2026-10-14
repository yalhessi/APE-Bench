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

# Two tasks on the same code

**APE-Bench:** given an instruction, reach the state.
Success = the edit compiles, and a judge agrees it does what the instruction says.

**Review:** given the state, produce the instruction.
The PR already compiles. Nobody hands the reviewer an ask.

<div class="take">

APE-Bench gives the direction and asks for the target. Review asks for the direction. The direction is where maintainers spend their time.

</div>

<!--
APE-Bench: tasks synthesised from real Mathlib commits; "dual verification", syntactic compilation
plus semantic requirement satisfaction; best evaluated agent 47 of 100 tasks.
-->

---

# A partial order on contribution states

For a PR against base commit $b$, take every state it could be edited into.

- $C$: the states that **compile**. Cheap, decidable, the kernel's job.
- $\preceq$: the community's **preference**. Partial: two golfs, two names, often incomparable.
- $M \subseteq C$: the states a maintainer would **merge**. Upward closed. Not decidable.

A **review** of $s_0$ is a set of asks, each a direction and a target: $s_0 \prec s_i$. The maintainer's asks and the author's replies trace one path into $M$.

<div class="take">

"Verifiable correctness is not enough" is the statement $M \subsetneq C$.

</div>

---

# The picture

```text
              ·  s*  maintainer's target        ·  s'  reviewer's target
               \                                /
  merge-ready M ─\──────────────────────────────/───────────────
                  \                            /
                   ·  s″  right direction, short of M
                    \                        /
  compiles  C  ·· s₀ ·························  the PR as submitted
                     \
                      ·  s‴  a change nobody asked for, not above s₀
```

| the judge asks | in the order |
|---|---|
| same issue | the ask's **direction** is the maintainer's |
| strict fix | the ask's **target** is $s^\ast$ |

---

# Merge-ready or not: three compiling PRs

- **#33304** — doc fix, merged untouched. <span class="above">Already in M.</span> The right review is empty.
- **#33305** — the same kind of PR, one blocking ask: a line too long. <span class="below">One step below.</span>
- **#33149** — Navier–Stokes, AI-assisted, 19 new axioms, vacuous definitions. <span class="below">Far below, closed.</span>

<div class="take">

$M$ is not a lint set. Blocking asks draw its line; advisory asks move inside it. Of the 23 scored asks on the twelve convening PRs, 4 are blocking.

</div>

<!--
All three from the convening's twelve December-2025 PRs. 33305's line was located by neither
reviewer in six runs. 33149: the compiler answered correctly, the meaning was wrong.
-->

---

# Taste inside M: PR #33098

<div class="cols">
<div class="panel">

## as submitted

```lean
lemma minimalCover_subset :
    minimalCover ε A ⊆ A := by
  by_cases h : coveringNumber ε A ≠ ⊤
  · simp only [minimalCover, ne_eq, h,
      not_false_eq_true, ↓reduceDIte]
    exact (exists_set_encard_eq_coveringNumber h)
      .choose_spec.1
  · simp [minimalCover, h]
```

</div>
<div class="panel">

## two one-liners, both compile

**maintainer**
```lean
  grind [minimalCover]
```

**our reviewer**
```lean
  simpa [minimalCover, h]
```

</div>
</div>

<div class="take">

Both above $s_0$, the PR merges with either. The order between them is a convention in motion. The judge says "same issue, not the fix"; the order says "a divergence inside $M$".

</div>

<!--
grind: 0% of Mathlib files Jan 2025, 14.5% by May 2026. The reviewer produced a compiling grind
proof in a probe and still submitted simpa: selection, not capability.
-->

---

# What else the order lets us say

- **Under-reach:** right direction, target short of $s^\ast$. #33117: *delete* the twin lemma vs *generate* it.
- **Gold is a lower bound:** a finding absent from the maintainer's review is unaligned, not wrong.
- **Clean PRs:** $s_0 \in M$, so every finding is sideways or down.
- **The order is dated:** `toLinearMap_` is the ask while the library counts 4,707 to 50 the other way.
- **A fix is a path, not an edge:** intermediate states may not even compile.

<!--
8 of the 10 asks never hit on the convening set were located and asked wrongly. The scaffolded
reviewer emitted 3 to 5 findings per run on the clean PRs; the whole-PR reviewer 0. Nothing in the
evaluation adjudicates the ~90% of findings that are off gold.
-->

---

# What it does not give us

- $\preceq$ is never observed. Each PR shows one chain; "incomparable" and "never compared" look alike.
- $M$ is seen only through merges.
- "Divergence we are fine with" has no adjudicator yet. Only a maintainer can say so.

<div class="take">

The question, in these terms: from $s_0$ alone, produce asks whose targets lie in $M$, preferring the maintainers' own order. Score direction and target against the one path on record.

</div>

---

<!-- _class: section-title -->

# 2 · The design space

What review systems have in common, and where they part

---

# Five decisions every review system makes

```text
 ① SCORE      what is one review, and what makes it right?
 ② KNOW       where does the judgement come from?
 ③ GENERATE   how are findings produced?
 ④ CHECK      what is filtered, and on what grounds?
 ⑤ DELIVER    when is it shown, and what is learned?
```

Read from primary sources: ByteDance, Google, Atlassian, Uber, Cursor, OpenAI, Anthropic, Alibaba; the benchmarks; MathlibPR and ProofJudge for Mathlib.

<!--
Surveys: docs/research/code-review-systems-survey-2026-09.md, open-code-review-comparison-2026-09.md,
and the October revisit. Sources slide at the end.
-->

---

<!-- _class: tbl -->

# ① Score: the unit decides what "correct" means

| unit scored | who | in the order |
|---|---|---|
| whole PR → merge-ready | MathlibPR | a **point**: is $s_0 \in M$? |
| declaration before / after | ProofJudge | an **edge**: is $s \prec s'$? |
| hunk → comments | SWR-Bench, SWE-PRBench | place and concern |
| review → tests | c-CRAB | the target, executed |
| one maintainer request | ours | direction and target |

<div class="take">

Every offline gold is a lower bound. Atlassian: 4% of comments match a human one, 38.7% get resolved. Deployed systems score online: was it acted on.

</div>

---

# ② Know: where the judgement comes from

- Rules inside a **trained** checker: ByteDance, 16.8% → 57% precision with its taxonomy.
- Norms learned from **comments** at scale: Google, ~800k norm-citing comments.
- Guidelines **in the prompt**: Atlassian +5%; ours in June, null.
- Team **feedback as memory**: Greptile, Semgrep, Qodo.

<div class="take">

Knowledge as prompt text is near null wherever measured. What moves is trained on outcomes, at a scale Mathlib does not have: 0.7% of its review comments cite a norm.

</div>

---

# ③ Generate: one pass, specialists, or many passes

- **One whole-diff pass:** strong and unstable. Our solo's three runs never hit the same ask twice.
- **Specialists** by concern or by evidence source: decomposition alone did not buy recall, here or at Alibaba.
- **Many passes:** Cursor votes over 8; aggregation lifts F1 up to 44%; ensembles gain up to 83% on the union, but majority vote is a "popularity trap".

<div class="take">

Diversity buys recall; voting throws it away. And restraint is the enemy: Cursor needed "aggressive" prompts; our arms went 0.20 → 0.50 when refused the option to stay silent.

</div>

---

# ④ Check: truth is safe, value moves precision

<div class="cols">
<div class="panel">

## on truth

- Atlassian's factual judge: minimal impact.
- Alibaba's filter deleted real defects while it judged value; refutation-only, 36% → 88%.
- Ours: compile the proposed edit in place.

</div>
<div class="panel">

## on value

- Atlassian's actionability gate, trained on 50k resolutions: +15–20pp.
- Uber: suppress whole categories.
- Google: a threshold per rule; switch off any past ~10% "not useful".

</div>
</div>

<div class="take">

In Lean the truth filter is free. Precision everywhere comes from the value filter, learned from outcomes. Google's rule is our thesis: a false positive is anything the user did not want to see.

</div>

---

# The convergent design, and the open disagreements

```text
specialised generators → separate verifier → suppression tuned on feedback → dedup → acted-on metric
```

Ours has the first, second and fourth. The other two need a deployment.

- **Verdict before reasoning?** ByteDance says yes, Alibaba says no. Different model kinds.
- **More context?** Eight models got *worse* with structured context. Structure helps to pose questions, hurts as padding.
- **Deterministic or agentic?** Deterministic spine; the agent for retrieval and judgement.
- **Decompose the change?** Changes effort and noise, not recall.

---

# What formal mathematics changes

- **Truth is cheap.** A proposed fix compiles or not: the strongest filter the industry trains for, free.
- **Value is the whole problem.** The compiler neither finds the issue nor picks among valid fixes.
- **The data is small, and moves.** ~30 people merge; no 50k-resolution labels; `grind` went 0% → 14.5% in a year.

<div class="take">

MathlibPR: models cannot tell merge-ready from build-passing PRs. ProofJudge: recovers reviewer preference on before/after pairs. Neither asks *where* the gap sits.

</div>

---

<!-- _class: tbl -->

# The map

| decision | converged | contested | open for Lean |
|---|---|---|---|
| ① score | acted-on signal | offline gold as precision | adjudicate off-gold once |
| ② know | trained per-rule checkers | prompt guidelines | knowledge **asserted at the place** |
| ③ generate | specialists + passes | decomposition alone; voting | the **model and harness** as the lever |
| ④ check | truth gate + value gate | truth judge alone | compile as the truth gate |
| ⑤ deliver | diff-time, per-rule tuning | — | author-side; no feedback loop |

<div class="take">

Since the convening the wall moved when the model or the harness changed, not when parts were added.

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
