"""Step 1 (PROTOCOL.md): stage H's flagged places, and a baseline of the PRs' other declarations, followed
from the round-1 head to the merged commit. Deterministic; no model. Writes follow.jsonl.

usage (repo root): ape/bin/python <this file>
"""
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
MINED = Path("results/pr_review_v5/probes/conventions-ceiling-2026-10-04/census_mined.json")
DRAW = Path("inputs/pull_requests/evaluation/val1000-2025-06-2026-03-v1/draw.json")
REPO = Path("data/code_execute/repos/mathlib4/source")
KW = r"(?:theorem|lemma|def|abbrev|instance|structure|class|inductive)"
HEADER = re.compile(r"^(?:@\[[^\]]*\]\s*)?(?:(?:protected|private|noncomputable|nonrec|scoped)\s+)*" + KW + r"\s+([^\s:({\[]+)")
TOP = re.compile(r"^(?:@\[|/--|" + r"(?:(?:protected|private|noncomputable|nonrec|scoped)\s+)*" + KW + r"\b|end\b|section\b|namespace\b|variable\b|open\b|#)")


def git_show(sha: str, path: str):
    out = subprocess.run(["git", "-C", str(REPO), "show", f"{sha}:{path}"], capture_output=True, text=True)
    return out.stdout if out.returncode == 0 else None


def apply_patch(base: str, patch: str) -> str:
    """Apply a GitHub-style unified diff (hunks only) to `base`."""
    src = base.splitlines() if base else []
    out, at = [], 0
    for hunk in re.finditer(r"(?m)^@@ -(\d+)(?:,(\d+))? \+\d+(?:,\d+)? @@.*\n((?:(?!@@ ).*(?:\n|$))*)", patch):
        start = int(hunk.group(1)) - 1 if hunk.group(2) != "0" else int(hunk.group(1))
        out.extend(src[at:start])
        at = start
        for line in hunk.group(3).splitlines():
            if line.startswith("\\"):
                continue
            tag, text = line[:1], line[1:]
            if tag == " ":
                out.append(text)
                at += 1
            elif tag == "-":
                at += 1
            elif tag == "+":
                out.append(text)
    out.extend(src[at:])
    return "\n".join(out)


def blocks(text: str) -> dict:
    """Declaration leaf -> (start line, normalised block text).

    Known defect (review 3, 2026-10-17): keyed by the last name component, so two declarations sharing a leaf in one
    file (`IsMeagre.union`, `IsGδ.union`) collide and the first wins; no reported number moved.
    """
    lines = text.splitlines()
    out = {}
    for i, line in enumerate(lines):
        m = HEADER.match(line)
        if not m:
            continue
        j = i + 1
        while j < len(lines) and not (lines[j][:1] not in (" ", "\t", "") and TOP.match(lines[j])):
            j += 1
        leaf = m.group(1).rsplit(".", 1)[-1]
        out.setdefault(leaf, (i + 1, " ".join(" ".join(lines[i:j]).split())))
    return out


def added_lines(patch: str) -> set:
    """Line numbers in the new file that the round-1 diff adds."""
    added = set()
    for hunk in re.finditer(r"(?m)^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@.*\n((?:(?!@@ ).*(?:\n|$))*)", patch):
        n = int(hunk.group(1))
        for line in hunk.group(2).splitlines():
            if line.startswith("+"):
                added.add(n)
                n += 1
            elif line.startswith(" "):
                n += 1
    return added


def outcome(leaf: str, head_blocks: dict, merged_blocks: dict) -> str:
    if leaf not in head_blocks:
        return "unlocated"
    if leaf not in merged_blocks:
        return "gone"
    return "unchanged" if head_blocks[leaf][1] == merged_blocks[leaf][1] else "changed"


def main() -> int:
    mined = json.loads(MINED.read_text())
    draw = {a["pr_number"]: a for a in json.loads(DRAW.read_text())["accepted"]}
    rows = []
    for pr in mined["prs"]:
        merged = subprocess.run(["git", "-C", str(REPO), "log", "--format=%H", "-1", f"--grep=(#{pr})"],
                                capture_output=True, text=True).stdout.strip()
        places = [i for i in mined["items"] if i["pr"] == pr]
        if not merged:
            rows += [{"pr": pr, "kind": "place", "rule": i["rule"], "status": i["status"], "asked": i["asked"],
                      "file": i["file"], "declaration": i["declaration"], "outcome": "no_merge_commit"} for i in places]
            continue
        head = draw[pr]["episode_id"].split(":")[3]
        base = draw[pr]["base_sha"]
        compare = json.loads(Path(f"data/pull_requests/pr/{pr}/compares/{head}.json").read_text())
        patches = {f["filename"]: f.get("patch") or "" for f in compare["files"]}
        flagged = {}
        for i in places:
            flagged.setdefault(i["file"], set()).add(i["declaration"].rsplit(".", 1)[-1])
        for path in sorted({i["file"] for i in places} | {p for p in patches if p.endswith(".lean")}):
            if path not in patches:
                continue
            head_text = apply_patch(git_show(base, path) or "", patches[path])
            merged_text = git_show(merged, path) or ""
            hb, mb = blocks(head_text), blocks(merged_text)
            for i in [i for i in places if i["file"] == path]:
                leaf = i["declaration"].rsplit(".", 1)[-1]
                rows.append({"pr": pr, "kind": "place", "rule": i["rule"], "status": i["status"], "asked": i["asked"],
                             "file": path, "declaration": i["declaration"], "outcome": outcome(leaf, hb, mb)})
            touched = added_lines(patches[path])
            lines = head_text.splitlines()
            for leaf, (start, _) in hb.items():
                if leaf in flagged.get(path, set()):
                    continue
                end = start
                while end < len(lines) and not (lines[end][:1] not in (" ", "\t", "") and TOP.match(lines[end])):
                    end += 1
                if touched & set(range(start, end + 1)):
                    rows.append({"pr": pr, "kind": "baseline", "file": path, "declaration": leaf,
                                 "outcome": outcome(leaf, hb, mb)})
    (HERE / "follow.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))

    def line(label, sub):
        c = Counter(r["outcome"] for r in sub)
        located = c["unchanged"] + c["changed"] + c["gone"]
        moved = c["changed"] + c["gone"]
        print(f"  {label:34} n={len(sub):4}  unchanged {c['unchanged']:4} changed {c['changed']:3} gone {c['gone']:3} "
              f"unlocated {c['unlocated']:3} no_merge {c['no_merge_commit']:3}  changed-or-gone "
              f"{moved}/{located} = {moved / located:.0%}" if located else f"  {label:34} n={len(sub)} (none located)")

    places = [r for r in rows if r["kind"] == "place"]
    line("asked places (validity)", [r for r in places if r["asked"]])
    line("unasked places", [r for r in places if not r["asked"]])
    line("baseline: other touched declarations", [r for r in rows if r["kind"] == "baseline"])
    print("by rule (unasked):")
    for rule in sorted({r["rule"] for r in places}):
        line(rule, [r for r in places if r["rule"] == rule and not r["asked"]])
    print("by status (unasked):")
    for st in ("check", "departs"):
        line(st, [r for r in places if r["status"] == st and not r["asked"]])
    return 0


if __name__ == "__main__":
    sys.exit(main())
