"""Agreement and distributions for the design-comparison reading. Run from the repo root."""
import json
from collections import Counter, defaultdict
from pathlib import Path
D = Path(__file__).parent
A = {r["cid"]: r for r in map(json.loads, open(D / "reader_A.jsonl"))}
B = {r["cid"]: r for r in map(json.loads, open(D / "reader_B.jsonl"))}
def kappa(pairs):
    n = len(pairs)
    if not n: return None
    po = sum(a == b for a, b in pairs) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return round((po - pe) / (1 - pe), 3) if pe < 1 else 1.0
out = {"n": {"A": len(A), "B": len(B), "both": len(A.keys() & B.keys())}, "fields": {}}
FIELDS = {"A": ["principle_stated", "principle_source"], "B": ["analogue_named", "findable_by", "wrong_analogue_plausible"]}
for grp, fields in FIELDS.items():
    cids = [c for c in A.keys() & B.keys() if A[c]["group"] == grp == B[c]["group"]]
    for f in fields:
        pairs = [(A[c][f], B[c][f]) for c in cids]
        agreed = Counter(a for a, b in pairs if a == b)
        out["fields"][f] = {"n": len(pairs), "kappa": kappa(pairs), "agreement": round(sum(a == b for a, b in pairs) / len(pairs), 3) if pairs else None,
                            "agreed": dict(agreed.most_common()), "split": len(pairs) - sum(agreed.values()),
                            "A": dict(Counter(a for a, _ in pairs).most_common()), "B": dict(Counter(b for _, b in pairs).most_common())}
# wrong-analogue cases named by either reader
out["wrong_analogue_named_by_either"] = sorted({c for c in A.keys() & B.keys() if A[c]["group"] == "B" and
                                                (A[c]["wrong_analogue_plausible"] == "yes" or B[c].get("wrong_analogue_plausible") == "yes")})
out["principles"] = {c: {"A": A[c]["principle"], "B": B[c].get("principle")} for c in sorted(A) if A[c]["group"] == "A" and c in B}
json.dump(out, open(D / "results.json", "w"), indent=1, ensure_ascii=False)
for f, v in out["fields"].items():
    print(f"{f:26} n={v['n']:3} kappa={v['kappa']}  agreed={v['agreed']}  split={v['split']}")
print("wrong analogue named by either:", out["wrong_analogue_named_by_either"])

# Same comparison object? Both readers' `analogue` fields, compared on the declaration names they
# carry (backticked, last component), else on shared content words.
import re
def keys(s):
    names = {n.split(".")[-1].strip("'`") for n in re.findall(r"`([^`]+)`", s)}
    words = {w for w in re.findall(r"[A-Za-z][A-Za-z0-9']{3,}", s)} - {"predicate", "lemma", "existing", "version", "variant", "form", "family", "definition", "definitions", "instance", "with", "that", "from", "this", "the", "should", "direction", "notation", "scoped", "constructor", "statement", "sibling", "siblings", "above", "twin", "other", "same", "counterpart", "duals", "dual", "lemmas"}
    return names, words
same = {}
for c in sorted(A):
    if A[c]["group"] != "B" or c not in B: continue
    na, wa = keys(A[c]["analogue"]); nb, wb = keys(B[c]["analogue"])
    same[c] = bool(na & nb) or (not na and not nb and bool(wa & wb)) or (bool(na) != bool(nb) and bool((na | wa) & (nb | wb)))
out["same_analogue"] = {"n": len(same), "same": sum(same.values()), "differ": [c for c, v in same.items() if not v]}
out["principle_written_by_both"] = sum(1 for c in A if A[c]["group"] == "A" and c in B and A[c]["principle"] and B[c].get("principle") and B[c].get("principle_stated") != "none")
json.dump(out, open(D / "results.json", "w"), indent=1, ensure_ascii=False)
print("same analogue:", out["same_analogue"]); print("principle written by both:", out["principle_written_by_both"], "of 31")
