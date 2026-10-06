#!/bin/bash
# Unattended DeepSeek-V4.1-Flash level gate (results/pr_review_v5/probes/local-ds41-2026-10-06/):
# wait for the server job, probe it, run the four reps one at a time, judge each, release the node.
# Usage: nohup setsid run_ds41_gate.sh <server job id> &   Progress: logs/ds41_gate.status
set -u
JOB=${1:?server job id}
W=/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/local-model-unlock
LM=/research/projects/proofedit/ya475/localmodel
LOGS=$LM/logs
STATUS=$LOGS/ds41_gate.status
SERVER_LOG=$LOGS/serve_ds41_$JOB.log
URL=http://127.0.0.1:8012/v1
say() { echo "$(date -Is) $*" >> "$STATUS"; }
release() { say "releasing the node: scancel $JOB"; scancel "$JOB"; }

say "gate started; waiting for job $JOB"
while true; do
  state=$(squeue -j "$JOB" -h -o %T 2>/dev/null)
  if [ -z "$state" ]; then say "STOP: job $JOB is gone before serving (see $SERVER_LOG)"; exit 1; fi
  if grep -q -E "core.py:[0-9]+\] Traceback|^Traceback" "$SERVER_LOG" 2>/dev/null; then
    say "STOP: server traceback (see $SERVER_LOG)"; release; exit 1
  fi
  if [ "$state" = RUNNING ] && curl -sf "$URL/models" >/dev/null 2>&1; then break; fi
  sleep 60
done
say "server up: $(grep -E 'download took|Loading weights took|GPU KV cache size' "$SERVER_LOG" | tail -3 | sed 's/.*\] //' | tr '\n' ' ')"

# 1. Basic probes; the gate stops on a failure here.
cd "$LM/probes" || exit 1
timeout 3600 "$LM/vllm-env/bin/python" probe_basic.py "$URL" local-deepseek > "$LOGS/probe_basic_ds41.out" 2>&1
rc=$?
verdict=$("$LM/vllm-env/bin/python" - "$LOGS/probe_basic_ds41.out" <<'EOF'
import re, sys
text = open(sys.argv[1]).read()
problems = []
m = re.search(r"responses with a tool call (\d+)/(\d+); calls schema-valid (\d+)/(\d+)", text)
if not m: problems.append("no tool-call summary")
else:
    a, b, x, y = map(int, m.groups())
    if a < 12: problems.append(f"only {a}/{b} replies called a tool")
    if y == 0 or x / y < 0.9: problems.append(f"schema-valid {x}/{y}")
if not re.search(r"same\s+prompt=\s*\d+ cached=[1-9]", text): problems.append("no warm cache hit reported")
m = re.search(r"reasoning_effort none\s+completion_tokens=\s*(\d+) reasoning_chars=\s*(\d+)", text)
if not m or int(m.group(2)) > 0: problems.append("reasoning_effort none did not turn thinking off")
print("ok" if not problems else "; ".join(problems))
EOF
)
say "probe_basic exit $rc: $verdict"
if [ $rc -ne 0 ] || [ "$verdict" != ok ]; then say "STOP: the basic probes failed"; release; exit 1; fi

# 2. The reps, one at a time; each judged as it finishes.
cd "$W" || exit 1
for spec in high:1 high:2 high:3 none:1; do
  effort=${spec%%:*}; n=${spec##*:}
  R=iter_ds41_contract2_${effort}_rep$n
  say "run $R starting"
  PYTHONPATH=$W/src nohup ape/bin/python -m src.mathlib_review.review.cli run \
    --config configs/pr_review_v5_dev_medium_local_ds41_contract2.yaml --run-name "$R" \
    --set llm_config.reasoning_effort="$effort" --execute > "$LOGS/cli_$R.log" 2>&1 &
  pid=$!
  while kill -0 $pid 2>/dev/null; do
    if [ -z "$(squeue -j "$JOB" -h -o %T 2>/dev/null)" ]; then
      say "STOP: server job ended during $R"; kill $pid; exit 1
    fi
    if [ "$(grep -c 'API call failed, retrying' "$LOGS/cli_$R.log")" -gt 20 ]; then
      say "STOP: $R is retrying (server unreachable?)"; kill $pid; release; exit 1
    fi
    sleep 30
  done
  say "run $R: $(grep -h 'completion_status=' "$LOGS/cli_$R.log" | sed 's/.*completion_status/completion_status/' | cut -c1-60); $(grep -c 'completed with success' "$LOGS/cli_$R.log") sessions ok, $(grep -c failed_error "$LOGS/cli_$R.log") failed"
  (set -a; . ~/.config/secrets/env.zsh; set +a
   PYTHONPATH=$W/src timeout 2400 ape/bin/python -m src.mathlib_review.review.cli judge \
     --config configs/pr_review_v5_medium_heldout_judge.yaml --of "$R" --execute > "$LOGS/judge_$R.log" 2>&1)
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
done

PYTHONPATH=$W/src ape/bin/python results/pr_review_v5/probes/local-unlock-2026-10-03/screen.py \
  | grep -E "^run|^ds41|^base" >> "$STATUS"
say "gate finished"
release
