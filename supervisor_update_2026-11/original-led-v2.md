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
The October task formulation remains the starting point. This revision makes the
solution/acceptance distinction explicit, brings conventions into the formulation,
and removes the boxed closing sentences from the first section. The former design-
space section is folded into the empirical questions; its comparison tables remain
in backup. The experimental opening follows the user's requested baseline → misses
→ specialized review → judgment → conventions → ceiling progression. This is an
argument order, not a claim about the chronology in which studies were designed.
See original-led-notes.md and evidence.md. Earlier presentation sources are preserved.
-->

---

<!-- _class: section-title -->

# 1 · The problem

What are we actually asking a reviewer to do?

---

<!-- _class: formulation lg -->

# The shared pieces

```text
Library     L = (C, P)          code C, and a purpose P        the library's overall purpose
PR          (δ, p)              a diff δ, and a purpose p      what this change is for

merge(C, δ)                     the code after δ               defined iff the patch applies
merge(C, δ) compiles            the kernel accepts it
δ realises p in C               the diff does what p says      decided by a judge

S(C, p)  =  { δ : merge(C, δ) compiles  ∧  δ realises p in C }      the solutions of a task
```

---

<!-- _class: formulation lg -->

# APE-Bench

```text
given        (C_b, p)            p stated as an instruction, cut from a real commit
emit         δ
correct iff  δ ∈ S(C_b, p)       the kernel decides "compiles", a judge decides "realises"
```


<!--
The paper (arXiv 2504.19110, Sections 3 and 4.1) gives this in prose: instruction, pinned
environment, boundaries, verification protocol; "compilation plus semantic validation". Best
evaluated agent: 47 of 100 tasks.
-->

<div class="source">APE-Bench · arXiv 2504.19110</div>

---

<!-- _class: formulation lg -->

# Reviewing

```text
given      (C_b, δ, p)          library purpose P in the background
emit       D                   a set of requests

Preference   ≽_t on S(C_b, p)    which solutions the community favours
Acceptable   A_t ⊆ S(C_b, p)     mergeable without a required revision

request    a test on revised PRs that the submitted δ fails
witness?   a revision that passes, compiles, and still realises p

aims       sound:     requests the community would endorse
           coverage:  identifies a required change when δ ∉ A_t

one round  δ_{i+1} = author(C_b, p, δ_i, D_i)
```

<!--
Retains the October objects: task purpose p, library purpose P, solution set S,
preference relation, acceptance set, requests and optional witnesses. A_t now has
an explicit idealized interpretation instead of "the region ≽ does not require
leaving", which hid the missing acceptance judgment. A preference relation alone
does not identify A_t. The old completeness condition requiring a single test
passed by EVERY acceptable revision was stronger than this informal task account
justified; coverage here states the intended task without that universal claim.
A request may be optional even when δ is already acceptable. Endorsement and
coverage are aims; historical matching only observes one sample of requests.
No claim of an identifiable global partial order or automatic acceptance oracle.
-->

---

# Extending what we can check

| Role | Contribution |
|---|---|
| **Compiler, kernel, tests** | Help separate solutions from non-solutions by checking explicit requirements |
| **Human reviewers** | Identify acceptable or preferred solutions using further community standards |
| **Automated reviewer** | Capture human review, or a useful subset, as additional checks |

```text
S_R(C, p) = { δ ∈ S(C, p) : δ passes the additional review checks R }
```

The aim is to exclude more unacceptable contributions from what passes, while retaining acceptable ones.

<!--
User's revised framing: automated systems help separate solutions/non-solutions;
reviewers identify accepted/preferred solutions; automating human review, or part
of it, makes more unacceptable solutions fail the combined system's requirements.
S_R denotes that refinement rather than changing the meaning of the original S.
R is the subset of required-change judgments we automate, not a claim that all
human preferences are blocking requirements. Ideally A_t ⊆ S_R ⊆ S, with fewer
members of S\A_t surviving. This is an aim, not a property established for our
current reviewer: false rejections and missed requirements must both be assessed.
Tests need not completely decide "realises p"; the slide says they HELP separate
solutions/non-solutions. Review can also uncover correctness or specification
failures missed by the existing checks. Some reviewer preferences remain advisory,
guiding improvement among solutions that pass. No recorded comment is automatically
a valid reusable check, and historical silence is not proof of acceptance.
-->

---

# Conventions in this formulation

A convention describes a **situation, scope, preferred form and exceptions**. These are candidate standards for the automated reviewer to capture.

```text
An applicable convention can support       δ′ ≽_t δ
A convention treated as a merge requirement can constrain membership in A_t
```

- It supplies a reason for a preference or requirement; other reasons can outweigh it.
- Knowing a general principle still leaves its application and priority to be judged.
- A reliable requirement can become an additional check; preferences can guide improvements among solutions that pass.

<!--
Brings the October convention/trigger account into the opening formulation rather
than introducing it only after experiments. The two roles are not a partition of
all conventions into fixed categories: a convention's force can depend on context.
Conventions are evidence for the relation and sometimes acceptance requirements;
they are not claimed to exhaustively determine ≽_t or A_t. A technical rule may
also be part of the declared task p. The census entries are candidate descriptions
of these practices, not automatically validated rules. Scope includes area and date.
Adding a blocking check requires establishing both the rule and its force here;
a mere preference for an alternative does not make the original unacceptable.
Source background:
../docs/todo/conventions-nature.md; evidence E1 and E3–E5.
-->

---

<!-- _class: tbl -->

# The formulation on four PRs

