"""Read a replay_bench_v2 jsonl: time per edit, the sound-truncation policy, and message agreement."""
import json, statistics as st, sys

rows = [json.loads(l) for l in open(sys.argv[1])]
pp = lambda s: s.replace("↦", "=>")  # noqa: E731  the server prints with Mathlib's pp.unicode.fun
same = lambda a, b, f=lambda s: s: {f(x) for x in a} == {f(x) for x in b}  # noqa: E731

cold, warm, policy = [], [], []
n_sound = 0
err_raw = err_pp = warn_raw = warn_pp = 0
trunc_ok = trunc_n = 0
diffs = []
print(f"{'file':48} {'lines':>5} {'as-is':>5} {'open':>5} {'base':>5} | {'cold':>5} {'warm':>5} {'policy':>6} | errs  warns(pp)")
for r in rows:
    c = [e["cold"] for e in r["edits"]]
    w = [e["warm"] for e in r["edits"]]
    p = [e["trunc"] if (e["trunc_sound"] and e["trunc"] is not None) else e["warm"] for e in r["edits"]]
    cold += c; warm += w; policy += p
    ea = wa = 0
    for e in r["edits"]:
        n_sound += bool(e["trunc_sound"] and e["trunc"] is not None)
        err_raw += same(e["cold_errs"], e["warm_errs"])
        ok_e = same(e["cold_errs"], e["warm_errs"], pp); err_pp += ok_e; ea += ok_e
        warn_raw += same(e["cold_warns"], e["warm_warns"])
        ok_w = same(e["cold_warns"], e["warm_warns"], pp); warn_pp += ok_w; wa += ok_w
        if not (ok_e and ok_w):
            diffs.append((r["rel"].split("/")[-1], e["mode"],
                          sorted({pp(x) for x in e["cold_errs"]} ^ {pp(x) for x in e["warm_errs"]}),
                          sorted({pp(x) for x in e["cold_warns"]} - {pp(x) for x in e["warm_warns"]}),
                          sorted({pp(x) for x in e["warm_warns"]} - {pp(x) for x in e["cold_warns"]})))
        if e["trunc_sound"] and e["trunc"] is not None:
            # A sound cut answers "does the edit compile": errors present iff present in the whole file.
            trunc_n += 1
            trunc_ok += bool(e["cold_errs"]) == bool(e["trunc_errs"])
    print(f"{r['rel'][-48:]:48} {r['lines']:5d} {r['asis_calls']:5d} {r['lsp_open']:5.1f} {r['baseline_cold']:5.1f} | "
          f"{st.median(c):5.1f} {st.median(w):5.2f} {st.median(p):6.2f} | {ea}/{len(c)}  {wa}/{len(c)}")
n = len(cold)
opens = sum(r["lsp_open"] for r in rows); base = sum(r["baseline_cold"] for r in rows)
asis_cold = sum(r["baseline_cold"] * r["asis_calls"] for r in rows)
print()
print(f"edits n={n}: cold median {st.median(cold):.1f} s, total {sum(cold):.0f} s")
print(f"   server, whole file   median {st.median(warm):.2f} s, total {sum(warm):.0f} s ({sum(cold)/sum(warm):.1f}x)")
print(f"   server, sound policy median {st.median(policy):.2f} s, total {sum(policy):.0f} s ({sum(cold)/sum(policy):.1f}x); "
      f"cut on {n_sound}/{n} edits")
print(f"per file, baseline + edits + as-is calls: cold {base + sum(cold) + asis_cold:.0f} s vs server "
      f"{opens + sum(policy):.0f} s ({(base + sum(cold) + asis_cold) / (opens + sum(policy)):.1f}x)")
print(f"errors identical {err_raw}/{n}, after =>/↦ {err_pp}/{n}; warnings identical {warn_raw}/{n}, after =>/↦ {warn_pp}/{n}; "
      f"sound cuts agree on error presence {trunc_ok}/{trunc_n}")
for d in diffs[:10]:
    print("  DIFF", d[0], d[1])
    if d[2]: print("     errors only one side:", [x[:150] for x in d[2]][:3])
    if d[3]: print("     warnings cold only:", [x[:150] for x in d[3]][:3])
    if d[4]: print("     warnings server only:", [x[:150] for x in d[4]][:3])
