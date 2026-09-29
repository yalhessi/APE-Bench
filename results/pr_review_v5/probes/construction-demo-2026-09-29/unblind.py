"""Unblind the construction demonstration and apply the reading rule README.md states.

Usage: python3 unblind.py <match_dir> <matcher id> [<matcher id> ...]
`match_dir` holds matches.<id>.json and k_index.json (from build_match_inputs.py).

Criterion 1's compile check: a K hit counts as backed when its reaching finding cites a
construction that records a compile result (`compiled` true or false) and whose Lean text matches
a `lean_verify_edit` call the wrapper logged in that session: one text contains the other, or
their difflib ratio is at least 0.6, after collapsing whitespace.
"""
import collections, difflib, json, re, sys
from pathlib import Path

P = Path(__file__).parent
M = Path(sys.argv[1])
seal = json.load(open(P / "blinding_SEALED.json"))
asks = json.load(open(P / "asks_SEALED.json"))
k_index = json.load(open(M / "k_index.json"))
RULE = {(pr, c) for pr in asks for c in asks[pr]["rule"]}
PROVENANCE_FLAGGED = {"v0106", "v0107", "v0108", "v0060", "v0061", "v0090", "v0091", "v0062", "v0063"}


def load(pr, session, name):
    path = P / f"pr{pr}" / session / name
    if not path.exists():
        return []
    if name.endswith(".jsonl"):
        return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    return json.load(open(path))


def norm(text):
    return re.sub(r"\s+", " ", text or "").strip()


def logged(con, calls):
    if con.get("compiled") not in (True, False):
        return False
    lean = norm(con.get("lean"))
    for call in calls:
        if call.get("tool") != "lean_verify_edit" or not isinstance(call.get("arguments"), dict):
            continue
        a = call["arguments"]
        text = norm((a.get("new_declaration") or "") + " " + (a.get("replacement") or ""))
        if lean and text and (lean in text or text in lean
                              or difflib.SequenceMatcher(None, lean, text).ratio() >= 0.6):
            return True
    return False


def backing(pr, run, label, idx):
    """(construction kinds, backed?) for the K finding a matcher credited."""
    pas, orig = k_index[pr][label][idx]
    finding = load(pr, run + pas, "findings.json")[orig]
    ids = finding.get("construction") or []
    ids = [ids] if isinstance(ids, str) else ids
    cons = {c.get("id"): c for c in load(pr, run + pas, "constructions.json")}
    calls = load(pr, run + pas, "calls.jsonl")
    cited = [cons[i] for i in ids if i in cons]
    return pas, sorted({c.get("kind") for c in cited}), any(logged(c, calls) for c in cited)


def count(pr, session):
    return len(load(pr, session, "findings.json"))


out = {}
for m in sys.argv[2:]:
    d = json.load(open(M / f"matches.{m}.json"))
    reached, partial, where = collections.defaultdict(set), collections.defaultdict(set), {}
    for a in d["asks"]:
        pr = str(a["pr"])
        for label, cond in seal[pr].items():
            if a[label] == "reached":
                reached[cond].add((pr, a["ask_id"]))
                where[(cond, pr, a["ask_id"])] = (label, a[label + "_finding"])
            elif a[label] == "partial":
                partial[cond].add((pr, a["ask_id"]))
    K = {r: reached[r] & RULE for r in ("K1", "K2")}
    k_stable = K["K1"] & K["K2"]
    pairs = [(reached["X1"] | reached["X2"]) & RULE, (reached["X3"] | reached["X4"]) & RULE]
    x_stable = pairs[0] & pairs[1]
    backed = {}
    for pr, cid in sorted(k_stable):
        per_run = {}
        for run in ("K1", "K2"):
            label, idx = where[(run, pr, cid)]
            per_run[run] = backing(pr, run, label, idx)
        backed[f"{pr}:{cid}"] = {r: {"pass": v[0], "kinds": v[1], "compile_logged": v[2]}
                                 for r, v in per_run.items()}
    c1 = len(k_stable) >= 3 and all(all(v["compile_logged"] for v in b.values())
                                    for b in backed.values())
    c2 = len(k_stable) - len(x_stable) >= 2
    prs = list(seal)
    k_per_pr_run = sum(count(pr, r + p) for pr in prs for r in ("K1", "K2") for p in ("p3", "p4")) / (2 * len(prs))
    x_per_pr_pair = sum(count(pr, x) for pr in prs for x in ("X1", "X2", "X3", "X4")) / (2 * len(prs))
    c3 = k_per_pr_run <= x_per_pr_pair
    per_ask = {}
    for pr in prs:
        for cid in asks[pr]["rule"] + asks[pr]["other"]:
            per_ask[f"{pr}:{cid}"] = {
                "rule": (pr, cid) in RULE, "provenance_flagged": cid in PROVENANCE_FLAGGED,
                "reached_by": sorted(c for c in reached if (pr, cid) in reached[c]),
                "partial_by": sorted(c for c in partial if (pr, cid) in partial[c])}
    out[m] = {
        "K1": sorted(map(list, K["K1"])), "K2": sorted(map(list, K["K2"])),
        "K_stable": sorted(map(list, k_stable)), "K_union": sorted(map(list, K["K1"] | K["K2"])),
        "X_pairs": [sorted(map(list, p)) for p in pairs], "X_stable": sorted(map(list, x_stable)),
        "X_union": sorted(map(list, pairs[0] | pairs[1])),
        "backing": backed, "findings_per_pr": {"K_run": k_per_pr_run, "X_pair": x_per_pr_pair},
        "criteria": {"1_K_stable_ge_3_backed": c1, "2_K_minus_X_stable_ge_2": c2, "3_noise": c3},
        "supported": c1 and c2 and c3, "per_ask": per_ask,
    }
    print(f"matcher {m}: K stable {len(k_stable)} (union {len(K['K1'] | K['K2'])}), "
          f"X stable {len(x_stable)} (union {len(pairs[0] | pairs[1])}); "
          f"findings/PR K run {k_per_pr_run:.1f}, X pair {x_per_pr_pair:.1f}; "
          f"criteria {out[m]['criteria']}; supported: {out[m]['supported']}")
    for key, v in per_ask.items():
        print(f"   {key:12} rule={v['rule']!s:5} flagged={v['provenance_flagged']!s:5} "
              f"reached={v['reached_by']} partial={v['partial_by']}")
json.dump(out, open(P / "unblinded.json", "w"), indent=1)
