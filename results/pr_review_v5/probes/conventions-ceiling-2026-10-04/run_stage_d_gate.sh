#!/bin/bash
# Stage D's unattended gate (pre-registered in this directory's README, 2026-10-08): DeepSeek-V4.1-Flash
# on `first` for the 18 runs, X (base), E (exact) and P (prec) on both of stage L's sets, three reps
# each. It starts the server (serve_ds41.sbatch, its defaults: the patched nightly, DSpark, a 1M
# context), runs probe_correct.py and probe_carry.py, then the runs, and releases the node.
# - Order is rep-major (rep 1 of every condition and set first), so a gate cut short leaves whole reps.
# - At most $INFLIGHT runs at once (default 3, at most 29 sessions): one dev rep of 15 sessions used
#   about half the server; kept thinking grows every prompt, so the KV pool, not the GPUs, is the limit.
# - The server job has an 8-hour limit. No run starts with under $MARGIN minutes left on it; when the
#   runs in flight are done the server is released and a new one started, at most $MAX_SERVERS in all.
#   An interrupted run resumes (`run_ds41.sh`: --resume), a complete one is skipped.
# - It stops and releases the node on a server traceback, a failed probe, or a run that keeps retrying.
# Usage (from any shell on first). 120 GB: with the server's 900 GB and one 100 GB job beside them the node
# (1,156 GB) still fits all three; 160 GB would make the server wait on memory as well as GPUs.
#   sbatch -p first -A first -c 12 --mem=120G --time=2-00:00:00 -J ds41-conv-gate \
#     -o /research/projects/proofedit/ya475/localmodel/logs/ds41_conv_gate_%j.log --wrap "<this file> [server job id]"
# Progress: /research/projects/proofedit/ya475/localmodel/logs/ds41_conv_gate.status
# No `set -u`: this bash (5.2.21) aborts on "${!A[@]}" of an empty associative array under it.
HERE=$(cd "$(dirname "$0")" && pwd)
# LM, RUN and RUNS are overridable only so the control flow can be dry-run with stubs.
LM=${LM:-/research/projects/proofedit/ya475/localmodel}
RUN=${RUN:-$HERE/run_ds41.sh}
RUNS=${RUNS:-$HERE/../../runs}
LOGS=$LM/logs
STATUS=$LOGS/ds41_conv_gate.status
URL=http://127.0.0.1:8012/v1
INFLIGHT=${INFLIGHT:-3}
MARGIN=${MARGIN:-60}
MAX_SERVERS=${MAX_SERVERS:-3}
JOB=${1:-}
servers=0
say() { echo "$(date -Is) $*" >> "$STATUS"; }
release() { [ -n "$JOB" ] && { say "releasing the node: scancel $JOB"; scancel "$JOB"; }; }
minutes_left() {  # of the server job's time limit: D-HH:MM:SS, HH:MM:SS or MM:SS
  squeue -j "$JOB" -h -o %L 2>/dev/null | awk -F'[-:]' '{ if (NF==4) print $1*1440+$2*60+$3; else if (NF==3) print $1*60+$2; else if (NF==2) print $1; else print 0 }'
}

QUEUE=()
for rep in 1 2 3; do for level in base exact prec; do for tag in val post; do QUEUE+=("$tag $level $rep"); done; done; done
declare -A PID TRIES

start_server() {
  if [ -z "$JOB" ]; then
    servers=$((servers + 1))
    if [ "$servers" -gt "$MAX_SERVERS" ]; then say "STOP: $MAX_SERVERS server starts used, ${#QUEUE[@]} runs left"; exit 1; fi
    # The gate is itself a job: its SLURM_* variables must not reach the server's submission.
    JOB=$(env $(env | awk -F= '/^SLURM_/ {print "-u " $1}') sbatch --parsable "$LM/serve_ds41.sbatch") || { say "STOP: sbatch serve_ds41.sbatch failed"; exit 1; }
    say "server job $JOB submitted (start $servers of $MAX_SERVERS)"
  fi
  local log=$LOGS/serve_ds41_$JOB.log
  while true; do
    state=$(squeue -j "$JOB" -h -o %T 2>/dev/null)
    if [ -z "$state" ]; then say "STOP: job $JOB is gone before serving (see $log)"; exit 1; fi
    if grep -q -E "core.py:[0-9]+\] Traceback|^Traceback" "$log" 2>/dev/null; then
      say "STOP: server traceback (see $log)"; release; exit 1
    fi
    if [ "$state" = RUNNING ] && curl -sf "$URL/models" >/dev/null 2>&1; then break; fi
    sleep 60
  done
  say "server $JOB up: $(grep -E 'download took|vllm|GPU KV cache size' "$log" | tail -3 | sed 's/.*\] //' | cut -c1-220 | tr '\n' ' ')"
  ( cd "$LM/probes" || exit 1
    timeout 3600 "$LM/vllm-env/bin/python" probe_correct.py "$URL" local-deepseek > "$LOGS/probe_correct_ds41_conv_$JOB.out" 2>&1 )
  rc=$?
  say "probe_correct exit $rc: $(grep -E '^17x19|^gsm8k [0-9]+/20' "$LOGS/probe_correct_ds41_conv_$JOB.out" | tr '\n' ' ')"
  if [ $rc -ne 0 ]; then say "STOP: the server does not compute correctly"; release; exit 1; fi
  ( cd "$LM/probes" || exit 1
    timeout 600 "$LM/vllm-env/bin/python" probe_carry.py "$URL" local-deepseek > "$LOGS/probe_carry_ds41_conv_$JOB.out" 2>&1 )
  rc=$?
  say "probe_carry exit $rc: $(tail -1 "$LOGS/probe_carry_ds41_conv_$JOB.out")"
  if [ $rc -ne 0 ]; then say "STOP: the server does not keep earlier thinking"; release; exit 1; fi
}

