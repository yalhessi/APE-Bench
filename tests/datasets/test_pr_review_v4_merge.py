"""Acceptance tests for the arm-neutral merge.

The merge exists because the two arms previously had no shared consumer at all:
`synthesis.link_candidates` raised unless a candidate mapped to exactly one opportunity,
and a holistic candidate has none. Everything here is a property the plan named as
acceptance criteria.
"""

from __future__ import annotations

import pytest

from src.mathlib_review.review.merge import (
    canonical_action,
    finding_from_candidate,
    finding_from_opportunity,
    merge_findings,
)
from src.mathlib_review.schema import (
    CandidateClaim,
    FindingSource,
    OpportunityTransformation,
    ReviewFinding,
    ReviewOpportunity,
    WorthinessDecision,
)


def _candidate(cid="candidate:1", family="naming", change_ids=("change:1",),
               requested="Rename the lemma.", severity="advisory"):
    return CandidateClaim(
        candidate_id=cid, work_unit_id="w", episode_id="e1", pr_number=1,
        change_ids=list(change_ids), primary_change_id=change_ids[0],
        concern_family=family, concern_label=family, severity=severity,
        claim="c", requested_change=requested, evidence_requests=[], source_sha256=f"h-{cid}",
    )


def _opportunity(oid="opportunity:1", change_id="change:1", requested="Rename the lemma.",
                 method="naming_norm.v1"):
    return ReviewOpportunity(
        opportunity_id=oid, investigation_id="investigation:1", method_id=method,
        episode_id="e1", pr_number=1, primary_change_id=change_id, related_change_ids=[],
        observed_pattern="pattern",
        proposed_transformation=OpportunityTransformation(
            kind="rename_declaration", symbols=["Foo.bar"], description=requested,
        ),
        source_artifact_ids=["opportunity-evidence:1"], discovery_rank=1,
        discovery_score=1.0, source_provenance="automatic", source_sha256=f"h-{oid}",
    )


def _decision(worthiness="request", force="advisory", oid="opportunity:1"):
    return WorthinessDecision(
        decision_id="decision:1", opportunity_id=oid,
        technical_assessment_id="technical-assessment:1",
        review_worthiness=worthiness,
        # The schema enforces that only a `request` may carry a force.
        request_force=force if worthiness == "request" else None,
        evidence_artifact_ids=["opportunity-evidence:1"],
        rationale="r", producer="policy", source_sha256="h",
    )


def _published(candidate, tier="model_assertion"):
    return finding_from_candidate(
        candidate, admission="published", admission_reason="evidence supported",
        evidence_tier=tier,
    )


def test_a_generalist_finding_needs_no_opportunity_lineage():
    """The structural blocker: the old link required an opportunity ID, so a holistic
    candidate could never pass through the merge at all."""

    finding = _published(_candidate())
    assert finding.sources[0].arm == "generalist"
    assert finding.sources[0].opportunity_id is None
    merged, conflicts, report = merge_findings([finding])
    assert report["by_admission"]["published"] == 1
    assert not conflicts


def test_a_deterministic_source_must_carry_its_lineage():
    """Auditability runs the other way: the deterministic arm's warrant is its evidence."""

    with pytest.raises(ValueError, match="lineage"):
        FindingSource(arm="deterministic", opportunity_id=None, evidence_artifact_ids=[])


def test_different_concerns_on_the_same_target_both_survive():
    """The plan's first acceptance test.

    A naming finding and an unrelated proof finding at one target are two review comments,
    not a duplicate — merging on location alone would silently delete one.
    """

    naming = _published(_candidate("candidate:n", family="naming"))
    golf = _published(_candidate("candidate:g", family="proof-golf",
                                 requested="Shorten the proof."))
    merged, conflicts, _report = merge_findings([naming, golf])
    published = [item for item in merged if item.admission == "published"]
    assert len(published) == 2
    assert {item.concern_family for item in published} == {"naming", "proof-golf"}
    assert not conflicts


def test_the_two_arms_agreeing_produce_one_finding_with_both_sources():
    deterministic = finding_from_opportunity(
        _opportunity(), _decision(), concern_family="naming",
        evidence_tier="repository_measurement",
    )
    holistic = _published(_candidate())
    merged, _conflicts, report = merge_findings([deterministic, holistic])
    published = [item for item in merged if item.admission == "published"]
    assert len(published) == 1
    assert published[0].arm == "merged"
    assert {source.arm for source in published[0].sources} == {"deterministic", "generalist"}
    # The surviving wording is the better-warranted one, not the first by hash.
    assert published[0].evidence_tier == "repository_measurement"
    assert report["by_arm"]["merged"] == 1


