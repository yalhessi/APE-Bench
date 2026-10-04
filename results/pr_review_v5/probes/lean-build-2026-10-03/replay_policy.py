"""Replay recorded edits under the full safe policy, strict completion wait, one server per file.

Per edit, by `classify_edits.classify`:
  proof_only / comment_only / stmt_unused -> the document cut after the changed declaration
  header                                  -> NOT sent to the server (it would restart the file and
                                             discard the warm state); answered by a separate cold
                                             process, so it costs what it costs today (cold time
                                             from the prior replay)
  needs_suffix:*                          -> the whole spliced file
The cut's answer is checked against the cold result on error presence; a whole-file answer on
error and warning sets. Usage (cwd: the replayed tree):
  replay_policy.py <replay script> <runs> <prior strict jsonl> <out.jsonl>
"""
import json, re, sys, time
from pathlib import Path

script_path, runs, prior_path, out_path = sys.argv[1:5]
here = Path(__file__).parent
V2 = "replay_bench_v2" in script_path
ns_text = Path(script_path).read_text().replace("asyncio.run(main())", "")
sys.argv = ["x", runs, "0", "8", "/dev/null"]
exec(compile(ns_text, script_path, "exec"))
strict_src = (here / "replay_server_strict.py").read_text()
exec(compile(strict_src[strict_src.index("def strict("):strict_src.index("prior = [json.loads")],
             "strict", "exec"))
from ape.toolkits.code.lean.lean_parser import parse_major_declarations  # noqa: E402
from ape.toolkits.code.lean.provider import LeanCodeToolsProvider  # noqa: E402
nocomment = LeanCodeToolsProvider.remove_comments
import ape.tasks.lean_tasks.formal_math.review.base as review_base  # noqa: E402
cls_src = (here / "classify_edits.py").read_text()
exec(compile(cls_src[cls_src.index("DELETES_SPAN = "):cls_src.index("runs = sys.argv[1]")]
             .replace("def splice(src, inp):", "def _unused_splice(src, inp):"), "classify", "exec"))
if not V2:
    as_compiled = lambda code: code  # noqa: E731
    def lsp_msgs(diags):  # noqa: F811
        errs = sorted({str(d.get("message", "")).strip() for d in diags if d.get("severity", 1) == 1})
        warns = sorted({str(d.get("message", "")).strip() for d in diags if d.get("severity") == 2})
        return errs, warns

CUT = ("proof_only", "comment_only", "stmt_unused")


def cut_point(src, code):
    """End of the declaration holding the last changed character of `code`."""
    k = 0
    while k < min(len(src), len(code)) and src[-1 - k] == code[-1 - k]:
        k += 1
    last = len(code) - k
    for d in parse_major_declarations(code):
        if d.span[1] >= last:
            return d.span[1]
    return len(code)


prior = [json.loads(l) for l in open(prior_path)]
out = open(out_path, "a")
for row in prior:
    ws, rel = row["ws"], row["rel"]
    src = (Path(ws) / rel).read_text(encoding="utf-8")
    decls = parse_major_declarations(src)
    edits, seen = [], set()
    for inp in groups[(ws, rel)]:
        code, mode = splice(src, inp)
        if code and code != src and code not in seen:
            seen.add(code); edits.append((code, mode, inp))
    edits = edits[:MAX_EDITS]
    if [m for _, m, _ in edits] != [e["mode"] for e in row["edits"]]:
        print("SKIP", rel, flush=True); continue
    client = LeanLSPClient(ws, initial_build=False, prevent_cache_get=True)
    t0 = time.perf_counter()
    client.open_file(rel)
    client.get_diagnostics(rel, inactivity_timeout=120, max_timeout=600)
    t_open, base, _, _ = strict(client, rel, t0)
    res = []
    for (code, mode, inp), e in zip(edits, row["edits"]):
        c = classify(src, code, decls)
        if c == "header":
            res.append(dict(cls=c, route="cold", t=e["cold"], errs=e["cold_errs"], warns=e.get("cold_warns", [])))
            continue
        text = as_compiled(code)
        route = "whole"
        if c in CUT:
            text = code[:cut_point(src, code)].rstrip() + "\n"; route = "cut"
        r = check(client, rel, text)
        res.append(dict(cls=c, route=route, t=r["t"], errs=r["errs"], warns=r["warns"]))
    client.close()
    print(f"== {rel}: " + ", ".join(f"{x['route']}:{x['t']:.1f}" for x in res), flush=True)
    new = dict(row, lsp_open=t_open, policy=[])
    for e, x in zip(row["edits"], res):
        ok = (bool(x["errs"]) == bool(e["cold_errs"])) if x["route"] == "cut" else \
             ({s.replace("↦", "=>") for s in x["errs"]} == {s.replace("↦", "=>") for s in e["cold_errs"]})
        new["policy"].append(dict(x, agrees=ok, cold=e["cold"]))
    out.write(json.dumps(new) + "\n"); out.flush()
