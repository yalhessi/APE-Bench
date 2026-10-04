import json, statistics as st, sys
from pathlib import Path

rows = [json.loads(l) for l in open(sys.argv[1])]
cold, warm, trunc, trunc_cold = [], [], [], []
agree = disagree = 0
trunc_agree = trunc_disagree = 0
examples = []
print(f"{'file':55} {'lines':>5} {'open':>5} {'base_cold':>9} | {'cold med':>8} {'warm med':>8} {'trunc med':>9} | err-agree")
for r in rows:
    c = [e["cold"] for e in r["edits"]]
    w = [e["warm"] for e in r["edits"]]
    t = [e["trunc"] for e in r["edits"] if e["trunc"] is not None]
    cold += c; warm += w; trunc += t
    trunc_cold += [e["cold"] for e in r["edits"] if e["trunc"] is not None]
    a = 0
    for e in r["edits"]:
        # Strip the baseline: compare only "has errors" and the error texts.
        same = set(e["cold_errs"]) == set(e["warm_errs"])
        a += same
        if same:
            agree += 1
        else:
            disagree += 1
            examples.append((r["rel"], e["mode"], e["cold_errs"][:3], e["warm_errs"][:3]))
        if e["trunc"] is not None:
            # Truncation answers "does the edited declaration compile": compare to errors located
            # anywhere in cold only by presence.
            if bool(e["cold_errs"]) == bool(e["trunc_errs"]):
                trunc_agree += 1
            else:
                trunc_disagree += 1
    print(f"{r['rel'][-55:]:55} {r['lines']:5d} {r['lsp_open']:5.1f} {r['baseline_cold']:9.1f} | "
          f"{st.median(c):8.1f} {st.median(w):8.2f} {(st.median(t) if t else float('nan')):9.2f} | {a}/{len(r['edits'])}"
          f"  base cold/lsp errs {len(r['baseline_cold_errs'])}/{len(r['baseline_lsp_errs'])}")
print()
print(f"edits n={len(cold)}  cold total {sum(cold):.0f}s mean {st.mean(cold):.1f} median {st.median(cold):.1f}")
print(f"           warm total {sum(warm):.0f}s mean {st.mean(warm):.2f} median {st.median(warm):.2f}  ratio of totals {sum(cold)/sum(warm):.1f}x")
if trunc:
    print(f"trunc n={len(trunc)} total {sum(trunc):.1f}s median {st.median(trunc):.2f}; cold on the same edits {sum(trunc_cold):.0f}s -> {sum(trunc_cold)/max(sum(trunc),1e-9):.0f}x")
opens = sum(r["lsp_open"] for r in rows); bcold = sum(r["baseline_cold"] for r in rows)
print(f"file opens total {opens:.0f}s vs cold baseline compiles {bcold:.0f}s")
print(f"session-shaped (baseline + all edits): cold {bcold+sum(cold):.0f}s vs warm {opens+sum(warm):.0f}s -> {(bcold+sum(cold))/(opens+sum(warm)):.1f}x")
print(f"error-set agreement cold vs warm: {agree}/{agree+disagree}; trunc presence agreement {trunc_agree}/{trunc_agree+trunc_disagree}")
for ex in examples[:8]:
    print("  DISAGREE", ex[0], ex[1]); print("     cold:", [s[:140] for s in ex[2]]); print("     warm:", [s[:140] for s in ex[3]])
