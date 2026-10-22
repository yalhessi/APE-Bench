"""A raw-ask matching, end to end: a sealed plan, matchers run as Tasks or imported, one report, one trace.

Before 2026-10-22 a matching was a chain under a probe directory: `probe seal`, `probe match-inputs`
writing input folders to a scratch directory outside the repository, `run_matching.sh` launching
headless Claude sessions over them, `check_matches.py` and `audit_batch.py`, a merge in an inline
script, and `probe unblind`. The verdicts were kept; the bytes the matchers judged were not, and
nothing tied a reported reach figure to its seal, instrument and inputs except the probe's README.

The lifecycle is now:

1. **plan** (`plan_matching`, `cli probe match-plan`): the blind packets `probes.blind_packets`
   builds, the seal, the batches and the measurement identity, sealed and written once into the
   measurement directory, which lives in the repository. No model runs.
2. **run** (`run_matching`, `cli match --execute`): one `lean_pr_review_ask_matching` task per batch,
   `sample_count` = the plan's replicates, through `TaskOrchestrator`; then every sample's verdict is
   read back through `TaskStorage` into `verdicts/task-<run>.jsonl`.
3. **import** (`import_matches`, `cli probe match-import`): an externally produced `matches.json`
   (every matching before this module) is validated against the plan's expected cells and stored the
   same way, its provenance written as what is known and `unknown` for the rest.
4. **report** (`report_matching`, `cli report match`): `unblind`'s arithmetic over the verdict store,
   with the measurement identity and each replicate's coverage beside the numbers. A replicate that
   does not cover every expected cell makes the report forensic, never a headline.
5. **trace** (`trace_matching`, `cli report trace`): from a PR, an ask and a session to the label it
   wore, the exact blind finding list that label showed, each replicate's cell and where its verdict's
   bytes are, and the reviewer's original finding in its source.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from src.mathlib_review.io import (
    canonical_json_bytes, jsonl_bytes, jsonl_rows, pretty_json_bytes, sealed_model, sha256_bytes,
    sha256_file, write_once,
)
from src.mathlib_review.judge.ask_matching import (
    INSTRUMENT, KEEP, V1_SESSION, V2_TASK, VERSIONS, labels_of, rubric_sha256, unblind,
    verdict_problems,
)
from src.mathlib_review.schema import (
    BlindAsk, BlindFinding, BlindPacket, MatchBatch, MatchVerdict, MatchingPlan,
    MeasurementIdentity, SubjectBinding,
)

from pydantic import BaseModel, ConfigDict


class MatchDatasetConfig(BaseModel):
    """A matcher config's `dataset` block: the run's name, if the config states one."""

    model_config = ConfigDict(extra="forbid")
    run_name: Optional[str] = None


PLAN_FILE = "matching_plan.json"
SEAL_FILE = "seal.json"
VERDICTS_DIR = "verdicts"
REPORT_FILE = "unblinded.json"

#: A source kind's subject binding: which loader it is and which output channel it reads.
_CHANNELS = {"claude": ("packet", "packet"), "solo": ("solo", "submitted"),
             "lead": ("lead", "finalized"), "findings_file": ("findings_file", "declared")}

#: What the identity says about failures, once, so every plan says the same thing.
MISSINGNESS = ("every expected cell needs a verdict in every replicate; a replicate that does not "
               "cover them makes the report forensic, and an absent cell is never read as `no`")
DENOMINATOR = ("the asks of the sealed PRs (in scope, if scoped); a session's reach is asks it "
               "reached over that count, per replicate")
AGGREGATION = "none: each replicate is read on its own, and two are compared cell by cell"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _subject(session: str, source) -> SubjectBinding:
    kind, channel = _CHANNELS[source.kind]
    runs = [source.run] if isinstance(source.run, str) else list(source.run or [])
    return SubjectBinding(session=session, source=kind, channel=channel, runs=runs,
                          path=getattr(source, "path", None))


def batches_of(prs: Sequence[int], size: Optional[int]) -> List[MatchBatch]:
    """The sealed PRs in numeric order, `size` to a batch (all in one when `size` is None), as
    `run_matching.sh` split them."""

    ordered = sorted(int(pr) for pr in prs)
    size = size or len(ordered) or 1
    return [MatchBatch(batch_id=f"b{n // size + 1}", prs=ordered[n:n + size])
            for n in range(0, len(ordered), size)]


def plan_matching(spec, *, name: str, seal: Dict[str, Dict[str, str]], seal_path: Path,
                  sources: Dict[str, Any], out_dir: Path, version: str = V2_TASK,
                  question_policy: str = "request_only", replicates: int = 2,
                  batch_size: Optional[int] = None, harness_blind: bool = False,
                  ask_packets: Optional[Dict[str, List[Dict[str, Any]]]] = None,
                  ask_packets_path: Optional[Path] = None) -> MatchingPlan:
    """Seal a matching before any matcher runs; returns the plan written to `out_dir`.

    `version` is `2-task` for a matching the Task will run, or `1-session` to bind an existing
    hand-launched matching's inputs so its `matches.json` can be imported and traced. A plan
    rebuilt for a v1 matching reproduces its inputs only if its sources still load as they did.
    """

    from src.mathlib_review.analysis import probes

    if version not in VERSIONS:
        raise ValueError(f"unknown {INSTRUMENT} version {version!r}")
    if replicates < 1:
        raise ValueError("a matching needs at least one replicate")
    if ask_packets is None:
        feedback = json.loads(spec.feedback_file.read_text())
        asks = json.loads(spec.asks_file.read_text())
        reference_source = f"{spec.feedback_file} + {spec.asks_file}"
    else:
        feedback = asks = None
        reference_source = str(ask_packets_path) if ask_packets_path else "(ask packets given)"
    raw, stats = probes.blind_packets(spec, seal, sources, feedback=feedback, asks=asks,
                                      ask_packets=ask_packets, harness_blind=harness_blind)
    packets = [BlindPacket(pr=int(pr), asks=[BlindAsk.model_validate(a) for a in item["asks"]],
                           reviewers={label: [BlindFinding.model_validate(f) for f in found]
                                      for label, found in item["reviewers"].items()})
               for pr, item in sorted(raw.items(), key=lambda kv: int(kv[0]))]
    for packet in packets:
        labels_of([packet])
    batches = batches_of([p.pr for p in packets], batch_size)
    for batch in batches:
        labels_of([p for p in packets if p.pr in batch.prs])
    used = sorted({s for labels in seal.values() for s in labels.values()})
    references = {str(p.pr): [a.model_dump(mode="json") for a in p.asks] for p in packets}
    identity = sealed_model(
        MeasurementIdentity,
        instrument=INSTRUMENT, instrument_version=version,
        rubric_sha256=rubric_sha256(version, question_policy),
        question_policy=question_policy, reference_kind="raw_ask",
        reference_source=reference_source,
        reference_sha256=sha256_bytes(canonical_json_bytes(references)),
        reference_count=sum(len(p.asks) for p in packets),
        population_prs=[p.pr for p in packets],
        seal_path=str(seal_path), seal_sha256=sha256_file(seal_path),
        subjects=[_subject(s, sources[s]) for s in used],
        projection={"keep": list(KEEP), "target": "repository path",
                    "redaction": ["construction cues"] + (["conventions cues"] if harness_blind else []),
                    "harness_blind": harness_blind,
                    "claude_cut_to": probes.SOLO_FINDING_BUDGET if harness_blind else None},
        replicates=replicates, aggregation=AGGREGATION, denominator=DENOMINATOR,
        missingness=MISSINGNESS,
    )
    plan = sealed_model(
        MatchingPlan, plan_id=name, identity=identity, identity_sha256=identity.source_sha256,
        seal=seal, batches=batches, packets=packets, session_stats=stats,
        expected_cells=sum(len(p.asks) * len(p.reviewers) for p in packets),
        created_at=_now(),
    )
    write_once(Path(out_dir) / PLAN_FILE, pretty_json_bytes(plan))
    return plan


def load_plan(path: Path) -> MatchingPlan:
    """A plan, checked against its own seal: an edited plan is refused, not read."""

    path = Path(path)
    if path.is_dir():
        path = path / PLAN_FILE
    plan = MatchingPlan.model_validate_json(path.read_text(encoding="utf-8"))
    for record, label in ((plan.identity, "identity"), (plan, "plan")):
        recomputed = sha256_bytes(canonical_json_bytes(
            record.model_dump(mode="json", exclude={"source_sha256"})))
        if recomputed != record.source_sha256:
            raise ValueError(f"{path}: the {label} does not match its seal; it was edited")
    if plan.identity_sha256 != plan.identity.source_sha256:
        raise ValueError(f"{path}: identity_sha256 does not name the identity it holds")
    return plan


def plan_dir_of(path: Path) -> Path:
    path = Path(path)
    return path if path.is_dir() else path.parent


# --- Run -----------------------------------------------------------------------------------------


def task_payloads(plan: MatchingPlan) -> List[Dict[str, Any]]:
    """One `lean_pr_review_ask_matching` task per batch."""

    from ape.tasks.lean_tasks.formal_math.review.ask_matching import ASK_MATCHING_TASK_TYPE

    if plan.identity.instrument_version != V2_TASK:
        raise ValueError(f"plan {plan.plan_id} is {plan.identity.instrument_version}; only "
                         f"{V2_TASK} runs as a task, a 1-session matching is imported")
    by_pr = {p.pr: p for p in plan.packets}
    return [{"task_type": ASK_MATCHING_TASK_TYPE, "task_id": f"match_{plan.plan_id}_{b.batch_id}",
             "plan_id": plan.plan_id, "batch_id": b.batch_id, "instrument_version": V2_TASK,
             "question_policy": plan.identity.question_policy,
             "packets": [by_pr[pr].model_dump(mode="json") for pr in b.prs]}
            for b in plan.batches]


def executor_of(scaffold) -> Dict[str, str]:
    """What will run the matchers, as far as the config says; unknowns stay `unknown`."""

    llm = getattr(scaffold, "llm_config", None)
    return {"scaffold": str(getattr(scaffold, "scaffold_type", "unknown")),
            "model": str(getattr(llm, "model_name", None) or getattr(scaffold, "claude_model", None)
                         or "unknown"),
            "effort": str(getattr(scaffold, "effort", None) or "unknown"),
            "cli_version": str(getattr(scaffold, "cli_version", None) or "unknown")}


async def collect_task_verdicts(plan: MatchingPlan, tasks_dir: Path, tasks: Sequence[Any],
                                run_name: str, executor: Dict[str, str]) -> List[MatchVerdict]:
    """Every sample's verdict, read through `TaskStorage`; a sample with no legal result has none."""

    from ape.orchestration.persistence import TaskStorage

    rows: List[MatchVerdict] = []
    by_batch = {b.batch_id: b for b in plan.batches}
    packets = {p.pr: p for p in plan.packets}
    for task in tasks:
        index = task.data.global_index
        storage = TaskStorage(Path(tasks_dir) / index, index)
        samples = await storage.load_all_samples(task.task_type)
        for sample_index, sample in sorted(samples.items()):
            attempt = sample.successful_attempt
            result = getattr(attempt, "result", None) if attempt else None
            if result is None:
                continue
            batch = by_batch[task.data.batch_id]
            problems = verdict_problems([packets[pr] for pr in batch.prs], result.asks,
                                        result.unmatched)
            if problems:
                raise ValueError(f"{run_name} sample {sample_index} of {batch.batch_id}: a "
                                 f"recorded verdict does not cover its batch: {problems[:3]}")
            rows.append(MatchVerdict(
                plan_id=plan.plan_id, batch_id=batch.batch_id, replicate=str(sample_index + 1),
                origin="task",
                locator={"run": run_name, "task_dir": str(storage.task_dir),
                         "sample": str(sample_index), "attempt": str(attempt.path),
                         "prompt_sha256": str(result.prompt_sha256)},
                executor=executor, asks=result.asks, unmatched=result.unmatched))
    return rows