def test_an_uncertain_paraphrase_is_not_merged():
    """Merging is lossy — only the representative's text survives to be judged — so it
    happens only on canonical equality, never on a guess about similarity."""

    a = _published(_candidate("candidate:a", requested="Rename the lemma."))
    b = _published(_candidate("candidate:b", requested="Give the lemma a better name."))
    merged, conflicts, _report = merge_findings([a, b])
    # Same anchor and family, different action: a conflict to surface, not a silent merge.
    assert len(conflicts) == 1
    assert not [item for item in merged if item.admission == "published"]


def test_canonical_action_ignores_only_case_and_whitespace():
    assert canonical_action("naming", "Rename  the\nlemma.") == canonical_action(
        "naming", "rename the lemma."
    )
    assert canonical_action("naming", "Rename it") != canonical_action("style", "Rename it")


def test_equal_strength_disagreement_becomes_a_conflict_not_a_winner():
    a = _published(_candidate("candidate:a", requested="Delete the helper."))
    b = _published(_candidate("candidate:b", requested="Keep the helper but rename it."))
    merged, conflicts, _report = merge_findings([a, b])
    assert len(conflicts) == 1
    assert sorted(conflicts[0].finding_ids) == sorted(
        item.finding_id for item in merged
    )
    assert all(item.admission == "diagnostic" for item in merged)
    assert "no side is preferred" in conflicts[0].rationale


def test_stronger_evidence_resolves_a_disagreement():
    weak = _published(_candidate("candidate:a", requested="Delete the helper."))
    strong = _published(
        _candidate("candidate:b", requested="Keep the helper but rename it."),
        tier="verified_compile",
    )
    merged, conflicts, _report = merge_findings([weak, strong])
    assert not conflicts
    published = [item for item in merged if item.admission == "published"]
    assert len(published) == 1
    assert published[0].evidence_tier == "verified_compile"


def test_deferred_checker_work_is_diagnostic_and_never_published():
    """`defer` means the policy could not decide, which is not something to tell a
    maintainer — but the reach it represents still has to be measurable."""

    finding = finding_from_opportunity(
        _opportunity(), _decision("defer"), concern_family="naming",
        evidence_tier="lexical_rule",
    )
    assert finding.admission == "diagnostic"
    assert "defer" in finding.admission_reason
    _merged, _conflicts, report = merge_findings([finding])
    assert report["by_admission"] == {"published": 0, "diagnostic": 1}


def test_the_publication_limit_is_per_pr_and_reports_what_it_cut():
    """It was applied to a flat list across every PR while claiming to be a PR budget."""

    findings = []
    for pr_number in (1, 2):
        for index in range(4):
            candidate = _candidate(
                f"candidate:{pr_number}-{index}", change_ids=(f"change:{pr_number}-{index}",),
                requested=f"Fix thing {index}.",
            )
            findings.append(_published(candidate).model_copy(update={"pr_number": pr_number}))

    merged, _conflicts, report = merge_findings(findings, pr_finding_limit=3)
    published = [item for item in merged if item.admission == "published"]
    per_pr = {pr: sum(item.pr_number == pr for item in published) for pr in (1, 2)}
    assert per_pr == {1: 3, 2: 3}, "the budget is per PR, not global"
    assert report["published_before_limit"] == 8
    assert report["published_after_limit"] == 6
    assert report["suppressed_by_limit"] == 2


def test_publication_ordering_never_reads_model_confidence():
    """Self-confidence has been falsified as a ranking signal three times.

    Checks for *access*, not for the word: forbidding the string would prevent the module
    from documenting why the signal is rejected, which is worth more than the shortcut.
    """

    import ast
    import inspect

    from src.mathlib_review.review import merge

    tree = ast.parse(inspect.getsource(merge))
    reads = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Attribute) and node.attr == "model_confidence"
    ] + [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and node.value == "model_confidence"
    ]
    assert not reads, "merge must never read model_confidence"


def test_ordering_prefers_verified_evidence_then_blocking_severity():
    weak = _published(_candidate("candidate:w", change_ids=("change:w",),
                                 requested="Weak ask.", severity="blocking"))
    strong = _published(_candidate("candidate:s", change_ids=("change:s",),
                                   requested="Strong ask."), tier="verified_compile")
    merged, _conflicts, _report = merge_findings([weak, strong], pr_finding_limit=1)
    published = [item for item in merged if item.admission == "published"]
    assert len(published) == 1
    assert published[0].evidence_tier == "verified_compile", (
        "a verified finding outranks an unverified one even when the latter is blocking"
    )


# --- candidate quarantine ----------------------------------------------------------

