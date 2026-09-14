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
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from src.mathlib_review.paths import PRECEDENT_CORPUS, PRECEDENT_INDEX, assert_repo_root

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
INDEX_VERSION = "v5-precedent-index/2"

#: The shape of `meta.jsonl`. Bumped when a field is added that the query path relies on, so an
#: index whose meta predates it is refused loudly instead of quietly behaving differently -- the
#: same contract `corpus_sha256` already has. `data/` is gitignored, so every machine builds its
#: own index and this is the only thing that can tell an operator to refresh it.
META_VERSION = "v5-precedent-meta/2"

#: How much of the anchored hunk is kept for display. The full hunk can be hundreds of
#: lines (a new file arrives as one hunk), and an arm shown a 400-line block has been handed
#: noise, not a precedent.
DISPLAY_HUNK_CHARS = 1200
DISPLAY_BODY_CHARS = 600


class PrecedentIndexMissing(RuntimeError):
    """The index has not been built. Carries the command that builds it."""


class StalePrecedentIndex(PrecedentIndexMissing):
    """The index was built from a corpus that has since changed.

    The manifest always recorded `corpus_sha256`; nothing compared it. The index was found built
    from 36,695 rows while its corpus held 43,874 -- September to November collected, never
    indexed -- and every precedent search in that state silently ignored three months, with the run
    plan still sealing the old sha as though it described what was searched."""


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


#: `#12345` or a github pull/issue URL. Used to drop a precedent that discusses the PR under
#: review; `\b` on the right keeps `#123` from matching inside `#12345`.
_PR_REFERENCE = re.compile(r"(?:#|mathlib4/(?:pull|issues)/)(\d{2,7})\b")


def references_pr(text: Optional[str], pr_number: Optional[int]) -> bool:
    """Whether `text` names `pr_number` as a PR or issue reference."""

    if not text or pr_number is None:
        return False
    target = str(int(pr_number))
    return any(found == target for found in _PR_REFERENCE.findall(text))


def row_references_pr(row: Dict[str, Any], pr_number: Optional[int]) -> bool:
    """Whether an index row discusses `pr_number`.

    Prefers `pr_refs`, parsed at index time from the comment's whole body; falls back to the
    stored body, which is truncated for display and so can miss a late reference.
    """

    if pr_number is None:
        return False
    refs = row.get("pr_refs")
    if refs is not None:
        return int(pr_number) in {int(ref) for ref in refs}
    return references_pr(row.get("body"), pr_number)


#: The embedder's context window, less the two special tokens it adds.
EMBED_TOKEN_BUDGET = 254


def embedding_text(diff_hunk: str, tokenizer=None) -> str:
    """The part of a hunk that is embedded: the END of it, not the beginning.

    GitHub builds a review comment's `diff_hunk` so that it ENDS at the commented line, and
    `all-MiniLM-L6-v2` truncates at 256 tokens from the START. Measured over a 3,000-row
    sample of the corpus, 53% of hunks exceed that window, so for most of the index the
    embedding described the context *before* the point -- on a new file, the copyright header
    -- while the line the maintainer was writing about was never seen by the model at all.
    That is the same wrong end the renderer was taking, and it is why a query matched "code
    that looks like a file opening" rather than "code that looks like what was flagged".

    The slice is tokenizer-driven rather than a fixed number of lines: how much fits varies
    from 1 line to dozens (median 12, p10 4), so any constant would truncate some rows and
    waste the window on others. Whole lines are kept, so the text stays syntactically
    readable.

    One case this cannot reach: a comment anchored to a *deleted* line. `hunk_code` drops
    removed lines, so the tail is then the nearest surviving line rather than the commented
    one.
    """

    from src.mathlib_review.corpus import hunk_code

    code = hunk_code(diff_hunk or "")
    if tokenizer is None or not code:
        return code
    if len(tokenizer.encode(code, add_special_tokens=False)) <= EMBED_TOKEN_BUDGET:
        return code
    lines = code.split("\n")
    kept: List[str] = []
    for line in reversed(lines):
        candidate = [line] + kept
        if len(tokenizer.encode("\n".join(candidate), add_special_tokens=False)) > EMBED_TOKEN_BUDGET:
            break
        kept = candidate
    # A single line longer than the window still has to yield something; take its tail.
    return "\n".join(kept) if kept else code[-(EMBED_TOKEN_BUDGET * 4):]