async def run_matching(plan: MatchingPlan, plan_dir: Path, scaffold, run_name: str,
                       logger) -> List[MatchVerdict]:
    """Run the plan's batches as Tasks and write the verdict store for this run."""

    from ape.orchestration.config import EarlyStopMode
    from ape.orchestration.orchestrator import TaskOrchestrator
    from ape.tasks.base import create_task_from_data

    replicates = plan.identity.replicates
    if scaffold.execution.sample_count not in (1, replicates):
        raise ValueError(f"the config asks for {scaffold.execution.sample_count} samples and the "
                         f"plan seals {replicates} replicates; the plan decides, so drop the "
                         "config's sample_count")
    scaffold.execution.sample_count = replicates
    # Every replicate is a measurement; stopping early on the first would discard the others.
    scaffold.execution.early_stop_mode = EarlyStopMode.DISABLED
    tasks = [create_task_from_data(payload, scaffold,
                                   task_config_overrides=scaffold.task_config_overrides)
             for payload in task_payloads(plan)]
    orchestrator = TaskOrchestrator(config=scaffold, orchestrator_id=run_name, logger=logger)
    await orchestrator.run(tasks)
    rows = await collect_task_verdicts(plan, orchestrator.tasks_dir, tasks, run_name,
                                       executor_of(scaffold))
    _write_verdicts(plan_dir, f"task-{run_name}", rows)
    return rows


