"""Blind matcher inputs for the post-cutoff probe: the in-window reference (the construction
demonstration's X1-X4 on 34091, 30458, 32875 against their 16 asks) and the post-cutoff PRs (X1, X2
against the asks both readers agree are asks), relabelled per PR by blinding_SEALED.json, each finding
stripped to target / claim / requested_change / severity, with condition cues redacted.

Usage: python3 build_match_inputs.py <val60_feedback.json> <probe_feedback.json> <reader_A.jsonl> <reader_B.jsonl> <out_dir>
"""
import json, re, sys
from pathlib import Path

Q = Path(__file__).parent
DEMO = Path("results/pr_review_v5/probes/construction-demo-2026-09-29")
val_fb, probe_fb, reader_a, reader_b, out = sys.argv[1:6]
out = Path(out); out.mkdir(parents=True, exist_ok=True)
seal = json.load(open(Q / "blinding_SEALED.json"))
demo_asks = json.load(open(DEMO / "asks_SEALED.json"))
KEEP = ("target", "claim", "requested_change", "severity")
_REDACT = [(re.compile(r"\bpass \d(?:'s)?\s+"), ""), (re.compile(r"\bc\d{1,3}\b"), "a compiled check")]


def redact(text):
    if not isinstance(text, str):
        return text
    for pattern, repl in _REDACT:
        text = pattern.sub(repl, text)
    return text


def rows(path):
    return {r["cid"]: r for r in json.load(open(path))["rows"]}


def labels(path):
    return {r["cid"]: r for r in (json.loads(l) for l in open(path) if l.strip())}


val_rows, probe_rows = rows(val_fb), rows(probe_fb)
a, b = labels(reader_a), labels(reader_b)
agreed = {c for c in probe_rows if a.get(c, {}).get("is_ask") == "ask" and b.get(c, {}).get("is_ask") == "ask"}
families = {c: (a[c]["family"] if a[c]["family"] == b[c]["family"] else "split") for c in agreed}
manifest = {"in": {}, "post": {}}
for pr, entry in seal.items():
    if entry["set"] == "in":
        src, ids = val_rows, demo_asks[pr]["rule"] + demo_asks[pr]["other"]
    else:
        src = probe_rows
        ids = sorted(c for c in agreed if str(probe_rows[c]["pr"]) == pr)
    manifest[entry["set"]][pr] = ids
    if ids:
        packet = []
        for cid in ids:
            r = src[cid]
            parent = src.get(r["reply_to_cid"]) if r.get("reply_to_cid") else None
            packet.append({"ask_id": cid, "path": r["path"], "code_at_comment": r["diff_hunk"],
                           "comment": r["body"], "replies_to": parent["body"] if parent else None})
        json.dump(packet, open(out / f"asks_pr{pr}.json", "w"), indent=1, ensure_ascii=False)
    base = DEMO if entry["set"] == "in" else Q
    for label, session in entry["labels"].items():
        path = base / f"pr{pr}" / session / "findings.json"
        found = json.load(open(path)) if path.exists() else []
        stripped = [{"i": n, **{k: redact(f.get(k)) for k in KEEP}} for n, f in enumerate(found)]
        if ids:
            json.dump(stripped, open(out / f"{label}_pr{pr}.json", "w"), indent=1, ensure_ascii=False)
json.dump({"asks": manifest, "families": families}, open(out / "ask_manifest.json", "w"), indent=1)
print("asks: in", sum(map(len, manifest["in"].values())), "post", sum(map(len, manifest["post"].values())),
      "| post PRs with asks", sum(1 for v in manifest["post"].values() if v))
