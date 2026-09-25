"""Situate each val1000 inline ask on the changed declaration it comments on (hunk-tail join)."""
import json, glob, collections, sys
from pathlib import Path
from src.mathlib_review.io import load_jsonl
from src.mathlib_review.schema import ChangeGraph, ModificationRecord
SP = Path(sys.argv[1]); S = SP / "structure_val1000"
fb = {r["cid"]: r for r in json.load(open(SP / "val1000_feedback.json"))["rows"]}
A, B = {}, {}
for f in glob.glob(str(SP / "labels/b*.A.jsonl")):
    for l in open(f): r = json.loads(l); A[r["cid"]] = r
for f in glob.glob(str(SP / "labels/b*.B.jsonl")):
    for l in open(f): r = json.loads(l); B[r["cid"]] = r
asks = [c for c in A if A[c]["is_ask"] == "ask" and B.get(c, {}).get("is_ask") == "ask"]
graphs = {g.pr_number: g for g in load_jsonl(S / "change_graphs.jsonl", ChangeGraph)}
life = {m.primary_change_id: m.lifecycle for m in load_jsonl(S / "modification_inventory.jsonl", ModificationRecord)}
out = {}
for c in asks:
    r = fb[c]
    if r["kind"] != "review_comment" or not r["diff_hunk"] or int(r["pr"]) not in graphs: continue
    tail = [l for l in r["diff_hunk"].split("\n") if l and not l.startswith("-") and not l.startswith("@@")]
    if not tail: continue
    line = tail[-1][1:].strip()
    if len(line) < 6: continue
    hits = [t for t in graphs[int(r["pr"])].targets if t.path == r["path"] and t.reviewed_code and line in t.reviewed_code]
    if not hits: continue
    t = min(hits, key=lambda t: len(t.reviewed_code))
    out[c] = {"kind": t.kind, "decl_kind": t.declaration_kind, "lifecycle": life.get(t.change_id), "family": A[c]["family"]}
json.dump(out, open(SP / "situated.json", "w"))
print("inline asks situated:", len(out), "of", sum(1 for c in asks if fb[c]["kind"] == "review_comment"), "inline asks")
k = collections.Counter((v["decl_kind"] or v["kind"]) for v in out.values())
print("by subject:", dict(k.most_common(12)))
