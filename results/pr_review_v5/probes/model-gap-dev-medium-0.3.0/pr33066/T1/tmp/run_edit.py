import json, subprocess, sys
D = "/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/conventions-dossiers/results/pr_review_v5/probes/model-gap-dev-medium-0.3.0/pr33066/T1"
path, decl, f = sys.argv[1], sys.argv[2], sys.argv[3]
args = {"path": path, "declaration_name": decl, "new_declaration": open(f).read()}
out = subprocess.run([D + "/ptool", "lean_verify_edit", json.dumps(args)], capture_output=True, text=True)
try:
    d = json.loads(out.stdout)
except Exception:
    print(out.stdout, out.stderr); sys.exit(1)
print("outcome:", d.get("outcome"), "success:", d.get("success"))
for e in d.get("errors_introduced_by_your_edit", []):
    print("ERR", json.dumps(e, ensure_ascii=False)[:1500])
for w in d.get("warnings", []):
    print("WARN", json.dumps(w, ensure_ascii=False)[:600])
for k in d:
    if k not in ("errors_introduced_by_your_edit","warnings","outcome","success","environment","warrants"):
        print(k, json.dumps(d[k], ensure_ascii=False)[:800])
