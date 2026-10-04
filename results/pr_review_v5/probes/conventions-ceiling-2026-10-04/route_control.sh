#!/usr/bin/env bash
# Stage C's route control, which its pre-registration attaches to a reading of >= +0.15: a fresh
# UNBRIEFED session (brief X, label XR1) on 30641 and 29842 through the route the briefed sessions
# used -- a headless parent on token B, CLI 2.1.285 -- matched beside X1, X2 and E1.
#
# The question: is any of E's gain the route's? Reading, fixed before the run:
#   - XR is the route's if it behaves as X does: its reach on these PRs' in-census asks is within
#     one ask of X1/X2's mean, on both matchers, and it reaches no ask that neither X1 nor X2 reached.
#   - Otherwise a route effect is suspected, and stage C's difference is read against XR, not X.
# Its power is small and stated: two PRs, 7 in-census asks, of which E gained 1 to 2.
# usage: bash route_control.sh <scratch dir>
set -euo pipefail
S=$1
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
export PYTHONPATH=$PWD/src PATH="$HOME/.elan/bin:$PATH"
P=results/pr_review_v5/probes/conventions-ceiling-2026-10-04
VAL=configs/probe_sets/val_small12.yaml
V=results/pr_review_v5/probes/model-gap-val-small12
probe() { ape/bin/python -m src.mathlib_review.review.cli probe "$@"; }
flagged=0

[ -f $V/pr30641/XR1/brief.md ] || probe packets --set $VAL --sessions XR1 --prs 30641 29842 --scratch $S/claude_stage_E > /dev/null
cmp $V/pr30641/XR1/brief.md results/pr_review_v5/probes/construction-demo-2026-09-29/brief_X.md
cmp $V/pr29842/XR1/brief.md results/pr_review_v5/probes/construction-demo-2026-09-29/brief_X.md
echo "$(date '+%H:%M:%S') XR1 on 30641 and 29842, token B"
$P/run_claude_batch.sh CLAUDE_CODE_OAUTH_TOKEN_B b6 $S/claude_logs XR1 $VAL:30641 $VAL:29842
python3 $P/batch_report.py $S/claude_logs/b6.jsonl $S/claude_logs/b6.prompt > $S/report_b6.txt
cat $S/report_b6.txt
python3 $P/audit_batch.py $S/claude_logs/b6.jsonl > $S/audit_b6.txt || flagged=1
cat $S/audit_b6.txt
[ -f $V/pr30641/XR1/findings.json ] && [ -f $V/pr29842/XR1/findings.json ]

printf '{"X1": {"kind": "claude"}, "X2": {"kind": "claude"}, "XR1": {"kind": "claude"}, "E1": {"kind": "claude"}}\n' > $P/sources_R.json
[ -f $P/blinding_R_val_SEALED.json ] || probe seal --set $VAL --sessions X1 X2 XR1 E1 --prs 30641 29842 --out $P/blinding_R_val_SEALED.json
probe match-inputs --set $VAL --seal $P/blinding_R_val_SEALED.json --sources $P/sources_R.json --out $S/match_R_val > $S/match_R_val.prompts
$P/run_claude_batch.sh CLAUDE_CODE_OAUTH_TOKEN_B m_route $S/claude_logs - @$S/match_R_val.prompts
python3 $P/batch_report.py $S/claude_logs/m_route.jsonl $S/claude_logs/m_route.prompt | sed -n '3,6p'
python3 $P/audit_batch.py $S/claude_logs/m_route.jsonl || flagged=1
python3 $P/check_matches.py $S/match_R_val/m1 $S/match_R_val/m2
mkdir -p $P/match_R_val
cp $S/match_R_val/m1/matches.json $P/match_R_val/matches.1.json
cp $S/match_R_val/m2/matches.json $P/match_R_val/matches.2.json
cp $S/match_R_val/inputs/session_stats.json $P/match_R_val/session_stats.json
probe unblind --set $VAL --seal $P/blinding_R_val_SEALED.json --matches $P/match_R_val > $P/match_R_val/unblinded.json

echo "$(date '+%H:%M:%S') THE ROUTE CONTROL (XR against X; E beside them)"
python3 $P/read_stage.py R XR X > $S/read_R.txt
cat $S/read_R.txt
python3 - $P/match_R_val/unblinded.json <<'EOF'
import json, sys
u = json.load(open(sys.argv[1]))
for m in ("1", "2"):
    print(f"matcher {m} per ask:", {cid: {s: (v or "-")[0] for s, v in sorted(row.items())} for cid, row in u[m]["table"].items()})
EOF
if [ "$flagged" = 0 ]; then
  { echo "probes: stage C's route control -- an unbriefed session through the briefed sessions' route on 30641 and 29842, matched; committed by route_control.sh unattended"
    echo; sed -n '3,5p' $S/report_b6.txt; echo; cat $S/audit_b6.txt; echo; cat $S/read_R.txt; } > $S/msg_R.txt
  git add $V/pr30641/XR1 $V/pr29842/XR1 $P/sources_R.json $P/blinding_R_val_SEALED.json $P/match_R_val
  git commit -q -F $S/msg_R.txt
fi
echo "$(date '+%H:%M:%S') ROUTE CONTROL DONE flagged=$flagged"
