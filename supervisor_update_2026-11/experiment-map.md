# Experiment map: Mathlib review research since September

Working reconstruction, 3 November 2026. This is the evidence base for rebuilding the
supervisor update. It precedes decisions about slides, duration and compression. The
October presentation and both November meeting drafts remain unchanged.

The organizing question is the original one: **what does assistance need to add to a
capable reviewer to produce useful requests about a Mathlib contribution?** The record
contains several investigations of that question, rather than one sequence of convention
experiments. Some characterize the task; some diagnose a failure; some test an intervention.
Success at one of these does not establish success at the others.

## Scope and how to read this map

The main period is September–October 2026, checked against the working record on 3 November.
Older findings appear only where they motivated a September investigation. The main sources
are the [experiment index](../docs/questions.md), [stopped and superseded directions](../docs/dead-ends.md),
[open hypotheses](../docs/todo/README.md), research assessments, probe records and branch-only
results. The project status file supplies background; its older headline interpretations are
not treated as the latest conclusions.

I checked the worktree/branch record as well as `develop`. In particular, the reconstruction,
grounds, preparation, independent-bank, focused-application, generation-suppression, naming
and useful-additions records contain relevant material outside the main branch. Links into
those worktrees are local evidence pointers; moving a worktree will require updating them.

The entries below are **experimental families**, not counts of independent experiments.
Several contain multiple conditions or follow-ups on the same spent development cases.
Motivations and registered decisions are taken from the linked records. The grouping into
questions is a retrospective synthesis for this presentation, not a claim that the programme
was designed in this order. These readings do not replace a fresh annotation of raw outputs.

Measurement conventions matter throughout:

- Historical ask recovery, obligation-judge recall, one-turn answers and reader labels are
  different instruments. Numbers below stay within their source comparisons.
- A historical nonmatch is not automatically an incorrect or useless request. A PR with no
  recorded ask is not certified defect-free.
- Reading the right declaration, proposing an alternative, checking it, requesting it and
  retaining it in the final output are distinct observations.
- Two agreeing model readers do not supply independent maintainer validation. A small
  selected-case diagnostic does not estimate autonomous performance on fresh PRs.

## The questions represented in the record

| Broad question | More specific questions actually tested | Entries |
|---|---|---|
| Can a structured process improve review? | Are specialists starved, silent, constrained by their contract, or asking the wrong questions? Does explicit coverage or a second pass help? | E01–E04, E10 |
| What work does review require? | Does our small development set represent the task? What is reviewed, against what reference, with what context and warrant? | E05–E07, E12 |
| What limits the solo baseline? | Is the gap reasoning, tools, harness, memory, missing knowledge, missing alternatives or request judgment? | E08–E09, E11 |
| Can project knowledge improve review? | Does exact supply help? Can we select and apply it without the target answer? Are our conventions valid? | E13–E18, E22–E24 |
| Can finding and comparing alternatives help? | Does the library settle the decision? Do independent sketches, supplied sources or stated grounds improve final review? | E19–E21 |
| What would establish useful progress? | Do additional suggestions have value beyond historical recovery? Were they actually delivered, and at what burden? | E25; a limit on every intervention |

## Process, coverage and the baseline

<a id="e01"></a>

### E01 · Reviewed-state verification and tool hygiene — September–October

**Motivation and test.** Before explaining review failures, check whether the tools expose the
PR state correctly. Cross-file verification used base build products beneath changed source;
later audits also found broken path handling, lookup and deletion behavior.

**Answer.** The stale-state audit found 41 of 321 arm sessions received `Unknown constant`
errors and 16 phantom build-failure findings. Building reviewed workspaces removed the
reproduced stale-state failure. October's broader hygiene repair removed most refused calls;
Opus's 9, 9, 7 of 23 obligations remained within the earlier baseline's variation.

**Consequence.** These repairs improve the validity of the experiment and remove false claims.
They do not establish a review capability gain. Historical retrieval runs also need the later
symlink-search qualification in E21.

Sources: [reviewed workspaces](../docs/research/reviewed-workspaces.md),
[model/tool audit](../results/pr_review_v5/probes/claude-models-2026-10-01/README.md).

<a id="e02"></a>

### E02 · Lead plus specialists versus a whole-PR solo reviewer — 14 September

**Motivation and test.** The initial thesis was that understanding and decomposing review work
could make a harness more useful than one agent with tools. On twelve PRs, compare ten
specialists plus a delegating lead with solo GPT-5.2, reasoning off, three repetitions each.

