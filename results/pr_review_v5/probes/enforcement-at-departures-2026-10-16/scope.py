"""The scope check (PROTOCOL.md, amendment 1): does a departure follow its own file's practice at base?

For each fact that survived or was fixed by merge, reads the file at the PR's base commit and counts the
departure form against the convention form for the same object; classifies the file's practice
(departure / convention / none / new_file) and prints the reading rule's table. For a new file the
directory's practice is reported beside it. Deterministic; no model. Writes `scope.jsonl`.

usage (repo root): ape/bin/python <this file>
"""
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
sys.path.insert(0, str(Path.cwd() / "src"))
from src.mathlib_review.io import jsonl_rows  # noqa: E402

HERE = Path(__file__).resolve().parent
REPO = Path("data/code_execute/repos/mathlib4/source")
DRAW = Path("inputs/pull_requests/evaluation/val1000-2025-06-2026-03-v1/draw.json")
FACTS = [Path("results/pr_review_v5/probes/convention-detectors-2026-10-06/census/dot_notation_v3/facts.jsonl"),
         Path("results/pr_review_v5/probes/convention-detectors-2026-10-06/census/primed_names/facts.jsonl")]
END = r"(?![\w'])"
START = r"(?<![\w'.])"
HEADER = (r"(?m)^\s*(?:@\[[^\]]*\]\s*)?(?:(?:protected|private|noncomputable|nonrec|scoped)\s+)*"
          r"(?:theorem|lemma|def|abbrev|instance|structure|class)\s+")
_CALL = re.compile(r"^`(?P<prefix>[^`\s]+)\.(?P<lemma>[^`\s.]+) (?P<arg>[^`\s]+)` applies")
_PLACE = re.compile(r"^`(?P<leaf>[^`]+)` concludes `(?P<head>[^`]+?) …`")
IDENT = r"[A-Za-z_α-ωΑ-Ω][\w'₀-₉]*"
#: A receiver: a variable, written lower-case (`h`, `hp`, `x₁`) or as one capital (`A`, `M'`, `S₂`), never a
#: multi-letter capitalised namespace (`Matrix.toLin'` is the departure form, not the dotted one).
RECEIVER = r"(?:[a-z_α-ω][\w'₀-₉]*|[A-Z][0-9'₀-₉]*)"


def git(*args: str):
    out = subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True)
    return out.stdout if out.returncode == 0 else None


def lower_first(name: str) -> str:
    return name[:1].lower() + name[1:]


def counts(fact: dict, text: str):
    """(departure, convention) occurrences in `text`; convention is None where it cannot be counted."""
    if fact["producer"] == "primed_names":
        leaves = set(re.findall(HEADER + r"(?:[\w'.]+\.)?([\w']+)", text))
        return sum(1 for leaf in leaves if leaf.endswith("'") and leaf.rstrip("'") in leaves), None
    call = _CALL.match(fact["text"])
    if call:
        prefix, lemma = call.group("prefix"), call.group("lemma")
        dep = len(re.findall(START + re.escape(prefix) + r"\." + re.escape(lemma) + r"\s+" + IDENT, text))
        conv = len(re.findall(START + RECEIVER + r"\." + re.escape(lemma) + END, text))
        return dep, conv
    place = _PLACE.match(fact["text"])
    if place:
        last = place.group("head").split()[0].rsplit(".", 1)[-1]
        stem = lower_first(last) + "_of_"
        dep = len(re.findall(HEADER + r"(?:[\w'.]+\.)?" + re.escape(stem) + r"[\w']*", text))
        conv = len(re.findall(HEADER + r"(?:[\w'.]+\.)?" + re.escape(last) + r"\.of_[\w']*", text))
        if re.search(r"(?m)^namespace\s+(?:[\w.]+\.)?" + re.escape(last) + r"\s*$", text):
            conv += len(re.findall(HEADER + r"of_[\w']*", text))
        return dep, conv
    return 0, None


def practice(dep: int, conv) -> str:
    if conv is None:
        return "departure" if dep >= 2 else "none"
    if dep >= 2 and dep >= conv:
        return "departure"
    if conv >= 2 and conv > dep:
        return "convention"
    return "none"


