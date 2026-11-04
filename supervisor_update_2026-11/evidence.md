# Evidence for the November supervisor update

Checked 3–4 November 2026 for the 4 November meeting. This register supports the empirical
update; it is not a new experiment or a new literature review. E1–E12 identify sources in
the slide speaker notes. Read the final corrections in each results file, since several
files preserve superseded tables and conclusions above their corrected readings.

## E1 — Census, exact convention supply and ask-free transfer

Sources:

- [Experiment synthesis, sections A–D](../docs/research/knowledge-transfer-experiment-synthesis-2026-10-23.md)
- [Ceiling experiment and subsequent stages](../results/pr_review_v5/probes/conventions-ceiling-2026-10-04/README.md)
- [One-reviewer table, including inspections](../results/pr_review_v5/probes/one-reviewer-table-2026-10-10/README.md)
- [12 October assessment](../docs/research/conventions-assessment-2026-10-12.md)
- [Original census presentation](../supervisor_update_2026-10/slides.md)

The original census gives 409/407 entries from 1,833 first-round asks on 1,000 PRs.
Later codebook views have other counts, including 399; the deck uses “about 400.” On
14 outside PRs, 39/46 asks have an entry. This is concern coverage, not validated
applicability at every flagged place.

The ceiling slide uses **in-census reach within each original comparison**, as summarized
in synthesis section B: Opus about .46–.49 to .74, GPT about .19 to .41, DeepSeek about
.22 to .44, or .64 with examples and precedence. These replace the earlier slide's
mixture of reporting views. No cross-model pooled effect is computed. Exact supply
selects entries using target asks and conveys relevance as well as content.

Ask-free selection supplied the entry for 22/33 asks but the bare-entry Opus gain was
about .03; guarded pinpointing gave .000. DeepSeek AP gains did not replicate on
post-cutoff/dev sets; Opus dev intervals included zero. These results constrain the
tested resources and delivery designs. They do not show that knowledge is irrelevant.

## E2 — GPT disposition under exact supply

Source: [generation-suppression, stage W and Result W](../.claude/worktrees/generation-suppression/results/pr_review_v5/probes/generation-suppression-2026-10-06/README.md).
Branch snapshot: `generation-suppression@d7c65fa6`. Also summarized in E1 section B.

13 other PRs, 37 in-census asks, one run per condition: .43 to .62 on both matchers;
without partly encountered PR 32875, .44 to .56 on 32 asks. Findings per PR: 2.38 to
3.15. Seven new reached asks, two new partials, none lost. This is an earlier positive
missing from the October presentation, incorporated by the later synthesis.

The disposition paragraph and request filing threshold changed together, and the baseline
ran the day before. Briefs still use the historical asks. This supports a conditional,
model-specific instruction effect; it does not establish ask-free transfer or full
finding usefulness. DeepSeek forced filing is a separate negative comparison.

## E3 — Departure validity and the withdrawn single rate

Sources:

- [Enforcement at departures, including final corrections](../results/pr_review_v5/probes/enforcement-at-departures-2026-10-16/RESULTS.md)
- [Stage-H places, later checks and adversarial corrections](../results/pr_review_v5/probes/stage-h-departures-2026-10-16/RESULTS.md)

Use the final **85–97%**, not the initial 97%, for namespace non-departures in the
relevant selected stratum. Dot calls: 12–13/16 checked open survivors were departures.
Re-derived primed-name text still yielded 4/6 known fixes for both readers, below the
5/6 calibration rule. No stable prime error rate follows.

The single “≤5% of applicable places” statement mixed situations with departures,
incorrect rule precedence, incomplete ask counting and attention. Later stage-H checks
showed genuine departures too, many without nearby comments. Neither “our rules were
wrong everywhere” nor “maintainers knowingly ignore valid rules 95% of the time” follows.
Merged survival is an outcome, not an observed decision to accept a departure.

## E4 — Rules of form, author practice and attention

Source: [attention/practice results, especially review-4 corrections](../results/pr_review_v5/probes/attention-practice-2026-10-17/RESULTS.md).

973 PRs, six script-checkable form rules. Theorem docstrings and term-proof placement
were robustly broader than practice; line joins and tactic layout were mixed under
corrected denominators. Per departure, all six were asked at under 2%. Near comments,
57% of touched declarations changed whether or not they held a departure. Action on
the specific rule is a narrower outcome than a surrounding rewrite.

