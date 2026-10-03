"""Replay recorded lean_verify_edit calls: the cold engine vs one persistent Lean server per file.

v2 (2026-10-03): run from the worktree whose run is replayed, so the splice, the cold compile's
options and its newline handling are that branch's own. Records warnings as well as errors, and
whether the edit is one the truncation rule may cut (a theorem whose statement is unchanged).

For each (workspace, file): cold-check the file and every recorded edit through `VerificationEngine`
as `lean_verify_edit` calls it, then open the file once in a Lean server and push each edit as a
didChange. Modes:
  full  -- the whole spliced file (what lean_verify_edit answers today)
  trunc -- declaration-mode edits: the file cut right after the new declaration
Usage: replay_bench_v2.py <run[,run]> <max_groups> <max_edits> <out.jsonl>
"""
import asyncio, collections, glob, json, re, sys, time
from pathlib import Path

sys.path.insert(0, "src"); sys.path.insert(0, ".")
import ape.tasks.lean_tasks.formal_math.review.base as review_base  # noqa: E402
from ape.toolkits.execute.lean.core.verification import VerificationEngine  # noqa: E402
from ape.toolkits.execute.lean.config import LeanVerifyToolConfig  # noqa: E402
from ape.toolkits.code.lean.lean_parser import parse_major_declarations  # noqa: E402
from leanclient import LeanLSPClient  # noqa: E402

splice_declaration = review_base.splice_declaration
WHOLE_FILE_OPTIONS = getattr(review_base, "WHOLE_FILE_OPTIONS", None)
# The branch's `execute` keeps one final newline; develop's strips it.
DELETES_SPAN = "if replacement else []" in Path("src/ape/tasks/lean_tasks/formal_math/review/base.py").read_text()
KEEPS_NEWLINE = "code = code.strip() + \"\\n\"" in Path("src/ape/toolkits/execute/lean/tools.py").read_text()

RUNS = sys.argv[1].split(",")
MAX_GROUPS = int(sys.argv[2]) if len(sys.argv) > 2 else 7
MAX_EDITS = int(sys.argv[3]) if len(sys.argv) > 3 else 8
OUT = Path(sys.argv[4]) if len(sys.argv) > 4 else Path("replay.jsonl")

groups = collections.defaultdict(list)
asis = collections.Counter()
for run in RUNS:
    for conv in glob.glob(f".ape/runs/{run}/tasks/*/samples/*/attempts/*/claude_code_conversation_*.jsonl"):
        att = Path(conv).parent
        tgt = att / "workspaces/target"
        if not tgt.exists():
            continue
        ws = tgt.resolve()
        for line in open(conv, errors="replace"):
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
                    if not inp.get("path"):
                        continue
                    key = (str(ws), inp["path"].removeprefix("target/"))
                    if inp.get("new_declaration") or inp.get("line_start") is not None:
                        groups[key].append(inp)
                    else:
                        asis[key] += 1


def splice(src, inp):
    """The branch's `_edited_file_code`, minus the file read."""
    if inp.get("declaration_name") and inp.get("new_declaration"):
        code, err = splice_declaration(src, inp["declaration_name"], inp["new_declaration"], label="x")
        return code, "decl"
    ls, le, rep = inp.get("line_start"), inp.get("line_end"), inp.get("replacement")
    lines = src.split("\n")
    if not (isinstance(ls, int) and isinstance(le, int) and 1 <= ls <= le <= len(lines)):
        return None, "line"
    body = (str(rep).split("\n") if rep else []) if DELETES_SPAN else str(rep).split("\n")
    return "\n".join(lines[: ls - 1] + body + lines[le:]), "line"


def as_compiled(code):
    return code.strip() + "\n" if KEEPS_NEWLINE else code.strip()


_norm = lambda s: re.sub(r"\s+", " ", s).strip().removesuffix(":=").strip()  # noqa: E731


def trunc_sound(src_decls, inp):
    """True when the edit is a theorem whose statement is unchanged: nothing after it can change."""
    if not inp.get("new_declaration"):
        return False
    name = inp["declaration_name"]
    olds = [d for d in src_decls if d.name and (d.name == name or name.endswith("." + d.name))]
    news = parse_major_declarations(inp["new_declaration"])
    if not olds or not news or olds[0].kind not in ("theorem", "lemma"):
        return False
    return _norm(olds[0].signature) == _norm(news[0].signature)


