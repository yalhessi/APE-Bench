#!/usr/bin/env bash
# usage: rd.sh <path> <start> <end>
D=/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/pipeline-overfit-review/results/pr_review_v5/probes/model-gap-dev-medium-0.3.0/pr33421/X1
$D/ptool file_read "{\"file_path\": \"$1\", \"line_start\": $2, \"line_end\": $3, \"omit_details\": false}" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("content", d))'
