"""Stage 5 (pre-registered in README.md): the release, and the S0 context file.

  python3 <this file> release <comma-separated PRs> <out_dir>
  python3 <this file> context <probe set yaml> <out.jsonl>

`release` cuts the release for the stage-5 PRs from the sealed val1000 draw; `context` writes each
PR's pass-0 PR model as the solo task's context_file (`probes.model_context`), which S1 then extends
with `cli producer context --base`.

The draw is restricted to the named PRs and written by the writer every evaluation release uses
(`frame.write_evaluation_release`): episodes, events, change graphs, work units, prompts,
inventory, strata. No gold. Run from the repository root with PYTHONPATH=$PWD:$PWD/src.
"""

import json
import sys
from pathlib import Path

from src.datasets.pull_requests.projections.frame import (
    Draw, load_sealed, seal_dir, write_evaluation_release,
)
from src.datasets.pull_requests.store import PullRequestStore

NAME = "val1000-2025-06-2026-03-v1"
if sys.argv[1] == "context":
    from src.mathlib_review.analysis.probes import load_probe_set, model_context

    spec = load_probe_set(Path(sys.argv[2]))
    out = Path(sys.argv[3])
    assert not out.exists(), f"{out} exists"
    out.write_text(model_context(spec, spec.pr_numbers), encoding="utf-8")
    print(f"wrote {out}: {len(spec.pr_numbers)} PRs")
    sys.exit(0)
prs = {int(x) for x in sys.argv[2].split(",")}
out = Path(sys.argv[3])
spec, _members, _seal = load_sealed(NAME)
draw = Draw.model_validate_json((seal_dir(NAME) / "draw.json").read_text(encoding="utf-8"))
missing = prs - {a.pr_number for a in draw.accepted}
assert not missing, f"not in the {NAME} draw: {sorted(missing)}"
restricted = draw.model_copy(update={"accepted": [a for a in draw.accepted if a.pr_number in prs]})
manifest = write_evaluation_release(out, spec, restricted, store=PullRequestStore(),
                                    seal_path=seal_dir(NAME) / "seal.json")
print(json.dumps({"release": str(out), "prs": manifest.pr_numbers,
                  "derived": {ref.path: ref.records for ref in manifest.derived_artifacts}}, indent=1))
