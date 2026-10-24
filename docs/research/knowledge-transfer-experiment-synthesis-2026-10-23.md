# Knowledge transfer: the experiments so far and the next useful comparison

**Research synthesis and recommendation, 2026-10-23.** Read against `develop@4b8d5b71`,
`knowledge-transfer@1474776d`, and the experiment records linked below, including branch-only
generation-suppression results. No new generation, judging or reviewer runs were launched.
This is an investment recommendation, not a frozen execution protocol.

**Next plan, 2026-10-24:** [reusable review knowledge](../plans/2026-10-24-reusable-review-knowledge.md)
turns the recommendation into a staged handoff. It uses three repetitions/54 final reviews,
revising the two-repetition proposal below, and specifies source eligibility and evaluation.

**Revision after review, 2026-10-24:** the active plan compares ordinary review with compact and
full banks acquired from the same eligible sources. The original census sentences remain
historical artifacts rather than arm B. Either acquired resource can earn a fresh test; fuller
notes need additional evidence to displace a qualifying compact bank. The synthesis below
preserves the earlier recommendation and experiment history.

## 1. Recommendation

Continue investigating knowledge transfer, but move the next intervention from **how a reviewer
is instructed to investigate a PR** to **what reusable knowledge we can acquire from independent
PRs and teach it before review**. Keep the reviewer, tools and runtime foundation stable.

The next candidate is a small, source-derived knowledge resource whose entries distinguish
the situations favoring a change from situations favoring the existing form. Test it in ordinary
whole-PR review against both a solo baseline and the existing terse convention resource.
Do this first on an explicitly developmental panel of already-used PRs; reserve fresh cases for
a frozen candidate that shows a useful effect. New concerns enter as data, through one shared
acquisition and review procedure, rather than through a detector or prompt branch per convention.

This revisits part of the dossier proposal. It is not new merely because the resource has a
different name. The reason to reopen a bounded version is the October 16 evidence that some
conventions and their applicability were incorrectly specified, together with the fact that
source-derived, independently checked dossiers were never built. It is **not** justified by a
general belief that longer explanations or more examples must improve understanding.

I would not make another hand-selected source-supply probe on the now-familiar aesop example the
main next experiment. That revises section 6.3 of my [pilot assessment](review-knowledge-transfer-pilot-assessment-2026-10-23.md).
We have already run enough conditional evidence-supply diagnostics to know that evidence can
change consideration and sometimes requests. The more valuable unresolved question is whether
we can acquire knowledge that makes correct distinctions and transfers across PRs without
supplying the target's applicability judgment.

## 2. What was actually tested

The numbers in this section are local to their original comparisons. July covered-obligation
counts, historical ask-match seals, one-turn ladder answers, and the new task-native matcher
are different measurements. They must not be pooled into a single improvement estimate.

### A. Written guidelines and precedent hints: delivery alone was insufficient

The [guidelines comparison](baseline-merge-readiness-review.md), on 57 PRs and 115 anchored
obligations, covered 10 with guidelines versus 12 without on gpt-5.4; the gpt-5.2 comparison was
32 versus 36. These used the older topical judge, not today's ask matcher. They do not establish
harm, but they remove the case for simply appending the community's general guidelines.

July's **precedent priming, Mode A** delivered code-similar historical comments. Uptake was
visible: 47% of primed findings echoed a precedent. The apparent first-20 gain did not replicate:
13 versus 11 covered on 41 shared PRs. See the [dead-end record](../dead-ends.md) and
[original design](precedent-retrieval-design.md).

Other July results are weaker evidence than they initially appeared. Mode B's site-discrimination
test used leaked delta sites. The instantiate/apply-all/facet battery used post-review
`gold.delta_total`; 106 of 202 hunks were eventual author fixes. Those are oracle diagnostics,
not evidence that a deployable retrieval system found the right review opportunities.

**Lesson:** getting a relevant-looking precedent into a prompt, and even seeing it echoed, does
not establish useful transfer. The historic retrieval measurements also do not validate a
modern ask-blind source-selection method.

### B. Applicable convention supply: a substantial conditional positive

