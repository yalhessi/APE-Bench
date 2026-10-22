"""Model sessions over folders, end to end: a sealed plan, sessions run as tasks or imported, one store.

The recurring mechanic the slice-B spike found still bespoke after the evaluation and context slices
(`docs/research/task-dataflow-refactor-implementation-2026-10-22.md`): a study writes a folder per
session (instructions, inputs), a prompt says "your working folder is {dir}", a script launches
headless sessions outside the orchestrator, and outputs are read back by path, with only the inputs'
digests kept. The reconstruction probe's extractor, auditor, sketch, context and reader sessions all
ran that way.

1. **plan** (`plan_sessions`, `cli probe session-plan`): every packet folder's files, the brief and
   the declared outputs, sealed and written once into a directory in the repository. No model runs.
2. **run** (`run_sessions`, `cli session --execute`): one `packet_session` task per packet,
   `sample_count` = replicates, through `TaskOrchestrator`; every sample's outputs are read back
   through `sample_products` and stored beside the plan with their digests and locators.
3. **import** (`import_session_outputs`, `cli probe session-import`): a hand-launched session's
   folder, its declared outputs checked and stored the same way, provenance `unknown` where unknown.

What the outputs mean, and what a study builds from them (a context section, a seal, a reading),
stays with the study; it reads `outputs/index.jsonl` rather than scratch paths.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from src.mathlib_review.io import (
    canonical_json_bytes, jsonl_bytes, jsonl_rows, pretty_json_bytes, sealed_model, sha256_bytes,
    write_once,
)
from src.mathlib_review.schema import SessionOutput, SessionPacket, SessionPlan

PLAN_FILE = "session_plan.json"
OUTPUTS_DIR = "outputs"
INDEX_FILE = "index.jsonl"
#: Never part of a packet: a session's scratch.
SKIP_DIRS = {"tmp"}


def _packet_files(folder: Path, outputs: Sequence[str]) -> Dict[str, str]:
    files: Dict[str, str] = {}
    done = [name for name in outputs if (folder / name).exists()]
    if done:
        raise ValueError(f"{folder} holds {done}: a finished session's folder is not a packet")
    for path in sorted(p for p in folder.rglob("*") if p.is_file()):
        rel = path.relative_to(folder)
        if rel.parts[0] in SKIP_DIRS:
            continue
        try:
            files[rel.as_posix()] = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            raise ValueError(f"{path} is not UTF-8 text; a packet holds text files only")
    if not files:
        raise ValueError(f"{folder} holds no files")
    return files


def plan_sessions(packets_root: Path, *, name: str, brief: str, outputs: List[Dict[str, Any]],
                  out_dir: Path, replicates: int = 1,
                  packet_ids: Optional[Sequence[str]] = None) -> SessionPlan:
    """Seal one session per packet folder under `packets_root` (or the named ones)."""

    from ape.tasks.packet_session import DIR_TOKEN, OutputSpec

    specs = [OutputSpec.model_validate(o).model_dump(mode="json") for o in outputs]
    if DIR_TOKEN not in brief:
        raise ValueError(f"the brief never says where the folder is ({DIR_TOKEN})")
    folders = sorted(p for p in Path(packets_root).iterdir() if p.is_dir())
    if packet_ids:
        missing = sorted(set(packet_ids) - {p.name for p in folders})
        if missing:
            raise ValueError(f"no packet folders {missing} under {packets_root}")
        folders = [p for p in folders if p.name in set(packet_ids)]
    packets = []
    for folder in folders:
        files = _packet_files(folder, [s["name"] for s in specs])
        packets.append(SessionPacket(packet_id=folder.name, files=files,
                                     files_sha256=sha256_bytes(canonical_json_bytes(files))))
    plan = sealed_model(SessionPlan, plan_id=name, brief=brief,
                        brief_sha256=sha256_bytes(brief.encode("utf-8")), outputs=specs,
                        packets=packets, replicates=replicates,
                        created_at=datetime.now(timezone.utc).isoformat())
    write_once(Path(out_dir) / PLAN_FILE, pretty_json_bytes(plan))
    return plan


def load_session_plan(path: Path) -> SessionPlan:
    path = Path(path)
    if path.is_dir():
        path = path / PLAN_FILE
    plan = SessionPlan.model_validate_json(path.read_text(encoding="utf-8"))
    body = plan.model_dump(mode="json", exclude={"source_sha256"})
    if sha256_bytes(canonical_json_bytes(body)) != plan.source_sha256:
        raise ValueError(f"{path}: the plan does not match its seal; it was edited")
    for packet in plan.packets:
        if sha256_bytes(canonical_json_bytes(packet.files)) != packet.files_sha256:
            raise ValueError(f"{path}: packet {packet.packet_id}'s files do not match their digest")
    return plan


def session_payloads(plan: SessionPlan) -> List[Dict[str, Any]]:
    from ape.tasks.packet_session import PACKET_SESSION_TASK_TYPE

    return [{"task_type": PACKET_SESSION_TASK_TYPE,
             "task_id": f"session_{plan.plan_id}_{packet.packet_id}",
             "brief": plan.brief, "plan_id": plan.plan_id, "packet_id": packet.packet_id,
             "files": [{"path": path, "content": text} for path, text in packet.files.items()],
             "outputs": plan.outputs}
            for packet in plan.packets]


def _store(plan_dir: Path, plan: SessionPlan, packet_id: str, replicate: str, origin: str,
           locator: Dict[str, str], executor: Dict[str, str],
           outputs: Dict[str, str]) -> SessionOutput:
    stored = {}
    for out_name, text in outputs.items():
        data = text.encode("utf-8")
        target = Path(plan_dir) / OUTPUTS_DIR / packet_id / replicate / out_name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        stored[out_name] = {"sha256": sha256_bytes(data), "path": str(target)}
    return SessionOutput(plan_id=plan.plan_id, packet_id=packet_id, replicate=replicate,
                         origin=origin, locator=locator, executor=executor, outputs=stored)


def _write_index(plan_dir: Path, name: str, rows: Sequence[SessionOutput]) -> Path:
    path = Path(plan_dir) / OUTPUTS_DIR / f"{name}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_bytes(jsonl_bytes(rows))
    tmp.replace(path)
    return path


async def run_sessions(plan: SessionPlan, plan_dir: Path, scaffold, run_name: str,
                       logger) -> List[SessionOutput]:
    """Run every packet as a `packet_session` task and store what each sample left."""

    from ape.orchestration.config import EarlyStopMode
    from ape.orchestration.orchestrator import TaskOrchestrator
    from ape.orchestration.products import sample_products
    from ape.tasks.base import create_task_from_data

    if scaffold.execution.sample_count not in (1, plan.replicates):
        raise ValueError(f"the config asks for {scaffold.execution.sample_count} samples and the "
                         f"plan seals {plan.replicates}; the plan decides")
    from src.mathlib_review.analysis.matching import bind_run_to_plan

    bind_run_to_plan(scaffold.runs_base_dir, run_name, "session", plan.plan_id, plan.source_sha256)
    scaffold.execution.sample_count = plan.replicates
    scaffold.execution.early_stop_mode = EarlyStopMode.DISABLED
    tasks = [create_task_from_data(payload, scaffold,
                                   task_config_overrides=scaffold.task_config_overrides)
             for payload in session_payloads(plan)]
    orchestrator = TaskOrchestrator(config=scaffold, orchestrator_id=run_name, logger=logger)
    await orchestrator.run(tasks)
    from src.mathlib_review.analysis.matching import executor_of

    executor = executor_of(scaffold)
    rows = []
    for item in await sample_products(orchestrator.tasks_dir, tasks, plan.replicates):
        if item.product is None:
            continue
        rows.append(_store(
            plan_dir, plan, item.product["packet_id"], str(item.sample_index + 1), "task",
            {"run": run_name, "task_dir": str(orchestrator.tasks_dir / item.task_global_index),
             "sample": str(item.sample_index), "attempt": str(item.attempt_path)},
            executor, {k: v["content"] for k, v in item.product["outputs"].items()}))
    _write_index(plan_dir, f"task-{run_name}", rows)
    return rows


def import_session_outputs(plan: SessionPlan, plan_dir: Path, folders: Dict[str, Path], name: str,
                           executor: Optional[Dict[str, str]] = None) -> List[SessionOutput]:
    """Hand-launched sessions' folders, `{packet_id: folder}`: their declared outputs, checked as
    `submit_outputs` checks them, stored beside the plan. The folder's inputs are not re-read: the
    plan holds what the session was given."""

    from ape.tasks.packet_session import OutputSpec, output_problems

    known = {p.packet_id for p in plan.packets}
    unknown = sorted(set(folders) - known)
    if unknown:
        raise ValueError(f"packets {unknown} are not in plan {plan.plan_id}")
    specs = [OutputSpec.model_validate(o) for o in plan.outputs]
    executor = {"kind": "external session", "model": "unknown", "route": "unknown",
                **(executor or {})}
    rows = []
    for packet_id, folder in sorted(folders.items()):
        found, problems = output_problems(Path(folder), specs)
        if problems:
            raise ValueError(f"{folder}: {problems}")
        rows.append(_store(plan_dir, plan, packet_id, "1", "external_import",
                           {"folder": str(folder)}, executor, found))
    _write_index(plan_dir, f"import-{name}", rows)
    return rows


def session_outputs(plan_dir: Path) -> List[SessionOutput]:
    """Every stored session output beside a plan, from every run and import."""

    rows = []
    for path in sorted((Path(plan_dir) / OUTPUTS_DIR).glob("*.jsonl")):
        rows.extend(SessionOutput.model_validate(row) for row in jsonl_rows(path))
    return rows
