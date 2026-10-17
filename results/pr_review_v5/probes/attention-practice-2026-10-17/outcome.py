"""Step 3 (Q2, Q3, control; PROTOCOL.md): each departure followed to the merge commit, and the readings.
Writes outcomes.jsonl. Reads practice.json for step 2's reading (Q3 is read only for rules not "not their practice").

usage (repo root): ape/bin/python <this file>
"""
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import detect  # noqa: E402
import places as PL  # noqa: E402
from practice import rate_of  # noqa: E402

HERE = Path(__file__).resolve().parent
REPO = PL.REPO
STAGE_G = {"P084J": "P084", "P097": "P097", "P341": "P341", "P012": "P012", "P240": "P240", "P392": "P392"}
RULES = ("P084J", "P097", "P341", "P012", "P240", "P392")
CENSUS_EVENTS = Path("results/pr_review_v5/adjudications/arm-coverage-val1000-2025-06-2026-03-v1/events.jsonl")
CENSUS_LABELS = Path("results/pr_review_v5/adjudications/conventions-census-v1/reader_A")


def merge_shas():
    log = subprocess.run(["git", "-C", str(REPO), "log", "--format=%H %s"], capture_output=True, text=True).stdout
    out = {}
    for line in log.splitlines():
        sha, subj = line.split(" ", 1)
        m = re.search(r"\(#(\d+)\)\s*$", subj)   # a squash merge's subject ends with its PR number;
        if m:                                         # a revert or follow-up that only mentions it does not
            out.setdefault(int(m.group(1)), sha)
    return out


def nows(s, lemma=False):
    s = re.sub(r"\s|;", "", s)
    return s.replace("theorem", "lemma") if lemma else s


def decl_text(lines, a, b):
    return "\n".join(lines[a:b])


def follow(place, head, merged, classes):
    rule = place["rule"]
    if merged is None:
        return "file_gone", False
    if rule == "LONG":
        text = place["key"][1]
        still = any(" ".join(l.split()) == text and len(l) > 100 for l in merged)
        return ("persists" if still else "fixed"), False
    if rule == "P012":
        cmd = place["key"][1]
        h = [i for i, l in enumerate(head) if " ".join(l.split()) == cmd]
        m = [i for i, l in enumerate(merged) if " ".join(l.split()) == cmd]
        if len(h) != 1 or len(m) > 1:
            return "ambiguous", False
        if not m:
            return "gone", False
        opp, dep = detect.detect(merged, {m[0] + 1}, classes)
        departs = any(d["rule"] == "P012" for d in dep)
        if departs:
            return "persists", False

        def hood(lines, i):
            nb = [x for x in lines[max(0, i - 8):i] if x.strip()][-3:] + [x for x in lines[i + 1:i + 9] if x.strip()][:3]
            return nows("".join(nb))
        return "fixed", hood(head, h[0]) == hood(merged, m[0])
    name = place["decl"]
    hd = [d for d in detect.declarations(head) if d[1] == name]
    md = [d for d in detect.declarations(merged) if d[1] == name]
    if len(hd) != 1 or len(md) > 1:
        return "ambiguous", False
    if not md:
        return "gone", False
    _, _, a, b = md[0]
    opp, dep = detect.detect(merged, set(range(a + 1, b + 1)), classes)
    same = [d for d in dep if d["rule"] == rule and d["decl"] == name]
    if rule == "P097":
        persists = any(tuple(d["key"]) == tuple(place["key"]) for d in same)
    elif rule == "P392":
        persists = any(tuple(d["key"]) == tuple(place["key"]) for d in same)
    else:
        persists = bool(same)
    if persists:
        return "persists", False
    ha, hb = hd[0][2], hd[0][3]
    targeted = rule != "P392" and nows(decl_text(head, ha, hb), rule == "P341") == nows(decl_text(merged, a, b), rule == "P341")
    return "fixed", targeted


def census_asks():
    labels = {}
    for f in sorted(CENSUS_LABELS.glob("labels_b*.jsonl")):
        for l in open(f):
            r = json.loads(l)
            labels[r["cid"]] = {r.get("principle_id"), r.get("second_principle_id")}
    out = defaultdict(list)
    for l in open(CENSUS_EVENTS):
        e = json.loads(l)
        if e["cid"] in labels and e.get("line") is not None:
            out[(e["pr"], e["path"])].append((e["line"], labels[e["cid"]]))
    return out


