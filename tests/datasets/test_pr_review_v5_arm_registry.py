"""The v5 specialist set: what it covers, and the two limits it exists to remove.

**Eligibility.** v4 schedules proof_golf and proof_idiom on `modified` proofs only, reasoning
that a new proof "is not a simplification *of* anything". Measured on the medium smoke set,
all 22 gold change targets in PRs 33066/33098 have lifecycle `added`, and 33098's gold is
dominated by proof-simplification asks — so both proof arms were ineligible at every site
where gold asked for exactly what they do.

**Coverage.** The four v4 checkers own proof-golf, duplication and generality. The gold none
of them could own was three `encard_` renames, a docstring typo, a section-formatting
request, and a build break — naming, docs, style and correctness respectively.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.mathlib_review.agenda.focused_specs import default_specs
from src.mathlib_review.io import load_jsonl
from src.mathlib_review.schema import ModificationRecord
from src.mathlib_review.agenda.arms import (
    CHECKABLE_ARMS,
    GENERALIST_ARM_ID,
    default_arms,
    v5_specs,
)

INVENTORY = Path(
    "inputs/pr_review_v4/treatments/systematic-opportunities-v2-medium/derived/"
    "modification_inventory.jsonl"
)
RELEASE = Path("inputs/pr_review_v4/releases/dev-medium-0.3.0")


def _spec(spec_id):
    return next(s for s in v5_specs() if s.spec_id == spec_id)


# --------------------------------------------------------------------------------------
# eligibility
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("spec_id", ["proof_golf", "proof_idiom"])
def test_the_proof_arms_run_on_added_declarations(spec_id):
    assert _spec(spec_id).lifecycles == frozenset({"added", "modified"})
    assert default_specs()[0].lifecycles == frozenset({"modified"}), (
        "v4 must stay as it was; v5 widens its own copy"
    )


def test_widening_changes_the_spec_identity():
    """`source_sha256` derives from `identity()`, so a v5 run can never be confused with a
    v4 one that shared a spec_id."""

    v4 = {s.spec_id: s for s in default_specs()}
    v5 = {s.spec_id: s for s in v5_specs()}
    assert v5["proof_golf"].source_sha256 != v4["proof_golf"].source_sha256
    assert v5["proof_golf"].spec_version.endswith("-v5")


def test_the_proof_arms_now_reach_the_gold_sites():
    """The measurement that motivated the change: under v4's rule these were 0."""

    modifications = load_jsonl(INVENTORY, ModificationRecord)
    added_proofs = [
        item for item in modifications
        if item.lifecycle == "added"
        and any(delta.component == "proof" for delta in item.component_deltas)
    ]
    assert added_proofs, "the inventory has no added proofs; the premise is wrong"
    for spec_id in ("proof_golf", "proof_idiom"):
        spec = _spec(spec_id)
        reached = sum(1 for item in added_proofs if spec.applies_to(item))
        assert reached > 0, f"{spec_id} still cannot see an added proof"
        v4_spec = next(s for s in default_specs() if s.spec_id == spec_id)
        assert not any(v4_spec.applies_to(item) for item in added_proofs), (
            "v4's rule should still exclude them — otherwise this test proves nothing"
        )


def test_the_proof_arms_still_require_a_proof_component():
    """Widening the lifecycle must not widen the component: a target with no proof has
    nothing for these arms to shorten."""

    for spec_id in ("proof_golf", "proof_idiom"):
        assert _spec(spec_id).component == "proof"


# --------------------------------------------------------------------------------------
# coverage
# --------------------------------------------------------------------------------------

def test_every_concern_family_in_the_gold_vocabulary_has_an_owner():
    """The generalist is the control, not the owner. A family with no specialist is a family
    only one broad pass ever looks for."""

    owned = {spec.concern_family for spec in v5_specs()}
    for family in ("proof-golf", "duplication", "generalization", "naming",
                   "documentation", "style", "correctness"):
        assert family in owned, f"no specialist owns {family}"


def test_the_new_arms_declare_a_checkable_issue_kind():
    from typing import get_args

    from src.mathlib_review.schema import ConcernFamily, IssueKind

    families, kinds = set(get_args(ConcernFamily)), set(get_args(IssueKind))
    for spec in v5_specs():
        assert spec.concern_family in families, spec.spec_id
        assert spec.issue_kind in kinds, spec.spec_id


def test_docs_and_style_are_separate_arms():
    """The rendered submission contract names ONE concern_family, so a combined arm would
    file its style findings as documentation — and the judge gates on concern kind."""

    assert _spec("docs").concern_family == "documentation"
    assert _spec("style").concern_family == "style"


def test_every_arm_has_a_prompt():
    from ape.tasks.lean_tasks.formal_math.review.focused_prompts import FOCUSED_PROMPTS

    for spec in v5_specs():
        assert spec.spec_id in FOCUSED_PROMPTS, spec.spec_id
        tools, system, _user = FOCUSED_PROMPTS[spec.spec_id]
        assert tools and system.strip()


