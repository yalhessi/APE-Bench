"""Build the step-4 audit packet (PROTOCOL.md, step 4 amendment): one entry per check row with the rule's
trigger and check text, the row's verdict and evidence, and where the reviewed code is. Nothing the auditor
may not see goes in: no reader label, note, `asked` flag, role or score.

usage (repo root): ape/bin/python <this file> <out.json>
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
sys.path.insert(0, str(Path.cwd() / "src"))
from src.mathlib_review.io import jsonl_rows  # noqa: E402

HERE = Path(__file__).resolve().parent
RULES = Path("results/pr_review_v5/probes/conventions-ceiling-2026-10-04/rules.json")
CFG = "configs/pr_review_v5_stage_h_v1_build.yaml"
WS = Path("data/code_execute/repos/mathlib4/workspaces")


def main(out: str) -> int:
    rules = {r["id"]: r for r in json.loads(RULES.read_text())}
    key = {row["item"]: row for row in jsonl_rows(HERE / "step3_items.jsonl")}
    listing = subprocess.run([sys.executable, "-m", "src.mathlib_review.release.prebuild", "--reviewed", "--config", CFG],
                             capture_output=True, text=True).stdout
    ws = {int(p[1]): p[2] for p in (line.split() for line in listing.splitlines() if line.strip().startswith("PR "))}
    rows = []
    for path in sorted((HERE / "checks").glob("*.jsonl")):
        for c in jsonl_rows(path):
            k, r = key[c["item"]], rules[c["rule"]]
            rows.append({"item": c["item"], "pr": k["pr"], "file": k["file"], "declaration": k["declaration"],
                         "reviewed_code": str(WS / ws[k["pr"]] / k["file"]),
                         "rule": c["rule"], "applies_to": r["applies_to"], "trigger": r["trigger"],
                         "required": r["required"], "check": r["check"], "not_when": r.get("not_when", ""),
                         "verdict": c["verdict"], "calls": c.get("calls"),
                         "compiled_candidates": c.get("compiled_candidates"), "evidence": c["evidence"]})
    Path(out).write_text(json.dumps(rows, ensure_ascii=False, indent=1))
    print(f"{len(rows)} rows -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
