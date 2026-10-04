"""Matcher inputs, blind: the asks (from the round-1 feedback, kept outside the repo) and each
reviewer set stripped to target / claim / requested_change / severity, relabelled R1-R6 per PR by
blinding_SEALED.json. A K run's findings are its pass-3 findings followed by its pass-4 findings;
`k_index.json` (kept beside the match inputs, not given to matchers) maps each back.

Usage: python3 build_match_inputs.py <val60_feedback.json> <out_dir>
"""
import json, sys
from pathlib import Path

P = Path(__file__).parent
feedback, out = json.load(open(sys.argv[1])), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
seal = json.load(open(P / "blinding_SEALED.json"))
asks = json.load(open(P / "asks_SEALED.json"))
rows = {r["cid"]: r for r in feedback["rows"]}
KEEP = ("target", "claim", "requested_change", "severity")

#: K findings cite their constructions by id ("as pass 3's c13 compiled"), which would tell a
#: matcher which reviewer is K. Redacted for every reviewer, mechanically, after the reviewer
#: outputs were committed (2bd0d96) and before any matcher ran. Mathlib paths are untouched.
import re
_REDACT = [(re.compile(r"\bpass \d(?:'s)?\s+"), ""), (re.compile(r"\bc\d{1,3}\b"), "a compiled check")]


def redact(text):
    if not isinstance(text, str):
        return text
    for pattern, repl in _REDACT:
        text = pattern.sub(repl, text)
    return text


def findings(session):
    path = P / f"pr{pr}" / session / "findings.json"
    return json.load(open(path)) if path.exists() else []


k_index = {}
for pr, labels in seal.items():
    ids = asks[pr]["rule"] + asks[pr]["other"]
    packet = []
    for cid in ids:
        r = rows[cid]
        parent = rows.get(r["reply_to_cid"]) if r.get("reply_to_cid") else None
        packet.append({"ask_id": cid, "path": r["path"], "code_at_comment": r["diff_hunk"],
                       "comment": r["body"], "replies_to": parent["body"] if parent else None})
    json.dump(packet, open(out / f"asks_pr{pr}.json", "w"), indent=1, ensure_ascii=False)
    for label, cond in labels.items():
        if cond.startswith("X"):
            items = [("X", i, f) for i, f in enumerate(findings(cond))]
        else:
            items = [(p, i, f) for p in ("p3", "p4") for i, f in enumerate(findings(cond + p))]
        stripped = [{"i": n, **{k: redact(f.get(k)) for k in KEEP}} for n, (_, _, f) in enumerate(items)]
        json.dump(stripped, open(out / f"{label}_pr{pr}.json", "w"), indent=1, ensure_ascii=False)
        k_index.setdefault(pr, {})[label] = [[p, i] for p, i, _ in items]
json.dump(k_index, open(out / "k_index.json", "w"), indent=1)
print("match inputs in", out)
