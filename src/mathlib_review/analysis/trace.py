"""One number, followed back to the bytes behind it, for either evaluation instrument.

A report row says a session reached an ask, or a run hit an obligation. Until 2026-10-22 answering
"which finding, as the matcher saw it, under which seal, judged by which verdict, from which run" took
the probe's author: the matcher's inputs were outside the repository, and the judge's pairs, verdicts,
votes and tasks were four files and an orchestrator tree joined by hand. `cli report trace` is that
join, done one way:

- **a matching cell** (`trace_matching`): the plan and its identity, the seal label the session wore
  on that PR, the exact finding list that label showed and its digest, each replicate's value and
  the finding it chose, where that verdict's bytes are (a task attempt or an imported file and its
  digest), and the session's own findings in their source with their output channel.
- **a judged obligation** (`trace_judgment`): the audit's identity, the obligation's status, every
  pair planned for it (tier, role, prompt digest), each pair's verdict and sample votes, the finding
  text the judge read, and the judge task's directory and attempts.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.mathlib_review.io import canonical_json_bytes, jsonl_rows, sha256_bytes


# --- A matching cell -----------------------------------------------------------------------------


def trace_matching(plan_dir: Path, pr: int, ask_id: str, session: str) -> Dict[str, Any]:
    """One cell, followed to its bytes: the label, what that label showed, each replicate's verdict
    and where it is, and the reviewer's own finding in its source."""

    from src.mathlib_review.analysis import probes
    from src.mathlib_review.analysis.matching import (
        PLAN_FILE, load_plan, plan_dir_of, replicate_tables, verdict_rows,
    )

    plan_dir = plan_dir_of(Path(plan_dir))
    plan = load_plan(plan_dir)
    labels = plan.seal.get(str(pr))
    if labels is None:
        raise ValueError(f"PR {pr} is not in plan {plan.plan_id}")
    label = next((lab for lab, s in labels.items() if s == session), None)
    if label is None:
        raise ValueError(f"session {session!r} is not sealed on PR {pr}: {sorted(labels.values())}")
    packet = next(p for p in plan.packets if p.pr == int(pr))
    ask = next((a for a in packet.asks if a.ask_id == ask_id), None)
    if ask is None:
        raise ValueError(f"PR {pr} has no ask {ask_id!r} in plan {plan.plan_id}")
    shown = [f.model_dump(mode="json") for f in packet.reviewers[label]]
    subject = next(s for s in plan.identity.subjects if s.session == session)
    batch_prs = {b.batch_id: b.prs for b in plan.batches}
    cells = []
    for rep, table in replicate_tables(plan, verdict_rows(plan_dir, plan.plan_id)).items():
        row = next((a for a in table["matches"]["asks"]
                    if int(a.get("pr")) == int(pr) and a.get("ask_id") == ask_id), None)
        index = row.get(f"{label}_finding") if row else None
        where = next((r for r in table["rows"]
                      if r["batch_id"] == "*" or int(pr) in batch_prs.get(r["batch_id"], [])), None)
        cells.append({
            "replicate": rep, "value": row.get(label) if row else "(no verdict)",
            "finding": index, "note": row.get("note") if row else None,
            "shown_finding": (shown[index] if isinstance(index, int) and 0 <= index < len(shown)
                              else None),
            "verdict_bytes": where})
    return {
        "plan": {"plan_id": plan.plan_id, "path": str(plan_dir / PLAN_FILE),
                 "sha256": plan.source_sha256, "identity_sha256": plan.identity_sha256,
                 "instrument": f"{plan.identity.instrument}/{plan.identity.instrument_version}",
                 "question_policy": plan.identity.question_policy},
        "seal": {"path": plan.identity.seal_path, "sha256": plan.identity.seal_sha256,
                 "pr": int(pr), "session": session, "label": label},
        "ask": ask.model_dump(mode="json"),
        "shown": {"label": label, "findings": shown,
                  "sha256": sha256_bytes(canonical_json_bytes(shown))},
        "subject": subject.model_dump(mode="json"),
        "original": _original_findings(probes, subject, int(pr)),
        "cells": cells,
    }


