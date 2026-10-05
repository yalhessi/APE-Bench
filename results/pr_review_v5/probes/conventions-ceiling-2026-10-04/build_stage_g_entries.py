"""Stage G's rule set: which census entries get a guarded rule. Deterministic, no model.

- `pool`: every entry behind an in-census ask on the ten stage C PRs (`briefs_exact.json`). This is
  the stage's stated leak: the set is chosen knowing the asks, pooled over the PRs. Which of them
  fire on which PR, and where, is decided blind.
- `decoys`: as many entries again, none behind any ask on any of the 14 PRs, taken from what stage
  F's blind selectors picked: the entries selected on the most of the ten PRs, ties broken by
  sha256 of the seed and the id. Their situations do occur in these PRs, and the maintainers asked
  nothing under them.

usage (repo root): python3 <this file> [--write]
"""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
SEED = "stage-g-2026-10-05"
TEN = [30641, 29842, 32875, 30458, 28649, 34091, 41930, 42814, 43167, 42184]
exact = json.loads((HERE / "briefs_exact.json").read_text())["prs"]
applicable = json.loads((HERE / "briefs_applicable.json").read_text())["prs"]
pool = sorted({i for pr in TEN for i in exact[str(pr)]})
behind_an_ask = {i for ids in exact.values() for i in ids}
picked = Counter(i for pr in TEN for i in applicable[str(pr)] if i not in behind_an_ask)
order = sorted(picked, key=lambda i: (-picked[i], hashlib.sha256(f"{SEED}\0{i}".encode()).hexdigest()))
decoys = sorted(order[:len(pool)])
out = {"seed": SEED, "prs": TEN, "pool": pool, "decoys": decoys,
       "decoy_picked_on": {i: picked[i] for i in decoys}}
print(f"pool {len(pool)}: {' '.join(pool)}")
print(f"decoys {len(decoys)}: {' '.join(decoys)}")
print("decoys by PRs that selected them:", dict(sorted(Counter(picked[i] for i in decoys).items(), reverse=True)))
if "--write" in sys.argv:
    (HERE / "stage_g_entries.json").write_text(json.dumps(out, indent=1) + "\n")
