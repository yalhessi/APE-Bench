import json, subprocess, sys
# usage: verify_decl.py <path> <declname> <file-with-new-decl>
path, name, f = sys.argv[1:4]
new = open(f).read()
args = json.dumps({"path": path, "declaration_name": name, "new_declaration": new})
open(f + ".args.json", "w").write(args)
out = subprocess.run(["/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/pipeline-overfit-review/results/pr_review_v5/probes/model-gap-dev-medium-0.3.0/pr33066/X2/ptool", "lean_verify_edit", args], capture_output=True, text=True)
print(out.stdout[:6000]); print(out.stderr[-2000:])
