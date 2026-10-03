import re, sys, glob
from datetime import datetime
from pathlib import Path
ts_re = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)")
pat = re.compile(r"Verification completed, time: ([0-9.]+)s")
for name in sys.argv[1:]:
    r = Path(".ape/runs")/name
    W=C=0; n=0; per=[]
    for log in glob.glob(str(r/"tasks/*/samples/*/attempts/*/logs/scaffold_*.log")):
        first=last=None; c=0
        for line in open(log, errors="replace"):
            m=ts_re.match(line)
            if m:
                t=datetime.strptime(m.group(1),"%Y-%m-%d %H:%M:%S")
                first=first or t; last=t
            m=pat.search(line)
            if m: c+=float(m.group(1))
        if first:
            w=(last-first).total_seconds(); W+=w; C+=c; n+=1; per.append((c/w if w else 0, w/60))
    per.sort()
    print(f"{name}: sessions={n} session-wall={W/60:.0f} min compile={C/60:.0f} min share={C/W:.1%}  max-session-share={per[-1][0]:.0%}")
