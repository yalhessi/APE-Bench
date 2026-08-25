"""Synthetic-ladder gates for the static C0-C2 census and reachability decision."""

import json

from src.datasets.pr_review_v4.implementation_registry import (
    assess_capabilities,
    build_registry_files,
    default_implementations,
)
from src.datasets.pr_review_v4.io import jsonl_bytes
from src.datasets.pr_review_v4.method_coverage_census import (
    build_static_census,
    classify_obligation_issue,
    classify_obligation_transformation,
)
from src.datasets.pr_review_v4.schema import (
    ChangeGraph,
    ChangeTarget,
    InterventionView,
    InvestigationTask,
    JudgmentAction,
    JudgmentAnnotation,
    JudgmentNode,
    JudgmentObligation,
    PilotCase,
)

from tests.datasets.test_pr_review_v4_implementation_registry import (
    INSERT_SEPARATION_POSITIVE,
    NAMING_POSITIVE,
    _graph,
    _target,
    _task,
)


def test_annotation_protocol_classifies_motivating_and_gap_obligations():
    naming = classify_obligation_issue(
        ["style"], "replace",
        "Rename the maximal-separated-set cardinality lemma with an `encard_` prefix.", None,
    )
    assert naming[0] == "naming_convention_violation"
    canonical = classify_obligation_issue(
        ["proof-golf"], "refactor",
        "Refactor the proof of the key step by introducing an abbreviation.", None,
    )
    assert canonical[0] == "proof_simplification"
    grind = classify_obligation_issue(
        ["style"], "replace",
        "Simplify the cardinality proof with the requested grind-based treatment.", None,
    )
    assert grind[0] == "proof_simplification"
    style = classify_obligation_issue(["style"], "insert", "Insert a blank line.", None)
    assert style[0] == "style_norm_violation"
    docs = classify_obligation_issue(["docs"], "fix", "Fix the docstring typo.", None)
    assert docs[0] == "documentation_gap"
    unknown = classify_obligation_issue(["meta"], "other", "Please rebase onto master.", None)
    assert unknown[0] == "manual_audit_required"
    rename = classify_obligation_transformation(
        "rename", "Rename the lemma with an encard_ prefix.", None,
    )
    assert rename[0] == "rename_declaration"
    repository_reuse = classify_obligation_transformation(
        "replace", "Use the existing repository lemma instead of duplicating this proof.", None,
    )
    assert repository_reuse[0] == "replace_with_repository_declaration"
    unknown_transformation = classify_obligation_transformation(
        "rewrite", "Make the proof more elegant.", None,
    )
    assert unknown_transformation[0] == "manual_audit_required"


def _judgment(judgment_id, pr, concerns, action_kind, obligations):
    return JudgmentNode(
        judgment_id=judgment_id,
        source_intervention_id=f"intervention:{judgment_id}",
        repo="leanprover-community/mathlib4",
        pr_number=pr,
        episode_id="episode:test",
        action=JudgmentAction(kind=action_kind, object="target"),
        speech_act="request",
        blocking_force="advisory",
        concern_labels=concerns,
        scope_relations=[],
        obligations=obligations,
        source_event_ids=[],
        context_relations=[],
        outcome_observation_ids=[],
        annotation=JudgmentAnnotation(
            producer="test",
            source_schema="test1",
            status="migration_proposal",
            atomicity_status="presumed_atomic",
        ),
        source_sha256="judgment-hash",
    )


def _obligation(obligation_id, claim, change_ids):
    return JudgmentObligation(
        obligation_id=obligation_id,
        claim=claim,
        status="proposed_atomic",
        change_ids=change_ids,
        source_sha256="obligation-hash",
    )


def _view(view_id, judgment_ids, obligation_ids, eligibility="included"):
    return InterventionView(
        view_id=view_id,
        source_intervention_id=f"intervention:{view_id}",
        judgment_ids=judgment_ids,
        obligation_ids=obligation_ids,
        aggregation_policy="all_required",
        evaluation_eligibility=eligibility,
        source_sha256="view-hash",
    )


def _write_fixture(root, judgments, views, cases, tasks, assessments):
    release = root / "release"
    treatment = root / "treatment"
    (release / "gold").mkdir(parents=True)
    (treatment / "derived").mkdir(parents=True)
    (release / "gold/judgments.jsonl").write_bytes(jsonl_bytes(judgments))
    (release / "gold/intervention_views.jsonl").write_bytes(jsonl_bytes(views))
    (release / "gold/pilot_cases.jsonl").write_bytes(jsonl_bytes(cases))
    (treatment / "derived/investigation_tasks.jsonl").write_bytes(jsonl_bytes(tasks))
    (treatment / "derived/capability_assessments.jsonl").write_bytes(jsonl_bytes(assessments))
    build_registry_files(treatment)
    return release, treatment


