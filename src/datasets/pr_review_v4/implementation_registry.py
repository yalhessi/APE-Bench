"""Frozen implementation capabilities, method-expression contracts, and shape assessments.

Broad method IDs (method_registry.py) describe research strategies. The entries here describe
the exact target shapes the current executable operators can genuinely investigate, so a
scheduled task can never be mistaken for one the implementation could execute. Capability
assessment is deterministic, gold-free, and uses only release-carried generation artifacts.
Workspace-backed inputs (frozen base snapshots and their derived indexes) are treated as
available because every medium base snapshot is prebuilt; this assumption is recorded per
assessment in `required_input_status`.
"""

import argparse
import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from ape.toolkits.code.lean.lean_parser import parse_major_declarations

from .io import (
    canonical_json_bytes,
    jsonl_bytes,
    sealed_model,
    sha256_bytes,
    sha256_file,
    write_once,
)
from .operators.canonical_api import match_insert_separation_template
from .operators.lint_policy import (
    LINT_VERSION,
    POLICY_VERSION,
    find_forbidden_construct,
    lint_target,
)
from .operators.naming_contrast import (
    SUBJECT_CLASSIFIER_VERSION,
    declaration_conclusion,
    infer_semantic_subject,
    proposed_subject_name,
)
from .operators.naming_norm import (
    # Both naming operators export `SUBJECT_CLASSIFIER_VERSION`; alias to keep the
    # subject-general one distinguishable from the frozen `encard`-specific one.
    SUBJECT_CLASSIFIER_VERSION as NORM_CLASSIFIER_VERSION,
    conclusion_subject,
)
from .operators.wrapper_composition import COMPOSITION_VERSION, _changed_roles, _target_goal
from .schema import (
    CapabilityAssessment,
    ChangeGraph,
    ChangeTarget,
    ImplementationCapability,
    InvestigationTask,
    MethodExpressionContract,
)


IMPLEMENTATION_REGISTRY_VERSION = "implementation-capability-registry/3"
CONTRACTS_VERSION = "method-expression-contracts/3"
ASSESSOR_VERSION = "capability-assessor/1"

KNOWN_METHOD_IDS = {
    "baseline_failure.v1",
    "canonical_api_search.v1",
    "wrapper_composition.v1",
    "naming_contrast.v1",
    "naming_norm.v1",
    "lint_norm.v1",
    "repository_policy.v1",
}

ISSUE_CLASSES = {
    "broken_build",
    "policy_violation",
    "duplicate_implementation",
    "missed_canonical_api",
    "proof_simplification",
    "naming_convention_violation",
    "documentation_gap",
    "style_norm_violation",
    "scope_placement",
    "correctness_policy",
    "generalization_available",
}
TRANSFORMATION_CLASSES = {
    "fix_target_compile",
    "apply_repository_policy",
    "replace_with_repository_declaration",
    "compose_wrapper_with_witnesses",
    "rename_declaration",
    # Protocol v3: maintainer acts the original five terms could not express. Adding them
    # to the vocabulary lets the census *classify* such asks; it does not claim any method
    # covers them — that requires a contract, which is a separate, deliberate act.
    "rewrite_proof",
    "extract_shared_declaration",
    "edit_documentation",
    "reformat_source",
    "relocate_declaration",
    "remove_declaration",
}

TERMINAL_OUTPUTS = ["opportunity", "checked_no_opportunity", "unsupported_shape"]

# Prohibited in registry entries: benchmark PR numbers, gold obligation IDs, and gold-side
# vocabulary. Shape tokens (encard, IsSeparated, ...) are allowed: shape-specific logic is
# exactly what a versioned implementation capability exists to declare.
_FORBIDDEN_TOKEN_RE = re.compile(r"\b33\d{3}\b|obligation:|maintainer comment|post-review|gold")

_SNAPSHOT_BACKED_INPUTS = {
    "reviewed_workspace",
    "compile_diagnostics",
    "repository_declaration_index",
    "semantic_subject_index",
    "pr_relation_graph",
}


