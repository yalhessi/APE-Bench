"""A tool the registry grants must actually reach the arm.

`arms._grant_for` returns `[name for name in CONTEXT_TOOLS if name in granted]`, so
`schema/review.py::CONTEXT_TOOLS` is a second closed vocabulary sitting behind the registry. A
tool missing from it is dropped from every grant with no error, no warning and no trace row --
the registry names it, the registrar exists, the arm never sees it.

That happened: `naming_norm` was added to the naming arm's registry row and to `_REGISTRARS`,
and left out of `CONTEXT_TOOLS`. The next paid run (33337 rep14, $1.11) came back with the arm
silent and zero `naming_norm` trace rows, which reads exactly like "the new contract changed
nothing" and was in fact "the tool was never registered". The same shape as this repository's
other silent-vocabulary failures: the concern-label mismatch that made the docs arm unmeasurable
for its whole life, and the retrieval gate's closed `Literal`.

So the three places are pinned against each other here rather than trusted to stay in step.
"""

from __future__ import annotations

from ape.tasks.lean_tasks.formal_math.review.context_tools import _REGISTRARS
from src.mathlib_review.agenda.arms import _grant_for
from src.mathlib_review.agenda.registry import ARM_DEFINITIONS, UNIVERSAL_CONTEXT_TOOLS
from src.mathlib_review.schema.review import CONTEXT_TOOLS


def test_every_granted_tool_survives_the_grant():
    """The bug this file exists for: registry -> _grant_for must lose nothing."""

    dropped = [
        (arm.arm_id, tool)
        for arm in ARM_DEFINITIONS
        for tool in arm.context_tools
        if tool not in _grant_for(arm.arm_id)
    ]
    assert dropped == [], (
        f"{dropped} are granted by the registry and filtered out by CONTEXT_TOOLS; the arm "
        "would run without them and nothing would say so")


def test_every_granted_tool_has_a_registrar():
    """Surviving the grant is not enough: something must actually register the MCP tool."""

    granted = {tool for arm in ARM_DEFINITIONS for tool in _grant_for(arm.arm_id)}
    missing = sorted(granted - set(_REGISTRARS) - set(UNIVERSAL_CONTEXT_TOOLS))
    assert missing == [], f"{missing} are granted but no registrar defines them"


def test_the_vocabulary_covers_the_registry_and_the_registrars():
    """CONTEXT_TOOLS is the vocabulary; nothing may be named outside it."""

    named = {tool for arm in ARM_DEFINITIONS for tool in arm.context_tools}
    assert named <= set(CONTEXT_TOOLS), sorted(named - set(CONTEXT_TOOLS))
    assert set(_REGISTRARS) <= set(CONTEXT_TOOLS), sorted(set(_REGISTRARS) - set(CONTEXT_TOOLS))


def test_the_naming_arm_can_reach_the_norm_tool():
    """The specific grant rep14 was supposed to exercise."""

    assert "naming_norm" in _grant_for("naming")
    assert "naming_norm" in _REGISTRARS


# --- refused, never dropped (2026-10-06) ---------------------------------------------------
#
# The tests above catch a registry that names a tool the vocabulary lacks. The places below are
# where a grant is *built*, and each used to filter an unknown name out in silence. Each now
# refuses it, naming it, at plan time or before the conversation starts.

import pytest


def test_the_arm_grant_refuses_a_tool_outside_the_vocabulary(monkeypatch):
    import src.mathlib_review.agenda.arms as arms

    monkeypatch.setattr(arms, "context_grants", lambda: {"naming": ("naming_norm", "nmaing_norm")})
    with pytest.raises(ValueError, match="nmaing_norm"):
        arms._grant_for("naming")


def test_solo_context_tools_refuses_a_misspelled_tool():
    from src.mathlib_review.review.runner import V5DatasetConfig

    fields = V5DatasetConfig.model_fields
    assert "solo_context_tools" in fields
    with pytest.raises(ValueError, match="precedent_serach"):
        V5DatasetConfig._known_tools_only(["zulip_search", "precedent_serach"])
    assert V5DatasetConfig._known_tools_only(["zulip_search"]) == ["zulip_search"]


def test_registration_refuses_a_granted_tool_with_no_registrar(tmp_path):
    from ape.tasks.lean_tasks.formal_math.review.arm import ARM_TASK_TYPE, ReviewArmData
    from ape.tasks.lean_tasks.formal_math.review.base import BasePRReviewTask
    from ape.tasks.lean_tasks.formal_math.review.context_tools import register_context_tools
    from ape.tasks.models import WorkspaceInfo

    # The arms' real data model, built the way `review/toolbox.py` builds its stand-in.
    task = BasePRReviewTask.__new__(BasePRReviewTask)
    task.data = ReviewArmData(
        task_type=ARM_TASK_TYPE, task_id="t", pr_number=1, diff="", episode_id="e",
        target_workspace=WorkspaceInfo(name="mathlib4", path=tmp_path, commit_hash="0" * 40),
        work_unit_id="wu", change_ids=[], entity_ids_by_change={}, primary_subjects_by_change={},
        rendered_system_prompt="", rendered_user_prompt="", rendered_prompt_sha256="",
        invocation_id="wu#a", arm_id="a", context_tools=["lean_verify_edit", "ghost_tool"])
    with pytest.raises(ValueError, match="ghost_tool"):
        register_context_tools(task, mcp=None)


def test_the_trace_record_accepts_every_tool_in_the_vocabulary():
    """The hand-written Literal it replaced had no `proof_profile`."""
    from src.mathlib_review.schema.review import ContextCall

    for tool in CONTEXT_TOOLS:
        ContextCall(invocation_id="wu:a#x", tool=tool, query="q")
    with pytest.raises(ValueError):
        ContextCall(invocation_id="wu:a#x", tool="ghost_tool", query="q")


def test_the_toolbox_holds_the_vocabulary_less_what_the_base_registers():
    from src.mathlib_review.review.toolbox import CONTEXT_TOOLS as TOOLBOX

    assert set(TOOLBOX) == set(CONTEXT_TOOLS) - set(UNIVERSAL_CONTEXT_TOOLS) == set(_REGISTRARS)
