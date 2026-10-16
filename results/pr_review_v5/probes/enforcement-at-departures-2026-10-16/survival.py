"""What happened to each detected departure by the time the PR merged (PROTOCOL.md).

Reads the census facts of the dot-notation and primed-name detectors, finds each PR's merged commit in
the Mathlib clone, and classifies the departure at merge: survived, fixed (the dotted call or the
renamed declaration is there), rewritten, gone. Writes `survival.jsonl` (one row per fact) and prints
the summary PROTOCOL.md's reading rule needs. Deterministic; no model.

usage (repo root): ape/bin/python <this file>
"""
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
sys.path.insert(0, str(Path.cwd() / "src"))
from src.mathlib_review.io import jsonl_rows  # noqa: E402

HERE = Path(__file__).resolve().parent
FACTS = {"dot_notation": Path("results/pr_review_v5/probes/convention-detectors-2026-10-06/census/dot_notation_v3/facts.jsonl"),
         "primed_names": Path("results/pr_review_v5/probes/convention-detectors-2026-10-06/census/primed_names/facts.jsonl")}
REPO = Path("data/code_execute/repos/mathlib4/source")
DECL = r"(?:theorem|lemma|def|instance|abbrev|structure|class|inductive)"
_CALL_FACT = re.compile(r"^`(?P<prefix>[^`\s]+)\.(?P<lemma>[^`\s.]+) (?P<arg>[^`\s]+)` applies")
_PLACE_FACT = re.compile(r"inside it, it is `(?P<dotted>[^`]+)`")


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True).stdout


def merged_commit(pr: int) -> str:
    return git("log", "--format=%H", "-1", f"--grep=(#{pr})").strip()


def file_at(sha: str, path: str):
    out = subprocess.run(["git", "-C", str(REPO), "show", f"{sha}:{path}"], capture_output=True, text=True)
    return out.stdout if out.returncode == 0 else None


def declared_in_tree(sha: str, leaf: str) -> bool:
    """A declaration whose (possibly qualified) name ends in `leaf` exists somewhere at `sha`."""
    pattern = rf"^\s*(?:@\[[^\]]*\]\s*)?(?:protected\s+|private\s+|noncomputable\s+|nonrec\s+)*{DECL}\s+(?:[\w'.]+\.)?{re.escape(leaf)}\b"
    return bool(git("grep", "-l", "-E", pattern, sha, "--", "Mathlib").strip())


def declared_in(text: str, leaf: str) -> bool:
    pattern = rf"(?m)^\s*(?:@\[[^\]]*\]\s*)?(?:protected\s+|private\s+|noncomputable\s+|nonrec\s+)*{DECL}\s+(?:[\w'.]+\.)?{re.escape(leaf)}\b"
    return re.search(pattern, text) is not None


def classify(row: dict, sha: str):
    text = file_at(sha, row["path"])
    leaf = (row["declaration"] or "").rsplit(".", 1)[-1]
    if text is None:
        # The file moved or went; follow the declaration by name.
        if leaf and not leaf.startswith("(") and declared_in_tree(sha, leaf):
            text = ""  # found elsewhere; the call check below cannot see it, so say so
            return "moved", "declaration found in another file"
        return "file_gone", "file absent at merge and declaration not found"
    if row["producer"] == "dot_notation":
        m = _CALL_FACT.match(row["text"])
        if m:
            prefix, lemma, arg = m.group("prefix"), m.group("lemma"), m.group("arg")
            call = re.compile(rf"\b{re.escape(prefix)}\.{re.escape(lemma)}\s+{re.escape(arg)}\b")
            dotted = re.compile(rf"\b{re.escape(arg)}\.{re.escape(lemma)}\b")
            if call.search(text):
                return "survived", "the undotted call is still in the file"
            if dotted.search(text):
                return "fixed_dotted", "the dotted form is in the file and the undotted call is not"
            return "fixed_other", "neither form is in the file (rewritten or removed)"
        p = _PLACE_FACT.search(row["text"])
        if p:
            if declared_in(text, leaf) or declared_in_tree(sha, leaf):
                return "survived", "the undotted name is still declared"
            dotted_leaf = p.group("dotted").rsplit(".", 1)[-1]
            if declared_in(text, dotted_leaf) or declared_in_tree(sha, dotted_leaf):
                return "fixed_renamed", "the dotted name is declared and the undotted one is not"
            return "gone", "neither name is declared at merge"
        return "unparsed", "fact text of an unknown shape"
    if row["producer"] == "primed_names":
        if declared_in(text, leaf) or declared_in_tree(sha, leaf):
            return "survived", "the primed name is still declared"
        if declared_in(text, leaf.rstrip("'")) or declared_in_tree(sha, leaf.rstrip("'")):
            return "fixed_renamed", "the primed name is gone and its unprimed sibling remains"
        return "gone", "neither the primed name nor its sibling is declared at merge"
    return "unparsed", "unknown producer"


def main() -> int:
    rows = [r for path in FACTS.values() for r in jsonl_rows(path)]
    merged = {pr: merged_commit(pr) for pr in sorted({r["pr_number"] for r in rows})}
    out = []
    for r in rows:
        sha = merged.get(r["pr_number"])
        if not sha:
            outcome, why = "no_merge_commit", "no commit mentions (#pr) in the clone"
        else:
            outcome, why = classify(r, sha)
        out.append({"producer": r["producer"], "convention": r["convention"], "pr_number": r["pr_number"],
                    "path": r["path"], "line": r["line"], "declaration": r["declaration"],
                    "control": bool(r.get("control")), "asked": bool(r.get("located_asks")),
                    "merged_sha": sha or None, "outcome": outcome, "why": why})
    (HERE / "survival.jsonl").write_text("".join(json.dumps(o, ensure_ascii=False) + "\n" for o in out))

    fixed = {"fixed_dotted", "fixed_renamed"}
    unchecked = {"no_merge_commit", "file_gone", "moved", "unparsed"}
    print(f"{len(out)} facts; outcomes {dict(Counter(o['outcome'] for o in out))}")

    def line(label, rows_):
        c = Counter(o["outcome"] for o in rows_)
        f, s = sum(c[k] for k in fixed), c["survived"]
        other = c["fixed_other"] + c["gone"]
        rate = f / (f + s) if f + s else float("nan")
        print(f"  {label:38} n={len(rows_):3}  fixed {f:3}  survived {s:3}  rewritten/gone {other:3}  "
              f"unchecked {sum(c[k] for k in unchecked):3}  enforcement {rate:.2f}")

    for producer in FACTS:
        sub = [o for o in out if o["producer"] == producer]
        print(f"\n== {producer}")
        line("all", sub)
        line("at a round-1 ask (validity check)", [o for o in sub if o["asked"]])
        line("unasked, ask PRs", [o for o in sub if not o["asked"] and not o["control"]])
        line("unasked, control PRs", [o for o in sub if o["control"]])
    print("\n== pooled")
    line("at a round-1 ask (validity check)", [o for o in out if o["asked"]])
    line("unasked, ask PRs", [o for o in out if not o["asked"] and not o["control"]])
    line("unasked, control PRs", [o for o in out if o["control"]])
    line("all unasked", [o for o in out if not o["asked"]])
    return 0


if __name__ == "__main__":
    sys.exit(main())
