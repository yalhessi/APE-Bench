"""Why each gold obligation ended where it did, and what became of every finding.

The join that has been done by hand in a scratchpad every time someone asked "why did we miss
this". Two properties are what make it worth having rather than another number: the coarse
level is judge-INDEPENDENT where it can be, so `UNTOUCHED` is computable before any judge runs
and cannot move with a rubric; and everything that is not a bucket stays an annotation, because
an abstention's reason and a retrieval failure answer different questions and folding them into
one ladder is how a tooling defect reads as a judgement call.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.mathlib_review.analysis.report import COARSE, FINE, buckets

RUN = "pr5_A_lead_heldout12_v2_rep1"
AUDIT = Path("results/pr_review_v5/audits/pr5-A-lead-heldout12-v2-rep1/semantic_report.json")
runs_exist = pytest.mark.skipif(
    not Path(f"results/pr_review_v5/runs/{RUN}/findings.jsonl").is_file(),
    reason="the held-out reps are not in this tree")


@pytest.fixture(scope="module")
def judged():
    return buckets([RUN], audit=True)["per_run"][RUN]


@runs_exist
def test_covered_is_exactly_what_the_judge_called_a_hit(judged):
    """Read from the judge's own `per_obligation`, never recomputed, so the two can never
    disagree about the same obligation."""

    report = json.loads(AUDIT.read_text())
    hits = sum(1 for row in report["per_obligation"] if row.get("issue_status") == "hit")
    assert judged["coarse"]["COVERED"] == hits == 7


@runs_exist
def test_the_denominator_difference_from_the_judge_is_counted_not_hidden(judged):
    """The judge scores 23 obligations here and this counts 22. The difference is one row
    `obligation_exclusions` names as contradicted by the release's own artifacts -- an automatic
    miss in the judge's report and not a fact about the reviewer. Counted, so the gap between
    the two numbers is never a mystery."""

    report = json.loads(AUDIT.read_text())
    assert len(report["per_obligation"]) == 23
    assert judged["obligations_counted"] == 22
    assert judged["obligations_not_counted"]["audit_excluded"] == 1
    assert sum(judged["coarse"].values()) == 22


@runs_exist
def test_untouched_is_judge_independent(judged):
    """Pure geometry: nothing the system emitted anchors at the obligation's sites, so no
    verdict could make it a hit. It is the number the 2026-06 miss decomposition called the
    robust one, and it must not move when the audit is taken away."""

    unjudged = buckets([RUN])["per_run"][RUN]
    assert unjudged["coarse"]["UNTOUCHED"] == judged["coarse"]["UNTOUCHED"] == 8
    assert (unjudged["obligation_ids_by_bucket"]["UNTOUCHED"]
            == judged["obligation_ids_by_bucket"]["UNTOUCHED"])
    # And without a judge the located ones are not split by guesswork.
    assert unjudged["coarse"]["LOCATED_UNJUDGED"] == 14
    assert unjudged["coarse"]["COVERED"] == unjudged["coarse"]["LOCATED_MISS"] == 0


@runs_exist
def test_the_fine_level_is_the_overlays_vocabulary_and_no_other(judged):
    """A second set of words for the same facts is how `documentation` and `docs` made an arm
    unmeasurable for its whole life."""

    from src.mathlib_review.analysis.review_overlay import STATES

    assert set(FINE) <= set(STATES)
    assert set(judged["fine"]) == set(FINE)
    assert judged["fine"]["silent"] == 8


@runs_exist
def test_a_silence_carries_its_reason_and_its_retrieval_as_annotations(judged):
    """Not buckets. "the arm declined" and "the arm got nothing back" are different answers to
    "why", and a ladder that mixed them would report a tooling failure as a judgement.

    Measured here: 48 distinct specialist invocations are silent at a gold site, 30 of them at
    an obligation this run missed. (The 45 in the replay todo is a near neighbour, not this
    set: it was selected by a scratch join over required gold changes -- which is the reason a
    selector has to be named and tested rather than written in a scratchpad.)"""

    cells = [cell for row in judged["obligations"] for cell in row["cells"]]
    silent = {cell["invocation_id"]: cell for cell in cells if cell["state"] == "silent"}
    specialists = {key: cell for key, cell in silent.items() if cell["arm_id"] != "generalist"}
    assert len(specialists) == 48

    missed = {cell["invocation_id"] for row in judged["obligations"]
              if row["coarse"] != "COVERED"
              for cell in row["cells"]
              if cell["state"] == "silent" and cell["arm_id"] != "generalist"}
    assert len(missed) == 30

    # Every silence says which kind it was, and what its retrieval returned.
    assert {cell["context"] for cell in specialists.values()} <= {"none", "empty", "partial", "ok"}
    reasons = {cell["abstention_reason"] for cell in specialists.values()}
    assert {"already_correct", "could_not_establish"} <= reasons


@runs_exist
def test_findings_are_bucketed_by_what_the_judge_did_with_them(judged):
    """The gap this exists to make visible: most of what the system emits is never paired with
    any obligation, so `gold_alignment_rate` is not precision and nothing yet says whether
    those findings are useful."""

    assert judged["findings_by_judge"] == {
        "matched": 26, "paired_unmatched": 13, "unpaired": 246}
    assert len(judged["findings"]) == 285


@runs_exist
def test_several_runs_say_how_often_a_claim_reproduced():
    """Reported, never ranked on: cross-rep agreement separates hits in-sample and is recorded
    as provisional."""

    payload = buckets([f"pr5_A_lead_heldout12_v2_rep{i}" for i in (1, 2, 3)], audit=True)
    counts = {row["reps_with_key"]
              for run in payload["per_run"].values() for row in run["findings"]}
    assert counts <= {1, 2, 3}
    everywhere = [row for run in payload["per_run"].values() for row in run["findings"]
                  if row["reps_with_key"] == 3]
    assert len(everywhere) == 463


@runs_exist
def test_the_report_says_what_it_read(judged):
    """A bucket count is only checkable if the artifacts behind it are named with their
    digests. That is what makes it a stage input rather than a scrape."""

    assert set(judged["requires"]) == {"agenda", "delegations", "arm_responses", "findings"}
    assert all(len(value) == 64 for value in judged["requires"].values())


def test_the_note_travels_with_the_numbers():
    """A bucket table read out of context is exactly how `location_recall` came to be quoted as
    a quality signal."""

    payload = buckets([], audit=False)
    assert "judge-independent" in payload["note"]
    assert "not buckets" in payload["note"] and "provisional" in payload["note"]
    assert list(payload["coarse_vocabulary"]) == list(COARSE)


@runs_exist
def test_a_cell_says_whether_the_ask_was_that_arms_business(judged):
    """The field that reordered the whole intervention plan.

    A gold-site silence is only evidence about an arm's contract if the ask was in that arm's
    remit. Most are not: on this run 53 of 76 silent cells are an arm quiet about somebody
    else's concern -- `duplication` at a rename, `naming` at "factor out a lemma" -- and
    counting those as silences to be fixed aims a contract change at nothing. The bridge is
    `benches.gold_labels_for`, shared with the bench builder, because a second copy of the
    documentation/docs mapping is exactly how that mismatch survived as long as it did.
    """

    cells = [cell for row in judged["obligations"] for cell in row["cells"]
             if cell["state"] == "silent"]
    assert len(cells) == 76
    assert sum(1 for cell in cells if cell["on_concern"]) == 13
    assert sum(1 for cell in cells if cell["on_concern"] is False) == 53
    # The generalist has no remit to be outside of, so the question does not apply to it.
    assert all(cell["on_concern"] is None for cell in cells if cell["arm_id"] == "generalist")

    # An arm silent inside its remit really is the minority, per arm as well as overall.
    naming = [cell for cell in cells if cell["arm_id"] == "naming"]
    assert sum(1 for cell in naming if cell["on_concern"]) == 3 < len(naming)


@runs_exist
def test_an_obligation_carries_the_ask_it_is_about(judged):
    """Reading a silence means reading the ask. Before this the join lived in a scratchpad,
    which is the defect `StageInput` and the named selectors were built to stop."""

    rows = {row["obligation_id"]: row for row in judged["obligations"]}
    rename = rows["obligation:6b02b6118fcd24d676894ab9eb795826ae036cf3de57f6a1648aff81bf55a336"]
    assert rename["claim"] == "Rename the theorem `round_eq'` to `round_eq_div`."
    assert rename["concern_labels"] == ["naming"]
    assert rename["blocking_force"] == "advisory"
    assert rename["required"] is True

    # And the one that says whether a contract change could ever have reached the site: on
    # this run every counted obligation had an arm of the right concern scheduled at it, so
    # the on-concern silences are declines, not gaps in the agenda.
    assert all(row["on_concern_arm_scheduled"] for row in judged["obligations"])


@runs_exist
def test_a_silence_carries_the_sentence_the_arm_wrote():
    """The reason enum is not the diagnosis. Under replay 17 of 45 sessions produced a
    different `abstention_reason` with the same outcome -- `already_correct` and
    `could_not_establish` swapping -- so a label made from the enum is a coin flip. The detail
    is what a reader can actually diagnose from, and it reached no report before this."""

    payload = buckets([RUN], audit=True)["per_run"][RUN]
    cells = [cell for row in payload["obligations"] for cell in row["cells"]]
    silent = [cell for cell in cells if cell["state"] == "silent"]
    assert sum(1 for cell in silent if cell["abstention_detail"]) >= 60
    # And it is a property of a silence, not of every cell.
    assert all(cell["abstention_detail"] is None for cell in cells if cell["state"] != "silent")


@runs_exist
def test_replay_annotations_carry_more_than_stability():
    """`stable` says whether to look; the rest says what at. A stable silence is diagnosed
    from its reasons and its text, and a silence that files in some samples is a different
    repair from one that never does."""

    payload = buckets(
        [RUN], audit=True,
        replay="pr5_replay_null_first_submit_candidates_goldabstain45_v2_rep1",
    )["per_run"][RUN]
    replayed = [cell for row in payload["obligations"] for cell in row["cells"]
                if cell["replay_stable"] is not None]
    assert replayed, "the replay annotated no cell"
    assert all(cell["replay_filed"] is not None for cell in replayed)
    assert all(isinstance(cell["replay_reasons"], list) for cell in replayed)
    # This replay predates outcome rows carrying the text, and it is reported absent rather
    # than reconstructed from attempt directories that belong to another worktree.
    assert all(cell["replay_details"] is None for cell in replayed)
    # The naming session that filed the gold rename in every replay is the unstable one.
    unstable = {cell["invocation_id"] for cell in replayed if not cell["replay_stable"]}
    assert "wu:1f9cf7865fe0948dfc6e47f8#naming" in unstable


@runs_exist
def test_the_gate_is_reported_beside_what_the_run_found(judged):
    """The last stage between a finding and a maintainer, and the one nothing measured.

    `finalize` publishes a claim only when a deterministic collector can warrant its concern
    family; everything else is kept as `diagnostic` with no channel. That is honest about what
    the system would *say*, and it is not the same as what it *found* -- so both numbers have
    to be visible or the smaller one gets quoted as the only one. On this rep the run hits 7
    gold obligations and publishes 2 of them, and 21 of the 24 suppressed hit-findings
    carry one reason: no collector can support that concern family, which is a statement about a KIND of
    claim rather than about this one.

    The control column is reported with it because the gate is what keeps published control-PR
    emission at zero, so opening it is a trade and not a free gain.
    """

    gate = judged["gate"]
    assert (gate["findings"], gate["published"]) == (285, 25)
    assert (gate["obligations_hit_pre_gate"], gate["obligations_hit_post_gate"]) == (7, 2)
    assert len(gate["obligations_lost_to_gate"]) == 5
    assert gate["control_findings"] == 3 and gate["control_published"] == 0

    top_reason, count = max(gate["suppressed_hits_by_reason"].items(), key=lambda kv: kv[1])
    assert "no collector can support" in top_reason and count == 21

    # And the inversion that makes this worth a report rather than a footnote: the families
    # that hit are not the families that publish.
    families = gate["by_concern_family"]
    assert families["correctness"]["hits"] == 14 and families["correctness"]["published"] == 0
    assert families["naming"]["hits"] == 4 and families["naming"]["published"] == 0
    assert families["style"]["hits"] == 0 and families["style"]["findings"] == 108
    assert families["proof-golf"]["hits"] == 1 and families["proof-golf"]["published"] == 8
    assert families["generalization"]["hits"] == 0 and families["generalization"]["published"] == 2


@runs_exist
def test_the_gate_block_needs_no_judge_for_the_half_that_needs_none():
    """Volume and control emission are facts about the run; only the obligation counts need an
    audit. Reporting the first pair without the second is what lets a reader see the gate at
    all on an unjudged run."""

    gate = buckets([RUN])["per_run"][RUN]["gate"]
    assert gate["findings"] == 285 and gate["published"] == 25
    assert gate["control_published"] == 0
    assert "obligations_hit_pre_gate" not in gate
    assert "not whether the claim is right" in gate["note"]


FANOUT = "pr5_F_fanout_stage1_rep1"
fanout_exists = pytest.mark.skipif(
    not Path(f"results/pr_review_v5/runs/{FANOUT}/findings.jsonl").is_file(),
    reason="the fanout stage-1 run is not in this tree")


@fanout_exists
def test_a_run_whose_ledger_carries_no_status_is_read_from_what_the_arms_said():
    """The report must never contradict the audit printed beside it.

    `ArmResponse.row()` uses `exclude_unset` on purpose, so "considered and declined" stays
    distinguishable from "never considered". In a fanout run the arms are top-level tasks
    rather than lead-delegated jobs, so *no* delegation row carries an outcome at all: all 173
    rows of `pr5_F_fanout_stage1_rep1` omit `status`, while all 173 arm responses say
    `success`. Reading that absence as "ran and did not come back" put every obligation in
    `UNTOUCHED` — including the two the judge scored `hit`.

    Same class as the rules-file trap "a closed vocabulary silently filters a correct
    registration": an absent value read as a negative one.
    """

    payload = buckets([FANOUT], audit=True)["per_run"][FANOUT]

    # The contradiction this fixes: nothing the judge called a hit may be UNTOUCHED, which is
    # judge-independent geometry and means nothing anchored there at all.
    hits = [row for row in payload["obligations"] if row["judge"] == "hit"]
    assert len(hits) == 2
    assert all(row["coarse"] == "COVERED" for row in hits), [
        (row["obligation_id"], row["coarse"]) for row in hits]
    assert payload["coarse"]["UNTOUCHED"] == 2

    # And no cell is `unavailable` merely because the ledger said nothing about it.
    cells = [cell for row in payload["obligations"] for cell in row["cells"]]
    assert cells and not any(cell["state"] == "unavailable" for cell in cells)


@runs_exist
def test_a_lead_runs_buckets_are_unchanged_by_that_fallback(judged):
    """The fallback reads the arm's status only when the delegation row carries none, so a
    lead run — where every row carries one, including the pruned jobs — is untouched."""

    assert judged["coarse"] == {
        "UNTOUCHED": 8, "LOCATED_MISS": 7, "LOCATED_UNJUDGED": 0, "COVERED": 7}
    states = {cell["state"] for row in judged["obligations"] for cell in row["cells"]}
    assert "pruned" in states