def _write_verdicts(plan_dir: Path, name: str, rows: Sequence[MatchVerdict]) -> Path:
    """The verdict store for one run or import. Derived from the run's own records (or the
    imported file, whose digest it carries), so a resumed run rewrites it with what it now holds."""

    path = Path(plan_dir) / VERDICTS_DIR / f"{name}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_bytes(jsonl_bytes(rows))
    tmp.replace(path)
    return path


# --- Import --------------------------------------------------------------------------------------


def import_matches(plan: MatchingPlan, plan_dir: Path, files: Dict[str, Path], name: str,
                   executor: Optional[Dict[str, str]] = None,
                   allow_incomplete: bool = False) -> List[MatchVerdict]:
    """Externally produced `matches.json` files, one per replicate, checked against the plan.

    Each file covers the whole plan (the probes merged their batches per matcher before
    unblinding). A file that misses a cell, names a finding that does not exist, or answers an ask
    twice is refused; `allow_incomplete` stores it marked so, and the report then says forensic.
    """

    executor = {"kind": "external session", "model": "unknown", "route": "unknown",
                **(executor or {})}
    rows = []
    for replicate, path in sorted(files.items()):
        data = json.loads(Path(path).read_text())
        problems = verdict_problems(plan.packets, data.get("asks") or [], data.get("unmatched"))
        if problems and not allow_incomplete:
            raise ValueError(f"{path} does not cover plan {plan.plan_id}: {len(problems)} "
                             f"problem(s), first {problems[:3]}")
        rows.append(MatchVerdict(
            plan_id=plan.plan_id, batch_id="*", replicate=str(replicate), origin="external_import",
            locator={"file": str(path), "sha256": sha256_file(Path(path)),
                     "problems": str(len(problems))},
            executor=executor, asks=data.get("asks") or [], unmatched=data.get("unmatched") or {}))
    _write_verdicts(plan_dir, f"import-{name}", rows)
    return rows


