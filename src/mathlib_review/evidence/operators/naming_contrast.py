"""Semantic-subject-conditioned naming contrast over a frozen Mathlib snapshot."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Set, Tuple

from ape.toolkits.code.lean.lean_parser import parse_major_declarations

from src.mathlib_review.io import canonical_json_bytes, sha256_bytes
from src.mathlib_review.schema import (
    ChangeTarget,
    InvestigationTask,
    NameCollisionResult,
    NamingPopulationMember,
    SemanticSubjectInference,
)


SUBJECT_CLASSIFIER_VERSION = "lean-conclusion-subject/1"
POPULATION_VERSION = "snapshot-direct-subject-names/1"
SUBJECT = "Set.encard"
SUBJECT_TOKEN = "encard"
MIN_SUPPORT = 20
MIN_SUPPORT_RATIO = 0.80
MAX_CONFLICT_RATIO = 0.05

_ENCARD_RE = re.compile(r"(?<![A-Za-z0-9_'])encard(?![A-Za-z0-9_'])")


@dataclass(frozen=True)
class NamingPopulationScan:
    members: List[NamingPopulationMember]
    all_fullnames: Set[str]
    parsed_files: int
    parse_failures: List[str]


def declaration_conclusion(signature: str) -> str:
    """Extract the top-level conclusion following a declaration's binder list."""

    depth = 0
    for index, character in enumerate(signature or ""):
        if character in "([{":
            depth += 1
        elif character in ")]}":
            depth = max(0, depth - 1)
        elif character == ":" and depth == 0 and signature[index:index + 2] != ":=":
            return signature[index + 1:].rsplit(":=", 1)[0].strip()
    return ""


def outer_lhs(conclusion: str) -> Optional[str]:
    """Return the left side of the outer relation, excluding quantified/role-led conclusions."""

    conclusion = (conclusion or "").strip()
    if not conclusion or conclusion.startswith(("∃", "∀")):
        return None
    depth = 0
    for index, character in enumerate(conclusion):
        if character in "([{":
            depth += 1
        elif character in ")]}":
            depth = max(0, depth - 1)
        elif depth == 0 and character in "=≤≥<>":
            if character == "=" and index + 1 < len(conclusion) and conclusion[index + 1] == ">":
                continue
            return conclusion[:index].strip()
    return None


def _subject_role(conclusion: str) -> Tuple[str, Optional[str], str]:
    left = outer_lhs(conclusion)
    if left and _ENCARD_RE.search(left):
        return "direct_lhs", left, "high"
    if _ENCARD_RE.search(conclusion):
        if conclusion.lstrip().startswith(("∃", "∀")):
            return "role_conditioned", None, "high"
        return "incidental", None, "medium"
    return "unknown", None, "low"


def infer_semantic_subject(
    task: InvestigationTask, target: ChangeTarget
) -> SemanticSubjectInference:
    code = target.reviewed_code or target.base_code or ""
    declarations = parse_major_declarations(code)
    if not declarations:
        conclusion = ""
        declaration_name = target.declaration_name or target.path
    else:
        declaration = declarations[0]
        conclusion = declaration_conclusion(declaration.signature or "")
        declaration_name = declaration.fullname or declaration.name or target.declaration_name or target.path
    role, expression, confidence = _subject_role(conclusion)
    payload = {
        "investigation_id": task.investigation_id,
        "primary_change_id": target.change_id,
        "declaration_name": declaration_name,
        "subject": SUBJECT if role != "unknown" else "unknown",
        "subject_role": role,
        "conclusion": conclusion,
        "subject_expression": expression,
        "confidence": confidence,
        "classifier_version": SUBJECT_CLASSIFIER_VERSION,
    }
    digest = sha256_bytes(canonical_json_bytes(payload))
    return SemanticSubjectInference(
        inference_id=f"semantic-subject:{digest[:24]}", source_sha256=digest, **payload
    )


def _line_number(source: str, offset: int) -> int:
    return source.count("\n", 0, offset) + 1


def _leaf_name(fullname: str) -> str:
    return fullname.rsplit(".", 1)[-1]


def _namespace(fullname: str) -> Optional[str]:
    return fullname.rsplit(".", 1)[0] if "." in fullname else None


def naming_form(leaf_name: str) -> str:
    lowered = leaf_name.lower()
    if lowered == SUBJECT_TOKEN or lowered.startswith(f"{SUBJECT_TOKEN}_"):
        return "subject_prefix"
    if lowered == "card" or lowered.startswith("card_"):
        return "conflicting_prefix"
    if SUBJECT_TOKEN in lowered:
        return "subject_elsewhere"
    return "role_specific_other"


