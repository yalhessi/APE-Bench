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
