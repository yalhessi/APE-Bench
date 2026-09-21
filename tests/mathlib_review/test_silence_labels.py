"""Why an arm said nothing where a maintainer asked for something, recorded once.

The companion store to `AdjudicationLabel` on the other side of the ledger: that one labels a
finding gold cannot judge, this one labels a silence gold can. Both exist because a judgement
somebody made by reading has to outlive the run it was made on, and both are held to the same
rule -- a human row outranks a model row, a correction is a later row rather than an edit,
disagreement is reported rather than averaged, and neither may ever enter recall.

What is specific to this one is where the label comes from. It is made from the arm's own
sentence, not from `abstention_reason`: under replay 17 of 45 sessions produced a different
reason with the same outcome, so the enum labels nothing on its own.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.mathlib_review.judge.adjudicate import (
    ingest_silences, load_silence_labels, resolve_silences,
)
from src.mathlib_review.schema import SilenceLabel, silence_key

RUN = "pr5_A_lead_heldout12_v2_rep1"
runs_exist = pytest.mark.skipif(
    not Path(f"results/pr_review_v5/runs/{RUN}/findings.jsonl").is_file(),
    reason="the held-out reps are not in this tree")


def _label(**kwargs) -> SilenceLabel:
    fields = {
        "invocation_id": "wu:1f9cf7865fe0948dfc6e47f8#naming",
        "obligation_id": "obligation:64e",
        "pr_number": 33337,
        "arm_id": "naming",
        "label": "advisory_suppressed",
        "labelled_by": "human:reader",
        "from_run": RUN,
        "written_at": "2026-09-21T12:00:00Z",
        "note": "read `emerging (21 vs 7)` and declined to ask",
    }
    fields.update(kwargs)
    fields.setdefault("key", silence_key(fields["invocation_id"], fields["obligation_id"]))
    return SilenceLabel(**fields)


def test_the_key_is_its_parts_and_cannot_be_typed_by_hand():
    """A key that does not decompose is a key that joins to nothing. It is derived, and the
    model refuses a row where someone wrote it out differently."""

    label = _label()
    assert label.key == "wu:1f9cf7865fe0948dfc6e47f8#naming|obligation:64e"
    with pytest.raises(ValidationError, match="key must be"):
        _label(key="naming-33337")


def test_an_evidence_gap_has_to_name_the_tool():
    """"The tools are weak" funds nothing; "`naming_norm` returned insufficient_evidence on a
    subject it could have resolved" funds a specific fix. The model will not accept the first
    one, and will not accept a tool named on a label that is not about a tool."""

    assert _label(label="evidence_gap", evidence_gap_tool="naming_norm").evidence_gap_tool

    with pytest.raises(ValidationError, match="evidence_gap needs"):
        _label(label="evidence_gap")
    with pytest.raises(ValidationError, match="does not mean a tool failed"):
        _label(label="off_concern", evidence_gap_tool="naming_norm")


def test_the_vocabulary_keeps_the_mechanisms_apart():
    """Eight labels because the first read found eight mechanisms, and collapsing them into
    three is what sent the first round of interventions at the wrong three. In particular
    `off_concern` (correct silence, a routing question) and `fix_required` (the contract
    refused the ask) are the two that a coarser vocabulary merges."""

    from typing import get_args

    labels = set(get_args(SilenceLabel.model_fields["label"].annotation))
    assert {"off_concern", "fix_required", "advisory_suppressed", "cross_unit",
            "evidence_gap", "knowledge_gap", "disagreement", "decision_noise"} == labels


def test_a_file_that_could_claim_to_be_a_model_is_refused(tmp_path):
    """Same guard as the adjudication store, and for the same reason: a human row outranks a
    model row, so a file that can claim either makes that ordering meaningless."""

    path = tmp_path / "silences.jsonl"
    path.write_text(json.dumps(_label(labelled_by="task:adjudicator/1").model_dump()) + "\n")
    with pytest.raises(ValueError, match="not `human:<name>`"):
        ingest_silences(path, store=tmp_path / "store.jsonl")


def test_a_correction_is_a_later_row_and_the_disagreement_is_kept(tmp_path):
    """Never an edit. Two readers calling one silence `off_concern` and `fix_required` is the
    most interesting row in the file, and a majority over n=2 would bury it."""

    path = tmp_path / "silences.jsonl"
    store = tmp_path / "store.jsonl"
    rows = [_label(label="off_concern", labelled_by="human:first"),
            _label(label="fix_required", labelled_by="human:second")]
    path.write_text("".join(json.dumps(row.model_dump()) + "\n" for row in rows))

    assert ingest_silences(path, store=store) == {"ingested": 2, "keys": 1}
    assert len(load_silence_labels(store)) == 2

    resolved = resolve_silences(load_silence_labels(store))
    verdict = resolved[rows[0].key]
    assert verdict["label"] == "fix_required"      # the later human row
    assert verdict["contested"] is True and verdict["rows"] == 2


def test_a_human_row_outranks_a_model_row_whenever_it_was_written(tmp_path):
    """Order in the file is how recency is expressed, but it does not let a model overrule a
    person: the human row wins even when the model's came later."""

    store = tmp_path / "store.jsonl"
    from src.mathlib_review.io import append_jsonl

    append_jsonl(store, _label(label="fix_required", labelled_by="human:reader"))
    append_jsonl(store, _label(label="disagreement", labelled_by="task:adjudicator/1"))
    assert resolve_silences(load_silence_labels(store))[_label().key]["label"] == "fix_required"


