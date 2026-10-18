# The four briefs, as handed over (2026-10-09, about 08:52 EDT)

**How the round ran.** Four `general-purpose` subagents of the orchestrating session (Opus 5.5, the
primary subscription), launched together in the background, read-only, each with its own lens. None
saw another's brief or report.

**Substitutions.** Each prompt below is shown as sent, with two substitutions only:
- `draft.md` (this folder) stands for the draft at `<SP>/round3/draft.md`, where `<SP>` is the
  session scratchpad
  `/tmp/claude-1905243447/-research-projects-proofedit-ya475-APE-Bench/592272bf-2a21-4fd7-84f0-c3c437872216/scratchpad`;
- `W` is the worktree `/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/conventions-dossiers`.

---

## R1 — the record and the evidence

You are one of four independent reviewers in an adversarial round on a design in the APE-Bench repository (Mathlib PR review research). Your lens: **THE RECORD AND THE EVIDENCE — for each of the draft's five components, does the project's own record (and the external systems it cites) support the expected effect, does it repeat a recorded dead end, and what is the most recall it could add?**

## Rules
- Read-only. Do not edit, write or commit anything in the repository. Do not start any LLM call, `claude` process, Slurm job or GPU job. Python/grep/sed for reading and counting is fine; scratch files only under <SP>/round3/R1/.
- Token economy: stay under ~120k tokens. Use grep, `sed -n` ranges and small Python counts.
- The other reviewers' reports are not available to you; do not look for them.

## Read first
The draft: `<SP>/round3/draft.md`.