def _model_revision(model_name: str = DEFAULT_MODEL) -> str:
    """The Hub snapshot the embedder resolves to on this machine, or `""`.

    `model_name` alone does not identify an embedding: a Hugging Face ref can move, and two
    indexes built from the same corpus under the same name would then rank differently with
    nothing recording it. The loaded model object only reports the repo name, so the snapshot
    is read from the Hub cache's `refs/main`, which is what `local_files_only` resolves.
    """

    import os

    home = os.environ.get("HF_HOME") or os.path.expanduser("~/.cache/huggingface")
    ref = (Path(home) / "hub" / f"models--{model_name.replace('/', '--')}" / "refs" / "main")
    try:
        return ref.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def _pr_authors(numbers: Iterable[int], logger=None) -> Dict[int, Optional[str]]:
    """`pr_number -> author login`, read from the PR store's listings.

    Roster-independent on purpose. Whether a commenter is the PR's own author is a fact about
    who opened the PR, fixed at the moment it was opened; whether they are a *reviewer* is a
    roster question whose answer has moved since (the shipped reviewer projection classifies
    against a 2026 roster, which would date a 2024 comment by a 2026 fact). Only the first is
    used here.
    """

    from src.datasets.pull_requests.store import PullRequestStore

    store = PullRequestStore()
    authors: Dict[int, Optional[str]] = {}
    for number in sorted({int(n) for n in numbers}):
        try:
            listing = store.read(number, "listing")
        except Exception:  # noqa: BLE001 -- a PR absent from the store is simply unknown
            authors[number] = None
            continue
        authors[number] = ((listing or {}).get("user") or {}).get("login")
    missing = [n for n, a in authors.items() if not a]
    if missing and logger:
        logger.warning("precedent meta: no author for %d of %d PRs (e.g. %s); their comments "
                       "cannot be identified as author replies",
                       len(missing), len(authors), missing[:5])
    return authors


