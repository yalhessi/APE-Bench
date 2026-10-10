#!/bin/bash
# The DeepSeek cells of the one reviewer table (docs/plans/2026-10-10-one-reviewer-table.md, step 5),
# unattended on `first`: AP on P14's other four PRs (the apt level, three reps a set), and on the dev
# release's 15 PRs both solo and AP, three reps each, in one server job on serve_ds41.sbatch's defaults
# (review finding 4). It starts the server, runs probe_correct.py and probe_carry.py, runs the twelve
# runs with at most 30 sessions at once (stage D's measured ceiling was 29), stops on a run that keeps
# retrying, and releases the node.
# Usage: sbatch -p first -A first --mem=64G --time=30:00:00 -J ds41-table \
#   -o /research/projects/proofedit/ya475/localmodel/logs/ds41_table_%j.log --wrap "<this file>"
# Progress: /research/projects/proofedit/ya475/localmodel/logs/ds41_table.status
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(git -C "$HERE" rev-parse --show-toplevel)
P=$ROOT/results/pr_review_v5/probes/conventions-ceiling-2026-10-04
LM=/research/projects/proofedit/ya475/localmodel
LOGS=$LM/logs
STATUS=$LOGS/ds41_table.status
URL=http://127.0.0.1:8012/v1
RUNS=$ROOT/results/pr_review_v5/runs
say() { echo "$(date -Is) $*" >> "$STATUS"; }
release() { [ -n "$JOB" ] && { say "releasing the node: scancel $JOB"; scancel "$JOB"; }; }

say "table gate started (job ${SLURM_JOB_ID:-none})"
( cd "$ROOT" && sha256sum -c --quiet "$P/context_apt.sha256" ) || { say "STOP: the apt context files are not the committed bytes"; exit 1; }
JOB=$(env $(env | awk -F= '/^SLURM_/ {print "-u " $1}') sbatch --parsable "$LM/serve_ds41.sbatch") || { say "STOP: sbatch serve_ds41.sbatch failed"; exit 1; }
say "server job $JOB submitted"
log=$LOGS/serve_ds41_$JOB.log
while true; do
  state=$(squeue -j "$JOB" -h -o %T 2>/dev/null)
  if [ -z "$state" ]; then say "STOP: job $JOB is gone before serving (see $log)"; exit 1; fi
  if grep -q -E "core.py:[0-9]+\] Traceback|^Traceback" "$log" 2>/dev/null; then say "STOP: server traceback (see $log)"; release; exit 1; fi
  if [ "$state" = RUNNING ] && curl -sf "$URL/models" >/dev/null 2>&1; then break; fi
  sleep 60
done
say "server $JOB up"
( cd "$LM/probes" && timeout 3600 "$LM/vllm-env/bin/python" probe_correct.py "$URL" local-deepseek > "$LOGS/probe_correct_ds41_table_$JOB.out" 2>&1 )
rc=$?
say "probe_correct exit $rc: $(grep -E '^17x19|^gsm8k [0-9]+/20' "$LOGS/probe_correct_ds41_table_$JOB.out" | tr '\n' ' ')"
[ $rc -eq 0 ] || { say "STOP: the server does not compute correctly"; release; exit 1; }
( cd "$LM/probes" && timeout 600 "$LM/vllm-env/bin/python" probe_carry.py "$URL" local-deepseek > "$LOGS/probe_carry_ds41_table_$JOB.out" 2>&1 )
rc=$?
say "probe_carry exit $rc: $(tail -1 "$LOGS/probe_carry_ds41_table_$JOB.out")"
[ $rc -eq 0 ] || { say "STOP: the server does not keep earlier thinking"; release; exit 1; }

# <set> <level> <rep> <PRs or -> <sessions>, in this order: the small P14 runs first, then dev
# solo and AP alternating, so an early stop leaves pairs.
queue=()
for rep in 1 2 3; do queue+=("val apt $rep [26755,36822] 2" "post apt $rep [43024,43192] 2"); done
for rep in 1 2 3; do queue+=("dev base $rep - 15" "dev apt $rep - 15"); done
declare -A PID SESS
running() { local n=0; for k in "${!PID[@]}"; do kill -0 "${PID[$k]}" 2>/dev/null && n=$((n + SESS[$k])); done; echo $n; }
check_retries() {
  for k in "${!PID[@]}"; do
    if kill -0 "${PID[$k]}" 2>/dev/null && [ "$(grep -c 'API call failed, retrying' "$LOGS/cli_$k.log")" -gt 20 ]; then
      say "STOP: $k is retrying (server unreachable?)"; for p in "${PID[@]}"; do kill "$p" 2>/dev/null; done; release; exit 1
    fi
  done
}
for item in "${queue[@]}"; do
  read -r tag level rep prs n <<< "$item"
  name=iter_ds41_conv_${tag}_${level}_rep$rep
  while [ $(( $(running) + n )) -gt 30 ]; do
    check_retries
    [ -z "$(squeue -j "$JOB" -h -o %T 2>/dev/null)" ] && { say "STOP: server job ended with runs queued"; exit 1; }
    sleep 60
  done
  if [ "$prs" = - ]; then
    "$P/run_ds41.sh" "$tag" "$level" "$rep" > "$LOGS/cli_$name.log" 2>&1 &
  else
    PRS=$prs "$P/run_ds41.sh" "$tag" "$level" "$rep" > "$LOGS/cli_$name.log" 2>&1 &
  fi
  PID[$name]=$!; SESS[$name]=$n
  say "run $name started ($n sessions)"
done
while [ "$(running)" -gt 0 ]; do
  check_retries
  [ -z "$(squeue -j "$JOB" -h -o %T 2>/dev/null)" ] && { say "STOP: server job ended with runs alive"; exit 1; }
  sleep 60
done
for name in "${!PID[@]}"; do
  status=$(grep -o '"completion_status": "[a-z_]*"' "$RUNS/$name/run_manifest.json" 2>/dev/null | cut -d'"' -f4)
  say "run $name: ${status:-no manifest}; $(grep -c 'completed with success' "$LOGS/cli_$name.log") sessions ok, $(wc -l < "$RUNS/$name/findings.jsonl" 2>/dev/null || echo '?') findings"
done
release
say "table gate finished"
