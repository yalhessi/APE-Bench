---
marp: true
theme: default
paginate: true
size: 16:9
math: katex
title: "Can we turn convention knowledge into better review?"
footer: "Mathlib review · Team check-in · 4 November 2026"
style: |
  section {
    background: #fcfcfa;
    color: #223047;
    font-size: 30px;
    line-height: 1.35;
    padding: 52px 68px;
  }
  h1 { color: #1d2b53; font-size: 43px; line-height: 1.15; margin-bottom: 30px; }
  h2 { color: #1d2b53; font-size: 29px; margin: 0 0 12px; }
  p { margin: 12px 0; }
  li { margin: 12px 0; }
  strong { color: #1d2b53; }
  header, footer { font-size: 16px; color: #6a7280; }
  header { letter-spacing: 0.05em; }
  section.lead h1 { font-size: 58px; max-width: 1050px; }
  section.lead h2 { font-size: 30px; font-weight: normal; color: #626c7b; }
  .cards { display: flex; gap: 24px; margin: 22px 0; }
  .card { flex: 1; padding: 22px 24px; background: #eef1f7; border-radius: 10px; }
  .card p { margin: 10px 0 0; }
  .card.plain { background: white; border: 2px solid #d7dce6; }
  .card.green { background: #e8f2ef; }
  .metric { font-size: 72px; line-height: 1.1; font-weight: bold; color: #1d2b53; }
  .metric.mid { font-size: 54px; }
  .label { font-size: 25px; color: #536075; }
  .callout { border-left: 6px solid #1d2b53; padding: 12px 22px; background: #eef1f7; margin-top: 24px; }
  .source { color: #626c7b; font-size: 20px; margin-top: 20px; }
  .common { padding: 16px 24px; background: #1d2b53; color: white; border-radius: 8px; text-align: center; }
  .arrow { align-self: center; font-size: 42px; color: #6a7280; }
  .flow { display: flex; align-items: stretch; gap: 15px; margin: 28px 0; }
  .flow .card { font-size: 27px; }
  .flow .card strong { display: block; margin-bottom: 10px; }
  .questions { counter-reset: question; }
  .questions p { margin: 24px 0; padding-left: 62px; position: relative; }
  .questions p::before { counter-increment: question; content: counter(question); position: absolute; left: 0; color: #1d2b53; font-weight: bold; font-size: 38px; top: -3px; }
  .example { font-family: monospace; font-size: 33px; padding: 22px; background: white; border: 2px solid #d7dce6; border-radius: 10px; }
  blockquote { font-size: 29px; color: #5c4b2c; background: #fbf1dc; border-left: 6px solid #c6973d; padding: 12px 22px; margin: 18px 0; }
  blockquote p { margin: 4px 0; }
  section.backup { font-size: 26px; }
  section.backup table { font-size: 23px; }
  section.backup .source { font-size: 19px; }
  a { color: #285c8c; }
---

<!-- _class: lead -->
<!-- _paginate: false -->
<!-- _footer: "" -->

# Can we turn convention knowledge into better review?

## Monthly progress update · 4 November 2026

Yousef Alhessi · University of Edinburgh

<div class="source">This month: checking the rules, testing transfer, and examining missed requests.</div>

<!--
About 30 seconds. This is the monthly empirical update, with the detailed report
preserved separately. We want the team to understand the questions that drove the
experiments and help choose the next one. Do not open with the full task notation.

The studies discussed here were completed through 26 October; the interpretation
includes the 27 October assessment. No new experiment was run for this presentation.
-->

---

<!-- _header: "WHERE WE LEFT OFF" -->

# Last time, supplying the right convention helped

<div class="cards">
<div class="card plain"><div class="metric">46–49%</div><p>Usual review</p></div>
<div class="arrow">→</div>
<div class="card green"><div class="metric">74%</div><p>The right conventions supplied</p></div>
</div>

Share of the relevant historical requests recovered, in the earlier Opus comparison.

<div class="callout">Could we acquire and use that knowledge without consulting the target PR's review?</div>

<!--
About 1 minute. Briefly remind the team of the task: recover worthwhile requests on
a real Mathlib PR that already compiles. Supplying the right conventions was an
earlier conditional positive. The entries were chosen using the historical asks.
The gain therefore combines content with information about which concerns matter.
It does not demonstrate automatic selection or applicability.

These are in-census ask-reach readings in the original Opus comparisons, not an
all-ask score or a new November experiment. Different matchings/repetitions give
the .46–.49 baseline range. Other models and the GPT disposition positive remain
in the reference and backup rather than a model leaderboard here.
Evidence: [E1](evidence.md#e1--census-exact-convention-supply-and-ask-free-transfer).
-->

---

<!-- _header: "THIS MONTH'S QUESTIONS" -->

# We investigated three questions

<div class="questions">
<p>Did our convention rules describe actual Mathlib practice?</p>
<p>Would notes acquired from other PRs improve ordinary review?</p>
<p>When a request was missed, was the alternative never proposed, or was it declined?</p>
</div>

<!--
About 45 seconds. Use this as the route through the talk. The first investigation
checks a premise of the earlier convention results. The second tests a specific
attempt to transfer knowledge. The third diagnoses why the primary requests were
still missing. They have different outcomes and should not be flattened into a
single statement that conventions or prompting work or fail.

Sources: E3–E4, E8–E11 in evidence.md.
-->

---

<!-- _header: "1 · CHECKING THE RULES" -->

# Our flags mixed different situations

We followed flagged places to merge and checked the rule against known fixes.

<div class="cards">
<div class="card"><h2>Namespace placement</h2><p>Many flags came from our detector preferring the wrong namespace.</p></div>
<div class="card"><h2>Dot notation</h2><p>Genuine departures also reached merge without a request.</p></div>
</div>

<div class="callout">The old “5% of applicable places” rate could not tell these apart.</div>

<!--
About 1 minute 45 seconds. Explain the empirical procedure before the conclusion.
We did not just count flags. We followed their outcomes and checked selected cases
against the convention and against departures maintainers actually fixed.

For namespace placement, the final corrected estimate was 85–97% non-departures
in the relevant selected unasked-survivor stratum. The detector often favored a
conclusion namespace where the reconstructed rule preferred the main hypothesis.
For dot calls, 12–13/16 checked survivors were genuine departures. Primed-name
calibration failed twice, so we could not establish a stable boundary there.

The broader practice study covered six form rules on 973 PRs. Some written rules
were broader than anyone's practice; comment proximity and surrounding rewrites
did not establish a decision on the rule itself. Those rules cover a narrow part
of the census. We withdraw a single enforcement-rate interpretation, rather than
replacing it with a new universal rate. Silence does not tell us whether someone
weighed and rejected a change. This is why source-derived scope and reasons seemed
worth testing, not proof that richer notes would improve review.

Evidence: E3–E4 in evidence.md; detailed update slides 22–24.
-->

---

<!-- _header: "2 · TRANSFERRING KNOWLEDGE" -->

# Would notes from other PRs improve review?

Earlier reviews → **six checked notes**, covering when and why to prefer a change.

<div class="common">Same PRs · same reviewer · same tools</div>

<div class="cards">
<div class="card plain"><h2>Ordinary review</h2><p>No extra notes</p></div>
<div class="card"><h2>Compact notes</h2><p>Short account</p></div>
<div class="card"><h2>Full notes</h2><p>Reasons and conditions</p></div>
</div>

<div class="source">6 PRs × 3 conditions × 3 repetitions = 54 final reviews · Opus 5.5</div>

<!--
About 1 minute 30 seconds. Establish the controlled contrast. All six notes go to
every treatment PR; we do not tell the reviewer which entry applies at which place.
Both note versions come from the same eligible earlier sources. The source work
included reserved checks and bounded repairs; unresolved priorities stayed uncertain.

The panel had three primary opportunities and three contrary targets. Sources and
retrieval exclude the target PRs and respect date gates, but source selection was
steered by already familiar targets. This is a development comparison, not a fresh
test of automatic acquisition. Only generality has a positive and contrary target
under the same entry. The source checks do not establish a universal rulebook.

Pause before the next slide: the prediction is that better independent knowledge
will make at least two of the missed primary concerns appear reliably in review.
Evidence: E8–E9 in evidence.md.
-->

---

<!-- _header: "2 · THE RESULT" -->

# The three target requests were still missing

<div class="cards">
<div class="card plain"><h2>Namespace</h2><div class="metric">0/9</div></div>
<div class="card plain"><h2>Proof automation</h2><div class="metric">0/9</div></div>
<div class="card plain"><h2>Generality</h2><div class="metric">0/9</div></div>
</div>

Reviews delivering the target concern. Each count combines three conditions and three repetitions on its PR.

<div class="callout">The notes did not meet our target for trying them on fresh PRs.</div>

<div class="source">Full notes recovered some other historical requests. Overall usefulness remains unjudged.</div>

<!--
About 1 minute 30 seconds. Give the primary observation first. The proof-automation
concern spans two parallel historical asks, neither reached. These are nine reviews
per primary PR, not nine independent PRs. The 54 total also includes contrary cases.
All notes were delivered. These target requests were absent from submissions as
well as final reviews, so finalization loss does not explain this primary result.

The study's advancement rule required gains on at least two primary concerns.
Neither resource can pass it. This closes the present bank under that rule; it
does not establish that knowledge cannot help or that the full arm had no gains.
Mean all-ask recovery was 35.6/34.4/41.1% for ordinary/compact/full. Those secondary
figures and counts are in backup. Both saved matchers agree on the primary misses.
The overall usefulness panel is still unlabeled.

Transition: before trying a larger bank, we inspected what happened at these places.
Evidence: E8 in evidence.md.
-->

---

<!-- _header: "3 · UNDERSTANDING THE MISSES" -->

# Next we narrowed the reviewer's question

<div class="flow">
<div class="card plain"><strong>Whole PR</strong>“Review this change.”</div>
<div class="arrow">→</div>
<div class="card"><strong>One declaration</strong>“Could this theorem be more general?”</div>
</div>

Compare **no note** with **the same relevant note**.

<div class="source">72 focused sessions across three selected cases, including sibling checks.</div>

<div class="callout">Would the missing alternative now be proposed—and would the reviewer ask for it?</div>

<!--
About 1 minute. These are illustrative descriptions of the two tasks, not transcript
quotations. The concern is now supplied; it was not supplied in ordinary review.
The 72 sessions include target and sibling declarations, 24 per case, three samples
per condition/declaration. We are diagnosing a conditional capability, not measuring
an autonomous reviewer gain or attributing effects to focus alone. Instructions,
resource allocation and retrieval scope also differ from whole review.

Start with generality because the mathematical change is easy to explain and every
focused target answer built an alternative. The two other cases follow afterwards.
Evidence: E10–E11 in evidence.md.
-->

---

<!-- _header: "ONE EXAMPLE · GENERALITY · PR #33421" -->

# A working generalization was often declined

<div class="flow">
<div class="example">2 * fract x = 1</div>
<div class="arrow">→</div>
<div class="example">c * fract x = 1<br><span class="label">with 1 &lt; c</span></div>
</div>

All **six** sessions compiled a generalization and kept the special case.

> “Nothing in the PR or the library calls for a constant other than 2.”

<div class="cards">
<div class="card plain"><h2>Without the note</h2><p><strong>2/3</strong> suggested generalizing</p></div>
<div class="card"><h2>With the note</h2><p><strong>0/3</strong> suggested generalizing</p></div>
</div>

<div class="source">One selected PR; one candidate shown. The six generalizations differed.</div>

<!--
About 2 minutes. Explain the example before interpreting the numbers. In PR 33421,
the new lemma characterized the half-integer case used by round. The displayed
expressions are schematic left sides; the full equivalence and context are omitted.
Efract2 compiled a candidate with 1<c; other sessions generalized different constants
or domains. All kept the original special lemma as a corollary. They are six working
generalizations, not six identical reproductions of the maintainer's suggestion.

The maintainer requested generalization. With a supplied generality question every
focused target session built one, where the nine whole reviews had not proposed
this parameterization. Without the note two requested generalization: one matched
the historical request fully, one partially. With the note none requested it.

The quote is Efract2's recorded reason, with initial capitalization changed. It
compiled essentially the historical alternative and declined it. The note favored
generalizing proof artifacts; the answers treated the constant as meaningful to
the task. A no-note answer also cited lack of another user, so this is not an
isolated causal account of what the note did. One selected PR, three samples per
condition. We have a concrete decision to examine, not proof that the maintainer's
choice is universally better or that a successful proof makes every cost zero.

Pause: what evidence would make the proposed generalization worth suggesting here?
Evidence: E10, generality answers Nfract2/Efract2; E11 in evidence.md.
-->

---

<!-- _header: "WHAT THE OTHER CASES ADD" -->

# The other cases stopped at different stages

<div class="cards">
<div class="card"><h2>Namespace</h2><p>The intended name appeared with the note, then was declined.</p></div>
<div class="card"><h2>Automation</h2><p>We asked about tagging lemmas. The missing request was to simplify their proofs.</p></div>
</div>

<div class="callout">The same score can hide different causes.</div>

<!--
About 1 minute. Namespace: 0/3 no-note answers formulate the intended conclusion
form; 2/3 note answers formulate it and decline. One tests it successfully and favors
sibling consistency. So generation changed but the final request did not.

Automation: both conditions answer the registration question we supplied; neither
proposes the missing grind proof. This is a narrow negative about a neighboring
question, not evidence that correctly focused proof investigation cannot help.
No case passed the registered rule for an autonomous step 2. The conditional result
does not rescue the failed whole-review bank. Detailed readings are in backup.
Evidence: E10–E11 in evidence.md.
-->

---

<!-- _header: "WHAT CHANGED IN OUR UNDERSTANDING" -->

# We can now separate two kinds of miss

<div class="flow">
<div class="card"><strong>Propose an alternative</strong>Does the relevant comparison occur to the reviewer?</div>
<div class="arrow">→</div>
<div class="card"><strong>Decide whether to ask</strong>Having checked it, is the change worth suggesting?</div>
</div>

The whole reviews missed comparisons. Some focused sessions made them and still chose differently from the maintainer.

<div class="callout">The next experiment can isolate the decision, with a concrete alternative held fixed.</div>

<!--
About 1 minute. This is the research progress from the negative comparisons. It
replaces a blanket diagnosis of missing convention knowledge with observable stages
we can test separately. Knowledge, scope and technical feasibility still matter.
We have not shown that all misses share these causes or that larger notes never help.

Generation and recommendation remain separate open problems. Supplying a candidate
will not test autonomous discovery; that is an intentional boundary of the proposed
diagnostic. We first need to know whether a reviewer can choose well when it has
the relevant alternative, rather than build another whole-PR process around an
unmeasured choice rule.
Evidence: E8–E11 in evidence.md.
-->

---

<!-- _header: "AN OPEN EVALUATION QUESTION" -->

# Could useful suggestions be missing from our score?

On another PR, reviewers suggested a **`dslope` proof** that avoids new derivative imports.

<div class="cards">
<div class="card plain"><div class="metric mid">0/3</div><p>Ordinary reviews</p></div>
<div class="card"><div class="metric mid">2/3</div><p>Each notes condition</p></div>
</div>

The historical reviewer did not request it. Saved checks support feasibility; usefulness is still unjudged.

<div class="callout">Would we want the reviewer to make this suggestion?</div>

<!--
About 1 minute. This is a concrete candidate for the team to discuss, not an
asserted success. On PR 33000 the requests occurred in B1/B2 and C2/C3; the saved
assessment spot-checked successful edit records in B1/C2. They replace a manual
analytic-order proof using dslope and avoid new derivative imports.

This was exploratory, not one of the primary concerns. It cannot replace the failed
primary outcome. Historical recovery cannot credit this exact request, but an
independent usefulness reading could decide its value against ordinary reviewers'
alternatives. A bounded reading of this case does not complete the still-unlabeled
491-item overall panel. We should avoid treating historical nonmatches as errors,
and avoid treating a compiling suggestion as useful by definition.
Evidence: E8, exploratory dslope requests, in evidence.md.
-->

---

<!-- _header: "PROPOSED NEXT STEP" -->

# Test decisions with a candidate supplied

<div class="flow">
<div class="card plain"><strong>Fixed evidence</strong>Current code + checked alternative</div>
<div class="arrow">→</div>
<div class="card"><strong>Reviewer decision</strong>Keep · optional suggestion · required change</div>
</div>

Use independent cases favoring **change** and **retention**.

Judge correctness, usefulness and unnecessary work alongside historical agreement.

<div class="source">Start with generality. Finding candidates autonomously remains a separate question.</div>

<!--
About 1 minute 30 seconds. This is a proposal for team input, not an agreed or
registered study. First inspect the existing generality answers and checked edits:
which rejection reasons describe checked costs, untested claims, or preferences?
Then assemble independent explicit decisions about feasible alternatives, with
genuine costs on the retention side. Silence is not a retention label.

If that premise holds, freeze a small contrasting panel and compare decisions with
the alternatives and observations held fixed. A note intervention is only worth
testing if its sources establish a different decision boundary, without encoding
the familiar target's answer. Record optional versus required requests, rather
than treating every useful suggestion as a condition of merging.

Advancement would need useful gains on independent cases, no offsetting useful
losses or extra clearly wrong requests, and retention on meaningful contrary cases.
Those thresholds need agreement before a run. A benefit confined to the known
fract target would not justify another whole-PR intervention.
Evidence: E11 in evidence.md, 27 October assessment.
-->

---

<!-- _header: "DISCUSSION" -->

# Where should we invest next?

<div class="card plain"><h2>Which uncertainty first?</h2><p>Test the decision with a candidate supplied, or prioritize finding candidates autonomously?</p></div>

<div class="card plain" style="margin-top: 24px"><h2>What should count as success?</h2><p>How should we judge a worthwhile suggestion that the historical reviewer never made?</p></div>

<!--
About 30 seconds to hand over, then discussion. State the recommendation: a bounded
decision diagnostic first, with the concrete generality and dslope cases as leads
for premise checking, not fresh evaluation cases. Ask the team to challenge that
priority and the evidential standard for a useful suggestion.

The desired output is a choice of next investigation and an approach to independent
judgment, rather than generic reactions to the whole project. The theoretical
framing can later distinguish acceptable implementations, useful optional comments
and required revisions using whatever distinctions this discussion supports.

The full report, all older experiments and formulation remain in slides.md and
evidence.md; this spoken route does not replace them.
-->

---

<!-- _class: backup -->
<!-- _header: "BACKUP · WHOLE-REVIEW COMPARISON" -->

# Broader recovery changed; usefulness is unfinished

| Across 18 reviews per condition | Ordinary | Compact | Full |
|---|---:|---:|---:|
| Each primary concern recovered | 0/3 | 0/3 | 0/3 |
| Historical ask recovery, mean over repetitions | 35.6% | 34.4% | 41.1% |
| Finalized findings | 165 | 158 | 168 |

30 raw historical asks. The full arm's extra recovery came from dot notation and calc indentation outside the primary concerns.

**The 491-item usefulness panel remains unlabeled.** The primary requirement failed; an overall quality comparison is not complete.

<div class="source">[Detailed report](slides.md) · [Evidence E8](evidence.md#e8--reusable-bank-whole-review-comparison)</div>

<!--
Both saved matchers agree on reached/not-reached for all 270 cells. Historical
references include some later declined/qualified suggestions. No population gain
follows from the full arm's descriptive increase on a target-steered small panel.
All 54 retained reviews succeeded and treatment delivery was checked. The 26 other
anchoring losses do not include a primary request. See E8 for costs and deviations.
-->

---

<!-- _class: backup -->
<!-- _header: "BACKUP · A CONDITIONAL POSITIVE" -->

# Filing instructions helped GPT with exact knowledge

Same target-derived conventions; add a disposition instruction and a request threshold.

<div class="cards">
<div class="card plain"><div class="metric mid">43%</div><p>Before</p></div>
<div class="arrow">→</div>
<div class="card green"><div class="metric mid">62%</div><p>After</p></div>
</div>

37 in-census asks on 13 other PRs; one run per condition. Findings per PR: 2.38 → 3.15.

The right conventions were still selected using the target's historical asks. Both instructions changed together; full usefulness was not established.

<div class="source">Earlier experiment, 6 October · [Evidence E2](evidence.md#e2--gpt-disposition-under-exact-supply)</div>

<!--
Keep this positive available so the narrower main narrative is not heard as
“instructions cannot help.” Both matchers agree. Without partly encountered PR
32875, the gain is .44 to .56 on 32 asks. Seven requests became reached and two
partial, none lost. Baseline came from the prior day. Conditional supply and a
model-specific response are different claims from ask-free knowledge transfer.
-->

---

<!-- _class: backup -->
<!-- _header: "BACKUP · PREPARATION PILOT" -->

# More source investigation did not improve recovery

Two PRs; three repetitions; 12 preparations feeding 12 final reviews.

| | Ordinary preparation | Conditional reasons |
|---|---:|---:|
| Requests recovered per paired repetition | 1 of 4 | 1 of 4 |
| Finalized findings, all reviews | 36 | 30 |

Relevant reasons sometimes reached the wrong decision axis: `aesop` rule-set membership instead of safe/unsafe status.

**Limit:** all 24 edit checks on one PR failed environmentally. No solo arm; usefulness labels pending.

<div class="source">23 October · [Evidence E7](evidence.md#e7--conditional-preparation-pilot)</div>

<!--
Paired repetition = one review of each of the two PRs, not a single-PR session
with four reference asks. Every pair reached the same weaker-typeclass ask. No
filing was lost in finalization. Toolchain preflight was repaired afterwards.
This tests a per-PR preparation procedure, not a bank acquired before target review.
-->

---

<!-- _class: backup -->
<!-- _header: "BACKUP · FOCUSED FOLLOW-UP" -->

# The focused results have different limits

| Target | No note | Relevant note |
|---|---|---|
| Namespace | Intended form absent, 0/3 requests | Formulated 2/3; declined both |
| Generality | Generalization built 3/3; two suggested it | Built 3/3; none suggested it |
| Automation | No target grind proof | Same; question concerned registration |

72 sessions include sibling checks. Generality's two suggestions had one full and one partial historical match. The six generalizations differ.

No case passed the registered progression rule. These supplied-concern diagnostics do not establish autonomous review improvement.

<div class="source">[Evidence E10–E11](evidence.md#e10--focused-application) · [Full reference](slides.md) · [Structure options](presentation-options.md)</div>

<!--
Sources and revisions: focused-application@f0a322eb, independently assessed at
develop@6391bfc7. Both matching replicates agree on every three-valued cell:
48 namespace, 72 generality, 216 automation. The raw answer and saved successful
edit records support construction claims; we do not infer an unobserved decision
from silence at sibling cases or turn a compile into a usefulness label.
-->
