import json, subprocess, sys
P = "/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/conventions-dossiers/results/pr_review_v5/probes/model-gap-dev-medium-0.3.0/pr33321/TA1/ptool"
def run(args, label):
    out = subprocess.run([P, "lean_verify_edit", json.dumps(args)], capture_output=True, text=True)
    try:
        d = json.loads(out.stdout)
    except Exception:
        print(label, "PARSE FAIL", out.stdout[:500], out.stderr[-500:]); return
    print("==", label, d.get("outcome"), d.get("success"))
    for e in d.get("errors_introduced_by_your_edit", [])[:4]:
        print("   ERR", str(e.get("message",""))[:400].replace("\n"," "), "|", e.get("code_line",""))
    for w in d.get("warnings", [])[:6]:
        print("   WARN", str(w)[:300].replace("\n"," "))
if __name__ == "__main__":
    spec = json.load(open(sys.argv[1]))
    for label, args in spec:
        run(args, label)
