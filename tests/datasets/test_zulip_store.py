"""
Gates for the Zulip discussion store.

The load-bearing tests here are the temporal-gate ones. Everything else in this
package is convenience; `gate()` is the property that makes the store safe to hand to
anything emulating a reviewer, and it is the kind of bug that produces plausible
results rather than a crash.
"""

import json
from pathlib import Path

import pytest

from src.datasets.zulip.datetimes import epoch_to_iso, iso_to_epoch
from src.datasets.zulip.html_text import extract
from src.datasets.zulip.identity import Identities, Person, is_bot
from src.datasets.zulip.io import jsonl_bytes
from src.datasets.zulip.normalize import (
    decode_archive_name,
    normalize_topic,
    split_stream_dir,
)
from src.datasets.zulip.schema import ZulipMessage
from src.datasets.zulip.store import ZulipStore, gate, parse_narrow_url
from src.datasets.zulip.tags import decl_refs, file_refs, is_poll, pr_refs, topic_pr_ref

FIXTURES = Path(__file__).parent / "fixtures" / "zulip"


@pytest.fixture
def identities():
    return Identities(
        {
            "Jireh Loreaux": Person("Jireh Loreaux", "j-loreaux", True),
            "Kevin Buzzard": Person("Kevin Buzzard", "kbuzzard", True),
        }
    )


# --- HTML extraction -----------------------------------------------------


def test_code_block_keeps_language_and_boundary():
    html = (
        '<p>try this:</p><div class="codehilite" data-code-language="Lean4"><pre>'
        '<span></span><code><span class="k">theorem</span><span class="w"> </span>'
        '<span class="n">foo</span></code></pre></div>'
    )
    result = extract(html)
    assert result.code_blocks == [("Lean4", "theorem foo")]
    assert "```Lean4" in result.text


def test_docs_link_target_is_kept_not_just_anchor_text():
    html = (
        '<p>use <a href="https://leanprover-community.github.io/mathlib4_docs/find/'
        '?pattern=BddAbove.closure#doc">docs#BddAbove.closure</a></p>'
    )
    result = extract(html)
    assert result.hrefs == [
        "https://leanprover-community.github.io/mathlib4_docs/find/"
        "?pattern=BddAbove.closure#doc"
    ]


def test_katex_emits_latex_once_and_suppresses_the_glyph_pile():
    """A formula is rendered twice by KaTeX; naive stripping duplicates it as noise."""
    html = (
        '<p>a <span class="katex"><span class="katex-mathml"><math><semantics><mrow>'
        '<mi>Z</mi></mrow><annotation encoding="application/x-tex">\\Z</annotation>'
        '</semantics></math></span><span class="katex-html" aria-hidden="true">'
        '<span class="base"><span class="mord">Z</span></span></span></span>-action</p>'
    )
    assert extract(html).text == "a $\\Z$-action"


def test_mentions_and_quotes():
    html = (
        '<blockquote><p><span class="user-mention">@Kevin Buzzard</span> said:</p>'
        "<p>quoted</p></blockquote><p>reply</p>"
    )
    result = extract(html)
    assert result.mentions == ["Kevin Buzzard"]
    assert result.has_quote is True
    assert "reply" in result.text


def test_extract_never_raises_on_malformed_markup():
    assert extract("<p>unclosed <span class='katex'><code>x").text is not None


# --- tags ----------------------------------------------------------------


def test_pr_refs_from_href_and_bang_spelling():
    href = "https://github.com/leanprover-community/mathlib4/pull/33145"
    assert pr_refs("see !4#33145", []) == [33145]
    assert pr_refs("", [href]) == [33145]


def test_mathlib3_bang_refs_are_a_different_numbering_space():
    assert pr_refs("see !3#17828", []) == []


def test_bare_hash_is_not_read_as_a_pr():
    assert pr_refs("my #1 problem, see section #3", []) == []


def test_decl_refs_combine_docs_links_and_dotted_backticks():
    href = "https://leanprover-community.github.io/mathlib4_docs/find/?pattern=Set.encard#doc"
    names = decl_refs("also `BddAbove.closure` and `plain`", [href])
    assert "Set.encard" in names
    assert "BddAbove.closure" in names
    assert "plain" not in names  # undotted backticks are as often prose as declarations


