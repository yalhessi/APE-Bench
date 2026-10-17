"""Build every departure (and every opportunity count) the detectors find in the round-1 diffs of the val1000
PRs, with the covariates the protocol reads: attention, moved or written, the file's own base practice, the
author group. Computes no outcome (nothing at the merge commit, no census ask). Writes places.jsonl and
opportunities.jsonl.

usage (repo root): ape/bin/python <this file>
"""
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import detect  # noqa: E402

HERE = Path(__file__).resolve().parent
DRAW = Path("inputs/pull_requests/evaluation/val1000-2025-06-2026-03-v1/draw.json")
REPO = Path("data/code_execute/repos/mathlib4/source")
BOTS = re.compile(r"bot|github-actions", re.I)
NEAR = 3          # a comment within this many lines of the declaration (or construct) counts as attention
REVIEWER_MIN = 20  # round-1 review comments on other val1000 PRs that make an author an active reviewer


def git_show(sha, path):
    out = subprocess.run(["git", "-C", str(REPO), "show", f"{sha}:{path}"], capture_output=True, text=True)
    return out.stdout if out.returncode == 0 else None


def apply_patch(base, patch):
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
    return out


def added_lines(patch):
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


def norm(s):
    return " ".join(s.split())


def round1_comments(pr, head, author):
    d = Path(f"data/pull_requests/pr/{pr}")
    out = []
    for line in open(d / "review_comments.jsonl"):
        r = json.loads(line)
        u = (r.get("user") or {}).get("login") or ""
        if u == author or BOTS.search(u) or r.get("original_commit_id") != head:
            continue
        out.append((r["path"], r.get("original_line"), r.get("original_start_line")))
    return out


def one_pr(a, classes, reviewers):
    pr, base = a["pr_number"], a["base_sha"]
    head = a["episode_id"].split(":")[3]
    cmp_path = Path(f"data/pull_requests/pr/{pr}/compares/{head}.json")
    pj = Path(f"data/pull_requests/pr/{pr}/pr.json")
    if not cmp_path.is_file() or not pj.is_file():
        return [], []
    author = json.load(open(pj))["user"]["login"]
    group = "ai" if a.get("ai_evidence") else ("reviewer" if author in reviewers else "other")
    files = json.load(open(cmp_path))["files"]
    removed = {norm(l[1:]) for f in files for l in (f.get("patch") or "").splitlines()
               if l.startswith("-") and not l.startswith("---") and l[1:].strip()}
    comments = round1_comments(pr, head, author)
    reviewed = bool(comments)
    places, opps = [], []
    for f in files:
        path = f["filename"]
        if not path.endswith(".lean") or not path.startswith("Mathlib/") or not f.get("patch"):
            continue
        base_text = git_show(base, path) if f.get("status") != "added" else ""
        base_lines = (base_text or "").splitlines()
        lines = apply_patch(base_text or "", f["patch"])
        look = added_lines(f["patch"])
        opp, dep = detect.detect(lines, look, classes)
        # the file's own practice at the base: the same detectors over every base line
        b_opp, b_dep = detect.detect(base_lines, set(range(1, len(base_lines) + 1)), classes) if base_lines else ({}, [])
        b_count = Counter(d["rule"] for d in b_dep)
        base_names = {m.group(2) for line in base_lines for m in [detect.HEADER.match(line)] if m}
        opps.append({"pr": pr, "path": path, "group": group, "opp": opp,
                     "dep": dict(Counter(d["rule"] for d in dep)),
                     "base_opp": b_opp, "base_dep": dict(b_count)})
        fc = [c for c in comments if c[0] == path]
        for d in dep:
            lo, hi = d["decl_span"] if d["decl_span"] else d["lines"]
            near = any((ln is not None and lo - NEAR <= ln <= hi + NEAR) or (st is not None and lo - NEAR <= st <= hi + NEAR)
                       for _, ln, st in fc)
            text = [norm(lines[k - 1]) for k in range(d["lines"][0], d["lines"][1] + 1)]
            moved = all(t in removed for t in text if t)
            existing = d["decl"] is not None and d["decl"] in base_names
            bo, bd = b_opp.get(d["rule"], 0), b_count.get(d["rule"], 0)
            places.append({**d, "pr": pr, "path": path, "group": group, "author": author,
                           "attention": "near" if near else ("pr_reviewed" if reviewed else "pr_unreviewed"),
                           "moved": moved, "decl_in_base_file": existing,
                           "file_base_opp": bo, "file_base_dep": bd})
    return places, opps


def main():
    draw = json.loads(DRAW.read_text())["accepted"]
    classes = frozenset(l.strip() for l in open(HERE / "classes_unambiguous.txt") if l.strip())
    # active reviewers: round-1 review comments on val1000 PRs other than their own
    by_login = Counter()
    for a in draw:
        pr = a["pr_number"]
        head = a["episode_id"].split(":")[3]
        pj = Path(f"data/pull_requests/pr/{pr}/pr.json")
        if not pj.is_file():
            continue
        author = json.load(open(pj))["user"]["login"]
        for line in open(f"data/pull_requests/pr/{pr}/review_comments.jsonl"):
            r = json.loads(line)
            u = (r.get("user") or {}).get("login") or ""
            if u != author and not BOTS.search(u) and r.get("original_commit_id") == head:
                by_login[u] += 1
    reviewers = {u for u, n in by_login.items() if n >= REVIEWER_MIN}
    with ThreadPoolExecutor(16) as ex:
        results = list(ex.map(lambda a: one_pr(a, classes, reviewers), draw))
    places = [p for r in results for p in r[0]]
    opps = [o for r in results for o in r[1]]
    (HERE / "places.jsonl").write_text("".join(json.dumps(p, ensure_ascii=False) + "\n" for p in places))
    (HERE / "opportunities.jsonl").write_text("".join(json.dumps(o) + "\n" for o in opps))
    (HERE / "reviewers.json").write_text(json.dumps({"min_round1_comments": REVIEWER_MIN,
                                                     "reviewers": sorted(reviewers)}, indent=1))
    print(f"{len(reviewers)} active reviewers; {len(places)} departures on {len({p['pr'] for p in places})} PRs")
    c = defaultdict(Counter)
    for p in places:
        c[p["rule"]]["n"] += 1
        c[p["rule"]][p["attention"]] += 1
        c[p["rule"]]["moved"] += p["moved"]
        c[p["rule"]][p["group"]] += 1
    tot = defaultdict(Counter)
    for o in opps:
        for r, n in o["opp"].items():
            tot[r]["opp"] += n
            tot[r]["opp_" + o["group"]] += n
    for r in detect.RULES:
        x = c[r]
        print(f"{r:6} departures {x['n']:5} of {tot[r]['opp']:6} opportunities | near {x['near']:4} pr_reviewed {x['pr_reviewed']:4} "
              f"pr_unreviewed {x['pr_unreviewed']:4} | moved {x['moved']:4} | reviewer {x['reviewer']:4} other {x['other']:4} ai {x['ai']:3}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
