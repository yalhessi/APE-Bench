---
marp: true
theme: default
paginate: true
size: 16:9
math: katex
style: |
  section {
    font-size: 24px;
    padding: 40px 56px;
  }
  section.lead h1 { font-size: 52px; }
  section.lead h2 { font-size: 30px; font-weight: normal; color: #555; }
  section.section-title { background: #1d2b53; color: white; }
  section.section-title h1 { color: white; font-size: 56px; }
  section.section-title p { color: #c7d0e8; font-size: 28px; }
  h1 { font-size: 40px; color: #1d2b53; }
  h2 { font-size: 30px; color: #1d2b53; }
  table { font-size: 20px; }
  section.small table { font-size: 16px; line-height: 1.25; }
  section.small { font-size: 20px; }
  section.small h1 { font-size: 34px; margin-bottom: 8px; }
  blockquote { border-left: 6px solid #e0a020; background: #fff8e6; padding: 8px 18px; font-style: normal; }
  pre { font-size: 18px; }
  .cols { display: grid; grid-template-columns: 1fr 1fr; gap: 32px; }
  .cols3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 24px; }
  .box { border: 2px solid #1d2b53; border-radius: 10px; padding: 12px 18px; }
  .muted { color: #666; font-size: 20px; }
  .case-panel { border: 2px solid #d6dcea; border-radius: 12px; padding: 10px 16px; }
  .case-panel h2 { font-size: 24px; margin: 0 0 4px; }
  .case-panel p { margin: 6px 0; }
  .case-panel pre { font-size: 16px; margin: 6px 0; }
  .above { color: #1a7f37; font-weight: bold; }
  .below { color: #b3261e; font-weight: bold; }
  .side { color: #8a6d00; font-weight: bold; }
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
Part 1 of the deck: the problem formulation. Later parts cover what was built and measured since
17 September, and what is next.
-->

---

<!-- _class: section-title -->

# 1 · What problem are we solving?

APE-Bench's task, our task, and the order that connects them

---

# APE-Bench's formulation: the direction is given

A task is built from a real Mathlib commit. The commit's diff is turned into a natural-language
**instruction**; the file before the commit is the **starting state**.

```text
input     instruction  I   +   starting state  s₀            (the file before the commit)
output    an edit            s₀ → s₁
success   s₁ compiles   ∧   a judge agrees s₁ satisfies I     ("dual verification")
```

<div class="cols">
<div class="box">

**What is hard.** Reaching the target: multi-file coordination, library knowledge, the proof itself.
The best evaluated agent completes 47 of 100 tasks.

</div>
<div class="box">

**What is given.** The direction. The instruction says *what* to change. The reference commit says
what "done" looks like, and the judge checks against it.

</div>
</div>

<p class="muted">Xin, Yuan, Jin, Fleuriot, Li — APE-Bench, arXiv 2504.19110 (v3, Feb 2026).</p>

---

# Our problem: nobody hands the reviewer an instruction

A pull request arrives. It **already compiles**. The maintainer reads it and writes the
instructions: rename this, this is a duplicate, derive the dual instead of re-proving it.

```text
input     a PR as the maintainer first saw it     s₀         (no instruction)
output    a set of asks, each naming a direction and a target      s₀ → sᵢ
success   the asks a maintainer would have made        (and nothing that would waste their time)
```

<div class="box">

APE-Bench asks: *given the ask, can you reach the state?*
We ask: *given the state, can you produce the ask?*

Both halves are needed for AI-written contributions. The second is the one maintainers are paying
for by hand today.

</div>

---

# The formulation: a partial order on contribution states

For a PR against base commit $b$, let $S_b$ be every state the contribution could be edited into.
The PR as submitted is one state, $s_0$.

- $C \subseteq S_b$ — the states that **compile**. Decidable, cheap, the kernel's job.
- $\preceq$ — the community's **preference** between states. A *partial* order: two golfs of one
  proof, or two defensible names, are often incomparable.
- $M \subseteq C$ — the states a maintainer would **merge**. Upward closed: improving a
  merge-ready state keeps it merge-ready. Not decidable. Seen only through what maintainers do.

A **review** of $s_0$ is a set of asks. Each ask names a direction (the *issue*) and a target
(the *fix*): $s_0 \prec s_i$. The maintainer's review plus the author's responses trace one path
$s_0 \to \cdots \to s^\ast \in M$ when the PR merges.

<div class="box">

**Verifiable correctness is not enough** is the statement $M \subsetneq C$: every PR we score is
in $C$, and what the maintainer asks for is the distance from $s_0$ to $M$ and beyond.

</div>

---

# The picture

```text
                          ·  s*   the maintainer's target           ·  s'  the reviewer's target
                           \                                        /
      merge-ready  M  ──────\──────────────────────────────────────/────────────────────
                             \                                    /
                              ·  s″  right direction, short of M (under-reach)
                               \                                /
                                \                              /
   compiles  C   ·· s₀ ·········································  the PR as submitted
                                 \
                                  ·  s‴   a change nobody asked for, not above s₀ (noise)

   s₀ ≺ s″ ≺ s*        s₀ ≺ s'        s' and s* incomparable, both in M        s‴ ⊀ s₀
```

The three questions the evaluation asks, in these terms:

| the judge's question | in the order |
|---|---|
| same place | the ask touches the declaration the maintainer touched |
| same issue | the ask's **direction** is the maintainer's |
| strict fix | the ask's **target** is $s^\ast$ |

---

<!-- _class: small -->

# Case 1 · merge-ready or not: three distances to $M$

Three December 2025 PRs from the convening talk's twelve. All three compiled.

<div class="cols3">
<div class="case-panel">

## #33304 — in $M$ already

Fix file references in docstrings. Merged with no request.

<span class="above">s₀ ∈ M.</span> The correct review is **empty**; anything emitted here moves
sideways or down.

</div>
<div class="case-panel">

## #33305 — one step below

The same kind of PR. One **blocking** ask: an over-long doc-comment line.

<span class="below">s₀ ∉ M,</span> one mechanical step from the boundary. Neither reviewer
located it in six runs.

</div>
<div class="case-panel">

## #33149 — far below, closed

Navier–Stokes regularity, AI-assisted, 469 lines, 19 new `axiom`s, vacuous definitions.

<span class="below">Every ask blocking.</span> The compiler answered correctly; the meaning
was wrong.

</div>
</div>

<div class="box" style="margin-top:12px">

$M$ is not a lint set: #33305's boundary is a line-length rule, #33149's is "the definitions do not
say what you claim". **Blocking** asks draw the line of $M$; **advisory** asks are moves inside it.
Of the 23 scored asks on the twelve PRs, 4 are blocking and 19 advisory.

</div>

---

<!-- _class: small -->

# Case 2 · taste we can live with: two targets, both in $M$

PR #33098: four `minimalCover` lemmas, each proved by cases on whether the covering number is finite.

<div class="cols">
<div class="case-panel">

## $s_0$ — as submitted

```lean
lemma minimalCover_subset : minimalCover ε A ⊆ A := by
  by_cases h : coveringNumber ε A ≠ ⊤
  · simp only [minimalCover, ne_eq, h,
      not_false_eq_true, ↓reduceDIte]
    exact (exists_set_encard_eq_coveringNumber h)
      .choose_spec.1
  · simp [minimalCover, h]
```

</div>
<div class="case-panel">

## two one-line targets, both compile

**Maintainer:** "This and the next three lemmas can be proven with this"
```lean
  grind [minimalCover]
```

**Our reviewer:**
```lean
  simpa [minimalCover, h]
```

</div>
</div>

<div class="box" style="margin-top:8px">

$s_0 \prec s'$, $s_0 \prec s^\ast$, and the PR merges with either. The order between them is a
**convention in motion**: `grind` was in 0% of Mathlib files in January 2025, 14.5% by May 2026.
The judge scores *same issue, not the strict fix*; the formulation reads that as a divergence
inside $M$, not a miss below it.

</div>

---

<!-- _class: small -->

# What else the order lets us say precisely

| Situation | In the order | Where we have seen it |
|---|---|---|
| **Under-reach** | right direction, target short of $s^\ast$; often still outside $M$ | #33117: reviewer asks to *delete* the hand-written `fun_neg`; maintainer asks to *generate* it with `@[to_fun]`. 8 of the 10 asks never hit were located and asked wrongly. |
| **Lateral target** | same direction, target of the same rank as $s_0$ | #33285: maintainer golfs to one term-mode line; our reviewer proposes a `simpa` proof of two or three lines, three runs out of three, no shorter than the PR's own two. |
| **Gold is a lower bound** | the maintainer names *one* path; other upward edges exist | A finding absent from the maintainer's review is *unaligned*, not wrong. Nothing in the evaluation yet adjudicates the ~90% of findings that are off-gold. |
| **Noise on a clean PR** | $s_0 \in M$; any ask is sideways or down | #33304, #33315: the scaffolded reviewer emitted 3–5 findings per run; the whole-PR reviewer 0. |
| **The order is dated** | $\preceq_t$ at the base commit, not today's | `toLinearMap_` vs `coe_`: the library counts 4,707 to 50 *against* the maintainer's rename; the convention lives in the review archive. |
| **A fix is a path, not an edge** | intermediate states may leave $C$ | `@[to_fun]` beside the hand-written twins is a name clash; the resolution is one atomic patch set, not a sequence of asks. |
| **AI-generated PRs** | states far below $M$ with long paths | #33149, the one AI-assisted PR in the twelve: four blocking asks, closed. Distance to $M$ is the maintainers' cost, which is the quantity we want to cut. |

---

<!-- _class: small -->

# What the formulation does not give us

- **$\preceq$ is never observed directly.** Each PR shows one chain: what was asked and what the
  author then did. "Incomparable" and "never compared" look the same in the data.
- **$M$ is seen only through merges.** An advisory ask the author ignored while the PR still merged
  says $s_0$ was already in $M$ at that site. A closed PR may be abandoned rather than rejected;
  the data keeps those apart.
- **Acceptable divergence has no adjudicator yet.** The judge can say *same issue, different fix*.
  Only a maintainer can say the other fix was fine too. That study is deferred until the output burden
  is low enough to ask for it.
- **The order is dated.** Conventions drift (the `grind` curve), so the reference is the order at the
  PR's date. A reviewer that knows only the library as it stands reads the order backwards.

<div class="box">

The project's question in these terms: from $s_0$ alone, produce asks whose targets lie in $M$,
preferring the maintainers' own $\preceq$. Measure direction (*issue recall*) and target
(*resolution recall*) against the one path on record, and treat what is off that path as
unadjudicated, not wrong.

</div>

---

<!-- _class: section-title -->

# 2 · The design space of review systems

What the deployed reviewers, the benchmarks and the Mathlib work share, and where they part

---

# Five decisions every review system makes

```text
 ① SCORE      what is one review, and what makes it right?    unit · ground truth · offline or online
 ② KNOW       where does the judgement come from?             the model · rules · guidelines · feedback
 ③ GENERATE   how are findings produced?                      one pass · specialists · many passes
 ④ CHECK      what is filtered, and on what grounds?          truth · value · agreement
 ⑤ DELIVER    when is it shown, and what is learned?          diff-time · acted-on · per-rule tuning
```

Read from primary sources in September, revisited in October: the deployed reviewers at ByteDance,
Google, Atlassian, Uber, Cursor, OpenAI, Anthropic and Alibaba; the products Qodo, CodeRabbit,
Greptile and Semgrep; Google's and Meta's static analysers; the benchmarks SWR-Bench, SWE-PRBench,
c-CRAB, AACR-Bench and Code Review Bench; for Mathlib, MathlibPR and ProofJudge.

<div class="box">

**The same five parts emerge independently in nearly every deployed system.** The interesting
differences sit inside ②, ③ and ④, and there the evidence sometimes disagrees. Each of the next
four slides takes one decision: what everyone does, what the measurements say, and where we stand.

</div>

---

<!-- _class: small -->

# ① Score: the unit decides what "correct" can mean

| Unit scored | Ground truth | Who | In Part 1's order |
|---|---|---|---|
| whole PR → merge-ready | merged vs revised | MathlibPR | is $s_0$ in $M$? a **point** |
| declaration pair | the accepted revision | ProofJudge | is $s \prec s'$? an **edge** |
| hunk → comments | mined or annotated comments | CodeReviewer, SWR-Bench, SWE-PRBench | the ask's **place and concern** |
| review → tests | tests derived from reviews | c-CRAB | the ask's **target, executed** |
| one maintainer request | decomposed comments, fenced | ours | **direction and target** |

**Every offline gold is a lower bound, and the deployed systems know it.** Atlassian: only 4% of its
comments match a human comment in place and intent, yet 38.7% get resolved. Code Review Bench: comments
scored as false positives were real issues the gold lacked. So deployment scores **online**: was the
flagged line changed (ByteDance), was the comment resolved (Atlassian, Cursor), does a re-run on the
final commit still fire (Uber).

<div class="box">

Alignment with one reviewer's path and usefulness to the author differ by an order of magnitude. We
hold only the first; the second, read as "what the author later changed", is on our dead-ends list as
ground truth, because authors change things maintainers never asked for.

</div>

---

<!-- _class: small -->

# ② Know: where the judgement comes from

| Channel | System | What was measured |
|---|---|---|
| the model alone, whole diff | Claude Code, Codex, Devin as reviewers | c-CRAB: all four together solve ~40% of review-derived tests; high recall, low precision |
| rules inside a **trained** checker | ByteDance BitsAI-CR: a 219-rule taxonomy, fine-tuned | precision 16.8% without the taxonomy, 57.0% with it |
| norms learned from **comments** | Google AutoCommenter: T5 on ~800k comments that cite a best-practice URL | ~40% of comments resolved; a confidence threshold per URL |
| guidelines **in the prompt** | Atlassian RovoDev; our "statute" injection (June) | +5%; null here at N=115 on two models |
| team feedback as **memory** | Greptile, Semgrep triage memories, Qodo reading past PRs | addressed 30% → 43% (vendor); accepted patterns not re-flagged |
| the **verification bar**, not the finder | Anthropic Code Review's `REVIEW.md` | tunes what survives and its severity, not what is found |

<div class="box">

**Knowledge as text in the prompt is near null everywhere it was measured.** The channels that move
are trained on outcomes at a scale Mathlib does not have: 709 of 104,093 reviewer comments in our
store cite a norm source. Part 3 reports the one channel that did move a strong reviewer here: the
same convention stated as applicable at the exact place, not offered as a list.

</div>

---

<!-- _class: small -->

# ③ Generate: one pass, specialists, or many decorrelated passes

<div class="cols3">
<div class="case-panel">

## One whole-diff pass

Claude Code and Codex as reviewers; Alibaba's reviewer at ~1/9 the tokens, lower recall by design; our whole-PR reviewer.

**Strong and unstable.** Our three runs never hit the same ask twice; one run reaches about two thirds of what the family of runs reaches.

</div>
<div class="case-panel">

## Specialists

By concern: Uber's three assistants, Qodo, our ten arms with a lead. By **evidence source**: Anthropic's plugin, one reviewer each on the conventions file, bugs, git history, prior PR comments.

**Decomposition alone did not buy recall.** Arms against whole-PR: neither wins; specialists give 10% of matches for 37% of spend. Alibaba's grouping cut recall 20.0% → 12.7%, starving secondary files.

</div>
<div class="case-panel">

## Many passes

Cursor Bugbot: 8 passes over a randomised diff order, then a vote. SWR-Bench: aggregating reviews lifts F1 up to 43.7%. Ensembles for code: the oracle over a union gains up to 83%; majority vote is a "popularity trap". Adversarial Review: the critic agrees unless told to disagree with evidence.

</div>
</div>

<div class="box" style="margin-top:8px">

**Diversity buys recall; voting throws it away.** Restraint is the enemy: Bugbot needed "aggressive"
prompts; our arms went from 0.20 to 0.50 of the asks when refused the option to stay silent.

</div>

---

<!-- _class: small -->

# ④ Check: truth filters are safe, value filters are what move precision

<div class="cols">
<div class="case-panel">

## Filters on truth

- Atlassian's factual judge: **minimal impact**. HalluJudge grounds each claim in the diff (F1 0.85).
- Alibaba's filter deleted 8 real defects while it judged value. Rebuilt **refutation-only**, reasoning before the ids: precision 36% → 88%, real defects deleted 8 → 0.
- Anthropic: a verification step **reproduces** each candidate against the code.
- c-CRAB: human reviews become tests. Ours: the proposed edit is compiled in place.

</div>
<div class="case-panel">

## Filters on value

- Atlassian's actionability gate, trained on 50k comments labelled by resolution: **+15–20pp**.
- Uber: suppress whole low-value categories; that was its largest gain.
- Google AutoCommenter: a threshold per rule, and 22 rules switched off: useful 54% → 66%.
- Google Tricorder: any analyser past ~10% "not useful" is disabled.
- Anthropic's plugin: a scorer on a 0–100 rubric, keep ≥ 80. Pointwise scorers of that kind measured at chance here.

</div>
</div>

<div class="box" style="margin-top:10px">

In Lean the truth filter is unusually strong: a proposed fix compiles or it does not. Precision in every
deployed system comes from the **value** filter, and value is learned from outcomes. Tricorder's rule is
our thesis in another language: *a false positive is anything the user did not want to see.*

</div>

---

<!-- _class: small -->

# The convergent design, and where the evidence disagrees

```text
specialised generators → a separate verifier with its own context → suppression tuned on feedback → dedup → an acted-on metric
```

Ours has the generators, a verifier (the compile receipt) and dedup. It lacks the two parts the industrial
write-ups credit with trust: feedback-tuned suppression and an acted-on signal. Both need a deployment.

| Question | One side | The other | Reading |
|---|---|---|---|
| **Verdict before reasoning?** | ByteDance: conclusion-first 77.1% vs reasoning-first 65.8% | Alibaba: ids serialised before reasoning could not be retracted | fine-tuned first-token classifier vs frontier model writing tool arguments; test both orders |
| **More context?** | RepoGraph: gains when agents answer *structural* questions | SWE-PRBench: eight models degrade *monotonically* as structured context is added; MathlibPR: diagnostics give "limited and uneven gains" | structure helps when it poses a question, hurts as padding |
| **Deterministic or agentic?** | Alibaba: deterministic for what must not go wrong; a survey of 11 harnesses finds no embedding retrieval in production | Cursor: the agentic switch was its largest gain | deterministic spine, agent for retrieval and judgement |
| **Decompose the change?** | Di Biase et al.: decomposed diffs found no more defects | Alibaba's grouping lost recall; our arms did not beat one pass | decomposition changes effort and noise, not recall |

---

<!-- _class: small -->

# What formal mathematics changes

<div class="cols3">
<div class="case-panel">

## Truth is cheap

A proposed fix compiles in place, so the strongest filter the industry has to train for is free. On the convening's 23 asks, 12 had a compilable replacement.

</div>
<div class="case-panel">

## Value is the whole problem

The compiler neither finds the issue nor chooses among valid fixes (Part 1). MathlibPR: models and agents "struggle to distinguish merge-ready PRs from build-passing PRs"; recall of not-merge-ready snapshots 0–12% for the systems that report it.

</div>
<div class="case-panel">

## The data is small, and moves

About 30 people can merge. Our store holds ~104k review comments, 0.68% citing a norm. Nothing like 50k resolution labels or 800k norm-citing comments exists, and the norms drift (`grind`: 0% → 14.5% of files).

</div>
</div>

| Mathlib work | Unit | Edits? | Truth | Time fence |
|---|---|---|---|---|
| MathlibPR (May 2026) | PR snapshot → merge-ready | agents may not edit | merged vs revised | no |
| ProofJudge (Aug 2026) | declaration pair → 5 dimensions | reads only | accepted revision; 63.5–80.8% recovered | — |
| ours | one maintainer request | compiles proposed edits in place | comments decomposed | yes |

---

<!-- _class: small -->

# The map, and the cells Part 3 explores

| Decision | Converged (everyone does it) | Contested or null | Open for Lean, and where we are |
|---|---|---|---|
| ① score | online acted-on signal | offline gold as a precision measure | adjudicate off-gold findings once; gold stays a lower bound |
| ② know | per-rule checkers trained on outcomes | guidelines as prompt text | the convention **asserted at the place**; a catalogue of ~400 conventions from the census |
| ③ generate | specialists plus several passes | decomposition alone; majority vote | the **model and the harness** as the lever; decorrelated passes with union, agreement kept as a label |
| ④ check | a truth gate and a value gate | a truth judge alone | compile as the truth gate; a refutation-only critic |
| ⑤ deliver | diff-time, per-rule calibration | — | author-side preview; no feedback loop offline, so volume is read through control PRs |

<div class="box">

Since the convening the wall moved when the **model or the harness** changed, and not when pipeline
parts were added. Part 3 reads the record in that order: the harness, then knowledge at the place,
then passes and checks.

</div>

---

<!-- _class: small -->

# Sources for Part 2

<div class="cols">
<div>

**Deployed reviewers.** BitsAI-CR, ByteDance, FSE'25 (arXiv 2501.15134) · AutoCommenter, Google, AIware'24 (2405.13565) · RovoDev Code Reviewer, Atlassian, ICSE'26 (2601.01129) and HalluJudge (2601.19072) · uReview, Uber engineering blog · Bugbot, Cursor engineering blog · Codex reviewer, OpenAI alignment blog · Anthropic Code Review and the open `code-review` plugin · open-code-review, Alibaba, with AACR-Bench · Qodo 2.0, CodeRabbit (2607.03316), Greptile v4, Semgrep Assistant.

**Static analysis at scale.** Tricorder, Google, ICSE'15 · Infer, Meta, CACM'19.

</div>
<div>

**Benchmarks and studies.** SWR-Bench (2509.01494) · SWE-PRBench (2603.26130) · c-CRAB (2603.23448) · CodeReviewer (2203.09095) · Code Review Bench, Martian · CRScore, NAACL'25 (2409.19801) · Adversarial Review (2608.18167) · LLM ensembles for code (2510.21513) · Harness Engineering, eleven systems (2609.00006) · Noise Floor Audit (2608.22331) · Di Biase et al., change decomposition (1805.10978) · Kamalı et al., Rethinking Code Review in the Age of AI (2605.17548).

**Mathlib.** MathlibPR (2605.07147) · ProofJudge (2608.20432) · Growing Mathlib (2508.21593) · Palomar registry, Tao, Aug 2026.

**Ours.** `docs/research/code-review-systems-survey-2026-09.md`, `open-code-review-comparison-2026-09.md`, and the October revisit on the conventions branch.

</div>
</div>

---

<!-- _class: section-title -->

# 3 · What we did, and where we stand

Four questions, five weeks, and the results that answered them

---

<!-- _class: small -->

# The thesis, the baseline, and the instruments

<div class="box">

**The project is about understanding, and then decomposing, the review process.** That is what can make
a harness more useful than one agent with tools. So one agent with tools is the baseline, always, and a
design earns its place only by beating it.

</div>

<div class="cols">
<div class="case-panel">

## The baseline, frozen

One session, the whole PR, the reviewer's brief, the context tools and compile-my-edit. On the twelve
dev PRs (23 asks, judged): Opus 5.5 **9, 9, 7**; the free self-hosted DeepSeek **8, 6, 9**; GPT 5.5
**2 to 5**. Strong and unstable: no two runs agree on much.

</div>
<div class="case-panel">

## The instruments, built since the convening

A validation set and a test set from 2025-06 to 2026-03 (50 main + 10 AI-generated each), with small
versions; **1,000 validation PRs** read by two blind readers; **six post-cutoff PRs** the Claude models
cannot have seen; blind matchers beside the judge.

</div>
</div>

**Four questions organised the work.** Does decomposition by concern beat the baseline? Where is the
wall? What does the community actually ask for? Can a reviewer be given that knowledge?

---

<!-- _class: small -->

# Q1 · Decomposition by concern: the specialist arms

The design at the convening: a lead routes the PR's units to a generalist and ten specialists (naming,
duplication, proof-golf, docs, …); an evidence gate admits findings; a merge dedups.

<div class="cols">
<div class="case-panel">

## Measured on the held-out 12, three reps

| | arms + lead | one agent |
|---|---|---|
| asks hit per rep | 7, 5, 6 | 4, 4, 1 |
| hit in all three reps | **5** | 0 |
| union of both | 13 of 23 | |
| findings on the two clean PRs | 3, 4, 5 | **0** |
| billed per rep | $14.59 | **$1.90** |

Neither wins: reproducible against precise, at 7.7× the cost.

</div>
<div class="case-panel">

## Where it was weak

- **The generalist did the work:** 64 of 71 matches; the specialists took 37% of spend for 10% of matches, six matched nothing.
- **The arms withheld.** Refused the option to abstain, four PRs went 0.20 → 0.50 of asks, and the clean PR 1 → 36 findings.
- **The gate discarded** 71–83% of the asks the run had already found.
- **Packed units starved targets:** candidates per declaration 0.49 → 0.15.

</div>
</div>

<div class="box" style="margin-top:6px">

**The reading that changed the direction:** 21 of 23 asks were located by somebody, 13 asked correctly.
We had decomposed the *output* by concern; the gap was *knowledge at the place*, not attention.

</div>

---

<!-- _class: small -->

# Q2 · Where is the wall: the harness, the prompt, or the model?

Same brief, same tools, same twelve dev PRs (23 asks), crossed over models and harnesses.

| reviewer | harness | of 23 | what it settles |
|---|---|---|---|
| GPT 5.2, GPT 5.5 | ours, three harnesses tried | 2 to 5 | three harnesses with the model held reach the same: the harness does not limit GPT |
| Opus 5.5 on GPT's exact messages | the probe harness | 10 | the prompt text does not limit GPT |
| Opus 4.8 / Opus 5 / Opus 5.5 | ours | 3 / 8 / 7–9 | the model generation moves the wall |
| Opus 5.5 | the probe harness (own shell, files) | 11–12 | our harness costs Claude volume: 22% fewer findings at the same hit rate |
| Qwen3.5-397B, self-hosted | ours | 2, 0, 2 | the floor; thirteen prompt settings left it there |
| **DeepSeek-V4.1-Flash, self-hosted** | ours | **8, 6, 9** | a free iteration tier, once its earlier thinking was kept |

**What the misses are.** Of 67 asks the weaker reviewers never reach, 63 had the object visited. The
misses are judgement at an attended place: an unknown convention or mechanism (25), a compile nobody
ran (19), an analogue not compared (6).

<div class="box" style="margin-top:4px">

The wall moved with the **model**, and barely otherwise. So: what does it know that the others lack?

</div>

---

<!-- _class: small -->

# Q3 · What does the community ask for? The census

**How it was made.** The 1,833 first-round maintainer asks on the 1,000 validation PRs, disjoint from
every evaluation set. Two blind readers, in one seeded order, each wrote the principle behind each ask
as one sentence (a situation, and the form preferred in it), keeping a running codebook.

<div class="cols">
<div class="case-panel">

## What came out

- **409 and 407 principles**, two apart, coinciding in size four times; readers agree on 0.81 of asks.
- **Not saturated:** one ask in ten still brings a principle the census lacks.
- **A small head, a long tail:** the top 10 cover 22% of asks, the top 50 cover 55%; 370 entries sit in the tail, two fifths seen once.
- Rules and standards split evenly (841 against 828); one open conflict (two maintainers, opposite rules on a non-terminal `simp`).

</div>
<div class="case-panel">

## Does it generalise?

On fresh PRs the census never read, 14 of them created after it was written: an entry behind **39 of
46** and **40 of 47** asks (85%), the same primary entry on 38 of 38. The seven outside are docstring
slips and two new norms.

**What it rules out.** Deterministic detectors for the head: four conventions built and validated hold
**2.9%** of asks between them. Recall is in the tail.

</div>
</div>

---

<!-- _class: small -->

# Q3 · Does knowing the convention help? The ceiling

**The condition.** Tell the reviewer which census conventions the maintainers invoked on this PR, as
general sentences with no location ("a lemma whose statement is a supremum is named `ciSup…`"), and
compare with the same reviewer unbriefed. Fourteen held-out PRs, 46 asks, blind matchers.

| reviewer | unbriefed, reach per session | told the PR's conventions | gain |
|---|---|---|---|
| Opus 5.5 | 0.47 | 0.73–0.75 | **+0.26 / +0.28** |
| GPT 5.5 | 0.24 | 0.46 | **+0.22** |
| DeepSeek-V4.1-Flash, three reps | 0.28 | 0.50 | **+0.22** |
| DeepSeek, told them with precedence and an example each | 0.28 | 0.70 | **+0.42** |
| Qwen3.5-397B, the floor model | 0.03 | 0.09 | +0.05 |

<div class="box">

**The knowledge is the lever.** Told which conventions are in play, every reviewer acts on them, the free
one as much as the paid ones. Of the 17 asks on these PRs that no unbriefed session of any model reaches,
the briefed sessions reach 11. This is the answer key, so it is a ceiling, not a design. The design
question became: can the reviewer be given this without the answer key?

</div>

---

<!-- _class: small -->

# Q4 · The delivery design space, without the answer key

Each row is one way of getting the census into the reviewer, from least to most assertive.

| delivery | what the reviewer gets | result |
|---|---|---|
| guides and the catalogue as prompt text | Mathlib's written guidance, summarised | null: N=115 in June; the floor model's worst setting |
| the applicable list, picked from the diff | the 25 census entries a selector thinks apply | **+0.03** |
| pinpointed at the place, asked to verify | the right sentence at the right declaration | **0.00**: overridden at 9 of 21 places the answer key reached |
| asserted with precedence and examples | the picks stated as applying here, outranking the reviewer | **+0.20** on the eight PRs it was developed on; **0.00 and −0.01** on fresh PRs |
| deterministic detectors as packet facts | "this declaration departs from convention X" | valid, 2.9% of asks; with a disposition rule, 13 of 14 unasked facts filed |
| a filing contract: no withholding | a verdict per declaration and concern, silence refused | 14 of the 37 asks it was built for, at 4.9 findings per clean PR (bar 2.0) |
| dossiers and exams per convention | an evidence-built understanding, tested before use | not built: the bare sentence at the place already passes 25–29 of 39; examples made the model more conservative |

**The demand side.** Maintainers raise a convention at **5% or fewer** of the places its situation
occurs; predicting which places reads AUC 0.56–0.78 at about **7% precision**.

---

<!-- _class: small -->

# The mechanism, on one PR

PR #42814. The maintainer asked for `variable {D}` declared once rather than repeated. The reviewer held
that exact convention at that exact declaration, and wrote:

> "Mathlib does not require these, so I would not request them."

<div class="cols">
<div class="box">

**The assertion, not the content, carries the gain.** The same sentence at the same place moves the
reviewer when stated as *applying here*, not when offered for verification. That is why guideline
injection reads near null in every industrial report too.

</div>
<div class="box">

**But asserting without the answer key means asserting wrongly.** An ask-free pick of 25 entries holds
about 2.8 true asks. Under precedence the reviewer files the other 22 as well; under verification it
overrides the right ones.

</div>
</div>

<div class="box" style="margin-top:10px">

The conventions problem splits in two. **The model acts on a convention it is told applies:** solved.
**Which of the hundreds that apply would this maintainer raise here:** open, and every ask-free design
so far tried to answer it from the PR alone.

</div>

---

<!-- _class: small -->

# Where we stand, 14 October

| layer | claim | status |
|---|---|---|
| **knowledge** | the census holds what maintainers ask for; a reviewer acts on it when told it applies | **supported, replicated** on three models |
| **delivery without the asks** | the applicable conventions can be chosen from the PR and delivered for that gain | **not supported off-sample** |
| **understanding** (dossiers, exams) | richer representations fix misapplication | **not supported**; its pre-registered drop rule is met |

**What one session still misses.** A third of the asks escape every unbriefed session of every model,
spread across kinds, none above 8% of a set: naming judgement, statement and API design, a proof to try,
a library mechanism, a migration in progress, a scope conflict, PR history. The census tail, from the other side.

**The newest premise check** (13 October): of 41 asks the free reviewer never reaches, an artifact at the
base commit *decides* the fix for 7; for 19 the library *points to* the change but the ask is a choice
among its options (`ciSup` against keeping `continuous_`); 11 are judgement, 4 need the PR's history.

<div class="box" style="margin-top:4px">

**Publishable now, as a result about the task:** a convention census with its saturation curve;
knowledge, selection and filing separated by experiment; demand as a small, unpredictable subset of
applicability; the assertion mechanism. No other review system has measured any of the four.

</div>

---

<!-- _class: small -->

# What this says about the next design

<div class="box">

**A maintainer's decision to raise a convention, or not, is reasoning on evidence that can be
reconstructed**, though the comment never states it: positive evidence (the trigger holds here, the
library's precedent, the PR's intent) and negative evidence (an exception, a deliberate local deviation,
a cost). Taste is a small residual. `Dense.ciSup`: the statement is a supremum, the library names such
lemmas `ciSup`, the lemma is not about continuity, so `continuous_` goes.

</div>

So the harness should **gather and weigh the evidence a maintainer would**, not learn a preference from
the asks or predict demand from the PR's surface. Read that way, the options with a ceiling above the noise:

| option | ceiling on the sets we hold | cost |
|---|---|---|
| the harness for the free model: its own shell, files it rereads | about +0.10 by the Opus analogy, unmeasured for DeepSeek | $0 generation, a day to build |
| analogue retrieval for the design asks, delivered as a refutable fact | up to 0.075 of asks a set, the largest never-reached class | a measurement on 43 labelled asks first |
| a deterministic closer battery as packet facts | about 0.065 of asks a set | compute; a persistent Lean checker makes it minutes a PR |
| the per-place engine: every picked convention asked at every changed place | 0.40–0.55 of in-census asks, the only design above +0.10 | 25× the filings at 7% precision; needs the adjudication of unasked departures |

<p class="muted">All on 93 asks over 26 PRs used to develop the designs. The fresh 40-PR set has built workspaces and has never been read.</p>
