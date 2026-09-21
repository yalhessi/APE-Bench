# Piping one stage's results into the next, instead of re-deriving them by hand

**Status** — open, written 2026-09-21 from what building decision-turn replay cost
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
