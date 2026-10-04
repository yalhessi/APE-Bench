import re, sys, glob, os, statistics as st
from pathlib import Path
pat = re.compile(r"Verification completed, time: ([0-9.]+)s")
to = re.compile(r"Lean verification timeout")
runs = sorted(Path(".ape/runs").iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
rows=[]
allt=[]
for r in runs[: int(sys.argv[1]) if len(sys.argv)>1 else 40]:
    if r.name.startswith("pr_review_v5_judge"): continue
    ts=[]; tos=0; sessions=0
    for log in glob.glob(str(r/"tasks/*/samples/*/attempts/*/logs/scaffold_*.log")):
        sessions+=1
        with open(log, errors="replace") as f:
            for line in f:
                m=pat.search(line)
                if m: ts.append(float(m.group(1)))
                elif to.search(line): tos+=1
    if not ts: continue
    ts.sort(); allt+=ts
    q=lambda p: ts[min(len(ts)-1,int(p*len(ts)))]
    rows.append((r.name[:60], sessions, len(ts), sum(ts)/60, st.median(ts), q(.9), ts[-1], tos))
print(f"{'run':60} {'sess':>5} {'n':>5} {'min':>7} {'med':>6} {'p90':>6} {'max':>6} {'tmo':>4}")
for x in rows: print(f"{x[0]:60} {x[1]:5d} {x[2]:5d} {x[3]:7.1f} {x[4]:6.1f} {x[5]:6.1f} {x[6]:6.1f} {x[7]:4d}")
allt.sort()
print("ALL n=",len(allt),"total min=",round(sum(allt)/60,1),"median",st.median(allt),"p90",allt[int(.9*len(allt))],"p99",allt[int(.99*len(allt))])
