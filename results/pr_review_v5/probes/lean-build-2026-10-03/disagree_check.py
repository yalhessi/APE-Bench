"""Separate option effects from incremental-server effects on the edits where cold and server disagree.

For each chosen edit of one replay group, check the edited text four ways:
  cold      -- the branch's cold path (`lake env lean`, the tool's -D options)
  setup     -- a fresh process with the server's own options: `lean --setup <lake setup-file json>`
  server    -- the persistent server after didChange (as in the replay), and again after a 20 s wait
Usage (from the replayed worktree): disagree_check.py <run> <file-suffix> <edit indices>
"""
import asyncio, json, os, subprocess, sys, tempfile, time
from pathlib import Path

script = Path(__file__).with_name("replay_bench_v2.py").read_text().replace("asyncio.run(main())", "")
sys.argv = ["x", sys.argv[1], "0", "8", "/dev/null"] + sys.argv[2:]
want_file, want = sys.argv[5], [int(x) for x in sys.argv[6].split(",")]
exec(compile(script, "replay_bench_v2", "exec"))

(ws, rel), inps = next(((k, v) for k, v in groups.items() if k[1].endswith(want_file)))
src = (Path(ws) / rel).read_text(encoding="utf-8")
edits, seen = [], set()
for inp in inps:
    code, mode = splice(src, inp)
    if code and code != src and code not in seen:
        seen.add(code); edits.append((code, mode, inp))
edits = edits[:MAX_EDITS]

env = dict(os.environ)
lean_path = subprocess.run(["lake", "env", "printenv", "LEAN_PATH"], cwd=ws, capture_output=True, text=True).stdout.strip()
setup = subprocess.run(["lake", "setup-file", "--no-build", rel], cwd=ws, capture_output=True, text=True).stdout
setup_file = Path(tempfile.mkdtemp()) / "setup.json"; setup_file.write_text(setup)
print("server options:", json.loads(setup)["options"])


def summary(errs, warns):
    return f"{len(errs)} err, {len(warns)} warn"


def fresh_setup(code):
    with tempfile.NamedTemporaryFile("w", suffix=".lean", delete=False) as f:
        f.write(as_compiled(code))
    out = subprocess.run(["lean", f"--setup={setup_file}", "--json", f.name], cwd=ws,
                         env={**env, "LEAN_PATH": lean_path}, capture_output=True, text=True).stdout
    items = [(m["severity"], m["data"]) for m in map(json.loads, filter(None, out.splitlines()))]
    return msgs(items, "error"), msgs(items, "warning")


async def main():
    eng = VerificationEngine(LeanVerifyToolConfig())
    client = LeanLSPClient(ws, initial_build=False, prevent_cache_get=True)
    client.open_file(rel)
    client.get_diagnostics(rel, inactivity_timeout=120, max_timeout=600)
    for i in want:
        code, mode, inp = edits[i]
        r = await eng.verify(code=as_compiled(code), working_dir=Path(ws), timeout=300, options=WHOLE_FILE_OPTIONS or None)
        items = [(m.severity, m.data) for m in r.messages]
        cold = (msgs(items, "error"), msgs(items, "warning"))
        setup_res = fresh_setup(code)
        client.update_file_content(rel, as_compiled(code))
        s1 = lsp_msgs(client.get_diagnostics(rel, inactivity_timeout=120, max_timeout=600))
        time.sleep(20)
        s2 = lsp_msgs(client.get_diagnostics(rel, inactivity_timeout=120, max_timeout=600))
        print(f"edit {i} ({mode}, first changed line {first_changed_line(src, code)}): cold {summary(*cold)} | "
              f"setup {summary(*setup_res)} | server {summary(*s1)} | server+20s {summary(*s2)}")
        pp = lambda xs: {x.replace('↦', '=>') for x in xs}  # noqa: E731
        print("   setup vs cold   errs only-cold", sorted(pp(cold[0]) - pp(setup_res[0]))[:2], "only-setup", sorted(pp(setup_res[0]) - pp(cold[0]))[:2])
        print("   setup vs server warns only-setup", [w[:90] for w in sorted(pp(setup_res[1]) - pp(s2[1]))][:4],
              "only-server", [w[:90] for w in sorted(pp(s2[1]) - pp(setup_res[1]))][:4])
    client.close()


asyncio.run(main())