def test_each_arm_prompt_refuses_the_other_concerns():
    """An arm that drifts has its findings rejected at submission, so the prompt has to say
    what it is not for."""

    from ape.tasks.lean_tasks.formal_math.review.focused_prompts import FOCUSED_PROMPTS

    for spec_id in ("naming", "docs", "style", "api_reuse", "correctness"):
        _tools, system, _user = FOCUSED_PROMPTS[spec_id]
        assert "only job" in system, spec_id
        assert "ignore" in system.lower(), spec_id


def test_the_concern_gate_covers_every_specialist():
    from ape.tasks.lean_tasks.formal_math.review.arm import EXPECTED_CONCERN_BY_ARM

    for spec in v5_specs():
        assert spec.spec_id in EXPECTED_CONCERN_BY_ARM, spec.spec_id
        assert spec.concern_family in EXPECTED_CONCERN_BY_ARM[spec.spec_id], spec.spec_id
    assert GENERALIST_ARM_ID not in EXPECTED_CONCERN_BY_ARM


# --------------------------------------------------------------------------------------
# how a finding is warranted
# --------------------------------------------------------------------------------------

def test_only_compile_settled_arms_take_the_verification_gate():
    """A naming or docstring claim cannot carry a compile artifact — renaming breaks call
    sites, a typo fix proves nothing by elaborating — so routing those arms to the gate
    would drop every finding they ever make for lacking a warrant their concern cannot
    produce."""

    assert CHECKABLE_ARMS == {"proof_golf", "proof_idiom", "duplication", "generality",
                              "api_reuse", "correctness"}
    for spec_id in ("naming", "docs", "style"):
        assert spec_id not in CHECKABLE_ARMS


def test_non_checkable_arms_are_routed_to_the_evidence_chain():
    import inspect

    from src.mathlib_review.review import finalize

    source = inspect.getsource(finalize.ingest_responses)
    assert "CHECKABLE_ARMS" in source


def test_arm_attribution_survives_the_evidence_route():
    """A naming candidate takes the generalist path but carries a spec_id, and
    `finding_from_candidate` reads the arm from that — so it is still filed as focused."""

    from src.mathlib_review.review.merge import finding_from_candidate
    import inspect

    assert "spec_id" in inspect.getsource(finding_from_candidate)


def test_the_registry_is_still_a_row_plus_a_prompt():
    arms = default_arms("candidate-prompt/12")
    assert len(arms) == len(v5_specs()) + 1  # + the generalist
    assert [a.arm_id for a in arms][0] == GENERALIST_ARM_ID


# --- the retrieval grant ----------------------------------------------------------------
#
# Uniform until smoke4 measured what an arm does when handed four retrieval tools: it reaches
# for the cheapest identifier lookup regardless of the question. 106 `declaration_search`
# calls run-wide, 50 from `family_design` alone — an arm whose question is the shape of a
# group, which no name lookup answers, and which returned nothing from eleven invocations.


def test_every_arm_keeps_lean_verify_edit():
    """The one tool no arm may lose.

    It is registered by the shared review base for *every* review task, and it is what turns
    a suggestion into a checked one: 87 of its 100 calls on smoke4 carried a real edit. A
    grant table is exactly the kind of change that quietly drops a tool from one row, so the
    guarantee is asserted rather than left to review.
    """

    from src.mathlib_review.agenda.arms import resolve_context_tools

    for arm in default_arms("v4-renderer/1"):
        assert "lean_verify_edit" in resolve_context_tools(arm), arm.arm_id


def test_family_design_loses_the_identifier_lookup_it_wasted():
    """`declaration_search` returns `X is declared in file Y` and nothing else.

    On PR 33117 the maintainer asked for `@[to_fun]` to generate the thirteen hand-written
    `fun_*` lemmas. `Mathlib/Tactic/ToFun.lean` was in the arm's own base workspace, its
    module docstring states exactly what the attribute does, and `content_search` finds it.
    The arm spent its retrieval budget on name lookups instead and abstained.
    """

    from src.mathlib_review.agenda.arms import resolve_context_tools

    arms = {arm.arm_id: arm for arm in default_arms("v4-renderer/1")}
    assert "declaration_search" not in resolve_context_tools(arms["family_design"])


def test_the_convention_arms_keep_the_review_corpus():
    """Naming, docs and style ask questions the code corpus answers wrongly.

    Measured: `coe_` outnumbers `toLinearMap_` 4,707 to 50 and flat names outnumber dot
    notation 22,345 to 2,359, so frequency argues *against* the maintainer in both naming
    cases this release scores. The review corpus states them.
    """

    from src.mathlib_review.agenda.arms import resolve_context_tools

    arms = {arm.arm_id: arm for arm in default_arms("v4-renderer/1")}
    for arm_id in ("naming", "docs", "style"):
        granted = resolve_context_tools(arms[arm_id])
        assert "precedent_search" in granted, arm_id


def test_the_generalist_grant_is_untouched():
    """It is the control. Narrowing the specialists and the control together would move both
    sides of the comparison at once, and neither could then be read off the result."""

    from src.mathlib_review.schema.review import CONTEXT_TOOLS
    from src.mathlib_review.agenda.arms import resolve_context_tools

    generalist = next(a for a in default_arms("v4-renderer/1")
                      if a.arm_id == GENERALIST_ARM_ID)
    assert sorted(resolve_context_tools(generalist)) == sorted(CONTEXT_TOOLS)
