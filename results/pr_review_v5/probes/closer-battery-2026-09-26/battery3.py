"""Round 3: the dual-lemma and axiom cases, whose edits replace a whole proof body located by name."""
import json, subprocess, time, os, re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
HERE = Path(__file__).parent
src = (HERE / "battery.py").read_text().split("CASES = [")[0]
ns = {"__file__": str(HERE / "battery.py")}; exec(src, ns)
IL = ("c2a50c83a4e2*+9ba5fc6ff7b4", "Mathlib/Topology/Order/IsLUB.lean")
GR = ("e9a7156e27ed*+80eabfc51d64", "Mathlib/Analysis/ODE/GalerkinRegularity.lean")
def body_of(text, decl):
    """The tactic body of `theorem <decl>`: from its `:= by\\n` to the next blank line."""
    i = text.index(f"theorem {decl} ")
    j = text.index(":= by\n", i) + len(":= by\n")
    k = text.index("\n\n", j) + 1
    return text[j:k]
def axiom_stmt(text, name):
    i = text.index(f"axiom {name} ")
    k = text.index("\n\n", i) + 1
    return text[i:k]
CASES = [
 ("63fdc033749f_inf_via_dual", IL, lambda t: (body_of(t, "Dense.continuous_inf"), "  exact hS.continuous_sup (α := αᵒᵈ) hf h\n")),
 ("63fdc033749f_inf'_via_dual", IL, lambda t: (body_of(t, "Dense.continuous_inf'"), "  exact hS.continuous_sup' (α := αᵒᵈ) hf\n")),
 ("168d80d11d79_parseval_exactq", GR, lambda t: (axiom_stmt(t, "parseval_orthonormal"),
     axiom_stmt(t, "parseval_orthonormal").replace("axiom ", "theorem ", 1).rstrip("\n") + " := by\n  exact?\n")),
]
def run(case):
    name, (wsp, rel), edit = case
    w = ns["ws"](wsp); text = (w / rel).read_text()
    old, new = edit(text); assert text.count(old) == 1, (name, text.count(old)); text = text.replace(old, new)
    d = HERE / name; d.mkdir(exist_ok=True); f = d / "Variant.lean"; f.write_text(text); (d / "edit.txt").write_text(f"--- old\n{old}\n--- new\n{new}")
    t = time.time()
    p = subprocess.run(["lake", "env", "lean", str(f)], cwd=w, env=ns["ENV"], capture_output=True, text=True, timeout=1500)
    if "`module` keyword is experimental" in p.stdout + p.stderr:
        p = subprocess.run(["lake", "env", "lean", "-Dexperimental.module=true", str(f)], cwd=w, env=ns["ENV"], capture_output=True, text=True, timeout=1500)
    r = {"case": name, "exit": p.returncode, "seconds": round(time.time() - t, 1), "stdout": p.stdout[-6000:], "stderr": p.stderr[-2000:]}
    (d / "result.json").write_text(json.dumps(r, indent=1, ensure_ascii=False))
    print(f"{name}: exit {p.returncode} in {r['seconds']}s", flush=True); return r
with ThreadPoolExecutor(max_workers=3) as ex:
    results = list(ex.map(run, CASES))
(HERE / "results3.json").write_text(json.dumps(results, indent=1, ensure_ascii=False)); print("DONE3")
