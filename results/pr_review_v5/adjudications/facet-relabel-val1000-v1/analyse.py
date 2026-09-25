"""The facet relabel's pre-registered readings (docs/todo/pipeline-overfit-review.md, "Facet relabel").

Usage: analyse.py <batch_dir> <val1000_label_dir> <facet_pilot.json>
<batch_dir> holds f{0..4}.jsonl, f{i}.A.jsonl, f{i}.B.jsonl and manifest.json. Writes results.json there.
"""
import collections, json, sys
from pathlib import Path

D, OLD, PILOT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
FACETS = ("object", "reference", "mechanism", "remedy", "warrant")
ALLOWED = {
    "object": {"proof", "name", "binders", "statement", "attributes", "definition", "instance", "family",
               "location", "prose", "layout", "pr", "meta", "build"},
    "reference": {"variant", "library", "norms", "siblings", "mechanism", "module_graph", "intent", "process"},
    "mechanism": {"", "registration", "generators", "typeclass", "defeq", "performance", "build"},
    "remedy": {"local", "interface", "delete", "add", "reencode", "move", "pr", "none"},
    "warrant": {"compile", "exhibit", "count", "judgment"},
}
manifest = json.load(open(D / "manifest.json"))
RANDOM, PILOT_CIDS = set(manifest["random"]), set(manifest["pilot"])


def load(reader):
    out = {}
    for i in range(5):
        order = [json.loads(l)["cid"] for l in open(D / f"f{i}.jsonl")]
        rows = [json.loads(l) for l in open(D / f"f{i}.{reader}.jsonl") if l.strip()]
        assert [r["cid"] for r in rows] == order, f"f{i}.{reader}: cids differ from the batch"
        for r in rows:
            for f in FACETS:
                assert r[f] in ALLOWED[f], (f"f{i}.{reader}", r["cid"], f, r[f])
            out[r["cid"]] = r
    return out


A, B = load("A"), load("B")


def kappa(pairs):
    n = len(pairs)
    if not n:
        return None
    po = sum(a == b for a, b in pairs) / n
    ca, cb = collections.Counter(a for a, _ in pairs), collections.Counter(b for _, b in pairs)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / n / n
    return round((po - pe) / (1 - pe), 3) if pe < 1 else 1.0


res = {"n_random": len(RANDOM), "n_pilot": len(PILOT_CIDS)}
# F: reliability on the random 600
rel = {}
for f in FACETS:
    cids = [c for c in RANDOM if f != "mechanism" or (A[c]["reference"] == B[c]["reference"] == "mechanism")]
    rel[f] = {"kappa": kappa([(A[c][f], B[c][f]) for c in cids]), "n": len(cids),
              "agree": round(sum(A[c][f] == B[c][f] for c in cids) / max(1, len(cids)), 3)}
    rel[f]["usable"] = rel[f]["kappa"] is not None and rel[f]["kappa"] >= 0.60
res["F_reliability"] = rel

# auditor against readers on the pilot
MAP = {"object": {"prf": "proof", "nam": "name", "sig": "binders", "stm": "statement", "att": "attributes",
                  "def": "definition", "ins": "instance", "fam": "family", "loc": "location", "txt": "prose",
                  "lay": "layout", "pr": "pr", "met": "meta", "bld": "build"},
       "reference": {"var": "variant", "lib": "library", "pop": "norms", "sib": "siblings", "mec": "mechanism",
                     "mod": "module_graph", "int": "intent", "pro": "process"},
       "mechanism": {"": "", "auto": "registration", "gen": "generators", "tc": "typeclass", "defeq": "defeq",
                     "perf": "performance", "build": "build"},
       "remedy": {"loc": "local", "ifc": "interface", "del": "delete", "add": "add", "enc": "reencode",
                  "mov": "move", "pr": "pr", "none": "none"},
       "warrant": {"cmp": "compile", "exh": "exhibit", "cnt": "count", "jud": "judgment"}}
aud = {r["cid"]: {f: MAP[f][r[f]] for f in FACETS} for r in json.load(open(PILOT))["labels"]}
res["auditor_vs_readers"] = {
    f: {"auditor_A": kappa([(aud[c][f], A[c][f]) for c in PILOT_CIDS]),
        "auditor_B": kappa([(aud[c][f], B[c][f]) for c in PILOT_CIDS]),
        "A_B_on_pilot": kappa([(A[c][f], B[c][f]) for c in PILOT_CIDS])}
    for f in ("object", "reference", "remedy", "warrant")}


def agreed(cids, *facets):
    return [c for c in cids if all(A[c][f] == B[c][f] for f in facets)]


# S1: references cross objects
s1 = {}
for ref in ("variant", "library", "norms"):
    cs = [c for c in agreed(RANDOM, "reference", "object") if A[c]["reference"] == ref]
    objs = collections.Counter(A[c]["object"] for c in cs)
    big = {o: k for o, k in objs.items() if cs and k / len(cs) >= 0.10}
    s1[ref] = {"n": len(cs), "objects": dict(objs.most_common()), "objects_at_10pct": len(big), "holds": len(big) >= 3}
res["S1"] = s1

