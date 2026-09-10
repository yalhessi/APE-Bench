"""A persisted dense precedent index, and the gated query that reads it.

**Why persisted.** `precedent_bench.DenseRetriever` embeds the whole 105 MB corpus in its
constructor. That is right for a benchmark, which builds once and queries 109 times in one
process, and wrong for a live tool: arms run in orchestrator worker processes, so the cost
would be paid again in every worker, for every run, to answer a handful of queries. Building
the embedding matrix once offline turns a per-process minute into a per-process mmap.

**Why dense.** The Stage-1 benchmark ran and reported `STRONG GO` at 0.615 hit@10
(`inputs/pr_review_v2/precedent_bench/report.json`). The three designs converge at k=10 but
separate sharply at the k a live tool actually returns:

    design            hit@1  hit@3  hit@5  hit@10   V2 hit@5
    dense_code          20%    38%    49%     61%        56%
    lexical+feature     15%    29%    42%     60%        44%
    lexical             16%    32%    40%     56%        38%

An arm asks for 5 precedents, not 10, and V2 is the dominant gold stratum. Choosing lexical
because it is cheaper to index would trade a measured 7-point advantage for a build step we
have to run once.

**Why the filter runs before ranking.** Filtering a ranked top-k afterwards silently
shortens it: a query whose best matches are all ineligible returns two weak precedents and
looks like a thin corpus rather than a gated one. Eligibility is a mask over the matrix, and
the ranking happens on what survives it.
"""

from __future__ import annotations

import argparse
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from src.mathlib_review.paths import PRECEDENT_CORPUS, PRECEDENT_INDEX, assert_repo_root

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
INDEX_VERSION = "v5-precedent-index/1"

#: How much of the anchored hunk is kept for display. The full hunk can be hundreds of
#: lines (a new file arrives as one hunk), and an arm shown a 400-line block has been handed
#: noise, not a precedent.
DISPLAY_HUNK_CHARS = 1200
DISPLAY_BODY_CHARS = 600


class PrecedentIndexMissing(RuntimeError):
    """The index has not been built. Carries the command that builds it."""


#: Rows whose timestamp could not be read. They are excluded from every gated read rather
#: than dated: the old parser returned 0 for them, which is before every real cutoff, so an
#: undated row was eligible for *every* review. In a leak gate that is the wrong direction to
#: fail, and it was the only direction it could fail.
UNDATED = -1


def _iso_to_epoch(stamp: Optional[str]) -> int:
    """Parse through the shared gate, so this index dates a row the way every other source does.

    It used to parse with `datetime.fromisoformat(...).timestamp()`, which resolves a *naive*
    timestamp in the machine's local time -- measured four hours off on a UTC-4 machine, and
    off the other way east of UTC, so whether a row was eligible depended on where the index
    was built. And it returned 0 on failure. See `mathlib_review/retrieval_gate.py`.
    """

    from src.mathlib_review.retrieval_gate import RetrievalGate, UngatedTimestamp

    try:
        return RetrievalGate().epoch_of(stamp, field="created_at")
    except UngatedTimestamp:
        return UNDATED


