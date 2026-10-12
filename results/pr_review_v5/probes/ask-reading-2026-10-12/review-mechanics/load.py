"""Shared loader for the mechanics review: every reading row with its batch, packets, sessions."""
import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROBE = HERE.parent
ROOT = PROBE.parents[3]


def rows():
    out = []
    for f in sorted((PROBE / "readings").glob("*.jsonl")):
        if f.name.startswith("aggregate"):
            continue
        for line in open(f):
            if line.strip():
                r = json.loads(line); r["batch"] = f.stem; out.append(r)
    return out


def packets():
    d = {}
    for st in ("D12", "P14_post", "P14_val"):
        for f in sorted((PROBE / "packets" / st).glob("*.json")):
            d[(st, int(f.stem))] = json.load(open(f))
    return d


def sessions():
    return json.load(open(PROBE / "sessions.json"))


def transcript(st, pr, label):
    return sessions()[f"{st}/{pr}"][label].get("transcript")