The six rules account for only 1.7% of census asks with principles. These results
cannot be generalized to all substantive design or naming conventions. Comment
proximity is a proxy for attention. The original control and several headline readings
were corrected after adversarial review; the deck uses those corrections.

## E5 — Stated grounds

Source: [stated-grounds results and final corrections](../results/pr_review_v5/probes/stated-grounds-2026-10-16/RESULTS.md).

Of 246 asks with an agreed ground in the selected sample: fact 32%, principle 27%,
preference 16%, scope practice 11%, authority 8%, currency 3%, other 3%. The favorable
registered verdict depended on treating facts as supporting the reasoning-over-taste
picture; corrected interpretation: **mixed**. Marker selection missed grounds, and a
later sample estimated some ground in about 37% of all asks. Model readers share a
family; high agreement does not supply independent community validation.

This supports investigating reasons. It does not establish that taste is a small
residual, that reasons reconstruct every decision, or that scope has a known causal role.

## E6 — Library evidence and reconstruction

Sources:

- [Experiment synthesis, section F](../docs/research/knowledge-transfer-experiment-synthesis-2026-10-23.md)
- [Library-knowledge diagnostic](../results/pr_review_v5/probes/library-knowledge-2026-10-13/RESULTS.md)
- [Mechanism grounds, including independent assessment and response](../.claude/worktrees/grounds-reading/docs/research/library-mechanism-grounds-2026-10-22.md)
- [Reconstruction result assessment](../docs/research/review-reconstruction-results-review-2026-10-19.md)

Grounds branch snapshot: `grounds-reading@b1b2d859`. Source/correspondence assistance
sometimes improved consideration or historical recovery, differently by model. Later
symlink-search repairs change the interpretation of earlier retrieval runs. The
grounds support conditional duplication and cost-benefit comparisons; they do not
settle both motivating examples or establish a universal library-over-local preference.
The slide intentionally avoids pooling the heterogeneous probes into one effect size.

## E7 — Conditional-preparation pilot

Sources:

- [Pilot results](../.claude/worktrees/knowledge-transfer/results/pr_review_v5/probes/knowledge-transfer-2026-10-23/RESULTS.md)
- [Pilot assessment](../docs/research/review-knowledge-transfer-pilot-assessment-2026-10-23.md)
- [Usefulness panel](../.claude/worktrees/knowledge-transfer/results/pr_review_v5/adjudications/knowledge-transfer-pilot-2026-10-23/README.md)

Snapshot: `knowledge-transfer@1474776d`. Two PRs, three repetitions, two conditions;
12 preparations and 12 final reviews. For each paired repetition across the two PRs,
both methods reached the same 1/4 agreed asks. Ordinary/conditional: 36/30 finalized
findings, 13.4M/15.5M preparation-plus-review tokens. Both matching replicates agree.
No solo/no-preparation arm was run.

All 24 edit checks on PR 37352 returned environmental failure. The launch and preflight
were repaired afterwards, not during these retained sessions. Source-channel coverage
was incomplete. The 66-finding usefulness panel contains a response template and no
completed response file in the inspected checkout; overall usefulness remains pending.

## E8 — Reusable-bank whole-review comparison

Sources:

- [Results assessment](../.claude/worktrees/reusable-review-knowledge/docs/research/reusable-review-knowledge-results-reading-2026-10-25.md)
- [Protocol](../.claude/worktrees/reusable-review-knowledge/results/pr_review_v5/probes/reusable-review-knowledge-2026-10-24/PROTOCOL.md)
- [Canonical matching report](../.claude/worktrees/reusable-review-knowledge/results/pr_review_v5/probes/reusable-review-knowledge-2026-10-24/eval/match_report.json)
- [Finding counts](../.claude/worktrees/reusable-review-knowledge/results/pr_review_v5/probes/reusable-review-knowledge-2026-10-24/eval/export.json)
- [Submission/finalization accounting](../.claude/worktrees/reusable-review-knowledge/results/pr_review_v5/probes/reusable-review-knowledge-2026-10-24/eval/channels.json)
- [Usefulness panel](../.claude/worktrees/reusable-review-knowledge/results/pr_review_v5/adjudications/reusable-review-knowledge-2026-10-24/README.md)

