"""The census's pre-registered numbers (reader_rubric_census_v1.md, "What is reported").
usage: analyse.py [--write]   (run from this directory or the repo root; spends nothing)

Reads order.json and reader_<X>/{codebook.json,labels.jsonl} for every reader directory present,
plus crossmap.json when it exists (pairs of matched entry ids across the two readers). Prints the
tables and, with --write, rewrites results.json.
"""
import json, sys
from collections import Counter, defaultdict
from pathlib import Path
HERE = Path(__file__).resolve().parent
order = json.load(open(HERE / "order.json"))
batches = [b["batch"] for b in order["batches"]]
set_of = {o["cid"]: o["set"] for o in order["order"]}
family_of = {o["cid"]: o["family"] for o in order["order"]}
batch_of = {o["cid"]: o["batch"] for o in order["order"]}
VAL_BATCHES = [b for b in batches if b.startswith("b")]
LAST3 = VAL_BATCHES[-3:]

def load_reader(d):
    cb = {e["id"]: e for e in json.load(open(d / "codebook.json"))} if (d / "codebook.json").exists() else {}
    labels = [json.loads(l) for f in sorted(d.glob("labels_*.jsonl")) for l in open(f) if l.strip()]
    return cb, labels

def summarise(name, cb, labels):
    done = [l for l in labels if l["cid"] in batch_of]
    done_batches = [b for b in batches if any(batch_of[l["cid"]] == b for l in done)]
    created_in = defaultdict(list)  # batch -> new entry ids
    first_seen = {}
    for l in done:
        for pid in (l["principle_id"], l.get("second_principle_id") or ""):
            if pid and pid != "none" and pid not in first_seen:
                first_seen[pid] = batch_of[l["cid"]]; created_in[batch_of[l["cid"]]].append(pid)
    curve, size = [], 0
    for b in done_batches:
        size += len(created_in[b]); curve.append({"batch": b, "new": len(created_in[b]), "size": size})
    val = [l for l in done if set_of[l["cid"]] == "val1000"]
    val_ids = {pid for pid, b in first_seen.items() if b.startswith("b")}
    out_ids = {pid for pid, b in first_seen.items() if not b.startswith("b")}
    assigned = Counter(l["principle_id"] for l in val if l["principle_id"] != "none")
    n_principled = sum(assigned.values())
    singletons = sum(1 for _, c in assigned.items() if c == 1)
    none_by = Counter(l.get("none_reason") or "" for l in val if l["principle_id"] == "none")
    top = assigned.most_common()
    def cover(k): return round(sum(c for _, c in top[:k]) / n_principled, 3) if n_principled else None
    by_family = defaultdict(lambda: {"asks": 0, "none": 0, "entries": set()})
    for l in val:
        f = family_of[l["cid"]].split("|")[0]
        by_family[f]["asks"] += 1
        if l["principle_id"] == "none": by_family[f]["none"] += 1
        else: by_family[f]["entries"].add(l["principle_id"])
    fam_table = {f: {"asks": v["asks"], "none": v["none"], "entries": len(v["entries"])} for f, v in sorted(by_family.items())}
    rationale = Counter(); form = Counter()
    for pid, c in assigned.items():
        e = cb.get(pid, {})
        for r in e.get("rationale", []): rationale[r] += c
        form[e.get("form", "?")] += c
    last3_new = sum(len(created_in[b]) for b in LAST3 if b in done_batches)
    val_done = all(b in done_batches for b in VAL_BATCHES)
    out_done = [b for b in done_batches if not b.startswith("b")]
    res = {
        "reader": name, "asks_labelled": len(done), "batches_done": done_batches,
        "codebook_size": len(cb), "val1000_entries": len(val_ids), "outside_new_entries": len(out_ids),
        "curve": curve,
        "saturation_val1000": {"last3_batches": LAST3, "new_entries_in_last3": last3_new,
                                "share_of_codebook": round(last3_new / len(val_ids), 3) if val_ids and val_done else None,
                                "verdict": (None if not val_done else ("saturated" if last3_new / len(val_ids) < 0.05 else "not saturated")),
                                "good_turing_p_new": round(singletons / n_principled, 3) if n_principled else None,
                                "singleton_entries": singletons},
        "held_out": {"outside_asks_labelled": len(done) - len(val), "new_entries": len(out_ids),
                     "share_of_val1000_codebook": round(len(out_ids) / len(val_ids), 3) if val_ids and out_done else None,
                     "verdict": (None if not out_done or len(out_done) < len(batches) - len(VAL_BATCHES) else
                                 ("saturated" if len(out_ids) / len(val_ids) <= 0.10 else "not saturated" if len(out_ids) / len(val_ids) >= 0.25 else "ambiguous"))},
        "concentration_val1000": {"asks_with_principle": n_principled, "none": dict(none_by),
                                  "none_share": round(sum(none_by.values()) / len(val), 3) if val else None,
                                  "top10": cover(10), "top25": cover(25), "top50": cover(50)},
        "by_family_val1000": fam_table,
        "rationale_weighted_by_asks": dict(rationale.most_common()), "form_weighted_by_asks": dict(form),
        "revised_entries": sum(1 for e in cb.values() if e.get("revised")),
        "unsure_share": round(sum(1 for l in done if l.get("confidence") == "unsure") / len(done), 3) if done else None,
    }
    return res

