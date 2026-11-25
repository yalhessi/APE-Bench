# Generate four comparable reviews on familiar Mathlib PRs

The [run guide](../guides/checkout-and-runs.md#run-and-score-one-reviewer) covers the independent solo and PR-search reviewers. The [pilot runbook](../../results/pr_review_v5/probes/convention-scope-2026-11-24/pilot.md) covers the existing four-strategy study.

## Run one named reviewer

A researcher chooses a reviewer design, a reviewed head and a run name. The command can score the accepted submission immediately. The same scoring operation can read it again later. A study may supply a list of these invocations. A run can start even when nobody has defined a study or launched another reviewer. See the [glossary](../../GLOSSARY.md#mathlib-pr-review-in-this-fork).

### Four standard definitions

Solo and PR search have named definitions. The two convention names below describe the next milestone. All four use one whole-PR reviewer session per head and sample. The agent sees the title, description, changed files, diff and pinned Mathlib checkout. Its task instruction asks what changes, if any, it would request, and why. It chooses what to investigate. File reads and search, declaration lookup, hover, go-to-definition, Lean goal inspection and Lean verification are available. It submits ordered findings with a reason and requested change, optional locations and an optional overall message. An empty list completes the review. The whole-PR task supplies this instruction in the user message. [Task and submission format](../../src/ape/tasks/lean_tasks/formal_math/review/whole_pr.py)

| Reviewer design | Additional evidence and procedure |
|---|---|
| `solo-v1` | The code and Lean tools above are the full investigation grant. Earlier PR search, Zulip, delivered convention lists, target feedback and the historical per-target checklist are absent. |
| `pr-search-v1` | Add one optional tool that searches a pinned collection of earlier inline comment-and-code excerpts. The starting review message is identical to solo. Record the grant even if the reviewer makes zero calls. |
| `conventions-auto-v1` | A separate selector receives the incoming PR and a fixed catalogue induced from those same earlier excerpts. It may choose zero to 25 entries. Deliver their sentences in catalogue order, with the shared advisory instruction. The reviewer has the solo tool grant. |
| `conventions-reference-v1` | The selector also receives the expert first-round requests for this head. It maps each request to supporting entries or records it as uncovered, with the same overall limit. Use the automatic design's renderer and reviewer grant. The reviewer sees only the selected sentences and advice. This measures reference-informed selection within this catalogue. |

Each name resolves to one checked-in definition shared by the CLI and every study. The definition specifies the task instruction and submission format, evidence grants, preparation procedure and delivery wording. A change to any of those creates a new design revision. The resolved run records the case, concrete evidence edition, selector outputs, execution profile and sample separately. Two runs can use the same design and different evidence or models. A comparison must show these differences before treating their scores as evidence about the design.

The first execution profile pins the pilot's Claude Code 2.1.285, Opus 5.5, xhigh effort, 40 turns, 600,000 processed tokens and the configured $1.50 per-review cost cap. Publish the effective profile alongside the design. A run with a different profile remains identifiable. The initial source edition is the pilot's 997 excerpts from 328 PRs before 1 January 2026. Pin the collection digest for search and learning, and record the catalogue, selector instructions, producer and exact delivered text for convention runs. Zero selected entries deliver the solo message. Selector rationales and expert requests stay outside the reviewer workspace. [Pilot artifacts and settings](../../results/pr_review_v5/probes/convention-scope-2026-11-24/pilot.md#what-is-frozen)

### Run and score a reviewer

These commands use the existing review CLI. The case argument resolves a PR and unique reviewed head in the pinned release. The scorer name resolves the first-round expert reference for that head, ordered submitted-findings projection, request-only rubric, matcher profile and two blind readings. Plan output shows those choices before execution.

```bash
ape/bin/python -m src.mathlib_review.review.cli plan --reviewer solo-v1 --case 42184@c5474cb4
ape/bin/python -m src.mathlib_review.review.cli run --reviewer solo-v1 --case 42184@c5474cb4 --run-name solo-42184-a --score round1-requests-v1 --execute
ape/bin/python -m src.mathlib_review.review.cli run --reviewer pr-search-v1 --case 42184@c5474cb4 --run-name search-42184-a --score round1-requests-v1 --execute
ape/bin/python -m src.mathlib_review.review.cli score --of solo-42184-a --using round1-questions-v1 --execute
```

The two run commands can start in separate terminals when capacity allows. The pilot’s per-run concurrency limit of one applies to the tasks launched by each process. Omit `--score` for generation only. For PR search, the first plan or run builds the excerpt index from local data. The convention reviewers still use the study command. Step 4 below describes the preparation they need to run independently. If scoring fails, retry scoring against the saved submission. A distinct run name requests a fresh sample in these single-head examples. Resuming the same run preserves its sample. Keep researcher-facing names out of model-visible paths.

### Implementation and acceptance

| Order | Change in the existing owner | Observable check |
|---|---|---|
| 1 | Add named design definitions alongside [existing design configs](../../configs/designs/). Extend [CLI plan and run](../../src/mathlib_review/review/cli.py) to resolve a definition and case. Move the [study's](../../src/mathlib_review/review/study.py) message and tool inspection into the normal runner's task preparation. Plan and execute consume the same resolved task. Include the exact rendered messages, tool schemas, profile, head, patch and evidence digests. Existing configs remain usable. New reviewer definitions can use the same run and score commands without adding a strategy branch to the study driver. | Plan and run `solo-v1` with the history files and expert feedback unavailable. Plan search independently. On 42184 its only reviewer-visible difference is the extra search tool. October's ordinary reviewer actually used that tool and cannot stand in for this solo baseline. [Archived search call](../../results/pr_review_v5/probes/postcutoff-2026-09-29/pr42184/X1/calls.jsonl#L26) |
| 2 | Make the runner publish [the accepted submission](../../src/mathlib_review/analysis/submissions.py) for each head and sample. Use APE's accepted attempt, preserve its exact submitted fields, and check the live transcript and grants against the plan. Retain the study archive as a reader of existing results. | A single review immediately yields a stable submission reference. A successful empty review yields one too. An interrupted attempt can resume. Failure on a different head or reviewer leaves the completed submission available. |
| 3 | Teach the [matcher](../../src/mathlib_review/analysis/matching.py) to read one or several accepted submissions directly. Have `run --score` call that same operation after saving. Resolve the reference bytes, projected findings, rubric, blinding and matcher settings before reusing a reading. Show requests reached out of eligible requests, findings submitted and the finding index credited for each match. | Score one archived 42184 review by itself with generation unavailable. For two archived reviews, revising the reference from two asks to one under the same reading name must change four judgments to two or identify the conflict. Zero expert requests still yields a finding count and an undefined recovery rate. Jointly scoring two reviews is a separate reading from scoring each alone. |
| 4 | Split [convention preparation](../../src/mathlib_review/conventions/selection.py) into reusable catalogue production and per-head selection. Reuse its packet sessions, source checks and selector outputs. Share completed immutable products across run names. Limit exclusive preparation to the particular missing product. | Search can finish while catalogue learning is pending. Two convention reviewers requesting the same missing catalogue pay for one preparation. Equal selections render byte-identical reviewer messages, and their separate producer records identify which selector saw the expert feedback. |
| 5 | Verify process isolation at the run entry point. APE already places task storage under the orchestrator ID and controls concurrency within a run. Give independent runs private writable workspaces, traces and output locations, and share pinned read-only inputs. Claim a run name atomically before spending. | Start solo and search on the same head with two workers and a capacity of two. Observe overlapping executions and two attributable submissions. Interrupt one and complete the other. A second launch with the same active name must observe the running job without executing it again. Resuming a name with a different resolved design, head or profile must identify the mismatch. A scorer can start on either completed submission. |

**Smallest runnable milestone.** Deliver steps 1–3 for solo and search and exercise step 5 on that pair. Then enable both convention designs with step 4 and repeat the concurrency check with shared preparation. Finally make the existing study command invoke the same operations. Its useful additional check is whether the paired reviewer inputs differ only in the ways the study declared.

**Earlier preflight.** At `b5009f69`, two independent native `plan --config` processes for PR 42184, one solo and one with the excerpt-search overrides, each resolved a single whole-PR task and a prebuilt reviewed workspace. The lower-level matcher also built a one-subject plan from the archived ordinary review with one submitted finding, two expert requests and two readings. These were local preflights. The named interfaces now resolve both reviewers on this head. Their first-message hashes agree, and PR search adds only `precedent_search` to the tool grant. In the [CLI regression](../../tests/mathlib_review/test_named_reviewers.py), a substitute provider holds solo open while PR search completes. A duplicate solo launch is refused, the interrupted solo resumes, and both submissions have distinct task stores. A separate check reduces the paired 42184 reference from two requests to one and observes a new plan with two judgment cells per reading in place of four. A fresh live pair and its judged scores are still outstanding.

## Map issue

**Title** · Generate four comparable reviews on familiar Mathlib PRs

**Label** · `wayfinder:map`

### Destination

A specification and local acceptance check for generating four reviews of the same Mathlib revision. Each saved submission can be evaluated against the same first-round expert requests under a later rubric without calling the reviewer again.

### Notes

- Use familiar PRs only. The expert review is historical reference feedback. Generate four agent reviews per PR per independent sample.
- Ordinary solo receives the PR, its pinned codebase and code/Lean tools. The search reviewer additionally has on-demand access to earlier comment-and-code excerpts. Excerpts suffice for this pilot.
- The other two reviewers receive convention sentences. An automatic selector sees the incoming PR and a fixed catalogue. An offline selector may also see its expert requests to assign the catalogue entries behind them. Both reviewers receive catalogue sentences in the same format. Only the offline selector and evaluator may see the target feedback.
- Direct search and catalogue construction share one dated collection, per the existing shared-history decision. The reviewer may use the pinned library as evidence in every design.
- Use the project glossary, the saved four-design input audit, and the grilling and domain-modeling skills when settling the task contract. Register the generated review separately from each run that evaluates it.

### Decisions so far

<!-- Resolution links go here when a child issue closes. -->

### Not yet specified

If the shared catalogue leaves either familiar case without a convention behind its expert request, revisit what that case can diagnose once the source coverage is known.

### Out of scope

A new PR draw, opening the reserved evaluation set, full historical PR browsing, redesigning APE's general review pipeline, and estimating the average improvement on incoming PRs. The exact condition measures the value of supplying reference-informed entries from this catalogue. Catalogue coverage and reviewer judgment both affect this reference point.

## Decision tickets

### What does an ordinary solo reviewer receive and submit?

`wayfinder:prototype` · Available now.

**Question**

What is the smallest common whole-PR task we recognize as ordinary review? Compare the actual first user message, available tools and submission schema against this candidate instruction on a familiar PR. “Review this Mathlib PR at the supplied revision. What changes, if any, would you ask the author to make? Give an ordered list of findings. For each finding, say what to change and why. You may return an empty list.” Decide what belongs in the model-facing contract, including how to submit a general finding. The existing baseline adds eight checks per target, a computed change map, verdict and classifications. Dropping the configured brief alone selects another built-in prompt. Decide which list the author receives and archive the underlying accepted submission, including any optional message and edits.

### Which excerpts make up the shared history?

`wayfinder:grilling` · Available now.

**Question**

Which dated comment texts and associated code hunks are eligible for both search and catalogue construction? A local candidate is the pre-2026 development export. Its 390 PRs contain 1,140 agreed requests, including 999 inline comments. Starting from the inline comments with verifiable edit times and recoverable hunks would fit the existing search interface. That choice would give both designs a history enriched for maintainer requests. Decide the cutoff, eligibility and excerpt boundaries. Record each retained ID, PR, timestamp, code and text, plus exclusions and the collection hash. Check which historical sources behind the familiar cases survive. The current default index is missing one of the two known origin comments for PR 42184.

### How should the two selectors deliver conventions?

`wayfinder:prototype` · Blocked by [the ordinary review contract](#what-does-an-ordinary-solo-reviewer-receive-and-submit) and [the shared history](#which-excerpts-make-up-the-shared-history).

**Question**

Given the frozen excerpts, what catalogue, selection rule and reviewer-visible list would make the two designs comparable? Trace catalogue entries back to earlier excerpts. Allow the automatic selector to use the incoming PR and code, and reserve expert requests for the offline assignment. Specify handling for an empty selection, a request the catalogue cannot express, list order, and the limit on delivered entries. Try the same list through both routes and compare the rendered bytes. A candidate delivery instruction is “Use these conventions when they apply. Decide whether any change is worth asking the author to make.” Keep selector rationale, target locations inferred from feedback and strategy names out of the reviewer input. Record them, where applicable, for analysis. Keep automatic selection cost and reviewer cost distinguishable.

### What makes a generated review ready to compare again?

`wayfinder:prototype` · Blocked by [the ordinary review contract](#what-does-an-ordinary-solo-reviewer-receive-and-submit) and [convention delivery](#how-should-the-two-selectors-deliver-conventions).

**Question**

What evidence must a run retain for a later reader to recover exactly what went in and which ordered findings came out? Use the actual scaffold and tool registrar to compare all four first messages and tool grants. Check visible paths, readable files and alternate tools for access to target feedback and strategy names. Bind each opaque run ID privately to the PR, reviewed head and patch, strategy, sample, model/scaffold settings, budget, source and catalogue hashes, selection, tool trace, cost, status and submitted review. Preserve a successful empty list separately from failure. Demonstrate two versioned evaluation plans consuming the same saved submissions and retaining distinct verdicts. Settle the sample count and retry policy before generation.

## Work this unlocks

| Order | Implementation work | Ready when |
|---|---|---|
| 1, in parallel | Add a pilot whole-PR contract to the existing solo task and scaffold. Use opaque run and workspace names. | The rendered messages and tool grants implement the agreed contract. The PR, reviewed files, Lean tools, model and reviewer budget agree across designs. |
| 1, in parallel | Materialize the shared excerpt file, build a pilot index, and point the search tool at that index. The index builder already accepts a corpus and output directory. The tool currently opens the default shared index. | A test query returns an eligible excerpt and its source ID. The trace records the pilot collection hash. Later edits and target feedback are excluded. Only the search reviewer has this tool. |
| 2 | Derive or verify one catalogue using those excerpts alone. Freeze it. Prepare an automatic selection and a separate offline exact assignment for each familiar PR. Reuse the existing selector and list builders where their inputs match. | Every delivered entry resolves to the frozen catalogue. Identical selections render identically. Keep a record of entries available, selected and delivered so a missed finding can be traced. |
| 3 | Pin the reviewed inputs, save the four generation manifests and private mapping, inspect actual model-visible inputs, and exercise the evaluation handoff on an archived submission locally. | Differences between arms are accounted for by the allowed search tool or delivered sentences. The ordinary arm has neither. A second evaluation plan identifies the same immutable submission. |
| 4 | Run the four strategies on each agreed familiar case in the user's model-enabled shell. Retain outputs before any post-processing and create the blind comparison from them. | Report first-round requests recovered and submitted finding counts per PR and sample. Inspect additional findings on their merits. Report failed attempts and selection misses separately. |

**Suggested first batch.** Use the original reviewed heads of PR 42184 (`c5474cb4`) and PR 41930 (`ec56eae5`). One sample of each strategy on each case gives eight reviewer sessions, plus any model work for the catalogue, automatic selection or semantic judging. The historical automatic selector included both reference entries on 42184 and missed the single reference entry on 41930. Recheck those relationships after rebuilding the catalogue. These contrasts explain the choice of fixtures. They are observations about the old selector. If the new selections change, record the change. A second independent sample generates eight new reviews. A second reading of the first eight uses their saved submissions.

**Why the shared collection matters on PR 41930.** The archived exact rule, P041, asks authors to motivate a new concept, lemma or design change. Its originating inline comment on PR 29121 asks for the motivation for a *concept*. The catalogue editor later extended it to *design changes* using an issue comment and to *new lemmas* using a review body. An inline-only collection retains the origin and excludes both of those revisions. Check whether the new catalogue actually covers the maintainer’s question about renaming arguments on 41930. An empty exact assignment is a valid outcome. [Origin](../../results/pr_review_v5/adjudications/conventions-census-v1/reader_A/labels_b00.jsonl#L48) · [Design-change extension](../../results/pr_review_v5/adjudications/conventions-census-v1/reader_A/labels_b01.jsonl#L78) · [Lemma extension](../../results/pr_review_v5/adjudications/conventions-census-v1/reader_A/labels_b09.jsonl#L5)

**Existing evidence and entry points**

- The [input audit](../../results/pr_review_v5/probes/convention-scope-2026-11-24/design-audit.md) traces the inherited prompt, tool grants, exposed run names, source mismatch, and submitted findings. The [renderer check](../../results/pr_review_v5/probes/convention-scope-2026-11-24/inspect_four.py) reproduces the audit on PR 42184 without a provider.
- The [shared-history decision](../adr/0001-shared-history-for-review-comparisons.md), [development export](../../data/pr_review_v5/first_round_development_before_2026-01-01.jsonl), [index builder](../../src/mathlib_review/retrieval/precedent_index.py) and [search tool](../../src/ape/tasks/lean_tasks/formal_math/review/context_tools.py) locate the data work. The export contains the two earlier inline comments behind the 42184 assignments, IDs `2553749321` and `2160528211`.
- The [reviewed episodes](../../inputs/probes/probe-2026-07-08-v1/input/episodes.jsonl), [October selector builder](../../results/pr_review_v5/probes/conventions-ceiling-2026-10-04/build_selector_folders.py) and [exact-list builder](../../results/pr_review_v5/probes/conventions-ceiling-2026-10-04/build_exact_briefs.py) provide fixtures. The [existing replay procedure](../../results/pr_review_v5/probes/convention-scope-2026-11-24/reproduce-review-reading.md) shows the working `run`, `probe match-plan`, `match` and `report match` entry points. Its generation example reproduces the audited historical conditions.
- [Preserve exact submitted review edits through comparison](https://github.com/yalhessi/APE-Bench/issues/2) tracks a narrower concern about what consumers can recover from a submission.
