"""Generic deterministic executor for frozen systematic-opportunity treatments.

This module deliberately separates scheduling and capability assessment from operator execution.
Every scheduled task receives one terminal ``InvestigationRecord`` plus a phase-level ledger row;
supported implementations are dispatched by implementation ID, never PR number or gold ID.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Tuple

from ape.toolkits.code.lean.lean_parser import parse_major_declarations

from .change_graph import apply_file_patch, parse_unified_diff
from .evidence import _tool_env
from .implementation_registry import load_implementations
from .io import (
    COMPILED_TARGET,
    canonical_json_bytes,
    jsonl_bytes,
    load_jsonl,
    pretty_json_bytes,
    sealed_from_payload,
    sha256_bytes,
    write_once,
)
from .operators.canonical_api import (
    build_declaration_index,
    check_applicability,
    evidence_artifact,
    is_high_confidence_insert_separation,
    propose_insert_separation_replacement,
    rank_declarations,
)
from .operators.naming_contrast import (
    POPULATION_VERSION,
    check_name_collision,
    declaration_conclusion,
    infer_semantic_subject,
    population_counts,
    proposed_subject_name,
    scan_repository_population,
    strong_subject_prefix_norm,
)
from .operators.naming_norm import (
    POPULATION_VERSION as NORM_POPULATION_VERSION,
    SUBJECT_CLASSIFIER_VERSION as NORM_CLASSIFIER_VERSION,
    conclusion_subject,
    propose_rename,
    scan_population,
)
from .operators.lint_policy import (
    LINT_VERSION,
    POLICY_VERSION,
    find_forbidden_construct,
    lint_target,
)
from .operators.wrapper_composition import discover_wrapper_composition
from .schema import (
    CapabilityAssessment,
    ChangeGraph,
    InvestigationRecord,
    InvestigationTask,
    OpportunityEvidenceArtifact,
    OpportunityTransformation,
    OperatorRun,
    ReviewEpisodeInput,
    ReviewOpportunity,
)


#: /2 — the runners began rendering their quantitative warrant (population counts, retrieval
#:      scores, named witness roles) into `observed_pattern` and `transformation.description`.
#:      The /1 artifacts under `results/pr_review_v4/runs/phase10-executor-smoke-*` predate
#:      that and are not comparable; see
#:      `results/pr_review_v4/audits/phase10-executor-equivalence-verdict.md`.
#: /3 — compile diagnostics stopped carrying the random temporary filename Lean was handed.
#:      Under /2, 129 of 410 evidence artifacts in a medium run embedded that name, so
#:      re-running the same inputs produced different evidence hashes and different
#:      opportunity IDs: identical in content, but not byte-reproducible. /2 and /3 artifacts
#:      are therefore not hash-comparable; their *contents* are.
#: /4 — a failing file yields one finding instead of one per declaration in it. Under /3 a
#:      single `lake env lean` failure was restated once per change target, turning 12 real
#:      failures into 128 findings and asserting that targets containing no error "fail to
#:      compile". /3 and /4 opportunity counts are not comparable.
EXECUTOR_VERSION = "generic-opportunity-executor/4"

DEFAULT_WORKSPACES = Path("data/code_execute/repos/mathlib4/workspaces")


@dataclass
class RunnerOutcome:
    operator_runs: List[OperatorRun] = field(default_factory=list)
    evidence: List[OpportunityEvidenceArtifact] = field(default_factory=list)
    opportunities: List[ReviewOpportunity] = field(default_factory=list)
    disposition: str = "checked_no_opportunity"
    basis: str = "The supported implementation completed without an opportunity."
    execution_status: str = "completed"


Runner = Callable[
    [InvestigationTask, ChangeGraph, ReviewEpisodeInput, Path, Dict], RunnerOutcome
]


def _operator_run(
    task: InvestigationTask,
    operator: str,
    status: str,
    artifact_ids: Iterable[str],
    result_count: int,
    query_sha256: Optional[str] = None,
    failure_reason: Optional[str] = None,
) -> OperatorRun:
    payload = {
        "investigation_id": task.investigation_id,
        "operator": operator,
        "status": status,
        "query_sha256": query_sha256,
        "artifact_ids": list(artifact_ids),
        "result_count": result_count,
        "failure_reason": failure_reason,
    }
    return sealed_from_payload(OperatorRun, "operator_run", payload)


def _opportunity(
    task: InvestigationTask,
    observed_pattern: str,
    artifact_ids: List[str],
    transformation: Optional[OpportunityTransformation],
    score: float,
    related_change_ids: Optional[List[str]] = None,
) -> ReviewOpportunity:
    payload = {
        "investigation_id": task.investigation_id,
        "method_id": task.method_id,
        "episode_id": task.episode_id,
        "pr_number": task.pr_number,
        "primary_change_id": task.primary_change_id,
        # A file-level finding names the other targets it also covers, so downstream
        # consumers can see its true scope instead of inferring it from repetition.
        "related_change_ids": (
            task.related_change_ids if related_change_ids is None else related_change_ids
        ),
        "observed_pattern": observed_pattern,
        "proposed_transformation": (
            transformation.model_dump(mode="json") if transformation else None
        ),
        "source_artifact_ids": artifact_ids,
        "discovery_rank": 1,
        "discovery_score": score,
        "source_provenance": "automatic",
    }
    return sealed_from_payload(ReviewOpportunity, "opportunity", payload)


def _record(
    task: InvestigationTask,
    outcome: RunnerOutcome,
) -> InvestigationRecord:
    followup_ids = (
        [f"followup:{task.source_sha256[:24]}"]
        if outcome.disposition == "needs_followup" else []
    )
    payload = {
        "investigation_id": task.investigation_id,
        "execution_status": outcome.execution_status,
        "disposition": outcome.disposition,
        "operator_run_ids": [item.operator_run_id for item in outcome.operator_runs],
        "artifact_ids": [item.artifact_id for item in outcome.evidence],
        "opportunity_ids": [item.opportunity_id for item in outcome.opportunities],
        "followup_ids": followup_ids,
        "basis": outcome.basis,
        "producer": "deterministic",
    }
    digest = sha256_bytes(canonical_json_bytes(payload))
    return InvestigationRecord(source_sha256=digest, **payload)


#: Lean diagnostics, e.g. `<compiled-target>:523:10: error(lean.unknownIdentifier): …`.
#: The optional parenthesised tag matters: matching a bare `error:` silently misses every
#: tagged diagnostic, which is most of them.
_LEAN_ERROR_RE = re.compile(
    rf"{re.escape(COMPILED_TARGET)}:(\d+):\d+: error(?:\([^)]*\))?:"
)

#: Reserved `cache` key holding the precomputed per-file claimants (see `file_claimants`).
_CLAIMANTS_KEY = "__file_claimants__"


def _error_lines(diagnostics: str) -> List[int]:
    """Ascending, de-duplicated line numbers Lean reported an *error* on."""

    return sorted({int(line) for line in _LEAN_ERROR_RE.findall(diagnostics or "")})


def _targets_covering(graph: ChangeGraph, path: str, lines: Iterable[int]) -> List[str]:
    """Names of changed declarations in `path` whose reviewed span contains a failing line.

    Attribution is reported, never used to decide whether a finding exists: change-target
    spans are hunk-level, so on some files every target covers the same line while on others
    the failing line lies outside every changed span entirely.
    """

    lines = list(lines)
    if not lines:
        return []
    spans = {item.range_id: item.reviewed_span for item in graph.changed_ranges}
    names = []
    for target in graph.targets:
        if target.path != path:
            continue
        covering = any(
            span is not None and span.line_start <= line <= span.line_end
            for span in (spans.get(range_id) for range_id in target.changed_range_ids)
            for line in lines
        )
        if covering:
            # Not every change target is a named declaration — imports, module docs and
            # bare commands have no name. Falling back to the `change_id` would print a
            # sha256 into a review comment, so unnamed targets are labelled by kind.
            names.append(target.declaration_name or f"<{target.kind}>")
    return sorted(names)


def file_claimants(
    tasks: Iterable[InvestigationTask],
    assessments: Iterable[CapabilityAssessment],
    graphs: Iterable[ChangeGraph],
) -> Dict[Tuple[str, str, str], str]:
    """Pick one scheduled task per (implementation, episode, file) to carry a file finding.

    Computed once, up front, from the whole task set rather than accumulated during
    dispatch: a claimant that depended on execution order would make each task's outcome a
    function of which tasks ran before it.

    The claimant must be chosen among *supported* tasks, not simply the file's first change
    target. On medium, 3 of 85 files have a lowest-`change_id` target that is not scheduled
    for the implementation, so anchoring on the graph alone would silently drop the finding
    for those files.
    """

    change_id_by_task = {item.investigation_id: item.primary_change_id for item in tasks}
    path_by_change = {
        target.change_id: target.path for graph in graphs for target in graph.targets
    }
    best: Dict[Tuple[str, str, str], Tuple[str, str]] = {}
    for assessment in assessments:
        if assessment.status != "supported":
            continue
        change_id = change_id_by_task.get(assessment.investigation_id)
        path = path_by_change.get(change_id)
        if path is None:
            continue
        key = (assessment.implementation_id, assessment.episode_id, path)
        candidate = (change_id, assessment.investigation_id)
        if key not in best or candidate < best[key]:
            best[key] = candidate
    return {key: investigation_id for key, (_, investigation_id) in best.items()}


def _file_claimant(
    cache: Dict, implementation_id: str, episode: ReviewEpisodeInput, path: str
) -> Optional[str]:
    return cache.get(_CLAIMANTS_KEY, {}).get((implementation_id, episode.episode_id, path))


def _target(graph: ChangeGraph, change_id: str):
    target = next((item for item in graph.targets if item.change_id == change_id), None)
    if target is None:
        raise ValueError(f"task target is absent from graph: {change_id}")
    return target


def _reviewed_artifact(
    task: InvestigationTask, episode: ReviewEpisodeInput, graph: ChangeGraph
) -> OpportunityEvidenceArtifact:
    target = _target(graph, task.primary_change_id)
    return evidence_artifact(
        task,
        "reviewed_code",
        f"reviewed-change:{target.change_id}",
        target.reviewed_code or target.base_code or "",
        episode.reviewed_head_sha,
    )


def _unavailable(
    task: InvestigationTask, operator: str, reason: str
) -> RunnerOutcome:
    run = _operator_run(task, operator, "unavailable", [], 0, failure_reason=reason)
    return RunnerOutcome(
        operator_runs=[run],
        disposition="needs_followup",
        basis=reason,
    )


def _canonical_runner(
    task: InvestigationTask,
    graph: ChangeGraph,
    episode: ReviewEpisodeInput,
    workspace: Path,
    cache: Dict,
) -> RunnerOutcome:
    if not workspace.is_dir():
        return _unavailable(task, "dependency_neighborhood", f"workspace missing: {workspace}")
    target = _target(graph, task.primary_change_id)
    key = ("declaration_index", episode.base_sha, target.path)
    declarations = cache.get(key)
    if declarations is None:
        declarations = build_declaration_index(workspace, episode.base_sha, target.path)
        cache[key] = declarations
    hits = rank_declarations(task, target, declarations)
    reviewed = _reviewed_artifact(task, episode, graph)
    trace = evidence_artifact(
        task,
        "retrieval_trace",
        f"canonical-retrieval:{task.primary_change_id}",
        "\n".join(
            f"rank={hit.rank} declaration={hit.declaration_id} score={hit.score:g} "
            f"already_used={str(hit.already_used).lower()}"
            for hit in hits[:10]
        ) or "No dependency-neighborhood declarations matched the query.",
        episode.base_sha,
    )
    runs = [
        _operator_run(task, "dependency_neighborhood", "completed", [], len(declarations)),
        _operator_run(
            task,
            "type_shape_retrieval",
            "completed",
            [trace.artifact_id],
            len(hits),
            hits[0].query_sha256 if hits else None,
        ),
    ]
    if not hits:
        return RunnerOutcome(runs, [reviewed, trace], [], "checked_no_opportunity",
                             "No canonical declaration was retrieved for the supported shape.")
    declarations_by_id = {item.declaration_id: item for item in declarations}
    top = hits[0]
    declaration = declarations_by_id[top.declaration_id]
    declaration_artifact = evidence_artifact(
        task,
        "repository_declaration",
        f"{episode.base_sha}:{declaration.path}:{declaration.line_start}",
        declaration.signature,
        episode.base_sha,
    )
    proposal = (
        propose_insert_separation_replacement(target.reviewed_code or target.base_code or "", declaration)
        if is_high_confidence_insert_separation(top, declaration) else None
    )
    applicability = check_applicability(workspace, episode, target, proposal)
    applicability_artifact = evidence_artifact(
        task,
        "applicability_check" if proposal else "negative_control",
        f"canonical-applicability:{task.investigation_id}",
        applicability.content + (
            "\nProposed replacement:\n" + applicability.replacement.new_block
            if applicability.replacement else ""
        ),
        episode.reviewed_head_sha,
    )
    runs.append(_operator_run(
        task,
        "applicability_check",
        "completed" if applicability.status in {"compiled", "failed"} or not proposal else "unavailable",
        [applicability_artifact.artifact_id],
        int(applicability.status == "compiled"),
        failure_reason=(
            None if applicability.status in {"compiled", "failed"} or not proposal
            else applicability.content
        ),
    ))
    evidence = [reviewed, trace, declaration_artifact, applicability_artifact]
    if proposal is None:
        return RunnerOutcome(runs, evidence, [], "checked_no_opportunity",
                             "Retrieved declarations did not meet the frozen canonical opportunity rule.")
    transformation = OpportunityTransformation(
        kind="replace_reconstructed_operation",
        symbols=[declaration.fullname],
        description=proposal.description,
    )
    opportunity = _opportunity(
        task,
        f"`{target.declaration_name or task.primary_change_id}` manually reconstructs an "
        f"inserted-set separation proof. `{declaration.fullname}` is the top "
        f"dependency-neighborhood retrieval (score {top.score:g}) and is not used by the target.",
        [item.artifact_id for item in evidence],
        transformation,
        min(top.score / 40.0, 1.0),
    )
    return RunnerOutcome(runs, evidence, [opportunity], "opportunities",
                         "A source-derived canonical replacement was constructed.")


def _naming_runner(
    task: InvestigationTask,
    graph: ChangeGraph,
    episode: ReviewEpisodeInput,
    workspace: Path,
    cache: Dict,
) -> RunnerOutcome:
    if not workspace.is_dir():
        return _unavailable(task, "scoped_naming_statistics", f"workspace missing: {workspace}")
    target = _target(graph, task.primary_change_id)
    key = ("naming_population", episode.base_sha)
    scan = cache.get(key)
    if scan is None:
        scan = scan_repository_population(workspace, episode.base_sha)
        cache[key] = scan
    inference = infer_semantic_subject(task, target)
    counts = population_counts(scan.members)
    strong_norm = strong_subject_prefix_norm(scan.members)
    current_name = target.declaration_name or ""
    proposed = proposed_subject_name(current_name, inference) if strong_norm else None
    pr_fullnames = [item.declaration_name for item in graph.targets if item.declaration_name]
    collision = check_name_collision(
        task, current_name, proposed, episode.base_sha, scan.all_fullnames, pr_fullnames
    )
    reviewed = _reviewed_artifact(task, episode, graph)
    subject = evidence_artifact(
        task, "semantic_subject", f"semantic-subject:{inference.inference_id}",
        f"subject={inference.subject}; role={inference.subject_role}; "
        f"confidence={inference.confidence}; conclusion={inference.conclusion}",
        episode.reviewed_head_sha,
    )
    population = evidence_artifact(
        task, "naming_population", f"naming-population:{POPULATION_VERSION}:{episode.base_sha}",
        json.dumps({"counts": counts, "strong_norm": strong_norm, "members": len(scan.members)}, sort_keys=True),
        episode.base_sha,
    )
    collision_artifact = evidence_artifact(
        task, "name_collision" if proposed else "negative_control", f"name-collision:{collision.collision_id}",
        f"current={current_name}; proposed={proposed}; collision={collision.collision}", episode.base_sha,
    )
    evidence = [reviewed, subject, population, collision_artifact]
    runs = [
        _operator_run(task, "semantic_subject_inference", "completed", [subject.artifact_id], 1),
        _operator_run(task, "scoped_naming_statistics", "completed", [population.artifact_id], len(scan.members)),
        _operator_run(task, "name_collision_check", "completed", [collision_artifact.artifact_id], 1),
    ]
    if not proposed or collision.collision:
        return RunnerOutcome(runs, evidence, [], "checked_no_opportunity",
                             "No collision-free rename passed the frozen naming norm rule.")
    transformation = OpportunityTransformation(
        kind="rename_to_semantic_subject_prefix",
        symbols=[current_name, proposed],
        description=(
            f"Rename `{current_name}` to `{proposed}` and update all references in the PR "
            f"so the declaration's direct `{inference.subject}` subject is reflected in its "
            "leaf name."
        ),
    )
    # The observed pattern must carry the population evidence, not just assert the
    # conclusion: it is rendered into the adjudication prompt, and a bare assertion asks
    # the model to take the norm on faith.
    conflicting = counts["conflicting_prefix"]
    opportunity = _opportunity(
        task,
        f"`{current_name}` has direct left-hand subject `{inference.subject}` but uses the "
        f"conflicting `card_` prefix. The scoped review-base population has "
        f"{counts['subject_prefix']}/{len(scan.members)} direct-subject declarations with an "
        f"`encard_` leaf prefix and "
        + ("no `card_` examples." if not conflicting else f"{conflicting} `card_` examples."),
        [item.artifact_id for item in evidence], transformation,
        counts["subject_prefix"] / max(len(scan.members), 1),
    )
    return RunnerOutcome(runs, evidence, [opportunity], "opportunities",
                         "A scoped naming norm and collision-free rename were established.")


def _wrapper_runner(
    task: InvestigationTask,
    graph: ChangeGraph,
    episode: ReviewEpisodeInput,
    workspace: Path,
    cache: Dict,
) -> RunnerOutcome:
    if not workspace.is_dir():
        return _unavailable(task, "pr_composition_search", f"workspace missing: {workspace}")
    discovery = discover_wrapper_composition(task, graph, episode, workspace)
    reviewed = _reviewed_artifact(task, episode, graph)
    sources = evidence_artifact(
        task,
        "repository_declaration" if discovery.plan.status == "composed" else "negative_control",
        f"composition-sources:{task.investigation_id}",
        "\n".join(f"{item.role}: {item.declaration_name}\n{item.signature}" for item in discovery.sources)
        or "No compatible source chain was found.",
        episode.base_sha,
    )
    plan = evidence_artifact(
        task, "composition_plan", discovery.plan.plan_id,
        discovery.plan.replacement_declaration or "No composition plan was produced.",
        episode.reviewed_head_sha,
    )
    applicability = evidence_artifact(
        task,
        "applicability_check" if discovery.plan.status == "composed" else "negative_control",
        f"wrapper-applicability:{task.investigation_id}",
        discovery.applicability.content,
        episode.reviewed_head_sha,
    )
    evidence = [reviewed, sources, plan, applicability]
    runs = [
        _operator_run(task, "pr_composition_search", "completed", [sources.artifact_id, plan.artifact_id],
                      int(discovery.plan.status == "composed")),
        _operator_run(
            task, "compile_composed_edit",
            "completed" if discovery.applicability.status in {"compiled", "failed"} else "unavailable",
            [applicability.artifact_id], int(discovery.applicability.status == "compiled"),
            failure_reason=(
                None if discovery.applicability.status in {"compiled", "failed"}
                else discovery.applicability.content
            ),
        ),
    ]
    if discovery.plan.status != "composed":
        return RunnerOutcome(runs, evidence, [], "checked_no_opportunity",
                             "No repository wrapper and witness chain satisfied the frozen rule.")
    # Name the witness roles the composition actually used; "wrapper and witnesses" alone
    # gives the adjudicator nothing to check the claim against.
    witness_roles = [
        item.role for item in discovery.sources if item.source_kind == "changed_declaration"
    ]
    wrapper_names = [
        item.declaration_name for item in discovery.sources
        if item.source_kind == "repository_declaration"
    ]
    roles_phrase = ", ".join(role.replace("_", " ") for role in witness_roles) or "current-PR"
    transformation = OpportunityTransformation(
        kind="compose_wrapper_with_witnesses",
        symbols=[item.declaration_name for item in discovery.sources],
        description=(
            "Replace the reconstructed implementation proof with the generated composition "
            f"of the repository wrapper and current-PR {roles_phrase} witnesses."
        ),
    )
    opportunity = _opportunity(
        task,
        "The target reconstructs its conclusion through low-level reasoning even though the "
        f"repository wrapper {' and '.join(f'`{name}`' for name in wrapper_names) or '(none)'} "
        f"composes with {len(witness_roles)} current-PR witnesses ({roles_phrase}).",
        [item.artifact_id for item in evidence], transformation, 1.0,
    )
    return RunnerOutcome(runs, evidence, [opportunity], "opportunities",
                         "A concrete wrapper-composition replacement was constructed.")


def _baseline_runner(
    task: InvestigationTask,
    graph: ChangeGraph,
    episode: ReviewEpisodeInput,
    workspace: Path,
    cache: Dict,
) -> RunnerOutcome:
    target = _target(graph, task.primary_change_id)
    if not workspace.is_dir():
        return _unavailable(task, "target_compile", f"workspace missing: {workspace}")
    diff_file = next((item for item in parse_unified_diff(episode.diff) if item.path == target.path), None)
    source_path = workspace / (diff_file.old_path if diff_file and diff_file.old_path else target.path)
    if diff_file is None or not source_path.is_file():
        return _unavailable(task, "target_compile", "reviewed file could not be reconstructed")
    cache_key = ("target_compile", episode.base_sha, target.path, episode.patch_sha256)
    result = cache.get(cache_key)
    if result is None:
        reviewed = apply_file_patch(source_path.read_text(encoding="utf-8"), diff_file)
        env = _tool_env(workspace)
        lake = shutil.which("lake", path=env.get("PATH"))
        if lake is None:
            return _unavailable(task, "target_compile", "lake is unavailable")
        with tempfile.NamedTemporaryFile(suffix=".lean", mode="w", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(reviewed)
        try:
            process = subprocess.run(
                [lake, "env", "lean", str(temporary)], cwd=workspace, env=env, text=True,
                capture_output=True, timeout=180,
            )
            diagnostics = (process.stdout + process.stderr).strip()
            # Lean reports diagnostics against the temporary file it was handed, whose name
            # is random. Left in, that name lands in the evidence content, so its hash — and
            # every opportunity ID derived from it — changes on every run, and the
            # "deterministic" arm stops being byte-reproducible. The compiled target is
            # identified by `source_ref`, so the path carries no information here.
            diagnostics = diagnostics.replace(str(temporary), COMPILED_TARGET)
            result = (process.returncode, diagnostics[-4000:])
        except (OSError, subprocess.TimeoutExpired) as exc:
            return _unavailable(task, "target_compile", f"compile could not complete: {exc}")
        finally:
            temporary.unlink(missing_ok=True)
        cache[cache_key] = result
    returncode, output = result
    compile_artifact = evidence_artifact(
        task, "applicability_check", f"target-compile:{target.path}",
        f"exit_code={returncode}\n{output}", episode.reviewed_head_sha,
    )
    run = _operator_run(task, "target_compile", "completed", [compile_artifact.artifact_id],
                        int(returncode != 0))
    if returncode == 0:
        return RunnerOutcome([run], [compile_artifact], [], "checked_no_opportunity",
                             "The reconstructed reviewed file compiles.")

    # The unit that failed is the *file*, not this declaration: one `lake env lean` run
    # compiled the whole reconstructed file. Emitting one opportunity per target in that
    # file restates a single failure once per declaration — at medium tier that turned 12
    # real failures into 128 findings, and told targets with no error in them that they
    # "fail to compile". Exactly one scheduled target carries the finding; the rest record
    # that they were checked.
    claimant = _file_claimant(cache, "baseline_failure.target_compile.v1", episode, target.path)
    if claimant is not None and claimant != task.investigation_id:
        return RunnerOutcome(
            [run], [compile_artifact], [], "checked_no_opportunity",
            f"`{target.path}` does not compile, but the failure is reported once for the "
            f"file rather than once per declaration in it.",
        )

    siblings = sorted(
        item.change_id for item in graph.targets
        if item.path == target.path and item.change_id != target.change_id
    )
    failing_lines = _error_lines(output)
    implicated = _targets_covering(graph, target.path, failing_lines)
    if implicated:
        located = (
            f" The diagnostics fall inside {len(implicated)} changed "
            f"declaration{'s' if len(implicated) > 1 else ''}: "
            + ", ".join(f"`{name}`" for name in implicated[:5])
            + ("…" if len(implicated) > 5 else "") + "."
        )
    elif failing_lines:
        located = (
            " None of the diagnostics fall inside the lines this PR changed, so the change "
            "breaks code elsewhere in the file."
        )
    else:
        located = ""
    lines_text = (
        f" at line{'s' if len(failing_lines) > 1 else ''} "
        + ", ".join(str(line) for line in failing_lines[:6])
        + ("…" if len(failing_lines) > 6 else "")
    ) if failing_lines else ""

    opportunity = _opportunity(
        task,
        f"The reconstructed reviewed file `{target.path}` fails to compile{lines_text}."
        f"{located}",
        [compile_artifact.artifact_id],
        OpportunityTransformation(
            kind="fix_target_compile",
            # Only real declaration names belong in `symbols`; kind labels are prose.
            symbols=[name for name in implicated if not name.startswith("<")],
            description=f"Repair the build failure in `{target.path}`.",
        ), 1.0,
        related_change_ids=siblings,
    )
    return RunnerOutcome([run], [compile_artifact], [opportunity], "opportunities",
                         f"`{target.path}` fails to compile at the reviewed head.")


def _lint_runner(
    task: InvestigationTask,
    graph: ChangeGraph,
    episode: ReviewEpisodeInput,
    workspace: Path,
    cache: Dict,
) -> RunnerOutcome:
    """Mathlib's text-based style lints over the target's reviewed source.

    No workspace is consulted: the rules are decidable from the reviewed text alone, which
    is why this runner is deterministic and free.
    """

    target = _target(graph, task.primary_change_id)
    reviewed = _reviewed_artifact(task, episode, graph)
    finding = lint_target(target)
    if finding is None:
        run = _operator_run(task, "text_style_lint", "completed", [reviewed.artifact_id], 0)
        return RunnerOutcome([run], [reviewed], [], "checked_no_opportunity",
                             "The reviewed source violates no Mathlib text-style lint.")
    report = evidence_artifact(
        task, "lint_report", f"text-style-lint:{LINT_VERSION}:{target.change_id}",
        json.dumps(
            {
                "lint_version": LINT_VERSION,
                "codes": finding.codes,
                "hits": [
                    {"code": hit.code, "line": hit.line_number, "message": hit.message}
                    for hit in finding.hits
                ],
            },
            sort_keys=True,
        ),
        episode.reviewed_head_sha,
    )
    run = _operator_run(task, "text_style_lint", "completed",
                        [reviewed.artifact_id, report.artifact_id], len(finding.hits))
    opportunity = _opportunity(
        task, finding.observed_pattern(), [reviewed.artifact_id, report.artifact_id],
        OpportunityTransformation(
            kind="reformat_source",
            symbols=finding.codes,
            description=finding.requested_change(),
        ), 1.0,
    )
    return RunnerOutcome([run], [reviewed, report], [opportunity], "opportunities",
                         "Reviewed lines violate Mathlib's published text-style lints.")


def _policy_runner(
    task: InvestigationTask,
    graph: ChangeGraph,
    episode: ReviewEpisodeInput,
    workspace: Path,
    cache: Dict,
) -> RunnerOutcome:
    """Forbidden constructs (`axiom`, `sorry`) newly introduced by the PR."""

    target = _target(graph, task.primary_change_id)
    reviewed = _reviewed_artifact(task, episode, graph)
    finding = find_forbidden_construct(target)
    if finding is None:
        run = _operator_run(task, "forbidden_construct_check", "completed",
                            [reviewed.artifact_id], 0)
        return RunnerOutcome([run], [reviewed], [], "checked_no_opportunity",
                             "The reviewed target introduces no forbidden construct.")
    report = evidence_artifact(
        task, "policy_report", f"forbidden-construct:{POLICY_VERSION}:{target.change_id}",
        f"construct={finding.construct}; declaration={finding.declaration_name}; "
        f"path={finding.path}",
        episode.reviewed_head_sha,
    )
    run = _operator_run(task, "forbidden_construct_check", "completed",
                        [reviewed.artifact_id, report.artifact_id], 1)
    opportunity = _opportunity(
        task, finding.observed_pattern(), [reviewed.artifact_id, report.artifact_id],
        OpportunityTransformation(
            kind="remove_declaration",
            symbols=[finding.declaration_name] if finding.declaration_name else [],
            description=finding.requested_change(),
        ), 1.0,
    )
    return RunnerOutcome([run], [reviewed, report], [opportunity], "opportunities",
                         f"The PR introduces a `{finding.construct}`.")


def _naming_norm_runner(
    task: InvestigationTask,
    graph: ChangeGraph,
    episode: ReviewEpisodeInput,
    workspace: Path,
    cache: Dict,
) -> RunnerOutcome:
    """Subject-general naming norm: mine the convention for *this* target's subject.

    The population scan is the expensive step and is snapshot-keyed, so it is cached per
    base SHA and shared across every target in the PR.
    """

    if not workspace.is_dir():
        return _unavailable(task, "snapshot_population_scan", f"workspace missing: {workspace}")
    target = _target(graph, task.primary_change_id)
    code = target.reviewed_code or target.base_code or ""
    declarations = parse_major_declarations(code) if code else []
    if not declarations:
        return _unavailable(task, "conclusion_subject_inference", "no parsed declaration")
    declaration = declarations[0]
    current_fullname = declaration.fullname or declaration.name or ""
    subject = conclusion_subject(declaration_conclusion(declaration.signature or ""))

    key = ("naming_norm_population", episode.base_sha)
    scan = cache.get(key)
    if scan is None:
        scan = scan_population(workspace, episode.base_sha)
        cache[key] = scan

    population = scan.population(subject.token) if subject.token else None
    proposal = propose_rename(current_fullname, subject, population)

    reviewed = _reviewed_artifact(task, episode, graph)
    subject_artifact = evidence_artifact(
        task, "semantic_subject", f"conclusion-subject:{NORM_CLASSIFIER_VERSION}:{target.change_id}",
        f"subject={subject.token}; kind={subject.kind}; confidence={subject.confidence}",
        episode.reviewed_head_sha,
    )
    population_artifact = evidence_artifact(
        task, "naming_population",
        f"subject-population:{NORM_POPULATION_VERSION}:{episode.base_sha}:{subject.token}",
        json.dumps(
            {
                "subject": subject.token,
                "members": population.members if population else 0,
                "counts": dict(population.prefix_counts) if population else {},
                "is_strong": bool(population and population.is_strong()),
                "parsed_files": scan.parsed_files,
            },
            sort_keys=True,
        ),
        episode.base_sha,
    )
    runs = [
        _operator_run(task, "conclusion_subject_inference", "completed",
                      [subject_artifact.artifact_id], 1),
        _operator_run(task, "snapshot_population_scan", "completed",
                      [population_artifact.artifact_id],
                      population.members if population else 0),
    ]
    evidence = [reviewed, subject_artifact, population_artifact]

    if proposal is None:
        runs.append(_operator_run(
            task, "name_collision_check", "unavailable", [], 0,
            failure_reason="no rename was proposed, so there is no name to check",
        ))
        return RunnerOutcome(
            runs, evidence, [], "checked_no_opportunity",
            "The snapshot shows no strong prefix norm this declaration violates.",
        )

    collision = check_name_collision(
        task, current_fullname, proposal.proposed_fullname, episode.base_sha,
        scan.all_fullnames, [item.declaration_name for item in graph.targets if item.declaration_name],
    )
    collision_artifact = evidence_artifact(
        task, "name_collision", f"name-collision:{collision.collision_id}",
        f"current={current_fullname}; proposed={proposal.proposed_fullname}; "
        f"collision={collision.collision}",
        episode.base_sha,
    )
    evidence.append(collision_artifact)
    runs.append(_operator_run(task, "name_collision_check", "completed",
                              [collision_artifact.artifact_id], 1))
    if collision.collision:
        return RunnerOutcome(runs, evidence, [], "checked_no_opportunity",
                             "The conventional name is already taken.")
    opportunity = _opportunity(
        task, proposal.observed_pattern(),
        [artifact.artifact_id for artifact in evidence],
        OpportunityTransformation(
            kind="rename_declaration",
            symbols=[current_fullname, proposal.proposed_fullname],
            description=f"Rename `{current_fullname}` to `{proposal.proposed_fullname}` to "
                        f"follow the established `{proposal.conventional_prefix}_` prefix for "
                        f"subject `{proposal.subject_token}`.",
        ), 1.0,
    )
    return RunnerOutcome(runs, evidence, [opportunity], "opportunities",
                         "The declaration's name conflicts with a measured subject prefix norm.")


DEFAULT_RUNNERS: Mapping[str, Runner] = {
    "baseline_failure.target_compile.v1": _baseline_runner,
    "canonical_api.insert_separation.v1": _canonical_runner,
    "naming_contrast.encard_subject_prefix.v1": _naming_runner,
    "wrapper_composition.packing_cover_chain.v1": _wrapper_runner,
    "naming_norm.subject_prefix.v1": _naming_norm_runner,
    "lint_norm.text_style.v1": _lint_runner,
    "repository_policy.forbidden_construct.v1": _policy_runner,
}


def execute_treatment(
    tasks: Iterable[InvestigationTask],
    graphs: Iterable[ChangeGraph],
    episodes: Iterable[ReviewEpisodeInput],
    assessments: Iterable[CapabilityAssessment],
    workspaces: Path,
    runners: Mapping[str, Runner] = DEFAULT_RUNNERS,
    implementation_limits: Optional[Mapping[str, int]] = None,
) -> Dict[str, List]:
    """Execute every scheduled task to a terminal state without gold access."""

    # Every argument is consumed more than once below, so materialise up front: a generator
    # would silently be empty on its second use.
    tasks = list(tasks)
    assessments = list(assessments)
    graph_by_episode = {item.episode_id: item for item in graphs}
    episode_by_id = {item.episode_id: item for item in episodes}
    assessments_by_task: Dict[str, List[CapabilityAssessment]] = {}
    for assessment in assessments:
        assessments_by_task.setdefault(assessment.investigation_id, []).append(assessment)
    cache: Dict = {
        _CLAIMANTS_KEY: file_claimants(tasks, assessments, graph_by_episode.values()),
    }
    output = {"evidence": [], "operator_runs": [], "opportunities": [], "records": [], "ledger": []}
    for task in sorted(tasks, key=lambda item: (item.pr_number, item.investigation_id)):
        task_assessments = sorted(
            assessments_by_task.get(task.investigation_id, []), key=lambda item: item.implementation_id
        )
        graph = graph_by_episode.get(task.episode_id)
        episode = episode_by_id.get(task.episode_id)
        if graph is None or episode is None:
            outcome = _unavailable(task, "executor_context", "episode or change graph is unavailable")
            outcome.execution_status = "failed"
            terminal_stage = "execution_failed"
            terminal_reason = outcome.basis
        else:
            supported = [item for item in task_assessments if item.status == "supported"]
            if not supported:
                statuses = sorted({item.status for item in task_assessments})
                reason = "no supported implementation: " + ",".join(statuses or ["missing_assessment"])
                outcome = RunnerOutcome(disposition="not_applicable", basis=reason)
                terminal_stage = "capability_assessed"
                terminal_reason = reason
            else:
                all_runs: List[OperatorRun] = []
                all_evidence: List[OpportunityEvidenceArtifact] = []
                all_opportunities: List[ReviewOpportunity] = []
                failures = []
                unavailable = []
                for assessment in supported:
                    runner = runners.get(assessment.implementation_id)
                    if runner is None:
                        partial = _unavailable(
                            task, "implementation_dispatch",
                            f"no runner registered for {assessment.implementation_id}",
                        )
                    else:
                        try:
                            partial = runner(task, graph, episode, workspaces / episode.base_sha, cache)
                        except Exception as exc:  # noqa: BLE001 - preserve task-local failure
                            partial = _unavailable(
                                task, "implementation_dispatch",
                                f"runner_exception:{type(exc).__name__}",
                            )
                            partial.execution_status = "failed"
                    limit = (implementation_limits or {}).get(assessment.implementation_id)
                    if limit is not None and len(partial.opportunities) > limit:
                        partial.opportunities = partial.opportunities[:limit]
                        partial.basis += f" Opportunity output was bounded to {limit}."
                    all_runs.extend(partial.operator_runs)
                    all_evidence.extend(partial.evidence)
                    all_opportunities.extend(partial.opportunities)
                    if partial.execution_status == "failed":
                        failures.append(partial.basis)
                    if partial.disposition == "needs_followup":
                        unavailable.append(partial.basis)
                if failures and not all_opportunities:
                    outcome = RunnerOutcome(
                        all_runs, all_evidence, [], "inconclusive", "; ".join(failures), "failed"
                    )
                    terminal_stage = "execution_failed"
                    terminal_reason = outcome.basis
                elif all_opportunities:
                    outcome = RunnerOutcome(
                        all_runs, all_evidence, all_opportunities, "opportunities",
                        "At least one supported implementation produced a deterministic opportunity.",
                    )
                    terminal_stage = "transformation_constructed"
                    terminal_reason = "opportunity_emitted"
                elif unavailable:
                    outcome = RunnerOutcome(
                        all_runs, all_evidence, [], "needs_followup", "; ".join(unavailable)
                    )
                    terminal_stage = "operator_unavailable"
                    terminal_reason = outcome.basis
                else:
                    outcome = RunnerOutcome(
                        all_runs, all_evidence, [], "checked_no_opportunity",
                        "Supported implementations completed without a deterministic opportunity.",
                    )
                    terminal_stage = "operator_completed"
                    terminal_reason = "checked_no_opportunity"
        record = _record(task, outcome)
        output["evidence"].extend(outcome.evidence)
        output["operator_runs"].extend(outcome.operator_runs)
        output["opportunities"].extend(outcome.opportunities)
        output["records"].append(record)
        output["ledger"].append({
            "schema_version": "opportunity-executor-ledger1",
            "investigation_id": task.investigation_id,
            "pr_number": task.pr_number,
            "scheduled": True,
            "capability_assessed": bool(task_assessments),
            "operator_completed": bool(outcome.operator_runs),
            "source_discovered": bool(outcome.evidence),
            "transformation_constructed": bool(outcome.opportunities),
            "technical_check_completed": any(
                item.operator in {"target_compile", "applicability_check", "compile_composed_edit"}
                and item.status == "completed" for item in outcome.operator_runs
            ),
            "worthiness_decided": False,
            "candidate_emitted": False,
            "finding_selected": False,
            "terminal_stage": terminal_stage,
            "terminal_reason": terminal_reason,
            "record_id": record.source_sha256,
        })
    if len(output["records"]) != len(tasks):
        raise ValueError("every scheduled task requires exactly one terminal record")
    return output


def execute_release(
    release: Path,
    treatment: Path,
    out: Path,
    workspaces: Path,
    investigation_ids: Optional[Iterable[str]] = None,
) -> Dict:
    tasks = load_jsonl(treatment / "derived/investigation_tasks.jsonl", InvestigationTask)
    assessments = load_jsonl(treatment / "derived/capability_assessments.jsonl", CapabilityAssessment)
    implementations = load_implementations(treatment / "implementations.jsonl")
    selected = set(investigation_ids or [])
    if selected:
        tasks = [item for item in tasks if item.investigation_id in selected]
        assessments = [item for item in assessments if item.investigation_id in selected]
        missing = selected - {item.investigation_id for item in tasks}
        if missing:
            raise ValueError(f"unknown investigation IDs: {sorted(missing)}")
    graphs = load_jsonl(release / "derived/change_graphs.jsonl", ChangeGraph)
    episodes = load_jsonl(release / "input/episodes.jsonl", ReviewEpisodeInput)
    rows = execute_treatment(
        tasks,
        graphs,
        episodes,
        assessments,
        workspaces,
        implementation_limits={item.implementation_id: item.max_opportunities for item in implementations},
    )
    for name, values, schema in (
        ("opportunity_evidence", rows["evidence"], "opportunity-evidence-artifact1"),
        ("operator_runs", rows["operator_runs"], "operator-run1"),
        ("investigation_records", rows["records"], "investigation-record1"),
        ("opportunities", rows["opportunities"], "review-opportunity1"),
        ("pipeline_ledger", rows["ledger"], "opportunity-executor-ledger1"),
    ):
        write_once(out / f"{name}.jsonl", jsonl_bytes(values))
    report = {
        "schema_version": "generic-opportunity-executor-report1",
        "executor_version": EXECUTOR_VERSION,
        "tasks": len(tasks),
        "records": len(rows["records"]),
        "operator_runs": len(rows["operator_runs"]),
        "opportunities": len(rows["opportunities"]),
        "terminal_stages": {
            key: sum(item["terminal_stage"] == key for item in rows["ledger"])
            for key in sorted({item["terminal_stage"] for item in rows["ledger"]})
        },
    }
    write_once(out / "report.json", pretty_json_bytes(report))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the generic deterministic opportunity executor")
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--treatment", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--workspaces", type=Path, default=DEFAULT_WORKSPACES)
    parser.add_argument("--investigation-id", action="append", default=[])
    args = parser.parse_args()
    print(json.dumps(
        execute_release(
            args.release,
            args.treatment,
            args.out,
            args.workspaces,
            args.investigation_id,
        ),
        indent=2,
    ))


if __name__ == "__main__":
    main()
