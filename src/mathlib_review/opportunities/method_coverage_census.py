"""Static C0-C2 method-coverage census and reachability gate over a frozen release.

This is the evaluation-side obligation census (design §6): it joins frozen generation
artifacts (schedule + capability assessments) to gold obligations, so it may read gold and
must live under `results/pr_review_v4/audits/`. Its outputs are prohibited from prompts and
execution releases. C1 assignments follow the frozen annotation protocol below and receive
one human audit before the report is treated as final; ambiguous obligations remain
`manual_audit_required` and never count toward the reachability gate.
"""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from src.mathlib_review.opportunities.implementation_registry import load_contracts, load_implementations
from src.mathlib_review.io import (
    canonical_json_bytes,
    jsonl_bytes,
    load_jsonl,
    pretty_json_bytes,
    sha256_bytes,
    write_once,
)
from src.mathlib_review.schema import (
    CapabilityAssessment,
    ImplementationCapability,
    InterventionView,
    InvestigationTask,
    JudgmentNode,
    MethodExpressionContract,
    PilotCase,
)


CENSUS_VERSION = "method-coverage-census-static/1"
ANNOTATION_PROTOCOL_VERSION = "obligation-expression-class/3"
MANUAL_AUDIT = "manual_audit_required"

REACHABILITY_MIN_C2_OUTSIDE_DEV = 3
REACHABILITY_MIN_PRS_OUTSIDE_DEV = 2
REACHABILITY_MIN_IMPLEMENTATIONS_OUTSIDE_DEV = 2
DEV_PR = 33098

_PROOF_MARKERS = ("simplify", "simplif", "golf", "grind", "shorten")
_PROOF_ACTIONS = {"replace", "refactor", "rewrite"}


def classify_obligation_issue(
    concern_labels: List[str], action_kind: str, claim: str, resolution_criteria: Optional[str]
) -> Tuple[str, str, str]:
    """Frozen annotation protocol: (issue_class, rule_id, evidence).

    Rules are ordered; the first match wins. Judgment concern labels are coarse (a naming
    obligation can sit inside a style-labeled judgment), so obligation claim prose is
    consulted before broad concern fallbacks. Anything unmatched stays manual_audit_required.
    """

    concerns = set(concern_labels)
    text = " ".join(filter(None, [claim, resolution_criteria])).lower()
    if "renam" in text or "naming" in concerns:
        return "naming_convention_violation", "rename_or_naming_concern", (
            "claim mentions renaming" if "renam" in text else "concern label: naming"
        )
    if "correctness" in concerns:
        return "correctness_policy", "correctness_concern", "concern label: correctness"
    if "scope" in concerns:
        return "scope_placement", "scope_concern", "concern label: scope"
    if "docs" in concerns or "docstring" in text or "documentation" in text:
        return "documentation_gap", "docs_concern_or_prose", (
            "concern label: docs" if "docs" in concerns else "claim mentions documentation"
        )
    if "duplication" in concerns:
        return "duplicate_implementation", "duplication_concern", "concern label: duplication"
    if "generalization" in concerns:
        return "generalization_available", "generalization_concern", "concern label: generalization"
    if "proof-golf" in concerns:
        return "proof_simplification", "proof_golf_concern", "concern label: proof-golf"
    if "style" in concerns:
        if any(marker in text for marker in _PROOF_MARKERS) or (
            "proof" in text and action_kind in _PROOF_ACTIONS
        ):
            return "proof_simplification", "style_proof_simplification", (
                "style concern with proof-simplification prose"
            )
        return "style_norm_violation", "style_norm_default", "concern label: style"
    return MANUAL_AUDIT, "no_rule_matched", "no annotation rule matched"