def _load_corpus(path: Path) -> List[Dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def meta_row(row: dict) -> dict:
    """The per-comment record the index keeps beside its embedding.

    `original_position`, `original_line`, `side` and `subject_type` are carried through so a
    comment can be attached to the declaration *enclosing its line* rather than to any
    declaration in its hunk (`conventions.review_join.situate_hunk`). The 34,640-row corpus
    the current index was built from predates these fields, so its rows carry `None` here; a
    re-fetched corpus does not. The hunk itself is truncated for display, so resolution
    against it must go through these fields, never through the stored text."""
    return {
        "comment_id": row.get("comment_id"),
        "pr_number": row.get("pr_number"),
        "path": row.get("path"),
        "created_at": row.get("created_at"),
        "created_epoch": _iso_to_epoch(row.get("created_at")),
        "original_position": row.get("original_position"),
        "original_line": row.get("original_line") or row.get("line"),
        "side": row.get("side"),
        "subject_type": row.get("subject_type"),
        "commenter": row.get("commenter"),
        "html_url": row.get("html_url"),
        "body": (row.get("body") or "")[:DISPLAY_BODY_CHARS],
        "diff_hunk": (row.get("diff_hunk") or "")[:DISPLAY_HUNK_CHARS],
    }


def build(
    corpus_path: Path = PRECEDENT_CORPUS,
    out_dir: Path = PRECEDENT_INDEX,
    model_name: str = DEFAULT_MODEL,
    logger=None,
) -> Path:
    """Embed the corpus once and write the index. Idempotent by content."""

    import numpy as np
    from sentence_transformers import SentenceTransformer

    from src.mathlib_review.io import sha256_file
    from src.mathlib_review.corpus import eval_pr_numbers as _eval_pr_numbers
    from src.mathlib_review.corpus import hunk_code

    if not corpus_path.is_file():
        raise FileNotFoundError(
            f"precedent corpus not found at {corpus_path}. Build it with "
            "`python -m src.datasets.pr_review_v2.corpus` (needs GITHUB_TOKEN)."
        )
    rows = _load_corpus(corpus_path)
    # The corpus builder already excludes eval PRs at collection time. Re-applying it here
    # costs nothing and means the index is safe even if it is ever pointed at a corpus whose
    # provenance is not this repo's.
    excluded = _eval_pr_numbers()
    rows = [row for row in rows if row.get("pr_number") not in excluded]
    if logger:
        logger.info("precedent index: %d rows (%d eval-PR rows excluded)",
                    len(rows), len(excluded))

    texts = [hunk_code(row.get("diff_hunk") or "") for row in rows]
    model = SentenceTransformer(model_name)
    embeddings = model.encode(
        texts, normalize_embeddings=True, batch_size=256,
        show_progress_bar=bool(logger),
    ).astype("float32")

    out_dir.mkdir(parents=True, exist_ok=True)
    np.save(out_dir / "embeddings.npy", embeddings)
    with (out_dir / "meta.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(meta_row(row), ensure_ascii=False) + "\n")
    manifest = {
        "index_version": INDEX_VERSION,
        "model_name": model_name,
        "corpus_path": str(corpus_path),
        "corpus_sha256": sha256_file(corpus_path),
        "rows": len(rows),
        "dim": int(embeddings.shape[1]),
        "excluded_eval_prs": sorted(excluded),
        "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    if logger:
        logger.info("precedent index written to %s (%d x %d)",
                    out_dir, len(rows), embeddings.shape[1])
    return out_dir


class PrecedentIndex:
    """A loaded index. One per process; `shared()` is what tools should call."""

    _shared: Optional["PrecedentIndex"] = None
    _lock = threading.Lock()

    def __init__(self, directory: Path):
        import numpy as np

        manifest_path = directory / "manifest.json"
        if not manifest_path.is_file():
            raise PrecedentIndexMissing(
                f"no precedent index at {directory}. Build it once with "
                "`./ape/bin/python -m src.mathlib_review.retrieval.precedent_index build`. "
                "It is not built on demand: embedding the corpus inside a worker process "
                "would pay a one-off cost in every worker of every run."
            )
        self.directory = directory
        self.manifest = json.loads(manifest_path.read_text())
        self.corpus_sha256 = self.manifest.get("corpus_sha256")
        self.model_name = self.manifest.get("model_name", DEFAULT_MODEL)
        self._np = np
        self.embeddings = np.load(directory / "embeddings.npy", mmap_mode="r")
        self.meta = _load_corpus(directory / "meta.jsonl")
        if len(self.meta) != self.embeddings.shape[0]:
            raise PrecedentIndexMissing(
                f"precedent index at {directory} is inconsistent: {len(self.meta)} metadata "
                f"rows vs {self.embeddings.shape[0]} embeddings. Rebuild it."
            )
        self._created = np.asarray([row["created_epoch"] for row in self.meta], dtype="int64")
        self._pr = np.asarray([row["pr_number"] or -1 for row in self.meta], dtype="int64")
        self._model = None

    @classmethod
    def shared(cls, directory: Path = PRECEDENT_INDEX) -> "PrecedentIndex":
        with cls._lock:
            if cls._shared is None or cls._shared.directory != directory:
                cls._shared = PrecedentIndex(directory)
            return cls._shared

    def _encode(self, text: str):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model.encode([text], normalize_embeddings=True)[0]

    def eligible_mask(self, as_of: Optional[str], exclude_pr: Optional[int]):
        """Which rows a reader at this instant is allowed to see.

        The rule is `mathlib_review.retrieval_gate`'s; this is its vectorised form, which is
        why the cutoff is taken from the gate rather than parsed here. `as_of` is exclusive: a
        comment written at exactly the cutoff was not available beforehand.
        """

        from src.mathlib_review.retrieval_gate import RetrievalGate

        np = self._np
        rule = RetrievalGate(as_of=as_of, exclude_pr=exclude_pr)
        mask = np.ones(len(self.meta), dtype=bool)
        # An undated row is never eligible under a cutoff. Ungated reads still see it: with no
        # cutoff there is no claim being made about when it was available.
        if rule.cutoff_epoch is not None:
            mask &= self._created != UNDATED
            mask &= self._created < rule.cutoff_epoch
        if exclude_pr is not None:
            mask &= self._pr != int(exclude_pr)
        return mask

    def search(
        self, code: str, k: int = 5, *, as_of: Optional[str] = None,
        exclude_pr: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        np = self._np
        mask = self.eligible_mask(as_of, exclude_pr)
        rows = np.flatnonzero(mask)
        if rows.size == 0:
            return []
        query = self._encode(code)
        sims = np.asarray(self.embeddings[rows]) @ query
        top = rows[np.argsort(-sims)[:k]]
        order = {int(row): float(score) for row, score in zip(rows, sims)}
        return [{**self.meta[int(i)], "score": order[int(i)]} for i in top]


def main() -> None:
    from ape.utils.logging import create_logger

    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("command", choices=["build", "stats"])
    parser.add_argument("--corpus", type=Path, default=PRECEDENT_CORPUS)
    parser.add_argument("--out", type=Path, default=PRECEDENT_INDEX)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()
    assert_repo_root()
    if args.command == "build":
        print(build(args.corpus, args.out, args.model, logger=create_logger()))
    else:
        index = PrecedentIndex(args.out)
        print(json.dumps(index.manifest, indent=2))


if __name__ == "__main__":
    main()
