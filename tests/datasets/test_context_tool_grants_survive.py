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