def agreement(readers, crossmap):
    if len(readers) != 2 or not crossmap: return None
    (na, (cba, la)), (nb, (cbb, lb)) = readers
    pairs = {(p["a"], p["b"]) for p in crossmap["pairs"]}
    A = {l["cid"]: l["principle_id"] for l in la}; B = {l["cid"]: l["principle_id"] for l in lb}
    both = [c for c in A if c in B]
    def matched(c):
        a, b = A[c], B[c]
        if a == "none" or b == "none": return a == b
        return (a, b) in pairs
    agree = sum(1 for c in both if matched(c))
    none_agree = sum(1 for c in both if (A[c] == "none") == (B[c] == "none"))
    return {"asks_in_both": len(both), "principle_matched": agree, "share": round(agree / len(both), 3) if both else None,
            "none_vs_some_agreement": round(none_agree / len(both), 3) if both else None,
            "entries_A": len(cba), "entries_B": len(cbb), "A_matched": len({a for a, _ in pairs}), "B_matched": len({b for _, b in pairs})}

def mapping_free_agreement(readers, sets=("val1000",)):
    """Agreement that needs no cross-map: none-vs-some per ask; for asks both readers gave a principle,
    whether two asks under one principle for one reader are under one principle for the other (both
    conditionals and the adjusted Rand index); and how far each A entry's asks fall under one B entry."""
    import itertools
    if len(readers) != 2: return None
    (_, (cba, la)), (_, (cbb, lb)) = readers
    A = {l["cid"]: l["principle_id"] for l in la if set_of[l["cid"]] in sets}
    B = {l["cid"]: l["principle_id"] for l in lb if set_of[l["cid"]] in sets}
    both = sorted(set(A) & set(B))
    if not both: return None
    nn = sum(1 for c in both if (A[c] == "none") == (B[c] == "none"))
    P = [c for c in both if A[c] != "none" and B[c] != "none"]
    ga, gb = defaultdict(set), defaultdict(set)
    for c in P: ga[A[c]].add(c); gb[B[c]].add(c)
    pa = {frozenset(p) for g in ga.values() for p in itertools.combinations(sorted(g), 2)}
    pb = {frozenset(p) for g in gb.values() for p in itertools.combinations(sorted(g), 2)}
    inter, n = len(pa & pb), len(P); total = n * (n - 1) // 2
    e = len(pa) * len(pb) / total if total else 0
    ari = (inter - e) / (0.5 * (len(pa) + len(pb)) - e) if total and (0.5 * (len(pa) + len(pb)) - e) else None
    dom = {a: Counter(B[c] for c in g).most_common(1)[0][1] / len(g) for a, g in ga.items()}
    big = [a for a, g in ga.items() if len(g) >= 3]
    return {"sets": list(sets), "asks_in_both": len(both), "none_vs_some_agreement": round(nn / len(both), 3),
            "asks_principled_by_both": n, "same_pairs_A": len(pa), "same_pairs_B": len(pb), "same_pairs_shared": inter,
            "p_B_same_given_A_same": round(inter / len(pa), 3) if pa else None,
            "p_A_same_given_B_same": round(inter / len(pb), 3) if pb else None,
            "adjusted_rand_index": round(ari, 3) if ari is not None else None,
            "A_entries_used": len(ga), "A_entries_with_dominant_B_half": sum(1 for v in dom.values() if v >= 0.5),
            "A_entries_with_dominant_B_all": sum(1 for v in dom.values() if v == 1.0),
            "A_entries_3plus": len(big), "A_entries_3plus_dominant_B_half": sum(1 for a in big if dom[a] >= 0.5)}

readers = [(d.name, load_reader(d)) for d in sorted(HERE.glob("reader_*")) if d.is_dir()]
results = {"order_seed": order["seed"], "counts": order["counts"], "readers": {n: summarise(n, cb, lb) for n, (cb, lb) in readers}}
cm = json.load(open(HERE / "crossmap.json")) if (HERE / "crossmap.json").exists() else None
results["agreement"] = agreement(readers, cm)
results["mapping_free_agreement_val1000"] = mapping_free_agreement(readers)
results["mapping_free_agreement_all"] = mapping_free_agreement(readers, sets=("val1000", "outside_window", "outside_years"))
for n, r in results["readers"].items():
    print(f"== {n}: {r['asks_labelled']} asks, codebook {r['codebook_size']} (val1000 {r['val1000_entries']}, outside adds {r['outside_new_entries']})")
    print("   curve:", " ".join(f"{c['batch']}:+{c['new']}={c['size']}" for c in r["curve"]))
    print("   saturation:", r["saturation_val1000"]); print("   held-out:", r["held_out"])
    print("   concentration:", r["concentration_val1000"]); print("   families:", r["by_family_val1000"])
    print("   rationale:", r["rationale_weighted_by_asks"], "form:", r["form_weighted_by_asks"], "unsure:", r["unsure_share"])
print("== agreement:", results["agreement"])
print("== mapping-free agreement (val1000):", results["mapping_free_agreement_val1000"])
if "--write" in sys.argv:
    json.dump(results, open(HERE / "results.json", "w"), indent=1); print("wrote results.json")
