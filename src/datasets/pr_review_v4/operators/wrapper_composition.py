"""Deterministic wrapper and intra-PR composition discovery."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from ape.toolkits.code.lean.lean_parser import parse_major_declarations

from ..io import canonical_json_bytes, sha256_bytes
from ..operators.canonical_api import (
    ApplicabilityResult,
    ReplacementProposal,
    build_declaration_index,
    check_applicability,
)
from ..operators.naming_contrast import declaration_conclusion
from ..schema import (
    ChangeGraph,
    ChangeTarget,
    CompositionSource,
    InvestigationTask,
    RepositoryDeclaration,
    ReviewEpisodeInput,
    WrapperCompositionPlan,
)


COMPOSITION_VERSION = "wrapper-composition-search/1"
_IDENT_RE = re.compile(r"[A-Za-z][A-Za-z0-9_']*(?:\.[A-Za-z][A-Za-z0-9_']*)*")
_DEPENDENCY_STOP = {
    "by", "by_cases", "exact", "false", "have", "only", "refine", "rw", "simp",
    "theorem", "true",
}


@dataclass(frozen=True)
class CompositionDiscovery:
    sources: List[CompositionSource]
    plan: WrapperCompositionPlan
    applicability: ApplicabilityResult


def _parsed(target: ChangeTarget):
    declarations = parse_major_declarations(target.reviewed_code or target.base_code or "")
    return declarations[0] if declarations else None


def _signature(target: ChangeTarget) -> str:
    declaration = _parsed(target)
    return declaration.signature or "" if declaration else ""


def _proof(target: ChangeTarget) -> str:
    declaration = _parsed(target)
    return declaration.proof or "" if declaration else ""


def _dependencies(code: str) -> List[str]:
    values = []
    for token in _IDENT_RE.findall(code or ""):
        leaf = token.rsplit(".", 1)[-1]
        if len(leaf) < 4 or leaf in _DEPENDENCY_STOP or leaf.startswith("h_"):
            continue
        if leaf in {"packingNumber", "coveringNumber", "maximalSeparatedSet"}:
            continue
        values.append(token)
    return sorted(set(values))


def _source(
    task: InvestigationTask,
    role: str,
    source_kind: str,
    source_id: str,
    declaration_name: str,
    signature: str,
    source_ref: str,
    snapshot_sha: str,
) -> CompositionSource:
    payload = {
        "investigation_id": task.investigation_id,
        "role": role,
        "source_kind": source_kind,
        "source_id": source_id,
        "declaration_name": declaration_name,
        "signature": signature,
        "source_ref": source_ref,
        "snapshot_sha": snapshot_sha,
    }
    digest = sha256_bytes(canonical_json_bytes(payload))
    return CompositionSource(
        composition_source_id=f"composition-source:{digest[:24]}",
        source_sha256=digest,
        **payload,
    )


def _changed_source(
    task: InvestigationTask,
    target: ChangeTarget,
    role: str,
    snapshot_sha: str,
) -> CompositionSource:
    return _source(
        task,
        role,
        "changed_declaration",
        target.change_id,
        target.declaration_name or target.change_id,
        _signature(target),
        f"reviewed-change:{target.change_id}",
        snapshot_sha,
    )


def _repository_source(
    task: InvestigationTask,
    declaration: RepositoryDeclaration,
) -> CompositionSource:
    return _source(
        task,
        "repository_wrapper",
        "repository_declaration",
        declaration.declaration_id,
        declaration.fullname,
        declaration.signature,
        f"{declaration.snapshot_sha}:{declaration.path}:{declaration.line_start}",
        declaration.snapshot_sha,
    )


def _target_goal(target: ChangeTarget) -> str:
    return declaration_conclusion(_signature(target))


def _find_repository_wrapper(
    target: ChangeTarget,
    declarations: Iterable[RepositoryDeclaration],
) -> Optional[RepositoryDeclaration]:
    goal = _target_goal(target)
    if not all(token in goal for token in ("coveringNumber", "packingNumber", "≤")):
        return None
    candidates = [
        declaration
        for declaration in declarations
        if "coveringNumber" in declaration.signature
        and "encard" in declaration.signature
        and "IsCover" in declaration.signature
        and "≤" in declaration.signature
    ]
    return sorted(candidates, key=lambda item: (len(item.signature), item.fullname))[0] if candidates else None


def _changed_roles(
    task: InvestigationTask,
    graph: ChangeGraph,
) -> Dict[str, ChangeTarget]:
    related = {
        target.change_id: target
        for target in graph.targets
        if target.change_id in set(task.related_change_ids)
    }
    roles: Dict[str, ChangeTarget] = {}
    for target in related.values():
        conclusion = _target_goal(target)
        if (
            "encard" in conclusion
            and "packingNumber" in conclusion
            and "=" in conclusion
            and "maximalSeparatedSet" in conclusion
        ):
            roles.setdefault("cardinality_bridge", target)
        if "IsCover" in conclusion and "maximalSeparatedSet" in conclusion:
            roles.setdefault("cover_witness", target)
        if "⊆" in conclusion and "maximalSeparatedSet" in conclusion:
            roles.setdefault("subset_witness", target)
    return roles


def _parallel_source(
    task: InvestigationTask,
    graph: ChangeGraph,
    snapshot_sha: str,
) -> Optional[CompositionSource]:
    target_by_id = {target.change_id: target for target in graph.targets}
    for change_id in task.related_change_ids:
        target = target_by_id.get(change_id)
        if target and target.kind == "declaration" and target.declaration_name:
            return _changed_source(task, target, "parallel_sibling", snapshot_sha)
    return None


def _replacement(
    target: ChangeTarget,
    cardinality: ChangeTarget,
    cover: ChangeTarget,
    subset: ChangeTarget,
    wrapper: RepositoryDeclaration,
) -> str:
    target_code = target.reviewed_code or target.base_code or ""
    header = target_code.split(":= by", 1)[0].rstrip() + " := by\n"
    cardinality_name = (cardinality.declaration_name or "").rsplit(".", 1)[-1]
    cover_name = (cover.declaration_name or "").rsplit(".", 1)[-1]
    subset_name = (subset.declaration_name or "").rsplit(".", 1)[-1]
    wrapper_name = wrapper.fullname.rsplit(".", 1)[-1]
    return (
        header
        + "  by_cases h_top : packingNumber ε A ≠ ⊤\n"
        + f"  · rw [← {cardinality_name} h_top]\n"
        + f"    exact {cover_name} h_top |>.{wrapper_name} {subset_name}\n"
        + "  · simp only [ne_eq, Decidable.not_not] at h_top\n"
        + "    simp [h_top]\n"
    )


def _plan(
    task: InvestigationTask,
    target: ChangeTarget,
    sources: List[CompositionSource],
    replacement: Optional[str],
) -> WrapperCompositionPlan:
    old_dependencies = _dependencies(_proof(target))
    new_dependencies = _dependencies(replacement or "")
    removed = sorted(set(old_dependencies) - set(new_dependencies))
    repository_ids = [
        source.source_id for source in sources if source.source_kind == "repository_declaration"
    ]
    related_ids = sorted(
        source.source_id for source in sources if source.source_kind == "changed_declaration"
    )
    payload = {
        "investigation_id": task.investigation_id,
        "primary_change_id": task.primary_change_id,
        "target_goal": _target_goal(target),
        "status": "composed" if replacement else "no_composition",
        "composition_source_ids": [source.composition_source_id for source in sources],
        "related_change_ids": related_ids,
        "repository_declaration_ids": repository_ids,
        "replacement_declaration": replacement,
        "old_dependencies": old_dependencies,
        "new_dependencies": new_dependencies,
        "removed_dependencies": removed,
    }
    digest = sha256_bytes(canonical_json_bytes(payload))
    return WrapperCompositionPlan(
        plan_id=f"wrapper-plan:{digest[:24]}", source_sha256=digest, **payload
    )


def discover_wrapper_composition(
    task: InvestigationTask,
    graph: ChangeGraph,
    episode: ReviewEpisodeInput,
    workspace: Path,
) -> CompositionDiscovery:
    target = next(item for item in graph.targets if item.change_id == task.primary_change_id)
    declarations = build_declaration_index(workspace, episode.base_sha, target.path)
    wrapper = _find_repository_wrapper(target, declarations)
    roles = _changed_roles(task, graph)
    required = {"cardinality_bridge", "cover_witness", "subset_witness"}
    if wrapper is not None and required <= set(roles):
        sources = [
            _repository_source(task, wrapper),
            *[
                _changed_source(task, roles[role], role, episode.reviewed_head_sha)
                for role in ("cardinality_bridge", "cover_witness", "subset_witness")
            ],
        ]
        replacement = _replacement(
            target,
            roles["cardinality_bridge"],
            roles["cover_witness"],
            roles["subset_witness"],
            wrapper,
        )
        plan = _plan(task, target, sources, replacement)
        applicability = check_applicability(
            workspace,
            episode,
            target,
            ReplacementProposal(
                old_block=target.reviewed_code or target.base_code or "",
                new_block=replacement,
                description="Compose the repository cover wrapper with current-PR witnesses.",
            ),
        )
        return CompositionDiscovery(sources, plan, applicability)
    parallel = _parallel_source(task, graph, episode.reviewed_head_sha)
    sources = [parallel] if parallel else []
    plan = _plan(task, target, sources, None)
    applicability = ApplicabilityResult(
        status="unavailable",
        content=(
            "No repository wrapper plus changed-sibling chain matched the target goal; parallel "
            "proof shape alone does not establish a composition opportunity."
        ),
        replacement=None,
    )
    return CompositionDiscovery(sources, plan, applicability)
