"""Inspection and comparison: one number followed back to its bytes, and two numbers set side by side.

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
from typing import Any, Dict, List, Optional, Sequence

from src.mathlib_review.io import canonical_json_bytes, jsonl_rows, sha256_bytes


# --- A matching cell -----------------------------------------------------------------------------


def trace_matching(plan_dir: Path, pr: int, ask_id: str, session: str,
                   producer: Optional[str] = None) -> Dict[str, Any]:
    """One cell, followed to its bytes: the label, what that label showed, each observation's
    verdict and where it is, and the reviewer's own finding in its source. `producer` restricts the
    observations to one execution or import; otherwise every one held is shown, each named."""

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
    rows = verdict_rows(plan_dir, plan.plan_id)
    if producer is not None:
        rows = [r for r in rows if r.producer == producer]
    for rep, table in replicate_tables(plan, rows).items():
        row = next((a for a in table["matches"]["asks"]
                    if int(a.get("pr")) == int(pr) and a.get("ask_id") == ask_id), None)
        index = row.get(f"{label}_finding") if row else None
        where = next((r for r in table["rows"]
                      if r["batch_id"] == "*" or int(pr) in batch_prs.get(r["batch_id"], [])), None)
        cells.append({
            "replicate": rep, "producer": table["producer"],
            "value": row.get(label) if row else "(no verdict)",
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


def _reviewer_inputs(run: str, pr: int) -> Dict[str, Any]:
    """What that run's reviewer of this PR was given (`run_inputs`), or why it cannot be said."""

    try:
        return run_inputs(run, pr=pr)
    except (ValueError, FileNotFoundError) as error:
        return {"unavailable": str(error)}


def _original_findings(probes, subject, pr: int) -> Optional[Dict[str, Any]]:
    """Where the session's findings for this PR came from, and the findings themselves."""

    if subject.source == "solo":
        for run in subject.runs:
            found = probes._solo(run).get(pr)
            if found is not None:
                return {"run": run, "channel": subject.channel, "findings": found[0],
                        "where": f".ape/runs/{run}/tasks/*/task_result.json (PR {pr})",
                        "reviewer_inputs": _reviewer_inputs(run, pr)}
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


# --- What a run's reviewers were given -----------------------------------------------------------


def run_inputs(run_name: str, pr: Optional[int] = None, full: bool = False,
               ape_root: Path = Path(".ape/runs")) -> Dict[str, Any]:
    """What one run's reviewers were given, from the run's own records, never today's files.

    The route the run executed on; each input file the task config names, with the digest the
    plan sealed, the snapshot of those bytes, and whether the file on disk still matches; and per
    attempt, the first messages as its transcript stored them and the tools it was offered. What
    a route does not record -- the Claude Code CLI's own system prompt and the MCP tool schemas it
    served -- is named as such rather than reconstructed.
    """

    from src.mathlib_review.paths import run_dir
    from src.mathlib_review.review.inputs import INPUT_FILE_FIELDS, SNAPSHOT_DIR

    root = Path(ape_root) / run_name
    config_path = root / "config.json"
    if not config_path.is_file():
        raise ValueError(f"no orchestrator record at {config_path}; transcripts live only under the "
                         "gitignored .ape/runs/ of the machine that ran it")
    config = json.loads(config_path.read_text()).get("config") or {}
    llm = config.get("llm_config") or {}
    route = {"scaffold": config.get("scaffold_type"),
             "model": config.get("claude_model") or llm.get("model_name"),
             "cli_version": config.get("cli_version"), "effort": config.get("effort")}
    overrides = config.get("task_config_overrides") or {}

    results = run_dir(run_name)
    plan_file = results / "run_plan.json"
    plans = ([plan_file] if plan_file.is_file() else []) + sorted(
        results.glob("run_plan_revision_*.json"))
    sealed = {}
    for path in plans:
        sealed.update((json.loads(path.read_text()).get("evaluation_settings") or {})
                      .get("input_files") or {})
    index_path = results / SNAPSHOT_DIR / "index.json"
    index = json.loads(index_path.read_text()) if index_path.is_file() else {}
    files = {}
    for field in INPUT_FILE_FIELDS:
        value = overrides.get(field)
        if value in (None, "", "None"):
            continue
        path = Path(value)
        current = sha256_bytes(path.read_bytes()) if path.is_file() else None
        seal = sealed.get(field)
        files[field] = {
            "path": str(path), "sealed_sha256": seal, "current_sha256": current,
            "snapshot": (index.get(field) or {}).get("snapshot"),
            "status": ("not recorded when the plan was sealed: the file on disk now is not "
                       "necessarily what the sessions read" if seal is None else
                       "unchanged since sealed" if seal == current else
                       "changed since sealed: read the snapshot, not the path")}

    attempts = asyncio.run(_attempts(root / "tasks", pr))
    shown = []
    for item in attempts:
        transcript = _first_messages(Path(item["attempt"]), route["scaffold"])
        if not full:
            for key in ("system", "user"):
                text = transcript.get(key)
                if isinstance(text, str):
                    transcript[key] = {"sha256": sha256_bytes(text.encode("utf-8")),
                                       "chars": len(text), "head": text[:300]}
        shown.append({**item, **transcript})
    return {"run": run_name, "route": route, "input_files": files,
            "plans": [str(p) for p in plans], "attempts": shown}


