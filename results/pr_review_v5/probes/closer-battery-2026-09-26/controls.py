import json, subprocess, time, os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import importlib.util
spec = importlib.util.spec_from_file_location("b", Path(__file__).parent / "battery.py")
# reuse the file table without running its cases
src = (Path(__file__).parent / "battery.py").read_text().split("CASES = [")[0]
ns = {"__file__": str(Path(__file__).parent / "battery.py")}; exec(src, ns)
FILES = {"POS": ns["POS"], "PI": ns["PI"], "PW": ns["PW"], "NC": ns["NC"], "PH": ns["PH"], "DJ": ns["DJ"],
         "RAT": ("26fffffcccd7*+102dba721ebc", "Mathlib/Data/Rat/Lemmas.lean")}
def run(item):
    name, (wsp, rel) = item
    w = ns["ws"](wsp); d = Path(__file__).parent / f"control_{name}"; d.mkdir(exist_ok=True)
    f = d / "Variant.lean"; f.write_text((w / rel).read_text())
    t = time.time()
    p = subprocess.run(["lake", "env", "lean", str(f)], cwd=w, env=ns["ENV"], capture_output=True, text=True, timeout=1500)
    r = {"case": f"control_{name}", "exit": p.returncode, "seconds": round(time.time() - t, 1), "stdout": p.stdout[-6000:], "stderr": p.stderr[-2000:]}
    (d / "result.json").write_text(json.dumps(r, indent=1, ensure_ascii=False))
    print(f"control_{name}: exit {p.returncode} in {r['seconds']}s", flush=True); return r
with ThreadPoolExecutor(max_workers=7) as ex:
    results = list(ex.map(run, FILES.items()))
(Path(__file__).parent / "controls.json").write_text(json.dumps(results, indent=1, ensure_ascii=False))
print("DONE")
