#!/bin/bash
# Judge one finished run and append its score to the gate status (the same steps as the gates' judge).
set -u
R=${1:?run name}
W=/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/local-model-unlock
LOGS=/research/projects/proofedit/ya475/localmodel/logs
cd "$W" || exit 1
set -a; . ~/.config/secrets/env.zsh; set +a
PYTHONPATH=$W/src timeout 2400 ape/bin/python -m src.mathlib_review.review.cli judge \
  --config configs/pr_review_v5_medium_heldout_judge.yaml --of "$R" --execute > "$LOGS/judge_$R.log" 2>&1
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
echo "$(date -Is) judged $R: $score (judge retries $(grep -c 'API call failed, retrying' "$LOGS/judge_$R.log"))" >> "$LOGS/ds41_gate.status"
