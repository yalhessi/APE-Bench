#!/usr/bin/env bash
# Stage C's remainder, run unattended once token B's five-hour window has reset: the last briefed
# session (34091), validation's one seal over its six run PRs, two blind matchers headless on token
# B, the unblinding and the pre-registered reading.
#
# Before it waits it dry-runs both launcher modes, so a broken step fails at once and not at the
# reset. A step that fails stops it. An audit flag does not stop the matching (the matchers are
# blind), but then nothing is committed, and the flag is read by hand before anything is used.
# usage: bash finish_stage_c.sh <scratch dir> <HH:MM, when to start>
set -euo pipefail
S=$1; start=$2
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
export PYTHONPATH=$PWD/src PATH="$HOME/.elan/bin:$PATH"
P=results/pr_review_v5/probes/conventions-ceiling-2026-10-04
VAL=configs/probe_sets/val_small12.yaml
E34091=results/pr_review_v5/probes/construction-demo-2026-09-29/pr34091/E1
probe() { ape/bin/python -m src.mathlib_review.review.cli probe "$@"; }
flagged=0

bash -n $P/run_claude_batch.sh
DRY_RUN=1 $P/run_claude_batch.sh CLAUDE_CODE_OAUTH_TOKEN_B b5 $S/claude_logs E1 $VAL:34091 > /dev/null
DRY_RUN=1 $P/run_claude_batch.sh CLAUDE_CODE_OAUTH_TOKEN_B dry_matchers $S/claude_logs - @$S/match_C1_post.prompts > /dev/null
[ "$(grep -c '^description: Matcher m' $S/claude_logs/dry_matchers.prompt)" = 2 ]
echo "$(date '+%H:%M:%S') dry runs pass; waiting until $start"
pause=$(( $(date -d "today $start" +%s) - $(date +%s) ))
[ "$pause" -le 0 ] || sleep "$pause"

# Token B must be allowed again, with most of its window free, before a session is started on it.
b_free() {
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
        print("token B:", info.get("status"), used)
        sys.exit(0 if str(info.get("status")).startswith("allowed") and used <= 0.5 else 1)
sys.exit(1)
EOF
}
for try in 1 2 3 4 5 6; do
  if b_free; then break; fi
  [ "$try" -lt 6 ] || { echo "token B is still not free"; exit 4; }
  sleep 300
done

echo "$(date '+%H:%M:%S') 34091 E1 on token B"
$P/run_claude_batch.sh CLAUDE_CODE_OAUTH_TOKEN_B b5 $S/claude_logs E1 $VAL:34091
python3 $P/batch_report.py $S/claude_logs/b5.jsonl $S/claude_logs/b5.prompt > $S/report_b5.txt
cat $S/report_b5.txt
python3 $P/audit_batch.py $S/claude_logs/b5.jsonl > $S/audit_b5.txt || flagged=1
cat $S/audit_b5.txt
[ -f $E34091/findings.json ]
if [ "$flagged" = 0 ]; then
  { echo "results: stage C's last briefed session, 34091 on token B -- audited clean, committed by finish_stage_c.sh unattended"
    echo; sed -n '3,4p' $S/report_b5.txt; echo; cat $S/audit_b5.txt; } > $S/msg_b5.txt
  git add $E34091
  git commit -q -F $S/msg_b5.txt
fi

echo "$(date '+%H:%M:%S') validation: seal, matcher inputs, two matchers on token B"
[ -f $P/blinding_C2_val_SEALED.json ] || probe seal --set $VAL --sessions X1 X2 E1 \
  --prs 30641 29842 32875 30458 28649 34091 --out $P/blinding_C2_val_SEALED.json
probe match-inputs --set $VAL --seal $P/blinding_C2_val_SEALED.json --sources $P/sources_C.json \
  --out $S/match_C2_val > $S/match_C2_val.prompts
$P/run_claude_batch.sh CLAUDE_CODE_OAUTH_TOKEN_B m_val $S/claude_logs - @$S/match_C2_val.prompts
python3 $P/batch_report.py $S/claude_logs/m_val.jsonl $S/claude_logs/m_val.prompt
python3 $P/audit_batch.py $S/claude_logs/m_val.jsonl || flagged=1
python3 $P/check_matches.py $S/match_C2_val/m1 $S/match_C2_val/m2
mkdir -p $P/match_C2_val
cp $S/match_C2_val/m1/matches.json $P/match_C2_val/matches.1.json
cp $S/match_C2_val/m2/matches.json $P/match_C2_val/matches.2.json
cp $S/match_C2_val/inputs/session_stats.json $P/match_C2_val/session_stats.json
probe unblind --set $VAL --seal $P/blinding_C2_val_SEALED.json --matches $P/match_C2_val > $P/match_C2_val/unblinded.json

echo "$(date '+%H:%M:%S') THE READING (rule: E - X on in-census asks, pooled, with the three PRs not run imputed)"
python3 $P/read_stage.py C1,C2 E X --impute 26755 36822 43192 > $S/read_C.txt
cat $S/read_C.txt
echo "--- the ten run PRs alone, no imputation (asks per finding are read here) ---"
python3 $P/read_stage.py C1,C2 E X > $S/read_C_run.txt
sed -n '/asks reached per finding/,$p' $S/read_C_run.txt
if [ "$flagged" = 0 ]; then
  { echo "probes: stage C matched on validation -- the reading's tables, committed by finish_stage_c.sh unattended; the write-up follows"
    echo; cat $S/read_C.txt; } > $S/msg_C2.txt
  git add $P/blinding_C2_val_SEALED.json $P/match_C2_val
  git commit -q -F $S/msg_C2.txt
fi
echo "$(date '+%H:%M:%S') STAGE C PIPELINE DONE flagged=$flagged"
