"""Farm build with Lake's own rebuild set: materialize a module only when Lake needs to write it.

Start from a farm in which only the changed modules have no build files. Run the targeted
`lake build`. If Lake must rebuild a module whose files are still symlinks into the base, its
write hits the base's 444 inode and the build fails naming the file; that module's links are
removed and the build resumes (Lake skips what it already built). The base is never written.
Usage: farm_iterative.py <base> <reviewed> <new root>
"""
import os, re, subprocess, sys, time
from pathlib import Path

here = Path(__file__).parent
src = (here / "farm_build.py").read_text()
# reuse the import-graph and farm code, with the rebuild prediction replaced by the changed set
src = src.replace("rebuild = sorted(m for m in closure if reaches(m))", "rebuild = sorted(changed)  # iterative: start minimal")
src = src[:src.index("# 4. The same targeted build")]
exec(compile(src, "farm_build", "exec"))
predicted_superset = sorted(m for m in closure if reaches(m))
print(f"import-graph superset would be {len(predicted_superset)} modules; starting from the {len(rebuild)} changed")

build = N / ".lake/build"
materialized = set(rebuild)
targets = ["+" + m for m in changed]
t_build = 0.0
for it in range(1, 200):
    t = time.perf_counter()
    p = subprocess.run(["lake", "build", *targets], cwd=N, capture_output=True, text=True)
    t_build += time.perf_counter() - t
    if p.returncode == 0:
        print(f"iteration {it}: build ok; cumulative build time {t_build:.0f}s")
        break
    out = p.stdout + p.stderr
    hits = set(re.findall(r"\.lake/build/(?:lib/lean|ir)/(Mathlib/[\w/'.«»]+?)\.(?:olean|ilean|ir|c|trace|setup)", out))
    blocked = {h.replace("/", ".") for h in hits} - materialized
    denied = "ermission denied" in out or "EACCES" in out or "read-only" in out.lower()
    if not blocked:
        print(f"iteration {it}: failed with nothing to materialize (denied={denied}):\n", out[-2500:])
        break
    for m in sorted(blocked):
        rel = m.replace(".", "/")
        for sub in ("lib/lean", "ir"):
            d = build / sub / Path(rel).parent
            # make sure the directory itself is real, then drop this module's links
            parts = Path(sub, rel).parent.parts
            cur = build
            for part in parts:
                nxt = cur / part
                if nxt.is_symlink():
                    target = nxt.resolve(); nxt.unlink(); nxt.mkdir()
                    for e in target.iterdir():
                        (nxt / e.name).symlink_to(e)
                cur = nxt
            for e in d.iterdir() if d.exists() else []:
                if e.is_symlink() and e.name.split(".", 1)[0] == Path(rel).name:
                    e.unlink()
        materialized.add(m)
    print(f"iteration {it}: materialized {sorted(blocked)} (denied={denied})")
else:
    print("gave up")

written = sorted({str(q.relative_to(build)) for q in build.rglob("*") if q.is_file() and not q.is_symlink()})
mods = sorted({re.sub(r"^(lib/lean|ir)/", "", w).split(".", 1)[0].replace("/", ".") for w in written if w.startswith(("lib/lean/", "ir/"))})
print(f"Lake wrote {len(written)} files for {len(mods)} modules; materialized {len(materialized)}; "
      f"real bytes {sum((build / w).stat().st_size for w in written) / 1e6:.1f} MB")
same = sum((build / w).read_bytes() == (R / '.lake/build' / w).read_bytes() for w in written if (R / '.lake/build' / w).exists())
print(f"byte-identical to the copied reviewed workspace: {same}/{len(written)}")
p = subprocess.run(["lake", "build", "--no-build", *targets], cwd=N, capture_output=True, text=True)
print("lake build --no-build:", p.returncode, (p.stdout + p.stderr).strip().splitlines()[-1:])
