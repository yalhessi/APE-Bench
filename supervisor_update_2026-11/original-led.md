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
  blockquote { border-left: 6px solid #e0a020; background: #fff8e6; padding: 8px 18px; font-style: normal; }
  pre { font-size: 20px; }
  .cols { display: grid; grid-template-columns: 1fr 1fr; gap: 32px; }
  .cols3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 24px; }
  .box { border: 2px solid #1d2b53; border-radius: 10px; padding: 12px 18px; }
  .take { border-left: 6px solid #1d2b53; background: #f3f5fa; padding: 10px 18px; margin-top: 18px; font-size: 26px; }
  .source { color: #666; font-size: 18px; margin-top: 12px; }
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

# Reviewing Mathlib PRs: progress since the convening

## Supervisor update · 4 November 2026

**Yousef Alhessi** · University of Edinburgh

<!--
Original-led revision. Parts 1 and 2 follow the October deck; the theoretical slides
are unchanged. Part 3 keeps its thesis and Q1–Q4 sequence, updates the empirical
claims and adds the later convention experiments. No duration target is imposed.
See original-led-notes.md for the source correspondence and conventions motivation;
evidence.md supports the later results. Earlier drafts remain available for reference.
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

Decomposition, the solo baseline, then conventions

---

# The thesis, and the baseline

<div class="box">

**Understand the review process, then decompose it.** That is what can make a harness more useful than one agent with tools. So one agent with tools is the baseline, always.

</div>

**The baseline:** one session, the whole PR, the brief, the tools, and compile-my-edit.

**The questions:**

- **Q1:** What decomposition is effective?
- **Q2:** What limits the solo reviewer?
- **Q3:** What conventions does the community follow?
- **Q4:** Can that knowledge improve review on another PR?

<!--
Retains the October thesis and four-question progression. These are research questions;
the following slides identify the experiments that narrow each one. Historical baseline
results remain historical, rather than being presented as new November measurements.
-->

---

<!-- _footer: "Mathlib PR review · Q1: decomposition · September experiments" -->

# Q1 · What decomposition is effective?

**Experiment:** concern specialists plus a lead, against one whole-PR reviewer.

| 12 PRs, 23 obligations; GPT 5.2, reasoning off | Lead + arms | Solo |
|---|---:|---:|
| Obligations recovered per run, three repetitions | 7, 5, 6 | 4, 4, 1 |
| Recovered in all three runs | **5** | 0 |
| Findings on the two PRs with no recorded asks | 3, 4, 5 | **0** |
| Billed per run | $14.59 | **$1.90** |

<div class="take">

The generalist produced 64 of 71 matched finding occurrences. Specialists added little at 7.7× the total cost.

</div>

<!--
Source: ../docs/research/ab-heldout12-obligation-spine.md, registered obligation judge
v4-semantic-v3-v9-rubric. Lead includes a generalist and ten specialist arms; the
October label "ten arms + a lead" was imprecise. Runs are not cost-matched. Mean
superiority is unresolved at this sample size; lead and solo are complementary
(unions 7 and 8, jointly 13 of 23). No recorded asks does not certify a clean PR.
The 64/71 attribution is the October trace analysis: matched finding occurrences,
not 71 distinct historical obligations and not 64 distinct asks.
-->

---

# Q1 · Specialized arms fracture shared context

**The problem:** naming, generality and proof structure often depend on the same mathematical and library context. Each arm has to reconstruct it again.

**Example — #33421:** understanding the lemma supports three related questions:

- What should it be called?
- Is the numeral `2` essential, or can it be a parameter?
- Can its repeated argument be factored out?

<div class="take">

Our design lesson: keep the shared understanding together. Specialized checks can support it without becoming separate reviewers.

</div>

<!--
This states the user's design assessment, grounded in the overlap/context record;
it is not a measured causal attribution of the 7.7× cost. On #33421, lead missed
all three obligations; solo recovered naming and generality once each. Do not
claim this single case proves the cause of the lead's misses.
Sources: ../docs/research/ab-heldout12-obligation-spine.md (#33421),
../docs/research/review-work-structure-2026-09.md sections 3 and 7,
../docs/research/decompose-and-shrink-review-2026-10.md section 2. The latter's
~45% external-context figure is exploratory, so it is not a headline here.
Follow-ups removing pruning, forcing output and unifying the contract did not
establish a better specialist design: unpruned 2/10 vs solo 4/10; forcing 2→5
with control output 1→36; unified contract 3/10 below its 5/10 gate.
This narrows the tried decomposition; it does not rule out all decomposition.
-->

---

<!-- _class: dense -->

<!-- _footer: "Mathlib PR review · Q2: the solo baseline · Measurements through 14 October" -->

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

<div class="take">

Reasoning and harness repairs matter, but they do not close the gap. Next: inspect what reviewers miss.

</div>

<!--
- **Reasoning:** GPT 5.2 barely moves (2 → 2–3) though every session now finishes at a third of the cost. DeepSeek: 5 → 8, 6, 9, only with its thinking carried between turns.
- **Harness:** three harnesses with GPT 5.2 held reach the same. Ours costs Opus 5.5 about three asks against its own shell.
- **Model:** Opus 4.8 → 5 → 5.5 is 3 → 8 → 7–12. Not the prompt: Opus on GPT 5.2's exact messages reaches 10.

dev = twelve held-out PRs, 23 obligations, judge v9. post-cutoff = six PRs created after the Claude
models' cutoff, 16 asks, reach per session by blind matchers. "carried" = reasoning at high effort
with the reasoning items passed back between tool calls; "off" = no reasoning tokens. GPT 5.4 carried
reads 0.19 (ours) and 0.31 (Codex) on post-cutoff. Qwen's one reasoning-high run had its thinking
dropped by our client (defect found 7 October) and is not a reasoning reading.
-->

---

# Q2 · What is missing at places already inspected?

**Diagnostic:** 67 residual asks — **37 reached by nobody**, plus **30 reached only by Claude**.

In **63 of 67**, every reviewer that missed the ask had read, searched or compiled the relevant object.

| Mechanism identified by both readers | Asks, of 67 |
|---|---:|
| Convention or library-mechanism knowledge (`to_fun`, naming, dot notation) | **25** |
| A check nobody tried (`positivity`, `simpa`, the old proof) | **19** |
| An analogue in the library not compared | **6** |

<div class="take">

More coverage is not the first lever suggested by this audit. Can we supply the knowledge needed to reach a different conclusion?

</div>

<!--
Sources: ../results/pr_review_v5/probes/phase1-residual-mechanisms-2026-09-30/mechanisms.md
and ../docs/plans/2026-09-30-post-carryover-replan.md, final Phase 1 result.
Two readers over 141 ask/reviewer pairs; non-exclusive mechanism labels. The counts
are transcript-based model judgments. Four asks were never attempted; two were
verified and withheld. The 67 are NOT all Claude successes over GPT, as the original
slide said. The audit's stated consequence was not to fund a coverage-motivated
lead/carried-reasoning run; try-it and convention supply were pursued directly.
-->

---

# Q3 · Why study conventions?

**Earlier clue:** readers could state a principle behind **30 of 31 design asks**, but only **8** were documented.

**The question we posed on 29 September:**

> “It's really learning what conventions hold at a given point and in a given window/scope that is fundamentally hard.”

How many conventions are there? Where do they hold? What happens when they conflict?

<div class="take">

The census asks what the knowledge is. The ceiling experiment asks whether supplying it can help a reviewer.

</div>

<!--
Source: ../docs/todo/conventions-nature.md, opening user statement dated 2026-09-29
and motivating design-comparison-val1000-v1 reading. Recorded at b291e80d.
The 30/31 and 8 counts belong to that design-ask reading, not all review asks.
Conventions work predates the residual audit: the 10 September drift plan addressed
missed evolving idioms, and the 11 September catalogue sought a denominator beyond
a few familiar examples. The 29 September prompt motivates the census in the form
used here. The 30 September residual audit adds intervention evidence. On 4 October,
the user explicitly requested a best-case/ceiling test before further designs:
../docs/todo/conventions-ceiling-probe.md, recorded at 898a7be5.
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

The experiments ask how many such entries we need, whether supplying them helps, and whether their triggers and scope describe actual practice.

</div>

---

# Q3 · How many conventions? The census

**How:** two independent model readers summarized the principles behind **1,833 first-round validation asks**, each keeping a running codebook.

- **409 and 407 entries** at this grain; neither reading had saturated.
- **Small head, long tail:** top 10 cover 22%; top 50 cover 55% of principled asks.
- On 14 PRs outside the census, an entry describes **39 of 46 asks (85%)**.

<div class="take">

A substantial inventory of review concerns. Whether each entry is a valid rule, and where it applies, remain separate questions.

</div>

<!--
Evidence E1 and ../docs/todo/conventions-nature.md, Study 1 result. The initial
codebooks are 409/407; later expanded or merged views (438, 399) are not pooled.
The nominal thousand-PR validation draw had 973 available PRs; the slide uses the
ask count to avoid implying 1,000 ask-bearing PRs. These entries are reader-produced
principles, not 400 independently established community rules. The readers share a
model family. One ask in ten was estimated to introduce another principle.
-->

---

<!-- _class: tbl -->

# Q3 · Does knowing the convention help? The ceiling

**Experiment:** select entries using the PR's historical asks; give the reviewer those general sentences, without locations.

| Reviewer | Repetitions | Unbriefed | Exact brief |
|---|---:|---:|---:|
| Opus 5.5 | 2 | 46–49% | **74%** |
| GPT 5.5 | 1 | 19% | **41%** |
| DeepSeek-V4.1-Flash | 3 | 22% | **44%** |
| DeepSeek + examples and precedence | 3 | 22% | **64%** |
| Qwen3.5-397B | 3 | 3% | 9% |

<div class="take">

A conditional positive: the entries help when selected using the answer. Can we obtain the gain without that selection?

</div>

<!--
Evidence E1, synthesis section B and ceiling probe results. In-census ask reach
within each original comparison, 39 asks across 14 ask-bearing PRs. Percentages
rounded; matcher and seal details remain in the linked record. Rows are not a
pooled or common-seal model ranking. The DeepSeek variants share their unbriefed
comparison. Exact supply conveys relevance as well as content; no locations does
not make it answer-free. The Qwen row is ~.034→.085, +.051, not a strong local-model
unlock. For GPT's separate disposition positive under exact supply, see backup.
-->

---

<!-- _class: tbl -->

# Q4 · Getting the knowledge in without the answer key

**Experiment:** select from the diff, then vary how the entries are delivered.

| Delivery | Result in the tested comparison |
|---|---|
| General guides in the prompt | No gain in the earlier GPT comparison |
| Select 25 entries from the diff | Entry for 22/33 asks; Opus gain **about +3 points** |
| Guarded rules, pinpointed at places | Opus gain **0 points** |
| Selected entries + examples + precedence | Initial gains; no reliable gain across the later sets |

<div class="take">

Supplying relevant topics did not reliably reproduce the ceiling gain. What judgment was the exact brief doing for the reviewer?

</div>

<!--
Evidence E1, synthesis sections A–D and conventions-assessment-2026-10-12.md.
The guidelines comparison used 57 PRs/115 obligations and the older topical judge;
do not compare its magnitude with ask reach. Stage F selector contained entries
for 22/33 asks, Opus +.026; stage G .000. DeepSeek AP: initial +.18 on used
validation PRs, .00 post-cutoff, -.01 dev. Opus AP: initial about +.20, dev
+.02–.09 with intervals including zero. These are distinct samples/designs.
Deterministic head detectors covered ~2.9% of asks; exhaustive application and
forced filing added substantial burden. Neither proves all unmatched findings
wrong. The detailed reference and experiment map retain these omitted variants.
-->

---

# Q4 · The mechanism, on one PR

**#42814:** the maintainer asked for `variable {D}` declared once.

Opus held the convention at the relevant declaration, then wrote:

> “Mathlib does not require these, so I would not request them.”

**The topic arrived. The decision differed.** In the earlier experiments, asserting that a convention applied could change that decision.

<div class="take">

That leaves a harder question: is the rule right here, and is its benefit worth requesting a change?

</div>

<!--
Retains the October example. Evidence E1, stage G and subsequent precedence/ladder
results. Do not retain the original universal "application solved" conclusion or
turn assertion into a validated delivery policy. Assertive instructions were tested
with target-derived entries; the separate GPT positive is in backup. Actual validity
and request value require evidence beyond historical agreement.
-->

---

<!-- _class: tbl -->

# Q4 · First check what “applies” meant

**Follow-up:** inspect flagged code and known fixes, rather than infer applicability from survival at merge.

| Convention | What the check found |
|---|---|
| Predicate namespaces | **85–97%** of selected unasked survivors were **not departures** under the reconstructed rule |
| Dot-notation calls | **12–13 of 16** checked survivors were genuine departures that merged unasked |
| Primed names | Both readers found only **4/6** known fixes; the revised rule failed calibration |

<div class="take">

Withdraw the old “≤5% of applicable places” claim. Incorrect rules and genuine unasked departures were mixed together.

</div>

<!--
Evidence E3, final corrections. Small selected strata, not population rates.
Scope, rule precedence, incomplete ask counting and attention all affected the old
denominator. Survival cannot show that a maintainer knowingly accepted a departure.
The dot-notation result prevents the opposite overclaim that all unasked cases
were simply bad rules. The six form-rule practice study is in backup (E4).
-->

---

# Q4 · Can the library settle the choice?

**Diagnostic:** inspect **41 asks** the free reviewer never reached.

- In **5–7**, library evidence decides the change.
- In **19**, it supplies ingredients, but a choice remains.

**Example:** finding `to_fun` connects a hand-written family to a generated alternative. Whether to adopt it still depends on interface and import costs.

<div class="take">

Next test: acquire conditional reasons from earlier PRs, then ask whether they improve ordinary review elsewhere.

</div>

<!--
Evidence E5–E6. Library-knowledge diagnostic: two readers, selected 41-ask residual;
5–7 and 19 are not a general population estimate. The to_fun reconstruction/source
probes are separate selected-case experiments. After fixing symlink search, all six
assisted Opus sessions connected the alternative; baseline 0/3, correspondence 0/3,
correspondence+adoption 1/3 historical recovery. Some constructions/import checks
failed, and some interface costs were real; connection is not a compiled full
replacement or an obligation to adopt it. Stated-grounds reading is mixed and does
not establish the old claim that taste is a small residual. Pilot details in backup.
-->

---

# Q4 · Can independently acquired notes transfer?

**Experiment:** acquire six entries from earlier sources, check and repair them, then freeze them before whole-PR review.

| Arm | Same Opus 5.5 reviewer receives |
|---|---|
| A | Ordinary inputs and tools |
| B | The same + compact notes |
| C | The same + full conditional notes |

**6 PRs × 3 arms × 3 repetitions = 54 final reviews.**

All six notes go to every treatment review. No target-specific assertion that a rule applies.

<!--
Evidence E8–E9. Compact/full acquired from the SAME eligible earlier sources;
B is not the historical census. Entries: namespace, name order, grind registration,
to_additive, generality, simp/iff orientation. Developmental cases; source selection
steered by known targets and disclosed. Reserved checks and repairs are specification
checks, not a controlled compact/full effectiveness result. Primary opportunities
namespace, automation, generality, plus contrary targets. No fresh autonomous
population claim follows. Date gates and target exclusions remain in protocol.
-->

---

<!-- _class: tbl -->

# Q4 · The notes did not recover the primary concerns

| Primary concern | A: ordinary | B: compact | C: full |
|---|---:|---:|---:|
| Namespace choice, #33294 | 0/3 | 0/3 | 0/3 |
| `grind` proof families, #33098 | 0/3 | 0/3 | 0/3 |
| Generalize the numeral, #33421 | 0/3 | 0/3 | 0/3 |
| **All historical asks, mean recovery** | **35.6%** | **34.4%** | **41.1%** |

The notes arrived; the intended alternatives still did not become requests.

<div class="take">

Narrow the question: if we supply the declaration and concern, can the reviewer construct the alternative and judge its value?

</div>

<!--
Evidence E8; two matcher replications agree on all 270 reached/not-reached cells.
Each primary row is a separate concern on its PR. The grind pair is one concern.
All-ask denominator: 30 asks per repetition; finalized findings 165/158/168.
The primary progression rule fails. The 5.5-point full/ordinary descriptive
all-ask difference is not a demonstrated population effect. Primary concerns were
absent at submission as well as finalization, not lost during serialization.
The 491-finding usefulness panel is unlabelled; historical recovery is not quality.
The namespace form was not requested, generality not proposed, and no target grind
proof was tried. The notes' topics did not map perfectly to these opportunities.
An exploratory dslope addition outside the historical reference is in backup.
-->

---

<!-- _class: tbl -->

# Q4 · Is focus enough?

**Diagnostic:** supply a declaration and concern; compare no note with its frozen note, three repetitions per condition.

| Target | Without note | With note |
|---|---|---|
| Namespace | Intended form absent, 0/3 | Formulated **2/3**; declined both |
| Generality | Constructed **3/3**; one reached request, one partial | Constructed **3/3**; all declined |
| Automation | No target `grind` proof | Same; probe asked about **registration** |

<div class="take">

Focus can expose an alternative. Constructing it and deciding to ask for it are separate steps.

</div>

<!--
Evidence E10–E11. 72 sessions including sibling cases, not 72 independent PRs;
three selected target PRs, Opus 5.5, three repetitions/cell. Conditional diagnosis,
not ordinary autonomous review. All six generalizations have successful verified
edits; their parameter domains/statements differ. No case passed the registered
progression rule for autonomous step 2, which did not run. Automation is not a
clean test of discovering a proof simplification because its question concerns
registration. Historical silence on siblings is not a wrong label.
-->

---

# Q4 · Generality: constructed, then declined

**#33421:** a lemma about `2 * fract x = 1`.

With the declaration and generality question supplied, **all six sessions compiled a parameterized version**, keeping the original as a corollary.

With the note, all three declined to suggest it. One compiled essentially the maintainer's form, then wrote:

> “The constant 2 is what the lemma is about.”

<div class="take">

The technical alternative is available. Does the reason for keeping the specialization distinguish useful restraint from a missed improvement?

</div>

<!--
Evidence E10–E11. Retains the detailed November example without treating its
historical maintainer as an independent usefulness adjudicator. No-note: two
requests, one reached/one partial. With-note: zero. Three samples per condition
do not show a stable causal harm from notes. The note favored generalizing proof
artifacts; the reviewer invoked that condition, plus sometimes lack of another
caller, to decline. The broad next question is decision quality with checked
candidates fixed, not forcing this historical answer. No exact synthesized theorem
is printed: the six emitted generalizations differ.
-->

---

<!-- _class: tbl -->

# Where we stand, 4 November

| Question | What the experiments support |
|---|---|
| **Decomposition** | The specialist arms are unpromising; preserve shared context |
| **Knowledge** | Target-selected conventions can substantially improve recovery |
| **Transfer** | Ask-free selection and the acquired bank did not establish a reliable gain |
| **Application and choice** | Focus can reveal checked alternatives that are then declined |
| **Evaluation** | Historical agreement, feasibility and usefulness are different; usefulness remains unfinished |

<!--
Synthesis of Q1–Q4, not a universal impossibility result. Exact supply has several
conditional positives, including GPT disposition (backup). Acquired-bank primary
failure is bounded to six development PRs and the tested notes. Focus is conditional.
The 491-item bank and 66-item pilot usefulness panels remain without completed
labels in the inspected records. The earlier hypothesis that taste is a small
residual is withdrawn; see E5. Current sources checked for the 4 November update.
-->

---

# What this says about the next design

**Proposed next question:** when a reviewer has a checked alternative, do its reasons for declining it identify when a suggestion is worthwhile?

Hold the alternatives fixed; compare nearby cases with different benefits and costs before building another whole-PR intervention.

**For discussion:**

- What makes extra generality or library reuse worth asking for?
- What evidence would justify keeping the existing form?
- How should we judge useful additions beyond the historical review?

<!--
Evidence E11, ../docs/research/review-harness-next-question-2026-10-27.md.
Recommendation, not an executed experiment or frozen protocol. Use independently
judged value and contrasting cases; familiar targets are development evidence.
A narrower selected-case closeout does not complete an overall usefulness panel.
Retains the October "next design" role while replacing its now-unsupported ceiling
estimates and universal prescription with questions the evidence leaves open.
-->

---

<!-- _class: tbl -->

# Backup · Instructions can help under exact supply

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

# Backup · More investigation, same recovery

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

# Backup · Does a written rule describe practice?

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

# Backup · A possible gain beyond historical matching

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

<!-- _class: dense -->

# Backup · The same five points, in our experiments

| Earlier point | What our experiments now say |
|---|---|
| **Tell the reviewer the standard** | General guides did not help in the older comparison; exact convention supply does. Ask-free transfer is unresolved. |
| **Evidence and request value** | Compiling an alternative establishes feasibility. The usefulness panels are still unfinished. |
| **Diversity and recall** | Earlier run unions recover more asks; measure their additional comment burden too. |
| **Decomposition** | The generalist produced most specialist-system matches. The tried arm designs do not justify repeating shared understanding. |
| **Silence and the filing bar** | Forcing can increase volume sharply. GPT disposition improved recovery with exact briefs; DeepSeek forcing did not unlock never-reached asks. |

<!--
Keeps the October return to the literature's five points, qualified by later results.
Sources: original October baseline records; E1–E2 and E8–E11. No universal claim that
voting always hurts, silence must be forbidden, all nonmatches are noise, or a
lower bar improves overall review quality. Decomposition is the user's current
design assessment of the tried specialist arms, not a ban on specialized tools.
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

<!-- _class: tbl -->

# Backup · sources

**Deployed reviewers.** BitsAI-CR, ByteDance (2501.15134) · AutoCommenter, Google (2405.13565) · RovoDev, Atlassian (2601.01129), HalluJudge (2601.19072) · uReview, Uber · Bugbot, Cursor · Codex reviewer, OpenAI · Anthropic Code Review and the open plugin · open-code-review, Alibaba, with AACR-Bench · Qodo 2.0 · CodeRabbit (2607.03316) · Greptile v4 · Semgrep Assistant. Tricorder (ICSE'15), Infer (CACM'19).

**Benchmarks and studies.** SWR-Bench (2509.01494) · SWE-PRBench (2603.26130) · c-CRAB (2603.23448) · CodeReviewer (2203.09095) · Code Review Bench, Martian · Adversarial Review (2608.18167) · LLM ensembles for code (2510.21513) · Harness Engineering (2609.00006) · Di Biase et al. (1805.10978) · Kamalı et al. (2605.17548).

**Mathlib.** MathlibPR (2605.07147) · ProofJudge (2608.20432) · Growing Mathlib (2508.21593) · APE-Bench (2504.19110).

**Ours.** `docs/research/code-review-systems-survey-2026-09.md`, `open-code-review-comparison-2026-09.md`, `conventions-assessment-2026-10-12.md`.
