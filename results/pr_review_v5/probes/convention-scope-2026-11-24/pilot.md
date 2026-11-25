# Run the four-reviewer pilot

One generation sample produces eight reviews. Four whole-PR reviewers assess the same two familiar Mathlib revisions. Both PRs have an expert first review round. The comparison asks which historical requests each submission recovers and how many findings it asks an author to read. These cases were selected with knowledge of the historical results.

| Strategy | Earlier review evidence available |
|---|---|
| Solo | The reviewer can investigate the PR and its pinned Mathlib checkout using file, declaration and Lean tools. |
| Search earlier reviews | The same reviewer can also query earlier comment-and-code excerpts by similarity to Lean code. Calling search is optional. |
| Automatically selected conventions | A separate reader selects up to 25 entries from a frozen catalogue using the PR title, description, files and diff. The reviewer sees only the selected sentences in catalogue order, with an invitation to exercise judgment. |
| Reference-informed conventions | A separate offline reader sees the same PR and catalogue plus the maintainer’s requests. It assigns entries to each request and records uncovered requests. The reviewer receives the same presentation as the automatic condition. |

The public review is the ordered list of findings the reviewer submits. A finding gives the proposed change and the reason. The reviewer can leave the location unspecified for a PR-wide comment, or submit an empty list. APE archives the optional summary separately. The first reading scores the list.

## Run from this topic worktree

The launcher sets the worktree Python path, selects the local Lean toolchain and uses the Claude subscription route. For the model-backed commands, use the shell where your Claude subscription login is configured.

```bash
cd /research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/convention-scope-pilot-20261124
pilot=results/pr_review_v5/probes/convention-scope-2026-11-24/pilot.sh
bash "$pilot" check
bash "$pilot" --execute
```

`check` uses no provider. It verifies the indexed history, preflights all four designs at both reviewed heads, compares rendered first messages and registered tools, and seals two rubrics over a pair of real archived reviews. The convention-delivery fixture uses one demonstration sentence on one PR and an empty list on the other. The fixture has separate IDs and cannot enter the pilot comparison.

`--execute` prepares the live catalogue and selections, preflights all four live inputs, generates the reviews, archives the accepted submissions, runs two blind readings under the request-only rubric and prints the report. The planned first sample costs **15 preparation sessions** (ten source batches, one consolidation, two automatic selections and two reference-informed assignments), **eight review sessions**, and **two matcher sessions**. All use Opus 5.5 on the subscription. Reviewers have 40 turns and a ceiling of 600,000 processed tokens per PR. Actual consumption is recorded. One exact assignment per PR is a reading of the expert feedback, with justifications available for inspection.

Rerun the same command after an interruption. The launcher reuses accepted preparation stages and completed reviewer runs. A partial reviewer run uses APE’s resume policy. Inspect its attempts and caps when interpreting a result. For a semantically invalid preparation output, the error identifies its stage. After inspecting the output, `bash "$pilot" conventions --execute --retry extract=2` uses a new producer for an unaccepted extraction stage. Substitute the indicated stage as needed. Use a new reading name such as `compare --reading revised-asks` when revising the reference or comparison. Each rubric digest gets its own directory. A fresh independent set of reviews requires a new sample number.

```bash
# Prepare an alternative reading of the existing sample, then run its two blind matchers.
bash "$pilot" compare --question-form
bash "$pilot" compare --question-form --execute

# Generate another review sample conditional on the same frozen selections, if needed.
bash "$pilot" generate --sample 2 --execute
bash "$pilot" compare --sample 2 --execute
```

## What is frozen

- **Targets.** PR 41930 at `ec56eae52c28b70ec6cc92f1a295973c193353a0` and PR 42184 at `c5474cb4a68a515228b49225b38a2507264f91f7`. Both have prebuilt reviewed workspaces. The release marks both descriptions as verified at review time. The cached timelines record a single later Bors rename on each PR with the release title as the previous title. [Reviewed episodes](../../../../inputs/probes/probe-2026-07-08-v1/input/episodes.jsonl)
- **History.** The request-enriched development export yielded 997 inline excerpts from 328 PRs. The last known edit must precede 1 January 2026. The excerpt holds up to the first 400 characters of the comment and the last 800 of its hunk. Of 1,140 candidate requests, 99 issue comments, 42 review bodies and two incomplete inline records were excluded. Search and convention extraction use the same corpus, SHA-256 `1a7b07366da7f69298b2a7780ba57ca35f9f1eb4f83cd384bb700e81d6242f03`. Three historical source comments were returned first when queried with their own hunks. A reviewer has to choose its own query. [Collection builder](pilot/history.py)
- **Catalogue and selectors.** The ten extraction packets contain earlier excerpts only. An induced sentence must cite text in its batch. Consolidation groups equivalent entries. The offline assignment can return zero entries for an ask. Emptiness is a catalogue-coverage outcome. The automatic selector never sees target requests. Both selectors hand off IDs, and the renderer delivers only catalogue sentences. An empty delivery gives the same text as solo. Each nonempty delivery uses the same advisory wording. [Preparation and validation](pilot/conventions.py)
- **Comparison.** A private map binds opaque run IDs to the strategy, sample, pinned head and patch, prompt, model, budget, grants and evidence. Capture checks the live SDK transcript, tools, containment, budget and accepted attempt. An incomplete run stays incomplete. The matched input is a projection of the original ordered list with location, reason and requested change. The optional message and exact submitted fields remain available to future rubrics. [Generation and input checks](four_reviews.py) · [Capture and replay](pilot/measure.py)

## Read the artifacts

All paths below start at `.ape/four-review-pilot/` in the topic checkout.

| Artifact | What it answers |
|---|---|
| `history/manifest.json`, `history/exclusions.jsonl` | Which earlier PR records qualified and which were excluded? |
| `conventions/protocol.json` and, after preparation, `catalogue.json`, `automatic.json`, `exact.json`, `seal.json` in that directory | Which catalogue entries could be used, which were chosen, and what evidence and stage outputs support them? |
| `wiring/generation.json`, `wiring/archived-42184/readings/` | What passed the local comparison check with fixture sentences and archived submissions? |
| `sample-1/generation.json` and `sample-1/inputs/` | What did the four real strategies have access to before they ran? |
| `sample-1/archive.json` and `sample-1/submissions/` | What did each reviewer actually submit? What tools, time and tokens did it use? |
| `sample-1/readings/<reading>-<rubric hash>/` | How does a versioned blind reading score the same submissions? Each reading has its own plan, verdicts and report. |

Read reach per PR and matcher alongside finding counts. Look at the original findings before treating unmatched ones as unnecessary. On 42184 the historical automatic selector had already selected both reference entries. On 41930 the historical catalogue broadened a concept-motivation rule using sources outside the pilot’s inline excerpts. Inspect the new catalogue coverage and selections before attributing a difference to the reviewer. [Original audit](design-audit.md) · [Work map](../../../../docs/plans/2026-11-25-four-review-strategies.md)
