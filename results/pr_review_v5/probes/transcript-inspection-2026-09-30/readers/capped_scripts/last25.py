import pickle, json, sys
sys.path.insert(0, __import__("os").path.dirname(__file__))
from metrics import analyse
SP = __import__("os").path.join(__import__("os").path.dirname(__file__), "out")
S = pickle.load(open(f"{SP}/sessions.pkl", "rb"))
PH = json.load(open(f"{SP}/phantom.json"))
CAPPED = ["42814", "26185", "32080", "34935", "33066", "33145", "33285", "33294", "33321", "33421"]
out = {}
for pr in CAPPED:
    s = next(v for (r, p), v in S.items() if p == pr)
    m, rows = analyse(s)
    N = len(s["turns"]); lo = N - 24
    ph = set(PH[pr]["follow_turns"])
    cls = {}
    for t in range(lo, N + 1):
        rs = [r for r in rows if r["turn"] == t]
        if any(r["name"] == "lean_verify_edit" and r["has_new"] for r in rs): c = "construct"
        elif t in ph: c = "phantom_follow"
        elif rs and all(r["kind"] in ("exact", "near") for r in rs): c = "repeat"
        elif any(r["err"] for r in rs) and all(r["err"] or r["kind"] != "new" for r in rs): c = "tool_error"
        else: c = "new_lookup"
        cls[t] = c
    from collections import Counter
    out[pr] = dict(window=f"T{lo}-T{N}", counts=dict(Counter(cls.values())), per_turn=cls)
    print(pr, out[pr]["window"], out[pr]["counts"])
json.dump(out, open(f"{SP}/last25.json", "w"), indent=1)
