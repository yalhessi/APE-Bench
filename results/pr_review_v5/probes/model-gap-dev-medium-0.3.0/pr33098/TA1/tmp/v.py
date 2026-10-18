import json, subprocess, sys
# usage: v.py <decl_name> <file_with_new_decl>   or  v.py --lines <start> <end> <file_with_replacement>
D = "/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/conventions-dossiers/results/pr_review_v5/probes/model-gap-dev-medium-0.3.0/pr33098/TA1"
args = {"path": "Mathlib/Topology/MetricSpace/CoveringNumbers.lean"}
if sys.argv[1] == "--lines":
    args["line_start"] = int(sys.argv[2]); args["line_end"] = int(sys.argv[3])
    if len(sys.argv) > 4:
        args["replacement"] = open(sys.argv[4]).read()
else:
    args["declaration_name"] = sys.argv[1]
    args["new_declaration"] = open(sys.argv[2]).read()
out = subprocess.run([D + "/ptool", "lean_verify_edit", json.dumps(args)], capture_output=True, text=True)
try:
    d = json.loads(out.stdout)
    keep = {k: d.get(k) for k in ("outcome", "success", "errors_introduced_by_your_edit", "warnings", "errors_already_in_the_file")}
    print(json.dumps(keep, indent=1, ensure_ascii=False))
except Exception:
    print(out.stdout, out.stderr)
