"""One-PR smoke of design D1 (`structured`) with no model call.

Builds the task exactly as `cli run` would for PR 33337 under
configs/designs/structured_dev_claude_sub.yaml, sets it up against the real reviewed workspace,
registers its tools, and drives its own submission by hand: a full ledger (5 declarations x 6
concerns) with five `would_change` cells -- an edit that is the declaration as the PR leaves it
(must compile: verified), an edit with a nonexistent lemma (must not: refuted, with Lean's
error), a `duplicate_of` naming a base-commit declaration (verified by lookup), a `rename_to`
onto a name the library already has (refuted by lookup), and a docstring ask nothing can check
(filed advisory, unverified). The first submission must be handed back naming the two refuted
changes; the second drops the clashing rename and keeps the broken edit past the press bound,
so the record shows every outcome the task can give a change.

What this smoke cannot settle: whether the Claude Code session on the subscription writes this
contract's typed `ledger` and `findings` in one call, and what the per-PR ledger costs in turns
and tokens. That takes the first paid rep.

Run from the repository root, spending nothing:
    PYTHONPATH=$PWD/src ape/bin/python results/pr_review_v5/probes/review-designs-2026-10-02/smoke_structured.py
Writes smoke_structured.json beside this file.
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
CONFIG = ROOT / "configs/designs/structured_dev_claude_sub.yaml"
OUT = Path(__file__).resolve().parent / "smoke_structured.json"
ATTEMPT = ROOT / ".ape/runs/review_designs_smoke_structured/tasks/0/samples/0/attempts/smoke"


def _ledger(names, would_change):
    rows = []
    for name in names:
        for concern in ("proof", "statement", "library", "name", "docstring", "placement"):
            verdict = "would_change" if (name, concern) in would_change else "no_issue"
            rows.append({"declaration": name, "concerns": [concern], "verdict": verdict,
                         "reason": f"smoke: {concern} checked by hand"})
    return rows


async def main() -> int:
    from ape.tasks.base import create_task_from_data
    from ape.tasks.lean_tasks.formal_math.review.structured import (
        LEDGER_PRESSES, LedgerRow, StructuredFinding,
    )
    from mcp.server.fastmcp import FastMCP
    from src.mathlib_review.agenda.cutoffs import cutoffs_by_episode
    from src.mathlib_review.review.runner import (
        _solo_task_data, load_release, load_run, select_units_and_episodes,
    )

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    log = logging.getLogger("smoke")
    record = {"pr": PR, "config": str(CONFIG.relative_to(ROOT)), "steps": []}

    dataset, scaffold, task_overrides = load_run(
        CONFIG, {"dataset": {"run_name": "review_designs_smoke_structured", "pr_numbers": [PR]}})
    release = load_release(dataset)
    units, episodes = select_units_and_episodes(dataset, release)
    agenda = SimpleNamespace(proposals=[SimpleNamespace(episode_id=e.episode_id) for e in episodes])
    [payload] = _solo_task_data(agenda, episodes, dataset, cutoffs_by_episode(episodes),
                                ATTEMPT / "context_trace.jsonl", graphs=release["graphs"])
    names = [row["name"] for row in payload["declarations"]]
    record["task_type"] = payload["task_type"]
    record["declarations"] = payload["declarations"]
    log.info("payload: %s, %d declarations", payload["task_type"], len(names))

    task = create_task_from_data(payload, scaffold, task_config_overrides=task_overrides)
    captured = {}

    async def terminate(result):
        captured["result"] = result

    started = time.monotonic()
    await task.setup(terminate, "review_designs_smoke_structured", ATTEMPT)
    record["setup_seconds"] = round(time.monotonic() - started, 1)
    record["target_workspace"] = {"commit_hash": task.target_workspace.commit_hash,
                                  "path": str(task.target_workspace.path)}
    log.info("workspace %s in %.1fs", task.target_workspace.commit_hash[:24], record["setup_seconds"])

    mcp = FastMCP("smoke")
    await task.register_task_tools(mcp)
    record["tools"] = sorted(tool.name for tool in await mcp.list_tools())
    prompt = await task.create_user_prompt()
    record["prompt_chars"] = len(prompt)
    record["prompt_has_ledger_contract"] = "## The ledger" in prompt and all(
        f"`{name}`" in prompt for name in names)
    log.info("tools %s; prompt %d chars", record["tools"], len(prompt))

    by_name = {row["declaration_name"]: row for row in (
        {"declaration_name": t.declaration_name, "reviewed_code": t.reviewed_code, "path": t.path}
        for g in release["graphs"] if g.pr_number == PR for t in g.targets
        if t.kind == "declaration" and t.declaration_name)}
    pos = "Mathlib/Analysis/InnerProductSpace/Positive.lean"
    sub = "Mathlib/Analysis/InnerProductSpace/Projection/Submodule.lean"
    identity = "Submodule.starProjection_le_starProjection_iff"
    broken = "Submodule.coe_starProjection_eq_isComplProjection"
    dup = "LinearMap.IsSymmetricProjection.le_iff_range_le_range"
    rename = "Submodule.coe_orthogonalProjection_eq_linearProjOfIsCompl"
    docs = "Submodule.orthogonalProjection_apply_eq_linearProjOfIsCompl"
    would_change = {(identity, "proof"), (broken, "proof"), (dup, "library"), (rename, "name"),
                    (docs, "docstring")}

    def findings(*, keep_rename: bool):
        items = [
            {"declaration": identity, "concern": "proof", "path": pos, "line_start": 1,
             "claim": f"{identity}: the proof as the PR leaves it (identity edit; must compile).",
             "suggested_fix": "keep it", "severity": "advisory",
             "edit": {"declaration_name": identity.rsplit(".", 1)[-1],
                      "new_declaration": by_name[identity]["reviewed_code"].strip()}},
            {"declaration": broken, "concern": "proof", "path": sub, "line_start": 1,
             "claim": f"{broken}: a proof by a lemma that does not exist (must be refuted).",
             "suggested_fix": "exact nonexistent_lemma_for_the_smoke", "severity": "blocking",
             "edit": {"declaration_name": broken.rsplit(".", 1)[-1],
                      "new_declaration": (
                          "theorem coe_starProjection_eq_isComplProjection [K.HasOrthogonalProjection] :\n"
                          "    K.starProjection.toLinearMap = K.isCompl_orthogonal_of_hasOrthogonalProjection.projection := by\n"
                          "  exact nonexistent_lemma_for_the_smoke")}},
            {"declaration": dup, "concern": "library", "path": pos, "line_start": 1,
             "claim": f"{dup}: the library has IsCompl.projection_range (lookup must find it).",
             "suggested_fix": "reuse it", "severity": "advisory",
             "duplicate_of": "IsCompl.projection_range"},
            {"declaration": rename, "concern": "name", "path": sub, "line_start": 1,
             "claim": f"{rename}: rename onto a name the library already has (must be refuted).",
             "suggested_fix": "rename", "severity": "advisory",
             **({"rename_to": "Submodule.starProjection"} if keep_rename else {})},
            {"declaration": docs, "concern": "docstring", "path": sub, "line_start": 1,
             "claim": f"{docs}: the docstring should say which projection (nothing can check this).",
             "suggested_fix": "reword the docstring", "severity": "blocking"},
        ]
        return [StructuredFinding(**item) for item in items]

    ledger = [LedgerRow(**row) for row in _ledger(names, would_change)]

    started = time.monotonic()
    first = await task._submit(ledger, findings(keep_rename=True), None, "smoke submission 1")
    record["steps"].append({
        "submission": 1, "seconds": round(time.monotonic() - started, 1),
        "accepted": bool(first["evaluation_result"].success),
        "message": first["evaluation_result"].message,
    })
    log.info("submission 1 (%.0fs): accepted=%s\n%s", record["steps"][-1]["seconds"],
             record["steps"][-1]["accepted"], first["evaluation_result"].message)

    # The reviewer's second move: drop the clashing rename (filed unverified, with the census),
    # keep the broken edit past the press bound so it is recorded refuted, not filed.
    task._refutation_presses = LEDGER_PRESSES
    started = time.monotonic()
    second = await task._submit(ledger, findings(keep_rename=False), None, "smoke submission 2")
    record["steps"].append({
        "submission": 2, "seconds": round(time.monotonic() - started, 1),
        "accepted": bool(second["evaluation_result"].success),
        "message": second["evaluation_result"].message,
    })
    log.info("submission 2 (%.0fs): accepted=%s %s", record["steps"][-1]["seconds"],
             record["steps"][-1]["accepted"], second["evaluation_result"].message)

    result = captured.get("result")
    if result is None:
        record["error"] = "no result was recorded"
        OUT.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
        return 1
    raw = result.model_dump(mode="json")
    record["result"] = {
        "design": raw.get("design"), "episode_id": raw.get("episode_id"),
        "cells": len(raw["ledger"]),
        "cells_by_verdict": {v: sum(1 for c in raw["ledger"] if c["verdict"] == v)
                             for v in sorted({c["verdict"] for c in raw["ledger"]})},
        "would_change_outcomes": {f"{c['declaration']}/{c['concern']}": c.get("outcome")
                                  for c in raw["ledger"] if c["verdict"] == "would_change"},
        "findings": [{k: f.get(k) for k in ("declaration", "concern", "severity", "verified",
                                              "verification", "concern_label", "concern_family",
                                              "issue_kind")}
                     | {"anchor": f.get("anchor"), "evidence": f.get("evidence")}
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