| PR | What the review said | What this illustrates |
|---|---|---|
| **#33149** | Three vacuous definitions; 19 axioms | Compilation does not establish that the claimed task was accomplished |
| **#33305** | One doc-comment line too long | A presentation requirement can matter even when the mathematics is unchanged |
| **#33304** | Nothing | An empty review is observed; it does not certify membership in A_t |
| **#33098** | Make this proof one tactic call | `grind` and `simpa` give feasible alternatives; feasibility alone does not settle preference or request value |

<!--
Retains the four familiar examples from the October framing. Removes the unsupported
inference from no recorded requests to known acceptability, and avoids claiming that
severity labels identify an empirical S/A boundary. For 33149, failure of "realises p"
assumes the stated purpose is to prove the advertised mathematics under the accepted
assumptions; compilation alone cannot certify that. For 33305, the historical request
is evidence of one reviewer's requirement, not an independently adjudicated community
acceptance label. The October "4 of 23" classification is not an estimate of A_t.
-->

---

# What a reviewer has to do

1. **Membership.** Does the PR accomplish its task? Compilation settles only part of this.
2. **Placement.** What alternatives are relevant, and which does current library practice favour?
3. **Request.** Which differences require a revision, or are worth raising as improvements?
4. **Update.** As the library and practice change, the relevant comparisons and conventions change too.

<!--
Keeps the October membership/placement/request/update structure. Removes the early
"the wall" verdict from the definition of the task; experiments establish particular
failure stages later. Relevant pair comparisons can inform placement. Preference,
required revision and optional request value remain distinct decisions.
-->

---

# What the formulation leaves open

- **The acceptance boundary:** which expectations are requirements, and which are preferences?
- **The conventions:** what holds in this area and period, with what exceptions?
- **The comparisons:** which alternative exposes a consequential difference?
- **The automation:** which reviewer judgments can we reliably turn into checks?
- **The evidence:** a historical review records some requests, not the whole standard.

Generating an alternative gives a pair to compare. We still need to judge the difference and whether it warrants a request.

<!--
The formulation names the unknowns rather than solving them. A_t is not recovered
from the existence of a better witness, and historical silence is not a negative
usefulness label. The pair-comparison route is an empirical hypothesis; the main
experimental section reports its tested reconstruction version alongside the later
transfer work. The full previous-work comparison remains in backup.
-->

---

<!-- _class: section-title -->

# 2 · Building a reviewer

Four questions about why the reviewer misses what maintainers ask for

---

# What have we learned about building a reviewer?

| | Question | Answer so far |
|---|---|---|
| **A** | Would **more focused attention** resolve the missed requests? | **Not enough in our tests.** Misses persist after inspection or specific instructions. |
| **B** | Does supplying the **right convention** help? | **Yes, when chosen using the human review.** This supplies both the convention and its relevance. |
| **C** | Can we get that benefit **without knowing the maintainer's requests**? | The methods tested so far have **not reliably reproduced that gain**. |
| **D** | If it can **construct the change**, will it request it? | **Not necessarily.** Reviewers can construct and check changes, then decline to request them. |

<!--
These questions and answers are the main takeaways. The following experiments
provide the evidence; slide 30 returns to the same questions. This is argument
order, not the chronology in which studies were designed (see original-led-notes.md).
A and B were reported in October; C is partly October (ask-free selection) and
partly new (the generated alternative, the acquired notes); D is new.
A asks about attention; specialized reviewers are one intervention, not the
question itself. It combines the specialist comparison with the residual and
specific-brief audits. The 7.7× cost shown in the specialist result is
billed cost in the dated GPT-5.2 comparison, not a cost-matched estimate or a claim
about current solo models. Inspection does not establish consideration of the
relevant alternative, and attention failures still occur. B supplies relevance as
well as convention content by selecting entries from target historical requests.
C is bounded to the tested delivery methods; it does not show conventions cannot
be acquired or used independently. D is a selected-case diagnosis, not proof that
declining the change is wrong. Sources remain in the speaker notes.
The result slides retain the setup needed to interpret each figure. Detailed
comparison conditions, dates and instruments are in their speaker notes.
-->

---

# What is a good baseline?

Start with **one reviewer, the whole PR, and tools**:

- Read the purpose, diff, surrounding code and library.
- Search for definitions and precedents; check proposed edits.
- Return the requests it judges worth making.

A more elaborate system must improve on this baseline, accounting for cost and extra comments.

<div class="source">MathlibPR: merge readiness. SWR-Bench and SWE-PRBench: review requests.</div>

<!--
The solo session with tools is the baseline, not an assumed successful design.
MathlibPR 2605.07147 asks about readiness; SWR-Bench 2509.01494 and SWE-PRBench
2603.26130 concern review generation. Sources and formal mapping retained in backup.
Historical experiments used several models and harnesses; the baseline must be
controlled within each comparison. Later reasoning/tool repairs and stronger solo
models prevent treating a gain over old GPT-5.2 as a gain over current solo review.
The model/harness table is retained in backup, not interposed in the argument here.
Historical ask recovery is one measurement, not an exhaustive usefulness score.
-->

---

# What does the solo reviewer miss?

**12 PRs; 23 individual changes requested by maintainers.** Solo GPT 5.2, with reasoning off, recovered **4, 4 and 1** across three runs.

| Example | What was missing |
|---|---|
| Doc-comment line too long | The relevant location was never reached |
| Naming and generality | Requests were inconsistent or absent despite reaching the declarations |
| Hand-written theorem family | A generated alternative was found in only one of three runs |