Snapshot: `reusable-review-knowledge@bbba4f24`. Underlying final reviews/matching are
committed there; the later analytical assessment is a local uncommitted file in that
worktree. This deck is a synthesis, not a merge of that branch.

54 retained reviews: six PRs, three arms, three repetitions. Both treatment arms receive
all six notes. Compact/full are acquired from the **same eligible sources**. Primary
concerns: namespace, two parallel grind proof families counted as one, and constant
generality. Each is absent in all nine reviews of its PR, so each arm scores 0/3 for
each concern. The primary advancement rule cannot be met.

All-ask means, from the canonical report: A 35.5556%, B 34.4444%, C 41.1111%, over
30 raw asks per repetition. Final findings sum to 165/158/168. Both replicates agree
on all 270 reached/not-reached cells. All notes were delivered. Primary requests were
absent from both submissions and final findings, so anchoring losses do not explain
the primary failure. There were 26 other anchoring losses, a separate coverage limit.

The panel is developmental and target-steered. Historical references include some
declined or qualified requests. The 491-item usefulness panel has no completed response
file, and `eval/concerns.json` is absent in the inspected checkout. No overall usefulness
or wrong-request rate can be reported.

The `dslope` request on 33000 appears in B1/B2/C2/C3 (0/3, 2/3, 2/3 by arm). The
assessment inspected successful compile records for B1/C2. This is exploratory and
outside the historical reference, rather than a replacement primary outcome.

## E9 — Source-bank acquisition and audit

Sources:

- [Source checks and repair reading](../.claude/worktrees/reusable-review-knowledge/results/pr_review_v5/probes/reusable-review-knowledge-2026-10-24/checks/READING.md)
- [Source selection](../.claude/worktrees/reusable-review-knowledge/results/pr_review_v5/probes/reusable-review-knowledge-2026-10-24/SELECTION.md)
- [Plan](../docs/plans/2026-10-24-reusable-review-knowledge.md)

Snapshot as E8. Six entries: namespace, name order, grind registration, to_additive,
generality, simp/iff orientation. Acquisition used independent earlier source cases,
with reserved checks, bounded repairs and explicit uncertainty. Checkers saw compact
and full versions together and could not compile. These were joint specification
checks; do not turn them into a compact-versus-full pass rate.

Source search was steered by familiar targets and disclosed. The experiment tests a
bounded acquired resource on developmental cases, not target-independent acquisition
or retrieval over the full census. Only E5 has positive/contrary whole-PR targets under
the same entry. Corrections must not manufacture an unsupported priority between forms.

## E10 — Focused application

Sources:

- [Focused results](../.claude/worktrees/focused-application/results/pr_review_v5/probes/focused-application-2026-10-26/RESULTS.md)
- [Protocol and amendments](../.claude/worktrees/focused-application/results/pr_review_v5/probes/focused-application-2026-10-26/PROTOCOL.md)
- [Namespace answers](../.claude/worktrees/focused-application/results/pr_review_v5/probes/focused-application-2026-10-26/eval/answers.json)
- [Generality answers](../.claude/worktrees/focused-application/results/pr_review_v5/probes/focused-application-2026-10-26/eval/generality/answers.json)
- [Generality reading](../.claude/worktrees/focused-application/results/pr_review_v5/probes/focused-application-2026-10-26/eval/generality/reading.json)

Snapshot: `focused-application@f0a322eb`. 72 sessions, 24 per case, including sibling
cases; three target PRs, one Opus model and three samples per cell. It supplies a
declaration/concern and is a conditional diagnostic, not autonomous review.

Namespace: the intended conclusion form appears in 0/3 without the note, 2/3 with it,
then is declined both times. Generality: all six construct parameterized versions
with successful checked edits, but the versions differ. Without the note, one request
is reached and one partial; with it, all three decline. The sibling generality cases
are kept. Automation asks about registration, so its zero is not a clean negative
test of discovering a grind proof simplification. No case meets the registered rule
for the next autonomous step.

The notes supplied some stated rejection criteria, but these small results do not
isolate a general causal mechanism. Historical mismatch is not by itself a wrong
review decision. The known targets are spent as development evidence.

## E11 — Independent reading and the next question

Source: [27 October assessment](../docs/research/review-harness-next-question-2026-10-27.md),
committed at `6391bfc7` on `develop`.

