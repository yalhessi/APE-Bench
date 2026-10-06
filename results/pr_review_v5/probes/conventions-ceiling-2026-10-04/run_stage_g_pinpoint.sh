#!/usr/bin/env bash
# Stage G's pinpointing pass for the PRs not yet done, unattended on token C: batches of up to four
# blind pinpointers while the window has room, each audited; then every PR's candidates are copied
# in as written, the briefs and the retrieval reading are built, and all of it is committed before
# any reviewer session exists. An audit flag or a malformed file stops it uncommitted.
# usage: bash run_stage_g_pinpoint.sh <scratch dir> <prompts file of the pinpointers still to run>
set -euo pipefail
S=$1; todo=$2
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
export PYTHONPATH=$PWD:$PWD/src PATH="$HOME/.elan/bin:$PATH"
P=results/pr_review_v5/probes/conventions-ceiling-2026-10-04
. $P/token_window.sh
total=$(wc -l < "$todo"); done_n=0; n=0
while [ "$done_n" -lt "$total" ]; do
  n=$(( n + 1 ))
  sed -n "$(( done_n + 1 )),$(( done_n + 4 ))p" "$todo" > $S/pinpoint_b$n.prompts
  k=$(wc -l < $S/pinpoint_b$n.prompts)
  wait_for_room $(( 18 * k )) 97 85 || { echo "no room for pinpointers, or the week is at 85%"; exit 6; }
  echo "$(date '+%H:%M:%S') pinpoint batch pb$n: $k pinpointers"
  $P/run_claude_batch.sh CLAUDE_CODE_OAUTH_TOKEN_C pb$n $S/claude_logs - @$S/pinpoint_b$n.prompts
  python3 $P/batch_report.py $S/claude_logs/pb$n.jsonl $S/claude_logs/pb$n.prompt | grep -E '^Pinpointer|^five-hour|^result'
  python3 $P/audit_batch.py $S/claude_logs/pb$n.jsonl
  done_n=$(( done_n + k ))
done
mkdir -p $P/pinpoints
for pr in 30641 29842 41930 32875 42814 30458 28649 42184 43167 34091; do
  python3 -c "import json,sys; json.load(open(sys.argv[1]))" $S/pinpoint/pr$pr/candidates.json
  cp $S/pinpoint/pr$pr/candidates.json $P/pinpoints/pr$pr.json
done
python3 $P/build_candidate_briefs.py --write > $S/retrieval_G.txt
cat $S/retrieval_G.txt
{ echo "probes: stage G's pinpointed candidates and its retrieval reading -- what the briefs hold, before any reviewer session; committed by run_stage_g_pinpoint.sh unattended"
  echo; cat $S/retrieval_G.txt; echo
  for f in $S/claude_logs/pa.jsonl $S/claude_logs/pb*.jsonl; do python3 $P/batch_report.py $f ${f%.jsonl}.prompt | grep -E '^Pinpointer|^five-hour'; python3 $P/audit_batch.py $f | tail -1; done; } > $S/msg_pinpoint.txt
git add $P/pinpoints $P/briefs_candidates.json $P/candidate_retrieval.json
git commit -q -F $S/msg_pinpoint.txt
echo "$(date '+%H:%M:%S') STAGE G PINPOINTING DONE"