Could dedicated passes catch more?

<!--
Comparison and measurement details (moved from the former on-slide box):
Compare three runs of one reviewer, nothing added · Held fixed GPT 5.2 with reasoning off, tools, 12 held-out PRs · Measured obligations recovered of the 23 the maintainers asked for, registered judge [Date: Sept]

Additional reference detail:
The 23 individual requested changes are atomic obligations under registered judge v4-semantic-v3-v9-rubric, not a raw-ask denominator. Examples: #33305 doc-comment line, #33421 naming and generality, #33117 generated fun_* family and to_fun.

Evidence E13, ab-heldout12-obligation-spine.md. GPT-5.2 reasoning off, three reps,
23 obligations, registered judge v4-semantic-v3-v9-rubric. In that source, location
means a candidate at the gold site; it is not proof that the precise alternative was
considered. #33421 solo naming and generality each reached once; repeat factoring
located all three times, never recovered. #33117 solo HLL. The narrative is a
logical motivation for decomposition, not a claim that these A/B runs preceded
all specialist design historically. This weak-model baseline is dated explicitly.
-->

---

# A · Would specialized reviewers catch more?

Separate passes for **proof, naming, generality and other concerns** might catch what one general pass misses.

A lead reviewer combines findings from **one generalist and ten specialists**.

Test against solo review: same twelve PRs, GPT 5.2 with reasoning off, same tools; three runs each.

<div class="source">Di Biase et al.: decomposing diffs found no more defects. Alibaba: file grouping reduced recall.</div>

<!--
References are placed before our experimental result rather than in a standalone
literature section. Di Biase et al. 1805.10978; Alibaba record in
../docs/research/open-code-review-comparison-2026-09.md and the saved review-systems
survey. Their tasks/decompositions differ; they motivate a controlled comparison,
not an inference that all specialization fails. Our A/B cost is not matched.
-->

---

# A · What did the specialist design buy?

Same 12 PRs and 23 requested changes; three runs of each design.

| | Lead + specialists | Solo |
|---|---:|---:|
| Requested changes recovered, of 23 | 7, 5, 6 | 4, 4, 1 |
| Cost per run | $14.59 | **$1.90** |

A modest gain at **7.7× the cost**. Most comments matching maintainer requests came from the generalist.

<!--
Comparison and measurement details (moved from the former on-slide box):
Compare a lead with a generalist and ten specialist arms, against the solo reviewer · Held fixed the 12 PRs, GPT 5.2 with reasoning off, tools, three runs each · Measured obligations recovered of 23, registered judge; billed cost per run [Date: Sept]

Additional reference detail:
Additional table rows retained from the previous draft: recovered in all three runs, lead 5 / solo 0; findings on the two PRs with no recorded asks, lead 3, 4, 5 / solo 0. Trace attribution: the generalist produced 64 of 71 matched finding occurrences across repeated reviews, not 64 unique maintainer requests.

Source: ../docs/research/ab-heldout12-obligation-spine.md, registered obligation judge
v4-semantic-v3-v9-rubric. Lead includes a generalist and ten specialist arms; the
October label "ten arms + a lead" was imprecise. Runs are not cost-matched. Mean
superiority is unresolved at this sample size; lead and solo are complementary
(unions 7 and 8, jointly 13 of 23). No recorded asks does not certify a clean PR.
The 64/71 attribution is the October trace analysis: matched finding occurrences,
not 71 distinct historical obligations and not 64 distinct asks.
-->

---

# A · Why this decomposition is unpromising

Naming, generality and proof structure depend on the **same mathematical and library context**. Each specialist has to reconstruct it.

On **#33421**, understanding one lemma supports three questions:

- What should it be called?
- Is `2` essential, or can it be a parameter?
- Can its repeated argument be factored out?

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

# A · Are missed requests simply overlooked?

**67 requests missed by solo GPT 5.2**, audited in transcripts from GPT 5.2 with reasoning enabled and Opus 5.5.

| What the transcripts showed | Requests, of 67 |
|---|---:|
| Every reviewer that missed it had inspected the relevant code | **63** |
| A reviewer concluded the code was fine | **40** |
| A reviewer pursued a different change | **25** |

Categories overlap. Inspecting the code does not establish that the right alternative was considered.

<!--
Comparison and measurement details (moved from the former on-slide box):
Population the 67 asks solo GPT 5.2 never reached: 37 reached by no reviewer, 30 reached only by Opus 5.5 · Reviewers GPT 5.2 with reasoning carried, and Opus 5.5 · Measured two blind readers label the transcript at each missed ask; a count needs both readers [Date: 30 Sept]

Additional reference detail:
The 67 requests were missed by the solo GPT-5.2 baseline: 37 were reached by no reviewer and 30 only by Opus 5.5. The omitted never-attempted category has 4 requests. Inspection is not proof of attention to the right issue.

Evidence E13, residual-mechanisms 2026-09-30. Two readers, 141 ask/reviewer pairs;
mechanism counts require both readers and count an ask if any relevant reviewer has
the label. The 63 figure requires every missing reviewer to have attended the object.
Never attempted 4, verified/withheld 2. Labels are judgments from transcripts/notes,
not direct observation of hidden reasoning. This is why the on-screen claim is
narrower than "models make the same decision regardless of focus". Knowledge/
convention mechanism 25; try-it-not-tried 19; analogue-not-compared 6. These are
later mechanism labels, not proof that all 63 understood and rejected the ask.
-->

---

# A · Does spelling out the check solve it?

