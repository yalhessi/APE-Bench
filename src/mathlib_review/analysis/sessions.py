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

What the outputs mean stays with the study; how they reach the next step does not:

4. **hand off** between sessions (`plan_sessions(inputs_from=...)`): a plan whose input files are
   upstream sessions' stored outputs, taken from them or, for folders sessions already worked in,
   checked against them; `lineage.json` beside the plan says which observation each input is.
5. **hand off** to a reviewer (`derive_context`, `cli probe context-derive`): a solo `context_file`
   whose per-PR sections are upstream outputs, with `<file>.lineage.json`; the reviewer input
   resolver (`review/inputs.py`) recomputes it from the observations before a run reads it and
   refuses a missing or changed one (implementation review follow-up, 2026-10-22, closure item 1).

Every read of an upstream output goes through `read_observation`, never a path.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from src.mathlib_review.io import (
    canonical_json_bytes, jsonl_bytes, jsonl_rows, pretty_json_bytes, sealed_model, sha256_bytes,
    sha256_file, write_once,
)
from src.mathlib_review.schema import SessionOutput, SessionPacket, SessionPlan
from src.mathlib_review.schema.runs import ContextLineage, InputLineage, ObservationRef

PLAN_FILE = "session_plan.json"
OUTPUTS_DIR = "outputs"
INDEX_FILE = "index.jsonl"
#: Beside a plan whose inputs are bound to upstream observations.
LINEAGE_FILE = "lineage.json"
#: Beside a derived context file: `<file>.lineage.json`.
CONTEXT_LINEAGE_SUFFIX = ".lineage.json"
#: Never part of a packet: a session's scratch.
SKIP_DIRS = {"tmp"}


def _packet_files(folder: Path, outputs: Sequence[str],
                  include: Optional[Sequence[str]] = None) -> Dict[str, str]:
    """A folder's files as a packet. `include` names exactly the files that were the session's
    inputs, for a folder a session has already finished in (its outputs, audits and scratch sit
    beside them); without it, every file is an input and a folder holding an output is refused."""

    files: Dict[str, str] = {}
    if include is not None:
        # A name with a glob character is a pattern (`base/**/*.lean`) and must match something; any
        # other name is one file and must exist.
        missing = sorted(name for name in include
                         if not (any(ch in name for ch in "*?[") and
                                 any(p.is_file() for p in folder.glob(name)))
                         and not (folder / name).is_file())
        if missing:
            raise ValueError(f"{folder} lacks the named input files {missing}")
        paths = sorted({p for name in include
                        for p in (folder.glob(name) if any(ch in name for ch in "*?[")
                                  else [folder / name]) if p.is_file()})
    else:
        done = [name for name in outputs if (folder / name).exists()]
        if done:
            raise ValueError(f"{folder} holds {done}: a finished session's folder is not a packet "
                             "(name its input files with `include` to plan it historically)")
        paths = sorted(p for p in folder.rglob("*") if p.is_file())
    for path in paths:
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
                  packet_ids: Optional[Sequence[str]] = None,
                  include: Optional[Sequence[str]] = None,
                  inputs_from: Optional[Dict[str, Any]] = None,
                  upstream_packets: Optional[Dict[str, str]] = None,
                  allow_unmatched: bool = False) -> SessionPlan:
    """Seal one session per packet folder under `packets_root` (or the named ones).

    `include` names the input files of each folder, for sessions that already ran there
    (`_packet_files`); the plan then holds what those sessions were given, and their outputs are
    imported against it.

    `inputs_from` is `{input path: {"plan_dir", "producer", "output"?, "replicate"?}}`: those inputs
    are upstream sessions' outputs, for the same packet id or the one `upstream_packets` maps it to.
    For a new plan the bytes are taken from the observation (`read_observation`); for a historical
    one (`include`) the folder's bytes are checked against the producer's observations -- or several
    producers', given as a list -- and an input no observation holds is refused unless
    `allow_unmatched`, which lists it with the reason.
    Either way `lineage.json` records the binding."""

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
    packets, bound, unmatched = [], {}, {}
    for folder in folders:
        files = _packet_files(folder, [s["name"] for s in specs], include)
        if inputs_from:
            files, bound[folder.name], missed = _bind_inputs(
                folder.name, files, inputs_from, (upstream_packets or {}).get(folder.name, folder.name),
                historical=include is not None)
            if missed:
                unmatched[folder.name] = missed
        packets.append(SessionPacket(packet_id=folder.name, files=files,
                                     files_sha256=sha256_bytes(canonical_json_bytes(files))))
    if unmatched and not allow_unmatched:
        raise ValueError(f"inputs no upstream observation holds: {unmatched}; bind them to the "
                         "producer that wrote them, or plan with allow_unmatched to record them so")
    plan = sealed_model(SessionPlan, plan_id=name, brief=brief,
                        brief_sha256=sha256_bytes(brief.encode("utf-8")), outputs=specs,
                        packets=packets, replicates=replicates,
                        created_at=datetime.now(timezone.utc).isoformat())
    if inputs_from:
        # The lineage first: a plan without its lineage would read as one with no upstream.
        lineage = sealed_model(InputLineage, plan_id=name, plan_sha256=plan.source_sha256,
                               bound=bound, unmatched=unmatched, created_at=plan.created_at)
        write_once(Path(out_dir) / LINEAGE_FILE, pretty_json_bytes(lineage))
    write_once(Path(out_dir) / PLAN_FILE, pretty_json_bytes(plan))
    return plan


