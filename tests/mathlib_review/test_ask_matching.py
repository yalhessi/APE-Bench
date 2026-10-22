"""The raw-ask matcher as an instrument: v1's rules carried into v2 unchanged, and a verdict that
covers its inputs exactly or is refused.

v2 (the registered Task) changes how the inputs arrive and how the verdict leaves. It must not
change how the matcher judges, so the judgment rules are pinned byte for byte against v1's two
rubric files, which stay where every earlier seal read them.
"""

from __future__ import annotations

import json

import pytest

from src.mathlib_review.judge import ask_matching as M
from src.mathlib_review.schema import BlindAsk, BlindFinding, BlindPacket


@pytest.mark.parametrize("policy", M.QUESTION_POLICIES)
def test_v2_judges_by_v1s_rules_byte_for_byte(policy):
    v1 = M.V1_RUBRIC_FILES[policy].read_text()
    section = v1[v1.index("## For every ask"):v1.index("## Output")]
    assert M.judgment_text(policy) == section
    assert M.judgment_text(policy) in M.v2_template(policy)


def test_the_two_versions_and_policies_have_distinct_rubric_identities():
    ids = {(v, p): M.rubric_sha256(v, p) for v in M.VERSIONS for p in M.QUESTION_POLICIES}
    assert len(set(ids.values())) == 4
    with pytest.raises(ValueError, match="unknown ask-match version"):
        M.rubric_sha256("3-nothing", "request_only")


def test_v2_renders_its_counts_and_leaves_no_placeholder():
    text = M.render_v2_rubric(5, 4, "request_only")
    assert "on four Mathlib pull requests. Five anonymous reviewers, `R1` to `R5`" in text
    assert "`R1_pr<N>.json` to `R5_pr<N>.json`" in text
    assert "{" not in text.replace('{"pr"', "").replace('{"reviewer"', "").replace('{"<pr>"', "") \
        .replace('{"R1"', "")
    one = M.render_v2_rubric(3, 1, "questions")
    assert "on one Mathlib pull request. Three anonymous reviewers" in one
    assert "question to the author" in one
    assert "question to the author" not in text


def _packet(pr=7, labels=("R1", "R2"), findings=2, asks=("a1", "a2")):
    return BlindPacket(
        pr=pr,
        asks=[BlindAsk(ask_id=a, path="Mathlib/X.lean", code_at_comment="x", comment=f"fix {a}")
              for a in asks],
        reviewers={label: [BlindFinding(i=i, target=f"Mathlib/X.lean:{i}", claim="c",
                                        requested_change="r", severity="advisory")
                           for i in range(findings)] for label in labels})


def test_the_prompt_holds_every_input_as_v1_wrote_it():
    packet = _packet()
    prompt = M.render_matcher_prompt([packet], "request_only")
    for name, content in M.packet_files(packet).items():
        assert f"### `{name}`" in prompt
        assert json.dumps(content, ensure_ascii=False, indent=1) in prompt
    assert prompt.index("### `R1_pr7.json`") < prompt.index("### `R2_pr7.json`")


def test_a_batch_whose_prs_disagree_on_labels_is_refused():
    with pytest.raises(ValueError, match="same reviewer labels"):
        M.render_matcher_prompt([_packet(7), _packet(8, labels=("R1", "R2", "R3"))], "request_only")


def _complete(packet):
    rows = [{"pr": packet.pr, "ask_id": a.ask_id, "R1": "reached", "R1_finding": 1,
             "R2": "no", "R2_finding": None, "note": ""} for a in packet.asks]
    return rows, {str(packet.pr): {"R1": 1, "R2": 2}}


def test_a_complete_verdict_has_no_problems():
    packet = _packet()
    rows, unmatched = _complete(packet)
    assert M.verdict_problems([packet], rows, unmatched) == []


@pytest.mark.parametrize("mutate, expected", [
    (lambda rows, um: rows.pop(), "has no verdict"),
    (lambda rows, um: rows.append(dict(rows[0])), "answered twice"),
    (lambda rows, um: rows[0].update(R2="maybe"), "not reached, partial or no"),
    (lambda rows, um: rows[0].update(R1_finding=5), "not an index"),
    (lambda rows, um: rows[0].update(R1_finding=True), "not an index"),
    (lambda rows, um: rows[0].update(R3="no"), "not this PR's reviewers"),
    (lambda rows, um: rows[0].update(ask_id="zz"), "has no ask 'zz'"),
    (lambda rows, um: um["7"].update(R1=9), "not a count"),
    (lambda rows, um: um.clear(), "no unmatched counts for PR 7"),
])
def test_an_incomplete_or_impossible_verdict_names_its_problem(mutate, expected):
    packet = _packet()
    rows, unmatched = _complete(packet)
    mutate(rows, unmatched)
    problems = M.verdict_problems([packet], rows, unmatched)
    assert any(expected in p for p in problems), problems


def test_typed_verdicts_flatten_to_the_shape_every_seal_was_read_in():
    asks = [M.AskVerdict(pr=7, ask_id="a1", note="n", verdicts=[
        M.ReviewerVerdict(reviewer="R2", value="no"),
        M.ReviewerVerdict(reviewer="R1", value="reached", finding=0)])]
    assert M.flat_rows(asks) == [{"pr": 7, "ask_id": "a1", "R1": "reached", "R1_finding": 0,
                                  "R2": "no", "R2_finding": None, "note": "n"}]
