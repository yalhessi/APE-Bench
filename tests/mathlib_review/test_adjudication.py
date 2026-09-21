"""Labelling the findings gold cannot judge, once, and carrying the labels across runs.

~90% of what the system emits is not a maintainer obligation, `gold_alignment_rate` is not
precision, and nothing says whether any of it is useful. This is the record that closes that
one claim at a time -- and the properties worth pinning are the ones that make it a record
rather than a metric: a label outlives its run, a human outranks a model, disagreement is
reported rather than averaged, and nothing here is gold.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.mathlib_review.io import jsonl_bytes
from src.mathlib_review.judge.adjudicate import (
    ADJUDICATION_VERSION, append_label, ingest, load_labels, population, resolve,
)
from src.mathlib_review.schema import AdjudicationLabel

KEY = "33337|change:abc|naming_convention_violation"


def _label(label="correct_ask", by="human:ya475", key=KEY, finding="finding:abc"):
    return AdjudicationLabel(
        key=key, pr_number=33337, primary_change_id="change:abc",
        issue_kind="naming_convention_violation", label=label,
        exemplar_finding_id=finding, exemplar_action_key="naming:rename it",
        exemplar_source_sha256="a" * 64, labelled_by=by,
        adjudication_version=ADJUDICATION_VERSION, from_run="pr5_probe_rep1",
        written_at="2026-09-21T00:00:00+00:00")


def test_a_label_outlives_the_run_it_was_made_on(tmp_path):
    """The whole economy of this: the site-and-kind key recurs 127 times across three
    repetitions where the full key recurs 0, so labelling once pays for every rep that
    reproduces the claim."""

    store = tmp_path / "labels.jsonl"
    append_label(_label(), store)
    append_label(_label(key="33145|change:xyz|proof_simplification"), store)
    assert len(load_labels(store)) == 2
    assert set(resolve(load_labels(store))) == {KEY, "33145|change:xyz|proof_simplification"}


def test_a_human_outranks_a_model_whatever_the_order(tmp_path):
    store = tmp_path / "labels.jsonl"
    append_label(_label("wrong", by="task:" + "d" * 64), store)
    append_label(_label("correct_ask", by="human:ya475"), store)
    append_label(_label("wrong", by="task:" + "e" * 64), store)
    verdict = resolve(load_labels(store))[KEY]
    assert verdict["label"] == "correct_ask" and verdict["labelled_by"].startswith("human:")


def test_disagreement_is_reported_rather_than_averaged(tmp_path):
    """Two people reading one claim differently is the most interesting row in the file, and a
    majority over n=2 would bury it."""

    store = tmp_path / "labels.jsonl"
    append_label(_label("correct_ask", by="human:a"), store)
    append_label(_label("valid_not_an_ask", by="human:b"), store)
    verdict = resolve(load_labels(store))[KEY]
    assert verdict["contested"] is True and verdict["rows"] == 2
    # The later human row is the current verdict, and the disagreement travels with it.
    assert verdict["label"] == "valid_not_an_ask"


def test_a_correction_is_a_later_row_not_an_edit(tmp_path):
    store = tmp_path / "labels.jsonl"
    append_label(_label("wrong", by="human:a"), store)
    append_label(_label("correct_ask", by="human:a"), store)
    assert len(load_labels(store)) == 2
    assert resolve(load_labels(store))[KEY]["label"] == "correct_ask"


def test_a_label_file_that_could_claim_to_be_either_is_refused(tmp_path):
    """The prefix is what orders a human above a model. A file that can write `task:` rows
    makes that ordering meaningless."""

    store, incoming = tmp_path / "labels.jsonl", tmp_path / "incoming.jsonl"
    incoming.write_bytes(jsonl_bytes([_label(by="task:" + "f" * 64)]))
    with pytest.raises(ValueError, match="human:"):
        ingest(incoming, store=store)
    assert not store.exists()

    incoming.write_bytes(jsonl_bytes([_label(by="human:ya475")]))
    assert ingest(incoming, store=store) == {"ingested": 1, "keys": 1}


def test_a_matched_finding_is_not_re_judged():
    """The maintainer already adjudicated it, and they are the only authority that settles what
    they wanted."""

    findings = [{"finding_id": "finding:a"}, {"finding_id": "finding:b"},
                {"finding_id": "finding:c"}]
    pairs = [{"candidate_id": "finding:a", "role": "observed"},
             {"candidate_id": "finding:b", "role": "observed"}]
    matches = [{"candidate_id": "finding:a", "role": "observed", "issue_match": True},
               {"candidate_id": "finding:b", "role": "observed", "issue_match": False}]
    left = {item["finding_id"] for item in population(findings, pairs, matches)}
    # `b` was paired and not matched -- gold saw it and said no -- and `c` was never paired at
    # all. Both are things gold cannot judge; only `a` is settled.
    assert left == {"finding:b", "finding:c"}


def test_the_store_is_outside_every_run_and_every_release():
    """A label is about a claim, not about a run, and it must outlive every run that reproduces
    the claim. It is also not gold: gold is what maintainers asked for, and these are
    judgements about what they did not."""

    from src.mathlib_review.judge.adjudicate import LABELS
    from src.mathlib_review.paths import AUDITS, RUNS, V4_RELEASES

    assert RUNS not in LABELS.parents and AUDITS not in LABELS.parents
    assert V4_RELEASES not in LABELS.parents


RUN = "pr5_A_lead_heldout12_v2_rep1"


@pytest.mark.skipif(
    not Path(f"results/pr_review_v5/audits/pr5-A-lead-heldout12-v2-rep1"
             "/semantic_report.json").is_file(),
    reason="the held-out audit is not in this tree")
def test_the_report_says_how_much_is_unread_and_what_a_key_costs(tmp_path, monkeypatch):
    """Not precision, and it says so. Until `labelled_share` is high, a rate over the labelled
    part is a rate over whatever was labelled first -- and the collision count is there so a
    label is never read as standing for exactly one ask when it stands for two.

    Runs against the committed audit and writes nothing into it: the report goes to a temp
    directory and the ledger row is captured rather than appended, because a test that leaves
    artifacts in a tracked run directory is a test that edits the record."""

    from src.mathlib_review.judge import adjudicate as module
    from src.mathlib_review.run_state import StageInput

    audit = tmp_path / "audit"
    audit.mkdir()
    original = StageInput.of

    def redirected(run_name, **kwargs):
        stage = original(run_name, **kwargs)
        for name in ("semantic_pairs.jsonl", "semantic_matches.jsonl"):
            (audit / name).write_bytes((stage.audit_dir / name).read_bytes())
        return type(stage)(**{**stage.__dict__, "audit_dir": audit,
                              "run_dir": stage.run_dir})

    rows = []
    monkeypatch.setattr(StageInput, "of", staticmethod(redirected))
    monkeypatch.setattr(module, "append_stage",
                        lambda directory, record: rows.append((directory, record)))
    out = module.adjudicate_run(RUN, store=tmp_path / "labels.jsonl")
    payload = json.loads(Path(out).read_text())

    assert payload["findings_total"] == 285
    assert payload["unadjudicated_population"] == 259      # 285 minus the 26 gold matched
    assert payload["distinct_keys"] == 214
    assert payload["findings_sharing_a_key"] == 45
    assert payload["labelled"] == 0 and payload["labelled_share"] == 0.0
    assert "Not precision" in payload["note"]
    assert "valid_not_an_ask" in payload["note"]

    # The row goes to the run, and says it changed nothing about its state.
    (directory, record), = rows
    assert directory.name == RUN
    assert record.stage == "adjudicate" and record.transition is None


def test_adjudicate_is_a_verb_that_does_not_spend():
    """No model runs: a label is in the store or it is not, and the report says how much of the
    run is still unread rather than filling the gap with something."""

    from src.mathlib_review.review.cli import SPENDS, build_parser

    assert "adjudicate" not in SPENDS
    args = build_parser().parse_args(["adjudicate", "--of", "pr5_probe_rep1"])
    assert args.of_run == "pr5_probe_rep1" and args.labels is None
    assert not hasattr(args, "execute")