def _unit():
    from src.mathlib_review.schema import ReviewWorkUnit

    return ReviewWorkUnit(
        work_unit_id="work-unit:1", episode_id="e1", graph_id="graph:1",
        repo="leanprover-community/mathlib4", pr_number=1, round_index=1,
        change_ids=["change:1"], target_sha256s={"change:1": "t"}, renderer_version="test/1",
        entity_ids_by_change={"change:1": []},
        primary_subjects_by_change={"change:1": "Foo.bar"},
        source_sha256="h",
    )


def _raw(subject="Foo.bar", claim="Foo.bar needs a rename."):
    return {
        "change_ids": ["change:1"], "primary_change_id": "change:1",
        "primary_subject": subject, "primary_entity_id": None,
        "concern_family": "naming", "concern_label": "naming", "severity": "advisory",
        "claim": claim, "requested_change": "Rename it.",
    }


def test_one_malformed_candidate_no_longer_discards_the_whole_batch():
    """Ingestion used to `raise` on the first bad item, losing every good one and leaving
    no artifact — so drop rates were unmeasurable."""

    from src.mathlib_review.review.candidates import candidates_from_response

    response = {"candidates": [_raw(), _raw(subject="Wrong.subject"), _raw()]}
    accepted, rejected = candidates_from_response(_unit(), response, strict=False)
    assert len(accepted) == 2
    assert len(rejected) == 1
    assert rejected[0].ordinal == 1
    assert rejected[0].reason_code == "primary_subject_mismatch"
    assert rejected[0].raw_sha256


def test_strict_mode_is_still_the_default_so_existing_gates_keep_their_meaning():
    from src.mathlib_review.review.candidates import candidates_from_response

    with pytest.raises(ValueError):
        candidates_from_response(_unit(), {"candidates": [_raw(subject="Wrong.subject")]})


def test_a_missing_candidates_list_is_still_a_response_level_failure():
    """A malformed *candidate* is quarantined; a response that produced nothing usable is
    a coverage failure and must not be silently downgraded to an empty candidate set."""

    from src.mathlib_review.review.candidates import candidates_from_response

    with pytest.raises(ValueError, match="candidates list"):
        candidates_from_response(_unit(), {}, strict=False)


# --- conditions --------------------------------------------------------------------

def test_running_both_naming_implementations_double_counts_every_rename():
    """Measured on medium: `naming_contrast` and `naming_norm` request the same renames in
    different words (`Metric.card_x` vs `card_x`), so the merge — whose canonical equality
    is case and whitespace only, deliberately — reports them as conflicts rather than
    silently choosing one.

    This used to be handled by naming the narrow implementation in `SUBSUMED_METHODS`, which
    `build_condition` never applied. It is now settled in the registry: `naming_contrast.v1`
    is retired outright, both because it double-counts against `naming_norm.v1` and because
    it hardcodes `Set.encard` and fires only on the PR it was written from. The guarantee
    holds with no exclusions passed, which is what makes it a guarantee.
    """

    from src.mathlib_review.opportunities.method_registry import default_methods

    scheduled = {item.method_id for item in default_methods()}
    assert "naming_contrast.v1" not in scheduled
    assert "naming_norm.v1" in scheduled


def test_a_condition_requires_the_inputs_its_arms_need():
    from pathlib import Path

    from src.mathlib_review.review.conditions import build_condition

    with pytest.raises(ValueError, match="execution-release"):
        build_condition("checker_only", Path("/tmp/nope"))
    with pytest.raises(ValueError, match="candidates"):
        build_condition("generalist_only", Path("/tmp/nope"))
    with pytest.raises(ValueError, match="unknown condition"):
        build_condition("something_else", Path("/tmp/nope"))


def test_evidence_tiers_claim_verified_only_where_a_compiler_actually_ran():
    """`verified_compile` outranks everything, so claiming it loosely would let a lexical
    rule outrank a real compile in both merge resolution and publication ordering."""

    from src.mathlib_review.review.conditions import _EVIDENCE_BY_METHOD

    assert _EVIDENCE_BY_METHOD["baseline_failure.v1"] == "verified_compile"
    assert _EVIDENCE_BY_METHOD["lint_norm.v1"] == "lexical_rule"
    assert _EVIDENCE_BY_METHOD["naming_norm.v1"] == "repository_measurement"


# --- alternatives vs contradictions ------------------------------------------------

