# Generate four comparable reviews on familiar Mathlib PRs

Tracker draft for `yalhessi/APE-Bench`. The first section is the map issue. The four decision tickets and their dependencies follow it.

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
