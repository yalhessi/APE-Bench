"""Build a reviewed workspace without copying `.lake/build`: a symlink farm into the base.

The current design copies the base's whole `.lake/build` (2.7-2.8 GB, ~10 min on NFS) before a
targeted `lake build`, because Lean rewrites some artifacts in place and "the set it rewrites is not
knowable before the build runs". This tests whether it is knowable: the modules Lake rebuilds are the
changed modules and the modules between them on the import graph, which the patched sources give.

Layout of the new root N:
  N/<every top-level entry>   symlink to the existing reviewed workspace R's source overlay
  N/.lake/config, packages    symlinks into the base (as R has them)
  N/.lake/build               real directories only on the paths to rebuilt modules; every other
                              entry a symlink into the base's build; no entry at all for the files
                              of a module predicted to be rebuilt.
A wrong prediction cannot corrupt the base: writing through a symlink hits the base's 444 inode.

Usage: farm_build.py <base> <reviewed> <new root>
"""
import json, os, re, subprocess, sys, time
from pathlib import Path

B, R, N = (Path(p).resolve() for p in sys.argv[1:4])
assert not N.exists(), N
t_all = time.perf_counter()

# 1. The changed sources: real files inside R's source overlay (everything else is a symlink).
changed = []
for root, dirs, files in os.walk(R / "Mathlib"):
    dirs[:] = [d for d in dirs if not (Path(root) / d).is_symlink()]
    for f in files:
        p = Path(root) / f
        if f.endswith(".lean") and not p.is_symlink():
            changed.append(p.relative_to(R).with_suffix("").as_posix().replace("/", "."))
print("changed modules:", changed)

# 2. Import graph from the patched sources, Mathlib modules only (packages cannot import Mathlib).
IMPORT = re.compile(r"^\s*(?:public\s+|private\s+)?(?:meta\s+)?import\s+([\w.'«»]+)")
_imports = {}


def imports(mod):
    if mod not in _imports:
        path = R / (mod.replace(".", "/") + ".lean")
        out, depth = [], 0
        for line in path.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if depth:
                depth += s.count("/-") - s.count("-/")
                continue
            if s.startswith("/-"):
                depth = s.count("/-") - s.count("-/")
                continue
            if not s or s.startswith("--") or s == "module" or s.startswith("prelude"):
                continue
            m = IMPORT.match(line)
            if not m:
                break
            out.append(m.group(1))
        _imports[mod] = [i for i in out if i.startswith("Mathlib.")]
    return _imports[mod]


closure, stack = set(), list(changed)
while stack:
    m = stack.pop()
    if m in closure:
        continue
    closure.add(m)
    stack.extend(imports(m))
_reach = {}


def reaches(m):
    if m not in _reach:
        _reach[m] = False
        _reach[m] = m in changed or any(reaches(i) for i in imports(m))
    return _reach[m]


rebuild = sorted(m for m in closure if reaches(m))
print(f"closure {len(closure)} modules; predicted rebuild {len(rebuild)}:", rebuild)

# 3. The farm.
t = time.perf_counter()
N.mkdir(parents=True)
for entry in R.iterdir():
    if entry.name != ".lake":
        (N / entry.name).symlink_to(entry)
(N / ".lake").mkdir()
for child in (B / ".lake").iterdir():
    if child.name != "build":
        (N / ".lake" / child.name).symlink_to(child)

rebuild_paths = {m.replace(".", "/") for m in rebuild}            # Mathlib/A/B
on_path = {str(Path(p).parent.joinpath(*[])) for p in rebuild_paths}
dirs_needed = set()
for p in rebuild_paths:
    parts = Path(p).parts
    for k in range(1, len(parts)):
        dirs_needed.add("/".join(parts[:k]))
n_links = n_dirs = 0


def farm(base_dir: Path, new_dir: Path, rel: str):
    """`rel` is the module-path prefix of this directory ('' at lib/lean or ir)."""
    global n_links, n_dirs
    new_dir.mkdir(exist_ok=True); n_dirs += 1
    for e in base_dir.iterdir():
        sub = f"{rel}/{e.name}" if rel else e.name
        if e.is_dir() and not e.is_symlink() and sub in dirs_needed:
            farm(e, new_dir / e.name, sub)
            continue
        stem = e.name.split(".", 1)[0]
        if e.is_file() and f"{rel}/{stem}" in rebuild_paths:
            continue                                                  # Lake writes these
        (new_dir / e.name).symlink_to(e); n_links += 1


build = N / ".lake/build"; build.mkdir(); n_dirs += 1
for top in (B / ".lake/build").iterdir():
    if top.name == "lib":
        (build / "lib").mkdir(); n_dirs += 1
        for e in top.iterdir():
            if e.name == "lean":
                farm(e, build / "lib/lean", "")
            else:
                (build / "lib" / e.name).symlink_to(e); n_links += 1
    elif top.name == "ir":
        farm(top, build / "ir", "")
    else:
        (build / top.name).symlink_to(top); n_links += 1
t_farm = time.perf_counter() - t
print(f"farm: {n_dirs} real dirs, {n_links} symlinks, {t_farm:.1f}s")

# 4. The same targeted build the current prebuild runs.
targets = ["+" + m for m in changed]
t = time.perf_counter()
p = subprocess.run(["lake", "build", *targets], cwd=N, capture_output=True, text=True)
t_build = time.perf_counter() - t
print(f"lake build rc={p.returncode} in {t_build:.0f}s")
if p.returncode:
    print((p.stdout + p.stderr)[-3000:])

# 5. What Lake wrote: real files under the farm, by module.
written = []
for root, dirs, files in os.walk(build):
    dirs[:] = [d for d in dirs if not (Path(root) / d).is_symlink()]
    for f in files:
        q = Path(root) / f
        if not q.is_symlink():
            written.append(q.relative_to(build).as_posix())
mods_written = sorted({re.sub(r"^(lib/lean|ir)/", "", w).split(".", 1)[0].replace("/", ".")
                       for w in written if w.startswith(("lib/lean/", "ir/"))})
print(f"Lake wrote {len(written)} files; modules: {mods_written}")
print("predicted == written modules:", set(mods_written) == set(rebuild),
      "| unpredicted:", sorted(set(mods_written) - set(rebuild)), "| predicted, not written:",
      sorted(set(rebuild) - set(mods_written)))
other = [w for w in written if not w.startswith(("lib/lean/", "ir/"))]
print("other files written:", other)
same = diff = 0
diffs = []
for w in written:
    a, b = build / w, R / ".lake/build" / w
    if b.exists() and a.read_bytes() == b.read_bytes():
        same += 1
    else:
        diff += 1; diffs.append(w)
print(f"byte-identical to the copied reviewed workspace: {same}/{len(written)}; differ: {diffs[:12]}")
real_bytes = sum((build / w).stat().st_size for w in written)
print(f"real bytes in the farm: {real_bytes/1e6:.1f} MB; total {time.perf_counter()-t_all:.0f}s")
json.dump(dict(changed=changed, rebuild=rebuild, written=written, t_farm=t_farm, t_build=t_build,
               n_links=n_links, n_dirs=n_dirs), open(N.parent / (N.name + ".json"), "w"))
