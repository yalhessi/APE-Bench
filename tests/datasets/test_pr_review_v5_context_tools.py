"""The gates. A context read that could see the future must not be possible to perform.

These are the tests that protect a result rather than a run. An ungated retrieval does not
crash; it quietly hands the arm the answer, and every number downstream of it is wrong
without anything saying so. So the assertions here are about *reachability*: not "the filter
usually applies" but "there is no code path to the corpus that skips it".

The cutoff itself is also checked empirically. It is derived from the reviewed commit rather
than from `review_started_at`, because the latter lives under `gold/`; the test confirms
that choice is conservative on every episode we have, not merely defensible in a docstring.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.mathlib_review.io import load_jsonl
from src.mathlib_review.schema import ReviewEpisodeBoundary, ReviewEpisodeInput
from src.mathlib_review.agenda.cutoffs import (
    CutoffUnavailable,
    cutoffs_by_episode,
    episode_cutoff,
)

RELEASE = Path("inputs/pr_review_v4/releases/dev-medium-0.3.0")


@pytest.fixture(scope="module")
def episodes():
    return load_jsonl(RELEASE / "input/episodes.jsonl", ReviewEpisodeInput)


# --------------------------------------------------------------------------------------
# the cutoff
# --------------------------------------------------------------------------------------

def test_every_episode_resolves_a_cutoff(episodes):
    resolved = cutoffs_by_episode(episodes)
    assert set(resolved) == {item.episode_id for item in episodes}
    assert all(value.endswith("Z") for value in resolved.values())


def test_the_cutoff_never_postdates_the_real_review_start(episodes):
    """The conservativeness claim, checked rather than asserted.

    Gold is read *here*, in a test, precisely because the generation path may not read it.
    If this ever fails, arms are being handed discussion written after review began.
    """

    boundaries = {
        item.episode_id: item.review_started_at
        for item in load_jsonl(RELEASE / "gold/episode_boundaries.jsonl", ReviewEpisodeBoundary)
    }
    resolved = cutoffs_by_episode(episodes)
    compared = 0
    for episode_id, cutoff in resolved.items():
        started = boundaries.get(episode_id)
        if started is None:
            continue
        compared += 1
        assert cutoff <= started, (
            f"{episode_id}: cutoff {cutoff} is after review start {started}"
        )
    assert compared, "no boundaries to compare against — the guarantee is untested"


def test_an_unresolvable_cutoff_raises_instead_of_defaulting(episodes):
    """Never `now`, never `None`. A default here is a silent leak."""

    broken = episodes[0].model_copy(update={"reviewed_head_sha": "0" * 40})
    with pytest.raises(CutoffUnavailable):
        episode_cutoff(broken)


def test_one_unresolvable_episode_fails_the_whole_map(episodes):
    """All-or-nothing: a partial map runs some arms gated and others not, inside one
    comparison, and the ungated ones look better."""

    broken = episodes[0].model_copy(update={"reviewed_head_sha": "0" * 40})
    with pytest.raises(CutoffUnavailable):
        cutoffs_by_episode([broken] + list(episodes[1:]))


# --------------------------------------------------------------------------------------
# the tools
# --------------------------------------------------------------------------------------

class FakeMCP:
    def __init__(self):
        self.tools = {}

    def tool(self, **_kwargs):
        def decorate(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorate


def _task(tmp_path, context_tools, cutoff="2025-06-01T00:00:00Z", pr_number=33098):
    return SimpleNamespace(
        data=SimpleNamespace(
            invocation_id="wu:abc#proof_golf",
            arm_id="proof_golf",
            pr_number=pr_number,
            snapshot_base_sha="deadbeef",
            context_tools=list(context_tools),
            retrieval_cutoff=cutoff,
            trace_path=str(tmp_path / "trace.jsonl"),
        ),
        logger=SimpleNamespace(warning=lambda *a, **k: None, info=lambda *a, **k: None),
    )


def _register(task):
    from ape.tasks.lean_tasks.formal_math.pr_review_v5.context_tools import (
        register_context_tools,
    )

    mcp = FakeMCP()
    register_context_tools(task, mcp)
    return mcp


def test_only_granted_tools_are_registered(tmp_path):
    assert set(_register(_task(tmp_path, ["zulip_search"])).tools) == {"zulip_search"}
    assert set(_register(_task(tmp_path, [])).tools) == set()
    granted = ["zulip_search", "precedent_search", "declaration_search"]
    assert set(_register(_task(tmp_path, granted)).tools) == set(granted)


def test_lean_verify_edit_is_not_registered_here(tmp_path):
    """It comes from the shared review base; registering it again would shadow it."""

    mcp = _register(_task(tmp_path, ["lean_verify_edit"]))
    assert "lean_verify_edit" not in mcp.tools


def test_zulip_search_always_passes_both_gates(tmp_path, monkeypatch):
    """Not "the results are filtered" — that the store is never reached without the gate."""

    seen = {}

    class RecordingStore:
        def __init__(self, path):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def search(self, query, **kwargs):
            seen["search"] = kwargs
            return []

        def threads_mentioning(self, declaration, **kwargs):
            seen["threads"] = kwargs
            return []

    import src.datasets.zulip.store as store_module

    monkeypatch.setattr(store_module, "ZulipStore", RecordingStore)
    monkeypatch.setattr(Path, "is_file", lambda self: True)

    task = _task(tmp_path, ["zulip_search"], cutoff="2025-06-01T00:00:00Z", pr_number=33098)
    tool = _register(task).tools["zulip_search"]

    asyncio.run(tool(query="grind"))
    assert seen["search"]["as_of"] == "2025-06-01T00:00:00Z"
    assert seen["search"]["exclude_pr"] == 33098

    asyncio.run(tool(query="x", declaration="Finset.sum_comm"))
    assert seen["threads"]["as_of"] == "2025-06-01T00:00:00Z"
    assert seen["threads"]["exclude_pr"] == 33098


def test_a_gated_tool_refuses_to_run_without_a_cutoff(tmp_path):
    """Refuses, rather than reading everything. The failure is the safe behaviour."""

    task = _task(tmp_path, ["zulip_search", "precedent_search"], cutoff=None)
    tools = _register(task).tools
    for name in ("zulip_search", "precedent_search"):
        result = asyncio.run(tools[name](**({"query": "x"} if "zulip" in name else {"code": "x"})))
        assert result["success"] is False
        assert "cutoff" in result["error"]


def test_declaration_search_rejects_prose(tmp_path):
    """The measured defect this guards: a substring search matched English words like "the"
    in 193 of 200 sampled Mathlib files, handing every duplication claim a `supports`."""

    task = _task(tmp_path, ["declaration_search"])
    tool = _register(task).tools["declaration_search"]
    result = asyncio.run(tool(identifier="the new declaration should be removed"))
    # Either it refuses outright, or it searched only identifier-shaped terms — never prose.
    if result.get("success"):
        assert all(len(term) > 2 and term.lower() not in {"the", "new", "should", "be"}
                   for term in result["searched_terms"])
    else:
        assert "identifier-shaped" in result["error"]


def test_context_calls_are_traced_even_when_a_read_returns_nothing(tmp_path, monkeypatch):
    """A job that fails or pauses returns no result; its trace is the only evidence of what
    it tried, so the trace is written as the call happens."""

    class EmptyStore:
        def __init__(self, path):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def search(self, query, **kwargs):
            return []

    import src.datasets.zulip.store as store_module

    monkeypatch.setattr(store_module, "ZulipStore", EmptyStore)
    monkeypatch.setattr(Path, "is_file", lambda self: True)

    task = _task(tmp_path, ["zulip_search"])
    tool = _register(task).tools["zulip_search"]
    asyncio.run(tool(query="nothing matches this"))

    lines = [x for x in (tmp_path / "trace.jsonl").read_text().splitlines() if x.strip()]
    assert len(lines) == 1
    import json

    row = json.loads(lines[0])
    assert row["tool"] == "zulip_search"
    assert row["as_of"] == "2025-06-01T00:00:00Z"
    assert row["exclude_pr"] == 33098
    assert row["result_count"] == 0
    assert row["invocation_id"] == "wu:abc#proof_golf"


# --------------------------------------------------------------------------------------
# the precedent index
# --------------------------------------------------------------------------------------

INDEX_DIR = Path("data/pr_review_v5/precedent_index")
requires_index = pytest.mark.skipif(
    not (INDEX_DIR / "manifest.json").is_file(),
    reason="precedent index not built (python -m src.mathlib_review.retrieval.precedent_index build)",
)


@requires_index
def test_precedent_filtering_happens_before_ranking():
    """Filtering a ranked top-k afterwards silently shortens it: a query whose best matches
    are all ineligible would return two weak precedents and look like a thin corpus rather
    than a gated one."""

    from src.mathlib_review.retrieval.precedent_index import PrecedentIndex

    index = PrecedentIndex.shared()
    cutoff = "2025-01-01T00:00:00Z"
    eligible = int(index.eligible_mask(cutoff, None).sum())
    assert 0 < eligible < index.embeddings.shape[0], "the gate must actually remove rows"
    hits = index.search("theorem foo : 1 = 1 := by simp", k=5, as_of=cutoff)
    assert len(hits) == 5, "a full page is returned from the eligible set, not a filtered stub"


@requires_index
def test_no_precedent_postdates_the_cutoff_or_comes_from_the_reviewed_pr():
    from src.mathlib_review.retrieval.precedent_index import PrecedentIndex

    index = PrecedentIndex.shared()
    cutoff = "2025-03-01T00:00:00Z"
    hits = index.search(
        "lemma upperBounds_image : upperBounds s = t := by simp",
        k=8, as_of=cutoff, exclude_pr=21493,
    )
    assert hits
    for hit in hits:
        assert hit["created_at"] < cutoff
        assert hit["pr_number"] != 21493


@requires_index
def test_the_index_excludes_the_eval_prs():
    """Belt and suspenders over the corpus builder's own exclusion: the index must be safe
    even if it is ever pointed at a corpus whose provenance is not this repo's."""

    from src.datasets.pr_review_v2.corpus import _eval_pr_numbers
    from src.mathlib_review.retrieval.precedent_index import PrecedentIndex

    index = PrecedentIndex.shared()
    excluded = _eval_pr_numbers()
    assert excluded, "no eval PR list found — the exclusion is untested"
    assert not (excluded & {row["pr_number"] for row in index.meta})
