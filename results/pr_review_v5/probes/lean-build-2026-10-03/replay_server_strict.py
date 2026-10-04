"""Re-measure the server half of a replay with a completion wait that cannot return early.

leanclient's `get_diagnostics` can return before Lean has finished the new version: its
`$/lean/fileProgress` handler ignores the document version, so a late "processing done" from the
previous version marks the new one done, and its `publishDiagnostics` handler accepts the previous
version's messages. On a file that already has messages it then returns those (2026-10-03:
GalerkinRegularity, 5 of 13 warnings, an error missing, at 0.0-0.1 s).

Here every check waits on Lean's own `textDocument/waitForDiagnostics` for the exact version just
sent, then for diagnostics stamped with that version. Both answers are recorded per edit: leanclient's
(`lc`) and the strict one. Cold results are taken from the prior jsonl unchanged.
Usage: replay_server_strict.py <replay script> <runs> <prior.jsonl> <out.jsonl>  (cwd: the replayed tree)
"""
import json, sys, time
from pathlib import Path

script_path, runs, prior_path, out_path = sys.argv[1:5]
V2 = "replay_bench_v2" in script_path
src_text = Path(script_path).read_text().replace("asyncio.run(main())", "")
sys.argv = ["x", runs, "0", "8", "/dev/null"]
exec(compile(src_text, script_path, "exec"))
if not V2:
    as_compiled = lambda code: code  # noqa: E731  v1 pushed the spliced text as is
    def lsp_msgs(diags):  # noqa: F811
        sev = {1: "error", 2: "warning"}
        errs = sorted({str(d.get("message", "")).strip() for d in diags if d.get("severity", 1) == 1})
        warns = sorted({str(d.get("message", "")).strip() for d in diags if d.get("severity") == 2})
        return errs, warns


def strict(client, rel, t0):
    path = client._normalize_local_path(rel)
    st = client.opened_files[path]
    v, uri = st.version, st.uri
    client._send_request_sync("textDocument/waitForDiagnostics", {"uri": uri, "version": v}, timeout=900)
    deadline = time.monotonic() + 30
    while client.opened_files[path].diagnostics_version < v and time.monotonic() < deadline:
        time.sleep(0.005)
    t = time.perf_counter() - t0
    diags = list(client.opened_files[path].diagnostics)
    stamped = client.opened_files[path].diagnostics_version
    # validation only, not timed: did anything for this version arrive after the reply?
    n_before = len(diags)
    time.sleep(1.0)
    late = len(client.opened_files[path].diagnostics) != n_before
    return t, lsp_msgs(diags), stamped == v, late


def check(client, rel, text):
    t0 = time.perf_counter()
    client.update_file_content(rel, text)
    d = client.get_diagnostics(rel, inactivity_timeout=120, max_timeout=600)
    t_lc = time.perf_counter() - t0
    lc = lsp_msgs(d)
    t_s, s, stamped, late = strict(client, rel, t0)
    return dict(t_lc=t_lc, lc_errs=lc[0], lc_warns=lc[1], t=t_s, errs=s[0], warns=s[1],
                stamped=stamped, late=late)


prior = [json.loads(l) for l in open(prior_path)]
out = open(out_path, "a")
for row in prior:
    ws, rel = row["ws"], row["rel"]
    src = (Path(ws) / rel).read_text(encoding="utf-8")
    edits, seen = [], set()
    for inp in groups[(ws, rel)]:
        code, mode = splice(src, inp)
        if code and code != src and code not in seen:
            seen.add(code); edits.append((code, mode, inp))
    edits = edits[:MAX_EDITS]
    if [m for _, m, _ in edits] != [e["mode"] for e in row["edits"]]:
        print("SKIP: edits do not match the prior replay for", rel, flush=True)
        continue
    client = LeanLSPClient(ws, initial_build=False, prevent_cache_get=True)
    t0 = time.perf_counter()
    client.open_file(rel)
    client.get_diagnostics(rel, inactivity_timeout=120, max_timeout=600)
    t_open, base, _, _ = strict(client, rel, t0)
    res, tres = [], []
    for code, mode, inp in edits:
        res.append(check(client, rel, as_compiled(code)))
    for code, mode, inp in edits:
        nd = (inp.get("new_declaration") or "").strip()
        i = code.find(nd) if nd else -1
        tres.append(check(client, rel, code[: i + len(nd)] + "\n") if (mode == "decl" and i >= 0) else None)
    client.close()
    early = sum(1 for r in res if (r["lc_errs"], r["lc_warns"]) != (r["errs"], r["warns"]))
    print(f"== {rel} open {t_open:.1f}s; strict s: {[round(r['t'], 1) for r in res]}; "
          f"leanclient early/wrong on {early}/{len(res)}; unstamped {sum(not r['stamped'] for r in res)}; "
          f"late {sum(r['late'] for r in res)}", flush=True)
    new = dict(row, lsp_open=t_open, baseline_lsp_errs=base[0], baseline_lsp_warns=base[1])
    new["edits"] = []
    for e, r, tr in zip(row["edits"], res, tres):
        e = dict(e, warm=r["t"], warm_errs=r["errs"], warm_warns=r["warns"], warm_lc=r["t_lc"],
                 lc_errs=r["lc_errs"], lc_warns=r["lc_warns"], stamped=r["stamped"], late=r["late"],
                 trunc=(tr["t"] if tr else None), trunc_errs=(tr["errs"] if tr else None),
                 trunc_warns=(tr["warns"] if tr else None))
        new["edits"].append(e)
    out.write(json.dumps(new) + "\n"); out.flush()