Specialist instructions named the specific check behind **17 of the 23 requested changes**. One asked about:

> “every member fixed to `2` where `k` would do”

The specialist investigated a different family and did not request the generalization.

**More focused attention has not been enough.** Which standard is the reviewer applying?

<!--
Comparison and measurement details (moved from the former on-slide box):
Audit the specialist briefs against the 23 obligations · Reviewer the GPT 5.2 arms above · Measured obligations whose brief names the specific check, by the more conservative of two readers; then whether the arm made the request [Date: Sept]

Evidence E13, the-question-is-already-asked-2026-09.md. Two model readers; the second
conservatively counted 17 full, 4 partial, 2 none. Seven of the 17 full cases relied
on text written after inspecting these very PRs; this is a development diagnostic,
not a generalization result. The numeric-constant prompt is one such tailored case.
The generality question was contested between family/generalist remits. The target
family_design arm ran on the generality obligation in all five inspected runs and
looked at a different family. Other missed asks were pruned or blocked by evidence/
compile contracts. Therefore neither "focus never helps" nor "all misses are
verified changes withheld" is licensed. Forcing/no-pruning/unified-contract results
also failed to establish a strong specialist route; retained in source notes.
-->

---

# B · Which standard should the reviewer apply?

In a reading of **31 design requests**, a principle could be stated for **30**, but only **8** were documented.

This separates two questions:

1. **Discovery:** what conventions hold, and where?
2. **Use:** if we supply the right convention, does review improve?

<div class="source">Tricorder: automated analyzers. AutoCommenter: comments about documented best practices.</div>

<!--
Comparison and measurement details (moved from the former on-slide box):
Reading 31 design asks from the validation PRs · Measured whether a reader could state the principle behind the ask, and whether Mathlib documents it [Date: 29 Sept]

Additional reference detail:
This is the selected reading of 31 design asks from validation PRs. The hypothesis is that the reviewer needs evidence about what current library practice expects in this situation.

Retains the motivation for conventions while connecting it to the judgment problem.
The 30/31 and 8 counts are a selected design-ask reading, not the entire review
population. ../docs/todo/conventions-nature.md records the user's 29 September
scope/time/conflict questions; the 30 September residual audit identifies 25
knowledge/convention cases. On 4 October the user requests a best-case ceiling
before further intervention designs. This argument order is not the exact discovery
chronology. Scope, priority, exceptions and even rule validity remain hypotheses;
we do not identify all judgment failures with missing convention knowledge.
References: Tricorder, ICSE 2015; AutoCommenter, arXiv 2405.13565. These are
comparisons with review assistance, not claims that their rules cover Mathlib's
unwritten standards. See the saved review-systems survey and comparison backup.
-->

---

# B · How many conventions?

Two Opus 5.5 readings of **1,833 first-round requests across 973 PRs**, each keeping a list of distinct conventions.

- **409 and 407 entries**; new conventions were still appearing.
- The top 10 cover **22%**; the top 50 cover **55%** of requests with an identifiable principle.
- On 14 further PRs, an entry describes **39 of 46 requests**.

These are **candidate conventions**. Their scope and exceptions still need checking.

<!--
Comparison and measurement details (moved from the former on-slide box):
Readers two independent Opus 5.5 sessions, each keeping a running codebook · Input the 1,833 first-round asks on the 973 validation PRs · Measured distinct principles per codebook; coverage checked on 14 PRs outside the census [Date: early Oct]

Evidence E1 and ../docs/todo/conventions-nature.md, Study 1 result. The initial
codebooks are 409/407; later expanded or merged views (438, 399) are not pooled.
The nominal thousand-PR validation draw had 973 available PRs; the slide uses the
ask count to avoid implying 1,000 ask-bearing PRs. These entries are reader-produced
principles, not 400 independently established community rules. The readers share a
model family. One ask in ten was estimated to introduce another principle.
-->

---

# B · A best-case test: supply the right convention

Select conventions **using the human review**, then supply general statements without code locations.

On 14 further PRs, measure recovery of the **39 requests covered by the convention list**:

| Reviewer | Without conventions | With selected conventions |
|---|---:|---:|
| Opus 5.5 | 46–49% | **74%** |
| GPT 5.5 | 19% | **41%** |
| DeepSeek-V4.1-Flash | 22% | **44%** |

The brief supplies **relevance as well as knowledge**.

<!--
Comparison and measurement details (moved from the former on-slide box):
Compare the same reviewer briefed with the conventions the maintainers invoked on the PR, as general sentences without locations, against unbriefed · Held fixed reviewer, tools, the 14 held-out PRs · Measured share of the 39 in-census asks (of 46) reached per session, blind matchers [Date: 4 Oct]

Additional reference detail:
Full previous table: Opus 5.5, 2 repetitions, 46–49% to 74%; GPT 5.5, 1 repetition, 19% to 41%; DeepSeek-V4.1-Flash, 3 repetitions, 22% to 44%; DeepSeek with examples and precedence, 3 repetitions, 22% to 64%; Qwen3.5-397B, 3 repetitions, 3% to 9%. October mixed reporting views; the present table uses the in-census measure throughout, so its unbriefed column differs slightly.

Evidence E1, synthesis section B and ceiling probe results. In-census ask reach
within each original comparison, 39 asks across 14 ask-bearing PRs. Percentages
rounded; matcher and seal details remain in the linked record. Rows are not a
pooled or common-seal model ranking. The DeepSeek variants share their unbriefed
comparison. Exact supply conveys relevance as well as content; no locations does
not make it answer-free. The Qwen row is ~.034→.085, +.051, not a strong local-model
unlock. For GPT's separate disposition positive under exact supply, see backup.
October's Opus row (0.47 → 0.74) took its unbriefed figure from the all-asks view
and its briefed figure from the in-census view (ceiling README, Result 3).
-->

