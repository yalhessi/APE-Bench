#!/bin/bash
# The places test's unattended run (README here, pre-registered 2026-10-09): DeepSeek-V4.1-Flash on
# `first`. It starts the server (serve_ds41.sbatch with its defaults, as stage D's gate does), waits for
# it, runs probe_correct.py and probe_carry.py, runs `places.py run`, and releases the node. It stops
# and releases the node on a server traceback or a failed probe. `places.py run` resumes: rerunning
# this script after a stop sends only the calls not yet answered.
# Usage (any shell that can sbatch; the server binds to localhost, so this must run on first):
#   sbatch -p first -A first --mem=8G --time=12:00:00 -J ds41-places \
#     -o /research/projects/proofedit/ya475/localmodel/logs/ds41_places_%j.log --wrap "<this file> [server job id]"
# Progress: /research/projects/proofedit/ya475/localmodel/logs/ds41_places.status
HERE=$(cd "$(dirname "$0")" && pwd)
W=$(cd "$HERE/../../../.." && pwd)
LM=/research/projects/proofedit/ya475/localmodel
LOGS=$LM/logs
STATUS=$LOGS/ds41_places.status
URL=http://127.0.0.1:8012/v1
JOB=${1:-}
say() { echo "$(date -Is) $*" >> "$STATUS"; }
release() { [ -n "$JOB" ] && { say "releasing the node: scancel $JOB"; scancel "$JOB"; }; }

say "places test started (job ${SLURM_JOB_ID:-none})"
( cd "$HERE" && sha256sum -c --quiet prompts.sha256 ) || { say "STOP: the prompts are not the pre-registered bytes"; exit 1; }
if [ -z "$JOB" ]; then
  # This script is itself a job: its SLURM_* variables must not reach the server's submission.
  JOB=$(env $(env | awk -F= '/^SLURM_/ {print "-u " $1}') sbatch --parsable "$LM/serve_ds41.sbatch") || { say "STOP: sbatch serve_ds41.sbatch failed"; exit 1; }
  say "server job $JOB submitted"
fi
log=$LOGS/serve_ds41_$JOB.log
while true; do
  state=$(squeue -j "$JOB" -h -o %T 2>/dev/null)
  if [ -z "$state" ]; then say "STOP: job $JOB is gone before serving (see $log)"; exit 1; fi
  if grep -q -E "core.py:[0-9]+\] Traceback|^Traceback" "$log" 2>/dev/null; then say "STOP: server traceback (see $log)"; release; exit 1; fi
  if [ "$state" = RUNNING ] && curl -sf "$URL/models" >/dev/null 2>&1; then break; fi
  sleep 60
done
say "server $JOB up"
( cd "$LM/probes" && timeout 3600 "$LM/vllm-env/bin/python" probe_correct.py "$URL" local-deepseek > "$LOGS/probe_correct_ds41_places_$JOB.out" 2>&1 )
rc=$?
say "probe_correct exit $rc: $(grep -E '^17x19|^gsm8k [0-9]+/20' "$LOGS/probe_correct_ds41_places_$JOB.out" | tr '\n' ' ')"
[ $rc -eq 0 ] || { say "STOP: the server does not compute correctly"; release; exit 1; }
( cd "$LM/probes" && timeout 600 "$LM/vllm-env/bin/python" probe_carry.py "$URL" local-deepseek > "$LOGS/probe_carry_ds41_places_$JOB.out" 2>&1 )
rc=$?
say "probe_carry exit $rc: $(tail -1 "$LOGS/probe_carry_ds41_places_$JOB.out")"
[ $rc -eq 0 ] || { say "STOP: the server does not keep earlier thinking"; release; exit 1; }
cd "$W" || { release; exit 1; }
say "places run starting"
PYTHONPATH=$W:$W/src ape/bin/python "$HERE/places.py" run "$URL" local-deepseek 48 >> "$LOGS/ds41_places_run.log" 2>&1
rc=$?
say "places run exit $rc: $(wc -l < "$HERE/outputs.jsonl" 2>/dev/null || echo 0) outputs; $(tail -1 "$LOGS/ds41_places_run.log")"
release
say "places finished"
