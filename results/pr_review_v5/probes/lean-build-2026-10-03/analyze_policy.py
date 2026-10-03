import json, statistics as st, sys, collections
for f in sys.argv[1:]:
    rows=[json.loads(l) for l in open(f)]
    P=[p for r in rows for p in r["policy"]]
    cold=[p["cold"] for p in P]; t=[p["t"] for p in P]
    routes=collections.Counter(p["route"] for p in P)
    def q(xs,a): xs=sorted(xs); return xs[min(len(xs)-1,int(a*len(xs)))]
    print(f"== {f.split('/')[-1]}: {len(P)} edits, routes {dict(routes)}")
    print(f"   cold   median {st.median(cold):5.1f}  p90 {q(cold,.9):5.1f}  total {sum(cold):5.0f} s")
    print(f"   policy median {st.median(t):5.2f}  p90 {q(t,.9):5.1f}  total {sum(t):5.0f} s  ({sum(cold)/sum(t):.1f}x)")
    nh=[p for p in P if p["route"]!="cold"]
    print(f"   excluding import edits: median {st.median([p['t'] for p in nh]):.2f}, total {sum(p['t'] for p in nh):.0f} s vs cold {sum(p['cold'] for p in nh):.0f} s ({sum(p['cold'] for p in nh)/sum(p['t'] for p in nh):.1f}x)")
    for rt in ("cut","whole","cold"):
        xs=[p["t"] for p in P if p["route"]==rt]
        if xs: print(f"   {rt:5} n={len(xs):2d} median {st.median(xs):5.2f} max {max(xs):5.1f}")
    slow=[(r["rel"].split('/')[-1],p["route"],p["cls"],round(p["t"],1)) for r in rows for p in r["policy"] if p["t"]>5 and p["route"]!="cold"]
    print("   >5 s, not import edits:", slow)
    print("   answers agree with cold:", sum(p["agrees"] for p in P), "/", len(P), [ (r["rel"].split('/')[-1],p["cls"]) for r in rows for p in r["policy"] if not p["agrees"]])