def test_file_refs_and_poll_and_topic_pr_ref():
    assert file_refs("edit Mathlib/Order/Bounds/Basic.lean now") == [
        "Mathlib/Order/Bounds/Basic.lean"
    ]
    assert is_poll("/poll which spelling?") is True
    assert is_poll("a /poll mid-sentence") is False
    assert topic_pr_ref("!4#33145 feat: dense supremum") == 33145
    assert topic_pr_ref("no pr here") is None


def test_bot_detection_uses_display_names_not_github_logins():
    """Zulip has no `[bot]` login suffix, so v2's login rule does not transfer."""
    assert is_bot("github mathlib4 bot")
    assert is_bot("Notification Bot")
    assert is_bot("Random Issue Bot")
    assert not is_bot("Kevin Buzzard")
    # Word-boundary matching, so a surname containing "bot" is not a bot.
    assert not is_bot("Robert Botman")


# --- archive naming ------------------------------------------------------


def test_decode_archive_name_handles_dot_and_percent_escapes():
    assert decode_archive_name("Continuous.20function") == "Continuous function"
    assert decode_archive_name("Is-there-code-for-X%3F") == "Is-there-code-for-X?"


def test_split_stream_dir_allows_a_slash_in_the_stream_name():
    assert split_stream_dir("287929-mathlib4") == (287929, "mathlib4")
    assert split_stream_dir("239415-metaprogramming-/-tactics") == (
        239415,
        "metaprogramming-/-tactics",
    )


# --- URL parsing ---------------------------------------------------------


@pytest.mark.parametrize(
    "url",
    [
        "https://leanprover.zulipchat.com/#narrow/channel/287929-mathlib4/topic/Foo.20bar/near/12",
        "https://leanprover.zulipchat.com/#narrow/stream/287929-mathlib4/topic/Foo.20bar/near/12",
        "https://leanprover.zulipchat.com/#narrow/channel/287929-mathlib4/topic/Foo.20bar/with/12",
    ],
)
def test_parse_narrow_url_spellings(url):
    assert parse_narrow_url(url) == (287929, "Foo bar", 12)


def test_parse_narrow_url_without_anchor_or_topic():
    assert parse_narrow_url(
        "https://leanprover.zulipchat.com/#narrow/channel/287929-mathlib4"
    ) == (287929, None, None)
    assert parse_narrow_url("https://example.com/not-zulip") == (None, None, None)


# --- timestamps ----------------------------------------------------------


def test_iso_roundtrip_and_naive_input_is_utc():
    assert epoch_to_iso(1772078229) == "2026-02-26T03:57:09Z"
    assert iso_to_epoch("2026-02-26T03:57:09Z") == 1772078229
    assert iso_to_epoch("2026-02-26T03:57:09") == 1772078229
    assert iso_to_epoch("2026-02-26") == iso_to_epoch("2026-02-26T00:00:00Z")


# --- the temporal gate ---------------------------------------------------


def _message(message_id: int, epoch: int, pr_refs_=()) -> ZulipMessage:
    return ZulipMessage(
        message_id=message_id,
        stream_id=1,
        stream="s",
        topic="t",
        thread_key="1/t",
        sender_full_name="A",
        timestamp_epoch=epoch,
        timestamp=epoch_to_iso(epoch),
        text=f"m{message_id}",
        permalink="p",
        pr_refs=list(pr_refs_),
    )


def test_gate_is_exclusive_at_the_cutoff():
    """A message posted at the review-start instant was not available beforehand."""
    messages = [_message(1, 100), _message(2, 200), _message(3, 300)]
    kept = gate(messages, as_of=epoch_to_iso(200))
    assert [m.message_id for m in kept] == [1]


def test_gate_drops_messages_about_the_pr_under_review_regardless_of_time():
    """Time alone does not exclude a thread that is *about* the PR being reviewed."""
    messages = [_message(1, 100), _message(2, 110, pr_refs_=[33145])]
    kept = gate(messages, as_of=epoch_to_iso(500), exclude_pr=33145)
    assert [m.message_id for m in kept] == [1]


def test_gate_without_arguments_is_the_identity():
    messages = [_message(1, 100), _message(2, 200)]
    assert len(gate(messages)) == 2


@pytest.mark.parametrize("cutoff", [50, 150, 250, 350])
def test_gate_property_no_message_at_or_after_cutoff_survives(cutoff):
    messages = [_message(i, i * 100) for i in range(1, 4)]
    for message in gate(messages, as_of=epoch_to_iso(cutoff)):
        assert message.timestamp_epoch < cutoff


