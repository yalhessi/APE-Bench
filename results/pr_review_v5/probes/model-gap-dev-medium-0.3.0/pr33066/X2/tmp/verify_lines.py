import json, subprocess, sys
# usage: verify_lines.py <path> <start> <end> <file-with-replacement>
path, s, e, f = sys.argv[1:5]
new = open(f).read()
if new.endswith("\n"): new = new[:-1]
args = json.dumps({"path": path, "line_start": int(s), "line_end": int(e), "replacement": new})
out = subprocess.run(["/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/pipeline-overfit-review/results/pr_review_v5/probes/model-gap-dev-medium-0.3.0/pr33066/X2/ptool", "lean_verify_edit", args], capture_output=True, text=True)
print(out.stdout[:6000]); print(out.stderr[-2000:])
