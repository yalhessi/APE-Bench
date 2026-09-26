"""Lead pipeline vs solo on the same 30 validation asks, both matchers."""
import json, collections
SP="."  # run from this directory: ask_families_SEALED.json, match/ and match_solo/ sit beside it
fam={c:f for pr,d in json.load(open(f"{SP}/ask_families_SEALED.json"))["families"].items() for c,f in d.items()}
def load(d,m): return {a["ask_id"]:a["R1"] for a in json.load(open(f"{SP}/{d}/matches.{m}.json"))["asks"]}
L={m:load("match",m) for m in ("1","2")}; S={m:load("match_solo",m) for m in ("1","2")}
asks=list(L["1"])
print("matcher agreement on solo:", sum(1 for c in asks if S["1"][c]==S["2"][c]), "of", len(asks))
for name,X in (("lead",L),("solo",S)):
    r={m:sum(1 for c in asks if X[m][c]=="reached") for m in X}; p={m:sum(1 for c in asks if X[m][c]=="partial") for m in X}
    print(f"{name}: reached m1 {r['1']} m2 {r['2']} | partial m1 {p['1']} m2 {p['2']}")
tot=collections.Counter(fam.values())
print("\nfamily | asks | lead m1/m2 | solo m1/m2")
for f in sorted(tot, key=lambda x:-tot[x]):
    print(f"  {f:4s} | {tot[f]:2d} | {sum(1 for c in asks if fam[c]==f and L['1'][c]=='reached')}/{sum(1 for c in asks if fam[c]==f and L['2'][c]=='reached')} | {sum(1 for c in asks if fam[c]==f and S['1'][c]=='reached')}/{sum(1 for c in asks if fam[c]==f and S['2'][c]=='reached')}")
both=lambda X,c: X["1"][c]=="reached" and X["2"][c]=="reached"
lb={c for c in asks if both(L,c)}; sb={c for c in asks if both(S,c)}
print(f"\nreached by both matchers: lead {len(lb)}, solo {len(sb)}, both systems {len(lb&sb)}, lead only {sorted(lb-sb)}, solo only {sorted(sb-lb)}, union {len(lb|sb)}")
for d,name in (("match","lead"),("match_solo","solo")):
    u=[json.load(open(f"{SP}/{d}/matches.{m}.json"))["unmatched"] for m in ("1","2")]
    print(f"{name} unmatched findings on ask-bearing PRs: m1 {sum(v['R1'] for v in u[0].values())} m2 {sum(v['R1'] for v in u[1].values())}")
