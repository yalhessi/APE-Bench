"""A claim's identity across runs, and the measurement that chose it.

`finding_id` identifies one finding's exact wording, which is what a merge needs and what an
adjudication cannot use: a label is about what the system asked for at a site, and free text
does not reproduce. The choice of key is therefore a measurement, not a preference, and this
pins it against the committed runs so a "more precise" key cannot be adopted later without
seeing what it costs.
"""

from __future__ import annotations

import collections
import json
from pathlib import Path

import pytest

from src.mathlib_review.review.merge import canonical_action, finding_key

REPS = [Path(f"results/pr_review_v5/runs/pr5_A_lead_heldout12_v2_rep{i}/findings.jsonl")
        for i in (1, 2, 3)]


def _rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").split("\n")
            if line.strip()]


def _key(row):
    return f"{row['pr_number']}|{row['primary_change_id']}|{row.get('issue_kind')}"


def test_the_key_is_site_and_kind():
    row = {"pr_number": 33337, "primary_change_id": "change:abc",
           "issue_kind": "naming_convention_violation"}
    from types import SimpleNamespace

    assert finding_key(SimpleNamespace(**row)) == "33337|change:abc|naming_convention_violation"


def test_the_full_action_key_recurs_essentially_never_and_site_and_kind_recurs_half_the_time():
    """The measurement behind the choice, on the three committed held-out reps.

    `canonical_action` normalises case and whitespace of model free text and nothing else --
    deliberately, since anything cleverer would merge claims we cannot prove equivalent -- so a
    key containing it is an identity of the sentence. Across 907 findings it reproduced twice.
    """

    if not all(path.is_file() for path in REPS):
        pytest.skip("the three held-out reps are not in this tree")

    fine, coarse = [], []
    for path in REPS:
        rows = _rows(path)
        fine.append({(row["pr_number"], row["primary_change_id"], row.get("issue_kind"),
                      row["action_key"]) for row in rows})
        coarse.append({_key(row) for row in rows})

    def recurrence(sets):
        counts = collections.Counter(key for one in sets for key in one)
        return (sum(1 for n in counts.values() if n == 3),
                sum(1 for n in counts.values() if n >= 2))

    assert recurrence(fine) == (0, 2)
    assert recurrence(coarse) == (127, 225)


def test_the_key_collides_within_a_run_and_the_rate_is_worth_reporting():
    """The cost of the coarse key, measured rather than waved at: about one finding in six sits
    on a site and kind some sibling also claims, so an adjudication report has to say that rate
    beside its coverage instead of letting one label stand silently for two asks."""

    if not REPS[0].is_file():
        pytest.skip("the held-out reps are not in this tree")

    rows = _rows(REPS[0])
    keys = {_key(row) for row in rows}
    assert (len(rows), len(keys)) == (285, 238)
    assert round(1 - len(keys) / len(rows), 2) == 0.16


def test_a_label_says_who_made_it_and_which_finding_it_read():
    """A label outlives the run it was made on, so it has to carry enough to be checked later:
    which finding was read, what that finding asked for, and whether a human or a model said
    so."""

    from src.mathlib_review.schema import AdjudicationLabel

    label = AdjudicationLabel(
        key="33337|change:abc|naming_convention_violation", pr_number=33337,
        primary_change_id="change:abc", issue_kind="naming_convention_violation",
        label="valid_not_an_ask", exemplar_finding_id="finding:abc",
        exemplar_action_key=canonical_action("naming", "Rename to toLinearMap_..."),
        exemplar_source_sha256="a" * 64, labelled_by="human:ya475",
        adjudication_version="v5-adjudication/1", from_run="pr5_A_lead_heldout12_v2_rep1",
        written_at="2026-09-21T00:00:00+00:00")
    assert label.labelled_by.startswith("human:")
    assert label.label == "valid_not_an_ask"