---

# B · Why we withdrew the “≤ 5%” claim

**October's claim:** maintainers raise conventions at ≤ 5% of the places where they apply.

Checking examples against the proposed rules exposed problems:

| Proposed rule | What we found |
|---|---|
| Namespace placement for predicate lemmas | Most flagged examples were not actually violations |
| Dot-notation calls (`x.f`) | Genuine violations also merged without comment |
| Primed lemma names (`foo'`) | The revised rule failed on known fixes |

**The rate mixed faulty rules with genuine unasked departures.**

<!--
Comparison and measurement details (moved from the former on-slide box):
Check flagged places and known fixes for three conventions by hand, instead of inferring applicability from survival at merge · Measured small selected strata; not population rates [Date: 16 Oct]

Additional reference detail:
Quantitative checks retained from the previous slide: predicate namespaces, 85–97% of selected unasked survivors were not departures under the reconstructed rule; dot-notation calls, 12–13 of 16 checked survivors were genuine departures that merged unasked; primed names, both readers found only 4/6 known fixes and the revised rule failed calibration. These are small selected strata, not population rates.

Evidence E3, final corrections. Small selected strata, not population rates.
Scope, rule precedence, incomplete ask counting and attention all affected the old
denominator. Survival cannot show that a maintainer knowingly accepted a departure.
The dot-notation result prevents the opposite overclaim that all unasked cases
were simply bad rules. The six form-rule practice study is in backup (E4).
-->

---

# C · Can we get the benefit without the review?

Choose conventions or generate alternatives from the PR and library; compare with review without these additions.

| Method | Result |
|---|---|
| Select conventions from the diff | Small gain: **46% → 49%**, versus 74% with human-selected conventions |
| Point to a possible application and ask for a check | No increase in recovery |
| Add examples and explain which rules take priority | Initial gains did not reliably transfer to new PRs |
| Give the reviewer a generated alternative | Did not consistently recover requests missed by ordinary review |

<!--
Comparison and measurement details (moved from the former on-slide box):
Compare each delivery against the same reviewer without it; row 4 against three historical controls · Target the ceiling's gain, which chose the conventions from the maintainers' asks · Measured per row; different sets, never pooled [Date: 5–12 Oct] [Date: 19–25 Oct]

Additional reference detail:
The generated-alternative row concerns one reconstruction route and its registered recovery criterion, not all pairwise preference experiments. Some proposals transferred. Six notes acquired from earlier PRs form the next experiment, introduced on slide 25. Every result in this table is measured against its own ordinary-review comparison; the rows are not pooled.

Say aloud: before these, Mathlib's written guides in the prompt gave no gain (GPT,
115 obligations, an older judge). ProofJudge judges supplied pairs; row 4 had to
generate its own alternative (detail in backup).
Evidence E1 (synthesis sections A–D), E14, E8. Row 1: ceiling README stage F, the
same in-census measure as the ceiling slide: unbriefed 0.46/0.44, selected 0.49/0.46,
exact 0.74/0.72 on both matchers; the 33 asks are the in-census asks on the ten PRs
that received a selection. Row 2: stage G, XR − X = 0.000 on both matchers. Row 3:
conventions-assessment-2026-10-12: DeepSeek +0.20 on validation small12 (the
synthesis quotes +0.18 on ten development PRs), 0.00 post-cutoff, −0.01 dev; Opus
+0.20 on the ten selected PRs, dev +0.02 to +0.09 with intervals spanning 0 and more
findings. Row 4: reconstruction consumer study, 56 new DeepSeek reviews (8 controls,
24 context, 24 context plus sketch), 25 agreed asks on six of the eight PRs; the
criterion was an ask missed by all three historical controls and reached in at least
two of three strategy sessions on both matchers. Some sketch proposals did transfer;
not a proof of zero usefulness. The next experiment is E8, on the following slides. The guidelines comparison
(57 PRs, 115 obligations, older topical judge) is not on the same instrument and is
kept to the source line. Deterministic head detectors covered ~2.9% of asks;
exhaustive application and forced filing added burden; omitted here, in the
detailed reference. Neither proves all unmatched findings wrong.
-->

---

<!-- _class: dense -->

# C · The best knowledge we could write: notes from earlier PRs

The one-line conventions above were sometimes wrong. If the quality of the knowledge was the gap, a proper account should close it.

**Six notes**, one per convention (naming scope, `grind` registration, generality, three more), written from earlier PRs where maintainers had decided the question: when it applies, the competing forms, reasons to decline, what to check.

| Inputs to Opus 5.5 | Contents |
|---|---|
| Ordinary review | PR and tools |
| Short notes | Same + one paragraph per convention |
| Detailed notes | Same + conditions, exceptions and sources |

All six notes go to every review; none says it applies to this PR. **6 PRs × 3 conditions × 3 runs = 54 reviews.** On three of the PRs we knew the maintainer's request, and which note held it.

<!--
Comparison and measurement details:
Compare the same reviewer with no notes, short notes and detailed notes · Held fixed Opus 5.5, tools, 6 development PRs, three reviews per condition · Measured whether the three requests the whole reviews had missed now appear; then all 30 historical asks, blind matchers [Date: 24–25 Oct]

