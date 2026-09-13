"""`precedent_search` returns distinct hunks, shows the commented line, and names who wrote it.

Four defects measured over every precedent delivered to an arm in the v5 runs (2,825 hits in
565 calls), all of which a trace-row audit is blind to because the rows themselves were
correctly gated:

* **The hunk was truncated from the front.** GitHub builds a review comment's `diff_hunk` so
  that it ENDS at the commented line, so the first N characters are the context *before* the
  point. 711 of 2,825 hits (25%) were longer than the render budget, and every one showed the
  arm code the comment was not about.
* **Thread replies filled the slots.** Every comment in one review thread carries the same
  hunk and therefore the same score; a k=5 answer held about 3 distinct hunks.
* **Everything was labelled "maintainer wrote".** The corpus keeps comments by GitHub
  `author_association`, which a PR's own author carries on their own PR, so 46% of delivered
  hits were the author replying to a reviewer ("Done.", "My bad, thanks.") presented as a
  maintainer's judgement.
* **A comment naming the PR under review was eligible.** `eligible_mask` excludes by the row's
  own `pr_number`, so a pre-cutoff comment on a *different* PR that announces this one passed.
  3 of 43,881 corpus rows name a scored PR; one is eligible for two real episodes of #33302.

Deliberately NOT fixed with a score threshold: measured over representative queries the top-5
similarities sit in 0.59-0.63 whether the hits are relevant or not, so no cutoff separates them
and one would only hide the problem. The tool says so in its result instead.
"""

from __future__ import annotations

import numpy as np
import pytest

from src.mathlib_review.retrieval.precedent_index import (
    META_VERSION, PrecedentIndex, StalePrecedentIndex, references_pr, refresh_meta,
    row_references_pr,
)


@pytest.mark.parametrize("text,pr,expected", [
    ("I've opened #33302 adding map_zero", 33302, True),
    ("see https://github.com/leanprover-community/mathlib4/pull/33302", 33302, True),
    ("fixed in #333021", 33302, False),          # a longer number is a different PR
    ("about #3330", 33302, False),
    ("no reference at all", 33302, True if False else False),
    (None, 33302, False),
    ("#33302", None, False),                      # nothing to exclude against
])
def test_pr_reference_detection(text, pr, expected):
    assert references_pr(text, pr) is expected


def _index(monkeypatch, rows, vectors):
    index = PrecedentIndex.__new__(PrecedentIndex)
    index._np = np
    index.meta = rows
    index.embeddings = np.asarray(vectors, dtype="float32")
    index._created = np.asarray([r["created_epoch"] for r in rows])
    index._pr = np.asarray([r["pr_number"] for r in rows])
    monkeypatch.setattr(PrecedentIndex, "_encode",
                        lambda self, text: np.asarray([1.0, 0.0], dtype="float32"))
    return index


def _row(cid, pr, hunk, body="looks wrong", created=1_000, commenter="alice"):
    return {"comment_id": cid, "pr_number": pr, "path": "M/A.lean", "created_at": "2025-01-01T00:00:00Z",
            "created_epoch": created, "commenter": commenter, "body": body, "diff_hunk": hunk,
            "original_line": 10, "original_position": None, "side": None, "subject_type": None,
            "html_url": "u"}


def test_one_slot_per_distinct_hunk(monkeypatch):
    """A whole review thread shares a hunk and a score; without dedupe it fills the answer."""

    rows = [_row(i, 100, "SHARED HUNK") for i in range(6)] + [
        _row(90, 101, "OTHER HUNK A"), _row(91, 102, "OTHER HUNK B")]
    vectors = [[1.0, 0.0]] * 6 + [[0.99, 0.14], [0.98, 0.2]]
    index = _index(monkeypatch, rows, vectors)

    hits = index.search("q", k=3, as_of=None, exclude_pr=None)

    assert [h["diff_hunk"] for h in hits] == ["SHARED HUNK", "OTHER HUNK A", "OTHER HUNK B"]


def test_fewer_than_k_distinct_hunks_returns_fewer(monkeypatch):
    """Returning 2 is a real answer about the corpus; padding to 5 would not be."""

    rows = [_row(i, 100, "SHARED") for i in range(4)] + [_row(90, 101, "OTHER")]
    index = _index(monkeypatch, rows, [[1.0, 0.0]] * 4 + [[0.9, 0.4]])

    assert len(index.search("q", k=5, as_of=None, exclude_pr=None)) == 2


def test_a_precedent_naming_the_pr_under_review_is_dropped(monkeypatch):
    """The demonstrated case: a comment on another PR announcing the one being reviewed."""

    rows = [_row(1, 31707, "HUNK A", body="I've opened #33302 adding map_zero for ShiftedHom"),
            _row(2, 31708, "HUNK B", body="unrelated remark")]
    index = _index(monkeypatch, rows, [[1.0, 0.0], [0.9, 0.4]])

    hits = index.search("q", k=5, as_of=None, exclude_pr=33302)

    assert [h["comment_id"] for h in hits] == [2], "the announcement must not be returned"
    assert index.search("q", k=5, as_of=None, exclude_pr=999)[0]["comment_id"] == 1, (
        "and it is returned when it is not about the PR under review")