In the [conventions ceiling](../../results/pr_review_v5/probes/conventions-ceiling-2026-10-04/README.md),
the supplied entries were selected using the target PR's asks and presented as applicable.
Within the original ask-match comparisons:

| Reviewer | Unbriefed in-census ask reach | Exact convention brief | Further intervention |
|---|---:|---:|---|
| Claude | about 0.46–0.49 | 0.74 | — |
| GPT-5.5 | about 0.19 | 0.41 | — |
| DeepSeek-V4.1-Flash | about 0.22 | 0.44 | about 0.64 with examples and precedence, three repetitions |

These are real positives for the tested conditional interventions. They combine knowledge with
information about which convention matters on this PR. They do not show that a reviewer can
recover that applicability judgment autonomously.

An important additional positive is **GPT stage W**, in the
[generation-suppression record](../../.claude/worktrees/generation-suppression/results/pr_review_v5/probes/generation-suppression-2026-10-06/README.md).
Holding exact convention sections fixed, a disposition paragraph plus `filing_bar: request`
took reach from 0.43 to 0.62 on 37 in-census asks across 13 other PRs, on both matchers. Excluding
32875, partly encountered during development, the difference was 0.44 to 0.56 on 32 asks.
Findings per PR increased from 2.38 to 3.15. Seven asks became reached, two more became partial,
and none was lost. This was one run per condition, with the baseline from the previous day.

Stage W should not be conflated with detector pass-through. It supports a model-specific
instruction effect under exact knowledge supply. It does not isolate the paragraph from the
filing-bar change, establish usefulness of all findings, or demonstrate ask-free transfer.

**Lesson:** knowledge and the decision contract can matter. Neither “the models already know
everything” nor “prompting cannot help” is a reasonable reading of the record.

### C. Ask-free convention selection: the positive did not reliably generalize

Stage F's selector chose 25 entries from the diff without the asks. It included the underlying
entry for 22 of 33 asks, but bare-sentence delivery improved Claude by only about 0.03. Stage G
added guarded rules, pinpointing and checks: the difference was 0.000.

AP supplied the selected entries with examples and precedence. DeepSeek initially improved by
0.18 on ten development PRs. The broader [reviewer table and assessment](conventions-assessment-2026-10-12.md)
found the gain concentrated in the eight already-used validation PRs: 0.00 post-cutoff and
−0.01 on dev. Opus's selected-set gain was about 0.20, but dev gains were 0.02–0.09 with
intervals crossing zero and substantially more findings.

This is not just a selector-recall problem. Even when an entry was selected, AP often reached
about half its asks, while solo's reach on those same asks varied strongly by set. The selected
development sample had unusually much room for AP to help.

**Lesson:** a selected-set gain is a candidate effect, not a reliable population improvement.
Supplying the topic is insufficient; scope, instantiation, attention and the decision to ask
remain entangled. A new content intervention needs an existing-knowledge comparator.

### D. Richer examples, demand prediction and exhaustive application: substantially explored

The [oracle ladder](../../results/pr_review_v5/probes/conventions-ladder-2026-10-08/README.md)
tested five arms, three samples each, on 39 in-census asks: 585 one-turn answers, DeepSeek,
fixed place, full PR, no tools. Passing means at least two of three samples reached the ask.
The two blind matchers found:

| Supplied information / instruction | Passing asks, matcher 1 / 2 |
|---|---:|
| Told a maintainer asked here; no convention | 5 / 6 |
| Convention sentence; judge conformity | 25 / 29 |
| Sentence plus examples; judge conformity | 21 / 25 |
| Sentence; told it applies | 29 / 29 |
| Sentence plus examples; told it applies | 27 / 29 |

At a known place, the sentence already carried most of the recoverable change. More examples
hurt the judged form. That is evidence against another generic “sentence versus examples”
experiment and against assuming all whole-review misses indicate conceptual misunderstanding.

Stage H also tested asked/unasked examples, base rates, and retrieval of nearby examples for
149 pinpointed candidates with 12 historical candidate positives, representing eight asks.
Its decision designs did not meet their bars; historical-ask ranking AUCs were 0.56–0.64.
The examples of “not asked” were **silences**, not explicit reasons to retain a form. This is
not a clean test of learning exceptions from reasoned contrary decisions.