The target PRs were excluded from the sources. Why this experiment, in one line for the room: it is the strongest version of "supply the
knowledge" we could build without using the maintainers' asks. Its decision table was fixed
before the run (synthesis 2026-10-23, section 4; plan 2026-10-24, section 1): if the notes
state accurate distinctions and the whole review still makes the same choices, park this
representation and do not keep elaborating notes.

Evidence E8–E9. Short and detailed notes were acquired from the SAME eligible earlier
sources; the short form is not the historical census sentence. Entries: namespace, name
order, grind registration, to_additive, generality, simp/iff orientation. Developmental
cases; source selection steered by known targets and disclosed. Reserved checks and
repairs are specification checks, not a short-versus-detailed effectiveness result.
Each of the three PRs also had a contrary target where the tempting change should be
declined. No fresh autonomous population claim follows. Date gates and target
exclusions remain in the protocol.
-->

---

<!-- _class: dense -->

# C · The notes arrived; the three requests did not

| Maintainer request | The note the reviewer held | Ordinary | Short | Detailed |
|---|---|---:|---:|---:|
| **#33294** name the lemma by its conclusion | naming a lemma by its conclusion or by its hypothesis | 0/3 | 0/3 | 0/3 |
| **#33098** prove the accessor lemmas by `grind` | when to register facts for `grind` | 0/3 | 0/3 | 0/3 |
| **#33421** replace `2` by a parameter | when to ask for a more general statement | 0/3 | 0/3 | 0/3 |
| All 30 recorded requests, mean recovered | | 35.6% | 34.4% | 41.1% |

The reviewer read the right declaration, and the notes, every time. On #33294 it took “several forms are defensible” as a reason to keep the name. On #33098 it wrote that the notes do not apply and never tried `grind`. On #33421 it checked the generality of the types, not of the constant.

**Better knowledge, delivered this way, did not change what was proposed. The human-chosen brief had carried something more: this concern, here.**

<!--
Comparison and measurement details:
Same comparison as the previous slide · Measured reviews, of three per condition, that make the maintainer's request; then the mean share of the 30 historical asks reached, blind matchers [Date: 24–25 Oct]

Evidence E8; two matcher replications agree on all 270 reached/not-reached cells.
Each primary row is a separate concern on its PR; the grind pair is one concern.
All-ask denominator: 30 asks per repetition; finalized findings 165/158/168. The
primary progression rule fails. The 5.5-point detailed/ordinary difference is not a
demonstrated population effect. Primary concerns were absent at submission as well
as finalization. Transcript reading, results reading of 2026-10-25: on 33294 a
short-notes review wrote that the p_of_q form is acceptable under the note and a
detailed-notes review that the note leaves the case open; on 33098 no tool request
tried grind in any of the nine, and a detailed-notes review wrote that the notes do
not apply here; on 33421 the generality note's first test is replacing a concrete
type with a type variable, and no review considered the constant. This experiment
did not establish that every note arrived at the right application; it is not proof
that the exact brief changed only judgment. The 491-finding usefulness panel is
unlabelled. An exploratory dslope addition outside the historical reference is in
backup.
-->

---

# D · Knowing the convention, declining the request

On **#42814**, the maintainer requested one shared `variable {D}` declaration.

Opus 5.5 received that convention at that declaration, checked it, and wrote:

> “Mathlib does not require these, so I would not request them.”

**Knowing the convention, at the right place, did not settle whether to request the change.**

Did it build the alternative and reject it, or never build it? A whole review cannot show which. So strip the review down to one declaration and one concern, where both steps are visible.

<!--
Comparison and measurement details:
Case from the pinpointed delivery in C: Opus 5.5, a whole review, the convention and a check delivered at the declaration · Observed the reviewer's submitted notes at that place [Date: Oct]

Retains the October example. Evidence E1, stage G (ceiling README, Result 5): of the
10 asks only the exact brief reached, the pinpointed delivery reached none, and 8
had a candidate at the place; the session verified the candidate and overrode it.
Do not retain the original universal "application solved" conclusion or turn
assertion into a validated delivery policy. Assertive instructions were tested with
target-derived entries; the separate GPT positive is in backup. Actual validity and
request value require evidence beyond historical agreement.
-->

---

# D · One declaration, one concern, the same reviewer

Opus 5.5 gets one declaration, one concern, the PR's purpose and diff for that declaration, the reviewed tree, lookups and a compile check. It is never told that a maintainer asked. It answers **revise** or **keep**, with the request it would make.

| PR | Declaration | Concern put to it |
|---|---|---|
| #33294 | the lemma named `…_of_isNormal` | naming a lemma that derives one property from another |
| #33421 | the lemma about `2 * fract x = 1` | the generality its argument supports |
| #33098 | the accessor lemmas | registering lemmas for `grind` |

With and without the detailed note, three runs each, sibling declarations as controls: **72 sessions**. Expected: with the concern pointed out, the maintainer's change gets built and requested.

<!--
Comparison and measurement details:
Compare the same reviewer with and without the detailed note from C, given one declaration and one concern · Held fixed Opus 5.5, the three PRs from C, three sessions per cell, sibling declarations as controls · Measured by reading each answer: did it build the maintainer's alternative; did it request it (blind matchers) [Date: 26 Oct]

