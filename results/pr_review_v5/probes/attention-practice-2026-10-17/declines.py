"""Step 4's packet: every comment on a val1000 PR, any round, by anyone but the PR's author and not a bot, that
carries a decline phrase (review3-direction.md's `declines.py` list), plus ten census asks (seed 17) mixed in blind
as calibration. Bodies go to the packet in scratch only; the committed key holds ids, never text.

usage (repo root): ape/bin/python <this file> <bodies.json from materialise_bodies.py> <packet.json out>
Writes declines_key.jsonl beside this file (item, source, pr, comment id, kind; `calibration` true for the asks).
"""
import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
sys.path.insert(0, str(Path.cwd() / "src"))

HERE = Path(__file__).resolve().parent
DRAW = Path("inputs/pull_requests/evaluation/val1000-2025-06-2026-03-v1/draw.json")
LABELS = Path("results/pr_review_v5/adjudications/conventions-census-v1/reader_A")
DECL = re.compile(r"\b(no need|not necessary|unnecessary to|fine as is|fine as it is|either (way|is fine)|I don'?t mind|"
                  r"doesn'?t matter|not worth|leave it|keep it as is|ok as is|okay as is|can stay|fine either way|"
                  r"not required|no strong (opinion|preference)|happy either way|feel free to ignore|up to you|I'?m fine with)\b",
                  re.I)
BOTS = re.compile(r"bot|github-actions", re.I)


def main(bodies_path: str, out: str) -> int:
    draw = json.loads(DRAW.read_text())["accepted"]
    items = []
    for a in draw:
        d = Path(f"data/pull_requests/pr/{a['pr_number']}")
        if not (d / "pr.json").is_file():
            continue
        author = json.load(open(d / "pr.json"))["user"]["login"]
        for fn, kind in (("review_comments.jsonl", "review_comment"), ("issue_comments.jsonl", "issue_comment")):
            rows = [json.loads(l) for l in open(d / fn)]
            by_id = {r.get("id"): r for r in rows}
            for r in rows:
                u = (r.get("user") or {}).get("login") or ""
                if u == author or BOTS.search(u) or not DECL.search(r.get("body") or ""):
                    continue
                parent = by_id.get(r.get("in_reply_to_id"))
                items.append({"source": "decline", "pr": a["pr_number"], "id": r.get("id"), "kind": kind,
                              "commenter_is_author": False, "path": r.get("path"),
                              "diff_hunk": (r.get("diff_hunk") or "")[-700:], "body": r.get("body") or "",
                              "replying_to": (parent.get("body") or "")[:700] if parent else None,
                              "replying_to_by_author": bool(parent and (parent.get("user") or {}).get("login") == author)})
    labelled = set()
    for f in sorted(LABELS.glob("labels_b*.jsonl")):
        for l in open(f):
            r = json.loads(l)
            if r.get("principle_id"):
                labelled.add(r["cid"])
    bodies = [r for r in json.load(open(bodies_path))["rows"]
              if r["set"] == "val1000" and r["cid"] in labelled and r["kind"] == "review_comment"
              and not DECL.search(r["body"] or "")]
    random.Random(17).shuffle(bodies)
    for r in bodies[:10]:
        items.append({"source": "calibration_ask", "pr": r["pr"], "id": r["gh_id"], "kind": r["kind"],
                      "commenter_is_author": False, "path": r["path"], "diff_hunk": (r["diff_hunk"] or "")[-700:],
                      "body": r["body"], "replying_to": None, "replying_to_by_author": False})
    random.Random(18).shuffle(items)
    for n, it in enumerate(items, 1):
        it["item"] = f"D{n:03d}"
    packet = [{k: it[k] for k in ("item", "pr", "kind", "path", "diff_hunk", "replying_to", "replying_to_by_author", "body")}
              for it in items]
    Path(out).write_text(json.dumps(packet, ensure_ascii=False, indent=1))
    (HERE / "declines_key.jsonl").write_text("".join(json.dumps({"item": it["item"], "source": it["source"],
                                                                  "pr": it["pr"], "id": it["id"], "kind": it["kind"]}) + "\n"
                                                      for it in items))
    print(f"{sum(it['source'] == 'decline' for it in items)} declines + "
          f"{sum(it['source'] == 'calibration_ask' for it in items)} calibration asks -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
