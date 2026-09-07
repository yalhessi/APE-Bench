"""Build and validate the production investigation-method registry."""

import argparse
import json
from pathlib import Path
from typing import Iterable, List

from src.mathlib_review.io import (
    canonical_json_bytes,
    jsonl_bytes,
    sealed_model,
    sha256_bytes,
    sha256_file,
    write_once,
)
from src.mathlib_review.schema import InvestigationMethod, MethodApplicability


METHOD_REGISTRY_VERSION = "systematic-opportunity-methods/4"

#: Retired at `/4`: three operators that only ever fire on the PR they were written from.
#:
#: Measured on medium — every opportunity any of them produced was on **PR 33098**, the
#: development PR:
#:
#: * `wrapper_composition.v1` requires `coveringNumber` AND `packingNumber` AND `IsCover`
#:   AND `maximalSeparatedSet` in the goal.
#: * `naming_contrast.v1` hardcodes `SUBJECT = "Set.encard"`.
#: * `canonical_api_search.v1` likewise fires nowhere else.
#:
#: Keeping them made the deterministic arm look like it published verified findings across
#: ten PRs when three of its seven operators were memorised from one. They entered the merge
#: at `verified_compile`, the top tier, so they also won every tie and every per-PR budget
#: cut they took part in. `naming_norm.v1` is the counter-example that stays: it mines the
#: subject from the conclusion and fires on 33098 *and* 33145.
#:
#: The method records remain constructible so frozen runs that reference them still replay;
#: what changes is that they are no longer scheduled. Their *modules* deliberately stay in
#: `operators/` rather than moving to `legacy/`, because general helpers live inside them —
#: `canonical_api.evidence_artifact`, `naming_contrast.declaration_conclusion` and
#: `wrapper_composition._target_goal` are used by operators that survive.
RETIRED_SINGLE_PR_METHODS = (
    "canonical_api_search.v1",
    "wrapper_composition.v1",
    "naming_contrast.v1",
)

#: Stable execution order. Named once so the registry and its validator cannot drift.
EXECUTION_ORDER = [
    "baseline_failure.v1",
    "naming_norm.v1",
    "lint_norm.v1",
    "repository_policy.v1",
]

#: Every method ever defined, in their original order — the denominator for replaying a
#: frozen run that was scheduled against `/3`.
EXECUTION_ORDER_V3 = [
    "baseline_failure.v1",
    "canonical_api_search.v1",
    "wrapper_composition.v1",
    "naming_contrast.v1",
    "naming_norm.v1",
    "lint_norm.v1",
    "repository_policy.v1",
]

#: A new file, never an edit: the `/3` registry is a frozen artifact whose sha256 is bound
#: into every existing run plan and investigation record.
DEFAULT_REGISTRY = Path(
    "inputs/pr_review_v4/treatments/systematic-opportunities-v2/methods.jsonl"
)
LEGACY_REGISTRY_V3 = Path(
    "inputs/pr_review_v4/treatments/systematic-opportunities-v1/methods.jsonl"
)

KNOWN_INPUTS = {
    "reviewed_declaration",
    # Any target's reviewed source, including module docs, imports and sections. Lint-style
    # rules apply to content the PR touched regardless of whether it is a declaration.
    "reviewed_source",
    "reviewed_workspace",
    "compile_diagnostics",
    "repository_declaration_index",
    "pr_relation_graph",
    "semantic_subject_index",
}
KNOWN_OPERATORS = {
    "target_local_compile",
    "repository_policy_check",
    "type_shape_retrieval",
    "dependency_neighborhood",
    "applicability_check",
    "pr_composition_search",
    "compile_composed_edit",
    "semantic_subject_inference",
    "scoped_naming_statistics",
    "name_collision_check",
    "conclusion_subject_inference",
    "snapshot_population_scan",
    "text_style_lint",
    "forbidden_construct_scan",
}
KNOWN_CHECKS = {
    "target_local_compile",
    "lean_compile",
    "name_collision",
    "lint_rule",
}
KNOWN_NORM_SOURCES = {
    "explicit_policy",
    "canonical_api_status",
    "local_usage",
    "abstraction_dependency_reduction",
    "subject_conditioned_prevalence",
    "meaningful_counterexamples",
}
KNOWN_POLICIES = {
    "direct_failure.v1",
    "canonical_replacement.v1",
    "wrapper_composition.v1",
    "strong_naming_convention.v1",
    "lint_rule.v1",
    "repository_policy.v1",
}


def all_methods() -> List[InvestigationMethod]:
    """Every method ever defined, including the retired single-PR templates.

    Used to replay frozen runs scheduled against `/3`. Not what a new run schedules.
    """

    return _method_definitions()


