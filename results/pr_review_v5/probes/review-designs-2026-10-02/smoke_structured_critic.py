"""One-PR smoke of design D2 (`structured_critic`) with no model call.

Reads D1's smoke as its first stage -- `stage_structured/ledgers.jsonl`, the row the runner's
`_ledger_rows` wrote from the D1 smoke's result (run `smoke_structured.py` first) -- through the
runner's own `stage_rows_for`, which reads a stage run with `StageInput` and checks it covers the
PR set. Then builds the critic task exactly as `cli run --of <run>` would for PR 33337 under
configs/designs/structured_critic_dev_claude_sub.yaml, sets it up against the real reviewed
workspace, and drives its own submission by hand:

- every `no_issue` cell conceded except two overturned: an edit to
  `coe_orthogonalProjection_eq_linearProjOfIsCompl`'s proof that is the declaration as the PR
  leaves it (must compile: verified), and a rename of `le_iff_range_le_range` onto a name the
  library already has (must be refuted and handed back; resubmitted without the name, it files
  unverified);
- D1's five `would_change` cells: the identity edit refuted (a label: the finding stays in the
  union), the duplicate and the docstring confirmed, the rename undecided, the change the tools
  refuted at D1 refuted.

What this smoke cannot settle: whether a Claude Code session argues with a ledger in this form,
and what a critic session costs; that is D2's first paid rep, after D1's.

Run from the repository root, spending nothing:
    PYTHONPATH=$PWD/src ape/bin/python results/pr_review_v5/probes/review-designs-2026-10-02/smoke_structured_critic.py
Writes smoke_structured_critic.json beside this file.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

PR = 33337
CONFIG = ROOT / "configs/designs/structured_critic_dev_claude_sub.yaml"
HERE = Path(__file__).resolve().parent
STAGE_DIR = HERE / "stage_structured"
STAGE_RUN = "review_designs_smoke_structured"
OUT = HERE / "smoke_structured_critic.json"
ATTEMPT = ROOT / ".ape/runs/review_designs_smoke_structured_critic/tasks/0/samples/0/attempts/smoke"


async def main() -> int:
    from ape.tasks.base import create_task_from_data
    from ape.tasks.lean_tasks.formal_math.review.structured import LEDGER_PRESSES, StructuredFinding
    from ape.tasks.lean_tasks.formal_math.review.structured_critic import Rebuttal
    from mcp.server.fastmcp import FastMCP
    from src.mathlib_review import run_state
    from src.mathlib_review.agenda.cutoffs import cutoffs_by_episode
    from src.mathlib_review.review.runner import (
        _solo_task_data, load_release, load_run, select_units_and_episodes, stage_rows_for,
    )

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    log = logging.getLogger("smoke")
    if not (STAGE_DIR / "ledgers.jsonl").is_file():
        print("run smoke_structured.py first: it writes the stage row this smoke reads")
        return 1
    record = {"pr": PR, "config": str(CONFIG.relative_to(ROOT)), "stage_run": STAGE_RUN}

    dataset, scaffold, task_overrides = load_run(CONFIG, {"dataset": {
        "run_name": "review_designs_smoke_structured_critic", "pr_numbers": [PR]}})
    dataset.stage_input_run = STAGE_RUN
    release = load_release(dataset)
    units, episodes = select_units_and_episodes(dataset, release)
    # The smoke's stage run lives beside this script, not under results/pr_review_v5/runs/, so
    # `StageInput.of` is pointed at it; everything after the lookup is the runner's own code.
    original_of = run_state.StageInput.of
    run_state.StageInput.of = classmethod(lambda cls, name, **kw: cls.at(STAGE_DIR, run_name=name, **kw))
    try:
        stage_rows = stage_rows_for(dataset, [PR], log)
    finally:
        run_state.StageInput.of = original_of
    agenda = SimpleNamespace(proposals=[SimpleNamespace(episode_id=e.episode_id) for e in episodes])
    [payload] = _solo_task_data(agenda, episodes, dataset, cutoffs_by_episode(episodes),
                                ATTEMPT / "context_trace.jsonl", graphs=release["graphs"],
                                stage_rows=stage_rows)
    from ape.tasks.lean_tasks.formal_math.review import DESIGNS

    record["task_type"] = payload["task_type"]
    record["payload_line"] = DESIGNS["structured_critic"].describe_design_payload(payload)
    log.info("payload: %s; %s", payload["task_type"], record["payload_line"])

    task = create_task_from_data(payload, scaffold, task_config_overrides=task_overrides)
    captured = {}

    async def terminate(result):
        captured["result"] = result

    await task.setup(terminate, "review_designs_smoke_structured_critic", ATTEMPT)
    record["target_workspace"] = task.target_workspace.commit_hash
    mcp = FastMCP("smoke")
    await task.register_task_tools(mcp)
    record["tools"] = sorted(tool.name for tool in await mcp.list_tools())
    prompt = await task.create_user_prompt()
    record["prompt_chars"] = len(prompt)
    record["prompt_renders_the_stage"] = ("## The first stage's ledger, and your task" in prompt
                                          and "Refuted at the first stage's submission" in prompt)
    log.info("tools %s; prompt %d chars", record["tools"], len(prompt))

    by_name = {t.declaration_name: t for g in release["graphs"] if g.pr_number == PR
               for t in g.targets if t.kind == "declaration" and t.declaration_name}
    sub = "Mathlib/Analysis/InnerProductSpace/Projection/Submodule.lean"
    pos = "Mathlib/Analysis/InnerProductSpace/Positive.lean"
    overturn_proof = "Submodule.coe_orthogonalProjection_eq_linearProjOfIsCompl"
    overturn_name = "LinearMap.IsSymmetricProjection.le_iff_range_le_range"
    identity = "Submodule.starProjection_le_starProjection_iff"
    positions_for_filed = {
        (identity, "proof"): "refute",
        ("LinearMap.IsSymmetricProjection.le_iff_range_le_range", "library"): "confirm",
        ("Submodule.orthogonalProjection_apply_eq_linearProjOfIsCompl", "docstring"): "confirm",
        ("Submodule.coe_orthogonalProjection_eq_linearProjOfIsCompl", "name"): "undecided",
        ("Submodule.coe_starProjection_eq_isComplProjection", "proof"): "refute",
    }
    overturned = {(overturn_proof, "proof"), (overturn_name, "name")}
    rebuttals = []
    for cell in payload["stage"]["ledger"]:
        key = (cell["declaration"], cell["concern"])
        position = (positions_for_filed[key] if cell["verdict"] == "would_change"
                    else "overturn" if key in overturned else "concede")
        rebuttals.append(Rebuttal(declaration=key[0], concerns=[key[1]], position=position,
                                  reason=f"smoke: {position} on {key[1]}"))

    def findings(*, keep_rename: bool):
        return [
            StructuredFinding(
                declaration=overturn_proof, concern="proof", path=sub, line_start=1,
                claim=f"{overturn_proof}: the proof as the PR leaves it (identity edit; must compile).",
                suggested_fix="keep it", severity="advisory",
                edit={"declaration_name": overturn_proof.rsplit(".", 1)[-1],
                      "new_declaration": by_name[overturn_proof].reviewed_code.strip()}),
            StructuredFinding(
                declaration=overturn_name, concern="name", path=pos, line_start=1,
                claim=f"{overturn_name}: rename onto a name the library already has (must be refuted).",
                suggested_fix="rename", severity="advisory",
                **({"rename_to": "Submodule.starProjection"} if keep_rename else {})),
        ]

    steps = []
    started = time.monotonic()
    first = await task._submit_critique(rebuttals, findings(keep_rename=True), None, "critic smoke 1")
    steps.append({"submission": 1, "seconds": round(time.monotonic() - started, 1),
                  "accepted": bool(first["evaluation_result"].success),
                  "message": first["evaluation_result"].message})
    log.info("submission 1 (%.0fs): accepted=%s\n%s", steps[-1]["seconds"], steps[-1]["accepted"],
             steps[-1]["message"])
    started = time.monotonic()
    second = await task._submit_critique(rebuttals, findings(keep_rename=False), None, "critic smoke 2")
    steps.append({"submission": 2, "seconds": round(time.monotonic() - started, 1),
                  "accepted": bool(second["evaluation_result"].success),
                  "message": second["evaluation_result"].message})
    log.info("submission 2 (%.0fs): accepted=%s %s", steps[-1]["seconds"], steps[-1]["accepted"],
             steps[-1]["message"])
    record["steps"] = steps
    result = captured.get("result")
    if result is None:
        record["error"] = "no result was recorded"
        OUT.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
        return 1
    raw = result.model_dump(mode="json")
    positions = {}
    for row in raw["rebuttals"]:
        positions[row["position"]] = positions.get(row["position"], 0) + 1
    record["result"] = {
        "design": raw["design"], "stage_run": raw["stage_run"], "cells": len(raw["ledger"]),
        "positions": dict(sorted(positions.items())),
        "union": [{k: f.get(k) for k in ("stage", "stages", "critic", "agreed", "declaration",
                                          "concern", "severity", "verified", "verification")}
                  for f in raw["findings"]],
        "refuted": [{"declaration": r["declaration"], "concern": r["concern"],
                     "evidence": r["evidence"]} for r in raw["refuted"]],
    }
    OUT.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    log.info("wrote %s", OUT)
    print(json.dumps(record["result"], indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
