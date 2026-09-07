"""One answer to "was this available to the reviewer?", and the two ways the copies differed.

Four sources each spelled the rule themselves, with three ISO parsers between them:

    zulip.store.gate               `timestamp_epoch >= cutoff` drop; drop on `pr_refs`
    precedent_index.eligible_mask  `_created < _iso_to_epoch(as_of)` keep; `_pr != exclude_pr`
    retrieval.eligible_precedents  `occurred < start` keep; drop on `pr_number`
    retrieval.validate_precedents  `occurred >= start` raises; same

They agreed on the boundary and disagreed on everything around it.
"""

from __future__ import annotations

import pytest

from src.mathlib_review.retrieval_gate import RetrievalGate, UngatedTimestamp

CUTOFF = "2026-08-01T12:00:00Z"


# --- the rule ------------------------------------------------------------------------------


def test_the_cutoff_is_exclusive():
    """Something written at exactly the instant review began was not available beforehand.
    All four implementations agreed on this and none said it where the others could read it."""

    gate = RetrievalGate(as_of=CUTOFF)
    assert gate.allows(timestamp="2026-08-01T11:59:59Z")
    assert not gate.allows(timestamp=CUTOFF)
    assert not gate.allows(timestamp="2026-08-01T12:00:01Z")


def test_no_cutoff_admits_everything_in_time():
    gate = RetrievalGate()
    assert gate.allows(timestamp="2030-01-01T00:00:00Z")
    assert gate.cutoff_epoch is None


def test_self_exclusion_has_two_forms_because_the_sources_need_different_ones():
    """Zulip excludes a message that *references* the PR -- a maintainer discussing it in
    another thread is still discussing it. The precedent sources exclude rows that *originate*
    in it. Both are right for their source and neither was written down."""

    gate = RetrievalGate(as_of=CUTOFF, exclude_pr=33117)
    assert gate.excludes_pr(pr_number=33117)
    assert gate.excludes_pr(pr_refs=[33117, 40000])
    assert not gate.excludes_pr(pr_number=33118, pr_refs=[40000])


def test_a_caller_that_passes_only_what_it_has_gets_only_that_check():
    gate = RetrievalGate(exclude_pr=33117)
    assert not gate.excludes_pr(pr_number=33118)   # no refs offered, none checked
    assert not gate.excludes_pr(pr_refs=[33118])   # no origin offered, none checked


# --- the parser, and the two ways the copies were wrong -------------------------------------


def test_an_undated_row_is_refused_rather_than_dated_to_the_epoch():
    """`precedent_index._iso_to_epoch` returned 0 on failure. Zero is before every real
    cutoff, so a row with a missing or malformed timestamp was eligible for *every* review --
    a leak gate failing open, in the only direction it could fail."""

    gate = RetrievalGate(as_of=CUTOFF)
    for bad in (None, "", "not-a-date"):
        with pytest.raises(UngatedTimestamp):
            gate.allows(timestamp=bad)


def test_a_naive_timestamp_is_read_as_utc():
    """It used to go through `datetime.fromisoformat(...).timestamp()`, which resolves a naive
    stamp in the machine's local time. Measured four hours off on a UTC-4 machine -- and off
    the other way east of UTC, where it over-includes. Eligibility must not depend on where
    the index was built."""

    gate = RetrievalGate(as_of=CUTOFF)
    assert gate.epoch_of("2026-08-01T12:00:00") == gate.epoch_of("2026-08-01T12:00:00Z")
    assert gate.epoch_of("2026-08-01") == gate.epoch_of("2026-08-01T00:00:00Z")


def test_a_bare_date_is_midnight_utc():
    assert RetrievalGate().epoch_of("2026-08-01") == RetrievalGate().epoch_of(
        "2026-08-01T00:00:00+00:00")


# --- the sources agree ----------------------------------------------------------------------


def test_zulip_and_the_shared_gate_agree_on_the_boundary():
    from src.datasets.zulip.datetimes import iso_to_epoch
    from src.datasets.zulip.schema import ZulipMessage
    from src.datasets.zulip.store import gate

    def _message(stamp, refs=()):
        return ZulipMessage(
            message_id=1, thread_key="k", stream="s", stream_id=1, topic="t",
            sender_full_name="n", timestamp_epoch=iso_to_epoch(stamp), timestamp=stamp,
            text="c", permalink="p", pr_refs=list(refs),
        )

    before, exact = _message("2026-08-01T11:59:59Z"), _message(CUTOFF)
    kept = gate([before, exact], as_of=CUTOFF)
    assert [m.timestamp_epoch for m in kept] == [before.timestamp_epoch]

    rule = RetrievalGate(as_of=CUTOFF)
    assert rule.allows(timestamp="2026-08-01T11:59:59Z")
    assert not rule.allows(timestamp=CUTOFF)


