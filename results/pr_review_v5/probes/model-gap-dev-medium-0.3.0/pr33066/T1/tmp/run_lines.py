import json, subprocess, sys
D = "/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/conventions-dossiers/results/pr_review_v5/probes/model-gap-dev-medium-0.3.0/pr33066/T1"
path, ls, le, f = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
args = {"path": path, "line_start": ls, "line_end": le, "replacement": open(f).read().rstrip("\n")}
out = subprocess.run([D + "/ptool", "lean_verify_edit", json.dumps(args)], capture_output=True, text=True)
try:
    d = json.loads(out.stdout)
except Exception:
    print(out.stdout, out.stderr); sys.exit(1)
print("outcome:", d.get("outcome"), "success:", d.get("success"))
for e in d.get("errors_introduced_by_your_edit", []):
    print("ERR", json.dumps(e, ensure_ascii=False)[:1500])
for k in d:
    if k not in ("errors_introduced_by_your_edit","outcome","success","environment","warrants","errors"):
        print(k, json.dumps(d[k], ensure_ascii=False)[:800])