def main() -> int:
    classes = frozenset(l.strip() for l in open(HERE / "classes_unambiguous.txt") if l.strip())
    places = [json.loads(l) for l in open(HERE / "places.jsonl")]
    opps = {(o["pr"], o["path"]): o for o in (json.loads(l) for l in open(HERE / "opportunities.jsonl"))}
    draw = {a["pr_number"]: a for a in json.loads(PL.DRAW.read_text())["accepted"]}
    merges = merge_shas()
    asks = census_asks()
    files = sorted({(p["pr"], p["path"]) for p in places})

    def load(k):
        pr, path = k
        a = draw[pr]
        head_sha = a["episode_id"].split(":")[3]
        f = {f["filename"]: f for f in json.load(open(f"data/pull_requests/pr/{pr}/compares/{head_sha}.json"))["files"]}[path]
        base = PL.git_show(a["base_sha"], path) if f.get("status") != "added" else ""
        head = PL.apply_patch(base or "", f["patch"])
        m = merges.get(pr)
        merged = None
        if m:
            t = PL.git_show(m, path)
            merged = t.splitlines() if t is not None else None
        return k, (head, merged, m)

    with ThreadPoolExecutor(16) as ex:
        texts = dict(ex.map(load, files))
    rows = []
    for p in places:
        head, merged, m = texts[(p["pr"], p["path"])]
        if not m:
            status, targeted = "no_merge", False
        else:
            status, targeted = follow(p, head, merged, classes)
        lo, hi = p["lines"]
        sid = STAGE_G.get(p["rule"])
        asked = any(lo - 1 <= ln <= hi + 1 and sid in labs for ln, labs in asks.get((p["pr"], p["path"]), []))
        o = opps[(p["pr"], p["path"])]
        bd, bn = rate_of(o["base_opp"], o["base_dep"], p["rule"]) if p["rule"] != "P097" else \
            (o["base_opp"].get("P097_proofs_departing", 0), o["base_opp"].get("P097_proofs", 0))
        rows.append({**p, "status": status, "targeted": targeted, "census_ask": asked,
                     "file_rate": (bd / bn) if bn >= 3 else None})
    (HERE / "outcomes.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    practice = json.loads((HERE / "practice.json").read_text())["rules"] if (HERE / "practice.json").is_file() else {}

    def fixed(r):
        return r["status"] == "fixed" and (r["targeted"] or r["rule"] == "P392")

    def rate(sub):
        n = [r for r in sub if r["status"] in ("fixed", "persists")]
        f = sum(fixed(r) for r in n)
        return f, len(n)

    def fmt(fn):
        f, n = fn
        return f"{f}/{n}" + (f" {f / n:.0%}" if n else "")

    print("status by rule:")
    for rule in RULES + ("LONG",):
        print(f"  {rule:6}", dict(Counter(r["status"] for r in rows if r["rule"] == rule)))
    lg = [r for r in rows if r["rule"] == "LONG" and r["status"] in ("fixed", "persists")]
    lf = sum(r["status"] == "fixed" for r in lg)
    ok = bool(lg) and lf / len(lg) >= 0.9
    print(f"\nCONTROL long lines fixed by merge (any): {lf}/{len(lg)}" + (f" {lf / len(lg):.0%}" if lg else "")
          + f" -> {'valid' if ok else 'BROKEN: nothing else is read'}")
    if not ok:
        return 1
    print("\nQ2 fixed by merge (targeted; P392 any), moved code left out")
    q2 = {}
    for rule in RULES:
        sub = [r for r in rows if r["rule"] == rule and not r["moved"]]
        near = [r for r in sub if r["attention"] == "near"]
        far = [r for r in sub if r["attention"] != "near"]
        fn, ff = rate(near), rate(far)
        anyfix = sum(r["status"] == "fixed" for r in near if r["status"] in ("fixed", "persists"))
        if fn[1] < 20:
            reading = "too few"
        else:
            s = fn[0] / fn[1]
            reading = "enforced where seen" if s >= 0.5 else "left where seen" if s <= 0.15 else "mixed"
        q2[rule] = reading
        lift = (fn[0] / fn[1]) / (ff[0] / ff[1]) if fn[1] and ff[1] and ff[0] else None
        asked = sum(r["census_ask"] for r in near)
        print(f"  {rule:6} near {fmt(fn):>12} (fixed any {anyfix})  far {fmt(ff):>12}  lift {lift:.1f}x" if lift else
              f"  {rule:6} near {fmt(fn):>12} (fixed any {anyfix})  far {fmt(ff):>12}  lift n/a", end="")
        print(f"  census asks near {asked}  -> {reading}")
        for g in ("reviewer", "other", "ai"):
            print(f"         by author group {g:8} near {fmt(rate([r for r in near if r['group'] == g])):>10}  "
                  f"far {fmt(rate([r for r in far if r['group'] == g])):>10}")
    print("\nQ3 place predicates on near departures (secondary: all departures)")
    for rule in RULES:
        p1 = practice.get(rule, {}).get("reading", "")
        eligible = not p1.startswith("not their practice") and q2[rule] in ("left where seen", "mixed")
        sub = [r for r in rows if r["rule"] == rule and not r["moved"]]
        for scope_name, pool in (("near", [r for r in sub if r["attention"] == "near"]), ("all", sub)):
            new, edited = rate([r for r in pool if not r["decl_in_base_file"]]), rate([r for r in pool if r["decl_in_base_file"]])
            conf = rate([r for r in pool if r["file_rate"] is not None and r["file_rate"] <= 0.10])
            dep_ = rate([r for r in pool if r["file_rate"] is not None and r["file_rate"] >= 0.50])

            def ratio(x, y):
                if x[1] < 10 or y[1] < 10:
                    return "too few"
                if y[0] == 0:
                    return "separates (0 in the second arm)" if x[0] else "neither fixed"
                v = (x[0] / x[1]) / (y[0] / y[1])
                return f"{v:.1f}x " + ("separates" if v >= 2 else "does not")
            tag = "" if eligible or scope_name == "all" else " (not eligible by steps 2-3; descriptive)"
            print(f"  {rule:6} {scope_name:4} new {fmt(new):>10} vs edited {fmt(edited):>10}: {ratio(new, edited):22} | "
                  f"file conforms {fmt(conf):>10} vs file departs {fmt(dep_):>10}: {ratio(conf, dep_)}{tag}")
    print("\nmoved departures:", dict(Counter((r["rule"], r["status"]) for r in rows if r["moved"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