def scan_repository_population(workspace: Path, snapshot_sha: str) -> NamingPopulationScan:
    mathlib = workspace / "Mathlib"
    if not mathlib.is_dir():
        raise FileNotFoundError(f"Mathlib source tree is unavailable: {mathlib}")
    members: List[NamingPopulationMember] = []
    all_fullnames: Set[str] = set()
    failures = []
    paths = sorted(mathlib.rglob("*.lean"))
    for path in paths:
        relative = path.relative_to(workspace).as_posix()
        try:
            source = path.read_text(encoding="utf-8")
            declarations = parse_major_declarations(source)
        except (OSError, UnicodeError, ValueError) as exc:
            failures.append(f"{relative}: {exc}")
            continue
        for declaration in declarations:
            name = declaration.name or ""
            fullname = declaration.fullname or name
            if fullname:
                all_fullnames.add(fullname)
            if declaration.kind not in {"lemma", "theorem"} or not fullname:
                continue
            conclusion = declaration_conclusion(declaration.signature or "")
            role, expression, _confidence = _subject_role(conclusion)
            if role != "direct_lhs" or expression is None:
                continue
            leaf = _leaf_name(fullname)
            payload = {
                "population_version": POPULATION_VERSION,
                "snapshot_sha": snapshot_sha,
                "path": relative,
                "line_start": _line_number(source, declaration.span[0]),
                "declaration_kind": declaration.kind,
                "fullname": fullname,
                "leaf_name": leaf,
                "namespace": _namespace(fullname),
                "subject": SUBJECT,
                "subject_role": "direct_lhs",
                "subject_expression": expression,
                "conclusion": conclusion,
                "naming_form": naming_form(leaf),
            }
            digest = sha256_bytes(canonical_json_bytes(payload))
            members.append(NamingPopulationMember(
                member_id=f"naming-member:{digest[:24]}",
                source_sha256=digest,
                **payload,
            ))
    members.sort(key=lambda item: (item.path, item.line_start, item.member_id))
    return NamingPopulationScan(
        members=members,
        all_fullnames=all_fullnames,
        parsed_files=len(paths),
        parse_failures=failures,
    )


def proposed_subject_name(current_fullname: str, inference: SemanticSubjectInference) -> Optional[str]:
    if inference.subject_role != "direct_lhs" or inference.confidence != "high":
        return None
    namespace = _namespace(current_fullname)
    leaf = _leaf_name(current_fullname)
    if not leaf.startswith("card_"):
        return None
    proposed_leaf = f"encard_{leaf.removeprefix('card_')}"
    return f"{namespace}.{proposed_leaf}" if namespace else proposed_leaf


def population_counts(members: Iterable[NamingPopulationMember]) -> dict:
    counts = {
        "subject_prefix": 0,
        "subject_elsewhere": 0,
        "conflicting_prefix": 0,
        "role_specific_other": 0,
    }
    for member in members:
        counts[member.naming_form] += 1
    return counts


def strong_subject_prefix_norm(members: Iterable[NamingPopulationMember]) -> bool:
    counts = population_counts(members)
    total = sum(counts.values())
    support = counts["subject_prefix"]
    conflicts = counts["conflicting_prefix"] + counts["role_specific_other"]
    return bool(
        total
        and support >= MIN_SUPPORT
        and support / total >= MIN_SUPPORT_RATIO
        and conflicts / total <= MAX_CONFLICT_RATIO
    )


def check_name_collision(
    task: InvestigationTask,
    current_fullname: str,
    proposed_fullname: Optional[str],
    snapshot_sha: str,
    repository_fullnames: Set[str],
    pr_fullnames: Iterable[str],
) -> NameCollisionResult:
    repository_matches = (
        [proposed_fullname] if proposed_fullname and proposed_fullname in repository_fullnames else []
    )
    pr_matches = sorted({
        name for name in pr_fullnames if proposed_fullname and name == proposed_fullname
        and name != current_fullname
    })
    payload = {
        "investigation_id": task.investigation_id,
        "primary_change_id": task.primary_change_id,
        "current_fullname": current_fullname,
        "proposed_fullname": proposed_fullname,
        "repository_matches": repository_matches,
        "pr_matches": pr_matches,
        "collision": bool(repository_matches or pr_matches),
        "snapshot_sha": snapshot_sha,
    }
    digest = sha256_bytes(canonical_json_bytes(payload))
    return NameCollisionResult(
        collision_id=f"name-collision:{digest[:24]}", source_sha256=digest, **payload
    )