@runs_exist
def test_the_report_puts_each_label_on_its_silence(tmp_path):
    """The loop closes: label a cell, and `report silences` shows it against the ask it is
    about rather than in a spreadsheet nobody can join back."""

    from src.mathlib_review.analysis.report import silences

    # Its own empty store, never the real one: a test that reads the production store passes or
    # fails on what somebody labelled last week.
    empty = tmp_path / "empty.jsonl"
    plain = silences(RUN, labels=empty)
    assert plain["silent_cells"] == 76 and plain["labelled"] == 0

    target = next(row for row in plain["rows"] if row["on_concern"])
    store = tmp_path / "store.jsonl"
    from src.mathlib_review.io import append_jsonl

    append_jsonl(store, _label(
        invocation_id=target["invocation_id"], obligation_id=target["obligation_id"],
        pr_number=target["pr_number"], arm_id=target["arm_id"], label="fix_required",
        note="could not get a compiling edit"))

    labelled = silences(RUN, labels=store)
    row = next(item for item in labelled["rows"] if item["key"] == target["key"])
    assert row["label"] == "fix_required"
    assert row["label_note"] == "could not get a compiling edit"
    assert labelled["labelled"] == 1
    assert labelled["by_label"] == {"fix_required": 1}
    assert labelled["by_label_on_concern"] == {"fix_required": 1}


@runs_exist
def test_the_report_separates_the_arms_remit_from_the_arms_decision(tmp_path):
    """The headline the instrument exists to produce, and the correction it forced: most
    gold-site silence is the wrong arm being correctly quiet. A contract change reaches the
    on-concern ones only, and there are 13 of them here, not 76."""

    from src.mathlib_review.analysis.report import silences

    payload = silences(RUN, labels=tmp_path / "empty.jsonl")
    assert payload["on_concern_cells"] == 13
    assert payload["off_concern_cells"] == 53
    assert payload["remitless_cells"] == 10       # the generalist, which has no remit
    assert (payload["on_concern_cells"] + payload["off_concern_cells"]
            + payload["remitless_cells"]) == payload["silent_cells"]
    # Routing scheduled an on-concern arm at every counted obligation, so none of this is a
    # gap in the agenda -- which is what distinguishes it from the fanout question.
    assert payload["obligations_without_an_on_concern_arm"] == []


def test_a_label_is_not_gold_and_the_report_says_so():
    """`AdjudicationLabel` carries this in its docstring and the rule file carries it for the
    store; a reader meets it in the output."""

    from src.mathlib_review.analysis.report import silences

    payload = silences(RUN) if Path(f"results/pr_review_v5/runs/{RUN}/findings.jsonl").is_file() \
        else None
    if payload is None:
        pytest.skip("the held-out reps are not in this tree")
    assert "never enters recall" in payload["note"]
    assert "routing, not the contract" in payload["note"]


@runs_exist
def test_the_labelled_corpus_says_what_it_says():
    """The step-0 result, pinned against the committed store so a later change to the report
    or the remit bridge cannot quietly restate it.

    The finding is that gold-site silence is mostly not a thing an intervention repairs: of 58
    distinct silent sessions, 37 are an arm correctly quiet about somebody else's concern and
    17 are the right arm declining on stated grounds. The three mechanisms the interventions
    in `docs/todo/specialist-abstention-interventions.md` were costed against total four
    sessions between them, and two of the three have none at all.
    """

    from src.mathlib_review.analysis.report import silences

    payload = silences(RUN)
    if not payload["labelled"]:
        pytest.skip("the silence-label store is not in this tree")

    assert payload["labelled"] == payload["silent_cells"] == 76
    assert payload["by_label"] == {
        "off_concern": 50, "disagreement": 19, "evidence_gap": 2,
        "decision_noise": 2, "fix_required": 2, "knowledge_gap": 1}
    # Neither mechanism that motivated a contract condition has a single instance here.
    assert "advisory_suppressed" not in payload["by_label"]
    assert "cross_unit" not in payload["by_label"]

    # Cells are not sessions: the one `fix_required` session is PR 33149's duplication arm,
    # counted against both of that PR's "remove the axioms" obligations.
    by_label_sessions = {}
    for row in payload["rows"]:
        by_label_sessions.setdefault(row["label"], set()).add(row["invocation_id"])
    assert len(by_label_sessions["fix_required"]) == 1
    assert {row["pr_number"] for row in payload["rows"]
            if row["label"] == "fix_required"} == {33149}

    # Both evidence gaps name one tool, which is what makes them worth a code check.
    assert {row["evidence_gap_tool"] for row in payload["rows"]
            if row["label"] == "evidence_gap"} == {"naming_norm"}

    # Seven cells where the reader and its adversary disagreed, kept as disagreement.
    assert len(payload["contested_keys"]) == 7