def _bind_inputs(packet_id: str, files: Dict[str, str], inputs_from: Dict[str, Any],
                 upstream_packet: str, historical: bool):
    """`(files, {path: ObservationRef}, {path: reason})` for one packet's bound inputs.

    A historical input may name several upstream sources (a list): the reconstruction probe's goal
    briefs came from first extractions, revisions or repairs, each its own plan. It binds to the one
    observation among them whose stored bytes are the folder's, preferring the mapped packet id; two
    different observations with those bytes are refused as ambiguous rather than chosen between."""

    files, bound, missed = dict(files), {}, {}
    for path, spec in sorted(inputs_from.items()):
        sources = spec if isinstance(spec, list) else [spec]
        if not historical:
            if len(sources) != 1:
                raise ValueError(f"{path}: a new plan takes an input from exactly one producer")
            source = sources[0]
            output = source.get("output") or Path(path).name
            ref = observation(source["plan_dir"], source["producer"], upstream_packet, output,
                              source.get("replicate", "1"))
            text = read_observation(ref)
            if path in files and files[path] != text:
                raise ValueError(f"{packet_id}: the folder holds a {path} other than "
                                 f"{source['producer']}'s {upstream_packet} {output}")
            files[path], bound[path] = text, ref
            continue
        if path not in files:
            raise ValueError(f"{packet_id}: {path} is named for binding but is not one of its inputs")
        digest = sha256_bytes(files[path].encode("utf-8"))
        matches = []
        for source in sources:
            output = source.get("output") or Path(path).name
            matches.extend((source, row, output) for row in session_outputs(source["plan_dir"],
                                                                            source["producer"])
                           if output in row.outputs and row.outputs[output]["sha256"] == digest)
        preferred = [m for m in matches if m[1].packet_id == upstream_packet] or matches
        distinct = sorted({(str(m[0]["plan_dir"]), m[0]["producer"], m[1].packet_id, m[1].replicate)
                           for m in preferred})
        producers = ", ".join(s["producer"] for s in sources)
        if not preferred:
            missed[path] = f"no observation of {producers} has these bytes"
        elif len(distinct) > 1:
            raise ValueError(f"{packet_id}: {path} is the output of several observations {distinct}; "
                             "name the one it came from")
        else:
            source, row, output = preferred[0]
            bound[path] = observation(source["plan_dir"], source["producer"], row.packet_id, output,
                                      row.replicate)
    return files, bound, missed


