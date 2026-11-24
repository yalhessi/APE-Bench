"""Replay the combined Lean edit and the saved candidates' merge, without a model."""

import json
import subprocess
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory

from src.mathlib_review.evidence.operators.canonical_api import lean_check_command
from src.mathlib_review.io import jsonl_rows, load_jsonl
from src.mathlib_review.review.finalize import _evidence_specialist_findings
from src.mathlib_review.review.merge import merge_findings
from src.mathlib_review.schema import CandidateClaim
from src.mathlib_review.workspace import tool_env

PROBE = Path(__file__).resolve().parent


def main():
    runs = json.loads((PROBE / "full_tool_reviews.json").read_text())
    comparison, = [r for r in runs if r["arm"] == "comparison"]
    run = Path(comparison["run"])
    root, = json.loads((run / "reviewed_workspaces.json").read_text()).values()
    root = Path(root)
    edit, = comparison["lean_verify_edit"]
    replacement = edit["input"]
    original = (root / replacement["path"]).read_bytes()
    assert sha256(original).hexdigest() == "b20ed2427082b6ce2e1310860b73f3f6a08b9d126b99f6f075723b2b33f8ee57"
    lines = original.decode().splitlines(keepends=True)
    start, end = replacement["line_start"] - 1, replacement["line_end"]
    assert "theorem tprod_nonneg" in "".join(lines[start:end])
    new = replacement["replacement"]
    assert "theorem HasProd.nonneg" in new and "exact h.hasProd.nonneg hf" in new
    assert "[L.NeBot]" not in new.split("theorem tprod_nonneg", 1)[1]
    source = "".join([*lines[:start], new.rstrip("\n") + "\n", *lines[end:]])
    assert sha256(source.encode()).hexdigest() == "167b13e17c284cb270a165522c89a04384909d06931330e0ed844ca0a8b76e79"
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "Replay.lean"
        path.write_text(source)
        subprocess.run(lean_check_command("lake", source, path), cwd=root, env=tool_env(root),
                       check=True, timeout=600)
    print("Combined edit compiled", flush=True)

    candidates = load_jsonl(run / "candidates_discovered.jsonl", CandidateClaim)
    packets = jsonl_rows(run / "evidence/packets.jsonl")
    supported = {packet["candidate_id"] for packet in packets if packet["status"] == "supported"}
    before = _evidence_specialist_findings(candidates, supported, [42184])
    after, conflicts, report = merge_findings(before, pr_finding_limit=None)
    assert {finding.finding_id for finding in after} == {f["finding_id"] for f in comparison["findings"]}
    print("Before merge", [f.admission for f in before])
    print("After merge", report["by_admission"], "conflicts", [c.conflict_id for c in conflicts])


if __name__ == "__main__":
    main()