def first_changed_line(a, b):
    la, lb = a.split("\n"), b.split("\n")
    for i, (x, y) in enumerate(zip(la, lb)):
        if x != y:
            return i + 1
    return min(len(la), len(lb))


def msgs(items, sev):
    return sorted({str(m).strip() for s, m in items if s == sev})


def lsp_msgs(diags):
    sev = {1: "error", 2: "warning", 3: "info", 4: "hint"}
    items = [(sev.get(d.get("severity", 1)), d.get("message", "")) for d in diags]
    return msgs(items, "error"), msgs(items, "warning")


async def main():
    eng = VerificationEngine(LeanVerifyToolConfig())
    opts = WHOLE_FILE_OPTIONS or None
    print(f"branch: WHOLE_FILE_OPTIONS={WHOLE_FILE_OPTIONS} keeps_newline={KEEPS_NEWLINE} deletes_span={DELETES_SPAN}", flush=True)
    ranked = sorted(groups.items(), key=lambda kv: -len(kv[1]))
    out = OUT.open("a")
    done = 0
    for (ws, rel), inps in ranked:
        fp = Path(ws) / rel
        if not fp.is_file():
            continue
        src = fp.read_text(encoding="utf-8")
        decls = parse_major_declarations(src)
        edits, seen = [], set()
        for inp in inps:
            code, mode = splice(src, inp)
            if code and code != src and code not in seen:
                seen.add(code)
                edits.append((code, mode, inp))
        edits = edits[:MAX_EDITS]
        if len(edits) < 3:
            continue
        print(f"== {Path(ws).name[:20]} {rel} ({len(src.splitlines())} lines) edits={len(edits)} as-is calls={asis[(ws, rel)]}", flush=True)

        cold = []
        for code in [src] + [e[0] for e in edits]:
            t = time.perf_counter()
            r = await eng.verify(code=as_compiled(code), working_dir=Path(ws), timeout=300, options=opts)
            items = [(m.severity, m.data) for m in r.messages]
            cold.append((time.perf_counter() - t, msgs(items, "error"), msgs(items, "warning"), r.return_code))
        print("   cold s:", [round(c[0], 1) for c in cold], flush=True)

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
            client.update_file_content(rel, as_compiled(code))
            d = client.get_diagnostics(rel, inactivity_timeout=120, max_timeout=600)
            warm.append((time.perf_counter() - t, *lsp_msgs(d)))
        trunc = []
        for code, mode, inp in edits:
            nd = (inp.get("new_declaration") or "").strip()
            i = code.find(nd) if nd else -1
            if mode != "decl" or i < 0:
                trunc.append(None)
                continue
            t = time.perf_counter()
            client.update_file_content(rel, code[: i + len(nd)] + "\n")
            d = client.get_diagnostics(rel, inactivity_timeout=120, max_timeout=600)
            trunc.append((time.perf_counter() - t, *lsp_msgs(d)))
        client.close()
        print(f"   lsp start {t_start:.1f}s open {t_open:.1f}s; edits s:", [round(w[0], 1) for w in warm], flush=True)
        print("   trunc s:", [round(x[0], 1) if x else None for x in trunc],
              "sound:", [trunc_sound(decls, e[2]) for e in edits], flush=True)
        base_err, base_warn = lsp_msgs(d0)
        rec = dict(ws=ws, rel=rel, lines=len(src.splitlines()), asis_calls=asis[(ws, rel)],
                   lsp_start=t_start, lsp_open=t_open, baseline_cold=cold[0][0],
                   baseline_cold_errs=cold[0][1], baseline_cold_warns=cold[0][2],
                   baseline_lsp_errs=base_err, baseline_lsp_warns=base_warn,
                   edits=[dict(mode=m, first_line=first_changed_line(src, code),
                               trunc_sound=trunc_sound(decls, inp),
                               cold=c[0], cold_errs=c[1], cold_warns=c[2], cold_rc=c[3],
                               warm=w[0], warm_errs=w[1], warm_warns=w[2],
                               trunc=(tr[0] if tr else None), trunc_errs=(tr[1] if tr else None),
                               trunc_warns=(tr[2] if tr else None))
                          for (code, m, inp), c, w, tr in zip(edits, cold[1:], warm, trunc)])
        out.write(json.dumps(rec) + "\n"); out.flush()
        done += 1
        if done >= MAX_GROUPS:
            break


asyncio.run(main())