def meta_row(row: dict, authors: Optional[Dict[int, Optional[str]]] = None) -> dict:
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
        # Whether this comment is the PR author replying on their own PR. The corpus keeps
        # comments by GitHub `author_association`, which an author carries on their own PR, so
        # 37% of rows are "Done." / "My bad, thanks." rather than review. `definitions.py`
        # already says a reviewer is "not the PR author"; the retrieval corpus never
        # implemented it, and this is where that is repaired.
        "commenter_is_pr_author": bool(
            authors and row.get("commenter")
            and row.get("commenter") == authors.get(int(row.get("pr_number") or 0))
        ),
        # Parsed from the FULL body, not the truncated copy above, so a reference past the
        # display cap is still caught.
        "pr_refs": sorted({int(found) for found in _PR_REFERENCE.findall(row.get("body") or "")}),
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
    from src.datasets.pull_requests.definitions import scored_pr_numbers
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
    excluded = set(scored_pr_numbers())
    rows = [row for row in rows if row.get("pr_number") not in excluded]
    if logger:
        logger.info("precedent index: %d rows (%d eval-PR rows excluded)",
                    len(rows), len(excluded))

    authors = _pr_authors({row.get("pr_number") for row in rows if row.get("pr_number")}, logger)
    model = SentenceTransformer(model_name)
    model_revision = _model_revision(model_name)
    texts = [embedding_text(row.get("diff_hunk") or "", model.tokenizer) for row in rows]
    embeddings = model.encode(
        texts, normalize_embeddings=True, batch_size=256,
        show_progress_bar=bool(logger),
    ).astype("float32")

    out_dir.mkdir(parents=True, exist_ok=True)
    np.save(out_dir / "embeddings.npy", embeddings)
    with (out_dir / "meta.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(meta_row(row, authors), ensure_ascii=False) + "\n")
    # When the corpus is a projection of the PR store, record which view of it was indexed, so a
    # run plan that seals this manifest says whose comments it could retrieve.
    projection_manifest = corpus_path.parent / "manifest.json"
    projection = (json.loads(projection_manifest.read_text()) if projection_manifest.is_file()
                  else {})
    manifest = {
        "index_version": INDEX_VERSION,
        "meta_version": META_VERSION,
        "model_name": model_name,
        "model_revision": model_revision,
        "corpus_path": str(corpus_path),
        "corpus_sha256": sha256_file(corpus_path),
        "corpus_view": projection.get("view"),
        "corpus_store_content_sha256": projection.get("store_content_sha256"),
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
        corpus = Path(self.manifest.get("corpus_path") or "")
        if corpus.is_file():
            from src.mathlib_review.io import sha256_file

            current = sha256_file(corpus)
            if current != self.corpus_sha256:
                raise StalePrecedentIndex(
                    f"precedent index at {directory} was built from {corpus} at sha "
                    f"{str(self.corpus_sha256)[:12]}; the corpus is now {current[:12]}. Rebuild it "
                    "(`./ape/bin/python -m src.mathlib_review.retrieval.precedent_index build`) "
                    "rather than search a corpus that no longer exists.")
        # Checked after the corpus, deliberately: if the corpus moved, refreshing the metadata
        # cannot help and `refresh_meta` refuses it, so "rebuild" is the instruction that
        # applies. Only once the corpus still matches is a stale meta the actionable fault.
        if self.manifest.get("meta_version") != META_VERSION:
            raise StalePrecedentIndex(
                f"the index at {directory} carries meta "
                f"{self.manifest.get('meta_version') or '(none)'}, but the query path needs "
                f"{META_VERSION}: without it a precedent cannot be told from the PR author's "
                f"own reply. Refresh it (no re-embedding) with "
                f"`python -m src.mathlib_review.retrieval.precedent_index refresh-meta`.")
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

            # `local_files_only`, as `ape.toolkits.retrieve` already does. Without it a query
            # can reach the Hugging Face Hub and, if the cache were missing or `refs/main`
            # moved, silently embed against a different snapshot than the index was built
            # with -- a retrieval regime change with nothing in the run saying so.
            self._model = SentenceTransformer(self.model_name, local_files_only=True)
        # The query is cut by the same 256-token window as a row, so it gets the same slice:
        # an arm pasting a long declaration would otherwise be matched on its opening lines.
        return self._model.encode(
            [embedding_text(text, self._model.tokenizer) if "\n" in text else text],
            normalize_embeddings=True)[0]

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

    #: How many candidates to rank before de-duplication, as a multiple of `k`. Every comment
    #: in one review thread carries the same `diff_hunk`, so they score identically and fill
    #: several slots with one piece of code: measured over five representative queries, a
    #: k=5 answer held 3 distinct hunks on average. Ranking 40 and keeping the best per hunk
    #: returned 5 distinct hunks on all five. The multiple is what makes that affordable --
    #: the whole index is 43,881 x 384 floats and a full scan is ~4 ms, so widening the
    #: candidate set costs nothing measurable.
    DEDUPE_FETCH_MULTIPLE = 8

    def search(
        self, code: str, k: int = 5, *, as_of: Optional[str] = None,
        exclude_pr: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """The `k` best eligible precedents, one per distinct hunk.

        Fewer than `k` rows is a real answer, not a failure: it means the corpus holds fewer
        distinct pieces of commented code that match. The tool says so rather than padding.
        """

        np = self._np
        mask = self.eligible_mask(as_of, exclude_pr)
        rows = np.flatnonzero(mask)
        if rows.size == 0:
            return []
        query = self._encode(code)
        sims = np.asarray(self.embeddings[rows]) @ query
        ranked = rows[np.argsort(-sims)[: k * self.DEDUPE_FETCH_MULTIPLE]]
        order = {int(row): float(score) for row, score in zip(rows, sims)}

        hits: List[Dict[str, Any]] = []
        seen_hunks: set = set()
        for index in ranked:
            row = self.meta[int(index)]
            if row.get("commenter_is_pr_author"):
                # The PR's own author replying on their own PR. `definitions.py` has said
                # since it was written that a reviewer is "not the PR author"; the retrieval
                # corpus kept them because GitHub reports an author's own association as
                # COLLABORATOR. 37% of the index and 46% of everything ever delivered to an
                # arm was this -- "Done.", "My bad, thanks." -- shown as review.
                continue
            if row_references_pr(row, exclude_pr):
                # A comment that names the PR under review is discussion *of* it, whoever
                # wrote it and whenever. `eligible_mask` cannot see this: it excludes by the
                # row's own `pr_number`, so a pre-cutoff comment on a different PR that
                # announces or describes this one passes. Measured on the shipped corpus: 3
                # of 43,881 rows name a scored PR, and one of them is eligible for two real
                # episodes of #33302. The stored body is capped, so this catches the common
                # case rather than every case; the complete fix is a `pr_refs` field parsed
                # from the full body at build time.
                continue
            hunk = row.get("diff_hunk")
            if hunk in seen_hunks:
                continue
            seen_hunks.add(hunk)
            hits.append({**row, "score": order[int(index)]})
            if len(hits) == k:
                break
        return hits


def refresh_meta(out_dir: Path = PRECEDENT_INDEX, logger=None) -> Path:
    """Recompute `meta.jsonl` from the corpus without re-embedding anything.

    The embeddings are a function of the hunk text alone, so a field added to the *metadata*
    needs no model run -- but it does need the rows to stay in the order the embedding matrix
    was written in, because a query maps a row index straight into `self.meta`.

    That alignment is proved, not assumed: the recomputed `comment_id` sequence is compared
    against the existing `meta.jsonl`, which `build` wrote in the same loop as the matrix. If
    the corpus has changed under the index, or the eval-PR exclusion now removes a different
    set, the sequences differ and this refuses rather than silently shifting every row's
    metadata by one.
    """

    from src.mathlib_review.io import sha256_file
    from src.datasets.pull_requests.definitions import scored_pr_numbers

    manifest_path = out_dir / "manifest.json"
    meta_path = out_dir / "meta.jsonl"
    if not manifest_path.is_file() or not meta_path.is_file():
        raise PrecedentIndexMissing(f"no precedent index at {out_dir}; build it first")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    corpus_path = Path(manifest["corpus_path"])
    if not corpus_path.is_file():
        raise StalePrecedentIndex(f"the indexed corpus {corpus_path} is gone; rebuild the index")
    current = sha256_file(corpus_path)
    if current != manifest.get("corpus_sha256"):
        raise StalePrecedentIndex(
            f"{corpus_path} has changed since the index was built "
            f"({str(manifest.get('corpus_sha256'))[:12]} -> {current[:12]}); rebuild, do not refresh")

    rows = _load_corpus(corpus_path)
    excluded = set(scored_pr_numbers())
    rows = [row for row in rows if row.get("pr_number") not in excluded]
    existing = _load_corpus(meta_path)
    recomputed_ids = [str(row.get("comment_id")) for row in rows]
    existing_ids = [str(row.get("comment_id")) for row in existing]
    if recomputed_ids != existing_ids:
        raise StalePrecedentIndex(
            f"the corpus no longer reproduces the indexed row order "
            f"({len(recomputed_ids)} rows against {len(existing_ids)}); the embedding matrix "
            f"cannot be reused, so rebuild the index instead of refreshing its metadata")

    authors = _pr_authors({row.get("pr_number") for row in rows if row.get("pr_number")}, logger)
    tmp = meta_path.with_suffix(".jsonl.refreshing")
    with tmp.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(meta_row(row, authors), ensure_ascii=False) + "\n")
    tmp.replace(meta_path)
    manifest["meta_version"] = META_VERSION
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if logger:
        by_author = sum(1 for row in rows
                        if row.get("commenter") == authors.get(int(row.get("pr_number") or 0)))
        logger.info("precedent meta refreshed: %d rows, %d (%.0f%%) are the PR author's own "
                    "replies", len(rows), by_author, 100.0 * by_author / max(len(rows), 1))
    return meta_path


def main() -> None:
    from ape.utils.logging import create_logger

    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("command", choices=["build", "refresh-meta", "stats"])
    parser.add_argument("--corpus", type=Path, default=PRECEDENT_CORPUS)
    parser.add_argument("--out", type=Path, default=PRECEDENT_INDEX)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()
    assert_repo_root()
    if args.command == "build":
        print(build(args.corpus, args.out, args.model, logger=create_logger()))
    elif args.command == "refresh-meta":
        print(refresh_meta(args.out, logger=create_logger()))
    else:
        index = PrecedentIndex(args.out)
        print(json.dumps(index.manifest, indent=2))


if __name__ == "__main__":
    main()
