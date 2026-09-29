"""Validate one reader's batch output against the order and its codebook.
usage: check_batch.py <census_dir> <reader> <batch>"""
import json, sys
from pathlib import Path
C, reader, batch = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
order = json.load(open(C / "order.json"))
want = [o["cid"] for o in order["order"] if o["batch"] == batch]
cb = json.load(open(C / reader / "codebook.json"))
ids = [e["id"] for e in cb]
rows = [json.loads(l) for l in open(C / reader / f"labels_{batch}.jsonl") if l.strip()]
errs = []
if ids != [f"P{i:03d}" for i in range(1, len(ids) + 1)]: errs.append(f"ids not consecutive: {ids[:3]}..{ids[-3:]}")
for e in cb:
    if set(e) - {"id", "principle", "rationale", "form", "revised"} or not e.get("principle") or e.get("form") not in ("rule", "standard"): errs.append(f"bad entry {e.get('id')}")
    bad = set(e.get("rationale", [])) - {"readability","compactness","maintainability","generality","automation","discoverability","consistency","correctness","performance","process","mathematics"}
    if bad or not e.get("rationale"): errs.append(f"rationale {e.get('id')}: {bad or 'empty'}")
got = [r["cid"] for r in rows]
if got != want:
    missing, extra = set(want) - set(got), set(got) - set(want)
    errs.append(f"cids: {len(got)} of {len(want)}; missing {sorted(missing)[:5]} extra {sorted(extra)[:5]}; order ok={sorted(got)==sorted(want) and got!=want}")
KEYS = {"cid", "principle_id", "second_principle_id", "none_reason", "new", "confidence", "note"}
for r in rows:
    if set(r) != KEYS: errs.append(f"{r.get('cid')}: keys {sorted(set(r) ^ KEYS)}")
    p = r.get("principle_id")
    if p != "none" and p not in ids: errs.append(f"{r.get('cid')}: principle_id {p}")
    if r.get("second_principle_id") not in ("",) and r.get("second_principle_id") not in ids: errs.append(f"{r.get('cid')}: second {r.get('second_principle_id')}")
    if (p == "none") != (r.get("none_reason") in ("specific", "unreadable")): errs.append(f"{r.get('cid')}: none_reason {r.get('none_reason')!r} with principle_id {p}")
    if r.get("confidence") not in ("sure", "unsure"): errs.append(f"{r.get('cid')}: confidence")
from collections import Counter
new = sum(1 for r in rows if r.get("new") is True); none = Counter(r.get("none_reason") for r in rows if r.get("principle_id") == "none")
print(f"{reader} {batch}: rows {len(rows)}/{len(want)} new {new} none {dict(none)} codebook {len(ids)} revised {sum(1 for e in cb if e.get('revised'))} unsure {sum(1 for r in rows if r.get('confidence')=='unsure')}")
if errs: print("ERRORS:", *errs[:12], sep="\n  "); sys.exit(1)
print("ok")