def default_implementations() -> List[ImplementationCapability]:
    """The current executable capabilities, with their narrow scope made explicit."""

    return [
        sealed_model(
            ImplementationCapability,
            implementation_id="baseline_failure.target_compile.v1",
            method_id="baseline_failure.v1",
            operator_version="target-local-compile/1",
            capability_predicate="lean_target_compile_shape.v1",
            required_inputs=["reviewed_workspace", "compile_diagnostics"],
            terminal_outputs=TERMINAL_OUTPUTS,
            max_opportunities=1,
        ),
        sealed_model(
            ImplementationCapability,
            implementation_id="canonical_api.insert_separation.v1",
            method_id="canonical_api_search.v1",
            operator_version="canonical-api-lexical-shape/1",
            capability_predicate="inserted_set_separation_shape.v1",
            required_inputs=["reviewed_declaration", "repository_declaration_index"],
            terminal_outputs=TERMINAL_OUTPUTS,
            max_opportunities=1,
        ),
        sealed_model(
            ImplementationCapability,
            implementation_id="wrapper_composition.packing_cover_chain.v1",
            method_id="wrapper_composition.v1",
            operator_version=COMPOSITION_VERSION,
            capability_predicate="packing_cover_chain_shape.v1",
            required_inputs=[
                "reviewed_declaration", "reviewed_workspace",
                "repository_declaration_index", "pr_relation_graph",
            ],
            terminal_outputs=TERMINAL_OUTPUTS,
            max_opportunities=1,
        ),
        sealed_model(
            ImplementationCapability,
            implementation_id="lint_norm.text_style.v1",
            method_id="lint_norm.v1",
            operator_version=LINT_VERSION,
            capability_predicate="text_style_lint_shape.v1",
            required_inputs=["reviewed_source"],
            terminal_outputs=TERMINAL_OUTPUTS,
            max_opportunities=1,
        ),
        sealed_model(
            ImplementationCapability,
            implementation_id="repository_policy.forbidden_construct.v1",
            method_id="repository_policy.v1",
            operator_version=POLICY_VERSION,
            capability_predicate="forbidden_construct_shape.v1",
            required_inputs=["reviewed_declaration"],
            terminal_outputs=TERMINAL_OUTPUTS,
            max_opportunities=5,
        ),
        sealed_model(
            ImplementationCapability,
            implementation_id="naming_contrast.encard_subject_prefix.v1",
            method_id="naming_contrast.v1",
            operator_version=SUBJECT_CLASSIFIER_VERSION,
            capability_predicate="encard_subject_prefix_shape.v1",
            required_inputs=["reviewed_declaration", "semantic_subject_index"],
            terminal_outputs=TERMINAL_OUTPUTS,
            max_opportunities=1,
        ),
        sealed_model(
            ImplementationCapability,
            implementation_id="naming_norm.subject_prefix.v1",
            method_id="naming_norm.v1",
            operator_version=NORM_CLASSIFIER_VERSION,
            capability_predicate="subject_prefix_norm_shape.v1",
            required_inputs=["reviewed_declaration", "reviewed_workspace"],
            terminal_outputs=TERMINAL_OUTPUTS,
            max_opportunities=3,
        ),
    ]


def default_contracts() -> List[MethodExpressionContract]:
    """Frozen C1 mapping from broad methods to normalized issue/transformation classes."""

    return [
        sealed_model(
            MethodExpressionContract,
            method_id="baseline_failure.v1",
            issue_classes=["broken_build", "policy_violation"],
            transformation_classes=["fix_target_compile", "apply_repository_policy"],
        ),
        sealed_model(
            MethodExpressionContract,
            method_id="canonical_api_search.v1",
            issue_classes=[
                "duplicate_implementation", "missed_canonical_api", "proof_simplification",
            ],
            transformation_classes=["replace_with_repository_declaration"],
        ),
        sealed_model(
            MethodExpressionContract,
            method_id="wrapper_composition.v1",
            issue_classes=["proof_simplification", "duplicate_implementation"],
            transformation_classes=["compose_wrapper_with_witnesses"],
        ),
        sealed_model(
            MethodExpressionContract,
            method_id="naming_contrast.v1",
            issue_classes=["naming_convention_violation"],
            transformation_classes=["rename_declaration"],
        ),
        sealed_model(
            MethodExpressionContract,
            method_id="naming_norm.v1",
            issue_classes=["naming_convention_violation"],
            transformation_classes=["rename_declaration"],
        ),
        sealed_model(
            MethodExpressionContract,
            method_id="lint_norm.v1",
            issue_classes=["style_norm_violation"],
            transformation_classes=["reformat_source"],
        ),
        sealed_model(
            MethodExpressionContract,
            method_id="repository_policy.v1",
            issue_classes=["policy_violation", "correctness_policy"],
            transformation_classes=["remove_declaration", "apply_repository_policy"],
        ),
    ]


