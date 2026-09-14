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
    from ape.tasks.lean_tasks.formal_math.review.context_tools import (
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


# --- declaration_search sees the PR's own changed files --------------------------------------


def _task_with_overlay(tmp_path, base_text, reviewed_text):
    """A base snapshot and a reviewed overlay that disagree about one declaration."""

    base = tmp_path / "base" / "Mathlib"
    base.mkdir(parents=True)
    (base / "A.lean").write_text(base_text)
    target = tmp_path / "target" / "Mathlib"
    target.mkdir(parents=True)
    (target / "A.lean").write_text(reviewed_text)

    task = _task(tmp_path, ["declaration_search"])
    task.data.changed_files = ["Mathlib/A.lean"]
    task.target_workspace = SimpleNamespace(path=tmp_path / "target")
    return task, tmp_path / "base"


def test_a_name_the_pr_introduces_is_found_in_the_reviewed_file(tmp_path, monkeypatch):
    """Base-only search blinded a rename review to the very name under review: on 33337 the
    naming arm looked up the PR's new name and was told no such declaration exists at the base
    commit -- true, useless, and the end of its investigation. The two corpora answer opposite
    questions and are reported apart."""

    import src.mathlib_review.evidence.evidence as evidence

    task, base_root = _task_with_overlay(
        tmp_path,
        base_text="theorem starProjection_coe_eq_isCompl_projection : True := trivial\n",
        reviewed_text="theorem coe_starProjection_eq_isComplProjection : True := trivial\n")
    monkeypatch.setattr(evidence, "snapshot_workspace", lambda sha: base_root)
    tool = _register(task).tools["declaration_search"]

    new = asyncio.run(tool(identifier="coe_starProjection_eq_isComplProjection"))
    assert new["success"]
    assert new["declared_before_this_pr"] == 0
    assert new["declared_in_this_pr"] == 1
    assert "IN THIS PR" in new["results"]

    old = asyncio.run(tool(identifier="starProjection_coe_eq_isCompl_projection"))
    assert old["declared_before_this_pr"] == 1
    assert old["declared_in_this_pr"] == 0
    assert "before this PR" in old["results"]


def test_the_two_corpora_are_never_folded_into_one_count(tmp_path, monkeypatch):
    """A name declared in both is not a duplicate of itself: it is the same declaration seen
    twice. Folding would turn every unchanged declaration in a changed file into an
    'already exists' hit."""

    import src.mathlib_review.evidence.evidence as evidence

    task, base_root = _task_with_overlay(
        tmp_path,
        base_text="theorem unchanged_lemma : True := trivial\n",
        reviewed_text="theorem unchanged_lemma : True := trivial\n")
    monkeypatch.setattr(evidence, "snapshot_workspace", lambda sha: base_root)
    tool = _register(task).tools["declaration_search"]

    result = asyncio.run(tool(identifier="unchanged_lemma"))
    assert result["declared_before_this_pr"] == 1 and result["declared_in_this_pr"] == 1
    assert result["count"] == 2


def test_the_trace_keeps_the_closed_gate_and_marks_overlay_hits_by_prefix(tmp_path, monkeypatch):
    """`gate` is a closed vocabulary (`as_of` | `base_snapshot`) that the leak audit
    enumerates, and the temporal bound of this tool is still the base snapshot -- the PR's own
    files can see nothing later than the PR. So the row keeps `base_snapshot`, and a hit from
    the reviewed overlay is told apart in `result_ids` by its `reviewed:` prefix rather than
    by inventing a gate value the audit has never heard of."""

    import json

    import src.mathlib_review.evidence.evidence as evidence

    task, base_root = _task_with_overlay(
        tmp_path, base_text="",
        reviewed_text="theorem coe_starProjection_eq_isComplProjection : True := trivial\n")
    monkeypatch.setattr(evidence, "snapshot_workspace", lambda sha: base_root)
    tool = _register(task).tools["declaration_search"]
    asyncio.run(tool(identifier="coe_starProjection_eq_isComplProjection"))

    rows = [json.loads(line) for line in open(task.data.trace_path) if line.strip()]
    assert rows[-1]["gate"] == "base_snapshot"
    assert rows[-1]["result_ids"] == ["reviewed:Mathlib/A.lean"]
    assert rows[-1]["result_count"] == 1


def test_without_a_target_workspace_the_tool_is_base_only_and_says_so(tmp_path, monkeypatch):
    import json

    import src.mathlib_review.evidence.evidence as evidence

    base = tmp_path / "base" / "Mathlib"
    base.mkdir(parents=True)
    (base / "A.lean").write_text("")
    monkeypatch.setattr(evidence, "snapshot_workspace", lambda sha: tmp_path / "base")
    task = _task(tmp_path, ["declaration_search"])
    tool = _register(task).tools["declaration_search"]

    result = asyncio.run(tool(identifier="anything_at_all"))
    assert result["declared_in_this_pr"] == 0
    assert "or in the files this PR changes" not in result["results"]
    rows = [json.loads(line) for line in open(task.data.trace_path) if line.strip()]
    assert rows[-1]["gate"] == "base_snapshot" and rows[-1]["result_ids"] == []