def default_methods() -> List[InvestigationMethod]:
    """The methods a new run schedules: general rules only.

    `RETIRED_SINGLE_PR_METHODS` are excluded here rather than filtered by the caller. The
    previous arrangement listed them in a `SUBSUMED_METHODS` constant that `build_condition`
    never applied — `exclude_methods` defaulted to empty — so the exclusion everyone believed
    was in force simply was not.
    """

    return [
        item for item in _method_definitions()
        if item.method_id not in RETIRED_SINGLE_PR_METHODS
    ]


def _method_definitions() -> List[InvestigationMethod]:
    """Return the deliberately small first registry in stable execution order."""

    public_code = ["theorem", "definition", "instance", "structure_or_class", "inductive"]
    return [
        sealed_model(InvestigationMethod, 
            method_id="baseline_failure.v1",
            applies_when=MethodApplicability(
                subject_kinds=public_code + ["command", "import", "module_doc", "unknown"],
                lifecycles=["added", "modified", "renamed", "moved", "unknown"],
                any_changed_components=[
                    "name", "binders", "statement_or_type", "attributes", "proof",
                    "value_or_body", "documentation", "namespace", "imports", "unknown",
                ],
            ),
            required_inputs=["reviewed_workspace", "compile_diagnostics"],
            operators=["target_local_compile", "repository_policy_check"],
            max_opportunities=5,
            technical_checks=["target_local_compile"],
            norm_sources=["explicit_policy"],
            selection_policy="direct_failure.v1",
        ),
        sealed_model(InvestigationMethod, 
            method_id="canonical_api_search.v1",
            applies_when=MethodApplicability(
                subject_kinds=["theorem", "definition"],
                lifecycles=["added", "modified"],
                any_changed_components=["proof", "value_or_body"],
            ),
            required_inputs=["reviewed_declaration", "repository_declaration_index"],
            operators=["type_shape_retrieval", "dependency_neighborhood", "applicability_check"],
            max_opportunities=5,
            technical_checks=["lean_compile"],
            norm_sources=["canonical_api_status", "local_usage"],
            selection_policy="canonical_replacement.v1",
        ),
        sealed_model(InvestigationMethod, 
            method_id="wrapper_composition.v1",
            applies_when=MethodApplicability(
                subject_kinds=["theorem", "definition"],
                lifecycles=["added", "modified"],
                any_changed_components=["statement_or_type", "proof", "value_or_body"],
            ),
            required_inputs=[
                "reviewed_declaration", "reviewed_workspace", "repository_declaration_index",
                "pr_relation_graph",
            ],
            operators=["pr_composition_search", "applicability_check", "compile_composed_edit"],
            max_opportunities=5,
            technical_checks=["lean_compile"],
            norm_sources=["abstraction_dependency_reduction", "canonical_api_status"],
            selection_policy="wrapper_composition.v1",
        ),
        sealed_model(InvestigationMethod,
            method_id="naming_contrast.v1",
            applies_when=MethodApplicability(
                subject_kinds=public_code,
                lifecycles=["added", "renamed", "modified"],
                any_changed_components=["name", "statement_or_type", "value_or_body"],
                visibilities=["public"],
            ),
            required_inputs=["reviewed_declaration", "semantic_subject_index"],
            operators=[
                "semantic_subject_inference", "scoped_naming_statistics", "name_collision_check",
            ],
            max_opportunities=3,
            technical_checks=["name_collision"],
            norm_sources=["subject_conditioned_prevalence", "meaningful_counterexamples"],
            selection_policy="strong_naming_convention.v1",
        ),
        sealed_model(InvestigationMethod,
            method_id="naming_norm.v1",
            # Same strategy as `naming_contrast.v1`, but the subject is inferred from the
            # conclusion rather than fixed in advance, so the facets are identical and the
            # difference lives entirely in the implementation.
            applies_when=MethodApplicability(
                subject_kinds=public_code,
                lifecycles=["added", "renamed", "modified"],
                any_changed_components=["name", "statement_or_type", "value_or_body"],
                visibilities=["public"],
            ),
            required_inputs=["reviewed_declaration", "reviewed_workspace"],
            operators=[
                "conclusion_subject_inference", "snapshot_population_scan", "name_collision_check",
            ],
            max_opportunities=3,
            technical_checks=["name_collision"],
            norm_sources=["subject_conditioned_prevalence", "meaningful_counterexamples"],
            selection_policy="strong_naming_convention.v1",
        ),
        sealed_model(InvestigationMethod,
            method_id="lint_norm.v1",
            # Mathlib's text-based style lints apply to any reviewed content, not just
            # declarations — the motivating case is a module doc comment — so the facets
            # are deliberately wide and the capability predicate does the filtering.
            applies_when=MethodApplicability(
                subject_kinds=public_code + [
                    "abbreviation", "command", "import", "module_doc",
                    "namespace_or_section", "non_lean", "unknown",
                ],
                lifecycles=["added", "modified", "renamed", "moved", "unknown"],
                any_changed_components=[
                    "name", "binders", "statement_or_type", "attributes", "proof",
                    "value_or_body", "documentation", "namespace", "imports", "layout",
                    "unknown",
                ],
            ),
            required_inputs=["reviewed_source"],
            operators=["text_style_lint"],
            max_opportunities=3,
            technical_checks=["lint_rule"],
            norm_sources=["explicit_policy"],
            selection_policy="lint_rule.v1",
        ),
        sealed_model(InvestigationMethod,
            method_id="repository_policy.v1",
            # A forbidden construct is only this review's finding when the PR introduces
            # it, so only added/modified lifecycles are scheduled.
            applies_when=MethodApplicability(
                subject_kinds=public_code + ["abbreviation", "command", "unknown"],
                lifecycles=["added", "modified"],
                any_changed_components=[
                    "name", "statement_or_type", "proof", "value_or_body", "unknown",
                ],
            ),
            required_inputs=["reviewed_declaration"],
            operators=["forbidden_construct_scan"],
            max_opportunities=5,
            technical_checks=["lint_rule"],
            norm_sources=["explicit_policy"],
            selection_policy="repository_policy.v1",
        ),
    ]