def test_zulip_still_excludes_by_reference_not_by_origin():
    """The per-source half. Collapsing this into origin-only exclusion would let a maintainer's
    comment about the PR under review reach the reviewer."""

    from src.datasets.zulip.datetimes import iso_to_epoch
    from src.datasets.zulip.schema import ZulipMessage
    from src.datasets.zulip.store import gate

    message = ZulipMessage(
        message_id=1, thread_key="k", stream="s", stream_id=1, topic="t",
        sender_full_name="n", sender_is_maintainer=True,
        timestamp_epoch=iso_to_epoch("2026-01-01T00:00:00Z"),
        timestamp="2026-01-01T00:00:00Z", text="c", permalink="p", pr_refs=[33117],
    )
    assert gate([message], as_of=CUTOFF, exclude_pr=33117) == []
    assert gate([message], as_of=CUTOFF, exclude_pr=33118) == [message]


def test_the_precedent_index_refuses_an_undated_row_under_a_cutoff():
    """The vectorised form of the same refusal."""

    from src.mathlib_review.retrieval.precedent_index import UNDATED, _iso_to_epoch

    assert _iso_to_epoch(None) == UNDATED
    assert _iso_to_epoch("not-a-date") == UNDATED
    assert _iso_to_epoch("2026-08-01T00:00:00Z") > 0


def test_the_precedent_index_reads_a_naive_stamp_as_utc():
    from src.mathlib_review.retrieval.precedent_index import _iso_to_epoch

    assert _iso_to_epoch("2026-08-01T12:00:00") == _iso_to_epoch("2026-08-01T12:00:00Z")


def test_no_source_parses_timestamps_for_itself_any_more():
    """The property that keeps them agreeing. A source may pre-filter with `cutoff_epoch` --
    `zulip.store.search` does, over-fetching so the gate can still drop rows -- but must not
    date a row itself.

    Checked on the syntax tree rather than the text, so the comments explaining what the old
    parse did are not mistaken for the old parse.
    """

    import ast
    from pathlib import Path

    for path in (Path("src/mathlib_review/retrieval/precedent_index.py"),
                 Path("src/datasets/pr_review_v4/retrieval.py"),
                 Path("src/datasets/zulip/store.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        calls = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "fromisoformat"
        ]
        assert not calls, (
            f"{path}:{calls[0].lineno} dates a row itself; the gate owns that")


# --- every retrieval call says how it was bounded ------------------------------------------


def test_every_context_tool_records_a_gate():
    """`as_of: null` meant two different things and the trace could not tell them apart.

    `declaration_search` reads the tree at the PR's base commit, so nothing from the PR under
    review and nothing after it can appear -- gated by the corpus, not by a cutoff, and its
    `as_of`/`exclude_pr` are correctly null. A call that was simply never gated would look
    identical, and telling those apart is the one question an audit of `context_trace.jsonl`
    exists to answer.
    """

    from pathlib import Path

    source = Path(
        "src/ape/tasks/lean_tasks/formal_math/pr_review_v5/context_tools.py"
    ).read_text(encoding="utf-8")

    tools = ("zulip_search", "precedent_search", "declaration_search")
    for tool in tools:
        marker = f'"tool": "{tool}",\n            "gate": '
        assert marker in source, f"{tool} records no gate"

    # Every trace row that names a tool names a gate on the next line: no tool can be added
    # without declaring how it is bounded.
    assert source.count('"gate": ') == len(tools)


def test_the_gate_kinds_are_a_closed_set():
    """A free-text gate would let a new tool declare `"gate": "probably fine"`."""

    from src.mathlib_review.schema.review import ContextCall

    annotation = ContextCall.model_fields["gate"].annotation
    assert set(getattr(annotation, "__args__", ())) == {"as_of", "base_snapshot"}


def test_a_base_snapshot_call_carries_the_commit_it_read():
    """It is the bound, so it has to be recorded. `corpus_sha256` holds the base sha for
    `declaration_search`, where `as_of` holds the cutoff for the other two."""

    from pathlib import Path

    source = Path(
        "src/ape/tasks/lean_tasks/formal_math/pr_review_v5/context_tools.py"
    ).read_text(encoding="utf-8")
    block = source[source.index('"tool": "declaration_search"'):]
    block = block[:block.index("return {")]
    assert '"gate": "base_snapshot"' in block
    assert '"corpus_sha256": task.data.snapshot_base_sha' in block