async def _attempts(tasks_dir: Path, pr: Optional[int]) -> List[Dict[str, Any]]:
    """Every attempt directory of the run's top-level tasks, with the PR each reviewed."""

    import re

    from ape.orchestration.persistence import TaskStorage

    found: List[Dict[str, Any]] = []
    if not tasks_dir.is_dir():
        return found
    for task_dir in sorted(p for p in tasks_dir.iterdir() if p.is_dir()):
        storage = TaskStorage(task_dir, task_dir.name)
        result = await storage.load_task_result() or {}
        outcome_path = task_dir / "task_outcome.json"
        task_id = (result.get("task_id")
                   or (json.loads(outcome_path.read_text()).get("task_id")
                       if outcome_path.is_file() else ""))
        number = result.get("pr_number")
        if number is None:
            match = re.search(r"_(\d+)_round", str(task_id))
            number = int(match.group(1)) if match else None
        if pr is not None and number != pr:
            continue
        samples = await storage.load_all_samples()
        for index, sample in sorted(samples.items()):
            for attempt in sample.attempts:
                found.append({"task_dir": str(task_dir), "task_id": task_id, "pr": number,
                              "sample": index, "attempt": str(attempt.path),
                              "status": str(getattr(attempt.status, "value", attempt.status))})
    return found


def _content_text(content) -> str:
    if isinstance(content, list):
        return "".join(block.get("text", "") for block in content if isinstance(block, dict))
    return "" if content is None else str(content)


def _first_messages(attempt: Path, scaffold: Optional[str]) -> Dict[str, Any]:
    """The first system and user messages and the tools, as this attempt's transcript holds them."""

    sessions = sorted(attempt.glob("ape_agent_session_*.jsonl"))
    if sessions:
        rows = jsonl_rows(sessions[-1])
        first = {}
        for row in rows:
            kind = row.get("type")
            if kind in ("system", "user") and kind not in first:
                first[kind] = _content_text((row.get("message") or {}).get("content"))
        definitions = next((row for row in rows if row.get("type") == "tool_definitions"), None)
        tools = list(((definitions or {}).get("message") or {}).get("tools") or [])
        return {"transcript": str(sessions[-1]), "system": first.get("system"),
                "user": first.get("user"),
                "tools": [t.get("function", {}).get("name") for t in tools],
                "tool_schemas_sha256": sha256_bytes(canonical_json_bytes(tools)) if tools else None,
                "opaque": []}
    conversations = sorted(attempt.glob("claude_code_conversation_*.jsonl"))
    if conversations:
        rows = jsonl_rows(conversations[-1])
        user = next((_content_text((row.get("message") or {}).get("content"))
                     for row in rows if row.get("type") == "user"), None)
        session_path = attempt / "claude_code_session.json"
        init = (json.loads(session_path.read_text()).get("init") or {}) if session_path.is_file() else {}
        return {"transcript": str(conversations[-1]), "system": None, "user": user,
                "tools": init.get("tools"),
                "observed": {"model": init.get("model"),
                             "cli_version": init.get("claude_code_version"),
                             "permission_mode": init.get("permissionMode")},
                "tool_schemas_sha256": None,
                "opaque": ["the Claude Code CLI's own system prompt is not recorded",
                           "the MCP tool schemas served to the CLI are not recorded per session"]}
    return {"transcript": None, "system": None, "user": None, "tools": None,
            "opaque": [f"no transcript in {attempt} ({scaffold or 'unknown scaffold'})"]}


# --- Why two results differ ----------------------------------------------------------------------

#: Identity fields that make two numbers the same kind of number. Equal on all of them, two
#: measurements are on one scale; equal on the first four only, they are one instrument read over
#: different references, seals or projections, and are shown side by side but never subtracted.
SCALE_FIELDS = ("instrument", "instrument_version", "rubric_sha256", "question_policy",
                "reference_kind", "reference_sha256", "seal_sha256", "population_prs",
                "projection", "replicates", "aggregation", "denominator")
