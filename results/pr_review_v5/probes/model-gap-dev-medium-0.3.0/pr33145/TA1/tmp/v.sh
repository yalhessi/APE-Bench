#!/bin/bash
# usage: v.sh <decl_name> <file>
D=/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/conventions-dossiers/results/pr_review_v5/probes/model-gap-dev-medium-0.3.0/pr33145/TA1
python3 -c '
import json,sys
print(json.dumps({"path":"Mathlib/Topology/Order/IsLUB.lean","declaration_name":sys.argv[1],"new_declaration":open(sys.argv[2]).read()}))' "$1" "$2" > "$2.json"
$D/ptool lean_verify_edit "$(cat $2.json)"
