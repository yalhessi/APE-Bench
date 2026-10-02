"""Design D2, `structured_critic`: structured disagreement on D1's ledger, as a chained stage.

Pinned: the critic reads its stage from a finished `structured` run's `ledgers.jsonl` row and is
refused a PR without one; its prompt renders the first stage's ledger and filed changes; every
cell gets a position that fits the first stage's verdict (`overturn`/`concede` where nothing was
filed, `confirm`/`refute`/`undecided` where something was), an `overturn` carries a finding and
missing cells are pressed then `unstated`; the critic's findings go through D1's verification;
and the output is the union -- the first stage's findings carried with the critic's position on
each, plus the critic's, labelled -- in which a `refute` removes nothing.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from ape.tasks.base import get_task_class
from ape.tasks.models import WorkspaceInfo
from ape.tasks.lean_tasks.formal_math.review import DESIGNS
from ape.tasks.lean_tasks.formal_math.review.candidates import UNSTATED_VERDICT
from ape.tasks.lean_tasks.formal_math.review.structured import (
    CONCERNS, LEDGER_PRESSES, REFUTED, VERIFIED, StructuredFinding,
)
from ape.tasks.lean_tasks.formal_math.review.structured_critic import (
    CRITIC_TASK_TYPE, STAGE_1, STAGE_2, Rebuttal, StructuredCriticData, StructuredCriticResult,
    StructuredCriticTask,
)
from tests.datasets.test_pr_review_v5_structured import DECLARATIONS, _fake_checks, _finding

NAMES = [row["name"] for row in DECLARATIONS]


def _stage_cells(would_change=()):
    cells = []
    for name in NAMES:
        for concern in CONCERNS:
            verdict = "would_change" if (name, concern) in would_change else "no_issue"
            cells.append({"declaration": name, "concern": concern, "verdict": verdict,
                          "reason": f"stage 1 checked {concern}",
                          **({"outcome": VERIFIED} if verdict == "would_change" else {})})
    return cells


def _stage_finding(**overrides):
    row = {"anchor": {"path": "Mathlib/A.lean", "line_start": 10, "line_end": 10},
           "severity": "blocking", "claim": "foo_bar's proof is three lines of simp.",
           "suggested_fix": "simp [bar]", "concern_family": "other", "issue_kind": "style_norm_violation",
           "evidence": None, "verified": True, "confidence": None,
           "declaration": "Submodule.foo_bar", "concern": "proof", "concern_label": "proof",
           "verification": VERIFIED}
    row.update(overrides)
    return row


STAGE = {"run_name": "probe_dev_structured_rep1",
         "ledger": _stage_cells({("Submodule.foo_bar", "proof")}),
         "findings": [_stage_finding()],
         "refuted": [{"declaration": "Submodule.baz", "concern": "library", "claim": "baz duplicates X.",
                      "evidence": [{"check": "duplicate_of", "answer": "no declaration of 'X'"}]}]}


def _data(**overrides):
    payload = dict(
        task_id="d2-1", pr_number=33337, pr_title="chore: rename lemmas", pr_description="A description.",
        diff="--- a/Mathlib/A.lean\n+++ b/Mathlib/A.lean\n", changed_files=["Mathlib/A.lean"],
        episode_id="ep:33337", invocation_id="ep:33337#solo_agent", declarations=list(DECLARATIONS),
        stage=STAGE, target_workspace=WorkspaceInfo(name="target", commit_hash="c" * 40, repo_url="x"),
    )
    payload.update(overrides)
    return StructuredCriticData(**payload)


def _task(**data_overrides):
    import logging

    from ape.scaffolds.ape_agent.config import ApeAgentConfig

    config = ApeAgentConfig()
    task_config = StructuredCriticTask.task_config_class(
        filing_bar="request", review_notes=True, notes_form="per_object_family",
        user_prompt="v2", finding_budget=40)
    config = config.model_copy(update={"task_config": task_config}, deep=True)
    task = StructuredCriticTask(_data(**data_overrides), config)
    task.logger = logging.getLogger("critic-test")
    task.termination_callback = None
    return task


def _rebuttals(positions=None):
    """Every cell conceded or confirmed, except the (declaration, concern) pairs in `positions`."""

    positions = positions or {}
    rows = []
    for cell in STAGE["ledger"]:
        key = (cell["declaration"], cell["concern"])
        default = "confirm" if cell["verdict"] == "would_change" else "concede"
        rows.append({"declaration": cell["declaration"], "concerns": [cell["concern"]],
                     "reason": f"critic: {cell['concern']} re-checked", "position": positions.get(key, default)})
    return rows


def _submit(task, rebuttals, findings=()):
    return asyncio.run(task._submit_critique([Rebuttal(**row) for row in rebuttals],
                                             [StructuredFinding(**item) for item in findings], None, ""))


def _captured(task):
    captured = {}

    async def terminate(result):
        captured["result"] = result

    task.termination_callback = terminate
    return captured


# --- registration and the stage -------------------------------------------------------------


def test_it_is_a_registered_chained_design():
    assert CRITIC_TASK_TYPE == "lean_pr_review_v5_structured_critic"
    assert get_task_class(CRITIC_TASK_TYPE) is StructuredCriticTask
    assert DESIGNS["structured_critic"] is StructuredCriticTask
    assert StructuredCriticTask.reads_stage is True
    assert StructuredCriticResult.model_fields["design"].default == "structured_critic"
    assert {"rebuttals", "stage_run", "ledger", "refuted", "findings"} <= set(StructuredCriticResult.model_fields)


def test_the_payload_carries_the_first_stages_row_and_refuses_a_pr_without_one():
    from tests.datasets.test_pr_review_v5_structured import _graph

    dataset = SimpleNamespace(stage_input_run="probe_dev_structured_rep1")
    payload = StructuredCriticTask.design_payload(
        episode=SimpleNamespace(episode_id="ep:1"), graph=_graph(), dataset=dataset, stage=STAGE)
    assert [row["name"] for row in payload["declarations"]] == ["Ns.first", "Ns.second", "Other.x"]
    assert payload["stage"]["run_name"] == "probe_dev_structured_rep1"
    assert payload["stage"]["ledger"] == STAGE["ledger"] and payload["stage"]["findings"] == STAGE["findings"]
    line = StructuredCriticTask.describe_design_payload(payload)
    assert "12 cells, 1 would_change, 1 finding(s) filed, 1 refuted" in line and "3 declaration(s)" in line
    with pytest.raises(ValueError, match="no first-stage ledger"):
        StructuredCriticTask.design_payload(
            episode=SimpleNamespace(episode_id="ep:1"), graph=_graph(), dataset=dataset, stage=None)


# --- the prompt ------------------------------------------------------------------------------


def test_the_prompt_renders_the_first_stages_ledger_and_asks_for_disagreement():
    prompt = asyncio.run(_task().create_user_prompt())
    assert "## The first stage's ledger, and your task" in prompt
    assert "argue the opposite" in prompt and "`overturn`" in prompt and "`concede`" in prompt
    assert "- `Submodule.foo_bar`" in prompt and "proof: **would_change**" in prompt
    assert "filed (verified, blocking) at `Mathlib/A.lean:10`" in prompt
    assert "Refuted at the first stage's submission" in prompt and "baz duplicates X." in prompt
    assert "removes nothing" in prompt
    assert "## The ledger\n" not in prompt, "D1's contract is replaced, not appended to"
    assert "## The diff" in prompt, "the packet is still the solo's"


# --- positions ---------------------------------------------------------------------------------


def test_a_position_must_fit_the_first_stages_verdict():
    task = _task()
    _, refusal = task._check_rebuttals(
        [Rebuttal(**row) for row in _rebuttals({("Submodule.foo_bar", "proof"): "concede"})], [])
    assert "one of ['confirm', 'refute', 'undecided'], not 'concede'" in refusal
    _, refusal = task._check_rebuttals(
        [Rebuttal(**row) for row in _rebuttals({("Submodule.baz", "name"): "refute"})], [])
    assert "one of ['overturn', 'concede'], not 'refute'" in refusal


def test_an_overturn_needs_a_finding_and_a_finding_needs_an_overturn():
    task = _task()
    _, refusal = task._check_rebuttals(
        [Rebuttal(**row) for row in _rebuttals({("Submodule.baz", "name"): "overturn"})], [])
    assert "`overturn` with no finding" in refusal
    _, refusal = task._check_rebuttals(
        [Rebuttal(**row) for row in _rebuttals()],
        [StructuredFinding(**_finding(declaration="Submodule.baz", concern="name", claim="baz is misnamed."))])
    assert "not `overturn`" in refusal
    cells, refusal = task._check_rebuttals(
        [Rebuttal(**row) for row in _rebuttals({("Submodule.baz", "name"): "overturn"})],
        [StructuredFinding(**_finding(declaration="Submodule.baz", concern="name", claim="baz is misnamed."))])
    assert refusal is None
    cell = next(c for c in cells if c["declaration"] == "Submodule.baz" and c["concern"] == "name")
    assert cell["verdict"] == "no_issue" and cell["position"] == "overturn"


def test_missing_cells_are_pressed_then_recorded_unstated():
    task = _task()
    rows = [Rebuttal(**row) for row in _rebuttals()[:-1]]
    for attempt in range(1, LEDGER_PRESSES + 1):
        cells, refusal = task._check_rebuttals(rows, [])
        assert cells is None and f"(attempt {attempt} of {LEDGER_PRESSES})" in refusal
    cells, refusal = task._check_rebuttals(rows, [])
    assert refusal is None
    assert cells[-1]["position"] == UNSTATED_VERDICT and cells[-1]["verdict"] == "no_issue"


def test_a_row_may_cover_several_cells_except_an_overturn():
    task = _task()
    rows = [Rebuttal(declaration=name, concerns=[c for c in CONCERNS if not (name == "Submodule.foo_bar" and c == "proof")],
                     reason="all conceded", position="concede") for name in NAMES]
    rows.append(Rebuttal(declaration="Submodule.foo_bar", concerns=["proof"], reason="checked", position="confirm"))
    cells, refusal = task._check_rebuttals(rows, [])
    assert refusal is None and len(cells) == 12
    rows[0] = Rebuttal(declaration="Submodule.baz", concerns=["name", "docstring"], reason="r", position="overturn")
    _, refusal = task._check_rebuttals(rows, [])
    assert "exactly one concern" in refusal


# --- the union ---------------------------------------------------------------------------------


def test_the_union_carries_the_first_stages_findings_with_the_critics_position_and_adds_the_critics(monkeypatch):
    task = _task()
    _fake_checks(task, monkeypatch, compile_outcome=VERIFIED)
    captured = _captured(task)
    new = _finding(declaration="Submodule.baz", concern="name", claim="baz is misnamed.",
                   suggested_fix="rename", rename_to="Submodule.quux", severity="blocking")
    out = _submit(task, _rebuttals({("Submodule.baz", "name"): "overturn",
                                    ("Submodule.foo_bar", "proof"): "refute"}), [new])
    assert out["evaluation_result"].success, out
    result = captured["result"]
    assert isinstance(result, StructuredCriticResult) and result.stage_run == "probe_dev_structured_rep1"
    carried = next(f for f in result.findings if f["stage"] == STAGE_1)
    assert carried["claim"] == "foo_bar's proof is three lines of simp."
    assert carried["critic"] == "refute" and carried["agreed"] is False, "a refute is a label; the finding stays"
    assert carried["verified"] is True and carried["severity"] == "blocking", "carried as it was"
    added = next(f for f in result.findings if f["stage"] == STAGE_2)
    assert added["declaration"] == "Submodule.baz" and added["critic"] == "overturn" and added["agreed"] is False
    assert added["verification"] == "unverified" and added["severity"] == "advisory", (
        "the critic's change went through the same verification: a rename is unverifiable")
    assert len(result.findings) == 2
    rebuttal = next(r for r in result.rebuttals if r["declaration"] == "Submodule.foo_bar" and r["concern"] == "proof")
    assert rebuttal == {"declaration": "Submodule.foo_bar", "concern": "proof", "verdict": "would_change",
                        "position": "refute", "reason": "critic: proof re-checked"}
    cell = next(c for c in result.ledger if c["declaration"] == "Submodule.baz" and c["concern"] == "name")
    assert cell["position"] == "overturn" and cell["outcome"] == "unverified"


def test_a_confirmed_first_stage_finding_is_labelled_agreed():
    task = _task()
    captured = _captured(task)
    out = _submit(task, _rebuttals())
    assert out["evaluation_result"].success
    [carried] = captured["result"].findings
    assert carried["critic"] == "confirm" and carried["agreed"] is True and carried["stages"] == [STAGE_1]


def test_the_critics_refuted_change_is_handed_back_then_recorded_and_not_in_the_union(monkeypatch):
    task = _task()
    _fake_checks(task, monkeypatch, compile_outcome=REFUTED)
    captured = _captured(task)
    new = _finding(declaration="Submodule.baz", concern="proof", claim="baz's proof can be `rfl`.",
                   edit={"declaration_name": "Submodule.baz", "new_declaration": "lemma baz : True := rfl"})
    rebuttals = _rebuttals({("Submodule.baz", "proof"): "overturn"})
    out = _submit(task, rebuttals, [new])
    assert not out["evaluation_result"].success and "contradicted by the tools" in out["evaluation_result"].message
    task._refutation_presses = LEDGER_PRESSES
    out = _submit(task, rebuttals, [new])
    assert out["evaluation_result"].success
    result = captured["result"]
    assert [f["stage"] for f in result.findings] == [STAGE_1]
    assert result.refuted[0]["declaration"] == "Submodule.baz"


def test_two_file_level_findings_at_one_site_and_concern_fold_into_one_carrying_both_stages(monkeypatch):
    stage = {**STAGE, "findings": STAGE["findings"] + [_stage_finding(
        declaration="Mathlib/A.lean", concern="docstring", concern_label="docstring",
        anchor={"path": "Mathlib/A.lean", "line_start": 1, "line_end": 1},
        claim="The module doc names the wrong file.", suggested_fix="Name this file.",
        verified=False, verification="unverified", severity="advisory")]}
    task = _task(stage=stage)
    _fake_checks(task, monkeypatch)
    captured = _captured(task)
    duplicate = _finding(declaration="Mathlib/A.lean", concern="docstring", line_start=1,
                         claim="The module docstring refers to another file.", suggested_fix="Fix the module doc.")
    out = _submit(task, _rebuttals(), [duplicate])
    assert out["evaluation_result"].success
    file_level = [f for f in captured["result"].findings if f["declaration"] == "Mathlib/A.lean"]
    assert len(file_level) == 1 and file_level[0]["stages"] == [STAGE_2, STAGE_1][::-1] or \
        file_level[0]["stages"] == sorted([STAGE_1, STAGE_2])
    assert file_level[0]["claim"] == "The module doc names the wrong file.", "the first stage's wording is kept"
    assert file_level[0]["agreed"] is True


# --- the stage input end to end through the runner's hooks -------------------------------------


def test_the_runner_builds_the_critics_payload_from_the_stage_rows():
    from pathlib import Path

    from src.mathlib_review.review.runner import V5DatasetConfig, _solo_task_data
    from tests.datasets.test_pr_review_v5_designs import _agenda, _episode
    from tests.datasets.test_pr_review_v5_structured import _graph

    dataset = V5DatasetConfig(release=Path("rel"), modification_inventory=Path("inv"), routing_mode="solo",
                              design="structured_critic", stage_input_run="probe_dev_structured_rep1")
    graph = _graph()
    graph.episode_id = "ep:33337"
    [payload] = _solo_task_data(_agenda([33337]), [_episode(33337)], dataset, {"ep:33337": "2026-01-01T00:00:00Z"},
                                Path("trace.jsonl"), graphs=[graph], stage_rows={"ep:33337": STAGE})
    assert payload["task_type"] == CRITIC_TASK_TYPE and payload["task_id"] == "pr5structured_critic_ep_33337"
    assert payload["stage"]["run_name"] == "probe_dev_structured_rep1"
    assert [row["name"] for row in payload["declarations"]] == ["Ns.first", "Ns.second", "Other.x"]
    with pytest.raises(ValueError, match="no first-stage ledger"):
        _solo_task_data(_agenda([33337]), [_episode(33337)], dataset, {}, Path("t"), graphs=[graph], stage_rows={})
