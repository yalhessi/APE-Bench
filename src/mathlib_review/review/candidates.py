"""Validate model responses into stable c1 candidate records."""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from src.mathlib_review.io import canonical_json_bytes, jsonl_bytes, sealed_model, sha256_bytes, write_once
from src.mathlib_review.agenda.render_prompts import renderer_number
from src.mathlib_review.schema import (
    CandidateClaim,
    CandidateRejection,
    ChangeGraph,
    EvidenceRequest,
    ProposedEdit,
    ReviewWorkUnit,
)


def plan_evidence(concern_family: str, primary_subject: str, requested_change: str,
                  proposed_edit: ProposedEdit | None) -> List[EvidenceRequest]:
    """Derive evidence obligations after ask generation so evidentiary ease cannot bias recall."""
    query = f"primary={primary_subject}; requested_change={requested_change}"
    collectors = ["local_context"]
    if concern_family in {"correctness", "proof-golf"}:
        collectors.append("lean_compile")
    elif concern_family in {"duplication", "naming", "generalization"}:
        collectors.append("repository_search")
    elif concern_family in {"documentation", "style", "scope"}:
        collectors.extend(["policy", "repository_search"])
    if proposed_edit is not None and "lean_compile" not in collectors:
        collectors.append("lean_compile")
    return [EvidenceRequest(collector=collector, query=query, purpose="both")
            for collector in collectors]


def _target_spans(graph: ChangeGraph, change_id: str) -> List[Tuple[int, int]]:
    target = next(item for item in graph.targets if item.change_id == change_id)
    entities = {item.entity_id: item for item in graph.entities}
    ranges = {item.range_id: item for item in graph.changed_ranges}
    spans = [
        (entities[entity_id].span.line_start, entities[entity_id].span.line_end)
        for entity_id in target.reviewed_entity_ids
        if entity_id in entities and entities[entity_id].side == "reviewed"
    ]
    if not spans:
        spans = [
            (ranges[range_id].reviewed_span.line_start, ranges[range_id].reviewed_span.line_end)
            for range_id in target.changed_range_ids
            if range_id in ranges and ranges[range_id].reviewed_span is not None
        ]
    return spans


def diagnostic_lines(output: str, path: str) -> List[int]:
    escaped = re.escape(path)
    patterns = [rf"(?:^|\s|/){escaped}:(\d+):", rf"file=(?:[^,]*/)?{escaped},line=(\d+)"]
    return [int(match) for pattern in patterns for match in re.findall(pattern, output, re.MULTILINE)]


def _tool_env(workspace: Path) -> Dict[str, str]:
    from src.mathlib_review.workspace import tool_env as evidence_tool_env
    return evidence_tool_env(workspace)


def _deterministic_candidate(unit: ReviewWorkUnit, graph: ChangeGraph, change_id: str,
                             concern_family: str, concern_label: str, claim: str,
                             requested_change: str, collectors: List[str]) -> CandidateClaim:
    target = next(item for item in graph.targets if item.change_id == change_id)
    entity_ids = target.reviewed_entity_ids or target.base_entity_ids
    subject = unit.primary_subjects_by_change[change_id]
    requests = [EvidenceRequest(
        collector=collector,
        query=f"primary={subject}; requested_change={requested_change}", purpose="both",
    ) for collector in ["local_context", *collectors]]
    payload = {
        "producer": "deterministic", "work_unit_id": unit.work_unit_id,
        "episode_id": unit.episode_id, "pr_number": unit.pr_number,
        "change_ids": [change_id], "entity_ids": entity_ids[:1],
        "primary_change_id": change_id,
        "primary_entity_id": entity_ids[0] if entity_ids else None,
        "primary_subject": subject, "requested_change": requested_change,
        "concern_family": concern_family, "concern_label": concern_label,
        "severity": "blocking" if concern_family == "correctness" else "advisory",
        "claim": claim, "suggested_fix": None, "proposed_edit": None,
        "evidence_requests": [item.model_dump(mode="json") for item in requests],
    }
    digest = sha256_bytes(canonical_json_bytes(payload))
    return CandidateClaim(candidate_id=f"candidate:{digest[:24]}", source_sha256=digest, **payload)