**Answer.** The lead reached 7, 5, 6 of 23 obligations; solo reached 4, 4, 1. Their unions were
7 and 8, with 13 reached jointly. The lead cost 7.7 times as much. Its generalist produced
64 of 71 matched finding occurrences. The sample did not resolve the mean difference.

**Consequence.** Complementarity and repeatability were real observations; superiority of
decomposition was not established. This motivated diagnosing what the specialists lost,
rather than treating a richer architecture as progress in itself.

Source: [per-obligation comparison](../docs/research/ab-heldout12-obligation-spine.md).

<a id="e03"></a>

### E03 · Scheduling, abstention, replay and the submission contract — 14–23 September

**Motivation and test.** Perhaps the lead pruned the useful specialists, or their contract
made them too reluctant to speak. Remove pruning; forbid empty output; replay silences;
then require a verdict per target while permitting requests without a compiled repair.

**Answer.** Unpruned fanout reached 2 of 10 obligations, against solo's 4 on the same four PRs.
Forcing raised 2 to 5, while findings on the no-ask control rose from 1 to 36. Replays largely
repeated decisions; many apparent silences were correctly off-concern. The later unified
contract reached 3 of 10, below its 5-of-10 gate, despite every target receiving an answer.
Auditing the original prompts also found that some briefs had been fitted to these PRs.

**Consequence.** Running more arms and removing silence did not supply the missing change
economically. The residual included smaller or different questions, limited naming evidence
and compound requests split across outputs. The original claim that forcing proved the bar
was only a volume filter was retracted: the quality comparison lacked power.

Sources: [stopped directions and corrections](../docs/dead-ends.md),
[questions already present in the briefs](../docs/research/the-question-is-already-asked-2026-09.md),
[silence audit](../docs/research/specialist-silences-2026-09.md),
[unified-contract result](../docs/research/unified-contract-fanout4-2026-09.md).

<a id="e04"></a>

### E04 · Joint work units and coordinated edits — September

**Motivation and test.** Some maintainer requests concern related declarations together.
Could fragmented units or an unusable patch channel explain those misses? Audit grouping,
edit grants and serialized candidates, repair the channel, then inspect ordinary emissions.

**Answer.** The audit found genuine representation and verification defects. Joint patch
emission was absent from 3,411 candidates across sixty recorded runs; providing a usable
channel did not establish that the tested GPT/Qwen reviewers would choose to use it.

**Consequence.** A capability the interface forbids must be repaired before testing it.
Making it expressible is still different from generating it. This was not a strong-model
test of the value of coordinated reasoning.

Sources: [coordinated-emission audit](../docs/research/coordinated-emission-2026-09.md),
[later synthesis and its limits](../docs/research/decompose-and-shrink-review-2026-10.md).

<a id="e05"></a>

### E05 · Does the development set represent review work? — September

**Motivation and test.** The arms reflected a small set of familiar PRs. Audit review work on
sixty PRs, then preregister a replication on a nominal thousand-PR draw: 973 available PRs,
1,833 first-round asks, two blind readers.

**Answer.** Four of seven claims from the small audit failed replication. The larger sample
put naming at 9.7%, statement/API design at 14.3%, and unowned asks at 21.4%. PR-level asks
were 16.1% among AI PR asks versus 5.1% among the others in this sample.

**Consequence.** The task is broader than the development set, and broad families are not an
adequate justification for the existing arm roster. This produced a substantive task map
and motivated testing PR-level work separately. It did not show that a new partition would
improve review.

Sources: [initial audit](../docs/research/pipeline-overfit-2026-09.md),
[large replication](../docs/research/pipeline-overfit-2026-09-replication.md).

<a id="e06"></a>

### E06 · Facets, reference, warrant and PR-level review — 25–26 September

**Motivation and test.** Derive review work from what a declaration does, who uses it, and
what evidence settles a concern. Test the reliability of that description, a facet-oriented
brief, a complementary hard-question pass, and a PR-level-only brief.

**Answer.** The facet labels were reproducible between model readers; reference plus object
predicted warrant in about 85% of the relabelled cases. The facet brief gained design and
PR-level asks but lost seven local asks. A complement's apparent gain concentrated on one
documentation PR. The separate PR-level study reached 13–14 of 21 asks against the
generalist's 6–9, but missed its stronger gain/volume gate.

