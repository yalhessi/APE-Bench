"""Link val1000's round-1 comments to the removed declarations they may be about.

    python3 anchor_asks.py <structure_dir> <removed.jsonl> <feedback.json> <labels_dir> <out.jsonl> [--no-text]

`<feedback.json>` is `arm-coverage-val1000-2025-06-2026-03-v1/provenance/extract_draw_feedback.py`'s
output, which carries the comment bodies; `<labels_dir>` holds `reader_A.jsonl` / `reader_B.jsonl`.
Without `--no-text` each row carries the body and hunk, for reading; with it, only the anchors, for
committing (the bodies stay out of the tree, as in `events.jsonl`).

Anchors, strongest first; a comment keeps every anchor it has:
  on_removed     a `-`-side review comment inside a removed declaration's base lines
  on_alias       a comment whose line is a deprecated alias or attribute naming a removed one
  on_successor   a `+`-side comment inside the declaration a removed one moved or was renamed to,
                 or that its alias points at
  names_removed  the body names a removed declaration (full name, or a distinctive short name)
  same_hunk      a `+`-side comment whose hunk also deletes lines of a removed declaration
  keyword        the body says deprecat/alias (any PR), or renam/remov/delet (PRs with a removal)
"""
import json, re, sys
from collections import defaultdict
from pathlib import Path

S, REMOVED, FEEDBACK, LABELS, OUT = map(Path, sys.argv[1:6])
NO_TEXT = "--no-text" in sys.argv[6:]
graphs = {g["pr_number"]: g for g in map(json.loads, open(S / "change_graphs.jsonl"))}
removed = [json.loads(l) for l in open(REMOVED)]
rows = json.load(open(FEEDBACK))["rows"]
readers = {k: {r["cid"]: r for r in map(json.loads, open(LABELS / f"reader_{k}.jsonl"))} for k in "AB"}

by_pr = defaultdict(list)
for r in removed:
    by_pr[r["pr"]].append(r)


def spans(g, ids):
    ents = {e["entity_id"]: e for e in g["entities"]}
    return [(ents[i]["path"], ents[i]["span"]["line_start"], ents[i]["span"]["line_end"]) for i in ids if i in ents]


def distinctive(short):
    return len(short) >= 6 or "_" in short or any(c.isupper() for c in short[1:])


def tok(name):
    return re.compile(r"(?<![\w'])" + re.escape(name) + r"(?![\w'!?])")


KW_ANY = re.compile(r"deprecat|\balias", re.I)
KW_REMOVAL = re.compile(r"renam|remov|delet", re.I)

out = []
for c in rows:
    pr = c["pr"]
    rem = by_pr.get(pr, [])
    g = graphs.get(pr)
    hunk = [l for l in (c["diff_hunk"] or "").split("\n") if l]
    last = hunk[-1] if hunk else ""
    side = "LEFT" if last.startswith("-") else "RIGHT"
    anchors = defaultdict(set)  # anchor -> change_ids
    if g and c["kind"] == "review_comment" and c["path"] and c["line"]:
        targets = {t["change_id"]: t for t in g["targets"]}
        for r in rem:
            t = targets[r["change_id"]]
            if side == "LEFT":
                for p, a, b in spans(g, t["base_entity_ids"]):
                    if p == c["path"] and a <= c["line"] <= b:
                        anchors["on_removed"].add(r["change_id"])
                if last[1:] and last[1:] in (t["base_code"] or "").split("\n") and r["path"] == c["path"]:
                    anchors["on_removed"].add(r["change_id"])
            else:
                tail = "\n".join(l[1:] for l in hunk[-2:])
                if "deprecat" in tail or "alias" in tail:
                    if r["short"] and tok(r["short"]).search(tail):
                        anchors["on_alias"].add(r["change_id"])
                successors = set(r["same_statement_added"]) | set(r["same_short_other_namespace"]) \
                    | ({r["name"]} if (r["same_fullname_other_file"] or r["survives_same_file"]) and r["name"] else set()) \
                    | set(r["alias_target_added"]) | set(r["generated_from"])
                for t2 in targets.values():
                    if t2["kind"] != "declaration" or not t2["reviewed_entity_ids"]:
                        continue
                    n2 = t2["declaration_name"] or ""
                    if n2 in successors or any(n2.endswith("." + s) for s in successors):
                        for p, a, b in spans(g, t2["reviewed_entity_ids"]):
                            if p == c["path"] and a <= c["line"] <= b:
                                anchors["on_successor"].add(r["change_id"])
                deleted_here = [l[1:] for l in hunk if l.startswith("-")]
                own = set((t["base_code"] or "").split("\n"))
                if r["path"] == c["path"] and any(l.strip() and l in own for l in deleted_here):
                    anchors["same_hunk"].add(r["change_id"])
    body = c["body"] or ""
    for r in rem:
        if r["name"] and (r["name"] in body or (distinctive(r["short"]) and tok(r["short"]).search(body))):
            anchors["names_removed"].add(r["change_id"])
    kw = bool(KW_ANY.search(body)) or (bool(rem) and bool(KW_REMOVAL.search(body)))
    if not anchors and not kw:
        continue
    linked = sorted(set().union(*anchors.values())) if anchors else []
    rmap = {r["change_id"]: r for r in rem}
    out.append({
        "cid": c["cid"], "pr": pr, "ai": c["ai"], "kind": c["kind"], "author": c["author"],
        "path": c["path"], "line": c["line"], "side": side if c["kind"] == "review_comment" else None,
        "anchors": sorted(anchors), "keyword": kw, "pr_has_removal": bool(rem),
        "linked": [{"change_id": i, "name": rmap[i]["name"], "class": rmap[i]["class"]} for i in linked],
        **({} if NO_TEXT else {"hunk_tail": "\n".join(hunk[-6:]), "body": body}),
        "reply_to_cid": c["reply_to_cid"],
        "A": {k: readers["A"].get(c["cid"], {}).get(k) for k in ("is_ask", "family", "primary", "owners", "question")},
        "B": {k: readers["B"].get(c["cid"], {}).get(k) for k in ("is_ask", "family", "primary", "owners", "question")},
    })

with open(OUT, "w") as f:
    for o in out:
        f.write(json.dumps(o, ensure_ascii=False) + "\n")
from collections import Counter
print(len(out), "comments;", sum(1 for o in out if o["anchors"]), "structurally anchored;",
      sum(1 for o in out if o["keyword"] and not o["anchors"]), "keyword only")
print(Counter(a for o in out for a in o["anchors"]))
print("asks (A):", sum(1 for o in out if o["A"]["is_ask"] == "ask"))
