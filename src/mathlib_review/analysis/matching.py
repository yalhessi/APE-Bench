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
                  ask_packets_path: Optional[Path] = None, reuse: bool = False) -> MatchingPlan:
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
    if reuse and (Path(out_dir) / PLAN_FILE).exists():
        saved = load_plan(out_dir)
        fields = {"identity", "packets", "batches", "seal", "session_stats"}
        if saved.model_dump(include=fields) != plan.model_dump(include=fields):
            raise ValueError(f"{out_dir}: saved reading differs from the requested inputs or rubric; "
                             "use a new reading name")
        return saved
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
            # Claude Code states effort on the scaffold; every other route on its llm_config.
            "effort": str(getattr(scaffold, "effort", None)
                          or getattr(llm, "reasoning_effort", None) or "unknown"),
            "cli_version": str(getattr(scaffold, "cli_version", None) or "unknown")}


#: Scaffold-config keys a resume may change: ceilings, retries, timeouts, concurrency and where
#: the run lives. Everything else -- the model, the route, the effort, the tools, the prompt
#: preamble -- changes what a session is, and a run continues under one of each.
OPERATIONAL_KEYS = {"execution", "runs_base_dir", "runtime_config", "mcp_server_startup_timeout",
                    "enable_streaming", "open_in_vscode", "logs_dir_name", "conversations_dir_name",
                    "conversation_trees_file_name", "workspaces_dir_name"}
OPERATIONAL_LLM_KEYS = {"timeout", "connect_timeout", "retry_max_attempts", "retry_min_wait",
                        "retry_max_wait", "streaming"}


def route_sha256(scaffold) -> str:
    """The digest of everything about a scaffold config that is not operational."""

    dumped = scaffold.model_dump(mode="json")
    semantic = {k: v for k, v in dumped.items() if k not in OPERATIONAL_KEYS}
    if isinstance(semantic.get("llm_config"), dict):
        semantic["llm_config"] = {k: v for k, v in semantic["llm_config"].items()
                                  if k not in OPERATIONAL_LLM_KEYS}
    return sha256_bytes(canonical_json_bytes(semantic))


def task_producer(run_name: str) -> str:
    """The producer of a plan's observations from a run of its tasks."""
    return f"task-{run_name}"


def import_producer(name: str) -> str:
    """The producer of a plan's observations imported from outside the orchestrator."""
    return f"import-{name}"


