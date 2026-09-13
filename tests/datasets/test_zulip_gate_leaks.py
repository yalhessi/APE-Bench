"""The Zulip gate must cover what is said ABOUT messages, and which threads are selected.

Which *messages* cross the gate was always right: `_require_cutoff` refuses to read without a
cutoff, `gate()` is the single rule, `_view` applies it per message inside a thread, and the
`as_of` predicate is in the SQL `WHERE` as well. Two things around it were not.

**The summary.** `ZulipStore._view` gates a thread's messages correctly. `render_thread` printed a header
built from the `threads` row -- `message_count`, `last_ts`, `maintainer_participants`,
`decl_refs`, `pr_refs` -- all of which the builder computed over the WHOLE thread. So the
messages were gated and the summary of them was not.

Measured against PR 33337's cutoff (2025-12-27T13:43:05Z) over the 400 stored threads that span
it: the header would have carried post-cutoff `last_ts` and `message_count` in 100% of them --
one printing 2026-06-16, nearly six months late -- post-cutoff `pr_refs` in 29%,
`maintainer_participants` in 28% and `decl_refs` in 22%. A declaration name from the future,
handed to the arm whose whole job is to judge a name, is the worst case this repository has a
word for.

The fix is to derive every summary line from the `messages` argument, which is already gated.
That is also correct for an ungated human browse, where the two sets coincide.
"""

from __future__ import annotations

from src.datasets.zulip.render import render_thread
from src.datasets.zulip.schema import ZulipMessage, ZulipThread


def _message(mid: int, ts: str, *, text="hi", maintainer=False, decls=(), prs=(), sender="Ann"):
    return ZulipMessage(
        message_id=mid, stream_id=1, stream="mathlib4", topic="Naming convention",
        thread_key="t1", sender_full_name=sender, sender_github=None,
        sender_is_maintainer=maintainer, sender_is_bot=False,
        timestamp_epoch=0, timestamp=ts, text=text, code_blocks=[], permalink="u",
        pr_refs=list(prs), issue_refs=[], decl_refs=list(decls), file_refs=[], mentions=[],
        code_langs=[], has_lean_code=False, is_poll=False, is_reply_quote=False, semantic=None,
    )


def _thread():
    """The stored row: aggregates over the whole thread, including the future half."""

    return ZulipThread(
        thread_key="t1", stream_id=1, stream="mathlib4", topic="Naming convention",
        message_count=9, first_ts="2025-01-01T00:00:00Z", last_ts="2026-06-16T03:16:23Z",
        maintainer_participants=["Ann", "FutureMaintainer"],
        decl_refs=["Submodule.coe_starProjection", "toLinearMap_futureRename"],
        pr_refs=[111, 99999], archive_url="https://example/thread",
        first_ts_epoch=0, last_ts_epoch=0,
    )


def test_the_header_never_names_a_declaration_only_a_removed_message_mentioned():
    """The leak that matters here: a naming arm being shown the rename that happened later."""

    shown = [_message(1, "2025-02-01T00:00:00Z", decls=["Submodule.coe_starProjection"],
                      maintainer=True)]
    out = render_thread(_thread(), shown, truncated=True)
    assert "Submodule.coe_starProjection" in out
    assert "toLinearMap_futureRename" not in out, "a post-cutoff declaration name leaked"


def test_the_header_never_shows_a_future_timestamp_or_a_future_count():
    shown = [_message(1, "2025-02-01T00:00:00Z"), _message(2, "2025-02-02T00:00:00Z")]
    out = render_thread(_thread(), shown, truncated=True)
    assert "2026-06-16T03:16:23Z" not in out, "the whole thread's last_ts leaked"
    assert "2025-02-02T00:00:00Z" in out, "the last visible message dates the thread"
    assert "9" not in out.split("https://example")[0], "the ungated message count leaked"
    assert "2 message(s)" in out and "(prefix)" in out


def test_the_header_never_names_a_person_or_a_pr_from_a_removed_message():
    shown = [_message(1, "2025-02-01T00:00:00Z", maintainer=True, prs=[111], sender="Ann")]
    out = render_thread(_thread(), shown, truncated=True)
    assert "Ann" in out and "#111" in out
    assert "FutureMaintainer" not in out, "a maintainer who only posted later leaked"
    assert "99999" not in out, "a PR referenced only later leaked"


def test_an_ungated_render_is_unchanged_in_substance():
    """browse.py renders whole threads for a human; deriving from `messages` gives the same
    answer there, because nothing was removed."""

    shown = [_message(1, "2025-02-01T00:00:00Z", maintainer=True, decls=["A.b"], prs=[111]),
             _message(2, "2025-03-01T00:00:00Z", decls=["C.d"], sender="Bob")]
    out = render_thread(_thread(), shown, truncated=False)
    assert "A.b" in out and "C.d" in out and "#111" in out
    assert "(prefix)" not in out and "NOTE:" not in out


def test_an_empty_thread_renders_without_inventing_a_span():
    assert "(no messages)" in render_thread(_thread(), [], truncated=True)


# --- which threads are selected -------------------------------------------------------


def _built(tmp_path):
    """A thread whose declaration is first mentioned only after the cutoff."""

    from src.datasets.zulip.schema import ZulipThread
    from src.datasets.zulip.store import ZulipStore

    early = _message(1, "2025-01-01T00:00:00Z", text="unrelated chat", decls=["Old.name"])
    late = _message(2, "2026-06-01T00:00:00Z", text="rename it", decls=["Future.name"])
    early.timestamp_epoch, late.timestamp_epoch = 1_000, 9_000
    thread = ZulipThread(
        thread_key="t1", stream_id=1, stream="mathlib4", topic="Naming convention",
        message_count=2, first_ts=early.timestamp, last_ts=late.timestamp,
        maintainer_participants=[], decl_refs=["Old.name", "Future.name"], pr_refs=[],
        archive_url="https://example/thread", first_ts_epoch=1_000, last_ts_epoch=9_000,
    )
    path = tmp_path / "zulip.sqlite3"
    ZulipStore.build(path, [early, late], [thread])
    return path


def test_a_declaration_named_only_after_the_cutoff_selects_no_thread(tmp_path):
    """The `refs` table is built over the whole thread, so selecting on it alone answers
    "some message here mentions X" for messages the gate is about to remove -- an existence
    claim about the future. On the real store, 89 of 2,920 declaration references did this."""

    from src.datasets.zulip.datetimes import epoch_to_iso
    from src.datasets.zulip.store import ZulipStore

    with ZulipStore(_built(tmp_path)) as store:
        cutoff = epoch_to_iso(5_000)
        assert store.threads_mentioning("Future.name", as_of=cutoff) == [], (
            "a declaration first mentioned after the cutoff must select nothing")
        assert [v.thread.thread_key for v in store.threads_mentioning("Old.name", as_of=cutoff)] \
            == ["t1"], "a declaration mentioned before the cutoff still selects its thread"


def test_without_a_cutoff_both_declarations_select_the_thread(tmp_path):
    """The re-check is the gate's, not a new filter: ungated, nothing is dropped."""

    from src.datasets.zulip.store import ZulipStore

    with ZulipStore(_built(tmp_path)) as store:
        assert len(store.threads_mentioning("Future.name")) == 1
        assert len(store.threads_mentioning("Old.name")) == 1