INSTRUMENT_FIELDS = ("instrument", "instrument_version", "rubric_sha256", "question_policy")
#: The contrast name for who ran a matching's matchers (model, effort, scaffold, CLI).
EXECUTOR = "executor"
#: Run-plan fields that change what a run measures (the plan's own non-resumable fields).
#: `agenda_sha256` is not among them: the sealed agenda carries its own run's name, id and
#: digest, so it differs between any two runs; `agenda_content_sha256` is the agenda without them.
RUN_FIELDS = ("model_name", "routing_mode", "release", "agenda_content_sha256", "evaluation_settings",
              "evaluation_contract_version", "coordination", "scaffold_config_sha256",
              "lead_cost_cap", "standard_budget_cap", "per_pr_cost_cap", "lead_token_cap",
              "standard_budget_tokens", "per_pr_token_cap")


def _measurement(source: str) -> Dict[str, Any]:
    """A measurement directory (a matching), optionally `@<producer>` for one of its executions or
    imports, or a judged run's name, read as identity and numbers."""

    path_text, _, producer = source.partition("@")
    path = Path(path_text)
    if path.is_dir() and (path / "matching_plan.json").is_file():
        from src.mathlib_review.analysis.matching import load_plan, report_matching

        plan = load_plan(path)
        report = report_matching(path, write=False, producers=[producer] if producer else None)
        numbers = {rep: {"condition_reach": report[rep]["condition_reach"],
                         "reach": report[rep]["reach"]}
                   for rep in report["measurement"]["replicates"]}
        numbers["asks"] = report["asks"]
        if "agreement" in report:
            numbers["agreement"] = report["agreement"]
        # Who ran the matchers: not in the identity (one plan may be executed or imported many
        # times), so read from the observations themselves.
        executors = sorted({json.dumps(row.get("executor") or {}, sort_keys=True)
                            for rep in report["measurement"]["replicates"].values()
                            for row in rep.get("rows") or []})
        return {"kind": "matching", "source": source,
                "executors": [json.loads(e) for e in executors],
                "producers": report["measurement"]["producers"],
                "identity": plan.identity.model_dump(mode="json"),
                "identity_sha256": plan.identity_sha256,
                "forensic": report["measurement"]["forensic"], "numbers": numbers}
    from src.mathlib_review.judge.runner import derive_from_run

    audit = Path(derive_from_run(source)["out_dir"]) / "semantic_report.json"
    if not audit.is_file():
        raise ValueError(f"{source} is neither a matching directory nor a judged run (no {audit})")
    report = json.loads(audit.read_text())
    rows = report.get("per_obligation") or []
    measurement = report.get("measurement") or {}
    return {"kind": "judged run", "source": source,
            "identity": measurement.get("identity"),
            "identity_sha256": measurement.get("identity_sha256")
            or "unrecorded (judged before 2026-10-22)",
            "judge_identity": report.get("judge_identity"),
            "forensic": bool(report.get("forensic")),
            "numbers": {"denominator": len(rows),
                        "issue_hits": sum(r.get("issue_status") == "hit" for r in rows),
                        "resolution_hits": sum(r.get("resolution_status") == "hit" for r in rows)}}


def _runs_of(entry: Dict[str, Any]) -> List[str]:
    identity = entry.get("identity") or {}
    runs = [run for subject in identity.get("subjects") or [] for run in subject.get("runs") or []]
    return runs or ([entry["source"]] if entry["kind"] == "judged run" else [])


def _run_plan(run: str) -> Optional[Dict[str, Any]]:
    """The last plan a run ran under: its revision if it has one, else the sealed plan."""

    from src.mathlib_review.paths import run_dir

    directory = run_dir(run)
    plans = sorted(directory.glob("run_plan_revision_*.json"),
                   key=lambda p: int(p.stem.rsplit("_", 1)[-1]))
    path = plans[-1] if plans else directory / "run_plan.json"
    if not path.is_file():
        return None
    plan = json.loads(path.read_text())
    agenda = directory / "agenda.json"
    if agenda.is_file():
        content = {k: v for k, v in json.loads(agenda.read_text()).items()
                   if k not in ("agenda_id", "run_name", "source_sha256")}
        plan["agenda_content_sha256"] = sha256_bytes(canonical_json_bytes(content))
    return plan


def _task_settings(run: str, ape_root: Path = Path(".ape/runs")) -> Optional[Dict[str, Any]]:
    path = Path(ape_root) / run / "config.json"
    if not path.is_file():
        return None
    return dict((json.loads(path.read_text()).get("config") or {}).get("task_config_overrides") or {})