def registry_sha256(methods: Iterable[InvestigationMethod]) -> str:
    return sha256_bytes(jsonl_bytes(methods))


def validate_registry(methods: Iterable[InvestigationMethod]) -> List[InvestigationMethod]:
    methods = list(methods)
    ids = [item.method_id for item in methods]
    if len(ids) != len(set(ids)):
        raise ValueError("method registry contains duplicate method IDs")
    # Ordered against the full historical list, not the active one. The `/4` registry is a
    # *subsequence* of `/3` — retiring the single-PR templates removed entries without
    # reordering the survivors — so both files must validate, or every frozen run scheduled
    # against `/3` stops loading and its lineage becomes unreplayable.
    if ids != sorted(ids, key=lambda value: (
        EXECUTION_ORDER_V3.index(value)
        if value in set(EXECUTION_ORDER_V3)
        else 100,
        value,
    )):
        raise ValueError("method registry is not in stable execution order")

    for item in methods:
        identity = item.model_dump(mode="json", exclude={"source_sha256"})
        expected = sha256_bytes(canonical_json_bytes(identity))
        if item.source_sha256 != expected:
            raise ValueError(f"method source hash mismatch: {item.method_id}")
        unknown_inputs = set(item.required_inputs) - KNOWN_INPUTS
        unknown_operators = set(item.operators) - KNOWN_OPERATORS
        unknown_checks = set(item.technical_checks) - KNOWN_CHECKS
        unknown_norms = set(item.norm_sources) - KNOWN_NORM_SOURCES
        if unknown_inputs or unknown_operators or unknown_checks or unknown_norms:
            raise ValueError(
                f"unknown method resources for {item.method_id}: "
                f"inputs={sorted(unknown_inputs)} operators={sorted(unknown_operators)} "
                f"checks={sorted(unknown_checks)} norms={sorted(unknown_norms)}"
            )
        if item.selection_policy not in KNOWN_POLICIES:
            raise ValueError(f"unknown selection policy for {item.method_id}: {item.selection_policy}")
        serialized = canonical_json_bytes(identity).decode("utf-8").lower()
        if any(token in serialized for token in ("gold", "maintainer comment", "post-review")):
            raise ValueError(f"method definition contains forbidden generation signal: {item.method_id}")
    return methods


def load_registry(path: Path = DEFAULT_REGISTRY) -> List[InvestigationMethod]:
    methods = [
        InvestigationMethod.model_validate_json(line)
        for line in path.read_text().splitlines()
        if line.strip()
    ]
    return validate_registry(methods)


def build_registry(path: Path = DEFAULT_REGISTRY) -> List[InvestigationMethod]:
    methods = validate_registry(default_methods())
    write_once(path, jsonl_bytes(methods))
    return methods


def main() -> None:
    parser = argparse.ArgumentParser(description="Build or validate v4 investigation methods")
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build")
    build.add_argument("--out", type=Path, default=DEFAULT_REGISTRY)
    validate = subparsers.add_parser("validate")
    validate.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    args = parser.parse_args()
    methods = build_registry(args.out) if args.command == "build" else load_registry(args.registry)
    path = args.out if args.command == "build" else args.registry
    print(json.dumps({
        "registry": str(path),
        "version": METHOD_REGISTRY_VERSION,
        "methods": [item.method_id for item in methods],
        "sha256": sha256_file(path),
    }, indent=2))


if __name__ == "__main__":
    main()