def _check_sealed(item, label: str) -> None:
    identity = item.model_dump(mode="json", exclude={"source_sha256"})
    expected = sha256_bytes(canonical_json_bytes(identity))
    if item.source_sha256 != expected:
        raise ValueError(f"{label} source hash mismatch: {item}")
    serialized = canonical_json_bytes(identity).decode("utf-8").lower()
    match = _FORBIDDEN_TOKEN_RE.search(serialized)
    if match:
        raise ValueError(f"{label} contains a target-specific or gold token: {match.group(0)}")


def validate_implementations(
    implementations: Iterable[ImplementationCapability],
) -> List[ImplementationCapability]:
    implementations = list(implementations)
    ids = [item.implementation_id for item in implementations]
    if len(ids) != len(set(ids)):
        raise ValueError("implementation registry contains duplicate IDs")
    for item in implementations:
        _check_sealed(item, "implementation capability")
        if item.method_id not in KNOWN_METHOD_IDS:
            raise ValueError(f"implementation references unknown method: {item.implementation_id}")
        if item.capability_predicate not in CAPABILITY_PREDICATES:
            raise ValueError(
                f"implementation references unknown predicate: {item.capability_predicate}"
            )
    return implementations


def validate_contracts(
    contracts: Iterable[MethodExpressionContract],
) -> List[MethodExpressionContract]:
    contracts = list(contracts)
    ids = [item.method_id for item in contracts]
    if len(ids) != len(set(ids)):
        raise ValueError("method-expression contracts contain duplicate method IDs")
    if set(ids) != KNOWN_METHOD_IDS:
        raise ValueError("method-expression contracts must cover the frozen method registry exactly")
    for item in contracts:
        _check_sealed(item, "method-expression contract")
        unknown_issues = set(item.issue_classes) - ISSUE_CLASSES
        unknown_transformations = set(item.transformation_classes) - TRANSFORMATION_CLASSES
        if unknown_issues or unknown_transformations:
            raise ValueError(
                f"contract for {item.method_id} uses unknown classes: "
                f"issues={sorted(unknown_issues)} transformations={sorted(unknown_transformations)}"
            )
    return contracts


# --- Capability predicates -----------------------------------------------------------------
#
# Each predicate returns (status, reason_code). Predicates are pure functions of the scheduled
# task and release-carried change-graph content; they never touch gold, the network, or a
# workspace. `unsupported_shape` means this implementation does not handle the target shape at
# all; `not_applicable` means the shape family matched but a stricter precondition rejected it.


def _target_code(target: ChangeTarget) -> str:
    return target.reviewed_code or target.base_code or ""


def _lean_target_compile_shape(
    task: InvestigationTask, target: ChangeTarget, graph: ChangeGraph
) -> Tuple[str, str]:
    if not target.path.endswith(".lean"):
        return "unsupported_shape", "non_lean_target"
    if not (target.reviewed_code or target.diff_fragments):
        return "unsupported_shape", "no_reviewed_content"
    return "supported", "lean_target_with_reviewed_content"


def _inserted_set_separation_shape(
    task: InvestigationTask, target: ChangeTarget, graph: ChangeGraph
) -> Tuple[str, str]:
    code = _target_code(target)
    if not code:
        return "unsupported_shape", "no_target_code"
    if match_insert_separation_template(code) is None:
        return "unsupported_shape", "no_insert_separation_template"
    return "supported", "insert_separation_template_matched"


def _encard_subject_prefix_shape(
    task: InvestigationTask, target: ChangeTarget, graph: ChangeGraph
) -> Tuple[str, str]:
    code = _target_code(target)
    declarations = parse_major_declarations(code) if code else []
    if not declarations:
        return "unsupported_shape", "no_parsed_declaration"
    inference = infer_semantic_subject(task, target)
    if inference.subject_role != "direct_lhs" or inference.confidence != "high":
        return "unsupported_shape", f"subject_role_{inference.subject_role}"
    declaration = declarations[0]
    fullname = declaration.fullname or declaration.name or ""
    if proposed_subject_name(fullname, inference) is None:
        return "not_applicable", "encard_subject_without_card_prefix"
    return "supported", "direct_lhs_encard_with_card_prefix"