stop_runs() { for k in "${!PID[@]}"; do kill "${PID[$k]}" 2>/dev/null; done; }

finished() {  # one line for a run whose process has exited
  local tag=$1 level=$2 rep=$3 name=iter_ds41_conv_$1_$2_rep$3 log=$LOGS/cli_iter_ds41_conv_$1_$2_rep$3.log
  local status
  status=$(grep -o '"completion_status": "[a-z_]*"' "$RUNS/$name/run_manifest.json" 2>/dev/null | cut -d'"' -f4)
  say "run $name: ${status:-no manifest}; $(grep -c 'completed with success' "$log") sessions ok, $(grep -c failed_error "$log") failed; $(wc -l < "$RUNS/$name/findings.jsonl" 2>/dev/null || echo '?') findings"
  [ "$status" = complete ]
}

say "stage D gate started (job ${SLURM_JOB_ID:-none}); ${#QUEUE[@]} runs, $INFLIGHT at a time"
( cd "$HERE/../../../.." && sha256sum -c --quiet "$HERE/context_prec.sha256" ) || { say "STOP: the prec context files are not the pre-registered bytes"; exit 1; }
start_server
while [ ${#QUEUE[@]} -gt 0 ] || [ ${#PID[@]} -gt 0 ]; do
  # Runs that have exited: requeue an incomplete one once (it resumes), else drop it.
  for k in "${!PID[@]}"; do
    if ! kill -0 "${PID[$k]}" 2>/dev/null; then
      unset "PID[$k]"
      set -- $k
      if ! finished "$@"; then
        TRIES[$k]=$(( ${TRIES[$k]:-1} + 1 ))
        if [ "${TRIES[$k]}" -le 2 ]; then QUEUE=("$k" "${QUEUE[@]}"); say "requeued $k (attempt ${TRIES[$k]})"; fi
      fi
    fi
  done
  if [ -z "$(squeue -j "$JOB" -h -o %T 2>/dev/null)" ]; then
    say "server job $JOB ended with ${#PID[@]} runs in flight; stopping them to resume on the next server"
    for k in "${!PID[@]}"; do QUEUE=("$k" "${QUEUE[@]}"); done
    stop_runs; sleep 30; PID=(); JOB=""
    [ ${#QUEUE[@]} -gt 0 ] && start_server
    continue
  fi
  for k in "${!PID[@]}"; do
    log=$LOGS/cli_iter_ds41_conv_$(echo "$k" | awk '{print $1"_"$2"_rep"$3}').log
    if [ "$(grep -c 'API call failed, retrying' "$log" 2>/dev/null)" -gt 20 ]; then
      say "STOP: $k is retrying (server unreachable?)"; stop_runs; release; exit 1
    fi
  done
  left=$(minutes_left)
  if [ ${#QUEUE[@]} -gt 0 ] && [ "${left:-0}" -lt "$MARGIN" ]; then
    if [ ${#PID[@]} -eq 0 ]; then
      say "server $JOB has ${left} min left; releasing it for a fresh one"; release; sleep 30; JOB=""; start_server
    fi
  elif [ ${#QUEUE[@]} -gt 0 ] && [ ${#PID[@]} -lt "$INFLIGHT" ]; then
    k=${QUEUE[0]}; QUEUE=("${QUEUE[@]:1}")
    set -- $k
    say "run iter_ds41_conv_$1_$2_rep$3 starting (${left} min left on $JOB)"
    "$RUN" "$1" "$2" "$3" >> "$LOGS/cli_iter_ds41_conv_$1_$2_rep$3.log" 2>&1 &
    PID[$k]=$!
    continue
  fi
  sleep 30
done
say "all runs done"
release
say "stage D gate finished"
