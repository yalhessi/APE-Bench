# One validation run and one reasoning twin, unattended (2026-09-25)

Launched by `launch.sh` in tmux session `val_probe`; progress in `launch.log`, the last stage in
`status.txt`. Written before either run started. The user's constraints: one run on validation
PRs, reasoning on is worth testing, nothing else spent.

## What runs

1. **The reasoning twin.** `configs/pr_review_v5_verdicts_fanout4.yaml` with
   `llm_config.reasoning_effort=medium`, against its paid control `pr5_V3_contract_fanout4_rep1`
   (3 of 10 obligations, 0 control-PR findings, $5.60). Same four PRs, prompts, model; judged v9 /
   `gpt_5_mini` with the control's scope.
   - **Why medium:** the free check (`reasoning_check.json`, and a second check on a realistic
     dossier prompt) found the default and `medium` produce 0 reasoning tokens on a trivial
     prompt, `medium` produces 2,016 on a review prompt at 2.4× the cost per call, and `high`
     overruns an 8,000-token reply. `medium` is the level that reasons when the task warrants it.
   - **Caps, deliberately changed and in the run name:** per-job cap $0.17 → $0.30, so a job
     that reasons is not paused mid-answer; run ceiling 140 × $0.30 = $42 (the runner refuses a
     smaller one). Expected ~$14 (2.4 × the control's $5.60).
   - **Reading rule:** through if ≥ 5 of 10 obligations with ≤ 1 control-PR finding (the rule
     the unified run failed at 3 of 10). One rep: a difference of one obligation is noise;
     anything under 5 is "not distinguishable at one rep".
2. **The validation baseline.** `pr5_val_small12_lead_rep1`: the current pipeline as configured
   (lead mode, ten arms, reasoning off) on small12, after its 12 reviewed workspaces are built.
   Worst case $24.05 under a $25 cap; the held-out twelve billed ~$7 a rep at this size.
   - **Why the baseline and not reasoning-on:** a validation number with reasoning on and no
     reasoning-off pair could not be attributed; the twin attributes reasoning cheaply, and every
     later comparison needs this baseline. If the twin is through, the reasoning-on validation
     run is the next spend, with the lead-mode caps scaled the same way.
   - **How it is read (next session, no spend):** the run's `findings.jsonl` (every channel)
     matched by two blind readers, with `results/pr_review_v5/probes/facet-brief-2026-09-25/
     match/matcher_rubric.md`, against small12's round-1 asks (31 asks on 9 PRs; 26185 and 34935
     have none and are the controls). Report the pair: asks reached, and findings per PR on the
     two no-ask PRs. No gold exists for these PRs; this is ask-level.

## Ceilings and expectations

Ceilings: $42 + $0.30 + $25. Expected: about $14 + $0.30 + $7-10.

## What each stage leaves

`twin_plan.log`, `twin_run.log`, `twin_judge.log`, `build_base.log`, `build_reviewed.log`,
`val_plan.log`, `val_run.log`. The runs land under `results/pr_review_v5/runs/<run_name>/` and
the twin's audit under `results/pr_review_v5/audits/`. If `status.txt` says the validation plan
was refused, the builds did not finish; re-run `prebuild --reviewed --execute` on the small12
config and then the last two commands of `launch.sh` by hand.

## Result 1: the reasoning twin (2026-09-26)

| | control `pr5_V3_contract_fanout4_rep1` | twin `…_medium_cap030_rep1` |
|---|---|---|
| obligations hit, of 10 | 3 | **2** |
| resolution hits | 2 | 1 |
| findings | 77 | 42 |
| findings on the control PR 33315 | 0 | **2** |
| jobs completed / paused at the cap | 139 / 1 | **111 / 29** |
| billed | $5.60 | **$21.39** |

**Not through** by the rule (≥ 5 of 10, ≤ 1 control finding). But it is not a clean negative
either, and the reason is on the table:

- **The cap deleted the hit.** The one obligation the control has and the twin lacks is the
  33337 rename (`9d9ed5ad`), and the twin's naming job on that unit
  (`wu:1f9cf7865fe0948dfc6e47f8#naming`) is one of the 29 jobs the $0.30 cap paused. Paused jobs
  lose their answers. Among obligations whose arm did run, the twin matched the control
  (`issue_recall_reachable` 0.33 for both).
- **Reasoning at `medium` costs 3.8× per job**, not the 2.4× one call suggested: agentic sessions
  reason at every turn. A cap that lets every job finish is about $0.60 a job and an $84
  ceiling for these 140 jobs, roughly $50 expected. That is the price of a fair single rep, and
  it is not affordable now.
- **Two findings on the control PR** against the control's zero, at 42 findings against 77. The
  paused jobs make the volume incomparable, but control emission is not.

**Reading.** On this evidence reasoning at `medium` neither helps nor hurts recall where the arm
ran, costs about four times as much, and slightly raises control emission. It is not the cheap
lever the record's "every run had reasoning off" suggested it might be. A fair test needs the
higher cap, three reps, and about $150; it is parked, with these numbers, unless something else
argues for it.

Judged with `allow_partial: true`, the only way to judge a run that closed partial; the judge
otherwise refuses it, which is why `launch.sh`'s judge step failed. Audit:
`results/pr_review_v5/audits/pr5-V3r-contract-fanout4-medium-cap030-rep1/`.

## The validation chain, relaunched (2026-09-26, `launch2.sh`, tmux `val_probe2`)

`launch.sh`'s chain failed on two things it did not know:
- **A reviewed build needs the base restored from its snapshot into `workspaces/<sha>` first.**
  The prebuild planner counted the 11 bases as available; the builder then refused all 11 in
  three seconds: "base workspace … is not built … build the base commit first". The toolbox hit
  the same step (`e30be07`). `restore_bases.py` restores them; the prebuild follows.
- **PR 30714's base fails inside `lake build`** after a successful `lake exe cache get`:
  "no such file or directory" replaying dependency modules (`ImportGraph`, `Qq`). Not debugged.
  The run is the **other 11** of small12, named `pr5_val_small12_minus30714_lead_rep1`; its two
  no-ask PRs (26185, 34935) are still in it. The reading rule is unchanged.

First launch of `launch2.sh` died on an import path (`restore_bases.py` runs as a file, so the
repo root must be on `PYTHONPATH`); `launch2.attempt1.log` is that attempt. The second is live.