def _verified(cid, requested, edit_text, change_ids=("change:1",)):
    """A finding carrying an edit the compiler accepted."""

    from src.mathlib_review.schema import ProposedEdit

    candidate = _candidate(cid, family="proof-golf", change_ids=change_ids,
                           requested=requested)
    candidate = candidate.model_copy(update={"proposed_edit": ProposedEdit(
        path="Mathlib/A.lean", declaration_name="Foo.bar", new_declaration=edit_text,
    )})
    return finding_from_candidate(
        candidate, admission="published", admission_reason="verified",
        evidence_tier="verified_compile",
    )


def test_two_verified_rewrites_of_one_proof_pick_a_winner_instead_of_annihilating():
    """The pathology this rule exists to prevent.

    golf and idiom fire on the same proofs and both collapse to `proof-golf` — there is no
    idiom concern family. Under a pure equal-tier conflict rule, every proof where BOTH
    succeed published nothing, so the system got worse the more of its checkers worked.
    Two verified edits are alternatives: each compiles, so each proves itself achievable.
    """

    short = _verified("candidate:a", "Use grind.", "theorem Foo.bar : True := by grind")
    long = _verified("candidate:b", "Use simp with lemmas.",
                     "theorem Foo.bar : True := by simp [a, b, c, d, e, f]")
    merged, conflicts, report = merge_findings([short, long])

    assert conflicts == [], "verified alternatives are not a contradiction"
    published = [item for item in merged if item.admission == "published"]
    assert len(published) == 1, "exactly one alternative is published"
    assert published[0].finding_id == short.finding_id, "the smaller edit is preferred"
    assert report["alternatives_not_selected"] == 1

    demoted = [item for item in merged if item.admission == "diagnostic"]
    assert "alternative verified edit was selected" in demoted[0].admission_reason


def test_unverified_disagreement_is_still_a_conflict():
    """Two prose claims that disagree, with nothing to choose between them, stay undecided."""

    a = _published(_candidate("candidate:a", requested="Delete the helper."))
    b = _published(_candidate("candidate:b", requested="Keep the helper but rename it."))
    _merged, conflicts, report = merge_findings([a, b])
    assert len(conflicts) == 1
    assert report["alternatives_not_selected"] == 0
    assert "no verified edit to choose between them" in conflicts[0].rationale


def test_a_verified_finding_without_an_edit_is_not_an_alternative():
    """The warrant is the edit. A `verified_compile` tier with no edit proves nothing about
    a specific replacement, so it cannot be one of two competing implementations."""

    from src.mathlib_review.review.merge import _is_verified_proposal

    edit_backed = _verified("candidate:a", "Use grind.", "theorem Foo.bar : True := by grind")
    tier_only = _published(_candidate("candidate:b"), tier="verified_compile")
    assert _is_verified_proposal(edit_backed)
    assert not _is_verified_proposal(tier_only)


def test_demotion_reasons_distinguish_their_three_causes():
    """They used to share one message, so a truncated finding, a losing alternative and an
    unresolved conflict were indistinguishable in the output."""

    weak = _published(_candidate("candidate:w", requested="Delete it."))
    strong = _published(_candidate("candidate:s", requested="Rename it."),
                        tier="verified_compile")
    merged, _conflicts, _report = merge_findings([weak, strong])
    demoted = [item for item in merged if item.admission == "diagnostic"]
    assert demoted and "better-warranted" in demoted[0].admission_reason


def test_non_strict_ingestion_preserves_each_candidate_s_ordinal():
    """`ordinal` is the candidate's index in the response it came from, strict or not.

    The non-strict path validates each candidate by recursing on a one-element list, where
    the loop index is always 0 — so every candidate in a batch used to be sealed with
    `ordinal=0`. Finalization joins verification artifacts on `(work_unit_id, ordinal)`, so
    a collapsed ordinal lets one candidate's compile warrant admit a sibling the compiler
    never saw, and `candidate_id` loses the field that disambiguates it.
    """

    from src.mathlib_review.review.candidates import candidates_from_response

    response = {"candidates": [_raw(), _raw(claim="Foo.bar is also shadowed elsewhere.")]}
    accepted, rejected = candidates_from_response(_unit(), response, strict=False)
    assert not rejected
    assert [item.ordinal for item in accepted] == [0, 1]
    assert len({item.candidate_id for item in accepted}) == 2


def test_a_rejected_candidate_does_not_renumber_its_successors():
    """Ordinals index the response, so a gap is the correct record of a dropped candidate."""

    from src.mathlib_review.review.candidates import candidates_from_response

    response = {"candidates": [_raw(), _raw(subject="Wrong.subject"), _raw(claim="Foo.bar has a third problem.")]}
    accepted, rejected = candidates_from_response(_unit(), response, strict=False)
    assert [item.ordinal for item in accepted] == [0, 2]
    assert [item.ordinal for item in rejected] == [1]
