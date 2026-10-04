"""Per-session packets for the post-cutoff probe: X1 and X2 for every drawn PR, each with the
construction demonstration's control brief verbatim, the PR, its diff, its pass-0 model and a
logging wrapper whose workdir and raw outputs live in the session scratchpad.

Usage (repo root): python3 make_packets.py <scratch_dir>
"""
import json, os, shutil, sys
from pathlib import Path

Q = Path(__file__).parent
ROOT = Path.cwd()
BRIEF = Path("results/pr_review_v5/probes/construction-demo-2026-09-29/brief_X.md")
RELEASE = Path("inputs/probes/probe-2026-07-08-v1")
scratch = Path(sys.argv[1])
template = (Q / "bin/ptool.template").read_text()
for line in (RELEASE / "input/episodes.jsonl").read_text().splitlines():
    e = json.loads(line)
    pr = e["pr_number"]
    title = e["title"]["text"] if isinstance(e["title"], dict) else e["title"]
    desc = (e.get("description") or {}).get("text") or "(not recoverable at review start)"
    prmd = (f"# PR #{pr}: {title}\n\n## Description\n\n{desc}\n\n## Changed files\n\n"
            + "\n".join(f"- `{c}`" for c in e["changed_files"]) + "\n")
    for session in ("X1", "X2"):
        d = Q / f"pr{pr}" / session
        d.mkdir(parents=True, exist_ok=True)
        shutil.copy(BRIEF, d / "brief.md")
        shutil.copy(Q / f"model_pr{pr}.md", d / "model.md")
        (d / "pr.md").write_text(prmd)
        (d / "diff.patch").write_text(e["diff"])
        wrapper = (template.replace("__PR__", str(pr)).replace("__OUT__", str(ROOT / d))
                   .replace("__WORK__", str(scratch / f"work/pr{pr}/{session}"))
                   .replace("__RAW__", str(scratch / f"raw/pr{pr}/{session}")).replace("__ROOT__", str(ROOT)))
        (d / "ptool").write_text(wrapper)
        os.chmod(d / "ptool", 0o755)
print("packets written")
