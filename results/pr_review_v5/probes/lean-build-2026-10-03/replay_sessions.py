"""One design for lean_verify and lean_verify_edit: replay whole sessions through one server.

Each recorded session's calls -- snippet probes (`lean_verify`), edits and as-is checks
(`lean_verify_edit`) -- are replayed in their recorded order through ONE Lean server on that
session's reviewed workspace, holding a pool of documents keyed by import header:
  * the reviewed file's own document, at its own path, pinned;
  * a snippet goes to the document for its header (a path under Scratch/ that does not exist);
  * an edit is routed as in replay_policy.py: cut / whole file on the file's document; an import
    edit goes to the document for its new header, like a snippet;
  * an as-is check is answered by the file document's diagnostics.
At most CAP documents are open; the least recently used non-pinned one is closed. Every call is
also run through the branch's cold path, and errors are compared (`=>`/`↦` normalised).
Usage (cwd: the replayed tree): replay_sessions.py <run> <out.jsonl> [cap]
"""
import asyncio, glob, hashlib, json, re, sys, time, urllib.parse
from collections import OrderedDict
from pathlib import Path

here = Path(__file__).parent
RUN, OUT = sys.argv[1], Path(sys.argv[2])
CAP = int(sys.argv[3]) if len(sys.argv) > 3 else 3

ns_text = (here / "replay_bench_v2.py").read_text().replace("asyncio.run(main())", "")
sys.argv_saved = list(sys.argv)
sys.argv = ["x", RUN, "0", "8", "/dev/null"]
exec(compile(ns_text, "replay_bench_v2", "exec"))  # splice, as_compiled, msgs, WHOLE_FILE_OPTIONS, engine imports
OUT = Path(sys.argv_saved[2])  # the exec above rebinds OUT to its own (/dev/null) argument
from ape.toolkits.code.lean.lean_parser import parse_major_declarations  # noqa: E402
from ape.toolkits.code.lean.provider import LeanCodeToolsProvider  # noqa: E402
nocomment = LeanCodeToolsProvider.remove_comments
cls_src = (here / "classify_edits.py").read_text()
exec(compile(cls_src[cls_src.index("DELETES_SPAN = "):cls_src.index("runs = sys.argv[1]")]
             .replace("def splice(src, inp):", "def _unused(src, inp):"), "classify", "exec"))
CUT = ("proof_only", "comment_only", "stmt_unused")
pol_src = (here / "replay_policy.py").read_text()
exec(compile(pol_src[pol_src.index("def cut_point("):pol_src.index("\nprior = [json.loads")], "cut", "exec"))
from leanclient import LeanLSPClient as _C  # noqa: E402
from leanclient.file_manager import FileState  # noqa: E402

HEADER = re.compile(r"\A(?:\s|/-.*?-/|--[^\n]*\n)*(?:module\s*\n)?(?:(?:\s|--[^\n]*\n)*(?:public\s+|private\s+)?(?:meta\s+)?import\s+\S+[^\n]*\n)*", re.S)


def header_of(text):
    return re.sub(r"\s+", " ", nocomment(HEADER.match(text).group(0))).strip()


class Server(_C):
    """leanclient with the two fixes: unresolved workspace paths, and a strict version wait."""
    def __init__(self, ws):
        super().__init__(ws, initial_build=False, prevent_cache_get=True)
        self.project_path = Path(ws)

    def _local_to_uri(self, p):
        q = Path(self._normalize_local_path(p))
        return urllib.parse.unquote((q if q.is_absolute() else Path(self.project_path) / q).absolute().as_uri())

    def _uri_to_local(self, uri):
        p = self._uri_to_abs(uri)
        try:
            return p.relative_to(self.project_path).as_posix()
        except ValueError:
            return p.as_posix()

    def open_text(self, path, text):
        uri = self._local_to_uri(path)
        key = self._uri_to_local(uri)
        with self._opened_files_lock:
            self.opened_files[key] = FileState(uri=uri, content=text, version=0)
        self._send_notification("textDocument/didOpen", {"textDocument": {
            "uri": uri, "languageId": "lean", "version": 0, "text": text}, "dependencyBuildMode": "never"})
        return key

    def strict(self, key):
        st = self.opened_files[key]
        self._send_request_sync("textDocument/waitForDiagnostics", {"uri": st.uri, "version": st.version}, timeout=900)
        t0 = time.monotonic()
        while self.opened_files[key].diagnostics_version < st.version and time.monotonic() - t0 < 30:
            time.sleep(0.005)
        d = self.opened_files[key].diagnostics
        sev = {1: "error", 2: "warning", 3: "information"}
        items = [(sev.get(x.get("severity", 1)), x.get("message", "")) for x in d]
        return msgs(items, "error"), msgs(items, "warning"), msgs(items, "information")

    def set_text(self, key, text):
        if self.opened_files[key].content != text:
            self.update_file_content(key, text)
        return self.strict(key)


