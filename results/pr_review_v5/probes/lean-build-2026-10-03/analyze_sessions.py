"""Read replay_sessions.py output: one server per session for snippets and edits alike."""
import collections, json, statistics as st, sys

rows = [json.loads(l) for l in open(sys.argv[1])]
calls = [c for s in rows for c in s["rows"]]
print(f"{len(rows)} sessions, {len(calls)} calls ({sum(c['kind'] == 'snippet' for c in calls)} snippets)")
by = collections.defaultdict(list)
for c in calls:
    by[c["route"]].append(c)
print(f"{'route':16} {'n':>4} {'cold med':>9} {'server med':>11} {'cold tot':>9} {'server tot':>11} {'agree':>7}")
for route in sorted(by):
    cs = by[route]
    print(f"{route:16} {len(cs):4d} {st.median(c['cold'] for c in cs):9.1f} {st.median(c['server'] for c in cs):11.2f} "
          f"{sum(c['cold'] for c in cs):9.0f} {sum(c['server'] for c in cs):11.0f} {sum(c['agree'] for c in cs):4d}/{len(cs)}")
for kind in ("snippet", "edit"):
    cs = [c for c in calls if c["kind"] == kind]
    if cs:
        print(f"{kind:7}: cold median {st.median(c['cold'] for c in cs):.1f} s, total {sum(c['cold'] for c in cs):.0f} s | "
              f"server median {st.median(c['server'] for c in cs):.2f} s, total {sum(c['server'] for c in cs):.0f} s "
              f"({sum(c['cold'] for c in cs) / max(1e-9, sum(c['server'] for c in cs)):.1f}x) | agree {sum(c['agree'] for c in cs)}/{len(cs)}")
tc, ts = sum(c["cold"] for c in calls), sum(c["server"] for c in calls)
print(f"all calls: cold {tc:.0f} s, one server per session {ts:.0f} s ({tc / ts:.1f}x)")
per = sorted((sum(c["cold"] for c in s["rows"]) / max(1e-9, sum(c["server"] for c in s["rows"])), len(s["rows"])) for s in rows)
print("per-session speedup (min / median / max):", round(per[0][0], 1), round(per[len(per) // 2][0], 1), round(per[-1][0], 1))
bad = [(s["ws"].split("/")[-1][:20], c["route"], c["cold_errors"], c["server_errors"]) for s in rows for c in s["rows"] if not c["agree"]]
print("disagreements:", bad)
