#!/usr/bin/env bash
# Unattended: the reasoning twin on the four fanout PRs, then the builds and the one validation
# run on small12. Started in tmux because the launching session disconnects. Each chain is gated
# stage by stage; the two chains (twin, validation) are independent.
#   tmux new-session -d -s val_probe "bash results/pr_review_v5/probes/val-small12-2026-09-25/launch.sh"
#   tail -f results/pr_review_v5/probes/val-small12-2026-09-25/launch.log
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../../.." && pwd)"
cd "$REPO"
source ~/.config/secrets/env.zsh
export PYTHONPATH="$REPO/src" PATH="/research/projects/proofedit/ya475/.elan/bin:$PATH"
source "$HERE/params.env"
LOG="$HERE/launch.log"; STATUS="$HERE/status.txt"
R="ape/bin/python -m src.mathlib_review.review.cli"
log() { echo "$(date '+%F %T') $*" | tee -a "$LOG"; echo "$*" > "$STATUS"; }
[ -n "${OPENAI_API_KEY:-}" ] || { log "ABORT: OPENAI_API_KEY is not set"; exit 2; }
log "start: twin effort=$TWIN_EFFORT job_cap=$TWIN_JOB_CAP run_cap=$TWIN_RUN_CAP; validation run=$VAL_RUN_NAME"

# ---- chain 1: the reasoning twin; matched control pr5_V3_contract_fanout4_rep1 is already paid ----
TWIN="pr5_V3r_contract_fanout4_${TWIN_EFFORT}_cap$(echo $TWIN_JOB_CAP | tr -d '.')_rep1"
SETS="--set llm_config.reasoning_effort=$TWIN_EFFORT --set dataset.standard_budget_cap=$TWIN_JOB_CAP --set dataset.run_total_cost_cap=$TWIN_RUN_CAP"
log "twin: plan $TWIN"
if $R plan --config configs/pr_review_v5_verdicts_fanout4.yaml --run-name "$TWIN" $SETS >> "$HERE/twin_plan.log" 2>&1; then
  log "twin: run $TWIN"
  $R run --config configs/pr_review_v5_verdicts_fanout4.yaml --run-name "$TWIN" $SETS --execute >> "$HERE/twin_run.log" 2>&1
  RC=$?
  log "twin: run exit $RC; completed: $(grep -c 'completed with success' "$HERE/twin_run.log"); retry warnings: $(grep -c 'API call failed, retrying' "$HERE/twin_run.log")"
  if [ "$RC" = "0" ]; then
    log "twin: judge"
    $R judge --config configs/pr_review_v5_judge.yaml --of "$TWIN" --set "dataset.pr_numbers=[33145,33337,33421]" --set "dataset.control_pr_numbers=[33315]" --execute >> "$HERE/twin_judge.log" 2>&1
    log "twin: judge exit $?"
  fi
else
  log "twin: plan refused; see twin_plan.log. Twin skipped."
fi

# ---- chain 2: builds after the twin (a reviewed build competes with a live run on this NFS), then the validation baseline ----
log "build: base workspace for PR 30714's commit"
ape/bin/python -m ape.toolkits.execute.lean.build --input_file "$HERE/base_build_rows.jsonl" --num_processes 1 >> "$HERE/build_base.log" 2>&1
log "build: base exit $?"
log "build: reviewed workspaces for small12"
ape/bin/python -m src.mathlib_review.release.prebuild --reviewed --execute --config configs/pr_review_v5_val_2025_06_2026_03_v1_small12.yaml >> "$HERE/build_reviewed.log" 2>&1
log "build: reviewed exit $?"
log "validation: plan $VAL_RUN_NAME"
if $R plan --config configs/pr_review_v5_val_2025_06_2026_03_v1_small12.yaml --run-name "$VAL_RUN_NAME" >> "$HERE/val_plan.log" 2>&1; then
  log "validation: run $VAL_RUN_NAME"
  $R run --config configs/pr_review_v5_val_2025_06_2026_03_v1_small12.yaml --run-name "$VAL_RUN_NAME" --execute >> "$HERE/val_run.log" 2>&1
  log "validation: run exit $?; completed: $(grep -c 'completed with success' "$HERE/val_run.log"); retry warnings: $(grep -c 'API call failed, retrying' "$HERE/val_run.log")"
else
  log "validation: plan refused (workspaces unbuilt?); see val_plan.log. NOT run."
fi
log "DONE"