def _original_findings(probes, subject, pr: int) -> Optional[Dict[str, Any]]:
    """Where the session's findings for this PR came from, and the findings themselves."""

    if subject.source == "solo":
        for run in subject.runs:
            found = probes._solo(run).get(pr)
            if found is not None:
                return {"run": run, "channel": subject.channel, "findings": found[0],
                        "where": f".ape/runs/{run}/tasks/*/task_result.json (PR {pr})"}
        return None
    if subject.source == "lead":
        return {"run": subject.runs[0], "channel": subject.channel,
                "where": f"results/pr_review_v5/runs/{subject.runs[0]}/findings.jsonl (PR {pr})"}
    if subject.source == "findings_file":
        return {"path": subject.path, "channel": subject.channel,
                "findings": json.loads(Path(subject.path).read_text()).get(str(pr))}
    return {"channel": subject.channel, "where": "the probe session's findings.json"}


# --- A judged obligation -------------------------------------------------------------------------


def trace_judgment(run_name: str, obligation_id: str, node: str = "judge",
                   ape_root: Path = Path(".ape/runs")) -> Dict[str, Any]:
    """One obligation of a judged run, followed to its pairs, verdicts, votes, findings and tasks."""

    from src.mathlib_review.judge.runner import derive_from_run

    derived = derive_from_run(run_name, node)
    audit = Path(derived["out_dir"])
    report_path = audit / "semantic_report.json"
    if not report_path.is_file():
        raise ValueError(f"no judge audit at {audit} for run {run_name} (node {node})")
    report = json.loads(report_path.read_text())
    status = next((row for row in report.get("per_obligation") or []
                   if row.get("obligation_id") == obligation_id), None)
    if status is None:
        raise ValueError(f"{obligation_id} is not in the audit's denominator ({audit})")
    pairs = [row for row in jsonl_rows(audit / "semantic_pairs.jsonl")
             if row.get("obligation_id") == obligation_id]
    matches = {row.get("pair_id"): row for row in jsonl_rows(audit / "semantic_matches.jsonl")
               if row.get("obligation_id") == obligation_id}
    votes_path = audit / "sample_votes.jsonl"
    votes = {row["candidate_id"]: row for row in (jsonl_rows(votes_path) if votes_path.is_file()
                                                  else [])
             if row.get("obligation_id") == obligation_id}
    findings_path = Path(derived["candidates"])
    findings = {}
    if findings_path.is_file():
        wanted = {p["candidate_id"] for p in pairs}
        for row in jsonl_rows(findings_path):
            key = row.get("finding_id") or row.get("candidate_id")
            if key in wanted:
                findings[key] = {k: row.get(k) for k in
                                 ("claim", "requested_change", "suggested_fix", "anchor",
                                  "admission", "concern_family")}
    tasks = asyncio.run(_judge_tasks(Path(ape_root) / derived["run_name"] / "tasks",
                                     obligation_id))
    return {
        "audit": {"path": str(audit), "report": str(report_path),
                  "measurement": report.get("measurement")
                  or "unrecorded (judged before 2026-10-22)",
                  "judge_identity": report.get("judge_identity")},
        "obligation": status,
        "pairs": [{**{k: p.get(k) for k in ("pair_id", "candidate_id", "pairing_tier", "role",
                                             "tier_justification", "prompt_sha256",
                                             "candidate_source_sha256")},
                   "verdict": {k: matches.get(p.get("pair_id"), {}).get(k)
                               for k in ("issue_match", "resolution_match", "abstain", "reason")}
                   if p.get("pair_id") in matches else "(no verdict)",
                   "votes": votes.get(p.get("candidate_id")),
                   "finding": findings.get(p.get("candidate_id")),
                   "task": tasks.get(p.get("candidate_id"))}
                  for p in pairs],
    }


async def _judge_tasks(tasks_dir: Path, obligation_id: str) -> Dict[str, Dict[str, Any]]:
    """{candidate_id: the judge task's directory and attempts}, read through `TaskStorage`."""

    from ape.orchestration.persistence import TaskStorage

    found: Dict[str, Dict[str, Any]] = {}
    if not tasks_dir.is_dir():
        return found
    for task_dir in sorted(p for p in tasks_dir.iterdir() if p.is_dir()):
        storage = TaskStorage(task_dir, task_dir.name)
        result = await storage.load_task_result()
        if not result or result.get("obligation_id") != obligation_id:
            continue
        samples = await storage.load_all_samples()
        found[result.get("candidate_id")] = {
            "task_dir": str(task_dir),
            "attempts": [str(a.path) for _i, s in sorted(samples.items()) for a in s.attempts]}
    return found