**Consequence.** The representation taught us something about review work, with concrete
examples such as `ConvexSpace`'s definition design and AI-edited prose. It did not validate
a replacement brief or a general decomposition. Local focus and broad context can compete.

Sources: [work structure](../docs/research/review-work-structure-2026-09.md),
[facet and complement results](../docs/research/facet-brief-probe-2026-09.md),
[PR-level probe](../results/pr_review_v5/probes/pr-level-2026-09-25/README.md).

<a id="e07"></a>

### E07 · Naming from statements rather than token prevalence — September

**Motivation and test.** Prefix counts cannot describe namespace moves, interior changes,
relations between names, or `round_eq'` becoming `round_eq_div`. Build statement-aware
evidence and test on held-out historical renames with controls, then two reviewer misses.

**Answer.** Unthresholded proposals contained the eventual word in 27 of 65 renames. At the
baseline false-alarm rate the primary comparison was 0 of 65 versus 2: no demonstrated gain.
The reviewer bench did not move either miss. Elaborated evidence also overturned an earlier
surface-count interpretation favoring `toLinearMap_`.

**Consequence.** Potentially useful evidence for *what* a new name could be, without a validated
detector of *whether* it should change. Corpus majority is not a substitute for understanding
the statement or the community's choice. Code was parked; the research question remained open.

Source: [branch result and motivating cases](../.claude/worktrees/naming-from-statement/docs/todo/naming-from-statement.md).

<a id="e08"></a>

### E08 · Reasoning, model, harness, prompt and cutoff controls — late September–October

**Motivation and test.** Before designing around weak GPT reviews, check reasoning effort,
carried reasoning, prompt exchange, three harnesses, Claude routes, tool hygiene and PRs
created after the reported cutoff. Establish usable local-model baselines too.

**Answer.** High effort improved GPT-5.2; carrying reasoning greatly improved completion and
efficiency without a clear further recovery gain. Harness swaps did not close its gap.
Claude retained substantial post-cutoff performance. Opus's route mattered, and its exact
GPT prompt still performed strongly. Qwen stayed near the floor; DeepSeek supplied a more
capable local iteration tier when its thinking was retained.

The consolidated October table reports Opus subagent reach 0.47/0.62, DeepSeek 0.28/0.40 and
GPT-5.5 0.24/0.28 on its two panels, within that table's matcher comparisons. These are
reviewer configurations, not a ranking isolated from route and resource differences.

**Consequence.** A general harness contribution needs comparison with the strong solo route.
Reasoning or provider repairs cannot be counted as the proposed review mechanism's benefit.
Later Luna/Sonnet baseline studies in E21 were operational substitutes, not replacements for
that standard.

Sources: [consolidated reviewer table](../results/pr_review_v5/probes/one-reviewer-table-2026-10-10/README.md),
[baseline assessment](../docs/research/beating-solo-2026-10.md),
[post-cutoff control](../results/pr_review_v5/probes/postcutoff-2026-09-29/README.md).

<a id="e09"></a>

### E09 · Where do residual misses actually occur? — 30 September; 12 October

**Motivation and test.** Read the recorded work at missed asks before changing coverage or
filing instructions. The September study used two readers on 141 reviewer/ask pairs over
67 residual asks; October reread 93 asks across DeepSeek solo and assisted sessions.

**Answer.** In September, at 63 of 67 asks every missing reviewer had read, searched or compiled
the object. Convention/mechanism gaps and untried checks were common overlapping labels;
verified-and-withheld occurred at only two asks. The 67 include **37 reached by neither
reviewer and 30 reached only by Claude**. They are not 67 Claude successes over GPT.
October found named-and-dropped concerns, acceptance of the current code, missing facts and
conventions applied along the wrong axis.

**Consequence.** These studies redirected attention from coverage alone to what the reviewer
constructs and concludes at an attended object. They do not prove attention is solved or
that every miss is withholding. October's filing-contract result in E18 tested, and limited,
one interpretation of the named-and-dropped labels.

Sources: [September mechanism table](../results/pr_review_v5/probes/phase1-residual-mechanisms-2026-09-30/mechanisms.md),
[October reading and corrected interpretation](../docs/research/filing-decision-design-2026-10-12.md).

<a id="e10"></a>

### E10 · Structured ledgers, critics and unions — early October

**Motivation and test.** Would explicit per-declaration concerns prevent premature approval?
Would a critic recover missed changes, or several independent passes provide a useful pool?

