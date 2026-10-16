"""Build the 90 reading packets (PROTOCOL.md amendment 2): the 77 open survivors and the 13 fixed
departures, shuffled with a fixed seed under opaque ids, each with the reviewed-head diff excerpt.

usage (repo root): ape/bin/python <this file>
writes reading_items.jsonl (the committed list, with the key) and packets/<id>.md (what readers see).
"""
import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
sys.path.insert(0, str(Path.cwd() / "src"))
from src.mathlib_review.io import jsonl_rows  # noqa: E402

HERE = Path(__file__).resolve().parent
DRAW = Path("inputs/pull_requests/evaluation/val1000-2025-06-2026-03-v1/draw.json")
FACTS = [Path("results/pr_review_v5/probes/convention-detectors-2026-10-06/census/dot_notation_v3/facts.jsonl"),
         Path("results/pr_review_v5/probes/convention-detectors-2026-10-06/census/primed_names/facts.jsonl")]
SECTION = {"P057": "Dot notation for a call (census P057)", "P108": "Placement in the predicate's namespace (census P108)",
           "P113": "Primed names (census P113, P211)"}
SEED = 20261016


def section(conv: str) -> str:
    text = (HERE / "conventions_as_held.md").read_text()
    start = text.index("## " + SECTION[conv])
    end = text.find("\n## ", start + 3)
    return text[start:end if end >= 0 else len(text)].strip()


def excerpt(patch: str, fact: dict) -> str:
    """The diff hunk that holds the declaration (or the call), trimmed to 60 lines around it."""
    leaf = (fact["declaration"] or "").rsplit(".", 1)[-1]
    call = re.match(r"^`([^`\s]+\.[^`\s.]+ [^`\s]+)`", fact["text"])
    needles = [n for n in (call.group(1) if call else None, leaf) if n and not n.startswith("(")]
    hunks = re.split(r"(?m)^(?=@@ )", patch)
    for needle in needles:
        for hunk in hunks:
            if needle in hunk:
                lines = hunk.splitlines()
                at = next(i for i, l in enumerate(lines) if needle in l)
                return "\n".join(lines[max(0, at - 25):at + 35])
    return "(the declaration was not found in the reviewed-head diff of this file)"


def main() -> int:
    draw = {a["pr_number"]: a for a in json.loads(DRAW.read_text())["accepted"]}
    facts = {(f["pr_number"], f["path"], f["line"], f["declaration"]): f for p in FACTS for f in jsonl_rows(p)}
    rows = list(jsonl_rows(HERE / "scope.jsonl"))
    open77 = [r for r in rows if r["outcome"] == "survived" and not r["asked"] and r["practice"] in ("none", "new_file")]
    fixed = [r for r in rows if r["outcome"] != "survived"]
    items = [("open", r) for r in open77] + [("calibration", r) for r in fixed]
    random.Random(SEED).shuffle(items)
    (HERE / "packets").mkdir(exist_ok=True)
    out = []
    for n, (role, r) in enumerate(items, 1):
        item = f"I{n:03d}"
        fact = facts[(r["pr_number"], r["path"], r["line"], r["declaration"])]
        head = draw[r["pr_number"]]["episode_id"].split(":")[3]
        compare = json.loads(Path(f"data/pull_requests/pr/{r['pr_number']}/compares/{head}.json").read_text())
        patch = next((f.get("patch") or "" for f in compare["files"] if f["filename"] == r["path"]), "")
        base = draw[r["pr_number"]]["base_sha"]
        packet = (f"# Item {item}\n\n**Convention.**\n\n{section(r['convention'])}\n\n"
                  f"**The detector's statement of the place.** {fact['text']}\n\n"
                  f"**Where.** `{r['path']}`, declaration `{r['declaration']}`. Library before the PR: base commit `{base}` "
                  f"(read it with `git -C data/code_execute/repos/mathlib4/source show {base}:<path>` or `git ... grep ... {base} -- Mathlib`).\n\n"
                  f"**The PR's diff at review time, around the place:**\n\n```diff\n{excerpt(patch, fact)}\n```\n")
        (HERE / "packets" / f"{item}.md").write_text(packet)
        out.append({"item": item, "role": role, "convention": r["convention"], "pr_number": r["pr_number"],
                    "path": r["path"], "line": r["line"], "declaration": r["declaration"], "outcome": r["outcome"],
                    "control": r["control"]})
    (HERE / "reading_items.jsonl").write_text("".join(json.dumps(o, ensure_ascii=False) + "\n" for o in out))
    print(len(out), "items;", sum(o["role"] == "calibration" for o in out), "calibration")
    missing = [o["item"] for o in out if "was not found" in (HERE / "packets" / f"{o['item']}.md").read_text()]
    print("packets without the declaration in the diff:", missing)
    return 0


if __name__ == "__main__":
    sys.exit(main())