The [places test](../../results/pr_review_v5/probes/conventions-places-2026-10-09/README.md)
did find moderate discrimination from verdicts, despite failing its registered confidence-based
criterion. Post hoc verdict/signed-confidence AUCs were roughly 0.68–0.78. But exhaustive
application projected a median of about 68 filings per PR, with about 7% aligned to historical
asked pairs. That is an alignment/burden measurement, not proof that the remainder was wrong.

Forced filing similarly recovered some already-recoverable asks while increasing output; it
reached none of 32 previously never-reached asks. A small detector catalogue covered only about
3% of census asks. See [dead ends](../dead-ends.md) and [questions](../questions.md).

**Lesson:** more calls, more examples, confidence scores and a lower filing threshold are not
an unexplored general solution. There is some useful per-place signal, but no validated
conversion of that signal into an economical, worthwhile whole review.

### E. The convention itself was sometimes wrong: a material correction

The October 12 assessment strongly rejected richer knowledge as the next lever. The later
[departure readings](../../results/pr_review_v5/probes/enforcement-at-departures-2026-10-16/RESULTS.md)
complicate that conclusion:

- The namespace detector preferred the conclusion's namespace, while the reconstructed convention
  often preferred the main hypothesis's namespace. The final corrected estimate was **85–97%**
  non-departures among the relevant unasked survivors, not a settled 97%.
- For primed names, changing the rule's wording changed many verdicts. Even a rederived rule
  failed its held-out calibration: both readers found only four of six fixed departures, below
  the five-of-six bar. Nine source asks did not establish a stable boundary.
- Dot-notation departures were often genuine and survived unasked. Construct error does not
  explain everything, and silence still does not establish acceptability.

**Lesson:** “a model ignores an applicable convention” was sometimes a mistaken description of
our own input. We must distinguish an incorrect rule, a rule applied outside its scope, a genuine
departure nobody noticed, and an unwelcome request. This is evidence for checking knowledge
validity; it is not evidence that a richer resource will improve review.

### F. Library knowledge, source packets and reconstruction: consideration improved more reliably than requests

The [library premise check](../../results/pr_review_v5/probes/library-knowledge-2026-10-13/RESULTS.md)
read 41 difficult asks. The library decided seven, or five after recheck; for 19 it supplied
ingredients while a choice remained. It was a diagnostic reading, not an intervention trial.

Ask-blind decision-context packets in the reconstruction probe did not improve the sketches'
recovery of 25 asks. Targeted source/correspondence packets did sometimes help: at PR 33117,
Sonnet's baseline/source/correspondence counts were 0/5, 1/5, 4/5. Opus did not reproduce that
gain. After fixing symlink search, Opus's baseline was 0/3, source plus correspondence 0/3,
and additional adoption evidence 1/3. Assisted sessions considered `to_fun`; unassisted ones did
not. Some declines followed faulty construction attempts, while a real client-call/interface
tradeoff remained. Wrapper removal at 33066 did not show a corresponding gain.

See the [reconstruction assessment](review-reconstruction-cheap-baselines-2026-10-20.md) and
[grounds reading](../../.claude/worktrees/grounds-reading/docs/research/library-mechanism-grounds-2026-10-22.md).
The grounds support conditional costs and benefits, not a universal preference for reuse or
generation. Historical search defects also limit cross-run comparisons.

**Lesson:** finding or compiling an alternative does not settle whether to request it. Another
single known-site evidence-supply demonstration would add less than a genuine cross-PR transfer
test. The grounds resource is motivated, not validated.

### G. The latest pilot: a procedural intervention, not a learned knowledge resource

The [October 23 pilot](../../.claude/worktrees/knowledge-transfer/results/pr_review_v5/probes/knowledge-transfer-2026-10-23/RESULTS.md)
compared ordinary preparation with conditional-reason investigation, each feeding the same
ordinary final reviewer. Two PRs, three repetitions, 12 preparations and 12 final reviews,
Opus 5.5/xhigh on contained Claude Code. There was **no solo/no-preparation arm**.

