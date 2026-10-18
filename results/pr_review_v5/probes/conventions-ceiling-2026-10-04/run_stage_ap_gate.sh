#!/bin/bash
# Stage AP's unattended gate (README, "Stage AP", pre-registered 2026-10-09). DeepSeek-V4.1-Flash on
# `first` for six runs: the ap level on both sets, three reps. It starts the server (serve_ds41.sbatch
# defaults), runs probe_correct.py and probe_carry.py, starts all six runs at once (30 sessions, stage
# D's measured ceiling of 29 concurrent), stops on a run that keeps retrying, and releases the node.
# Usage: sbatch -p first -A first --mem=120G --time=12:00:00 -J ds41-ap-gate \
#   -o /research/projects/proofedit/ya475/localmodel/logs/ds41_ap_gate_%j.log --wrap "<this file>"
# Progress: /research/projects/proofedit/ya475/localmodel/logs/ds41_ap_gate.status
HERE=$(cd "$(dirname "$0")" && pwd)
LM=/research/projects/proofedit/ya475/localmodel
LOGS=$LM/logs
STATUS=$LOGS/ds41_ap_gate.status
URL=http://127.0.0.1:8012/v1
RUNS=$HERE/../../runs
say() { echo "$(date -Is) $*" >> "$STATUS"; }
release() { [ -n "$JOB" ] && { say "releasing the node: scancel $JOB"; scancel "$JOB"; }; }

say "stage AP gate started (job ${SLURM_JOB_ID:-none})"
( cd "$HERE/../../../.." && sha256sum -c --quiet "$HERE/context_ap.sha256" ) || { say "STOP: the ap context files are not the pre-registered bytes"; exit 1; }
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
( cd "$LM/probes" && timeout 3600 "$LM/vllm-env/bin/python" probe_correct.py "$URL" local-deepseek > "$LOGS/probe_correct_ds41_ap_$JOB.out" 2>&1 )
rc=$?
say "probe_correct exit $rc: $(grep -E '^17x19|^gsm8k [0-9]+/20' "$LOGS/probe_correct_ds41_ap_$JOB.out" | tr '\n' ' ')"
[ $rc -eq 0 ] || { say "STOP: the server does not compute correctly"; release; exit 1; }
( cd "$LM/probes" && timeout 600 "$LM/vllm-env/bin/python" probe_carry.py "$URL" local-deepseek > "$LOGS/probe_carry_ds41_ap_$JOB.out" 2>&1 )
rc=$?
say "probe_carry exit $rc: $(tail -1 "$LOGS/probe_carry_ds41_ap_$JOB.out")"
[ $rc -eq 0 ] || { say "STOP: the server does not keep earlier thinking"; release; exit 1; }

declare -A PID
for rep in 1 2 3; do
  for tag in val post; do
    name=iter_ds41_conv_${tag}_ap_rep$rep
    "$HERE/run_ds41.sh" "$tag" ap "$rep" > "$LOGS/cli_$name.log" 2>&1 &
    PID[$name]=$!
    say "run $name started"
  done
done
while true; do
  alive=0
  for name in "${!PID[@]}"; do
    if kill -0 "${PID[$name]}" 2>/dev/null; then
      alive=$((alive + 1))
      if [ "$(grep -c 'API call failed, retrying' "$LOGS/cli_$name.log")" -gt 20 ]; then
        say "STOP: $name is retrying (server unreachable?)"; for p in "${PID[@]}"; do kill "$p" 2>/dev/null; done; release; exit 1
      fi
    fi
  done
  [ "$alive" -eq 0 ] && break
  if [ -z "$(squeue -j "$JOB" -h -o %T 2>/dev/null)" ]; then say "STOP: server job ended with $alive runs alive"; exit 1; fi
  sleep 60
done
for name in "${!PID[@]}"; do
  status=$(grep -o '"completion_status": "[a-z_]*"' "$RUNS/$name/run_manifest.json" 2>/dev/null | cut -d'"' -f4)
  say "run $name: ${status:-no manifest}; $(grep -c 'completed with success' "$LOGS/cli_$name.log") sessions ok, $(grep -c failed_error "$LOGS/cli_$name.log") failed; $(wc -l < "$RUNS/$name/findings.jsonl" 2>/dev/null || echo '?') findings"
done
release
say "stage AP gate finished"