def _case(pr, kind):
    return PilotCase(
        pr_number=pr,
        episode_ids=["episode:test"],
        case_kind=kind,
        target_facets=["test"],
        rationale="synthetic",
        control_semantics="no intervention expected" if kind == "control" else None,
        source_sha256="case-hash",
    )


def test_static_census_ladder_and_reachability_rejection(tmp_path):
    # One obligation reaches C2 (naming, supported); one stops at C1 gap (style norm);
    # one is manual-audit; one is excluded and must stay out of the decision denominator.
    targets = [
        _target("change:naming-pos", NAMING_POSITIVE),
        _target("change:style", "theorem foo : True := by trivial\n"),
    ]
    graph = _graph(targets)
    tasks = [
        _task("investigation:n1", "naming_contrast.v1", "change:naming-pos"),
        _task("investigation:b1", "baseline_failure.v1", "change:style"),
    ]
    assessments = assess_capabilities(tasks, [graph], default_implementations())
    judgments = [
        _judgment("j1", 100, ["style"], "replace", [
            _obligation("obligation:1", "Rename the lemma with an `encard_` prefix.",
                        ["change:naming-pos"]),
        ]),
        # A method gap that survives the current registry: no contract covers relocating
        # a declaration. (A blank-line ask would now be covered by lint_norm.v1, so it no
        # longer demonstrates a C1 gap.)
        _judgment("j2", 100, ["scope"], "move", [
            _obligation("obligation:2", "Move the lemma into the `Complex` namespace.",
                        ["change:style"]),
        ]),
        _judgment("j3", 200, ["meta"], "other", [
            _obligation("obligation:3", "Please rebase onto master.", []),
        ]),
        _judgment("j4", 200, ["docs"], "fix", [
            _obligation("obligation:4", "Fix the docstring.", ["change:style"]),
        ]),
    ]
    views = [
        _view("v1", ["j1"], ["obligation:1"]),
        _view("v2", ["j2"], ["obligation:2"]),
        _view("v3", ["j3"], ["obligation:3"]),
        _view("v4", ["j4"], ["obligation:4"], eligibility="excluded_not_judgeable"),
    ]
    cases = [_case(100, "intervention"), _case(200, "intervention"), _case(300, "control")]
    release, treatment = _write_fixture(tmp_path, judgments, views, cases, tasks, assessments)

    report = build_static_census(release, treatment, tmp_path / "census")
    # Under annotation protocol v3 the relocation ask classifies as `relocate_declaration`
    # rather than abstaining, so only the meta obligation still needs a human ruling.
    assert report["included"] == {
        "obligations": 3, "c0": 2, "c1": 1, "c2": 1, "manual_audit_required": 1,
    }
    assert report["excluded"]["obligations"] == 1
    rows = {
        json.loads(line)["obligation_id"]: json.loads(line)
        for line in (tmp_path / "census/obligation_rows.jsonl").read_text().splitlines()
    }
    # The ladder is not inferred from overlap: C0 without C1, and C1 gaps are explicit.
    assert rows["obligation:1"]["c0_location_scheduled"]
    assert rows["obligation:1"]["c1_method_expressible"]
    assert rows["obligation:1"]["c2_implementation_supported"]
    assert rows["obligation:1"]["c2_supporting"][0]["implementation_id"] == (
        "naming_contrast.encard_subject_prefix.v1"
    )
    assert rows["obligation:2"]["c0_location_scheduled"]
    assert not rows["obligation:2"]["c1_method_expressible"]
    # v3 names the uncovered pair instead of reporting an abstention — a C1 gap that is
    # now attributable to a missing *method* rather than to a missing vocabulary term.
    assert "(scope_placement, relocate_declaration)" in rows["obligation:2"]["c1_explanation"]
    assert rows["obligation:3"]["issue_class"] == "manual_audit_required"
    assert not rows["obligation:3"]["c1_method_expressible"]
    assert rows["obligation:2"]["transformation_class"] == "relocate_declaration"
    assert rows["obligation:4"]["evaluation_eligibility"] == "excluded_not_judgeable"

    # One C2 obligation outside the dev PR across one PR and one implementation: rejected.
    gate = report["reachability_gate"]
    assert gate["decision"] == "static_reachability_rejected"
    assert not gate["conditions"]["c2_supported_obligations_outside_dev"]["pass"]

    # The audit queue covers every included obligation for the one-pass human audit.
    queue = (tmp_path / "census/manual_audit_queue.jsonl").read_text().splitlines()
    assert len(queue) == 3

    # Rerunning must be byte-identical; write_once raises on any drift.
    again = build_static_census(release, treatment, tmp_path / "census")
    assert again["source_sha256"] == report["source_sha256"]