def test_the_cutoff_still_runs_before_ranking(monkeypatch):
    """Dedupe must not have moved the gate: an ineligible row is never a candidate."""

    from src.datasets.zulip.datetimes import epoch_to_iso

    rows = [_row(1, 100, "FUTURE", created=9_000), _row(2, 101, "PAST", created=1_000)]
    index = _index(monkeypatch, rows, [[1.0, 0.0], [0.5, 0.86]])

    hits = index.search("q", k=5, as_of=epoch_to_iso(5_000), exclude_pr=None)

    assert [h["comment_id"] for h in hits] == [2]


# --- the data step: metadata the query path needs ---------------------------------------


def test_an_author_reply_is_not_a_precedent(monkeypatch):
    """37% of the index and 46% of everything ever delivered to an arm was the PR's own author
    replying on their own PR. `definitions.py` has always said a reviewer is "not the PR
    author"; the retrieval corpus kept them because GitHub reports an author's own association
    as COLLABORATOR."""

    rows = [_row(1, 100, "HUNK A", body="Done."), _row(2, 101, "HUNK B", body="wrong name here")]
    rows[0]["commenter_is_pr_author"] = True
    rows[1]["commenter_is_pr_author"] = False
    index = _index(monkeypatch, rows, [[1.0, 0.0], [0.9, 0.4]])

    assert [h["comment_id"] for h in index.search("q", k=5, as_of=None, exclude_pr=None)] == [2]


def test_pr_refs_is_preferred_over_the_truncated_body():
    """The stored body is cut for display, so a reference past the cap is invisible in it.
    `pr_refs` is parsed from the whole body at index time."""

    late = {"body": "a" * 600, "pr_refs": [33302]}
    assert row_references_pr(late, 33302) is True
    assert row_references_pr(late, 111) is False
    # no pr_refs (an index built before the field): fall back to the body
    assert row_references_pr({"body": "see #33302"}, 33302) is True
    assert row_references_pr({"body": "see #33302"}, None) is False


def _fake_index(tmp_path, corpus_rows, *, meta_version=META_VERSION):
    import json
    from src.mathlib_review.io import sha256_file

    corpus = tmp_path / "corpus.jsonl"
    corpus.write_text("".join(json.dumps(r) + "\n" for r in corpus_rows), encoding="utf-8")
    d = tmp_path / "index"
    d.mkdir()
    (d / "meta.jsonl").write_text(
        "".join(json.dumps({"comment_id": r["comment_id"]}) + "\n" for r in corpus_rows),
        encoding="utf-8")
    (d / "manifest.json").write_text(json.dumps({
        "corpus_path": str(corpus), "corpus_sha256": sha256_file(corpus),
        "meta_version": meta_version, "rows": len(corpus_rows)}), encoding="utf-8")
    return d, corpus


def _corpus_row(cid, pr, commenter="alice", body="looks wrong"):
    return {"comment_id": cid, "pr_number": pr, "path": "M/A.lean", "line": 3,
            "diff_hunk": "@@\n+x", "body": body, "commenter": commenter,
            "author_association": "COLLABORATOR", "created_at": "2025-01-01T00:00:00Z"}


def test_refresh_refuses_when_the_corpus_no_longer_reproduces_the_indexed_rows(tmp_path, monkeypatch):
    """The embeddings are reused, so the rows must line up. Alignment is proved against the
    existing meta, not assumed: a shifted corpus would silently give every row its neighbour's
    metadata."""

    import src.mathlib_review.retrieval.precedent_index as mod

    rows = [_corpus_row(1, 100), _corpus_row(2, 101)]
    d, corpus = _fake_index(tmp_path, rows)
    monkeypatch.setattr(mod, "_pr_authors", lambda numbers, logger=None: {100: "alice", 101: "bob"})
    # the same corpus refreshes cleanly
    refresh_meta(d)
    # now the corpus gains a row at the front: same file, different order
    import json
    from src.mathlib_review.io import sha256_file
    new_rows = [_corpus_row(9, 102)] + rows
    corpus.write_text("".join(json.dumps(r) + "\n" for r in new_rows), encoding="utf-8")
    manifest = json.loads((d / "manifest.json").read_text())
    manifest["corpus_sha256"] = sha256_file(corpus)      # pretend the sha was updated too
    (d / "manifest.json").write_text(json.dumps(manifest))

    with pytest.raises(StalePrecedentIndex, match="row order"):
        refresh_meta(d)