Ask-match/2-task, rubric `d1889a8bf62d`, question-form/harness-blind, seal `5a13fdcc5378`, scored
finalized findings against four agreed raw asks. Both matcher replicates agreed: every review
reached the same one of four asks. Conditional reviews delivered 30 findings versus 36 ordinary,
using about 15.5M versus 13.4M processed tokens including preparation. Usefulness labels remain
pending. On 37352, all 24 edit checks failed environmentally; the launch/preflight is now fixed.

The treatment found more explicit sources, but often considered the same choices. At the aesop
attribute it applied relevant evidence to the rule-set axis rather than the safe/unsafe axis.
At the theorem name, it weighed a reasonable competing analogue. A sourced instance-name
correspondence was also reversed in one preparation and survived into final review.

The [source check](../../.claude/worktrees/knowledge-transfer/results/pr_review_v5/probes/knowledge-transfer-2026-10-23/source_check/RESULTS.md)
also limits the claim: precedent search ranked by code and indexed only review line comments
through December 2025. It omitted review bodies/issue comments and returned none of the eligible
review reasons in four worked choices. Library practice and Zulip were reachable; comprehensive
transfer of maintainers' review-comment reasons was not tested.

**Lesson:** the shared task/handoff worked, and the more explicit procedure did not improve
historical recovery here. This does not test a reusable knowledge base acquired and checked
across independent PRs. More citations did not establish correct preservation or use of a relation.

## 3. The resulting hypothesis

There is evidence that the right knowledge can change review, but no established general method
for acquiring, selecting and correctly applying it without target-answer assistance. The history
does not identify a single bottleneck for every concern.

The bounded hypothesis worth testing is:

> An independently acquired account of when and why a project prefers an alternative can improve
> ordinary review beyond the current terse census, including declining the same tempting change
> when its premise does not hold.

This differs from “add examples” only if the source work actually changes or establishes the
decision boundary: scope, precedence, semantic correspondence, consequences, or uncertainty.
An unchanged sentence with decorative examples is already a low-priority intervention.
The October 16 errors make this a plausible bet; the ladder and AP failures make it a risky one.

An entry can be a short Markdown file: the choice it concerns; conditions favoring each form;
independent code/discussion excerpts with dates; explicit contrary decisions where available;
what to inspect or try; and what remains inferred or disputed. Unasked merged code is not an
automatic negative. An uncertain convention should remain uncertain. No new ontology, runtime
ledger, per-convention checker or calibrated-authority mechanism is necessary.

For example, the namespace entry must distinguish the main-hypothesis and conclusion roles.
For a dual-instance naming comparison, it must preserve which action is on the dual and which
is by dual scalars. These are concrete information distinctions, not requests to “reason harder.”
Neither example should be counted as new validation after developing the entry from its outcome.

## 4. The next experiment I recommend

### Acquire a bounded resource, then make one three-arm comparison

Use **three concern families**, spanning different decisions rather than three versions of
redundancy: a scope/precedence convention, an automation/mechanism choice, and statement/API
design. Choose specific entries from the documented failures with adequate independent sources;
include a tail entry. This is a proposed scope, not a claim that eligible sources have already
been assembled for all three.

Build a small fixed bank of roughly six entries from independent earlier source PRs. Use the
same source-study procedure for every entry, with existing Tasks and declared document outputs.
Inspect it against reserved source cases to catch wrong scope or reversed relationships. Keep
this bounded: no corpus-wide census rebuild or standalone exam campaign. If the sources cannot
establish a claimed distinction, record that instead of manufacturing a rule.

Select six **already-used development PRs**, two per family: one representing an existing miss
and one with a competing form/reason that tests overapplication. The retention judgment needs
explicit evidence or adjudication, not historical silence. Target PRs and their later outcomes
must be excluded from source induction, examples and retrieved references. Respect each target's
date cutoff. These development choices can be informed by known failures; they are not a random
sample or fresh validation.

Give **the same bank of candidate entries to every PR**, without selecting a convention or place
from that PR's asks. This deliberately bounds the selection problem for the initial content
comparison and includes irrelevant entries. It does not validate retrieval over 400 conventions.