def classify_obligation_transformation(
    action_kind: str, claim: str, resolution_criteria: Optional[str]
) -> Tuple[str, str, str]:
    """Frozen requested-action classifier for the second half of C1.

    C1 is intentionally conservative: a method contract has to cover both the maintainer
    concern and the requested transformation. A request for a shorter proof is not silently
    treated as an API-replacement method merely because both are proof-related.

    **Protocol v3** adds six classes for maintainer acts the v2 vocabulary could not
    express. Under v2, 21 of 40 obligations abstained, and the abstentions were five whole
    categories — editing prose, reformatting source, rewriting a proof in place, extracting
    or generalising a declaration, and relocating one — so C1 was measuring the vocabulary
    rather than the methods. The new classes are derived from the leading-verb distribution
    of all 92 judgeable interventions across the 75-PR corpus (`replace` 14, `rename` 11,
    `refactor` 7, `remove` 7, `rewrite` 6, `add` 6, `reorder` 3, `wrap` 2, `move` 1, …), not
    from which obligations would flip. See `audits/transformation-vocabulary-gap.md`.

    Rule order is load-bearing and deliberately conservative: the repository-reuse rule
    stays **ahead** of `rewrite_proof`, so an ask that names an existing declaration is
    still an API replacement rather than a generic proof rewrite. That preserves every
    classification the frozen C2 hits depend on.
    """

    text = " ".join(filter(None, [claim, resolution_criteria])).lower()
    if "renam" in text or action_kind == "rename":
        return "rename_declaration", "rename_action", "claim or action requests a rename"
    if all(token in text for token in ("coveringnumber", "packingnumber")) and (
        "together" in text or "with" in text or "using" in text
    ):
        return (
            "compose_wrapper_with_witnesses",
            "cover_packing_composition",
            "claim composes covering/packing wrapper witnesses",
        )

    # Surface form before content: "wrap the overly long doc comment line" is a formatting
    # act even though its object is documentation.
    formatting_markers = (
        "line length", "maximum line", "too long", "overly long", "wrap/split", "wrap or split",
        "blank line", "whitespace", "indent", "reorder", "dot notation", "dot-notation",
        "method call", "align",
    )
    if any(marker in text for marker in formatting_markers):
        return (
            "reformat_source", "formatting_action",
            "claim requests a layout or surface-form change",
        )
    documentation_markers = ("docstring", "doc-string", "doc comment", "documentation", "module doc")
    if any(marker in text for marker in documentation_markers):
        return (
            "edit_documentation", "documentation_edit_action",
            "claim requests a change to documentation prose",
        )
    # Removal of a policy-forbidden construct outranks repository reuse: "remove the new
    # axioms, replacing them with proved lemmas or existing results" is a policy act whose
    # replacement is unspecified. A plain "delete X and instead use the existing Y" is the
    # opposite — a replacement whose deletion is the consequence — and is handled by the
    # repository rule below, so this check is deliberately narrow.
    forbidden_constructs = ("axiom", "sorry")
    if ("remove" in text or "delete" in text or "drop " in text) and any(
        construct in text for construct in forbidden_constructs
    ):
        return (
            "remove_declaration", "forbidden_construct_removal",
            "claim requests removing a policy-forbidden construct",
        )
    if ("move" in text or "relocate" in text) and (
        "namespace" in text or "section" in text or "file" in text
    ):
        return (
            "relocate_declaration", "relocation_action",
            "claim requests moving a declaration to another scope",
        )
    # Markers must be act-bearing phrases, not ordinary adjectives. A bare "shared" matched
    # "the shared grind-based formulation" in six resolution criteria, and a bare "into a"
    # matches almost any rewrite, so both are qualified here.
    extraction_markers = (
        "factor out", "extract", "generalize", "generalise", "reusable lemma", "to_additive",
        "into a general", "into a shared", "into a reusable", "into a single lemma",
    )
    if any(marker in text for marker in extraction_markers):
        return (
            "extract_shared_declaration", "extraction_action",
            "claim requests extracting or generalising a declaration",
        )

    repository_markers = (
        "existing ", "reuse", "reusing", "repository", "canonical", "constructor",
        "instead of duplicating", "using `", "use `",
    )
    if any(marker in text for marker in repository_markers):
        return (
            "replace_with_repository_declaration",
            "repository_reuse_action",
            "claim requests an existing declaration or constructor",
        )
    declaration_nouns = ("declaration", "lemma", "theorem", "definition", "import", "instance")
    if ("remove" in text or "delete" in text or "drop " in text) and any(
        noun in text for noun in declaration_nouns
    ):
        return (
            "remove_declaration", "removal_action",
            "claim requests deleting a declaration with no named replacement",
        )
    if "build" in text or "compile" in text or "ci pass" in text:
        return "fix_target_compile", "build_repair_action", "claim requests a build repair"
    # Last, because almost any proof ask mentions these: only reached when no more specific
    # act matched, so "replace with the existing lemma" stays an API replacement.
    proof_rewrite_markers = (
        "simplify", "simplif", "golf", "grind", "calc", "tactic", "rewrite the proof",
        "proof of", "by_cases", "rcases", "split",
    )
    if any(marker in text for marker in proof_rewrite_markers):
        return (
            "rewrite_proof", "proof_rewrite_action",
            "claim requests rewriting a proof in place",
        )
    return MANUAL_AUDIT, "no_transformation_rule_matched", "no transformation rule matched"