def test_refresh_marks_the_authors_own_replies(tmp_path, monkeypatch):
    import json

    import src.mathlib_review.retrieval.precedent_index as mod

    rows = [_corpus_row(1, 100, commenter="alice"), _corpus_row(2, 100, commenter="carol")]
    d, _ = _fake_index(tmp_path, rows)
    monkeypatch.setattr(mod, "_pr_authors", lambda numbers, logger=None: {100: "alice"})

    refresh_meta(d)

    meta = [json.loads(line) for line in (d / "meta.jsonl").read_text().splitlines()]
    assert [m["commenter_is_pr_author"] for m in meta] == [True, False]


def test_an_index_whose_meta_predates_the_query_path_is_refused(tmp_path, monkeypatch):
    """`data/` is gitignored, so every machine builds its own index. A loud refusal naming the
    refresh command is the only thing that can tell an operator to update it."""

    import numpy as np

    d, _ = _fake_index(tmp_path, [_corpus_row(1, 100)], meta_version="v5-precedent-meta/1")
    np.save(d / "embeddings.npy", np.zeros((1, 2), dtype="float32"))

    with pytest.raises(StalePrecedentIndex, match="refresh-meta"):
        PrecedentIndex(d)


# --- the run must be able to say which retrieval regime produced it ----------------------


def test_the_run_identity_carries_what_changes_an_answer(tmp_path, monkeypatch):
    """`_context_index_identity` exists because "rebuild the index and the same query returns
    something else, with nothing in the run saying so". It recorded only the corpus sha and the
    model name -- neither of which moves when the *recipe* does. Re-embedding a different slice
    of each hunk, or adding a metadata field the query path filters on, changes every answer
    and leaves both untouched."""

    import json

    import src.mathlib_review.review.runner as runner

    index = tmp_path / "precedent_index"
    index.mkdir()
    (index / "manifest.json").write_text(json.dumps({
        "corpus_sha256": "c" * 64, "model_name": "m", "model_revision": "r" * 40,
        "index_version": "v5-precedent-index/9", "meta_version": "v5-precedent-meta/9",
        "rows": 17,
    }))
    monkeypatch.setattr(runner, "PRECEDENT_INDEX", index)

    identity = runner._context_index_identity()

    assert identity["precedent_index_version"] == "v5-precedent-index/9"
    assert identity["precedent_meta_version"] == "v5-precedent-meta/9"
    assert identity["precedent_model_revision"] == "r" * 40
    assert identity["precedent_rows"] == "17"


def test_the_shipped_index_reports_a_complete_identity():
    """A field that is silently empty records nothing. Skips where no index is built."""

    import json

    from src.mathlib_review.paths import PRECEDENT_INDEX

    manifest = PRECEDENT_INDEX / "manifest.json"
    if not manifest.is_file():
        pytest.skip("no precedent index on this machine")
    payload = json.loads(manifest.read_text())
    for key in ("corpus_sha256", "model_name", "model_revision", "index_version",
                "meta_version", "rows"):
        assert payload.get(key), f"{key} is missing from the index manifest"


# --- what gets embedded ------------------------------------------------------------------


class _FakeTokenizer:
    """One token per whitespace-separated word: enough to exercise the budget logic."""

    def encode(self, text, add_special_tokens=False):
        return text.split()


def test_the_embedded_slice_is_the_end_of_the_hunk():
    """GitHub builds a hunk to END at the commented line and the embedder truncates at 256
    tokens from the START, so 53% of the corpus was embedded from its opening lines -- on a new
    file, the copyright header -- and the flagged line was never seen by the model."""

    from src.mathlib_review.retrieval.precedent_index import embedding_text

    hunk = "@@ -0,0 +1,9 @@\n" + "\n".join(f"+filler {i}" for i in range(200)) + \
           "\n+theorem the_commented_one : True"
    text = embedding_text(hunk, _FakeTokenizer())

    assert text.strip().endswith("theorem the_commented_one : True")
    assert len(text.split()) <= 254
    assert "filler 0" not in text, "the head is what gets dropped, not the tail"


def test_a_hunk_inside_the_window_is_untouched():
    from src.mathlib_review.retrieval.precedent_index import embedding_text

    hunk = "@@ -1,2 +1,2 @@\n+theorem a : True := trivial"
    assert embedding_text(hunk, _FakeTokenizer()) == "theorem a : True := trivial"


def test_whole_lines_are_kept():
    """The slice keeps line boundaries so the embedded text stays readable Lean."""

    from src.mathlib_review.retrieval.precedent_index import embedding_text

    hunk = "@@\n" + "\n".join(f"+aaa bbb ccc line{i}" for i in range(300))
    text = embedding_text(hunk, _FakeTokenizer())
    assert all(line.startswith("aaa bbb ccc") for line in text.split("\n") if line)


def test_without_a_tokenizer_the_whole_hunk_comes_back():
    """The slice is a property of the embedder's window; a caller with no tokenizer (any
    non-embedding use of the text) must not get a silently shortened hunk."""

    from src.mathlib_review.retrieval.precedent_index import embedding_text

    hunk = "@@\n" + "\n".join(f"+line{i}" for i in range(300))
    assert len(embedding_text(hunk, None).split("\n")) == 300