# --- store round trip ----------------------------------------------------


@pytest.fixture
def built_store(tmp_path, identities):
    topic = FIXTURES / "sample_topic.json"
    messages, thread = normalize_topic(topic, "287929-mathlib4", identities)
    path = tmp_path / "zulip.sqlite3"
    ZulipStore.build(path, messages, thread and [thread] or [])
    return path, messages, thread


def test_store_roundtrip_preserves_every_field(built_store):
    path, messages, _ = built_store
    with ZulipStore(path) as store:
        for original in messages:
            assert store.message(original.message_id) == original


def test_store_search_and_reference_lookup(built_store):
    path, _, thread = built_store
    with ZulipStore(path) as store:
        assert store.search("supremum")
        assert store.threads_mentioning("BddAbove.closure")
        assert store.thread(287929, thread.topic) is not None


def test_store_search_applies_the_gate(built_store):
    path, messages, _ = built_store
    cutoff = epoch_to_iso(messages[1].timestamp_epoch)
    with ZulipStore(path) as store:
        for hit in store.search("the", as_of=cutoff, limit=50):
            assert hit.timestamp < cutoff


def test_resolve_url_prefers_the_message_anchor_over_the_topic(built_store):
    """A topic can be renamed or moved; a message id cannot."""
    path, messages, _ = built_store
    anchor = messages[0].message_id
    url = (
        "https://leanprover.zulipchat.com/#narrow/channel/287929-mathlib4"
        f"/topic/a.20renamed.20topic/near/{anchor}"
    )
    with ZulipStore(path) as store:
        view = store.resolve_url(url)
    assert view is not None
    assert view.thread.message_count == len(messages)


def test_thread_view_reports_truncation(built_store):
    path, messages, _ = built_store
    cutoff = epoch_to_iso(messages[-1].timestamp_epoch)
    with ZulipStore(path) as store:
        view = store.resolve_url(messages[0].permalink, as_of=cutoff)
    assert view.truncated is True
    assert len(view.messages) < view.thread.message_count


def test_bots_are_excluded_from_search_by_default(tmp_path, identities):
    bot = _message(9001, 1000)
    bot.sender_full_name = "Notification Bot"
    bot.sender_is_bot = True
    bot.text = "unique-token-xyzzy"
    human = _message(9002, 1001)
    human.text = "unique-token-xyzzy"
    path = ZulipStore.build(tmp_path / "s.sqlite3", [bot, human], [])
    with ZulipStore(path) as store:
        assert [m.message_id for m in store.search("xyzzy")] == [9002]
        assert len(store.search("xyzzy", exclude_bots=False)) == 2


# --- determinism ---------------------------------------------------------


def test_normalization_is_byte_reproducible(identities):
    topic = FIXTURES / "sample_topic.json"
    first, _ = normalize_topic(topic, "287929-mathlib4", identities)
    second, _ = normalize_topic(topic, "287929-mathlib4", identities)
    assert jsonl_bytes(first) == jsonl_bytes(second)


def test_normalize_topic_tolerates_a_broken_file(tmp_path, identities):
    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    assert normalize_topic(broken, "287929-mathlib4", identities) == ([], None)

    empty = tmp_path / "empty.json"
    empty.write_text("[]", encoding="utf-8")
    assert normalize_topic(empty, "287929-mathlib4", identities) == ([], None)


# --- identity ------------------------------------------------------------


def test_derived_roster_matches_the_v2_snapshot():
    """The two packages derive the roster independently; they must agree."""
    from src.datasets.zulip.identity import load_identities

    snapshot = Path("src/datasets/pr_review_v2/data/mathlib_roster.txt")
    if not snapshot.exists():  # pragma: no cover - repo layout guard
        pytest.skip("v2 roster snapshot not present")
    v2 = {
        line.strip()
        for line in snapshot.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }
    derived = load_identities().maintainer_logins()
    assert v2 <= derived, f"v2 roster logins missing from the Zulip identity map: {v2 - derived}"


def test_identity_resolution_is_total():
    from src.datasets.zulip.identity import load_identities

    identities = load_identities()
    assert identities.resolve("Definitely Not A Real Person") == (None, False)
    assert identities.resolve("Kevin Buzzard") == ("kbuzzard", True)
