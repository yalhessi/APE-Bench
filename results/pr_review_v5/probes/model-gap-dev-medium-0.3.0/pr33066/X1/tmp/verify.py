import json, subprocess, sys
# usage: verify.py <path> <decl_name|-> <file with new text> [line_start line_end]
D = "/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/pipeline-overfit-review/results/pr_review_v5/probes/model-gap-dev-medium-0.3.0/pr33066/X1"
path, name, f = sys.argv[1:4]
text = open(f).read().rstrip("\n")
if name == "-":
    args = {"path": path, "line_start": int(sys.argv[4]), "line_end": int(sys.argv[5]), "replacement": text}
else:
    args = {"path": path, "declaration_name": name, "new_declaration": text}
r = subprocess.run([D + "/ptool", "lean_verify_edit", json.dumps(args, ensure_ascii=False)], capture_output=True, text=True)
out = r.stdout
try:
    d = json.loads(out)
    print("success:", d.get("success"), d.get("message"))
    for e in d.get("errors_introduced_by_your_edit", d.get("errors", [])):
        print("---", e.get("pos"), e.get("code_line"))
        print(e.get("data"))
    for w in d.get("warnings", []):
        print("WARN", w.get("pos"), str(w.get("data"))[:300])
except Exception:
    print(out, r.stderr[-2000:])