# --- Report --------------------------------------------------------------------------------------


def verdict_rows(plan_dir: Path, plan_id: str) -> List[MatchVerdict]:
    rows = []
    for path in sorted((Path(plan_dir) / VERDICTS_DIR).glob("*.jsonl")):
        for row in jsonl_rows(path):
            verdict = MatchVerdict.model_validate(row)
            if verdict.plan_id != plan_id:
                raise ValueError(f"{path} holds verdicts for plan {verdict.plan_id}, not {plan_id}")
            rows.append(verdict)
    return rows


def replicate_tables(plan: MatchingPlan, rows: Sequence[MatchVerdict]) -> Dict[str, Dict[str, Any]]:
    """Per replicate: its merged `matches` table, where its rows came from, and its coverage."""

    by_rep: Dict[str, List[MatchVerdict]] = {}
    for row in rows:
        by_rep.setdefault(f"{row.origin}:{row.replicate}", []).append(row)
    out = {}
    for rep, items in sorted(by_rep.items()):
        asks: List[Dict[str, Any]] = []
        unmatched: Dict[str, Dict[str, int]] = {}
        for item in items:
            asks.extend(item.asks)
            unmatched.update(item.unmatched)
        problems = verdict_problems(plan.packets, asks, unmatched, require_unmatched=False)
        out[rep] = {"matches": {"asks": asks, "unmatched": unmatched},
                    "rows": [{"batch_id": i.batch_id, "origin": i.origin, "locator": i.locator,
                              "executor": i.executor} for i in items],
                    "complete": not problems, "problems": problems[:20],
                    "problem_count": len(problems)}
    return out