This audit rechecked 72 exported answers and all matching cells, and inspected saved
successful edit records for all six generalizations. It narrows the focused study's
claims: focus changed generation, decisions still differed, and automation asked a
neighboring question. The next study of decline reasons is a recommendation, not a
registered or completed experiment. A fresh decision test needs independent value
judgments and contrasting cases; forcing publication does not establish usefulness.

## E12 — Shared experimental foundation

Sources:

- [Implementation record](../docs/research/task-dataflow-refactor-implementation-2026-10-22.md)
- [Implementation review](../docs/research/task-dataflow-refactor-implementation-review-2026-10-22.md)

Integrated at `a9154196`, reviewed at `e13343c8`. Reconstruction-chain reproduction:
`954c6f9b`. Second-consumer matching reproduction: `68dea3b5`. Sonnet transport smoke:
`fcca6c76`. These establish execution, lineage and reproduction properties, not an
improvement in maintainer-worthy review. Later comparisons used the shared paths.

## E13 — Baseline misses, specialist focus and residual judgments

Sources:

- [Held-out lead/solo comparison](../docs/research/ab-heldout12-obligation-spine.md)
- [Specific questions already in the specialist briefs](../docs/research/the-question-is-already-asked-2026-09.md)
- [Residual-mechanism reading](../results/pr_review_v5/probes/phase1-residual-mechanisms-2026-09-30/mechanisms.md)

The twelve-PR comparison used GPT-5.2 with reasoning off and the registered obligation
judge `v4-semantic-v3-v9-rubric`: lead 7/5/6, solo 4/4/1 of 23 across three repetitions.
Costs were not matched; the experiment did not resolve mean superiority. Solo's
`HLL` on #33117, inconsistent requests on #33421, and never-located doc-comment line
on #33305 illustrate different failures. Location matching is not evidence that the
precise alternative was considered. Later model/tool improvements remain in backup.

The brief audit found 17/23 obligations specifically covered by an instruction,
using the second, more conservative model reader. Seven of those cases depended on
text written after earlier work on the same PRs. The numeric-constant example is
one such tailored instruction: the arm ran but investigated another family. Other
misses involved pruning, contracts and evidence gates. This is a developmental
diagnostic; it does not show that focus never changes decisions or that every miss
is a checked change deliberately withheld.

The residual population was 37 asks reached by nobody plus 30 reached only by
Claude. In 63/67, every missing reviewer had inspected the object. Both readers
labelled 40 asks as concluded fine, 25 as a different/opposite change, four as never
attempted, and 25 as convention/mechanism knowledge. Labels overlap and count an
ask when the mechanism occurs for a relevant reviewer; they are not a partition or
direct observations of hidden reasoning. The source's implications motivate a
knowledge intervention; they do not identify a universal cause of review failure.

## E14 — Generating alternatives and consuming them in review

Sources:

- [Initial reconstruction audit](../docs/research/review-reconstruction-results-review-2026-10-19.md)
- [Consumer study assessment](../docs/research/review-reconstruction-phase-a-review-2026-10-20.md)
- [Primary reconstruction record](../.claude/worktrees/review-reconstruction/results/pr_review_v5/probes/review-reconstruction-2026-10-19/RESULTS.md)
- [Saved prior-work survey](../docs/research/code-review-systems-survey-2026-09.md)

The reconstruction consumer study ran 56 new DeepSeek reviews on eight selected
development PRs: eight fresh controls, 24 with context and 24 with context plus
fixed Opus-produced independent sketches. Twenty-five agreed asks belong to six
PRs; two have no agreed asks. Three historical controls also entered matching.
Neither intervention achieved the registered gain: an ask missed by all three
historical controls and recovered in at least two of three strategy sessions on
both matchers. Some concrete sketch proposals were checked and delivered as requests.

The panel is small and selected; the matchers disagree materially on one proof
family. Initial goal-extraction and scorer-context defects were corrected or
qualified in the linked audits. Transmission, historical agreement, usefulness and
value at the added cost are separate outcomes. The result limits this whole-PR
reconstruction route. It does not establish that comparing fixed alternatives is
unproductive or that the preference relation cannot be learned.

ProofJudge (arXiv 2608.20432) supplies the relevant prior-work comparison: preference
between given before/after versions. The open review task also requires choosing
which alternative to construct and deciding whether its advantage warrants a request.
