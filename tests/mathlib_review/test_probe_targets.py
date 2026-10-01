"""A matcher input's target must not say which harness wrote it.

On the harness comparison (2026-10-01) the same location arrived three ways: `target/Mathlib/...`
from APE-Agent, the absolute store path from Claude Code, `Mathlib/...` from Claude's packets.
"""

import pytest

from src.mathlib_review.analysis.probes import repo_target

STORE = "/research/projects/proofedit/ya475/APE-Bench/data/code_execute/repos/mathlib4/workspaces"


@pytest.mark.parametrize("written", [
    "target/Mathlib/Algebra/Group/Subgroup/Pointwise.lean:13",
    f"{STORE}/3ed2ddca3d874aa6644072e61ec97bfef3ce8ae3+8fabcf9c1318/Mathlib/Algebra/Group/Subgroup/Pointwise.lean:13",
    "/x/.ape/runs/r/tasks/t/samples/0/attempts/attempt_1/workspaces/target/Mathlib/Algebra/Group/Subgroup/Pointwise.lean:13",
    "Mathlib/Algebra/Group/Subgroup/Pointwise.lean:13",
])
def test_every_spelling_of_one_location_reads_the_same(written):
    assert repo_target(written) == "Mathlib/Algebra/Group/Subgroup/Pointwise.lean:13"


def test_a_target_with_no_path_is_left_alone():
    assert repo_target("PresheafOfModulesOfCommRing.map") == "PresheafOfModulesOfCommRing.map"
    assert repo_target(None) is None
