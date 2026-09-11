"""The consumers the store feeds are gated, and the paths they read cannot silently disagree."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.mathlib_review.paths import PRECEDENT_CORPUS, PRECEDENT_INDEX, ZULIP_STORE


def test_the_analysis_loaders_refuse_to_pick_a_corpus_window_for_you():
    """The corpus's end date used to *be* the date gate.

    It stopped at 2025-08-31, before every eval PR (the 201 bundles open 2025-11-07..12-31), so
    `precedent_bench`'s four callers were leak-safe whether or not they gated, and
    `review_join` applied no window at all and was leak-safe too. Collection now runs to
    2026-08-31. Keeping the old pin silently discards a year of review; dropping it silently
    hands a query its own future. Both are invisible at the call site, so neither loader has a
    default any more -- omitting the window is a `TypeError`, not a guess."""

    from src.datasets.pr_review_v2.precedent_bench import load_corpus
    from src.mathlib_review.conventions.review_join import load_corpus_rows, load_index_rows, load_rows

    for loader in (load_corpus, load_corpus_rows, load_index_rows, load_rows):
        with pytest.raises(TypeError, match="end"):
            loader()


def test_the_research_corpus_loader_excludes_scored_prs_and_its_window_binds():
    """`precedent_bench`, `precedent_prime`, `site_worklist` and `site_discrimination` share this
    loader and applied neither exclusion nor window; the corpus now reaches December 2025, the
    month their queries come from.

    The window assertion is over the *raw* file, not over rows the loader already filtered --
    the previous form (`max(created_at) <= VALIDATED_CORPUS_END` on the loaded rows) was true by
    construction and so could not observe the corpus growing underneath it."""

    if not PRECEDENT_CORPUS.is_file():
        pytest.skip("corpus absent")
    from src.datasets.pr_review_v2.precedent_bench import VALIDATED_CORPUS_END, load_corpus
    from src.datasets.pull_requests.definitions import scored_pr_numbers

    raw = [json.loads(l) for l in PRECEDENT_CORPUS.read_text().splitlines() if l.strip()]
    raw_end = max(str(r.get("created_at") or "")[:10] for r in raw)

    rows = load_corpus(PRECEDENT_CORPUS, end=VALIDATED_CORPUS_END)
    assert rows
    assert not {r["pr_number"] for r in rows} & scored_pr_numbers()
    assert max(r["created_at"][:10] for r in rows) <= VALIDATED_CORPUS_END == "2025-08-31"

    unwindowed = load_corpus(PRECEDENT_CORPUS, end=None)
    if raw_end > VALIDATED_CORPUS_END:
        assert len(unwindowed) > len(rows), (
            f"the corpus reaches {raw_end}, past the pinned window {VALIDATED_CORPUS_END}, yet "
            "windowing dropped nothing -- the window is not binding")


def test_a_precedent_index_built_from_a_different_corpus_is_refused(tmp_path):
    import numpy as np

    from src.mathlib_review.retrieval.precedent_index import PrecedentIndex, StalePrecedentIndex

    corpus = tmp_path / "corpus.jsonl"
    corpus.write_text('{"comment_id": 1}\n')
    index = tmp_path / "index"
    index.mkdir()
    np.save(index / "embeddings.npy", np.zeros((1, 4), dtype="float32"))
    (index / "meta.jsonl").write_text(json.dumps({"comment_id": 1, "pr_number": 1, "created_epoch": 0}) + "\n")
    (index / "manifest.json").write_text(json.dumps({"corpus_path": str(corpus), "corpus_sha256": "0" * 64}))
    with pytest.raises(StalePrecedentIndex) as excinfo:
        PrecedentIndex(index)
    assert "Rebuild it" in str(excinfo.value)


def test_the_zulip_store_path_is_spelled_once():
    """`paths.ZULIP_STORE` was declared and unused; the live reader asks `ZulipConfig`. Pinned
    equal so the two cannot drift apart without a failure."""

    from ape.utils.project import PROJECT_ROOT
    from src.datasets.zulip.config import ZulipConfig

    assert ZulipConfig().sqlite_path.resolve() == (PROJECT_ROOT / ZULIP_STORE).resolve()


def test_the_v2_fetcher_cannot_write_into_the_frozen_caches(monkeypatch):
    """Its default cache directory is the one eleven release manifests hash. Reading cached
    bundles still works; fetching a new PR refuses before any request is made."""

    from src.datasets.pr_review_v2.config import PRReviewV2Config
    from src.datasets.pr_review_v2 import fetch

    class NoNetwork:
        def __getattr__(self, name):
            raise AssertionError("must refuse before touching the network")

    config = PRReviewV2Config()
    assert fetch.fetch_pr_bundle(NoNetwork(), config, 33098)["pr"]["number"] == 33098   # cached: fine
    with pytest.raises(PermissionError) as excinfo:
        fetch.fetch_pr_bundle(NoNetwork(), config, 99999999)
    assert "pull_requests.collect" in str(excinfo.value)
    with pytest.raises(PermissionError):
        fetch.fetch_compare(NoNetwork(), config, "master", "f" * 40)


def test_the_old_corpus_command_refuses_and_names_the_new_one(capsys):
    from src.datasets.pr_review_v2 import corpus

    with pytest.raises(SystemExit) as excinfo:
        corpus.main()
    assert excinfo.value.code == 2
    err = capsys.readouterr().err
    assert "pull_requests.collect" in err and "--acceptance" in err
