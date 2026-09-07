"""Two channels, because one admission field answered two questions.

`admission` says `published` or `diagnostic`, which conflates "the system would say this" with
"the system proved this". That conflation is what makes the publication ceiling read as a
reviewer failure: 27 of the release's 43 gold obligations carry a concern no deterministic
warrant can settle, so a correct finding about any of them can never be `published` however
good it is.

* `review`   -- every maintainer-facing finding.
* `verified` -- the subset with claim-scoped deterministic support and no contradiction.

A finding in `review` but not `verified` is not a worse finding; it is one whose concern has no
warrant yet.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from src.datasets.pr_review_v5.finalize import _assign_channels, _contradicted_candidate_ids


def _finding(admission="published", candidate_ids=("c1",)):
    return SimpleNamespace(
        admission=admission,
        sources=[SimpleNamespace(candidate_id=item) for item in candidate_ids],
        channels=[],
        contradiction=None,
    )


def test_a_supported_finding_is_in_both_channels():
    finding = _finding("published")
    _assign_channels([finding], contradicted=set())
    assert finding.channels == ["review", "verified"]
    assert finding.contradiction is None


def test_an_unsupported_finding_is_maintainer_facing_but_not_verified():
    """The case the single field could not express. A naming or style claim has no
    deterministic warrant, so it can never be `published` -- but the system would still say
    it, and a recall figure that ignores it measures the mechanism rather than the reviewer."""

    finding = _finding("diagnostic")
    _assign_channels([finding], contradicted=set())
    assert finding.channels == ["review"]


def test_a_contradicted_finding_stays_in_review_and_says_so():
    """Contradiction is not a veto. The collector ran, looked, and disagreed -- which is a
    fact a maintainer would want, and deleting it would also destroy the evidence that the
    check happened at all."""

    finding = _finding("published", candidate_ids=("c1",))
    _assign_channels([finding], contradicted={"c1"})
    assert finding.channels == ["review"]
    assert "contradicted" in finding.contradiction


def test_a_finding_is_contradicted_if_any_of_its_sources_was():
    """A merged finding carries several sources; one contradiction is enough to withhold the
    verified claim."""

    finding = _finding("published", candidate_ids=("c1", "c2"))
    _assign_channels([finding], contradicted={"c2"})
    assert finding.channels == ["review"]


def test_every_finding_lands_in_review():
    """`review` is the maintainer-facing set, so nothing that survived the merge is absent
    from it -- otherwise the channel would be a second publication gate under a new name."""

    findings = [_finding("published"), _finding("diagnostic"),
                _finding("published", candidate_ids=("x",))]
    _assign_channels(findings, contradicted={"x"})
    assert all("review" in item.channels for item in findings)


# --- reading contradictions off the evidence packets --------------------------------------


def _packets(tmp_path, rows):
    evidence = tmp_path / "evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "packets.jsonl").write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    return tmp_path


def test_contradicted_ids_are_read_from_the_packets(tmp_path):
    """`collect_supported` returns only the supported set. A contradiction is not the same as
    an absence of support and must not be reported as one."""

    root = _packets(tmp_path, [
        {"candidate_id": "a", "status": "supported"},
        {"candidate_id": "b", "status": "contradicted"},
        {"candidate_id": "c", "status": "inconclusive"},
    ])
    assert _contradicted_candidate_ids(root) == {"b"}


def test_no_packets_means_no_contradictions_rather_than_an_error(tmp_path):
    """A run with the evidence chain skipped has no packets, and that is not a failure."""

    assert _contradicted_candidate_ids(tmp_path) == set()


def test_a_malformed_packet_line_does_not_break_the_read(tmp_path):
    evidence = tmp_path / "evidence"
    evidence.mkdir(parents=True)
    (evidence / "packets.jsonl").write_text(
        '{"candidate_id": "a", "status": "contradicted"}\nnot json\n', encoding="utf-8")
    assert _contradicted_candidate_ids(tmp_path) == {"a"}


def test_the_finding_model_carries_both_fields():
    from src.datasets.pr_review_v4.schema import ReviewFinding

    fields = ReviewFinding.model_fields
    assert "channels" in fields
    assert "contradiction" in fields
    # Defaulted, so every existing construction site still works.
    assert fields["channels"].default_factory is not None
    assert fields["contradiction"].default is None
