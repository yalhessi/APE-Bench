"""Replay recorded lean_verify_edit calls: cold VerificationEngine vs a persistent LSP per file.

For each (workspace, file) group: cold-compile every recorded edit through the engine the tool
uses today, then open the file once in a Lean server and push each edit as a didChange.
Modes for the LSP:
  full  -- whole spliced file (what lean_verify_edit answers today)
  trunc -- declaration-mode edits only: the file cut right after the new declaration
Records wall time and the set of error messages for each, so equivalence can be checked.
"""
import asyncio, collections, glob, json, sys, time
from pathlib import Path

sys.path.insert(0, "src"); sys.path.insert(0, ".")
from ape.tasks.lean_tasks.formal_math.review.base import splice_declaration  # noqa: E402
from ape.toolkits.execute.lean.core.verification import VerificationEngine  # noqa: E402
from ape.toolkits.execute.lean.config import LeanVerifyToolConfig  # noqa: E402
from leanclient import LeanLSPClient  # noqa: E402

RUNS = sys.argv[1].split(",")
MAX_GROUPS = int(sys.argv[2]) if len(sys.argv) > 2 else 6
MAX_EDITS = int(sys.argv[3]) if len(sys.argv) > 3 else 8
OUT = Path(sys.argv[4]) if len(sys.argv) > 4 else Path("replay.jsonl")

groups = collections.defaultdict(list)
for run in RUNS:
    for conv in glob.glob(f".ape/runs/{run}/tasks/*/samples/*/attempts/*/claude_code_conversation_*.jsonl"):
        att = Path(conv).parent
        tgt = att / "workspaces/target"
        if not tgt.exists():
            continue
        ws = tgt.resolve()
        for line in open(conv):
            try:
                ev = json.loads(line)
            except Exception:
                continue
            cont = (ev.get("message") or {}).get("content")
            if not isinstance(cont, list):
                continue
            for c in cont:
                if c.get("type") == "tool_use" and c.get("name", "").endswith("lean_verify_edit"):
                    inp = c.get("input") or {}
                    if inp.get("path") and (inp.get("new_declaration") or inp.get("replacement") is not None):
                        groups[(str(ws), inp["path"].removeprefix("target/"))].append(inp)


def splice(src, inp):
    if inp.get("declaration_name") and inp.get("new_declaration"):
        code, err = splice_declaration(src, inp["declaration_name"], inp["new_declaration"], label="x")
        return code, "decl"
    ls, le, rep = inp.get("line_start"), inp.get("line_end"), inp.get("replacement")
    lines = src.split("\n")
    if not (isinstance(ls, int) and isinstance(le, int) and 1 <= ls <= le <= len(lines)):
        return None, "line"
    return "\n".join(lines[: ls - 1] + str(rep).split("\n") + lines[le:]), "line"


def errset(msgs):
    return sorted({str(m).strip() for m in msgs})


def lsp_errors(diags):
    return errset(d.get("message", "") for d in diags if d.get("severity", 1) == 1)


async def main():
    cfg = LeanVerifyToolConfig()
    eng = VerificationEngine(cfg)
    ranked = sorted(groups.items(), key=lambda kv: -len(kv[1]))
    out = OUT.open("a")
    done = 0
    for (ws, rel), inps in ranked:
        fp = Path(ws) / rel
        if not fp.is_file():
            continue
        src = fp.read_text(encoding="utf-8")
        edits = []
        for inp in inps:
            code, mode = splice(src, inp)
            if code and code != src:
                edits.append((code, mode, inp))
        # dedupe identical edits, keep order
        seen, uniq = set(), []
        for e in edits:
            if e[0] not in seen:
                seen.add(e[0]); uniq.append(e)
        edits = uniq[:MAX_EDITS]
        if len(edits) < 3:
            continue
        print(f"== {Path(ws).name[:20]} {rel} ({len(src.splitlines())} lines) edits={len(edits)}", flush=True)

        # cold, the current path (baseline file + each edit)
        cold = []
        for code in [src] + [e[0] for e in edits]:
            t = time.perf_counter()
            r = await eng.verify(code=code.strip(), working_dir=Path(ws), timeout=300)
            cold.append((time.perf_counter() - t, errset(m.data for m in r.errors), r.return_code))
        print("   cold s:", [round(c[0], 1) for c in cold], flush=True)

        # persistent server
        t = time.perf_counter()
        client = LeanLSPClient(ws, initial_build=False, prevent_cache_get=True)
        t_start = time.perf_counter() - t
        t = time.perf_counter()
        client.open_file(rel)
        d0 = client.get_diagnostics(rel, inactivity_timeout=120, max_timeout=600)
        t_open = time.perf_counter() - t
        warm = []
        for code, mode, inp in edits:
            t = time.perf_counter()
            client.update_file_content(rel, code)
            d = client.get_diagnostics(rel, inactivity_timeout=120, max_timeout=600)
            warm.append((time.perf_counter() - t, lsp_errors(d)))
        trunc = []
        for code, mode, inp in edits:
            if mode != "decl":
                trunc.append(None); continue
            nd = inp["new_declaration"].strip()
            i = code.find(nd)
            if i < 0:
                trunc.append(None); continue
            cut = code[: i + len(nd)] + "\n"
            t = time.perf_counter()
            client.update_file_content(rel, cut)
            d = client.get_diagnostics(rel, inactivity_timeout=120, max_timeout=600)
            trunc.append((time.perf_counter() - t, lsp_errors(d)))
        client.close()
        print(f"   lsp start {t_start:.1f}s open {t_open:.1f}s; edits s:", [round(w[0], 1) for w in warm], flush=True)
        print("   trunc s:", [round(x[0], 1) if x else None for x in trunc], flush=True)
        rec = dict(ws=ws, rel=rel, lines=len(src.splitlines()), lsp_start=t_start, lsp_open=t_open,
                   baseline_cold=cold[0][0], baseline_cold_errs=cold[0][1], baseline_lsp_errs=lsp_errors(d0),
                   edits=[dict(mode=m, cold=c[0], cold_errs=c[1], cold_rc=c[2], warm=w[0], warm_errs=w[1],
                               trunc=(tr[0] if tr else None), trunc_errs=(tr[1] if tr else None))
                          for (code, m, inp), c, w, tr in zip(edits, cold[1:], warm, trunc)])
        out.write(json.dumps(rec) + "\n"); out.flush()
        done += 1
        if done >= MAX_GROUPS:
            break


asyncio.run(main())