def sessions():
    for conv in sorted(glob.glob(f".ape/runs/{RUN}/tasks/*/samples/*/attempts/*/claude_code_conversation_*.jsonl")):
        tgt = Path(conv).parent / "workspaces/target"
        if not tgt.exists():
            continue
        calls = []
        for line in open(conv, errors="replace"):
            try:
                ev = json.loads(line)
            except Exception:
                continue
            cont = (ev.get("message") or {}).get("content")
            if not isinstance(cont, list):
                continue
            for x in cont:
                if x.get("type") != "tool_use":
                    continue
                name, inp = x.get("name", ""), x.get("input") or {}
                if name.endswith("__lean_verify") and inp.get("code"):
                    calls.append(("snippet", inp))
                elif name.endswith("__lean_verify_edit") and inp.get("path"):
                    calls.append(("edit", inp))
        import os
        if os.environ.get("WS_FILTER") and not any(f in str(tgt.resolve()) for f in os.environ["WS_FILTER"].split(",")):
            continue
        if any(k == "snippet" for k, _ in calls):
            yield conv, tgt.resolve(), calls


async def main():
    eng = VerificationEngine(LeanVerifyToolConfig())
    out = OUT.open("a")
    for conv, ws, calls in sessions():
        srv = Server(str(ws))
        pool = OrderedDict()          # header -> (doc key, pinned)
        file_docs, n_scratch, rows = {}, [0], []

        def doc_for(header, path_hint, text, pinned=False):
            if header in pool:
                pool.move_to_end(header)
                return pool[header][0], False
            while len(pool) >= CAP:
                victim = next((h for h, (k, p) in pool.items() if not p), None)
                if victim is None:
                    break
                k, _ = pool.pop(victim)
                srv.close_files([k], blocking=False)
            if path_hint is None:
                n_scratch[0] += 1
                path_hint = f"Scratch/Probe{n_scratch[0]}.lean"
            key = srv.open_text(path_hint, text)
            pool[header] = (key, pinned)
            return key, True

        for kind, inp in calls:
            row = dict(kind=kind)
            if kind == "snippet":
                code = inp["code"].strip() + "\n"
                t = time.perf_counter()
                r = await eng.verify(code=code, working_dir=ws, timeout=300)
                row["cold"] = time.perf_counter() - t
                items = [(m.severity, m.data) for m in r.messages]
                cold = (msgs(items, "error"), msgs(items, "warning"))
                t = time.perf_counter()
                key, opened = doc_for(header_of(code), None, code)
                res = srv.strict(key) if opened else srv.set_text(key, code)
                row.update(server=time.perf_counter() - t, route="snippet:open" if opened else "snippet:warm")
            else:
                rel = inp["path"].removeprefix("target/")
                fp = ws / rel
                if not fp.is_file():
                    continue
                src = fp.read_text(encoding="utf-8")
                code, mode = splice(src, inp) if (inp.get("new_declaration") or inp.get("line_start") is not None) else (src, "as_is")
                if code is None:
                    continue
                t = time.perf_counter()
                r = await eng.verify(code=as_compiled(code), working_dir=ws, timeout=300, options=WHOLE_FILE_OPTIONS or None)
                row["cold"] = time.perf_counter() - t
                items = [(m.severity, m.data) for m in r.messages]
                cold = (msgs(items, "error"), msgs(items, "warning"))
                t = time.perf_counter()
                if rel not in file_docs:
                    file_docs[rel], _ = doc_for(header_of(src), rel, as_compiled(src), pinned=True)
                    file_docs[rel + "#base"] = srv.strict(file_docs[rel])
                fkey = file_docs[rel]
                if mode == "as_is":
                    res, route = file_docs[rel + "#base"], "as_is:baseline"
                else:
                    c = classify(src, code, parse_major_declarations(src))
                    if c == "header":
                        key, opened = doc_for(header_of(code), None, as_compiled(code))
                        res = srv.strict(key) if opened else srv.set_text(key, as_compiled(code))
                        route = "header:open" if opened else "header:warm"
                    elif c in CUT:
                        res, route = srv.set_text(fkey, code[:cut_point(src, code)].rstrip() + "\n"), "cut"
                    else:
                        res, route = srv.set_text(fkey, as_compiled(code)), "whole"
                row.update(server=time.perf_counter() - t, route=route)
            pp = lambda xs: {x.replace("↦", "=>") for x in xs}  # noqa: E731
            if row["route"] == "cut":
                row["agree"] = bool(cold[0]) == bool(res[0])
            else:
                row["agree"] = pp(cold[0]) == pp(res[0])
            row["cold_errors"], row["server_errors"] = len(cold[0]), len(res[0])
            if not row["agree"]:
                row["cold_error_texts"], row["server_error_texts"] = sorted(cold[0]), sorted(res[0])
            rows.append(row)
        srv.close()
        print(f"== {Path(conv).parent.parent.parent.parent.name[:10]} {ws.name[:20]}: {len(rows)} calls, "
              f"{sum(r['kind'] == 'snippet' for r in rows)} snippets; cold {sum(r['cold'] for r in rows):.0f}s, "
              f"server {sum(r['server'] for r in rows):.0f}s; agree {sum(r['agree'] for r in rows)}/{len(rows)}", flush=True)
        out.write(json.dumps(dict(session=conv, ws=str(ws), rows=rows)) + "\n"); out.flush()


asyncio.run(main())