def report_matching(plan_dir: Path, families: Optional[Dict[str, str]] = None,
                    scope: Optional[set] = None, replicates: Optional[Sequence[str]] = None,
                    write: bool = True) -> Dict[str, Any]:
    """`unblind` over the verdict store, with the identity and coverage beside every number."""

    plan_dir = plan_dir_of(Path(plan_dir))
    plan = load_plan(plan_dir)
    tables = replicate_tables(plan, verdict_rows(plan_dir, plan.plan_id))
    if replicates:
        missing = sorted(set(replicates) - set(tables))
        if missing:
            raise ValueError(f"no verdicts for replicates {missing}; held: {sorted(tables)}")
        tables = {k: v for k, v in tables.items() if k in replicates}
    if not tables:
        raise ValueError(f"plan {plan.plan_id} has no verdicts yet ({plan_dir / VERDICTS_DIR})")
    if scope and families is None:
        raise ValueError("a scoped report needs the asks' families (`--asks <asks.json>`)")
    asks = {"asks": {str(p.pr): [a.ask_id for a in p.asks] for p in plan.packets},
            "families": dict(families or {})}
    stats = {pr: {s: dict(v) for s, v in sessions.items()}
             for pr, sessions in plan.session_stats.items()}
    numbers = unblind(asks, plan.seal, {k: v["matches"] for k, v in tables.items()}, stats,
                      scope=scope)
    complete = all(t["complete"] for t in tables.values())
    report = {
        "measurement": {
            "plan_id": plan.plan_id,
            "plan_sha256": plan.source_sha256,
            "identity_sha256": plan.identity_sha256,
            "identity": plan.identity.model_dump(mode="json"),
            "scope": sorted(scope) if scope else None,
            "replicates": {k: {"rows": t["rows"], "complete": t["complete"],
                               "problem_count": t["problem_count"], "problems": t["problems"]}
                           for k, t in tables.items()},
            "replicates_expected": plan.identity.replicates,
            "forensic": not complete or len(tables) < plan.identity.replicates,
        },
        **numbers,
    }
    if write:
        path = plan_dir / REPORT_FILE
        tmp = path.with_name(f".{path.name}.tmp")
        tmp.write_bytes(pretty_json_bytes(report))
        tmp.replace(path)
    return report


# --- Trace ---------------------------------------------------------------------------------------


def trace_matching(plan_dir: Path, pr: int, ask_id: str, session: str) -> Dict[str, Any]:
    """One cell, followed to its bytes: the label, what that label showed, each replicate's verdict
    and where it is, and the reviewer's own finding in its source."""

    from src.mathlib_review.analysis import probes

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
    cells = []
    for rep, table in replicate_tables(plan, verdict_rows(plan_dir, plan.plan_id)).items():
        row = next((a for a in table["matches"]["asks"]
                    if int(a.get("pr")) == int(pr) and a.get("ask_id") == ask_id), None)
        value = row.get(label) if row else None
        index = row.get(f"{label}_finding") if row else None
        where = next((r for r in table["rows"]
                      if r["batch_id"] in ("*",) or int(pr) in
                      next((b.prs for b in plan.batches if b.batch_id == r["batch_id"]), [])), None)
        cells.append({"replicate": rep, "value": value if row else "(no verdict)",
                      "finding": index, "note": row.get("note") if row else None,
                      "shown_finding": shown[index] if isinstance(index, int) and 0 <= index < len(shown) else None,
                      "verdict_bytes": where})
    original = None
    if subject.source in ("solo", "lead", "findings_file", "packet"):
        original = _original_findings(probes, plan, subject, int(pr))
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
        "original": original,
        "cells": cells,
    }


def _original_findings(probes, plan: MatchingPlan, subject: SubjectBinding, pr: int):
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
