"""Maintainer requests, grouped the way the maintainer made them.

An obligation is not the unit a reviewer works in: on PR33098 one comment becomes four
obligations and another becomes three. Scoring per obligation turns one request into seven
independent misses; building per obligation makes it unbuildable, because no finding in the
system can span the four sites.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.mathlib_review.analysis.request_groups import (
    CLASSIFICATION, INFORMATION_SOURCES, KNOWN_ARMS, OUTPUT_SHAPES, answerable_by, build,
    report,
)
from src.mathlib_review.analysis.obligation_capability import SCOPES

RELEASE = Path("inputs/pr_review_v4/releases/dev-medium-0.3.0")


def _groups():
    if not (RELEASE / "gold/judgments.jsonl").is_file():
        pytest.skip("no release in this checkout")
    return build(RELEASE)


def test_every_classification_uses_the_declared_vocabularies():
    """A typo in a scope or an arm id would silently drop a group from every count."""

    for row in CLASSIFICATION:
        assert row.required_scope in SCOPES, row.lead_obligation
        assert row.required_information in INFORMATION_SOURCES, row.lead_obligation
        assert row.required_output in OUTPUT_SHAPES, row.lead_obligation
        assert set(row.answerable_arm_ids) <= KNOWN_ARMS, row.lead_obligation
        assert row.why.strip(), row.lead_obligation
        # `generalist` has no concern filter, so listing it would say nothing.
        assert "generalist" not in row.answerable_arm_ids, row.lead_obligation


def test_the_grouping_covers_every_eligible_obligation_exactly_once():
    groups = _groups()
    ids = [item for group in groups for item in group.obligation_ids]
    assert len(ids) == len(set(ids)) == 40
    assert len(groups) == 35


def test_the_two_grind_families_are_the_only_multi_obligation_groups():
    """The 4+3 split of PR33098's two `grind` comments is the whole reason this unit exists."""

    groups = {group.group_id: group for group in _groups()}
    multi = {gid: g.size for gid, g in groups.items() if g.size > 1}
    assert multi == {"14f5e6d60163": 4, "f4d1ab7fb96f": 3}
    for group_id in multi:
        row = groups[group_id].classification
        assert row.required_output == "patch_set"
        assert row.required_scope == "family"
        assert "proof_idiom" in row.answerable_arm_ids


def test_no_group_is_left_unclassified():
    assert report(_groups())["unclassified"] == []


def test_the_audit_disagrees_sharply_with_the_gold_concern_labels():
    """The reason the bench must not select on labels.

    13 of PR33098's 14 obligations carry `style`, the seven `grind` requests included, so a
    label-driven selector hands `style` work that belongs to the proof arms and starves
    `family_design` entirely.
    """

    index = answerable_by(_groups())
    assert len(index["proof_idiom"]) == 9
    assert len(index["family_design"]) == 6
    assert len(index["style"]) == 3
