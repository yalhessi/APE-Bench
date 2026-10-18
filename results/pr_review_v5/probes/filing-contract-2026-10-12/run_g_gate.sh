#!/bin/bash
# Design G's sessions, unattended on `first` (README; the table's run_ds41_gate.sh pattern): start the
# DeepSeek server of serve_ds41.sbatch (with a 24 h limit), run probe_correct.py and probe_carry.py, run
# the smoke (amendment 1) and its health checks, and only if they hold, the three reps of the three sets,
# at most 30 sessions at once; stop on a run that keeps retrying; release the node.
# Usage: sbatch -p first -A first --mem=64G --time=40:00:00 -J filing-g \
#   -o /research/projects/proofedit/ya475/localmodel/logs/filing_g_%j.log --wrap "<this file>"
# Progress: /research/projects/proofedit/ya475/localmodel/logs/filing_g.status
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(git -C "$HERE" rev-parse --show-toplevel)
C=$ROOT/results/pr_review_v5/probes/conventions-ceiling-2026-10-04
LM=/research/projects/proofedit/ya475/localmodel
LOGS=$LM/logs
STATUS=$LOGS/filing_g.status
URL=http://127.0.0.1:8012/v1
RUNS=$ROOT/results/pr_review_v5/runs
say() { echo "$(date -Is) $*" >> "$STATUS"; }
release() { [ -n "$JOB" ] && { say "releasing the node: scancel $JOB"; scancel "$JOB"; }; }

say "filing-g gate started (job ${SLURM_JOB_ID:-none})"
( cd "$ROOT" && sha256sum -c --quiet "$C/context_apt.sha256" ) || { say "STOP: the apt context files are not the registered bytes"; exit 1; }
JOB=$(env $(env | awk -F= '/^SLURM_/ {print "-u " $1}') sbatch --parsable --time=24:00:00 "$LM/serve_ds41.sbatch") || { say "STOP: sbatch serve_ds41.sbatch failed"; exit 1; }
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
( cd "$LM/probes" && timeout 3600 "$LM/vllm-env/bin/python" probe_correct.py "$URL" local-deepseek > "$LOGS/probe_correct_filing_g_$JOB.out" 2>&1 )
rc=$?
say "probe_correct exit $rc: $(grep -E '^17x19|^gsm8k [0-9]+/20' "$LOGS/probe_correct_filing_g_$JOB.out" | tr '\n' ' ')"
[ $rc -eq 0 ] || { say "STOP: the server does not compute correctly"; release; exit 1; }
( cd "$LM/probes" && timeout 600 "$LM/vllm-env/bin/python" probe_carry.py "$URL" local-deepseek > "$LOGS/probe_carry_filing_g_$JOB.out" 2>&1 )
rc=$?
say "probe_carry exit $rc: $(tail -1 "$LOGS/probe_carry_filing_g_$JOB.out")"
[ $rc -eq 0 ] || { say "STOP: the server does not keep earlier thinking"; release; exit 1; }

declare -A PID SESS
running() { local n=0; for k in "${!PID[@]}"; do kill -0 "${PID[$k]}" 2>/dev/null && n=$((n + SESS[$k])); done; echo $n; }
check_retries() {
  for k in "${!PID[@]}"; do
    if kill -0 "${PID[$k]}" 2>/dev/null && [ "$(grep -c 'API call failed, retrying' "$LOGS/cli_$k.log")" -gt 20 ]; then
      say "STOP: $k is retrying (server unreachable?)"; for p in "${PID[@]}"; do kill "$p" 2>/dev/null; done; release; exit 1
    fi
  done
}
launch() {  # <set> <rep|smoke> <sessions>
  local name; [ "$2" = smoke ] && name=filing_g_smoke_$1 || name=filing_g_${1}_rep$2
  while [ $(( $(running) + $3 )) -gt 30 ]; do
    check_retries
    [ -z "$(squeue -j "$JOB" -h -o %T 2>/dev/null)" ] && { say "STOP: server job ended with runs queued"; exit 1; }
    sleep 60
  done
  "$HERE/run_g.sh" "$1" "$2" > "$LOGS/cli_$name.log" 2>&1 &
  PID[$name]=$!; SESS[$name]=$3
  say "run $name started ($3 sessions)"
}
wait_all() {
  while [ "$(running)" -gt 0 ]; do
    check_retries
    [ -z "$(squeue -j "$JOB" -h -o %T 2>/dev/null)" ] && { say "STOP: server job ended with runs alive"; exit 1; }
    sleep 60
  done
}

# The smoke and its health checks (amendment 1).
launch dev smoke 2; launch val smoke 1; launch post smoke 1
wait_all
( cd "$ROOT" && PYTHONPATH=$ROOT/src "$ROOT/ape/bin/python" "$HERE/smoke_check.py" filing_g_smoke_dev filing_g_smoke_val filing_g_smoke_post ) >> "$STATUS" 2>&1
if [ $? -ne 0 ]; then say "STOP: the smoke's health checks failed; read it by hand before anything else runs"; release; exit 1; fi
say "smoke healthy; the reps start"
PID=(); SESS=()
declare -A PID SESS

# The reps: the small sets first in each rep, so an early stop leaves whole reps of P14.
for rep in 1 2 3; do launch val "$rep" 8; launch post "$rep" 6; launch dev "$rep" 15; done
wait_all
for name in filing_g_val_rep{1,2,3} filing_g_post_rep{1,2,3} filing_g_dev_rep{1,2,3}; do
  status=$(grep -o '"completion_status": "[a-z_]*"' "$RUNS/$name/run_manifest.json" 2>/dev/null | cut -d'"' -f4)
  say "run $name: ${status:-no manifest}; $(grep -c 'completed with success' "$LOGS/cli_$name.log" 2>/dev/null) sessions ok, $(wc -l < "$RUNS/$name/findings.jsonl" 2>/dev/null || echo '?') findings"
done
release
say "filing-g gate finished"