**Answer.** Opus's structured ledger reached 10 and 10 of 23 against hygiene runs of 9, 9, 7;
the critic added one recovery at roughly another pass's token cost. Two first stages reached
12 jointly. A four-pass union reached 12, with seven findings per no-ask control PR; pass
agreement did not discriminate historical hits in that experiment (AUC 0.48).

**Consequence.** More coverage and repetition can add asks and burden. These designs did not
clear their advancement rules or establish a calibrated signal for choosing comments. A
generic critic, exhaustive grid or union is already an investigated intervention.

Sources: [structured/critic records](../results/pr_review_v5/probes/review-designs-2026-10-02/README.md),
[union study](../results/pr_review_v5/probes/ensemble-union-2026-10-02/README.md).

<a id="e11"></a>

### E11 · Mechanical alternatives, construction, folding and linters — September–October

**Motivation and test.** Some missed questions can be answered by trying a specific edit.
Check targeted closer/replay procedures, definition folding, construction-oriented briefing
and a static pass over changed files.

**Answer.** Targeted procedures produced eight of fifteen historical asks outright and a ninth
with seeded closer lemmas; three maintainer questions instead received a technical "no".
The edits were selected using the asks: exhaustive yield was not measured. Definition folding
recovered analogues for six of 66 selected comparison asks with substantial synonym noise.
Construction briefing did not improve Claude's selected-case recovery; GPT compiled more
without recovering more. The static pass found one exact and one partial ask on its dev panel.

**Consequence.** Concrete checks can resolve a narrow question and expose a mistaken historical
suggestion. That does not measure how often autonomous review finds the right question, or
justify requesting every successful alternative. These are useful operations, with unproven
whole-review contribution.

Sources: [closer battery](../results/pr_review_v5/probes/closer-battery-2026-09-26/README.md),
[fold search](../results/pr_review_v5/probes/fold-search-2026-09-26/README.md),
[construction probe](../results/pr_review_v5/probes/construction-demo-2026-09-29/README.md),
[static pass](../results/pr_review_v5/probes/static-pass-2026-10-01/README.md).

## What project knowledge can and cannot supply

<a id="e12"></a>

### E12 · Written practices, changing conventions and the census — September–October

**Motivation and test.** What standard is a reviewer trying to infer? Read written guidance,
library mechanisms and dated practice; extract principles from the large review corpus,
then check whether they describe asks on PRs outside that corpus.

**Answer.** The catalogue contained 112 entries, including 23 binding syntax rules largely
handled by CI. A linter's introduction did not date adoption of the convention: `grind`
practice continued to change while the relevant linter was unchanged. The review census
produced hundreds of entries and a long tail. On fourteen outside PRs, 39 of 46 asks had an
entry. Counts such as 409/407, 438 and 399 belong to different codebook views; they are not
interchangeable estimates from one frozen instrument.

**Consequence.** A small rule list is an inadequate description of the task. The census is a
knowledge resource and descriptive result, not proof that every sentence has a correct
operational scope or that its presence warrants a request at every matching place.

