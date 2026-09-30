"""Exact repeats of calls whose earlier identical call already returned a negative (error, 0 matches,
'No declaration', compile failure) -- a direct sign the session did not retain the earlier answer.
Also reasoning/zero-reasoning by 20-turn bucket, cumulative processed tokens."""
import pickle, json, collections, statistics
SP = __import__("os").path.join(__import__("os").path.dirname(__file__), "out")
S = pickle.load(open(f"{SP}/sessions.pkl", "rb"))
CAPPED = {"42814", "26185", "32080", "34935", "33066", "33145", "33285", "33294", "33321", "33421"}
def negative(c):
    r = c["res"] or ""
    return (c["rsum"].startswith("ERROR") or '"files_with_matches": 0' in r or "No declaration of" in r
            or '"success": false' in r)
out = {}
for (run, pr), s in S.items():
    seen = {}
    rep_neg = rep_any = 0
    rep_neg_list = []
    for t in s["turns"]:
        for c in t["calls"]:
            k = (c["name"], json.dumps(c["input"], sort_keys=True))
            if k in seen:
                rep_any += 1
                if seen[k][1]:
                    rep_neg += 1; rep_neg_list.append((seen[k][0], t["turn"], c["name"], json.dumps(c["input"])[:90]))
            else:
                seen[k] = (t["turn"], negative(c))
    T = s["turns"]
    buckets = []
    for a in range(0, 80, 20):
        b = T[a:a+20]
        if not b: continue
        buckets.append(dict(turns=f"{a+1}-{a+len(b)}", mean_reasoning=round(statistics.mean(x["reasoning"] or 0 for x in b)),
                            zero_r=sum(1 for x in b if (x["reasoning"] or 0) == 0), calls_per_turn=round(statistics.mean(len(x["calls"]) for x in b), 2)))
    cum = sum((x["prompt"] or 0) + (x["completion"] or 0) for x in T)
    after40 = sum((x["prompt"] or 0) + (x["completion"] or 0) for x in T[40:])
    out[pr] = dict(capped=pr in CAPPED, exact_repeats=rep_any, repeats_of_negative=rep_neg, examples=rep_neg_list[:6],
                   buckets=buckets, processed_tokens=cum, processed_after_t40=after40,
                   zero_reasoning_frac=round(sum(1 for x in T if (x["reasoning"] or 0) == 0) / len(T), 2))
json.dump(out, open(f"{SP}/memloss.json", "w"), indent=1)
for pr, v in sorted(out.items(), key=lambda kv: (not kv[1]["capped"], kv[0])):
    print(pr, "Y" if v["capped"] else "-", "rep", v["exact_repeats"], "rep_neg", v["repeats_of_negative"], "zeroR", v["zero_reasoning_frac"],
          "proc", v["processed_tokens"], "after40", v["processed_after_t40"], [ (b["turns"], b["mean_reasoning"], b["zero_r"]) for b in v["buckets"]])
cap = [v for v in out.values() if v["capped"]]; unc = [v for v in out.values() if not v["capped"]]
print("zero-reasoning frac capped", round(statistics.mean(v["zero_reasoning_frac"] for v in cap), 2), "uncapped", round(statistics.mean(v["zero_reasoning_frac"] for v in unc), 2))