def test_static_census_authorizes_only_with_breadth_beyond_dev_pr(tmp_path):
    # Three C2-supported obligations outside the dev PR, across two PRs and two
    # implementations, satisfy every reachability condition.
    naming_b = NAMING_POSITIVE.replace("card_maximalSeparatedSet", "card_of_isSeparated")
    targets = [
        _target("change:n1", NAMING_POSITIVE),
        _target("change:n2", naming_b),
        _target("change:c1", INSERT_SEPARATION_POSITIVE),
    ]
    graph = _graph(targets)
    tasks = [
        _task("investigation:n1", "naming_contrast.v1", "change:n1"),
        _task("investigation:n2", "naming_contrast.v1", "change:n2"),
        _task("investigation:c1", "canonical_api_search.v1", "change:c1"),
    ]
    assessments = assess_capabilities(tasks, [graph], default_implementations())
    judgments = [
        _judgment("j1", 100, ["naming"], "rename", [
            _obligation("obligation:1", "Rename with an encard_ prefix.", ["change:n1"]),
        ]),
        _judgment("j2", 100, ["naming"], "rename", [
            _obligation("obligation:2", "Rename with an encard_ prefix.", ["change:n2"]),
        ]),
        _judgment("j3", 200, ["proof-golf"], "refactor", [
            _obligation(
                "obligation:3",
                "Use the existing insert-separation declaration instead of duplicating the case analysis.",
                ["change:c1"],
            ),
        ]),
    ]
    views = [
        _view("v1", ["j1"], ["obligation:1"]),
        _view("v2", ["j2"], ["obligation:2"]),
        _view("v3", ["j3"], ["obligation:3"]),
    ]
    cases = [_case(100, "intervention"), _case(200, "intervention")]
    release, treatment = _write_fixture(tmp_path, judgments, views, cases, tasks, assessments)

    report = build_static_census(release, treatment, tmp_path / "census")
    gate = report["reachability_gate"]
    assert gate["decision"] == "authorized_for_paid_smoke"
    assert report["outside_dev_pr"]["c2_supporting_implementations"] == [
        "canonical_api.insert_separation.v1",
        "naming_contrast.encard_subject_prefix.v1",
    ]
    exposure = report["generation_side_exposure"]
    assert exposure["100"]["role"] == "intervention"
    assert (
        exposure["100"]["by_implementation"]["naming_contrast.encard_subject_prefix.v1"][
            "supported"
        ]
        == 2
    )


def test_static_census_requires_transformation_contract_match(tmp_path):
    graph = _graph([_target("change:c1", INSERT_SEPARATION_POSITIVE)])
    task = _task("investigation:c1", "canonical_api_search.v1", "change:c1")
    assessments = assess_capabilities([task], [graph], default_implementations())
    judgments = [_judgment("j1", 100, ["proof-golf"], "refactor", [
        _obligation("obligation:1", "Simplify this case analysis.", ["change:c1"]),
    ])]
    views = [_view("v1", ["j1"], ["obligation:1"])]
    release, treatment = _write_fixture(
        tmp_path, judgments, views, [_case(100, "intervention")], [task], assessments,
    )

    report = build_static_census(release, treatment, tmp_path / "census")
    row = json.loads((tmp_path / "census/obligation_rows.jsonl").read_text())
    # The ask is now *classified* (protocol v3 can express an in-place proof rewrite), which
    # makes this a stronger demonstration of C1 conjunctivity than the old abstention did:
    # the issue class matches canonical_api's contract, but the transformation class does
    # not, so C1 must still be false.
    assert row["issue_class"] == "proof_simplification"
    assert row["transformation_class"] == "rewrite_proof"
    assert not row["c1_method_expressible"]
    assert not row["c2_implementation_supported"]
    assert report["included"]["c1"] == 0
