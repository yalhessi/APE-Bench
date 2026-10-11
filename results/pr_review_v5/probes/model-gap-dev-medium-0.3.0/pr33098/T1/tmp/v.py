import json, subprocess, sys
D = "/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/conventions-dossiers/results/pr_review_v5/probes/model-gap-dev-medium-0.3.0/pr33098/T1"
name = sys.argv[1]
src = open(sys.argv[2]).read()
args = {"path": "Mathlib/Topology/MetricSpace/CoveringNumbers.lean", "declaration_name": name, "new_declaration": src}
out = subprocess.run([D + "/ptool", "lean_verify_edit", json.dumps(args)], capture_output=True, text=True)
try:
    d = json.loads(out.stdout)
    for k in ("outcome", "success", "errors_introduced_by_your_edit", "warnings_introduced_by_your_edit", "warnings"):
        if k in d: print(k, json.dumps(d[k], indent=1, ensure_ascii=False)[:3000])
except Exception:
    print(out.stdout[:3000], out.stderr[-2000:])
