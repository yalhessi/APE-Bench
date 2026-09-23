"""The ledger rows are constructed, not assembled -- and the artifacts in the tree prove it.

`arm_responses.jsonl` and `delegations.jsonl` were written as five dict literals across two
files. `DelegationRecord` existed and validated **no row in the tree**: it required a
`source_sha256` nothing wrote and forbade three fields every lead row carries, so
`delegation_view` read the rows raw and said so in a comment. A model that cannot load its own
artifacts is documentation, not a contract.

These tests are the contract in the only form that means anything here: every row this
repository has ever written loads, and every row written by today's code survives the
round-trip byte for byte. They read the committed runs, so they cost nothing and they fail on
the artifacts rather than on a fixture.
"""

from __future__ import annotations

import collections
import json
from pathlib import Path

import pytest

from src.mathlib_review.io import jsonl_bytes
from src.mathlib_review.schema.review import ArmResponse, DelegationRecord

RUNS = Path("results/pr_review_v5/runs")


def _rows(name: str):
    for path in sorted(RUNS.glob(f"*/{name}")):
        for line in path.read_text(encoding="utf-8").split("\n"):
            if line.strip():
                yield path, json.loads(line)


def test_every_delegation_row_in_the_tree_round_trips_byte_for_byte():
    """All five key sets the tree holds, across 20k rows: the lead's ran and pruned shapes,
    the rule-dispatched one, and two older shapes. `row()` excludes what was never set, which
    is what keeps "never considered" (no `status` key) apart from "considered and declined"
    (`status: null`) -- flattening those would make a pruned job and an unscheduled one the
    same row."""

    rows = list(_rows("delegations.jsonl"))
    if not rows:
        pytest.skip("no committed delegation ledger in this tree")

    shapes, differing = collections.Counter(), []
    for path, row in rows:
        shapes[tuple(sorted(row))] += 1
        rebuilt = DelegationRecord.model_validate(row).row()
        # Bytes, not dicts: `turns` is an int and a float-typed usage map would rewrite it as
        # `3.0` in every historical row while comparing equal here.
        if jsonl_bytes([rebuilt]) != jsonl_bytes([row]):
            differing.append((str(path), sorted(set(rebuilt) ^ set(row)) or "values"))
    assert differing == [], differing[:5]
    assert len(shapes) >= 3, f"only {len(shapes)} shapes seen; this tree is missing runs"


#: Fields added to `ArmResponse` after rows were committed, oldest first. A committed row that
#: predates one gains it as null on the way back: the field arriving, not a drift.
_ARRIVED_LATER = ("abstention", "target_verdicts")


def test_every_arm_response_written_by_current_code_round_trips():
    """Rows that predate a field in `_ARRIVED_LATER` gain it as null, which is the field
    arriving and not a drift. Everything else round-trips unchanged."""

    rows = list(_rows("arm_responses.jsonl"))
    if not rows:
        pytest.skip("no committed arm responses in this tree")

    current, older, orphan = 0, 0, 0
    for _path, row in rows:
        if row.get("invocation_id") is None:
            # `lead_smoke4_rep2` holds exactly one: a failed job synthesised with every
            # identity field null, which reconciliation read as an orphan response. The runner
            # stopped writing them and the model refuses them.
            orphan += 1
            continue
        rebuilt = ArmResponse.model_validate(row).row()
        arrived = set(rebuilt) - set(row)
        assert arrived <= set(_ARRIVED_LATER), arrived
        assert all(rebuilt[key] is None for key in arrived)
        assert {key: rebuilt[key] for key in row} == row
        # "Current" is a row that already carries `abstention`: every builder since then.
        if "abstention" in row:
            current += 1
        else:
            older += 1
    assert current > 0 and older > 0, (current, older)
    assert orphan <= 1, orphan


def test_the_three_row_shapes_are_distinguishable():
    """Constructed, not asserted about the tree: a job that ran, one the lead declined, and one
    a rule dispatched without any lead. The middle and the last differ only by which keys exist
    at all, and that difference is the whole reason `row()` excludes unset fields."""

    common = dict(invocation_id="wu:a#naming", arm_id="naming", work_unit_id="wu:a", pr_number=1)
    ran = DelegationRecord(**common, proposal_id="p", disposition="proposed", reason="r",
                           budget_tier="standard", budget_cap=0.3, status="success",
                           wall_seconds=12.0, cost=0.04,
                           token_usage={"billed_cost": 0.04, "nominal_cost": 0.1, "turns": 7},
                           candidate_count=1, verification_artifact_count=0,
                           result_sha256="d" * 64, brief=None,
                           delivered_prompt_sha256="e" * 64, context_calls=[]).row()
    pruned = DelegationRecord(**common, proposal_id="p", disposition="pruned",
                              reason="not selected by the lead", reason_given=False,
                              budget_tier=None, budget_cap=None, status=None,
                              wall_seconds=None, cost=None, token_usage=None,
                              candidate_count=None, verification_artifact_count=None,
                              result_sha256=None, context_calls=[]).row()
    by_rule = DelegationRecord(**common, proposal_id="p", disposition="pruned",
                               reason="not selected in rules mode", budget_tier=None,
                               context_calls=[]).row()

    assert "status" in pruned and pruned["status"] is None
    assert "status" not in by_rule
    assert "reason_given" in pruned and "reason_given" not in ran
    assert ran["token_usage"]["turns"] == 7 and isinstance(ran["token_usage"]["turns"], int)


def test_no_module_writes_a_delegation_row_by_hand():
    import inspect

    from ape.tasks.lean_tasks.formal_math.review import lead
    from src.mathlib_review.review import runner

    for module in (lead, runner):
        source = inspect.getsource(module)
        assert '"schema_version": "v5-delegation1"' not in source, (
            f"{module.__name__} writes the ledger's schema version as a literal again; "
            f"construct `DelegationRecord`, which is the one place it is spelled")


def test_target_verdicts_reach_the_arm_response_row():
    """Asserted at the far end, not the near one: a verdict the arm recorded must still be on
    the row `finalize` reads after the direct-arm runner has normalised the result. A field the
    task records and a later hop does not name is dropped with the suite green -- the failure
    `abstention` had in one of three writers."""

    from types import SimpleNamespace

    from ape.tasks.lean_tasks.formal_math.review.arm import ReviewArmResult
    from src.mathlib_review.review.runner import _responses_from_results

    verdicts = [{"change_id": "change:a", "verdict": "no_issue", "reason": "checked it"}]
    result = ReviewArmResult(
        task_id="pr5_test", task_type="lean_pr_review_v5_arm", global_index="0",
        success=True, score=1.0, pr_number=33098, work_unit_id="wu:abc",
        rendered_prompt_sha256="a" * 64, candidates=[], verification_artifacts=[],
        findings=[], review_message="", invocation_id="wu:abc#naming", arm_id="naming",
        spec_id="naming", abstention={"reason": "per_target_verdicts", "detail": "1 no_issue"},
        target_verdicts=verdicts,
    )
    (row,) = _responses_from_results(SimpleNamespace(task_results=[result]), mode="fanout")
    assert row["target_verdicts"] == verdicts
    assert ArmResponse.model_validate(row).row() == row