def _differing(values: Dict[str, Any]) -> bool:
    return len({json.dumps(v, sort_keys=True, default=str) for v in values.values()}) > 1


def compare_measurements(sources: Dict[str, str],
                         contrast: Optional[Sequence[str]] = None,
                         ape_root: Path = Path(".ape/runs")) -> Dict[str, Any]:
    """Why two or more results differ, and what the difference can and cannot support.

    `sources` is `{label: matching directory or judged run}`. `contrast` names what is meant to
    differ -- identity fields, or run-plan fields such as `model_name` or
    `evaluation_settings.design`; everything else that differs is listed as undeclared, because a
    difference nobody intended is a confound until it is explained. Two measurements on one scale
    may be read against each other; one instrument over different references or seals is shown side
    by side and never subtracted; two instruments are never pooled.
    """

    contrast = set(contrast or ())
    entries = {label: _measurement(source) for label, source in sources.items()}
    unrecorded = sorted(label for label, e in entries.items() if not e.get("identity"))
    identity_differences = {}
    if not unrecorded:
        for field in SCALE_FIELDS + ("subjects",):
            values = {label: e["identity"].get(field) for label, e in entries.items()}
            if field == "subjects":
                values = {label: sorted((s.get("session"), s.get("channel")) for s in v or [])
                          for label, v in values.items()}
            if _differing(values):
                identity_differences[field] = values
    # The matcher's executor is part of what was measured: the first live Luna matching
    # (2026-10-22) compared with the Opus matchers named only the instrument version and rubric,
    # though a different model at a different effort on another scaffold had run it.
    matchings = {label: e.get("executors") for label, e in entries.items()
                 if e["kind"] == "matching"}
    executor_differences = ({EXECUTOR: matchings}
                            if len(matchings) > 1 and _differing(matchings) else {})
    instruments = {label: (e["identity"] or {}).get("instrument") if e.get("identity")
                   else ("semantic-judge" if e["kind"] == "judged run" else None)
                   for label, e in entries.items()}
    if len(set(instruments.values())) > 1:
        verdict = ("different instruments: never pooled or subtracted; each number is read under "
                   "its own definition")
    elif unrecorded:
        verdict = (f"identity unrecorded for {unrecorded}: comparable only as far as their judge "
                   "identities and denominators agree (`report conditions` checks both)")
    elif any(f in identity_differences for f in INSTRUMENT_FIELDS):
        verdict = "different versions of one instrument: side by side only, never subtracted"
    elif set(identity_differences) - {"subjects"} - contrast:
        verdict = ("one instrument over different references, seals or projections: side by side "
                   "only, never subtracted")
    elif executor_differences and EXECUTOR not in contrast:
        verdict = ("one instrument run by different matchers (model, effort or route): side by "
                   "side only, unless the comparison is the calibration (`--contrast executor`)")
    else:
        verdict = "one scale: the numbers may be read against each other"

    runs = {run: _run_plan(run) for e in entries.values() for run in _runs_of(e)}
    run_differences = {}
    for field in RUN_FIELDS:
        values = {run: (plan or {}).get(field) for run, plan in runs.items() if plan}
        if field == "evaluation_settings":
            keys = {k for v in values.values() for k in (v or {})}
            for key in sorted(keys):
                sub = {run: (v or {}).get(key) for run, v in values.items()}
                if _differing(sub):
                    run_differences[f"evaluation_settings.{key}"] = sub
        elif len(values) > 1 and _differing(values):
            run_differences[field] = values
    # What a scaffold digest difference is made of: the task settings each run executed with, from
    # its orchestrator record (`.ape/runs/<run>/config.json`), key by key.
    settings = {run: _task_settings(run, ape_root) for run in runs}
    settings = {run: v for run, v in settings.items() if v is not None}
    for key in sorted({k for v in settings.values() for k in v}):
        sub = {run: v.get(key) for run, v in settings.items()}
        if len(sub) > 1 and _differing(sub):
            run_differences[f"task_config.{key}"] = sub
    undeclared = sorted((set(identity_differences) - {"subjects"} | set(run_differences)
                         | set(executor_differences)) - contrast)
    return {
        "measurements": {label: {k: e.get(k) for k in ("kind", "source", "identity_sha256",
                                                         "forensic", "executors", "numbers",
                                                         "judge_identity")
                                 if k in e}
                         for label, e in entries.items()},
        "verdict": verdict,
        "identity_differences": identity_differences,
        "executor_differences": executor_differences,
        "run_differences": run_differences,
        "runs_without_a_plan": sorted(run for run, plan in runs.items() if plan is None),
        "contrast": sorted(contrast),
        "undeclared_differences": undeclared,
    }
