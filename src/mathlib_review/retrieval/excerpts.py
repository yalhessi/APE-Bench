"""Freeze the same dated inline excerpts for precedent search and catalogue construction."""

import json
import tempfile
from collections import Counter
from pathlib import Path

from ape.tasks.lean_tasks.formal_math.review.context_tools import MAX_SNIPPET
from src.datasets.pull_requests.definitions import scored_pr_numbers
from src.datasets.pull_requests.store import PullRequestStore
from src.mathlib_review.io import (
    jsonl_bytes, jsonl_rows, pretty_json_bytes, sha256_file, write_once,
)
from src.mathlib_review.retrieval.precedent_index import (
    DEFAULT_MODEL, PrecedentIndex, build, references_pr,
)
from src.mathlib_review.retrieval_gate import RetrievalGate, UngatedTimestamp


def excerpt(number, author, raw, gate, targets):
    """Return the actual display text available before the cutoff, or its exclusion reason."""
    if raw is None:
        return None, "raw_comment_missing"
    try:
        created = gate.epoch_of(raw.get("created_at"))
        updated = gate.epoch_of(raw.get("updated_at"))
    except UngatedTimestamp:
        return None, "unknown_revision_date"
    if updated < created or updated >= gate.cutoff_epoch:
        return None, "outside_revision_window"
    who = (raw.get("user") or {}).get("login")
    if not who or not author or who.casefold() == author.casefold():
        return None, "author_or_unknown_identity"
    body = (raw.get("body") or "").strip()
    hunk = (raw.get("diff_hunk") or "").strip()
    if not body or not hunk or not raw.get("path"):
        return None, "missing_comment_or_anchor"
    if any(references_pr(text, pr) for pr in targets for text in (body, hunk)):
        return None, "references_pilot_target"
    return {
        "comment_id": raw["id"], "pr_number": number, "path": raw["path"],
        "commenter": who, "created_at": raw["created_at"], "updated_at": raw["updated_at"],
        "body": body[:MAX_SNIPPET], "diff_hunk": hunk[-(2 * MAX_SNIPPET):],
    }, None


def freeze(out, source, cutoff, targets):
    episodes = jsonl_rows(source)
    store = PullRequestStore()
    gate = RetrievalGate(as_of=cutoff)
    withheld = set(scored_pr_numbers()) | set(targets)
    rows = []
    excluded = []
    for episode in episodes:
        number = episode["pr_number"]
        comments = {c["id"]: c for c in store.read(number, "review_comments")}
        author = (store.read(number, "listing").get("user") or {}).get("login")
        for request in episode["requests"]:
            key = int(request["gh_id"])
            reason = None
            if number in withheld:
                reason = "withheld_pr"
            elif request["kind"] != "review_comment":
                reason = request["kind"]
            else:
                row, reason = excerpt(number, author, comments.get(key), gate, targets)
            if reason:
                excluded.append({"pr_number": number, "id": key, "reason": reason})
            else:
                rows.append(row)
    rows.sort(key=lambda row: row["comment_id"])
    if not rows or len({row["comment_id"] for row in rows}) != len(rows):
        raise ValueError("Shared history is empty or has duplicate comment IDs")
    corpus = out / "excerpts.jsonl"
    write_once(corpus, jsonl_bytes(rows))
    write_once(out / "exclusions.jsonl", jsonl_bytes(excluded))
    manifest = {
        "view": "familiar-pr-inline-excerpts/v1", "source": str(source),
        "source_sha256": sha256_file(source), "source_prs": len(episodes),
        "cutoff_exclusive": cutoff, "withheld_targets": list(targets),
        "source_requests": len(rows) + len(excluded), "rows": len(rows),
        "retained_prs": len({row["pr_number"] for row in rows}),
        "comment_prefix_chars": MAX_SNIPPET, "hunk_suffix_chars": 2 * MAX_SNIPPET,
        "excluded": dict(Counter(row["reason"] for row in excluded)),
        "exclusions_sha256": sha256_file(out / "exclusions.jsonl"),
        "corpus_sha256": sha256_file(corpus),
    }
    write_once(out / "manifest.json", pretty_json_bytes(manifest))
    return corpus, manifest


def prepare(out, source, cutoff, targets):
    corpus, manifest = freeze(out, source, cutoff, targets)
    index = out / "index"
    if not index.exists():
        # Publish a complete index atomically. A concurrent preparer can finish first.
        with tempfile.TemporaryDirectory(dir=out) as temporary:
            built = build(corpus.resolve(), Path(temporary) / "index", local_files_only=True)
            path = built / "manifest.json"
            meta = json.loads(path.read_text())
            if not meta["model_revision"] or meta["rows"] != manifest["rows"]:
                raise ValueError("Index model revision missing or index and catalogue have different rows")
            meta["artifacts_sha256"] = {name: sha256_file(built / name)
                                       for name in ("embeddings.npy", "meta.jsonl")}
            path.write_bytes(pretty_json_bytes(meta))
            try:
                built.rename(index)
            except OSError:
                if not index.is_dir():
                    raise
    loaded = PrecedentIndex(index, expected_manifest_sha256=sha256_file(index / "manifest.json"))
    if (loaded.corpus_sha256 != manifest["corpus_sha256"]
            or loaded.model_name != DEFAULT_MODEL
            or [r["comment_id"] for r in loaded.meta] != [r["comment_id"] for r in jsonl_rows(corpus)]):
        raise ValueError("Search index and catalogue source disagree")
    return manifest