def load_input_lineage(plan_dir: Path) -> Optional[InputLineage]:
    """The plan's input lineage, or None for a plan with no upstream; refused when edited or when it
    belongs to another seal of the plan."""

    path = Path(plan_dir) / LINEAGE_FILE
    if not path.is_file():
        return None
    lineage = InputLineage.model_validate_json(path.read_text(encoding="utf-8"))
    _check_seal(lineage, path)
    plan = load_session_plan(plan_dir)
    if lineage.plan_sha256 != plan.source_sha256:
        raise ValueError(f"{path} binds another seal of {plan.plan_id} than the one beside it")
    return lineage


def _check_seal(record, path: Path) -> None:
    body = record.model_dump(mode="json", exclude={"source_sha256"})
    if sha256_bytes(canonical_json_bytes(body)) != record.source_sha256:
        raise ValueError(f"{path} does not match its seal; it was edited")


def _repo_path(path: Path) -> str:
    """A path as the repository names it: relative to the root (the working directory) when inside."""

    path = Path(path)
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return str(path)


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


def _store(plan_dir: Path, plan: SessionPlan, producer: str, packet_id: str, replicate: str,
           origin: str, locator: Dict[str, str], executor: Dict[str, str],
           outputs: Dict[str, str]) -> SessionOutput:
    """Keep one observation's outputs under its producer, so two executions or imports of one plan
    hold their own bytes: until 2026-10-22 the path was `<packet>/<replicate>/<name>` and a second
    import replaced the first's files while the first's index still named its old digest
    (implementation review, finding 1). Re-storing the same bytes is a no-op; different bytes under
    one observation are refused, never overwritten."""

    stored = {}
    for out_name, text in outputs.items():
        data = text.encode("utf-8")
        target = Path(plan_dir) / OUTPUTS_DIR / producer / packet_id / replicate / out_name
        target.parent.mkdir(parents=True, exist_ok=True)
        write_once(target, data)
        stored[out_name] = {"sha256": sha256_bytes(data), "path": str(target)}
    return SessionOutput(plan_id=plan.plan_id, packet_id=packet_id, producer=producer,
                         replicate=replicate, origin=origin, locator=locator, executor=executor,
                         outputs=stored)


def read_output(row: SessionOutput, name: str) -> str:
    """One stored output's text, refused when its bytes no longer match the index's digest."""

    item = row.outputs[name]
    data = Path(item["path"]).read_bytes()
    if sha256_bytes(data) != item["sha256"]:
        raise ValueError(f"{item['path']} does not match the digest {row.producer} recorded for "
                         f"{row.packet_id}/{row.replicate}/{name}; it was changed after it was stored")
    return data.decode("utf-8")


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

    binding = bind_run_to_plan(scaffold.runs_base_dir, run_name, "session", plan.plan_id,
                               plan.source_sha256, scaffold)
    scaffold.execution.sample_count = plan.replicates
    scaffold.execution.early_stop_mode = EarlyStopMode.DISABLED
    tasks = [create_task_from_data(payload, scaffold,
                                   task_config_overrides=scaffold.task_config_overrides)
             for payload in session_payloads(plan)]
    orchestrator = TaskOrchestrator(config=scaffold, orchestrator_id=run_name, logger=logger)
    await orchestrator.run(tasks)
    executor = binding["executor"]          # the run's recorded route, never the invoking config's
    producer = f"task-{run_name}"
    rows = []
    for item in await sample_products(orchestrator.tasks_dir, tasks, plan.replicates):
        if item.product is None:
            continue
        rows.append(_store(
            plan_dir, plan, producer, item.product["packet_id"], str(item.sample_index + 1), "task",
            {"run": run_name, "task_dir": str(orchestrator.tasks_dir / item.task_global_index),
             "sample": str(item.sample_index), "attempt": str(item.attempt_path)},
            executor, {k: v["content"] for k, v in item.product["outputs"].items()}))
    _write_index(plan_dir, producer, rows)
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
        rows.append(_store(plan_dir, plan, f"import-{name}", packet_id, "1", "external_import",
                           {"folder": str(folder)}, executor, found))
    _write_index(plan_dir, f"import-{name}", rows)
    return rows


