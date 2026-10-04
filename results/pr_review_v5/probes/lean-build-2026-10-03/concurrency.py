"""K persistent Lean servers at once: latency, agreement and memory.

Each session is its own process with its own leanclient server (as one per attempt would be):
open `rel` in `ws`, strict-wait, push each text in `texts` in order with a strict wait, then sit
idle with the document open until released, so the driver can read memory with every server live.

  driver: concurrency.py drive <label> <spec.json> <out.json>
          spec = {"sessions": [{"ws": ..., "rel": ..., "texts": [...]}, ...]}
  session (spawned by the driver): concurrency.py session <spec.json> <i> <dir>
Memory is summed over every descendant of every session (lake serve, lean --server, workers) from
/proc/<pid>/smaps_rollup: Pss (shared pages divided among their mappers), Private_Dirty (heap),
and file-backed Private_Clean vs Shared_Clean (an .olean mapped by one process only, or by several).
"""
import json, os, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).parent
SETTLE = 60


def session(spec_path, i, d):
    sys.path.insert(0, "src"); sys.path.insert(0, ".")
    import urllib.parse
    from leanclient import LeanLSPClient as _Client

    class LeanLSPClient(_Client):
        """leanclient resolves symlinks when it builds a document URI, so a reviewed workspace's
        unchanged file (a symlink into the base) opens in the base's environment and its
        diagnostics never match the opened document. Keep the workspace's own path."""
        def __init__(self, ws, **kw):
            super().__init__(ws, **kw)
            self.project_path = Path(ws)

        def _local_to_uri(self, local_path):
            return urllib.parse.unquote((Path(self.project_path) / self._normalize_local_path(local_path)).absolute().as_uri())

        def _uri_to_local(self, uri):
            p = self._uri_to_abs(uri)
            try:
                return p.relative_to(self.project_path).as_posix()
            except ValueError:
                return p.as_posix()
    s = json.load(open(spec_path))["sessions"][int(i)]
    d = Path(d)
    strict_src = (HERE / "replay_server_strict.py").read_text()

    def lsp_msgs(diags):
        e = sorted({str(x.get("message", "")).strip() for x in diags if x.get("severity", 1) == 1})
        w = sorted({str(x.get("message", "")).strip() for x in diags if x.get("severity") == 2})
        return e, w
    g = {"time": time, "lsp_msgs": lsp_msgs}
    exec(compile(strict_src[strict_src.index("def strict("):strict_src.index("def check(")], "strict", "exec"), g)
    strict = g["strict"]
    (d / f"{i}.ready").write_text("")
    while not (d / "go").exists():
        time.sleep(0.05)
    t0 = time.perf_counter()
    c = LeanLSPClient(s["ws"], initial_build=False, prevent_cache_get=True)
    (d / f"{i}.pid").write_text(str(c.process.pid))
    c.open_file(s["rel"])
    t_open, base, _, _ = strict(c, s["rel"], t0)
    times, answers = [], []
    for text in s["texts"]:
        t = time.perf_counter()
        c.update_file_content(s["rel"], text)
        tt, msgs, stamped, _ = strict(c, s["rel"], t)
        times.append(tt); answers.append(msgs)
    json.dump(dict(open=t_open, times=times, answers=answers, base=base), open(d / f"{i}.json", "w"))
    (d / f"{i}.done").write_text("")
    while not (d / "release").exists():
        time.sleep(0.2)
    c.close()


def mem(pids):
    import psutil
    tot = dict(pss=0, private_dirty=0, private_clean=0, shared_clean=0, n=0)
    procs = []
    for p in pids:
        try:
            root = psutil.Process(p)
            procs += [root] + root.children(recursive=True)
        except psutil.NoSuchProcess:
            pass
    for pr in procs:
        try:
            for line in open(f"/proc/{pr.pid}/smaps_rollup"):
                k, v = line.split(":", 1)
                key = {"Pss": "pss", "Private_Dirty": "private_dirty", "Private_Clean": "private_clean",
                       "Shared_Clean": "shared_clean"}.get(k)
                if key:
                    tot[key] += int(v.split()[0]) * 1024
            tot["n"] += 1
        except (FileNotFoundError, ProcessLookupError, ValueError):
            pass
    return {k: (round(v / 2**30, 2) if k != "n" else v) for k, v in tot.items()}


def drive(label, spec_path, out_path):
    spec = json.load(open(spec_path))
    k = len(spec["sessions"])
    d = Path(out_path).with_suffix(".d"); d.mkdir(parents=True, exist_ok=True)
    for f in d.iterdir():
        f.unlink()
    procs = [subprocess.Popen([sys.executable, __file__, "session", spec_path, str(i), str(d)],
                              stdout=open(d / f"{i}.log", "w"), stderr=subprocess.STDOUT)
             for i in range(k)]
    while sum((d / f"{i}.ready").exists() for i in range(k)) < k:
        time.sleep(0.1)
    t = time.perf_counter()
    (d / "go").write_text("")
    while sum((d / f"{i}.done").exists() for i in range(k)) < k:
        if any(p.poll() not in (None, 0) for p in procs):
            print("a session failed; see", d); break
        time.sleep(0.5)
    wall = time.perf_counter() - t
    time.sleep(SETTLE)  # let every server finish loading its reference index before reading memory
    pids = [int((d / f"{i}.pid").read_text()) for i in range(k) if (d / f"{i}.pid").exists()]
    m = mem(pids)
    (d / "release").write_text("")
    for p in procs:
        p.wait(timeout=120)
    res = [json.load(open(d / f"{i}.json")) for i in range(k) if (d / f"{i}.json").exists()]
    import statistics as st
    opens = [r["open"] for r in res]
    edits = [t for r in res for t in r["times"]]
    agree = all(r["answers"] == res[0]["answers"] and r["base"] == res[0]["base"] for r in res)
    summary = dict(label=label, k=k, sessions_ok=len(res), wall=round(wall, 1),
                   open_median=round(st.median(opens), 1), open_max=round(max(opens), 1),
                   edit_median=round(st.median(edits), 2) if edits else None,
                   edit_max=round(max(edits), 1) if edits else None,
                   identical_answers=agree, mem=m)
    print(json.dumps(summary), flush=True)
    with open(out_path, "a") as f:
        f.write(json.dumps(summary) + "\n")


if __name__ == "__main__":
    if sys.argv[1] == "session":
        session(*sys.argv[2:5])
    else:
        drive(*sys.argv[2:5])