| Arm | Final reviewer receives |
|---|---|
| A: solo | The ordinary review inputs and tools, with no added convention bank |
| B: existing knowledge | The same review, plus the original terse entries for the fixed bank |
| C: acquired knowledge | The same review, plus the independently derived conditional entries for that bank |

Use Opus 5.5 on the current contained route first: weaker models' failures would be less useful
for the current harness goal. Two independent repetitions per arm and PR make **36 final-review
sessions**, plus the shared offline acquisition. Freeze entries before generating any target
review; use the same reviewer instructions, tools, limits and resource-use guidance in B and C.
Do not assert that an entry applies, require a finding per entry, or add a per-PR preparer.
The intervention bundles knowledge content and its representation; it does not isolate prose
length or prove one abstract format superior.

Before any user-run generation, write the usual protocol with an **Already answered?** section,
exact PRs/source exclusions, frozen inputs, legal resume identities, budget and manual commands.
The suggested counts here are an explicit small design, not a power calculation. No fresh
population effect can be estimated reliably from this panel.

### What to score and what the result changes

Score finalized whole reviews using the same canonical matcher plan across arms. Separately
adjudicate a blinded union of distinct delivered concerns for correctness and request value,
preserving materially different proposed fixes. Retain per-arm occurrences and losses; collapsing
similar names must not hide a reversed rename. The older pilot's already-frozen full panel should
still be completed under its own protocol.

The diagnostic success pattern is a stable improvement in C over both A and B on multiple PRs
and at least two families, accompanied by correct handling of contrary cases and no offsetting
loss of useful concerns or rise in wrong requests. Freeze the investment rule before running;
the counts above do not provide a universal significance threshold. Source references and checks
explain an effect but never substitute for the delivered-review outcomes.

| Observation | Next investment |
|---|---|
| C improves on A and B, across concerns, and handles contrary cases | Freeze the acquisition procedure; test fresh PRs with target-independent selection. A genuinely new entry should require data work, not new runtime code. |
| B and C improve similarly | Prefer the cheaper resource. The gain may be attention from the small bank; rich acquisition has not earned its cost. |
| C improves only when a researcher supplies the target's applicability or place | Keep the conditional capability result; do not call it autonomous transfer. Selection/attention remains the question. |
| C states accurate distinctions but whole review still makes the same choices | Park this representation as a review intervention. Try a materially different use of knowledge or model-learning approach only with a new premise; do not keep elaborating notes. |
| Entries cannot predict independent source cases or retain genuine uncertainty | The proposed knowledge has not been acquired reliably. More runtime retrieval will not repair that representation. |
| More findings explain the apparent gain, or contrary cases become wrong requests | No basis for adoption; inspect the specific overapplication rather than add universal filing authority. |

## 5. Work to keep separate

Finish the pending usefulness panel and carry the repaired toolchain preflight into subsequent
runs. Neither requires a full rerun of the latest pilot or prevents a separate content experiment.

Do not prioritize an unchanged conditional-preparation expansion, generic sentence-versus-example
ladder, another `to_fun`/wrapper campaign, forced filing, exhaustive per-place application, or a
large convention platform. Each has a relevant negative or scope limitation above.

Text search over review reasons is a real missing capability, not disproven by this pilot. It may
be a small extension of the existing retrieval surface. I would first demonstrate a consumer for
independently assembled reasons with the bounded bank, then measure retrieval of those reasons
from visible-code queries. Building a larger store before that repeats the risk of delivering
context without improving decisions. If the immediate work is specifically a retrieval study,
it should measure reason/correspondence recovery, not claim review-quality improvement.

Fine-tuning or persistent model learning is also distinct from the in-context experiments so
far. This record does not close it, but it needs a defensible training target and clean transfer
test; historical ask/no-ask labels alone do not provide correctness or usefulness labels.

The cumulative goal is a stable ordinary reviewer with an evolving, tested knowledge resource.
The experiments justify investigating that goal, while requiring the next resource to earn its
place through cross-PR behavior rather than through the apparent thoroughness of its notes.