Evidence E10–E11. Protocol: focused-application-2026-10-26/PROTOCOL.md, step 1,
registered before each case ran. 72 sessions = 24 per case (two conditions, four
declarations, three replicates at 33294 and 33421; two targets and siblings at
33098), not 72 independent PRs. Opus 5.5 xhigh on the contained route, the reviewed
tree, declaration search, naming lookup and the compile check; no Zulip or precedent
retrieval. The packets differ only by the presence of the note; no packet holds the
merged name, "maintainer" or "suggestion". Conditional diagnosis, not ordinary
autonomous review: declaration isolation, the supplied concern and the instructions
all differ from whole review and are not separately isolated.
-->

---

<!-- _class: tbl -->

# D · The change gets built, then declined

| Change sought | Built it: no note · note | Requested it: no note · note | Whole reviews |
|---|---|---|---|
| Name by conclusion, #33294 | 0/3 · **2/3** | 0 · 0 | 0/9 |
| Replace `2` by a parameter, #33421 | **3/3 · 3/3**, all compiled | **1**, plus 1 partial · 0 | 0/9 |
| Prove by `grind`, #33098 | 0/6 · 0/6 | 0 · 0 | 0/9 |

- **What gets built follows the question.** Asked about generality, every session built the general theorem no whole review had considered. Asked about *registering* for `grind`, none thought of *proving by* `grind`.
- **Once built, the decision is where it is lost.** Of the eight sessions holding the maintainer's change, one requested it and one partly, both without the note.

**Pointing at the concern fixes construction, not the decision. The note, written to prevent over-application, supplied the reasons to decline.**

<!--
Comparison and measurement details:
Same comparison as the previous slide · Measured sessions of three per cell; "built" means the maintainer's alternative appears in the answer, for generality compiled; "requested" means the request matches the maintainer's, blind matchers [Date: 26 Oct]

Evidence E10–E11, RESULTS.md "Step 1 across the three cases". Both matcher
replicates agree three ways on all 48 namespace, 72 generality and 216 automation
cells. At 33294 the no-note sessions asked for the hypothesis namespace instead
(2 of 3; with the note 1 of 3), which both matchers call partial. The six
generalizations differ (natural-number parameters, ring-valued, the maintainer's
1 < c form); all six have a saved successful verified_edit with zero errors,
keeping the special case as a corollary. One note session compiles the conclusion
form at 33294 and declines it as the odd sibling with marginal gain, so the lambda
is not a technical barrier. Automation is a narrow negative: the packets ask about
tagging, the historical asks use grind [definition] in the proofs; zero under the
tagging question does not test proof simplification. Siblings: no wrong generality
or grind requests in 30; at 33294, 5 of 9 without the note and 3 of 9 with it
moved siblings the merge kept, all to Order.IsNormal.*, historical non-asks rather
than established wrong requests. No case met the registered rule for the next
step. 72 sessions, 21.7M processed tokens.
-->

---

# D · Generality: the reasons given for declining

**#33421.** The maintainer: “Better I think as” the version with `1 < c` in place of `2`. The author generalised it; it cost nothing.

All six sessions built and compiled a general version, keeping the original as a corollary.

- **Without the note:** two requested a general version, one in the maintainer's form. One kept the lemma: the general version “needs two side hypotheses and has no other user”.
- **With the note**, which says to ask when the restriction is an artifact of the proof: all three kept it. One compiled the maintainer's form, then wrote:

> “The restriction does not come from how the proof was written. The constant 2 is what the lemma is about.”

**The reviewer can build the change. What differs is the judgment that it is worth asking for, and its reasons are ones a maintainer could give too.**

<!--
Comparison and measurement details:
Case #33421 from the previous slide, six sessions · Observed the general version each session compiled, and its stated reason to request or to keep [Date: 26 Oct]