def session_outputs(plan_dir: Path, producer: Optional[str] = None) -> List[SessionOutput]:
    """Every stored session output beside a plan, from every run and import, or one producer's."""

    rows = []
    for path in sorted((Path(plan_dir) / OUTPUTS_DIR).glob("*.jsonl")):
        if producer is not None and path.stem != producer:
            continue
        rows.extend(SessionOutput.model_validate(row) for row in jsonl_rows(path))
    return rows


def observation(plan_dir: Path, producer: str, packet_id: str, output: str,
                replicate: str = "1") -> ObservationRef:
    """A reference to one stored output, checked readable now."""

    plan = load_session_plan(plan_dir)
    row = next((r for r in session_outputs(plan_dir, producer)
                if r.packet_id == packet_id and r.replicate == str(replicate)), None)
    if row is None:
        raise ValueError(f"{producer} holds no observation of {plan.plan_id}/{packet_id}/{replicate}")
    if output not in row.outputs:
        raise ValueError(f"{producer}'s {packet_id}/{replicate} has no output {output!r}")
    read_output(row, output)
    return ObservationRef(plan_id=plan.plan_id, plan_dir=_repo_path(plan_dir),
                          plan_sha256=plan.source_sha256, producer=producer, packet_id=packet_id,
                          replicate=str(replicate), output=output,
                          sha256=row.outputs[output]["sha256"])


def read_observation(ref: ObservationRef) -> str:
    """The text a reference names, refused when its plan was re-sealed or edited, the observation is
    gone, its index names other bytes, or the stored bytes changed: a missing or tampered upstream
    output never reaches the step that consumes it."""

    plan = load_session_plan(ref.plan_dir)
    if plan.source_sha256 != ref.plan_sha256:
        raise ValueError(f"{ref.plan_dir} was re-sealed since {ref.producer}'s {ref.packet_id} was "
                         "consumed; the observation belongs to another plan")
    row = next((r for r in session_outputs(ref.plan_dir, ref.producer)
                if r.packet_id == ref.packet_id and r.replicate == ref.replicate), None)
    if row is None:
        raise ValueError(f"{ref.producer} no longer holds {ref.plan_id}/{ref.packet_id}/"
                         f"{ref.replicate}; the consumer's input is missing")
    item = row.outputs.get(ref.output)
    if item is None or item["sha256"] != ref.sha256:
        raise ValueError(f"{ref.producer}'s {ref.packet_id}/{ref.replicate} {ref.output} is not the "
                         "output that was consumed (its index names other bytes)")
    return read_output(row, ref.output)


def _section_text(lead: str, text: str) -> str:
    lead = (lead or "").strip()
    return f"{lead}\n\n{text.strip()}" if lead else text.strip()


def context_lineage_path(context_file: Path) -> Path:
    context_file = Path(context_file)
    return context_file.with_name(context_file.name + CONTEXT_LINEAGE_SUFFIX)


def _compose(base: Path, sections: Sequence[Dict[str, str]],
             rows: Dict[str, List[ObservationRef]]) -> str:
    from src.mathlib_review.analysis.probes import context_with_sections

    extra = {int(pr): [{"title": section["title"],
                        "text": _section_text(section.get("lead", ""), read_observation(ref))}
                       for section, ref in zip(sections, refs)]
             for pr, refs in rows.items()}
    return context_with_sections(Path(base), extra)


