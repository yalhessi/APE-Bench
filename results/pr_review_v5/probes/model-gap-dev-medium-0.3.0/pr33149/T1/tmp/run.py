import json, subprocess, sys
D = "/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/conventions-dossiers/results/pr_review_v5/probes/model-gap-dev-medium-0.3.0/pr33149/T1"
args = json.load(open(sys.argv[1]))
args.setdefault("path", "Mathlib/Analysis/ODE/GalerkinRegularity.lean")
out = subprocess.run([D + "/ptool", "lean_verify_edit", json.dumps(args)], capture_output=True, text=True)
open(sys.argv[1].replace(".json", ".out.json"), "w").write(out.stdout + out.stderr)
try:
    d = json.loads(out.stdout)
except Exception:
    print(out.stdout[:3000], out.stderr[:3000]); sys.exit()
print("outcome:", d.get("outcome"), "success:", d.get("success"))
for e in d.get("errors_introduced_by_your_edit", []):
    print("ERR", e.get("pos"), e.get("code_line"), "\n   ", e.get("data")[:800])
for w in d.get("warnings", []):
    if isinstance(w, dict):
        print("WARN", w.get("pos"), (w.get("code_line") or "")[:100], "|", w.get("data","")[:300].replace("\n"," "))
for k in d:
    if k not in ("errors_introduced_by_your_edit","warnings","errors_already_in_the_file","outcome","success","environment","warrants"):
        print(k, str(d[k])[:500])