def library_undotted(fact: dict, base: str):
    call = _CALL.match(fact["text"])
    if not call:
        return None
    def ere(s: str) -> str:
        return re.sub(r"([.^$*+?()\[\]{}|\\])", r"\\\1", s)
    pattern = r"(^|[^[:alnum:]_.'])" + ere(call.group("prefix")) + r"\." + ere(call.group("lemma")) + r"[[:space:]]+[[:alpha:]_]"
    out = git("grep", "-c", "-E", pattern, base, "--", "Mathlib")
    return sum(int(line.rsplit(":", 1)[1]) for line in (out or "").splitlines() if line.strip())


def main() -> int:
    bases = {a["pr_number"]: a["base_sha"] for a in json.loads(DRAW.read_text())["accepted"]}
    facts = {(f["pr_number"], f["path"], f["line"], f["declaration"]): f for p in FACTS for f in jsonl_rows(p)}
    rows = [r for r in jsonl_rows(HERE / "survival.jsonl") if r["outcome"] in ("survived", "fixed_dotted", "fixed_renamed")]
    out = []
    for r in rows:
        fact = facts[(r["pr_number"], r["path"], r["line"], r["declaration"])]
        base = bases[r["pr_number"]]
        text = git("show", f"{base}:{r['path']}")
        row = {k: r[k] for k in ("producer", "convention", "pr_number", "path", "line", "declaration", "asked", "control", "outcome")}
        if text is None:
            directory = r["path"].rsplit("/", 1)[0]
            names = (git("ls-tree", "--name-only", base, directory + "/") or "").split()
            dtext = "\n".join(git("show", f"{base}:{n}") or "" for n in names if n.endswith(".lean"))
            dep, conv = counts(fact, dtext)
            row.update(practice="new_file", file_dep=None, file_conv=None, dir_dep=dep, dir_conv=conv,
                       dir_practice=practice(dep, conv))
        else:
            dep, conv = counts(fact, text)
            row.update(practice=practice(dep, conv), file_dep=dep, file_conv=conv)
        row["library_undotted"] = library_undotted(fact, base)
        out.append(row)
    (HERE / "scope.jsonl").write_text("".join(json.dumps(o, ensure_ascii=False) + "\n" for o in out))

    def table(label, sub):
        c = Counter(o["practice"] for o in sub)
        measured = c["departure"] + c["convention"]
        share = lambda k: f"{c[k] / measured:.0%}" if measured else "-"
        print(f"  {label:34} n={len(sub):3}  departure {c['departure']:3} ({share('departure')})  convention {c['convention']:3} "
              f"({share('convention')})  none {c['none']:3}  new_file {c['new_file']:3}")

    for producer in ("dot_notation", "primed_names"):
        sub = [o for o in out if o["producer"] == producer]
        print(f"== {producer}")
        table("survived, unasked", [o for o in sub if o["outcome"] == "survived" and not o["asked"]])
        table("survived, co-located with an ask", [o for o in sub if o["outcome"] == "survived" and o["asked"]])
        table("fixed (contrast)", [o for o in sub if o["outcome"] != "survived"])
    print("== pooled")
    table("survived, all", [o for o in out if o["outcome"] == "survived"])
    table("survived, unasked", [o for o in out if o["outcome"] == "survived" and not o["asked"]])
    table("fixed (contrast)", [o for o in out if o["outcome"] != "survived"])
    new = [o for o in out if o["practice"] == "new_file" and o["outcome"] == "survived"]
    print(f"new files among survivors: {len(new)}; their directory's practice {dict(Counter(o['dir_practice'] for o in new))}")
    lib = [o["library_undotted"] for o in out if o["library_undotted"] is not None and o["outcome"] == "survived"]
    if lib:
        lib.sort()
        print(f"library-wide undotted uses of the same Prefix.lemma, surviving calls (n={len(lib)}): median {lib[len(lib) // 2]}, "
              f"0 for {sum(1 for x in lib if x == 0)}, 10 or more for {sum(1 for x in lib if x >= 10)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
