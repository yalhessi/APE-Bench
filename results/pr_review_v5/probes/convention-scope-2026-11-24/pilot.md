# Run the four-reviewer pilot

To run solo or PR search on one head and score its saved submission, use the [independent reviewer commands](../../../../docs/guides/checkout-and-runs.md#run-and-score-one-reviewer).

One generation sample produces eight reviews. Four whole-PR reviewers assess the same two familiar Mathlib revisions. Both PRs have an expert first review round. The comparison asks which historical requests each submission recovers and how many findings it asks an author to read. These cases were selected with knowledge of the historical results.

| Strategy | Earlier review evidence available |
|---|---|
| Solo | The reviewer can investigate the PR and its pinned Mathlib checkout using file, declaration and Lean tools. |
| Search earlier reviews | The same reviewer can also query earlier comment-and-code excerpts by similarity to Lean code. Calling search is optional. |
| Automatically selected conventions | A separate reader selects up to 25 entries from a frozen catalogue using the PR title, description, files and diff. The reviewer sees only the selected sentences in catalogue order, with an invitation to exercise judgment. |
| Reference-informed conventions | A separate offline reader sees the same PR and catalogue plus the maintainer’s requests. It assigns entries to each request and records uncovered requests. The reviewer receives the same presentation as the automatic condition. |

The public review is the ordered list of findings the reviewer submits. A finding gives the proposed change and the reason. The reviewer can leave the location unspecified for a PR-wide comment, or submit an empty list. APE archives the optional summary separately. The first reading scores the list.

## Run from this topic worktree

The [study definition](../../../../configs/studies/familiar-conventions.yaml) pins the reviewed heads, shared history and cutoff, reference set, model configs and output directory. The same CLI accepts another study YAML. For a solo versus search comparison, set `strategies: [solo, history]`, omit `selector`, and give the study a new output directory. That comparison skips catalogue and selector sessions. Use the repository’s worktree environment and your Claude subscription login for model execution.

```bash
cd /research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/convention-scope-pilot-20261124
export PYTHONPATH="$PWD/src:$PWD" ELAN_HOME=/research/projects/proofedit/ya475/.elan
export PATH="$ELAN_HOME/bin:$PATH"
ape/bin/python -m src.mathlib_review.review.cli study plan familiar-conventions
ape/bin/python -m src.mathlib_review.review.cli study run familiar-conventions --execute
ape/bin/python -m src.mathlib_review.review.cli study score familiar-conventions --execute
```

`plan` checks both real heads and the four tool grants locally. It uses demonstration sentences to test delivery while the real catalogue is pending. `run` prepares missing convention selections, preflights all four real reviewer inputs, runs one paired sample and archives the accepted submissions. You can run just the preparation with `study prepare familiar-conventions --execute`. Preparation and reviewer execution reuse completed work on a retry. For a rejected extraction output, `study prepare familiar-conventions --retry extract=2 --execute` selects a new producer for that unaccepted stage.

The first sample calls for **15 preparation sessions** (ten extraction batches, one consolidation and four selections), **eight reviews**, and **two blind matcher sessions**. Each PR has one reference-informed selection with per-request justifications. Reviewers have 40 turns and a 600,000-processed-token ceiling per PR.

Use `study score familiar-conventions --question-form --execute` to apply the alternative rubric to the same submitted findings. Use `--reading NAME` for another comparison and `--sample 2` on both run and score for a new reviewer sample. Model calls require `--execute`. The [checkout and run guide](../../../../docs/guides/checkout-and-runs.md) describes the subscription environment, including credentials that select a competing provider route.

## What is frozen

- **Targets.** PR 41930 at `ec56eae52c28b70ec6cc92f1a295973c193353a0` and PR 42184 at `c5474cb4a68a515228b49225b38a2507264f91f7`. Both have prebuilt reviewed workspaces. The release marks both descriptions as verified at review time. The cached timelines record a single later Bors rename on each PR with the release title as the previous title. [Reviewed episodes](../../../../inputs/probes/probe-2026-07-08-v1/input/episodes.jsonl)
- **History.** The request-enriched development export yielded 997 inline excerpts from 328 PRs. The last known edit must precede 1 January 2026. The excerpt holds up to the first 400 characters of the comment and the last 800 of its hunk. Of 1,140 candidate requests, 99 issue comments, 42 review bodies and two incomplete inline records were excluded. Search and convention extraction use the same corpus, SHA-256 `1a7b07366da7f69298b2a7780ba57ca35f9f1eb4f83cd384bb700e81d6242f03`. Three historical source comments were returned first when queried with their own hunks. A reviewer has to choose its own query. [Collection builder](../../../../src/mathlib_review/retrieval/excerpts.py)
- **Catalogue and selectors.** The ten extraction packets contain earlier excerpts only. An induced sentence must cite text in its batch. Consolidation groups equivalent entries. The offline assignment can return zero entries for an ask. Emptiness is a catalogue-coverage outcome. The automatic selector never sees target requests. Both selectors hand off IDs, and the renderer delivers only catalogue sentences. An empty delivery gives the same text as solo. Each nonempty delivery uses the same advisory wording. [Preparation and validation](../../../../src/mathlib_review/conventions/selection.py)
- **Comparison.** A private map binds opaque run IDs to the strategy, sample, pinned head and patch, prompt, model, budget, grants and evidence. Capture checks the live SDK transcript, tools, containment, budget and accepted attempt. An incomplete run stays incomplete. The matched input is a projection of the original ordered list with location, reason and requested change. The optional message and exact submitted fields remain available to future rubrics. [Generation and input checks](../../../../src/mathlib_review/review/study.py) · [Capture and replay](../../../../src/mathlib_review/analysis/submissions.py)

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
