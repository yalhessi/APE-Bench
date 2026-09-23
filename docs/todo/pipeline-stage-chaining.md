# Piping one stage's results into the next, instead of re-deriving them by hand

**Status** — **closed 2026-09-21** on branch `stage-provenance`. See the amendment at the end: the user chose a declared stage graph over a bare typed hand-off, and the constraint below is met rather than waived
**Cost** — code; no model spend to build, and it removes spend caused by mis-chained stages
**Owner question** — what is the typed hand-off between a finished stage and the one that reads it?

## Motivating example

A v5 experiment is four processes today, chained by a run name typed correctly four times:

```
cli run    --config <cfg> --run-name X --execute      # the reviewer
cli judge  --config <j>   --of X       --execute      # scoring, a separate process
cli replay --config <r>   --of X       --execute      # re-decide, a third
cli report replay --run <replay run> --against <null> # reading it, a fourth
```

`judge --of X` exists *because* the three paths it derives (`candidates`, `out_dir`,
`run_name`) were once three free-form strings and disagreed: a judge scored rep1's findings
under rep2's name. That fix was made for one stage and never generalised, and replay is now the
third stage to re-implement "find the previous stage's artifacts and check they belong together".

The concrete cost, measured while building replay (2026-09-15/16):

- **Selection logic lives in scratch scripts.** Choosing the 45 sessions for the planned
  diagnostic — specialist invocations whose work unit carries a *required gold* change and that
  abstained — took an ad-hoc join across `arm_pool.jsonl`, `arm_responses.jsonl`, the execution
  index and `gold/judgments.jsonl`, written in a scratchpad, untested, and thrown away. It is
  exactly the join `judge` and `bench` each already do differently. A selector that a later run
  cannot name is a selector nobody can reproduce.
- **A directive did not survive the hop.** `TaskOrchestrator` rebuilt each job's `task_data`
  from `task.data.model_dump()`, so every key the task model does not declare was dropped
  between stages: `execution_limits` never reached a worker (v5 arms ran at the nested
  `sample_max_cost` of $1.00, not the run's $0.30) and `session_replay` turned a replay into an
  ordinary run that still submitted (`ac396ee`). Both are the same defect: state passed between
  stages by convention rather than by a typed carrier that refuses to lose a field.
- **Artifacts are found by convention, and the convention breaks.** `cli trajectory` returns 0
  arm invocations for all three `rel050` reps because the index holds absolute paths into a
  deleted worktree; `arm_pool.jsonl` was invisible from every worktree until the setup script
  started linking it (2026-09-16); `rel050`'s pools are simply gone
  (`docs/todo/operational-floor.md` §5).

Replay sharpens the case because it is the first stage that wants to run *after the judge*: the
sessions worth re-deciding are the ones the judge says were missed, and there is no way to say
"replay the arm sessions behind the obligations this audit scored as missed" without hand-joining
audit output to run artifacts again.

## What would close it

One named, tested hand-off: a stage declares what it consumes (a finished run, optionally its
audit) and what it emits, so that

* a selector is a named thing with a test (`--select missed-obligations`, `--select
  gold-site-abstentions`) rather than a scratch join, and the selection is recorded in the
  consuming run's sealed plan;
* the chain is checkable before it spends — the plan names its upstream run, its upstream
  audit, and the release all three agree on, the way `judge --of` already checks its three;
* a key one stage attaches survives to the stage that reads it, or the hop refuses.

Not a workflow engine: the smallest version is a typed `StageInput` the three existing
`--of`-style commands share, plus selectors that live in `src/mathlib_review/` with tests.

## Risk

The pipeline is four commands because the stages really are separable, and they are separable
because each writes immutable artifacts under one run name. A chaining layer that hides which
artifacts a stage read would remove the property that makes a v5 run reproducible at all. The
hand-off must be *named provenance*, not a scheduler.

## Closed, 2026-09-21 — and the risk above is the reason it took the shape it did

`StageInput` (`run_state.py`) is the typed hand-off: a stage names the artifacts it consumes,
they are resolved and hashed, the run's state is checked, and every refusal is stated once
rather than per caller. `judge`, `replay` and the reports read through it. Selectors are named
and tested (`--select gold-site-abstentions`), sealed into the replay's plan, and the numbers
differ from the scratch join they replace -- 58 sessions where it chose 45, because it filtered
on required gold changes and this filters on gold sites. That difference is the argument, not a
counterexample: nothing could previously say which question had been asked.

Each stage now appends a `StageRecord` to `stages.jsonl` in the run's own directory: consumed
digests, produced digests, identity, transition, forensic. That is what makes the chain
checkable after the fact, and it is what `state_of` reads to say a run was judged.

**The user asked for more than a hand-off** (2026-09-21): an arbitrary number of downstream
stages, A → B → C and A → {B, C}, each with its own runtime config, starting as soon as
capacity and inputs allow. `cli pipeline` is that, and the risk this file states -- *"a chaining
layer that hides which artifacts a stage read would remove the property that makes a v5 run
reproducible"* -- is met three ways rather than waived:

* every node runs the same code path its own command runs, under its own config, and writes
  the same artifacts and the same ledger row either way. A judge node derives its audit from
  `derive_from_run(root, node)` because that is what `judge --of` does, and then passes the
  judge's own `assert_paths_agree`. A test asserts the adapters contain no path arithmetic of
  their own;
* what a stage read is still recorded *by the stage*, through `StageInput`, so the chain is
  checkable from the rows and not from the graph;
* the graph is sealed into the root run as `pipeline.json` before the first stage starts.

So the ordering layer adds when a stage may start, and nothing else. It is a scheduler over
*commands*, which is what was asked for, rather than over artifacts, which is what this file
warned against.

What is **not** done and is now its own entry: per-item streaming, where PR X is judged while
PR Y is still under review. It needs per-PR finalization, and `finalize` is whole-run.
See [pipeline-streaming.md](pipeline-streaming.md).