## The record (W = /research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/conventions-dossiers, the branch with today's work)
- `W/docs/research/ceiling-residual-2026-10.md` (why the ceiling is not 100%), `W/docs/research/decompose-and-shrink-review-2026-10.md` (+ its folder: the last round's reports), `W/docs/research/conventions-dossiers-review-2026-10.md`, `W/docs/research/code-review-systems-survey-2026-09.md` (incl. "Revisited 2026-10-09"), `W/docs/research/open-code-review-comparison-2026-09.md`.
- `W/results/pr_review_v5/probes/conventions-ceiling-2026-10-04/README.md` (stages C, F, G, H, D, Result 7), `W/results/pr_review_v5/probes/conventions-ladder-2026-10-08/README.md`, `W/results/pr_review_v5/probes/conventions-places-2026-10-09/README.md` (running now).
- `W/docs/dead-ends.md` (detectors, statute, selection from artifact-only signals, precedent priming Mode A and flag-rate priors, family division, specialists as the coverage floor, idiom checker, linter-as-oracle).
- `W/docs/todo/selection-signal.md` (cross-run agreement), `W/docs/plans/2026-10-01-beyond-the-solo-baseline.md` and `W/docs/plans/2026-10-03-after-structure.md` (K passes, D1/D2, closer battery, analogue retrieval), `W/results/pr_review_v5/probes/closer-battery-2026-09-26/README.md`, `W/docs/todo/static-analysis-pass.md`, `W/docs/todo/lean-persistent-checker.md`, `W/docs/todo/remaining-misses-kind.md`.

## Your task
For each component A (engine: A1-A6), B (aggregated solo), C (exhaustive execution checks), D (history source), E (census robustness):
- What does the record say about its mechanism? Cite the closest prior experiment, its result, and whether the conditions differ enough that the result may not transfer (model, delivery, regime).
- Is any part a re-run of a dead end under another name? Say exactly which reopen condition it does or does not meet.
- The most issue recall it could add on the dev held-out 12 and on the probe sets, with numbers from the record where possible (e.g., the union figures in the draft; the closer battery's 8 of 15; the residual classes).
- Which components are most and least likely to move a deployable reviewer past solo, in your judgement, and why.

## Deliver, as your final message (≤ 1,200 words; it goes to the orchestrating session, not the user)
1. Verdict per component (keep / narrow / drop / defer), one line each, then one paragraph overall.
2. The strongest objections, ranked, each with evidence (file:line or figure) and what would refute it.
3. Proposals you would reject outright, with evidence.
4. What is missing from the draft that the record says matters.
5. The order you would run the measurements in, and the one you would cut.
Report at the altitude the evidence supports; separate "tried and failed" from "cannot work"; mark read versus inferred. The project's goal is issue recall.

---

## R2 — mechanics, codebase and cost

You are one of four independent reviewers in an adversarial round on a design in the APE-Bench repository (Mathlib PR review research). Your lens: **MECHANICS, CODEBASE AND COST — can each component be built as described, where does it belong in the codebase under the project's rules, what will break, and what does it really cost in GPU time, compute and subscription tokens?**

## Rules
- Read-only. Do not edit, write or commit anything in the repository. Do not start any LLM call, `claude` process, Slurm job or GPU job. Python/grep/sed for reading and counting is fine; scratch files only under <SP>/round3/R2/.
- Token economy: stay under ~120k tokens. Read signatures and docstrings, not whole modules.
- The other reviewers' reports are not available to you; do not look for them.

## Read first
The draft: `<SP>/round3/draft.md`.

## The codebase and rules (W = /research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/conventions-dossiers)
- `W/CLAUDE.md` — read in full: "Code: native to APE, and minimal" (TaskOrchestrator, BaseTask.spawn_subtasks, ExecutionLimits, the run layout, one entrypoint per pipeline, every knob in the run name), the providers and the self-hosted DeepSeek section (server on `first`, 8 GPUs, ~12 min to serve, 8-hour job limit, the patched stack), the frozen roots, the commit rules.
- `W/docs/research/codebase-redesign-2026-10.md` §4 (producers seam, designs own their run data, the stage as the probe unit).
- `W/src/mathlib_review/producers/__init__.py` (the producer interface), `W/src/mathlib_review/review/runner.py` (the `design` field; grep `design`), `W/src/mathlib_review/review/merge.py`, `W/src/mathlib_review/analysis/probes.py` (probe harness: packets, seals, matcher inputs).
- The probe scripts the draft builds on: `W/results/pr_review_v5/probes/conventions-places-2026-10-09/places.py` and `run_places.sh`; `W/results/pr_review_v5/probes/conventions-ladder-2026-10-08/ladder.py`; `W/results/pr_review_v5/probes/closer-battery-2026-09-26/` (battery.py, outcomes.json: compile times).
- `W/docs/research/reviewed-workspaces.md` (how reviewed workspaces are built and restored; their identity), `W/docs/todo/lean-persistent-checker.md` (compile cost).
- Live throughput facts: the ladder ran 585 one-turn DeepSeek calls in ~2 h at 24 concurrent (median ~15k completion tokens, 11% hit 32k); the places test is running 2,022 calls at 48 concurrent at about 9 a minute (log: `/research/projects/proofedit/ya475/localmodel/logs/ds41_places_run.log`, read only). The primary Claude subscription's week resets at 10:00 today; blind matchers cost ~0.1-0.2M tokens per matcher run.

## Your task
- For A1-A6, B, C, D, E: what exists already (cite file and function), what must be written, and where it should live under CLAUDE.md's rules (probe script vs `src/` vs a new design vs a producer). Flag anything the draft puts in the wrong place, or that duplicates a primitive.
- Mapping a segment to a `primary_change_id` so findings can be judged: does the change graph support that, and how?
- Cost: calls per PR for A (places × rules × samples), wall time on `first` for measurements 1-5 at the observed throughput, compile counts and time for A5 and C, subscription tokens for the matchers. Which measurements fit in one 8-hour server, which need several?
- Failure modes: workspaces not built for census PRs (A4 and C on census PRs need them?), compile flakiness, KV pressure, the server's 8-hour limit, leakage (census PRs vs evaluation sets), the run-name rule.
- The cheapest build that still answers the draft's main question.

## Deliver, as your final message (≤ 1,200 words; it goes to the orchestrating session, not the user)
1. Verdict per component on buildability (as specified / needs change / not buildable now), one line each, then one paragraph overall.
2. The strongest objections, ranked, each with evidence (file:line or figure) and what would refute it.
3. A cost table for measurements 1-6 (calls, GPU hours, compile hours, subscription tokens).
4. Placement in the codebase you would require, and anything you would reject outright.
5. The cheapest build-and-measure sequence that answers the main question.
Report at the altitude the evidence supports; mark read versus inferred.

---

## R3 — measurement and evaluation

You are one of four independent reviewers in an adversarial round on a design in the APE-Bench repository (Mathlib PR review research). Your lens: **MEASUREMENT AND EVALUATION — will the draft's six measurements tell us whether we have a better deployable reviewer than solo, are their thresholds informative and powered, and is the evaluation valid (in-sample vs out-of-sample, volume, the judge)?**

## Rules
- Read-only. Do not edit, write or commit anything in the repository. Do not start any LLM call, `claude` process, Slurm job or GPU job. Python/grep/sed for reading and counting is fine; scratch files only under <SP>/round3/R3/.
- Token economy: stay under ~120k tokens.
- The other reviewers' reports are not available to you; do not look for them.

## Read first
The draft: `<SP>/round3/draft.md`.

## The record (W = /research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/conventions-dossiers)
- `W/CLAUDE.md` §"Reporting results" (three reps; judge self-agreement ~90% so one obligation at n≈8 is ±12pp; `location_recall` is not a quality signal; gold is a lower bound, precision claims unsupported; `coverage_gaps`; the routing degenerate-check).
- The probe sets and their measurement: `W/results/pr_review_v5/probes/conventions-ceiling-2026-10-04/README.md` (stage D Result 7: three reps, two blind matchers, read_stage.py; one ask = 0.026), the matcher rubric in any `match_*` input folder (`W/src/mathlib_review/analysis/probes.py`, grep `matcher_rubric`).
- The dev held-out 12 and its judge: `W/results/pr_review_v5/probes/local-ds41-2026-10-06/` (DeepSeek 8, 6, 9 of 23), `W/docs/plans/2026-10-01-beyond-the-solo-baseline.md` §5 (rules stated before any run; ensembles; control emission), `W/docs/plans/2026-10-03-after-structure.md`, `W/docs/todo/eval-set-selection.md`, `W/docs/todo/judge-and-measurement.md`, `W/docs/todo/selection-signal.md` (cross-run agreement, in-sample).
- The places test running now: `W/results/pr_review_v5/probes/conventions-places-2026-10-09/README.md` (its pre-registered rule and the secondary readings).
- `W/docs/research/ceiling-residual-2026-10.md`, `W/docs/research/decompose-and-shrink-review-2026-10.md`.
- `W/docs/todo/adjudication-rubric.md` (the unadjudicated ~90%), stage H in the stage README (maintainers raise 1 in 20 to 1 in 400 of flagged places).

## Your task
- For each measurement 0-6: what result would change what we build, what would not; is the threshold informative given the noise (one ask = 0.022 of 46; judge noise; DeepSeek rep-to-rep 6-9 of 23 on dev); is the comparison fair (same reps, same matchers or judge, same seal)?
- In-sample vs out-of-sample: the designs were developed on stage L/D's probe sets; which measurements can only show in-sample effects; is the dev held-out 12 a clean evaluation for these designs (were any of its PRs used to develop conventions work)? Is there a fresher set (`eval-set-selection.md`, a held-out window)?
- Volume without gold: the draft reports findings per PR and control-PR emission. Is that enough to tell "a better reviewer" from "a detector with a model in it"? What volume guard does the record use, and should this design use a different one?
- How to compare designs A and B against solo, and against each other, in one fair frame; and what "better deployable reviewer" should mean as a pre-stated rule.
- A4's calibration on census PRs: can it be validated, with what power (asked pairs per rule on 25 PRs)?

## Deliver, as your final message (≤ 1,200 words; it goes to the orchestrating session, not the user)
1. Verdict on the measurement plan, one paragraph.
2. The strongest objections, ranked, each with evidence and what would refute it.
3. A corrected measurement plan: for each kept measurement, the set, the comparison, the threshold, and its noise.
4. The single pre-stated rule for "a better deployable reviewer than solo".
5. Measurements you would cut or reorder, with reasons.
Report at the altitude the evidence supports; mark read versus inferred.

---

## S — steelman

You are the STEELMAN in an adversarial round of four on a design in the APE-Bench repository (Mathlib PR review research). Three other reviewers attack it independently; your job is to make the plan as strong as it honestly can be — the strongest combination of components, the missing ideas, and the cheapest decisive sequence — then say where even that fails.

## Rules
- Read-only. Do not edit, write or commit anything in the repository. Do not start any LLM call, `claude` process, Slurm job or GPU job. Python/grep/sed for reading and counting is fine; scratch files only under <SP>/round3/S/.
- Token economy: stay under ~120k tokens.
- The other reviewers' reports are not available to you; do not look for them.

## Read first
The draft: `<SP>/round3/draft.md`.

## The record (W = /research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/conventions-dossiers)
- `W/docs/research/code-review-systems-survey-2026-09.md` (with "Revisited 2026-10-09") and `W/docs/research/open-code-review-comparison-2026-09.md` — the external systems (BitsAI, AutoCommenter, RovoDev, uReview, Bugbot, Codex reviewer, Anthropic Code Review and plugin, Qodo, CodeRabbit, Greptile, Semgrep, Tricorder/Infer, SWR-Bench, OCR).
- `W/docs/research/ceiling-residual-2026-10.md`, `W/docs/research/decompose-and-shrink-review-2026-10.md` (+ folder), `W/docs/research/conventions-dossiers-review-2026-10.md`.
- `W/results/pr_review_v5/probes/conventions-ceiling-2026-10-04/README.md` (stages F, G, H, D, Result 7), the ladder `W/results/pr_review_v5/probes/conventions-ladder-2026-10-08/README.md`, the places test `W/results/pr_review_v5/probes/conventions-places-2026-10-09/README.md`.
- `W/docs/plans/2026-10-01-beyond-the-solo-baseline.md`, `W/docs/plans/2026-10-03-after-structure.md`, `W/docs/todo/static-analysis-pass.md`, `W/docs/todo/lean-persistent-checker.md`, `W/results/pr_review_v5/probes/closer-battery-2026-09-26/README.md`, `W/docs/todo/selection-signal.md`, `W/docs/dead-ends.md`.
- External context from memory is allowed (do not browse): how deployed rule-checker systems are staged, calibrated and rolled out; ensemble/self-consistency methods; static analysis at diff time.

## Your task
- Build the strongest plan from A-E (and anything else the systems or the record suggest): which components to combine, in what architecture, with what volume control, and why that combination addresses the residual classes (instability; at the place but asked something else; execution; information outside the packet).
- Identify missing ideas the external systems use that the draft does not, and say whether the record supports trying them.
- The cheapest decisive sequence: what to run first so that each result either kills a component or justifies the next spend; reuse anything already on disk or running (the places test, the ladder, stage D's runs).
- The most recall the strongest plan could add on the dev held-out 12, with the factors behind the estimate.
- Where the steelman fails.

## Deliver, as your final message (≤ 1,400 words; it goes to the orchestrating session, not the user)
1. The strongest plan, one paragraph.
2. The components kept, changed, added and dropped, each with evidence.
3. The cheapest decisive sequence, each step with a pre-stated threshold and cost.
4. The recall ceiling estimate with its factors.
5. Where the steelman fails.
Report at the altitude the evidence supports; mark read versus inferred. The project's goal is issue recall.
