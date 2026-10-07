#!/bin/bash
# Continuation of run_ds41_gate.sh, which was paused with SIGSTOP during rep 1 (2026-10-07 08:0x).
# One rep took ~2.5 h (35 tok/s a session, 92% of it thinking), so four reps in sequence would not fit the
# server job's 8 h; the server had room in its batch (KV cache 15% used at 12 sessions). So the three reps
# left run side by side here while rep 1 finishes, and each is judged as it finishes.
# Usage (as a step of the paused gate job, so it shares that job's memory limit):
#   srun --jobid=<gate job> --overlap -n1 run_ds41_parallel.sh <server job> <rep 1 cli pid> <gate job>
# Progress: logs/ds41_gate.status, as before.
set -u
JOB=${1:?server job id}; REP1_PID=${2:?rep 1 cli pid}; GATE_JOB=${3:?gate job id}
W=/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/local-model-unlock
LM=/research/projects/proofedit/ya475/localmodel
LOGS=$LM/logs
STATUS=$LOGS/ds41_gate.status
say() { echo "$(date -Is) $*" >> "$STATUS"; }
# rep 1's cli is a child of the stopped gate shell, which cannot reap it: once it exits it stays a
# zombie, and `kill -0` still succeeds on a zombie.
alive() { [ -d "/proc/$1" ] && ! grep -q '^State:[[:space:]]*Z' "/proc/$1/status" 2>/dev/null; }

judge_rep() {
  local R=$1
  say "run $R: $(grep -h 'completion_status=' "$LOGS/cli_$R.log" | sed 's/.*completion_status/completion_status/' | cut -c1-60); $(grep -c 'completed with success' "$LOGS/cli_$R.log") sessions ok, $(grep -c failed_error "$LOGS/cli_$R.log") failed"
  (set -a; . ~/.config/secrets/env.zsh; set +a
   PYTHONPATH=$W/src timeout 2400 ape/bin/python -m src.mathlib_review.review.cli judge \
     --config configs/pr_review_v5_medium_heldout_judge.yaml --of "$R" --execute > "$LOGS/judge_$R.log" 2>&1)
  local A score
  A=$(echo "$R" | tr '_' '-')
  score=$(PYTHONPATH=$W/src ape/bin/python -m src.mathlib_review.review.cli report score \
    --audit "results/pr_review_v5/audits/$A" --run "$R" 2>/dev/null | ape/bin/python -c "
import json, sys
def find(o, k):
    if isinstance(o, dict):
        if k in o: return o[k]
        for v in o.values():
            r = find(v, k)
            if r is not None: return r
d = json.load(sys.stdin); p = find(d, 'pre_publication'); e = find(d, 'silent_pr_emission')
print(f\"{p['issue_hits']} of 23 obligations, {p['resolution_hits']} resolutions, control findings {e['candidates']}\")" 2>&1)
  say "judged $R: $score (judge retries $(grep -c 'API call failed, retrying' "$LOGS/judge_$R.log"))"
}

cd "$W" || exit 1
declare -A PID
PID[iter_ds41_contract2_high_rep1]=$REP1_PID
for spec in high:2 high:3 none:1; do
  effort=${spec%%:*}; n=${spec##*:}
  R=iter_ds41_contract2_${effort}_rep$n
  say "run $R starting (in parallel)"
  PYTHONPATH=$W/src ape/bin/python -m src.mathlib_review.review.cli run \
    --config configs/pr_review_v5_dev_medium_local_ds41_contract2.yaml --run-name "$R" \
    --set llm_config.reasoning_effort="$effort" --execute > "$LOGS/cli_$R.log" 2>&1 &
  PID[$R]=$!
done
say "parallel continuation: pids $(for R in "${!PID[@]}"; do printf '%s=%s ' "$R" "${PID[$R]}"; done)"

pending=(iter_ds41_contract2_high_rep1 iter_ds41_contract2_high_rep2 iter_ds41_contract2_high_rep3 iter_ds41_contract2_none_rep1)
while [ ${#pending[@]} -gt 0 ]; do
  if [ -z "$(squeue -j "$JOB" -h -o %T 2>/dev/null)" ]; then
    say "STOP: server job ended with ${pending[*]} unfinished"
    for R in "${pending[@]}"; do alive "${PID[$R]}" && kill "${PID[$R]}"; done
    exit 1
  fi
  for R in "${pending[@]}"; do
    if [ "$(grep -c 'API call failed, retrying' "$LOGS/cli_$R.log")" -gt 20 ]; then
      say "STOP: $R is retrying (server unreachable?)"
      for P in "${pending[@]}"; do alive "${PID[$P]}" && kill "${PID[$P]}"; done
      scancel "$JOB"; exit 1
    fi
  done
  next=()
  for R in "${pending[@]}"; do
    if alive "${PID[$R]}"; then next+=("$R"); else judge_rep "$R"; fi
  done
  pending=("${next[@]}")
  [ ${#pending[@]} -gt 0 ] && sleep 30
done

PYTHONPATH=$W/src ape/bin/python results/pr_review_v5/probes/local-unlock-2026-10-03/screen.py \
  | grep -E "^run|^ds41|^base" >> "$STATUS"
say "gate finished; releasing the node: scancel $JOB, then the paused gate job $GATE_JOB"
scancel "$JOB"
scancel "$GATE_JOB"