# S2: mechanisms stay on their own objects
s2 = {}
cs = [c for c in agreed(RANDOM, "reference", "mechanism", "object") if A[c]["reference"] == "mechanism"]
for m in sorted({A[c]["mechanism"] for c in cs}):
    mc = [c for c in cs if A[c]["mechanism"] == m]
    objs = collections.Counter(A[c]["object"] for c in mc)
    top2 = sum(k for _, k in objs.most_common(2))
    s2[m] = {"n": len(mc), "objects": dict(objs.most_common()), "top2_share": round(top2 / len(mc), 3),
             "tested": len(mc) >= 10, "holds": (top2 / len(mc) >= 0.80) if len(mc) >= 10 else None}
res["S2"] = s2

# S3: the reference predicts the warrant
cs = agreed(RANDOM, "reference", "warrant")
per = collections.defaultdict(collections.Counter)
for c in cs:
    per[A[c]["reference"]][A[c]["warrant"]] += 1
modal = sum(v.most_common(1)[0][1] for v in per.values())
res["S3"] = {"n": len(cs), "pooled_modal_share": round(modal / len(cs), 3), "holds": modal / len(cs) >= 0.80,
             "per_reference": {r: {"n": sum(v.values()), "modal": v.most_common(1)[0][0],
                                   "share": round(v.most_common(1)[0][1] / sum(v.values()), 3), "warrants": dict(v)}
                               for r, v in per.items()}}

# C: warrant purity per arm
old = {}
for rd in ("A", "B"):
    for f in sorted(OLD.glob(f"b*.{rd}.jsonl")):
        for l in open(f):
            r = json.loads(l)
            old.setdefault(r["cid"], {})[rd] = r["family"]
FD = {"F1": "proof", "F2": "interface", "F3": "interface", "F4": "library_fit", "F5": "library_fit",
      "F6": "design", "F7": "design", "F8": "naming", "F9": "formatting", "F10": "doc_quality",
      "F11": "correctness", "CORR": "correctness", "F12": "pr_level"}


def s76(r):
    ref, obj, mech = r["reference"], r["object"], r["mechanism"]
    if ref == "variant":
        return "proof" if obj == "proof" else "generality"
    if ref in ("library", "module_graph"):
        return "library"
    if ref == "siblings":
        return "siblings"
    if ref == "norms":
        return {"name": "naming", "layout": "layout", "prose": "prose"}.get(obj, "form")
    if ref == "mechanism":
        return {"registration": "automation", "generators": "automation", "performance": "automation",
                "typeclass": "typeclass", "defeq": "typeclass", "build": "correctness"}.get(mech, "automation")
    if ref == "intent":
        return "prose" if obj == "prose" else "correctness"
    return "pr_level"


def purity(assign):
    arms = collections.defaultdict(collections.Counter)
    for c, arm in assign.items():
        arms[arm][A[c]["warrant"]] += 1
    out = {a: {"n": sum(v.values()), "modal": v.most_common(1)[0][0],
               "purity": round(v.most_common(1)[0][1] / sum(v.values()), 3), "warrants": dict(v)}
           for a, v in arms.items()}
    tot = sum(x["n"] for x in out.values())
    return out, round(sum(x["purity"] * x["n"] for x in out.values()) / tot, 3)


wa = agreed(RANDOM, "warrant")
fd_assign = {c: FD[old[c]["A"]] for c in wa if old.get(c, {}).get("A") == old.get(c, {}).get("B") and old[c]["A"] in FD}
fd, fd_mean = purity(fd_assign)
s76_assign = {c: s76(A[c]) for c in agreed(wa, "reference", "object", "mechanism")}
new, new_mean = purity(s76_assign)
low = [a for a, x in fd.items() if x["n"] >= 10 and x["purity"] < 0.70]
res["C"] = {"family_division": fd, "family_division_weighted_mean": fd_mean,
            "section_7_6": new, "section_7_6_weighted_mean": new_mean,
            "family_arms_under_70pct_with_n_ge_10": low,
            "holds": fd.get("design", {}).get("purity", 1) < 0.70 and len(low) >= 2}

# exploratory
pairs = collections.Counter()
for c in RANDOM:
    for r in (A[c], B[c]):
        if r["second_reference"]:
            pairs[tuple(sorted((r["reference"], r["second_reference"])))] += 1
res["exploratory_second_reference_pairs"] = {" + ".join(k): v for k, v in pairs.most_common(12)}
tab = collections.defaultdict(collections.Counter)
for c in agreed(RANDOM, "reference", "object"):
    tab[A[c]["reference"]][A[c]["object"]] += 1
res["exploratory_reference_by_object"] = {r: dict(v.most_common()) for r, v in tab.items()}
json.dump(res, open(D / "results.json", "w"), indent=1)
print(json.dumps({k: res[k] for k in ("F_reliability", "auditor_vs_readers")}, indent=1))
for k in ("S1", "S2"):
    print(k, json.dumps({m: {kk: v[kk] for kk in v if kk != "objects"} for m, v in res[k].items()}))
print("S3", res["S3"]["pooled_modal_share"], res["S3"]["holds"], {r: (v["modal"], v["share"], v["n"]) for r, v in res["S3"]["per_reference"].items()})
print("C family division", {a: (x["modal"], x["purity"], x["n"]) for a, x in fd.items()}, "mean", fd_mean)
print("C section 7.6", {a: (x["modal"], x["purity"], x["n"]) for a, x in new.items()}, "mean", new_mean)
print("C holds", res["C"]["holds"], "low", low)