def _subject_prefix_norm_shape(
    task: InvestigationTask, target: ChangeTarget, graph: ChangeGraph
) -> Tuple[str, str]:
    """Subject-general naming: any conclusion with a resolvable direct left-hand subject.

    Unlike `encard_subject_prefix_shape.v1`, no subject token is hardcoded. Whether the
    corpus actually has a convention for *this* subject cannot be decided here — it needs
    the snapshot population scan — so the predicate reports the shape and the runner
    decides applicability. That split is deliberate: assessment must stay cheap and
    gold-free, and a subject with no strong norm yields `checked_no_opportunity`, not a
    false candidate.
    """

    code = _target_code(target)
    declarations = parse_major_declarations(code) if code else []
    if not declarations:
        return "unsupported_shape", "no_parsed_declaration"
    declaration = declarations[0]
    inference = conclusion_subject(declaration_conclusion(declaration.signature or ""))
    if inference.token is None or inference.confidence != "high":
        return "unsupported_shape", f"subject_kind_{inference.kind}"
    if not (declaration.fullname or declaration.name):
        return "unsupported_shape", "declaration_without_name"
    return "supported", f"direct_lhs_subject:{inference.kind}"


def _packing_cover_chain_shape(
    task: InvestigationTask, target: ChangeTarget, graph: ChangeGraph
) -> Tuple[str, str]:
    goal = _target_goal(target)
    if not all(token in goal for token in ("coveringNumber", "packingNumber", "≤")):
        return "unsupported_shape", "goal_not_covering_le_packing"
    roles = _changed_roles(task, graph)
    missing = sorted({"cardinality_bridge", "cover_witness", "subset_witness"} - set(roles))
    if missing:
        return "not_applicable", "missing_witness_roles:" + ",".join(missing)
    return "supported", "wrapper_chain_roles_present"


def _text_style_lint_shape(
    task: InvestigationTask, target: ChangeTarget, graph: ChangeGraph
) -> Tuple[str, str]:
    if not (target.reviewed_code or ""):
        return "unsupported_shape", "no_reviewed_content"
    finding = lint_target(target)
    if finding is None:
        return "unsupported_shape", "no_text_style_violation"
    return "supported", "violations:" + ",".join(finding.codes)


def _forbidden_construct_shape(
    task: InvestigationTask, target: ChangeTarget, graph: ChangeGraph
) -> Tuple[str, str]:
    if not (target.reviewed_code or ""):
        return "unsupported_shape", "no_reviewed_content"
    finding = find_forbidden_construct(target)
    if finding is None:
        return "unsupported_shape", "no_forbidden_construct_introduced"
    return "supported", f"introduces_{finding.construct}"


CAPABILITY_PREDICATES = {
    "text_style_lint_shape.v1": _text_style_lint_shape,
    "forbidden_construct_shape.v1": _forbidden_construct_shape,
    "lean_target_compile_shape.v1": _lean_target_compile_shape,
    "inserted_set_separation_shape.v1": _inserted_set_separation_shape,
    "encard_subject_prefix_shape.v1": _encard_subject_prefix_shape,
    "subject_prefix_norm_shape.v1": _subject_prefix_norm_shape,
    "packing_cover_chain_shape.v1": _packing_cover_chain_shape,
}


def _input_availability(
    implementation: ImplementationCapability, target: ChangeTarget
) -> Dict[str, str]:
    status = {}
    for name in implementation.required_inputs:
        if name == "reviewed_declaration":
            available = target.kind == "declaration" and bool(_target_code(target))
        elif name == "reviewed_source":
            available = bool(_target_code(target))
        elif name in _SNAPSHOT_BACKED_INPUTS:
            available = True
        else:
            available = False
        status[name] = "available" if available else "unavailable"
    return status


