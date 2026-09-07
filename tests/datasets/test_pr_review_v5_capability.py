"""Two axes, because scope alone never explained the failures.

PR 33117 is the case: the lead *did* recognise the duplicated `fun_*` family — it is in the
run's own assessments — and the specialist still failed. Knowing thirteen lemmas are
hand-written duplicates does not tell you `@[to_fun]` generates them, and nothing in the
contract lets one candidate carry an import, attributes and deletions together. More context
would not have fixed it.

This table is derived from gold and is strictly evaluation-side. The test that matters most
is the last one: none of it may reach a prompt.
"""

from __future__ import annotations

from src.datasets.pr_review_v5.obligation_capability import (
    CAPABILITIES, CLASSIFICATION, SCOPES, cross_tab, report,
)


def test_every_row_is_classified_on_both_axes():
    assert CLASSIFICATION
    for row in CLASSIFICATION:
        assert row.scope in SCOPES
        assert row.capability in CAPABILITIES
        # The reasoning is the artifact; a bare label cannot be disagreed with.
        assert len(row.why) > 80, row.obligation


def test_rows_are_unique():
    ids = [r.obligation for r in CLASSIFICATION]
    assert len(ids) == len(set(ids))


def test_a_quarter_of_the_set_cannot_be_resolved_without_coordinated_edits():
    """The quantified case for a multi-edit candidate. These are unreachable *as
    resolutions* by a reviewer confined to one work unit with one edit, however well briefed
    — which is why context alone was the wrong bet."""

    counts = report()
    assert counts["needs_coordinated_edit"] >= 5
    assert counts["needs_coordinated_edit"] / counts["obligations"] >= 0.25


def test_family_scope_and_coordinated_capability_travel_together():
    """Almost perfectly correlated, which is why the two axes decompose the work cleanly:
    seeing the family and being able to edit it are the same requirement in practice."""

    table = cross_tab()
    assert table["family"]["coordinated"] >= 5
    assert table["site"]["coordinated"] == 0


def test_conventions_are_a_retrieval_problem_and_nothing_else():
    table = cross_tab()
    assert table["convention"]["retrieval"] == 3
    assert sum(v for k, v in table["convention"].items() if k != "retrieval") == 0


def test_the_largest_single_cell_is_local_design_work():
    """site x transformation: the reviewer already sees everything it needs and must design
    the change. This is the under-reach failure, and it is a prompting problem rather than an
    architecture one."""

    table = cross_tab()
    biggest = max(
        ((s, c, n) for s, row in table.items() for c, n in row.items()),
        key=lambda item: item[2])
    assert biggest[:2] == ("site", "transformation")


def test_none_of_this_reaches_a_prompt():
    """It is derived from gold. A routing artifact or an instruction that quoted it would be
    the same class of leak as the three found in the arm prompts."""

    import json

    from src.datasets.pr_review_v4.contracts import prompt_leaks
    from src.datasets.pr_review_v4.render_focused import (
        SUBMISSION_CONTRACT, focused_system_prompt,
    )
    from src.datasets.pr_review_v5.arms import specs_by_arm_id

    derived = [row.why for row in CLASSIFICATION]
    texts = [SUBMISSION_CONTRACT] + [
        focused_system_prompt(spec) for spec in specs_by_arm_id().values()]
    for text in texts:
        assert not prompt_leaks(text, derived)