Sources: [catalogue](../docs/research/mathlib-convention-catalogue.md),
[census and exact-supply record](../results/pr_review_v5/probes/conventions-ceiling-2026-10-04/README.md),
[snapshot qualifications](evidence.md#e1--census-exact-convention-supply-and-ask-free-transfer).

<a id="e13"></a>

### E13 · Does supplying the relevant convention help? — 4–9 October

**Motivation and test.** Separate the possibility of knowledge helping from the difficulty
of finding which knowledge matters. Supply entries selected using the target's historical
asks, stated as applicable, and compare within each model's original matching.

**Answer.** In-census recovery improved: Opus roughly 46–49% to 74%, GPT-5.5 roughly 19% to
41%, DeepSeek roughly 22% to 44%, or 64% with examples and precedence. A separate GPT stage W,
holding exact sections fixed but changing both disposition and filing threshold, improved
43% to 62% on 37 in-census asks, one run per condition.

**Consequence.** A substantial conditional positive: knowledge and instructions can matter.
The intervention also conveys relevance. It does not demonstrate autonomous knowledge
acquisition, applicability judgment or usefulness of every extra request. Stage W prevents
the opposite blanket conclusion that changing the filing contract never helps.

Sources: [synthesis of original comparisons](../docs/research/knowledge-transfer-experiment-synthesis-2026-10-23.md),
[stage W](../.claude/worktrees/generation-suppression/results/pr_review_v5/probes/generation-suppression-2026-10-06/README.md).

<a id="e14"></a>

### E14 · Can the same gain be obtained without the target asks? — 4–11 October

**Motivation and test.** Pick entries from the diff rather than the answer. Try bare
sentences, guarded rules at candidate places, examples and precedence, then repeat outside
the cases that motivated the intervention.

**Answer.** The selector included the relevant entry for 22 of 33 asks; bare supply improved
Opus by about three points and guarded pinpointing by zero. DeepSeek's AP gain on familiar
cases did not transfer to the post-cutoff or dev panels. Opus's selected-case gain also did
not establish a dev improvement; intervals crossed zero and output increased.

**Consequence.** This breaks the inference from the ceiling positive to an effective review
system. Some failures occur even when an entry is delivered. Merely improving retrieval
recall cannot be assumed sufficient. The exact and ask-free settings must remain separate.

Sources: [conventions assessment](../docs/research/conventions-assessment-2026-10-12.md),
[consolidated table and inspections](../results/pr_review_v5/probes/one-reviewer-table-2026-10-10/README.md).

<a id="e15"></a>

### E15 · Known-place ladder, examples, exhaustive application and dossiers — 8–9 October

**Motivation and test.** Was a sentence too weak, was the place missing, or did the reviewer
not believe the rule applied? Test five one-turn conditions on 39 known asks, per-place
verdicts on asked/unasked pairs, and cheaper shortlist methods.

**Answer.** The known-place ladder recovered 5–6 of 39 without a sentence, 25–29 with one;
adding examples did not improve that form. Per-place verdicts had some retrospective
discrimination, but exhaustive application projected a median of about 68 filings per PR.
Historical "unasked" examples were silences, not explicit retention decisions.

**Consequence.** A generic sentence-versus-examples experiment and an unbounded apply-every-rule
engine were already weak investments. The dossier/exam programme was narrowed by an
adversarial assessment; it was not executed as a validated learning system. This later
mattered when valid scope, rather than prose length, became the premise for E23.

Sources: [ladder](../results/pr_review_v5/probes/conventions-ladder-2026-10-08/README.md),
[places study](../results/pr_review_v5/probes/conventions-places-2026-10-09/README.md),
[dossier assessment](../docs/research/conventions-dossiers-review-2026-10.md).

<a id="e16"></a>

### E16 · Deterministic convention detectors — 6–7 October

**Motivation and test.** Supply concrete departures rather than hoping the reviewer notices
the rule. Develop dot-notation, prime-name, generated-twin and attribute checks; measure
coverage and downstream use.

**Answer.** Some narrow checks were reliable; others, particularly generated twins, failed.
The four convention families represented about 2.9% of census asks. On a selected GPT test,
facts stating thirteen asks yielded one; a disposition paragraph yielded five, together with
thirteen of fourteen unasked detector facts.

**Consequence.** The limitation was both coverage of the long tail and whether detected facts
became worthwhile requests. This line was parked as a general recall strategy. It does not
imply that a cheap detector is useless for every separate concrete objective.

Sources: [detector record](../results/pr_review_v5/probes/convention-detectors-2026-10-06/README.md),
[stopping rationale](../docs/dead-ends.md).

<a id="e17"></a>

### E17 · Were our flags actually departures? — 16 October

**Motivation and test.** The early account said maintainers requested a change at at most five
percent of applicable places. Follow flags to merge, re-read them against reconstructed
rules, calibrate on known fixes and compare literal checks with model readings.

**Answer.** Corrected namespace readings found 85–97% non-departures in the selected unasked
survivor stratum. Dot notation differed: 12–13 of sixteen checked survivors were genuine
departures. Prime-name rules failed held-out calibration even after rederivation. These
figures have different denominators and do not estimate one global rule-error rate.

**Consequence.** Withdraw the single low-enforcement interpretation. The old denominator mixed
candidate situations, mis-specified rules and real departures. Merge survival does not tell
us whether a maintainer noticed and endorsed the choice. This correction reopened the
question of acquiring a valid conditional rule; it did not validate richer notes.

Sources: [departure-enforcement corrections](../results/pr_review_v5/probes/enforcement-at-departures-2026-10-16/RESULTS.md),
[stage-H corrections](../results/pr_review_v5/probes/stage-h-departures-2026-10-16/RESULTS.md).

<a id="e18"></a>

### E18 · Practice, stated reasons and a forced filing contract — 12–17 October

**Motivation and tests.** Three distinct checks bear on the claim that a reviewer knows the
right rule but suppresses it: compare six form rules with author practice and attention
proxies; code grounds stated in review; force evidence-backed per-concern verdicts, filing
everything other than supported conformity.

**Answers.** Some rule texts were broader than maintainers' own practice; nearby changes did
not establish action on the particular rule. The stated-grounds study's corrected verdict
was mixed, not confirmation that taste is a tiny residual. The filing contract reached
fourteen of 37 previously named-and-dropped asks, below its sixteen-ask gate, and none of
32 never-reached asks, while delivering 4.9 findings per no-ask control PR.

**Consequence.** Reasons are worth investigating, but neither observable practice nor explicit
ground categories reconstruct a complete standard. Forcing a named concern into output
often produces a partial or different request. The next missing capability cannot simply
be called "permission to file".

Sources: [practice/attention](../results/pr_review_v5/probes/attention-practice-2026-10-17/RESULTS.md),
[stated grounds, including final corrections](../results/pr_review_v5/probes/stated-grounds-2026-10-16/RESULTS.md),
[filing-contract result](../results/pr_review_v5/probes/filing-contract-2026-10-12/README.md).

## Alternatives, comparison and transfer

<a id="e19"></a>

### E19 · Does the library itself decide the missing request? — 13 October

**Motivation and test.** If missing knowledge is the problem, perhaps the base library can
supply the answer. Read 41 asks no free-reviewer session reached and seek a deciding artifact.

**Answer.** Seven were judged decided, five after recheck; for nineteen, the library supplied
ingredients but left a choice among alternatives. Other asks required judgment or history.
The premise check failed its thirteen-ask threshold.

**Consequence.** Library search remains necessary in many cases, but finding existing code
does not settle adoption, naming or request value. This motivates comparison with reasons,
rather than another retrieval platform justified by search coverage alone.

Source: [library-knowledge premise check](../results/pr_review_v5/probes/library-knowledge-2026-10-13/RESULTS.md).

<a id="e20"></a>

### E20 · Independent reconstruction and its review consumer — 19–20 October

**Motivation and test.** Perhaps the submitted design anchors the reviewer. Extract a goal,
hide or show the design, add decision context, then ask whether a normal reviewer benefits
from the resulting packet or an independent sketch.

**Answer.** The initial visible/hidden/context sketch comparison gave no clear historical
recovery gain. Goal extraction sometimes turned author choices into invented requirements;
these were repaired before the consumer study. Phase A ran 56 new DeepSeek reviews on eight
selected PRs, comparing context and context-plus-sketch with ordinary review. Neither
strategy produced the registered multi-PR gain on 25 agreed asks. Some sketch proposals
were checked and transmitted, including the normalizer generalization on #43167.

**Consequence.** The producer-to-reviewer channel works for some concrete proposals. Avoiding
a redundant object in a new implementation is not the same as diagnosing it in the author's
implementation. Historical recovery, novel useful additions and resource benefit need
separate evidence. The expensive whole-contribution route was deprioritized; general
comparison was not disproved. See E25 for the subsequent additions triage.

Sources: [first reconstruction audit](../docs/research/review-reconstruction-results-review-2026-10-19.md),
[consumer assessment](../docs/research/review-reconstruction-phase-a-review-2026-10-20.md),
[primary record](../.claude/worktrees/review-reconstruction/results/pr_review_v5/probes/review-reconstruction-2026-10-19/RESULTS.md).

<a id="e21"></a>

### E21 · Missing source, correspondence, adoption and stated grounds — 20–23 October

**Motivation and tests.** Reconstruction left several decisions unresolved. Establish Luna
and Sonnet baselines; inspect whether the relevant source arrived; supply sources and explicit
correspondence; repair symlink search; inspect the costs and reasons behind adoption.

**Answer.** Luna was near the floor on this panel; Sonnet provided a usable diagnostic route.
At #33117, sources plus correspondence improved Sonnet's `to_fun` requests, without a matching
Opus improvement. Under fixed search, Opus reached 0/3 without supply, 0/3 with correspondence,
1/3 with adoption evidence. All six assisted sessions connected the mechanism to the twins;
several then made construction errors or weighed local practice/import cost against it.
The generated API also differed in client use, so equivalence was not merely a compile check.

A separate comment reading found recurring anti-duplication reasons in nine PRs by eight
maintainers. The later assessment restricted the inference: this was not a universal reason
to replace handwritten families with generators, nor an intervention success.

**Consequence.** Source discovery, semantic correspondence, correct construction and deciding
to adopt can fail separately. This is a stronger explanation than "retrieve the library"
or "always prefer the library". Known-target source supply remains a conditional diagnostic.

Sources: [baseline and source-supply primary record](../.claude/worktrees/review-reconstruction/results/pr_review_v5/probes/review-reconstruction-2026-10-19/RESULTS.md),
[grounds reading and appended corrections](../.claude/worktrees/grounds-reading/docs/research/library-mechanism-grounds-2026-10-22.md).

<a id="e22"></a>

### E22 · Conditional preparation before ordinary review — 23 October

**Motivation and test.** Instead of supplying a bare rule or mandating reconstruction,
investigate competing reasons before handing the PR to an ordinary reviewer. Compare ordinary
and conditional-reason preparation on two PRs, three repetitions: twelve final reviews.

**Answer.** Every paired repetition recovered the same one of four agreed asks. Conditional
preparation found more sources without improving recovery; some evidence was applied to the
wrong axis. All 24 edit checks on one PR failed environmentally. There was no no-preparation arm.

**Consequence.** No support for advancing this procedural treatment. It did not test a frozen,
independently acquired resource. The environmental failure limits the negative, and more
citations do not establish that the comparison was preserved or used correctly.

Sources: [pilot](../.claude/worktrees/knowledge-transfer/results/pr_review_v5/probes/knowledge-transfer-2026-10-23/RESULTS.md),
[assessment](../docs/research/review-knowledge-transfer-pilot-assessment-2026-10-23.md).

<a id="e23"></a>

### E23 · Independently acquired compact and full knowledge banks — 24–25 October

**Motivation and test.** E17 exposed wrong scope; E14–E15 made simply adding examples
unpromising. Acquire six checked notes from independent earlier sources, freeze them, give
the same bank to every PR, and compare ordinary/compact/full review. Six development PRs,
three repetitions, 54 final reviews; source selection remained steered by familiar targets.

**Answer.** Neither bank recovered any of the three primary concerns in any repetition:
namespace, proof automation and constant generality. Broader historical recovery was
35.6%, 34.4%, 41.1%; finalized findings were 165, 158, 168. All notes arrived; the primary
misses were absent at submission as well as finalization. The 491-item usefulness panel
remained unlabelled in the inspected record.

**Consequence.** The bank failed its advancement rule. This is more informative than another
exact-supply test, but still developmental evidence. The modest broader change and exploratory
`dslope` proposals cannot rescue the primary result or establish overall usefulness.
Reading the misses motivated a focused test of instantiation and choice.

Sources: [protocol](../.claude/worktrees/reusable-review-knowledge/results/pr_review_v5/probes/reusable-review-knowledge-2026-10-24/PROTOCOL.md),
[completed-review assessment](../.claude/worktrees/reusable-review-knowledge/docs/research/reusable-review-knowledge-results-reading-2026-10-25.md).

<a id="e24"></a>

### E24 · Focused application with and without the frozen note — 26–27 October

**Motivation and test.** Did whole review fail to pose the relevant question, or could the
reviewer not construct or endorse the alternative even when directed to it? Supply the
declaration and concern, compare the frozen note with no note, and include siblings:
72 sessions over three selected cases.

**Answer.** Namespace: the intended alternative appeared 0/3 without the note, 2/3 with it,
then was declined. Generality: all six target sessions built and checked a parameterized
theorem; without the note two suggested it (one full, one partial historical match), with
the note none did. Automation asked about registration rather than the missing proof
simplification, so its negative does not answer that neighboring question.

**Consequence.** Focusing changed some construction, without producing autonomous whole-review
improvement. At least some disagreements persist after a working alternative exists.
The proposed next decision diagnostic is conditional work, not a finding that alternatives
are generally solved or that the notes causally worsen judgment.

Sources: [focused results](../.claude/worktrees/focused-application/results/pr_review_v5/probes/focused-application-2026-10-26/RESULTS.md),
[independent assessment and next question](../docs/research/review-harness-next-question-2026-10-27.md).

<a id="e25"></a>

### E25 · Useful additions, output loss and the evaluation gap — September–October

**Motivation and checks.** Historical recovery omits plausible contributions. Conversely,
valid-looking extra requests can be wrong, out of scope or not worth the API burden.
Audit the old admission gate and later final outputs; assess selected reconstruction additions
and prepare blinded usefulness panels.

**Answers.** The September admission gate discarded 71–83% of obligations already found;
these were actual downstream losses. Later Phase A additions included a checked normalizer
generalization and `gcongr` behavior, but also a purported hypothesis weakening that actually
strengthened it. The subsequent selected-case triage corrected submission/finalization counts
and kept human value labels pending. Textual transmission did not isolate causal benefit
over another ordinary pass. Some out-of-diff suggestions were lost at finalization.
The preparation and bank panels likewise did not supply completed overall usefulness labels.

**Consequence.** Historical recovery is an incomplete reference, while compilation is an
incomplete value test. Finding-stage, delivery-stage and evaluation-stage losses must stay
separate. Park the costly reconstruction pipeline on its current evidence; retain the
conditional comparison question and selected cases without declaring their usefulness settled.

Sources: [admission gate](../docs/research/the-admission-gate-2026-09.md),
[Phase A assessment](../docs/research/review-reconstruction-phase-a-review-2026-10-20.md),
[additions triage and independent corrections](../.claude/worktrees/useful-additions-triage/docs/research/phase-a-additions-triage-2026-10-23.md),
[current empirical evidence register](evidence.md).

## Directions and changes of mind

This table records investment consequences, rather than declaring whole classes of methods
impossible. Several were provisional decisions on selected cases.

| Direction | Why it looked promising | What changed the investment case | Current interpretation |
|---|---|---|---|
| More specialist scheduling | Useful questions were pruned | Unpruned arms remained weak; forced answers changed volume more than the missing requests | Park more fanout tuning as the main lever; no theorem against decomposition |
| Contract and critic alone | Reviewers cleared concerns or stayed silent | Unified verdicts and critics did not clear their gates; forced filing produced partials and burden | Keep useful interface discipline; do not equate it with better judgment |
| Repartition review from a task map | The roster missed design and PR-level work | Facets exposed hard questions but traded away local findings; broad replication changed the task weights | Retain characterization; a new division still needs a strong-baseline test |
| A small detector catalogue | Concrete, checkable alternatives | Narrow families covered little of the tail; pass-through did not establish value | Stopped as a general recall strategy |
| Exact convention supply | Large conditional gains | Applicable entries were selected from the target asks | Retain the positive; acquisition and application remain open |
| Ask-free rule delivery and richer examples | Remove the answer-assisted relevance signal | Gains failed to transfer; known-place sentences already recovered much of the change | Tested delivery forms failed to establish reliable improvement |
| Demand is a tiny fraction of applicability | Many flags went unasked | Wrong rule precedence, non-departures and uncertain calibration corrupted the denominator | Withdraw the single-rate account |
| Rich independent notes | Correct scope could address those input errors | The acquired bank missed every primary concern | Do not keep extending this bank without a new discriminating premise |
| Independent whole-PR reconstruction | Unanchor review and expose alternatives | Sketches transmitted proposals but did not establish the desired final-review gain or value at cost | Deprioritize the expensive route; retain narrower operations and cases |
| More library evidence | Mechanisms and reasons were missing | Sources sometimes changed consideration; working comparisons and requests still diverged | Investigate the particular missing claim; no universal reuse rule |
| Supplied-candidate decision diagnostic | Some focused sessions build an alternative and decline it | Proposed in the 27 October assessment; not yet a demonstrated improvement | Open, conditional investigation with independent contrary cases required |

## Coverage boundaries

Other records were checked for relevance but should not become another progress storyline:

- Serving, caching, cost, token, API-continuity, build-speed and shared-dataflow work made these
  experiments possible. Include a repair when it changes interpretation, as in E01/E08/E21;
  infrastructure completion alone is not evidence of review improvement.
- Removed-declaration audits and naming-threshold sweeps refine task/tool coverage. They are
  supporting detail for E05/E07, not independent evidence of a new general reviewer.
- The PR-representation/blackboard programme was stopped with alternatives unscored. The
  dossier/exam programme and proposed decision diagnostic must also be distinguished from
  completed intervention results.
- June guidelines/selection and July precedent-priming studies explain why some ideas were
  already weak bets. They are older context, not new results since September.
- The saved literature survey and mechanism comparison position the work. Their reported
  product outcomes do not validate transfer to Mathlib; no new literature search was made here.

The next task is to choose a coherent argument from this map. Selection should follow which
question a result answers and which interpretation it changes, with a few concrete zooms.
It should not follow the dates, the raw condition names, or an obligation to mention every row.