def external_executor(executor: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """An import's executor: what the caller knows, `unknown` for the rest, never guessed."""
    return {"kind": "external session", "model": "unknown", "route": "unknown", **(executor or {})}


async def task_observations(tasks_dir: Path, tasks: Sequence[Any], replicates: int, run_name: str,
                            logger=None) -> List[Any]:
    """Every sample slot with a legal product, read once for every shared path (sessions and
    matchings both collected a run this way, each with its own copy of the loop). A slot without
    one is named in a warning, not passed over; whether the plan is covered is the report's
    question (`report match`, `report sessions`)."""

    from ape.orchestration.products import sample_products

    kept, gaps = [], []
    for item in await sample_products(tasks_dir, tasks, replicates):
        (kept if item.product is not None else gaps).append(item)
    if gaps and logger is not None:
        logger.warning("%s: %d sample slot(s) have no legal product: %s", run_name, len(gaps),
                       "; ".join(f"{g.task_id}#{g.sample_index} ({g.status}: {g.error})"
                                 for g in gaps[:8]))
    return kept


async def collect_task_verdicts(plan: MatchingPlan, tasks_dir: Path, tasks: Sequence[Any],
                                run_name: str, executor: Dict[str, str],
                                logger=None) -> List[MatchVerdict]:
    """Every replicate's verdict, as `sample_products` reads it; a sample with no legal product has
    none, and is a coverage gap in the report rather than a verdict.

    `executor` is the run's recorded one (`bind_run_to_plan`), never the invoking config's: a
    resume with the same binding ran on the same route, and a different route is refused before
    any cached sample could be read under its name."""

    rows: List[MatchVerdict] = []
    by_batch = {b.batch_id: b for b in plan.batches}
    packets = {p.pr: p for p in plan.packets}
    for item in await task_observations(tasks_dir, tasks, plan.identity.replicates, run_name, logger):
        verdict = item.product
        batch = by_batch[verdict["batch_id"]]
        problems = verdict_problems([packets[pr] for pr in batch.prs], verdict["asks"],
                                    verdict["unmatched"])
        if problems:
            raise ValueError(f"{run_name} sample {item.sample_index} of {batch.batch_id}: a "
                             f"recorded verdict does not cover its batch: {problems[:3]}")
        rows.append(MatchVerdict(
            plan_id=plan.plan_id, batch_id=batch.batch_id, producer=task_producer(run_name),
            replicate=str(item.sample_index + 1), origin="task",
            locator={**item.locator(run_name, tasks_dir),
                     "prompt_sha256": str(verdict["prompt_sha256"])},
            executor=executor, asks=verdict["asks"], unmatched=verdict["unmatched"]))
    return rows


BINDING_FILE = "plan_binding.json"


def bind_run_to_plan(runs_root: Path, run_name: str, kind: str, plan_id: str,
                     plan_sha256: str, scaffold=None) -> Dict[str, Any]:
    """Bind an orchestrator run name to the one plan and the one route it executes.

    A resumed run continues its plan on its route; a changed plan or a changed route is a new
    run. Without the plan half, a second plan under an old name shared the first's orchestrator
    directory and cache. Without the route half, a resume under another model skipped the tasks
    already done and the collector stamped their cached verdicts with the new model (implementation
    review, 2026-10-22, finding 3). Operational settings (`OPERATIONAL_KEYS`) may change on a
    resume. Returns the binding held, whose `executor` is what every observation of this run is
    attributed to.
    """

    path = Path(runs_root) / run_name / BINDING_FILE
    binding: Dict[str, Any] = {"kind": kind, "plan_id": plan_id, "plan_sha256": plan_sha256}
    if scaffold is not None:
        binding["executor"] = executor_of(scaffold)
        binding["route_sha256"] = route_sha256(scaffold)
    if path.is_file():
        held = json.loads(path.read_text())
        if {k: held.get(k) for k in ("kind", "plan_id", "plan_sha256")} != \
                {k: binding.get(k) for k in ("kind", "plan_id", "plan_sha256")}:
            raise ValueError(
                f"run {run_name!r} executes {held.get('kind')} plan {held.get('plan_id')} "
                f"({str(held.get('plan_sha256'))[:12]}); this is {kind} plan {plan_id} "
                f"({plan_sha256[:12]}). Resume the same plan under this name, or give the new "
                "plan a new run name.")
        if scaffold is not None and held.get("route_sha256") not in (None, binding["route_sha256"]):
            differing = sorted(k for k in binding["executor"]
                               if binding["executor"][k] != (held.get("executor") or {}).get(k))
            raise ValueError(
                f"run {run_name!r} ran on {held.get('executor')}; this config is "
                f"{binding['executor']}" + (f" (differs in {differing})" if differing else
                                            " (a setting beyond the execution ceilings differs)")
                + ". A run continues on one route: resume with the route it ran on, or give the "
                "new route a new run name, so its observations are never attributed to another's.")
        return held
    path.parent.mkdir(parents=True, exist_ok=True)
    write_once(path, pretty_json_bytes(binding))
    return binding


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
    binding = bind_run_to_plan(scaffold.runs_base_dir, run_name, "matching", plan.plan_id,
                               plan.source_sha256, scaffold)
    scaffold.execution.sample_count = replicates
    # Every replicate is a measurement; stopping early on the first would discard the others.
    scaffold.execution.early_stop_mode = EarlyStopMode.DISABLED
    tasks = [create_task_from_data(payload, scaffold,
                                   task_config_overrides=scaffold.task_config_overrides)
             for payload in task_payloads(plan)]
    orchestrator = TaskOrchestrator(config=scaffold, orchestrator_id=run_name, logger=logger)
    await orchestrator.run(tasks)
    rows = await collect_task_verdicts(plan, orchestrator.tasks_dir, tasks, run_name,
                                       binding["executor"], logger)
    verdicts = _write_verdicts(plan_dir, task_producer(run_name), rows)
    record_match_stage(plan, Path(plan_dir), run_name, verdicts, logger)
    return rows


def record_match_stage(plan: MatchingPlan, plan_dir: Path, run_name: str, verdicts: Path,
                       logger=None) -> List[str]:
    """Leave the matching's row in each source run's stage ledger, as the judge leaves its own.

    "This run's findings were matched, under this identity, into that directory" is a fact about
    the run (`judge.runner._record_stage`). Solo and lead sources only: a packet or a findings
    file has no run directory. Digests and identity only -- the asks are gold-side and never enter
    a run directory. Never fatal: the verdicts are paid for and written. Returns the runs written.

    Only into a run whose findings are recorded in this checkout. The first live matching
    (2026-10-22) wrote a ledger into `probe_dev_opus55_contract2_claude_sub_rep3/`, a folder holding
    nothing but the worktree setup's link to its arm pool: that run's results were never recorded on
    any branch, and a lone `stages.jsonl` there would read as a recorded run. Runs recorded on
    another branch are skipped too, and every skipped run is named in a warning, not passed over.
    """

    from src.mathlib_review import paths
    from src.mathlib_review.run_state import RUN_ARTIFACTS, append_stage, digests_of, stage_record

    written, skipped = [], []
    for subject in plan.identity.subjects:
        if subject.source not in ("solo", "lead"):
            continue
        for run in subject.runs:
            try:
                directory = paths.run_dir(run)
                if not (directory / RUN_ARTIFACTS["findings"].filename).is_file():
                    skipped.append(run)
                    continue
                append_stage(directory, stage_record(
                    "match", run_name=run,
                    consumed=digests_of([plan_dir / PLAN_FILE]),
                    produced={**digests_of([verdicts]), "plan_dir": str(plan_dir)},
                    identity={"instrument": f"{plan.identity.instrument}/"
                                            f"{plan.identity.instrument_version}",
                              "plan_id": plan.plan_id,
                              "identity_sha256": plan.identity_sha256,
                              "matcher_run": run_name, "session": subject.session,
                              "channel": subject.channel}))
                written.append(run)
            except Exception:  # noqa: BLE001 - see the docstring
                if logger is not None:
                    logger.warning("could not record the matching's row in %s's ledger", run,
                                   exc_info=True)
    if skipped and logger is not None:
        logger.warning("the matching's row is not in the ledger of %d source run(s) whose findings "
                       "are not recorded in this checkout (another branch, or never recorded): %s",
                       len(skipped), ", ".join(skipped))
    return written


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

    executor = external_executor(executor)
    rows = []
    for replicate, path in sorted(files.items()):
        data = json.loads(Path(path).read_text())
        problems = verdict_problems(plan.packets, data.get("asks") or [], data.get("unmatched"))
        if problems and not allow_incomplete:
            raise ValueError(f"{path} does not cover plan {plan.plan_id}: {len(problems)} "
                             f"problem(s), first {problems[:3]}")
        rows.append(MatchVerdict(
            plan_id=plan.plan_id, batch_id="*", producer=import_producer(name), replicate=str(replicate),
            origin="external_import",
            locator={"file": str(path), "sha256": sha256_file(Path(path)),
                     "problems": str(len(problems))},
            executor=executor, asks=data.get("asks") or [], unmatched=data.get("unmatched") or {}))
    _write_verdicts(plan_dir, import_producer(name), rows)
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


def observation_key(producer: str, replicate: str) -> str:
    """One blind matcher's observation: which execution or import, and which of its replicates."""

    return f"{producer}:{replicate}"


def producers_of(rows: Sequence[MatchVerdict]) -> List[str]:
    return sorted({row.producer for row in rows})


def replicate_tables(plan: MatchingPlan, rows: Sequence[MatchVerdict]) -> Dict[str, Dict[str, Any]]:
    """Per observation (`producer:replicate`): its merged `matches` table over that producer's
    batches, where its rows came from, and its coverage. Batch rows merge only within one
    observation; two runs of one plan are two sets of observations, never one."""

    by_rep: Dict[str, List[MatchVerdict]] = {}
    for row in rows:
        by_rep.setdefault(observation_key(row.producer, row.replicate), []).append(row)
    out = {}
    for rep, items in sorted(by_rep.items()):
        asks: List[Dict[str, Any]] = []
        unmatched: Dict[str, Dict[str, int]] = {}
        for item in items:
            asks.extend(item.asks)
            unmatched.update(item.unmatched)
        problems = verdict_problems(plan.packets, asks, unmatched, require_unmatched=False)
        out[rep] = {"producer": items[0].producer, "replicate": items[0].replicate,
                    "matches": {"asks": asks, "unmatched": unmatched},
                    "rows": [{"batch_id": i.batch_id, "origin": i.origin, "locator": i.locator,
                              "executor": i.executor} for i in items],
                    "complete": not problems, "problems": problems[:20],
                    "problem_count": len(problems)}
    return out


def report_matching(plan_dir: Path, families: Optional[Dict[str, str]] = None,
                    scope: Optional[set] = None, replicates: Optional[Sequence[str]] = None,
                    producers: Optional[Sequence[str]] = None,
                    write: bool = True) -> Dict[str, Any]:
    """`unblind` over one producer's observations, with the identity and coverage beside every number.

    A producer is one execution or import of the plan (`task-<run>`, `import-<name>`). With one
    in the store it is read; with several, the report refuses until one is named, or several are
    named explicitly, in which case each producer's coverage is judged on its own and the report
    says which observations it combined. Partial runs never complete each other.
    """

    plan_dir = plan_dir_of(Path(plan_dir))
    plan = load_plan(plan_dir)
    rows = verdict_rows(plan_dir, plan.plan_id)
    if not rows:
        raise ValueError(f"plan {plan.plan_id} has no verdicts yet ({plan_dir / VERDICTS_DIR})")
    held = producers_of(rows)
    if producers:
        unknown = sorted(set(producers) - set(held))
        if unknown:
            raise ValueError(f"no verdicts from producers {unknown}; held: {held}")
        chosen = list(producers)
    elif len(held) == 1:
        chosen = held
    else:
        raise ValueError(
            f"plan {plan.plan_id} holds verdicts from {len(held)} producers: {held}. Name one "
            "(--producer), or several to read side by side (--producers), each judged on its own "
            "coverage; observations from different executions are never merged into one replicate.")
    tables = replicate_tables(plan, [row for row in rows if row.producer in chosen])
    if replicates:
        missing = sorted(set(replicates) - set(tables))
        if missing:
            raise ValueError(f"no verdicts for replicates {missing}; held: {sorted(tables)}")
        tables = {k: v for k, v in tables.items() if k in replicates}
    if scope and families is None:
        raise ValueError("a scoped report needs the asks' families (`--asks <asks.json>`)")
    asks = {"asks": {str(p.pr): [a.ask_id for a in p.asks] for p in plan.packets},
            "families": dict(families or {})}
    stats = {pr: {s: dict(v) for s, v in sessions.items()}
             for pr, sessions in plan.session_stats.items()}
    numbers = unblind(asks, plan.seal, {k: v["matches"] for k, v in tables.items()}, stats,
                      scope=scope)
    # Coverage is judged producer by producer: each must hold the plan's replicates, complete.
    by_producer = {name: {k: t for k, t in tables.items() if t["producer"] == name}
                   for name in chosen}
    producer_status = {
        name: {"replicates": len(ts),
               "complete": all(t["complete"] for t in ts.values()),
               "forensic": (len(ts) < plan.identity.replicates
                            or not all(t["complete"] for t in ts.values()))}
        for name, ts in by_producer.items()}
    report = {
        "measurement": {
            "plan_id": plan.plan_id,
            "plan_sha256": plan.source_sha256,
            "identity_sha256": plan.identity_sha256,
            "identity": plan.identity.model_dump(mode="json"),
            "scope": sorted(scope) if scope else None,
            "producers": producer_status,
            "replicates": {k: {"producer": t["producer"], "rows": t["rows"],
                               "complete": t["complete"], "problem_count": t["problem_count"],
                               "problems": t["problems"]}
                           for k, t in tables.items()},
            "replicates_expected": plan.identity.replicates,
            "forensic": any(p["forensic"] for p in producer_status.values()),
        },
        **numbers,
    }
    report["reviews"] = []
    for reading, table in tables.items():
        for packet in plan.packets:
            eligible = {ask.ask_id for ask in packet.asks
                        if scope is None or (families or {}).get(ask.ask_id) in scope}
            decisions = [a for a in table["matches"]["asks"]
                         if int(a["pr"]) == packet.pr and a["ask_id"] in eligible]
            for label, session in plan.seal[str(packet.pr)].items():
                report["reviews"].append({
                    "reading": reading, "pr": packet.pr, "session": session,
                    "shown_findings": len(packet.reviewers[label]), "eligible_asks": len(eligible),
                    "reached": sum(a.get(label) == "reached" for a in decisions),
                    "matches": {a["ask_id"]: {"verdict": a.get(label), "finding": a.get(f"{label}_finding")}
                                for a in decisions},
                })
    if write:
        path = plan_dir / REPORT_FILE
        tmp = path.with_name(f".{path.name}.tmp")
        tmp.write_bytes(pretty_json_bytes(report))
        tmp.replace(path)
    return report
