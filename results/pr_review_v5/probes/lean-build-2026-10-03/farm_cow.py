"""Farm build in one Lake pass: real copies for every module Lake might rewrite, links for the rest.

The refusal loop (`farm_iterative.py`) learns Lake's rebuild set one layer per Lake pass, which is
slow when a PR touches a foundational module (33321 changes Algebra/Group/Hom/Basic). Here every
module in the import-graph superset -- the changed modules and every module between them and a
target -- gets *real copies* of the base's build files instead of links. Lake rewrites in one pass
exactly what its traces say is stale, the rest of the superset stays byte-identical to the base,
and no link into the base is ever written through. New modules (absent from the base) simply have
no files yet.
Usage: farm_cow.py <base> <reviewed> <new root>
"""
import os, re, shutil, subprocess, sys, time
from pathlib import Path

here = Path(__file__).parent
src = (here / "farm_build.py").read_text()
src = src[:src.index("# 3. The farm.")]
exec(compile(src, "farm_build", "exec"))         # B, R, N, changed, imports, closure, reaches
superset = sorted(m for m in closure if reaches(m))
print(f"changed {len(changed)}; superset {len(superset)} modules")

t = time.perf_counter()
N.mkdir(parents=True)
for entry in R.iterdir():
    if entry.name != ".lake":
        (N / entry.name).symlink_to(entry)
(N / ".lake").mkdir()
for child in (B / ".lake").iterdir():
    if child.name != "build":
        (N / ".lake" / child.name).symlink_to(child)
paths = {m.replace(".", "/") for m in superset}
dirs_needed = {"/".join(Path(p).parts[:k]) for p in paths for k in range(1, len(Path(p).parts))}
n_links = n_copies = copied_bytes = 0


def farm(base_dir, new_dir, rel):
    global n_links, n_copies, copied_bytes
    new_dir.mkdir(exist_ok=True)
    for e in base_dir.iterdir():
        sub = f"{rel}/{e.name}" if rel else e.name
        if e.is_dir() and not e.is_symlink() and sub in dirs_needed:
            farm(e, new_dir / e.name, sub); continue
        if e.is_file() and f"{rel}/{e.name.split('.', 1)[0]}" in paths:
            shutil.copy2(e, new_dir / e.name); os.chmod(new_dir / e.name, 0o644)  # writable copy with the base mtime
            n_copies += 1; copied_bytes += e.stat().st_size; continue
        (new_dir / e.name).symlink_to(e); n_links += 1


build = N / ".lake/build"; build.mkdir()
for top in (B / ".lake/build").iterdir():
    if top.name == "lib":
        (build / "lib").mkdir()
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
print(f"farm: {n_links} links, {n_copies} copied files ({copied_bytes / 1e6:.0f} MB) in {t_farm:.1f}s")
before = {str(q.relative_to(build)): q.stat().st_mtime_ns for q in build.rglob("*") if q.is_file() and not q.is_symlink()}

t = time.perf_counter()
p = subprocess.run(["lake", "build", *["+" + m for m in changed]], cwd=N, capture_output=True, text=True)
t_build = time.perf_counter() - t
print(f"lake build rc={p.returncode} in {t_build:.0f}s")
if p.returncode:
    print((p.stdout + p.stderr)[-2500:])
after = {str(q.relative_to(build)): q.stat().st_mtime_ns for q in build.rglob("*") if q.is_file() and not q.is_symlink()}
rewritten = sorted(k for k in after if before.get(k) != after[k])
mods = sorted({re.sub(r"^(lib/lean|ir)/", "", w).split(".", 1)[0].replace("/", ".") for w in rewritten
               if w.startswith(("lib/lean/", "ir/"))})
print(f"Lake rewrote {len(rewritten)} files for {len(mods)} modules (superset {len(superset)})")
same = sum((build / w).read_bytes() == (R / ".lake/build" / w).read_bytes()
           for w in rewritten if (R / ".lake/build" / w).exists())
print(f"rewritten files byte-identical to the copied reviewed workspace: {same}/{len(rewritten)}")
p = subprocess.run(["lake", "build", "--no-build", *["+" + m for m in changed]], cwd=N, capture_output=True, text=True)
print("lake build --no-build:", p.returncode, (p.stdout + p.stderr).strip().splitlines()[-1:])