Evidence E10–E11; answers in eval/generality/answers.json. No-note: one reached
(k * fract x = m), one partial (natural m < n), one kept ("needs two side hypotheses
and has no other user"). With the note: "the constants 2 and 1 are what the lemma is
about, not a side effect of the proof"; the quoted session compiles the 1 < c form
and keeps the lemma; the third, "the constant 2 comes from round's definition".
Three samples per condition do not show a stable causal harm from the note; the
27 October review calls the note's use as an exclusive permission condition a
hypothesis. The historical maintainer is not an independent usefulness adjudicator;
"Better I think as" is a suggestion, not a required revision. The next question
(next-design slide) is decision quality with checked candidates fixed, not forcing
this historical answer.
-->

---

# Where we stand, 4 November

| | Question | What the experiments support |
|---|---|---|
| **A** | Would **more focused attention** resolve the missed requests? | **Not enough in our tests.** Misses persist after inspection or specific instructions. |
| **B** | Does supplying the **right convention** help? | **Yes, when chosen using the human review.** This supplies both the convention and its relevance. |
| **C** | Can we get that benefit **without knowing the maintainer's requests**? | The methods tested so far have **not reliably reproduced that gain**. |
| **D** | If it can **construct the change**, will it request it? | **Not necessarily.** Reviewers can construct and check changes, then decline to request them. |

<!--
Synthesis of the baseline, specialization and convention questions, not a universal
impossibility result. Exact supply has several conditional positives, including GPT
disposition (backup). Acquired-bank primary failure is bounded to six development
PRs and the tested notes. Focus is conditional. The 491-item bank and 66-item pilot
usefulness panels remain without completed labels in the inspected records. The
earlier hypothesis that taste is a small residual is withdrawn; see E5. Current
sources checked for the 4 November update.
-->

---

# What this says about the next design

Hold checked alternatives fixed. Test the reviewer's **reasons for requesting or declining a change**.

For discussion:

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

# Backup · Can generating an alternative improve review?

**ProofJudge** compares supplied pairs of versions. We tried generating an alternative first:

**PR purpose → independent alternative and library context → reviewer**

On 8 PRs, we tracked 25 maintainer requests using a DeepSeek reviewer and Opus-generated alternatives.

Neither library context alone nor context plus an alternative consistently recovered requests that ordinary review missed.

Here, “consistently” means at least **two of three runs**, with both independent assessments agreeing.

<!--
Comparison and measurement details (moved from the former on-slide box):
Compare a reviewer given a generated alternative and library context against the same reviewer without · Held fixed DeepSeek reviewer, Opus-produced sketches, 8 development PRs, 25 agreed asks · Measured registered gain: an ask missed by all three historical controls and reached in two of three sessions, both matchers [Date: 19–20 Oct]

Additional reference detail:
56 new consumer reviews: 8 controls, 24 library-context reviews, 24 context-plus-sketch reviews. Registered gain required a request missed by all three historical controls and reached in at least two of three strategy sessions, as agreed by both matchers. Neither treatment met that requirement.

Evidence E14. ProofJudge 2608.20432 is a supplied-pair preference task, not a system
for choosing useful alternatives or determining acceptance. Our reconstruction
consumer is DeepSeek high, Opus-produced sketches: 8 fresh controls + 24 CTX +
24 CXS = 56 new reviews. Three historical controls are also matched. No registered
gain: an ask missed by all three historical controls and reached by >=2/3 strategy
sessions on both matchers. Small selected panel, fixed artifacts, material matcher
disagreement on one proof family; not a proof of zero usefulness. Some concrete
proposals transfer; value and resource comparison remain unresolved. Initial scorer
packets had missing context and goal extraction imposed invented requirements;
consumer briefs were repaired. This experiment tests one end-to-end reconstruction
route, not direct learning of ≽_t from controlled pair judgments. The broader
comparison hypothesis remains open. See reconstruction-phase-a-review and initial
audit, plus the comparison source table in backup.
-->

---

<!-- _class: tbl -->

# Backup · Instructions can help with selected conventions

**GPT 5.5, given conventions selected from the human review:** require an explicit decision on each candidate change and when it warrants a request.

| 13 other PRs; one run per condition | Before | After |
|---|---:|---:|
| Requests covered by the convention list: share recovered, of 37 | 0.43 | **0.62** |
| Excluding one partly encountered PR, 32 asks | 0.44 | **0.56** |
| Findings per PR | 2.38 | 3.15 |

Seven requests became full matches; two more became partial matches; none was lost.

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

| Request delivered | Ordinary | Short notes | Detailed notes |
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

# Backup · Five design lessons

| Design idea | What our experiments now say |
|---|---|
| **Tell the reviewer the standard** | General guides did not help in the older comparison; conventions selected using the human review do. Getting the same benefit without those requests is unresolved. |
| **Evidence and request value** | Compiling an alternative establishes feasibility. The usefulness panels are still unfinished. |
| **Diversity and recall** | Earlier run unions recover more asks; measure their additional comment burden too. |
| **Decomposition** | The generalist produced most specialist-system matches. The tried arm designs do not justify repeating shared understanding. |
| **When to make a request** | Requiring output can increase volume sharply. Explicit decisions helped GPT given human-selected conventions; forcing DeepSeek to submit findings did not recover previously missed requests. |

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
| E13–E14 | Baseline/focus diagnostics and alternative-generation experiment |

The 54-review and 72-session records are on **experiment branches**. The register records their revisions; they have not all been merged into `develop`.

---

<!-- _class: tbl -->

# Backup · sources

**Deployed reviewers.** BitsAI-CR, ByteDance (2501.15134) · AutoCommenter, Google (2405.13565) · RovoDev, Atlassian (2601.01129), HalluJudge (2601.19072) · uReview, Uber · Bugbot, Cursor · Codex reviewer, OpenAI · Anthropic Code Review and the open plugin · open-code-review, Alibaba, with AACR-Bench · Qodo 2.0 · CodeRabbit (2607.03316) · Greptile v4 · Semgrep Assistant. Tricorder (ICSE'15), Infer (CACM'19).

**Benchmarks and studies.** SWR-Bench (2509.01494) · SWE-PRBench (2603.26130) · c-CRAB (2603.23448) · CodeReviewer (2203.09095) · Code Review Bench, Martian · Adversarial Review (2608.18167) · LLM ensembles for code (2510.21513) · Harness Engineering (2609.00006) · Di Biase et al. (1805.10978) · Kamalı et al. (2605.17548).

**Mathlib.** MathlibPR (2605.07147) · ProofJudge (2608.20432) · Growing Mathlib (2508.21593) · APE-Bench (2504.19110).

**Ours.** `docs/research/code-review-systems-survey-2026-09.md`, `open-code-review-comparison-2026-09.md`, `conventions-assessment-2026-10-12.md`.

---

<!-- _class: dense -->

<!-- _footer: "Mathlib PR review · The solo baseline · Measurements through 14 October" -->

# Backup · Reasoning, harness, or model?

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

# Backup · Can the library settle the choice?

**Diagnostic:** inspect **41 requests** the ordinary reviewer never recovered.

- In **5–7**, library evidence decides the change.
- In **19**, it supplies ingredients, but a choice remains.

**Example:** the `to_fun` attribute generates a theorem family that could replace a hand-written one. Whether to adopt it still depends on interface and import costs.

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

<!-- _class: dense -->

# Backup · The question each published formulation answers

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

# Backup · What the literature suggests testing

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