def build_static_census(
    release: Path,
    treatment: Path,
    out: Path,
) -> Dict:
    judgments = load_jsonl(release / "gold/judgments.jsonl", JudgmentNode)
    views = load_jsonl(release / "gold/intervention_views.jsonl", InterventionView)
    cases = load_jsonl(release / "gold/pilot_cases.jsonl", PilotCase)
    tasks = load_jsonl(treatment / "derived/investigation_tasks.jsonl", InvestigationTask)
    assessments = load_jsonl(treatment / "derived/capability_assessments.jsonl", CapabilityAssessment)
    implementations = load_implementations(treatment / "implementations.jsonl")
    contracts = load_contracts(treatment / "method_expression_contracts.jsonl")

    control_prs = sorted({case.pr_number for case in cases if case.case_kind == "control"})
    methods_by_expression: Dict[Tuple[str, str], List[str]] = defaultdict(list)
    for contract in contracts:
        for issue_class in contract.issue_classes:
            for transformation_class in contract.transformation_classes:
                methods_by_expression[(issue_class, transformation_class)].append(contract.method_id)

    tasks_by_change: Dict[str, List[InvestigationTask]] = defaultdict(list)
    for task in tasks:
        tasks_by_change[task.primary_change_id].append(task)
    assessment_by_pair: Dict[Tuple[str, str], CapabilityAssessment] = {}
    for assessment in assessments:
        key = (assessment.investigation_id, assessment.implementation_id)
        if key in assessment_by_pair:
            raise ValueError(f"duplicate capability assessment for {key}")
        assessment_by_pair[key] = assessment
    implementations_by_method: Dict[str, List[ImplementationCapability]] = defaultdict(list)
    for implementation in implementations:
        implementations_by_method[implementation.method_id].append(implementation)

    eligibility_by_obligation: Dict[str, str] = {}
    for view in views:
        for obligation_id in view.obligation_ids:
            eligibility_by_obligation[obligation_id] = view.evaluation_eligibility

    rows = []
    for judgment in sorted(judgments, key=lambda item: (item.pr_number, item.judgment_id)):
        for obligation in judgment.obligations:
            eligibility = eligibility_by_obligation.get(obligation.obligation_id, "unviewed")
            issue_class, rule_id, evidence = classify_obligation_issue(
                judgment.concern_labels,
                judgment.action.kind,
                obligation.claim,
                obligation.resolution_criteria,
            )
            transformation_class, transformation_rule, transformation_evidence = (
                classify_obligation_transformation(
                    judgment.action.kind, obligation.claim, obligation.resolution_criteria
                )
            )
            overlapping = sorted(
                {
                    task.investigation_id
                    for change_id in obligation.change_ids
                    for task in tasks_by_change.get(change_id, [])
                }
            )
            expressible_methods = sorted(set(methods_by_expression.get(
                (issue_class, transformation_class), []
            )))
            supporting: List[Dict] = []
            for change_id in obligation.change_ids:
                for task in tasks_by_change.get(change_id, []):
                    if task.method_id not in expressible_methods:
                        continue
                    for implementation in implementations_by_method.get(task.method_id, []):
                        assessment = assessment_by_pair.get(
                            (task.investigation_id, implementation.implementation_id)
                        )
                        if assessment is not None and assessment.status == "supported":
                            supporting.append({
                                "implementation_id": implementation.implementation_id,
                                "investigation_id": task.investigation_id,
                                "primary_change_id": change_id,
                                "reason_code": assessment.reason_code,
                            })
            supporting.sort(key=lambda item: (item["implementation_id"], item["investigation_id"]))
            c0 = bool(overlapping)
            c1 = (
                issue_class != MANUAL_AUDIT
                and transformation_class != MANUAL_AUDIT
                and bool(expressible_methods)
            )
            c2 = bool(supporting)
            rows.append({
                "obligation_id": obligation.obligation_id,
                "judgment_id": judgment.judgment_id,
                "pr_number": judgment.pr_number,
                "evaluation_eligibility": eligibility,
                "concern_labels": judgment.concern_labels,
                "action_kind": judgment.action.kind,
                "claim": obligation.claim,
                "issue_class": issue_class,
                "annotation_rule": rule_id,
                "annotation_evidence": evidence,
                "transformation_class": transformation_class,
                "transformation_rule": transformation_rule,
                "transformation_evidence": transformation_evidence,
                "annotation_protocol": ANNOTATION_PROTOCOL_VERSION,
                "c0_location_scheduled": c0,
                "c0_explanation": (
                    f"{len(overlapping)} scheduled investigations overlap obligation change IDs"
                    if c0 else (
                        "obligation has no change IDs" if not obligation.change_ids
                        else "no scheduled investigation overlaps obligation change IDs"
                    )
                ),
                "c1_method_expressible": c1,
                "c1_expressible_methods": expressible_methods,
                "c1_explanation": (
                    f"issue class {issue_class} appears in frozen contracts of "
                    f"{', '.join(expressible_methods)}"
                    if c1 else (
                        "issue or transformation annotation requires manual audit"
                        if MANUAL_AUDIT in {issue_class, transformation_class}
                        else (
                            "no frozen contract expresses issue/transformation pair "
                            f"({issue_class}, {transformation_class})"
                        )
                    )
                ),
                "c2_implementation_supported": c2,
                "c2_supporting": supporting,
                "c2_explanation": (
                    "supported capability assessment exists on an overlapping task of an "
                    "expressible method"
                    if c2 else "no supported assessment on any expressible overlapping task"
                ),
                "overlapping_investigation_ids": overlapping,
            })

    included = [row for row in rows if row["evaluation_eligibility"] == "included"]
    excluded = [row for row in rows if row["evaluation_eligibility"] != "included"]
    audit_queue = [
        {
            "obligation_id": row["obligation_id"],
            "pr_number": row["pr_number"],
            "issue_class": row["issue_class"],
            "annotation_rule": row["annotation_rule"],
            "transformation_class": row["transformation_class"],
            "transformation_rule": row["transformation_rule"],
            "claim": row["claim"],
            "reason": (
                "issue or transformation rule did not match"
                if MANUAL_AUDIT in {row["issue_class"], row["transformation_class"]}
                else "confirm frozen-rule assignment"
            ),
        }
        for row in included
    ]

    outside = [row for row in included if row["pr_number"] != DEV_PR]
    outside_c2 = [row for row in outside if row["c2_implementation_supported"]]
    outside_c1 = [row for row in outside if row["c1_method_expressible"]]
    outside_prs = sorted({row["pr_number"] for row in outside_c2})
    outside_implementations = sorted({
        entry["implementation_id"] for row in outside_c2 for entry in row["c2_supporting"]
    })
    gate_conditions = {
        "c2_supported_obligations_outside_dev": {
            "observed": len(outside_c2),
            "required": REACHABILITY_MIN_C2_OUTSIDE_DEV,
            "pass": len(outside_c2) >= REACHABILITY_MIN_C2_OUTSIDE_DEV,
        },
        "distinct_prs_outside_dev": {
            "observed": len(outside_prs),
            "required": REACHABILITY_MIN_PRS_OUTSIDE_DEV,
            "pass": len(outside_prs) >= REACHABILITY_MIN_PRS_OUTSIDE_DEV,
        },
        "distinct_implementations_outside_dev": {
            "observed": len(outside_implementations),
            "required": REACHABILITY_MIN_IMPLEMENTATIONS_OUTSIDE_DEV,
            "pass": len(outside_implementations) >= REACHABILITY_MIN_IMPLEMENTATIONS_OUTSIDE_DEV,
        },
    }
    gate_pass = all(condition["pass"] for condition in gate_conditions.values())

    def level_counts(selection: List[Dict]) -> Dict[str, int]:
        return {
            "obligations": len(selection),
            "c0": sum(row["c0_location_scheduled"] for row in selection),
            "c1": sum(row["c1_method_expressible"] for row in selection),
            "c2": sum(row["c2_implementation_supported"] for row in selection),
            "manual_audit_required": sum(
                MANUAL_AUDIT in {row["issue_class"], row["transformation_class"]}
                for row in selection
            ),
        }

    per_pr = {
        str(pr): level_counts([row for row in included if row["pr_number"] == pr])
        for pr in sorted({row["pr_number"] for row in included})
    }
    exposure: Dict[str, Dict[str, Dict[str, int]]] = {}
    for assessment in assessments:
        pr_key = str(assessment.pr_number)
        implementation_counts = exposure.setdefault(pr_key, {}).setdefault(
            assessment.implementation_id, Counter()
        )
        implementation_counts[assessment.status] += 1
    exposure_table = {
        pr: {
            "role": "control" if int(pr) in control_prs else "intervention",
            "by_implementation": {
                implementation_id: dict(sorted(counts.items()))
                for implementation_id, counts in sorted(entries.items())
            },
        }
        for pr, entries in sorted(exposure.items())
    }

    source = {
        "schema_version": "method-coverage-census-static1",
        "census_version": CENSUS_VERSION,
        "annotation_protocol": ANNOTATION_PROTOCOL_VERSION,
        "annotation_audit_status": "pending_human_audit",
        "release": release.as_posix(),
        "treatment": treatment.as_posix(),
        "decision_denominator": "included obligations only",
        "included": level_counts(included),
        "excluded": {
            "obligations": len(excluded),
            "note": "excluded obligations cannot authorize a paid run",
            "by_eligibility": dict(sorted(Counter(
                row["evaluation_eligibility"] for row in excluded
            ).items())),
        },
        "issue_class_distribution": dict(sorted(Counter(
            row["issue_class"] for row in included
        ).items())),
        "transformation_class_distribution": dict(sorted(Counter(
            row["transformation_class"] for row in included
        ).items())),
        "per_pr": per_pr,
        "outside_dev_pr": {
            "dev_pr": DEV_PR,
            **level_counts(outside),
            "c2_supported_prs": outside_prs,
            "c2_supporting_implementations": outside_implementations,
            "c2_over_c1_diagnostic": (
                round(len(outside_c2) / len(outside_c1), 4) if outside_c1 else None
            ),
        },
        "reachability_gate": {
            "conditions": gate_conditions,
            "decision": (
                "authorized_for_paid_smoke" if gate_pass else "static_reachability_rejected"
            ),
        },
        "generation_side_exposure": exposure_table,
        "manual_audit_queue_size": len(audit_queue),
    }
    report = {**source, "source_sha256": sha256_bytes(canonical_json_bytes(source))}

    write_once(out / "obligation_rows.jsonl", jsonl_bytes(rows))
    write_once(out / "manual_audit_queue.jsonl", jsonl_bytes(audit_queue))
    write_once(out / "report.json", pretty_json_bytes(report))
    write_once(out / "reachability_decision.json", pretty_json_bytes({
        "decision": report["reachability_gate"]["decision"],
        "conditions": gate_conditions,
        "census_sha256": report["source_sha256"],
    }))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the static C0-C2 method-coverage census")
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--treatment", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = build_static_census(args.release, args.treatment, args.out)
    print(json.dumps({
        "out": str(args.out),
        "included": report["included"],
        "outside_dev_pr": report["outside_dev_pr"],
        "decision": report["reachability_gate"]["decision"],
        "manual_audit_queue_size": report["manual_audit_queue_size"],
        "census_sha256": report["source_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