def discover_deterministic_candidates(
    units: Iterable[ReviewWorkUnit], graphs: Iterable[ChangeGraph],
    workspace_map: Dict[str, str], run_command=subprocess.run,
) -> Tuple[List[CandidateClaim], Dict[str, str]]:
    """Run universal repository checks once per scheduled reviewed file."""
    units = list(units)
    graph_by_episode = {item.episode_id: item for item in graphs}
    unit_by_change = {change_id: unit for unit in units for change_id in unit.change_ids}
    targets_by_episode_path = {}
    for unit in units:
        graph = graph_by_episode[unit.episode_id]
        targets = {item.change_id: item for item in graph.targets}
        for change_id in unit.change_ids:
            target = targets[change_id]
            if target.path.endswith(".lean"):
                targets_by_episode_path.setdefault((unit.episode_id, target.path), []).append(change_id)

    discovered, failures = [], {}
    for (episode_id, path), change_ids in sorted(targets_by_episode_path.items()):
        workspace_raw = workspace_map.get(episode_id)
        if not workspace_raw:
            failures[f"{episode_id}:{path}"] = "workspace_not_supplied"
            continue
        workspace = Path(workspace_raw)
        source_path = workspace / path
        if not source_path.is_file():
            failures[f"{episode_id}:{path}"] = "reviewed_file_missing"
            continue
        graph = graph_by_episode[episode_id]
        env = _tool_env(workspace)
        try:
            compile_proc = run_command(
                ["lake", "env", "lean", str(source_path)], cwd=workspace, text=True,
                capture_output=True, timeout=180, env=env,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            failures[f"compile:{episode_id}:{path}"] = type(exc).__name__
            continue
        compile_output = (compile_proc.stdout + "\n" + compile_proc.stderr).strip()
        compile_lines = set(diagnostic_lines(compile_output, path)) if compile_proc.returncode else set()
        for change_id in change_ids:
            spans = _target_spans(graph, change_id)
            if any(start <= line <= end for line in compile_lines for start, end in spans):
                unit = unit_by_change[change_id]
                subject = unit.primary_subjects_by_change[change_id]
                discovered.append(_deterministic_candidate(
                    unit, graph, change_id, "correctness", "target-local Lean compile failure",
                    f"`{subject}` fails to compile in the reviewed state.",
                    f"Fix `{subject}` so the reviewed file compiles.", ["lean_compile"],
                ))

        style_script = workspace / "scripts" / "lint-style.py"
        if not style_script.is_file():
            failures[f"style:{episode_id}:{path}"] = "style_policy_checker_missing"
            continue
        try:
            style_proc = run_command(
                [sys.executable, str(style_script), path], cwd=workspace, text=True,
                capture_output=True, timeout=60, env=env,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            failures[f"style:{episode_id}:{path}"] = type(exc).__name__
            continue
        style_output = (style_proc.stdout + "\n" + style_proc.stderr).strip()
        style_lines = set(diagnostic_lines(style_output, path)) if style_proc.returncode == 1 else set()
        for change_id in change_ids:
            spans = _target_spans(graph, change_id)
            if any(start <= line <= end for line in style_lines for start, end in spans):
                unit = unit_by_change[change_id]
                subject = unit.primary_subjects_by_change[change_id]
                discovered.append(_deterministic_candidate(
                    unit, graph, change_id, "style", "repository style checker failure",
                    f"`{subject}` triggers the repository style checker.",
                    f"Fix the style diagnostic in `{subject}`.", ["policy"],
                ))
    unique = {item.candidate_id: item for item in discovered}
    return list(unique.values()), failures


_REJECTION_CODES = (
    ("evidence_requests", "candidate_planned_own_evidence"),
    ("outside its work unit", "change_id_outside_work_unit"),
    ("primary_change_id", "primary_change_id_not_in_change_ids"),
    ("primary_subject", "primary_subject_mismatch"),
    ("primary_entity_id", "primary_entity_mismatch"),
    ("does not name its primary subject", "claim_does_not_name_subject"),
    ("empty", "empty_required_field"),
)


def _rejection_code(message: str) -> str:
    """A stable code per failure mode, so drop rates are aggregatable across runs."""

    for needle, code in _REJECTION_CODES:
        if needle in message:
            return code
    return "other"


def invocation_work_unit(invocation_id: str) -> str:
    """The work unit a composite invocation id belongs to.

    The focused arm schedules four specs against one work unit, so `wu:…#proof_golf` and
    `wu:…#proof_idiom` are separate invocations of the same unit. Plain work-unit ids are
    returned unchanged, which is what every holistic invocation is.
    """

    return invocation_id.split("#", 1)[0]


def candidates_from_response(unit: ReviewWorkUnit, response: Dict[str, Any],
                             *, strict: bool = True, spec_id: Optional[str] = None,
                             _ordinal: Optional[int] = None):
    """Validate one response's candidates.

    `spec_id`, when given, is the *invocation's* spec and is authoritative. A model is not
    trusted to label which focused agent it is: golf and idiom both declare
    `proof_simplification` while making different claims, and `verify_proof_simplification`
    keys its warrant on the spec — so a golf agent that reported itself as `proof_idiom`
    would inherit idiom's no-length-requirement rule and repeal golf's own. A candidate that
    self-reports a *different* spec is a contract violation rather than a preference.

    With `strict=True` (the default, preserving every existing caller and gate) the first
    malformed candidate raises. With `strict=False` the batch continues and each rejection
    is recorded as a `CandidateRejection`.

    The distinction matters: a malformed *candidate* is one bad item among good ones, while
    a failed *terminal response* means the model produced nothing usable and is a coverage
    failure. Raising on the former discarded every other candidate in the run and left no
    artifact, so drop rates were unmeasurable — and a silently smaller candidate set makes
    the system look more precise than it is.

    Returns the candidate list in strict mode, or `(candidates, rejections)` otherwise.

    `_ordinal` is private and exists because the non-strict path validates each candidate by
    recursing on a one-element list, where the loop index is always 0. Without it every
    candidate in a non-strict batch was sealed with `ordinal=0` — measured on the v5 probe,
    all 5 candidates including two responses that returned two each. That is not cosmetic:
    `ordinal` disambiguates `candidate_id`, and finalization joins verification artifacts on
    `(work_unit_id, ordinal)`, so a collapsed ordinal lets one candidate's compile warrant
    admit a sibling the compiler never saw. v4's own callers are strict and were never
    affected.
    """

    raw_candidates = response.get("candidates")
    if not isinstance(raw_candidates, list):
        raise ValueError("response must contain a candidates list; [] is valid")
    allowed = set(unit.change_ids)
    result = []
    rejections: List[CandidateRejection] = []
    for index, raw in enumerate(raw_candidates):
        if not strict:
            try:
                result.extend(candidates_from_response(
                    unit, {"candidates": [raw]}, strict=True, spec_id=spec_id,
                    _ordinal=index,
                ))
            except ValueError as error:
                rejections.append(sealed_model(
                    CandidateRejection,
                    work_unit_id=unit.work_unit_id,
                    pr_number=unit.pr_number,
                    ordinal=index,
                    reason_code=_rejection_code(str(error)),
                    detail=str(error),
                    raw_sha256=sha256_bytes(canonical_json_bytes(raw)),
                ))
            continue
        if "evidence_requests" in raw:
            raise ValueError(f"candidate {index} must not plan its own evidence requests")
        change_ids = list(dict.fromkeys(raw.get("change_ids") or []))
        allowed_by_suffix = {item.removeprefix("change:"): item for item in unit.change_ids}
        change_ids = [allowed_by_suffix.get(item, item) for item in change_ids]
        if not change_ids or not set(change_ids) <= allowed:
            raise ValueError(f"candidate {index} addresses change IDs outside its work unit")
        primary_change_id = allowed_by_suffix.get(raw.get("primary_change_id"),
                                                  raw.get("primary_change_id"))
        if primary_change_id not in change_ids:
            raise ValueError(f"candidate {index} primary_change_id is not one of its change_ids")
        expected_subject = unit.primary_subjects_by_change.get(primary_change_id)
        primary_subject = raw.get("primary_subject")
        if expected_subject is None or primary_subject != expected_subject:
            raise ValueError(f"candidate {index} primary_subject does not match its change target")
        issue_kind = raw.get("issue_kind")
        if renderer_number(unit.renderer_version) >= 12 and not issue_kind:
            # Required from /12: without it a claim cannot be routed to a verifier, and an
            # unroutable claim can never be published. Failing here names the reason.
            raise ValueError(f"candidate {index} is missing issue_kind")
        allowed_entities = set(unit.entity_ids_by_change.get(primary_change_id, []))
        primary_entity_id = raw.get("primary_entity_id")
        if ((allowed_entities and primary_entity_id not in allowed_entities) or
                (not allowed_entities and primary_entity_id is not None)):
            raise ValueError(f"candidate {index} primary_entity_id does not match its change target")
        proposed_edit_raw = raw.get("proposed_edit")
        if proposed_edit_raw:
            from ape.tasks.lean_tasks.formal_math.review.candidates import (
                normalize_proposed_edit_path,
            )

            proposed_edit_raw = {
                **proposed_edit_raw,
                "path": normalize_proposed_edit_path(proposed_edit_raw.get("path", "")),
            }
        proposed_edit = (
            ProposedEdit.model_validate(proposed_edit_raw) if proposed_edit_raw else None
        )
        concern_label = raw.get("concern_label")
        concern_family = raw.get("concern_family")
        if concern_family is None:
            concern_family = concern_label if concern_label in {
                "correctness", "proof-golf", "duplication", "naming", "generalization",
                "documentation", "style", "scope", "other",
            } else "other"
        claim = str(raw.get("claim") or "").strip()
        requested_change = str(raw.get("requested_change") or "").strip()
        if not claim:
            raise ValueError(f"candidate {index} has an empty claim")
        if not requested_change:
            raise ValueError(f"candidate {index} has an empty requested_change")
        if "/" not in primary_subject:
            short_subject = primary_subject.rsplit(".", 1)[-1]
            if short_subject not in f"{claim} {requested_change}":
                raise ValueError(f"candidate {index} does not name its primary subject")
        declared_spec_id = raw.get("spec_id")
        if spec_id is not None and declared_spec_id not in (None, spec_id):
            raise ValueError(
                f"candidate {index} reports spec_id {declared_spec_id!r} but was produced by "
                f"the {spec_id!r} invocation"
            )
        effective_spec_id = spec_id if spec_id is not None else declared_spec_id
        requests = plan_evidence(concern_family, primary_subject, requested_change, proposed_edit)
        payload = {
            "producer": "model", "work_unit_id": unit.work_unit_id,
            "ordinal": index if _ordinal is None else _ordinal,
            "change_ids": change_ids,
            "entity_ids": [primary_entity_id] if primary_entity_id else [],
            "primary_change_id": primary_change_id, "primary_entity_id": primary_entity_id,
            "primary_subject": primary_subject, "requested_change": requested_change,
            "concern_family": concern_family, "concern_label": concern_label,
            "issue_kind": issue_kind,
            # In the identity payload, not just on the record: two specs scheduled on the
            # same work unit can produce a byte-identical candidate at the same ordinal,
            # and without this they would collide on `candidate_id`.
            "spec_id": effective_spec_id,
            "severity": raw.get("severity"), "claim": claim,
            "suggested_fix": raw.get("suggested_fix"),
            "proposed_edit": proposed_edit.model_dump(mode="json") if proposed_edit else None,
            "evidence_requests": [item.model_dump(mode="json") for item in requests],
        }
        digest = sha256_bytes(canonical_json_bytes(payload))
        result.append(CandidateClaim(
            candidate_id=f"candidate:{digest[:24]}", producer="model", work_unit_id=unit.work_unit_id,
            ordinal=index if _ordinal is None else _ordinal,
            episode_id=unit.episode_id, pr_number=unit.pr_number, change_ids=change_ids,
            entity_ids=payload["entity_ids"], primary_change_id=primary_change_id,
            primary_entity_id=primary_entity_id, primary_subject=primary_subject,
            requested_change=requested_change, concern_family=payload["concern_family"],
            # Passed through as opaque strings, and *not* in `payload`: the arm layer owns
            # this vocabulary (it is the only layer that knows what an arm is for), and an
            # annotation must not move `candidate_id`.
            concern_tags=[
                tag for tag in (raw.get("concern_tags") or []) if isinstance(tag, str)
            ],
            issue_kind=payload["issue_kind"], spec_id=payload["spec_id"],
            concern_label=payload["concern_label"],
            severity=payload["severity"], claim=payload["claim"],
            suggested_fix=payload["suggested_fix"], proposed_edit=proposed_edit,
            evidence_requests=requests,
            model_confidence=raw.get("model_confidence"), source_sha256=digest,
        ))
    return (result, rejections) if not strict else result


def ingest_responses(units: Iterable[ReviewWorkUnit], responses: Iterable[Dict[str, Any]],
                     *, expected_invocations: Optional[Iterable[str]] = None):
    """Ingest terminal responses, one per *invocation*.

    The exactly-one rule is per invocation, not per work unit. The holistic arm makes these
    the same thing, but the focused arm runs four specs against one unit, and keying on the
    work unit would read those four terminal responses as four duplicates of one and raise.

    `expected_invocations` is the coverage denominator when the run is not simply "every work
    unit once" — pass the scheduler's invocation ids for a focused run. Without it the
    denominator stays the full unit set, which is what every existing caller means.
    """

    unit_by_id = {unit.work_unit_id: unit for unit in units}
    rows_by_key, candidates = {}, []
    for row in responses:
        key = row.get("invocation_id") or row.get("work_unit_id")
        work_unit_id = row.get("work_unit_id") or invocation_work_unit(key or "")
        if work_unit_id not in unit_by_id:
            raise ValueError(f"unknown work unit in response: {work_unit_id}")
        rows_by_key.setdefault(key, []).append((work_unit_id, row))
    expected = set(expected_invocations) if expected_invocations is not None else set(unit_by_id)
    missing = expected - set(rows_by_key)
    if missing:
        raise ValueError(f"missing terminal responses for {len(missing)} invocations")
    unexpected = set(rows_by_key) - expected
    if unexpected:
        # Not merely noise: an unscheduled invocation means candidates entered the run that
        # no plan accounts for, and the gold-free scheduling claim rests on the plan.
        raise ValueError(f"{len(unexpected)} responses for unscheduled invocations")
    for key, entries in rows_by_key.items():
        successful = [item for item in entries if item[1].get("success") is not False]
        if len(successful) != 1:
            errors = [row.get("error") for _wu, row in entries if row.get("success") is False]
            raise ValueError(
                f"invocation {key} has {len(successful)} successful terminal responses; "
                f"failures={errors}"
            )
        work_unit_id, row = successful[0]
        spec_id = row.get("spec_id")
        if spec_id is None and key and "#" in key:
            spec_id = key.split("#", 1)[1]
        candidates.extend(candidates_from_response(
            unit_by_id[work_unit_id], row.get("response") or row, spec_id=spec_id,
        ))
    return candidates


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-units", type=Path, required=True)
    parser.add_argument("--responses", type=Path, nargs="+", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--allow-subset", action="store_true",
                        help="Evaluate only work-unit IDs present in responses (smoke runs)")
    parser.add_argument("--graphs", type=Path)
    parser.add_argument("--workspace-map", type=Path)
    parser.add_argument("--deterministic-discovery", action="store_true",
                        help="Add universal compile/style candidates for scheduled reviewed targets")
    args = parser.parse_args()
    units = [ReviewWorkUnit.model_validate_json(x) for x in args.work_units.read_text().splitlines() if x]
    responses = [json.loads(x) for path in args.responses for x in path.read_text().splitlines() if x]
    if args.allow_subset:
        response_ids = {row.get("work_unit_id") for row in responses}
        units = [unit for unit in units if unit.work_unit_id in response_ids]
    candidates = ingest_responses(units, responses)
    deterministic = []
    discovery_failures = {}
    if args.deterministic_discovery:
        if args.graphs is None or args.workspace_map is None:
            raise ValueError("deterministic discovery requires --graphs and --workspace-map")
        graphs = [ChangeGraph.model_validate_json(x) for x in args.graphs.read_text().splitlines() if x]
        deterministic, discovery_failures = discover_deterministic_candidates(
            units, graphs, json.loads(args.workspace_map.read_text()))
        candidates.extend(deterministic)
    candidates = list({item.candidate_id: item for item in candidates}.values())
    write_once(args.out, jsonl_bytes(candidates))
    print(json.dumps({"work_units": len(units), "model_candidates": len(candidates) - len(deterministic),
                      "deterministic_candidates": len(deterministic),
                      "candidates": len(candidates), "discovery_failures": discovery_failures}, indent=2))


if __name__ == "__main__":
    main()
