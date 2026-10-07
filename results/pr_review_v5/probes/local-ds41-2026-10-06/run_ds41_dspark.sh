#!/bin/bash
# Speculative decoding (DSpark, the draft stages in the V4.1 checkpoint) on the keepthink condition: one rep,
# against keepthink reps 1-3 on the plain server. Same config, concurrency and PRs; only the server differs
# (--speculative-config {"method":"dspark"}, 5 draft tokens from dspark_block_size). Speculative decoding is
# lossless in distribution, so the score should sit inside the reps' spread; what it measures is speed.
# Original header of run_ds41_keepthink.sh, from which this is copied:
# DeepSeek-V4.1-Flash level gate, rerun with each turn's thinking kept (2026-10-07).
# high reps (iter_ds41_contract2_high_rep*) ran with the client dropping every turn's thinking
# (OpenAIMessageFormatter; fixed in 5fd560ab) and were stopped; its none rep is unaffected and stands.
# New run names, since the fix is in code and not in any config the orchestrator would see: the old
# names would resume the defective runs. One rep at a time, all 15 sessions at once: with the thinking
# kept a session's prompt grows ~8k a turn, and the KV pool cannot hold three reps' tails side by side.
# Usage: sbatch ... --wrap "./run_ds41_keepthink.sh <server job id>"   Progress: logs/ds41_gate.status
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

say "dspark gate started; waiting for job $JOB"
while true; do
  state=$(squeue -j "$JOB" -h -o %T 2>/dev/null)
  if [ -z "$state" ]; then say "STOP: job $JOB is gone before serving (see $SERVER_LOG)"; exit 1; fi
  if grep -q -E "core.py:[0-9]+\] Traceback|^Traceback" "$SERVER_LOG" 2>/dev/null; then
    say "STOP: server traceback (see $SERVER_LOG)"; release; exit 1
  fi
  if [ "$state" = RUNNING ] && curl -sf "$URL/models" >/dev/null 2>&1; then break; fi
  sleep 60
done
say "server up: $(grep -E 'download took|Loading weights took|GPU KV cache size|max len' "$SERVER_LOG" | tail -4 | sed 's/.*\] //' | tr '\n' ' ')"

cd "$LM/probes" || exit 1
timeout 3600 "$LM/vllm-env/bin/python" probe_correct.py "$URL" local-deepseek > "$LOGS/probe_correct_ds41.out" 2>&1
rc=$?
say "probe_correct exit $rc: $(grep -E '^17x19|^gsm8k [0-9]+/20' "$LOGS/probe_correct_ds41.out" | tr '\n' ' ')"
if [ $rc -ne 0 ]; then say "STOP: the server does not compute correctly"; release; exit 1; fi
timeout 600 "$LM/vllm-env/bin/python" probe_carry.py "$URL" local-deepseek > "$LOGS/probe_carry_ds41.out" 2>&1
rc=$?
say "probe_carry exit $rc: $(cat "$LOGS/probe_carry_ds41.out" | tail -1)"
if [ $rc -ne 0 ]; then say "STOP: the server does not keep earlier thinking"; release; exit 1; fi

cd "$W" || exit 1
for n in 1; do
  R=iter_ds41_contract2_keepthink_dspark_high_rep$n
  say "run $R starting"
  PYTHONPATH=$W/src nohup ape/bin/python -m src.mathlib_review.review.cli run \
    --config configs/pr_review_v5_dev_medium_local_ds41_contract2.yaml --run-name "$R" \
    --set llm_config.reasoning_effort=high --set execution.max_concurrency=15 --execute > "$LOGS/cli_$R.log" 2>&1 &
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
grep -E "SpecDecoding metrics" "$SERVER_LOG" | tail -3 | sed "s/.*\] //" >> "$STATUS"
say "dspark gate finished"
release
