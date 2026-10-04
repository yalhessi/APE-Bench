#!/usr/bin/env python3
# usage: v.py <path> <declname> <leanfile>   (declaration mode)
#        v.py <path> L <start> <end> <leanfile>  (line mode)
import json, subprocess, sys
P = "/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/pipeline-overfit-review/results/pr_review_v5/probes/model-gap-val-small12/pr34935/X1/ptool"
path = sys.argv[1]
if sys.argv[2] == "L":
    args = {"path": path, "line_start": int(sys.argv[3]), "line_end": int(sys.argv[4]), "replacement": open(sys.argv[5]).read()}
else:
    args = {"path": path, "declaration_name": sys.argv[2], "new_declaration": open(sys.argv[3]).read()}
r = subprocess.run([P, "lean_verify_edit", json.dumps(args)], capture_output=True, text=True)
try:
    j = json.loads(r.stdout)
    for k in ("success", "compiles", "errors_introduced_by_your_edit", "errors_already_in_the_file", "warnings"):
        if k in j: print(k, "=", json.dumps(j[k], ensure_ascii=False, indent=1))
except Exception:
    print(r.stdout); print(r.stderr)