def assess_capabilities(
    tasks: Iterable[InvestigationTask],
    graphs: Iterable[ChangeGraph],
    implementations: Iterable[ImplementationCapability],
) -> List[CapabilityAssessment]:
    """Produce one deterministic assessment per (scheduled task, matching implementation)."""

    graphs = list(graphs)
    implementations = validate_implementations(implementations)
    graph_by_episode = {graph.episode_id: graph for graph in graphs}
    target_by_change: Dict[str, ChangeTarget] = {
        target.change_id: target for graph in graphs for target in graph.targets
    }
    by_method: Dict[str, List[ImplementationCapability]] = {}
    for implementation in implementations:
        by_method.setdefault(implementation.method_id, []).append(implementation)

    assessments = []
    for task in sorted(tasks, key=lambda item: (item.pr_number, item.investigation_id)):
        graph = graph_by_episode.get(task.episode_id)
        target = target_by_change.get(task.primary_change_id)
        for implementation in by_method.get(task.method_id, []):
            if graph is None or target is None:
                status, reason = "failed", "missing_change_graph_target"
                input_status = {}
            else:
                input_status = _input_availability(implementation, target)
                predicate = CAPABILITY_PREDICATES[implementation.capability_predicate]
                try:
                    status, reason = predicate(task, target, graph)
                except Exception as exc:  # noqa: BLE001 - recorded as an explicit terminal state
                    status, reason = "failed", f"predicate_exception:{type(exc).__name__}"
                if status == "supported" and "unavailable" in input_status.values():
                    unavailable = sorted(
                        name for name, value in input_status.items() if value == "unavailable"
                    )
                    status, reason = "missing_input", "unavailable_inputs:" + ",".join(unavailable)
            payload = {
                "assessor_version": ASSESSOR_VERSION,
                "implementation_id": implementation.implementation_id,
                "implementation_sha256": implementation.source_sha256,
                "investigation_id": task.investigation_id,
                "task_sha256": task.source_sha256,
                "method_id": task.method_id,
                "episode_id": task.episode_id,
                "pr_number": task.pr_number,
                "primary_change_id": task.primary_change_id,
                "status": status,
                "reason_code": reason,
                "required_input_status": input_status,
            }
            digest = sha256_bytes(canonical_json_bytes(payload))
            assessments.append(CapabilityAssessment(
                assessment_id=f"capability:{digest[:24]}",
                implementation_id=implementation.implementation_id,
                investigation_id=task.investigation_id,
                method_id=task.method_id,
                episode_id=task.episode_id,
                pr_number=task.pr_number,
                primary_change_id=task.primary_change_id,
                status=status,
                reason_code=reason,
                required_input_status=input_status,
                source_sha256=digest,
            ))
    return assessments


def build_registry_files(out: Path) -> Tuple[List[ImplementationCapability], List[MethodExpressionContract]]:
    implementations = validate_implementations(default_implementations())
    contracts = validate_contracts(default_contracts())
    write_once(out / "implementations.jsonl", jsonl_bytes(implementations))
    write_once(out / "method_expression_contracts.jsonl", jsonl_bytes(contracts))
    return implementations, contracts


def load_implementations(path: Path) -> List[ImplementationCapability]:
    return validate_implementations(
        ImplementationCapability.model_validate_json(line)
        for line in path.read_text().splitlines()
        if line.strip()
    )


def load_contracts(path: Path) -> List[MethodExpressionContract]:
    return validate_contracts(
        MethodExpressionContract.model_validate_json(line)
        for line in path.read_text().splitlines()
        if line.strip()
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build or validate the frozen v4 implementation registry and C1 contracts"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build")
    build.add_argument("--out", type=Path, required=True)
    validate = subparsers.add_parser("validate")
    validate.add_argument("--dir", type=Path, required=True)
    args = parser.parse_args()
    root = args.out if args.command == "build" else args.dir
    if args.command == "build":
        implementations, contracts = build_registry_files(root)
    else:
        implementations = load_implementations(root / "implementations.jsonl")
        contracts = load_contracts(root / "method_expression_contracts.jsonl")
    print(json.dumps({
        "registry_version": IMPLEMENTATION_REGISTRY_VERSION,
        "contracts_version": CONTRACTS_VERSION,
        "implementations": [item.implementation_id for item in implementations],
        "contracts": {item.method_id: item.issue_classes for item in contracts},
        "implementations_sha256": sha256_file(root / "implementations.jsonl"),
        "contracts_sha256": sha256_file(root / "method_expression_contracts.jsonl"),
    }, indent=2))


if __name__ == "__main__":
    main()