def derive_context(*, base: Path, sections: Sequence[Dict[str, Any]], prs: Sequence[int],
                   out: Path) -> ContextLineage:
    """Write a solo `context_file` whose per-PR sections are upstream session outputs.

    Each PR keeps the base file's row and gains, after its own sections, one section per entry of
    `sections`: `{"title", "lead", "plan_dir", "producer", "output", "replicate"?, "by_pr"?: {pr:
    {any of plan_dir, producer, packet_id, output, replicate}}}`; the packet defaults to `pr<N>`.
    The text is the lead, a blank line and the output verbatim (stripped), which is how the
    reconstruction probe's Phase A built its strategies. Writes the file and its lineage once;
    deriving the same file again is a no-op."""

    rows: Dict[str, List[ObservationRef]] = {}
    for pr in sorted(int(p) for p in prs):
        refs = []
        for section in sections:
            source = {**section, **(section.get("by_pr") or {}).get(str(pr), {})}
            refs.append(observation(source["plan_dir"], source["producer"],
                                    source.get("packet_id") or f"pr{pr}", source["output"],
                                    source.get("replicate", "1")))
        rows[str(pr)] = refs
    kept = [{"title": section["title"], "lead": section.get("lead", "")} for section in sections]
    data = _compose(base, kept, rows).encode("utf-8")
    out = Path(out)
    if out.is_file() and out.read_bytes() != data:
        raise ValueError(f"{out} exists with other bytes; a derived context file is written once")
    lineage_path = context_lineage_path(out)
    if lineage_path.is_file():
        held = load_context_lineage(lineage_path)
        if (held.context_sha256, held.base_sha256, held.sections, held.rows) == (
                sha256_bytes(data), sha256_file(Path(base)), kept, rows):
            write_once(out, data)
            return held
    lineage = sealed_model(ContextLineage, context_sha256=sha256_bytes(data),
                           base_path=_repo_path(base), base_sha256=sha256_file(Path(base)),
                           sections=kept, rows=rows,
                           created_at=datetime.now(timezone.utc).isoformat())
    out.parent.mkdir(parents=True, exist_ok=True)
    write_once(lineage_path, pretty_json_bytes(lineage))
    write_once(out, data)
    return lineage


def load_context_lineage(path: Path) -> ContextLineage:
    lineage = ContextLineage.model_validate_json(Path(path).read_text(encoding="utf-8"))
    _check_seal(lineage, Path(path))
    return lineage


def verify_context(context_file: Path) -> Optional[ContextLineage]:
    """The lineage of a derived context file, after recomputing the file from it; None for a file
    with no lineage. Refused when the file, its base or any upstream output is not what was
    derived from -- before a reviewer reads it."""

    path = context_lineage_path(context_file)
    if not path.is_file():
        return None
    lineage = load_context_lineage(path)
    data = Path(context_file).read_bytes()
    if sha256_bytes(data) != lineage.context_sha256:
        raise ValueError(f"{context_file} is not the file its lineage derived; it was edited")
    if sha256_file(Path(lineage.base_path)) != lineage.base_sha256:
        raise ValueError(f"{context_file}'s base {lineage.base_path} changed since the derivation")
    if _compose(Path(lineage.base_path), lineage.sections, lineage.rows).encode("utf-8") != data:
        raise ValueError(f"{context_file} no longer follows from its upstream outputs")
    return lineage


def lineage_chain(ref: ObservationRef, depth: int = 4) -> Dict[str, Any]:
    """An observation and, through each plan's `lineage.json`, the observations its inputs were,
    back to a plan with no upstream: what a derived input was made from, step by step."""

    node: Dict[str, Any] = {"observation": ref.model_dump(mode="json")}
    lineage = load_input_lineage(ref.plan_dir) if depth > 0 else None
    if lineage is not None:
        node["inputs"] = {path: lineage_chain(up, depth - 1)
                          for path, up in (lineage.bound.get(ref.packet_id) or {}).items()}
        if lineage.unmatched.get(ref.packet_id):
            node["unmatched_inputs"] = lineage.unmatched[ref.packet_id]
    return node
