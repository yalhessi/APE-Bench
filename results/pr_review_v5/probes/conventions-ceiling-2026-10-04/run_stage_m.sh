#!/usr/bin/env bash
# Stage M unattended (cross_model.md): twelve gpt-5.5 runs through ELM in two queues, one a set, in
# rep order (base, exact; rep 1 to 3), each run committed as it finishes; then one seal a set over
# X1, X2, GB1-3, GE1-3, two blind matchers a set headless on token B, the unblinding and the reading.
# A failed run stops its queue; an audit flag holds back the matching's commit.
# usage: bash run_stage_m.sh <scratch dir>
set -euo pipefail
S=$1
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
export PYTHONPATH=$PWD/src PATH="$HOME/.elan/bin:$PATH"
P=results/pr_review_v5/probes/conventions-ceiling-2026-10-04
L=$S/logs_M; mkdir -p $L
declare -A SET=([val]=configs/probe_sets/val_small12.yaml [post]=configs/probe_sets/postcutoff_2026_07_08_v1.yaml)
probe() { ape/bin/python -m src.mathlib_review.review.cli probe "$@"; }
commit() { flock $S/git_M.lock bash -c "$1"; }

queue() {
  local tag=$1
  for rep in 1 2 3; do
    for level in base exact; do
      local name=probe_conv_${tag}_elmgpt55_${level}_rep${rep} t
      t=$(date +%s)
      $P/run_elm.sh $tag $level $rep > $L/$name.log 2>&1
      local ok fail found
      ok=$(grep -c 'completed with success' $L/$name.log || true)
      fail=$(grep -c 'API call failed, retrying' $L/$name.log || true)
      found=$(grep -o 'finalized: .*' $L/$name.log | tail -1)
      echo "$(date '+%H:%M:%S') $name: $(( $(date +%s) - t )) s, $ok sessions succeeded, $fail retries | $found"
      commit "git add results/pr_review_v5/runs/$name && git commit -q -m 'results: stage M run $name -- gpt-5.5 through ELM, $level, rep $rep; committed by run_stage_m.sh unattended

$ok sessions completed with success, $fail \"API call failed, retrying\" lines; $found'"
    done
  done
}

queue val > $L/queue_val.out 2>&1 &
qv=$!
queue post > $L/queue_post.out 2>&1 &
qp=$!
status=0
wait $qv || status=1
wait $qp || status=1
cat $L/queue_val.out $L/queue_post.out
[ $status = 0 ] || { echo "a queue failed"; exit 5; }

flagged=0
window() {
  ( set +eu; source ~/.config/secrets/env.zsh; mkdir -p "$S/home_B"; cd "$S/home_B"
    HOME=$S/home_B CLAUDE_CODE_OAUTH_TOKEN="$CLAUDE_CODE_OAUTH_TOKEN_B" timeout 120 claude -p "Reply with the single word: ok" \
      --model claude-haiku-4-5-20251001 --output-format stream-json --verbose < /dev/null 2> /dev/null ) > "$S/limit_B.jsonl" || true
  python3 - "$S/limit_B.jsonl" <<'EOF'
import json, sys
for line in open(sys.argv[1]):
    try:
        d = json.loads(line)
    except ValueError:
        continue
    if d.get("type") == "rate_limit_event":
        info = d.get("rate_limit_info") or d
        used = ((info.get("unifiedWindows") or {}).get("five_hour") or {}).get("utilization") or 0
        print(info.get("status"), round(100 * used)); sys.exit()
print("unknown", 100)
EOF
}
for tag in val post; do
  python3 - $tag > $S/sources_M_$tag.json <<'EOF'
import json, sys
tag = sys.argv[1]
src = {"X1": {"kind": "claude"}, "X2": {"kind": "claude"}}
for label, level in (("GB", "base"), ("GE", "exact")):
    for n in (1, 2, 3):
        src[f"{label}{n}"] = {"kind": "solo", "run": f"probe_conv_{tag}_elmgpt55_{level}_rep{n}"}
print(json.dumps(src, indent=1))
EOF
  cp $S/sources_M_$tag.json $P/sources_M_$tag.json
  [ -f $P/blinding_M_${tag}_SEALED.json ] || probe seal --set ${SET[$tag]} --sessions X1 X2 GB1 GB2 GB3 GE1 GE2 GE3 --out $P/blinding_M_${tag}_SEALED.json
  probe match-inputs --set ${SET[$tag]} --seal $P/blinding_M_${tag}_SEALED.json --sources $P/sources_M_$tag.json --out $S/match_M_$tag > $S/match_M_$tag.prompts
  for try in $(seq 1 30); do
    read -r st used < <(window)
    echo "$(date '+%H:%M:%S') token B: $st, $used% used"
    if [[ "$st" == allowed* ]] && [ "$used" -le 80 ]; then break; fi
    [ "$try" -lt 30 ] || { echo "token B never had room"; exit 7; }
    sleep 900
  done
  echo "$(date '+%H:%M:%S') matchers, $tag, on token B"
  $P/run_claude_batch.sh CLAUDE_CODE_OAUTH_TOKEN_B m_M_$tag $S/claude_logs - @$S/match_M_$tag.prompts
  python3 $P/batch_report.py $S/claude_logs/m_M_$tag.jsonl $S/claude_logs/m_M_$tag.prompt | grep -E '^Matcher|^five-hour'
  python3 $P/audit_batch.py $S/claude_logs/m_M_$tag.jsonl || flagged=1
  python3 $P/check_matches.py $S/match_M_$tag/m1 $S/match_M_$tag/m2
  mkdir -p $P/match_M_$tag
  cp $S/match_M_$tag/m1/matches.json $P/match_M_$tag/matches.1.json
  cp $S/match_M_$tag/m2/matches.json $P/match_M_$tag/matches.2.json
  cp $S/match_M_$tag/inputs/session_stats.json $P/match_M_$tag/session_stats.json
  probe unblind --set ${SET[$tag]} --seal $P/blinding_M_${tag}_SEALED.json --matches $P/match_M_$tag > $P/match_M_$tag/unblinded.json
done
echo "$(date '+%H:%M:%S') THE READING (rule: GE - GB on in-census asks, pooled, both matchers)"
python3 $P/read_stage.py M GE GB > $S/read_M.txt
cat $S/read_M.txt
if [ "$flagged" = 0 ]; then
  { echo "probes: stage M matched -- gpt-5.5's tables, committed by run_stage_m.sh unattended; the write-up follows"
    echo; cat $S/read_M.txt; } > $S/msg_M.txt
  commit "git add $P/sources_M_val.json $P/sources_M_post.json $P/blinding_M_val_SEALED.json $P/blinding_M_post_SEALED.json $P/match_M_val $P/match_M_post && git commit -q -F $S/msg_M.txt"
fi
echo "$(date '+%H:%M:%S') STAGE M PIPELINE DONE flagged=$flagged"
