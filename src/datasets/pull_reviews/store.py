"""The raw PR store: one directory per PR, holding what GitHub returned and nothing else.

    data/pull_reviews/pr/<n>/
      listing.json                                        tier 0, free from the listing walk
      review_comments.jsonl reviews.jsonl issue_comments.jsonl                       tier 1
      pr.json commits.jsonl files.jsonl timeline.jsonl review_threads.jsonl body_edits.jsonl
      compares/<head_sha>.json                                                        tier 2
      fetch.json                    the per-PR ledger: for every endpoint, when, from where,
                                    how many rows, which sha -- or that it came back null

**Payload files are immutable** (`io.write_once`): tiers add files, nothing is rewritten, and a
refetch that returns different bytes for an endpoint already recorded raises rather than
overwriting. One transition is allowed, because it gains information without moving any: a
recorded *null* may be filled once by a later successful fetch. GraphQL enrichment fails or needs a
token; if a null froze forever, one failed fetch would permanently omit that PR's description. The
reverse never happens -- a later failure does not erase a value. This is the "data never moves" rule applied at file granularity, so a projection that
pinned an endpoint's sha can never be silently invalidated. The ledger itself evolves as tiers are
added, but only by *adding* entries, each immutable once written, and it is replaced atomically so a
crash mid-collection cannot leave a PR unreadable.

**Null is not empty.** GraphQL enrichment (`review_threads`, `body_edits`) can fail, and the
funnel treats `body_edits is None` -- unknown edit history -- as "the description may have been
edited after review" and omits it, where `[]` means "never edited" and keeps it. Measured on the
201 cached bundles: `body_edits` is null in 1 and empty in 124. A store that wrote both as an empty
file would change episodes, so a null endpoint is recorded with no file.

**Never under `data/pr_review_v2/`.** Eleven and eight frozen release manifests hash the bundle and
compare caches there as trees, so one added file breaks them. The constructor refuses such a root.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple

from src.mathlib_review.io import (
    canonical_json_bytes, jsonl_bytes, sha256_bytes, write_once,
)
from src.mathlib_review.paths import LEGACY_V2_BUNDLES, PULL_REVIEWS_STORE

LEDGER_VERSION = "pull-review-ledger/1"
STORE_VERSION = "pull-review-store/1"

#: endpoint -> (tier, file name, shape). Order is the legacy bundle's key order after `pr`.
ENDPOINTS: Dict[str, Tuple[int, str, str]] = {
    "listing": (0, "listing.json", "object"),
    "review_comments": (1, "review_comments.jsonl", "list"),
    "reviews": (1, "reviews.jsonl", "list"),
    "issue_comments": (1, "issue_comments.jsonl", "list"),
    "pr": (2, "pr.json", "object"),
    "commits": (2, "commits.jsonl", "list"),
    "files": (2, "files.jsonl", "list"),
    "timeline": (2, "timeline.jsonl", "list"),
    "review_threads": (2, "review_threads.jsonl", "list"),
    "body_edits": (2, "body_edits.jsonl", "list"),
}

#: The endpoints of a legacy `data/pr_review_v2/cache/bundles/pr_<n>.json`, in its key order.
BUNDLE_ENDPOINTS = ("pr", "reviews", "review_comments", "issue_comments", "commits", "files",
                    "timeline", "review_threads", "body_edits")

TIERS: Dict[int, Tuple[str, ...]] = {
    tier: tuple(name for name, (t, _, _) in ENDPOINTS.items() if t == tier) for tier in (0, 1, 2)
}


class StoreError(RuntimeError):
    pass


class ImmutableEndpointError(StoreError):
    """An endpoint already recorded for a PR was offered different bytes."""


class IncompletePR(StoreError):
    """A reader asked for data from a tier this PR has not been collected to."""


def write_atomically(path: Path, content: bytes) -> None:
    """Replace `path` with `content` so readers see the old file or the new one, never half."""

    path.parent.mkdir(parents=True, exist_ok=True)
    handle, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(handle, "wb") as out:
            out.write(content)
            out.flush()
            os.fsync(out.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def _payload_bytes(shape: str, payload: Any) -> bytes:
    if shape == "object":
        if not isinstance(payload, dict):
            raise StoreError(f"object endpoint given {type(payload).__name__}")
        return canonical_json_bytes(payload) + b"\n"
    if not isinstance(payload, list):
        raise StoreError(f"list endpoint given {type(payload).__name__}")
    return jsonl_bytes(payload)


class PullReviewStore:
    """Read and append to the store. Consumers go through this, never through the layout."""

    def __init__(self, root: Path = PULL_REVIEWS_STORE):
        self.root = Path(root)
        forbidden = LEGACY_V2_BUNDLES.parent.parent.resolve()      # data/pr_review_v2
        resolved = self.root.resolve()
        if resolved == forbidden or forbidden in resolved.parents:
            raise StoreError(
                f"refusing a store under {forbidden}: frozen release manifests hash the caches "
                "there as trees, so writing any file into them breaks verify_frozen")

    # --- layout ----------------------------------------------------------------------------
    def pr_dir(self, number: int) -> Path:
        return self.root / "pr" / str(int(number))

    def _ledger_path(self, number: int) -> Path:
        return self.pr_dir(number) / "fetch.json"

    def numbers(self) -> List[int]:
        base = self.root / "pr"
        if not base.is_dir():
            return []
        return sorted(int(p.name) for p in base.iterdir()
                      if p.name.isdigit() and (p / "fetch.json").is_file())

    def has(self, number: int) -> bool:
        return self._ledger_path(number).is_file()

    # --- ledger ----------------------------------------------------------------------------
    def ledger(self, number: int) -> Dict[str, Any]:
        path = self._ledger_path(number)
        if not path.is_file():
            return {"schema_version": LEDGER_VERSION, "pr_number": int(number),
                    "endpoints": {}, "compares": {}}
        return json.loads(path.read_text(encoding="utf-8"))

    def _save_ledger(self, number: int, ledger: Dict[str, Any]) -> None:
        write_atomically(self._ledger_path(number),
                         (json.dumps(ledger, indent=1, sort_keys=True, ensure_ascii=False) + "\n")
                         .encode("utf-8"))

    def tiers(self, number: int) -> Set[int]:
        """Tiers whose every endpoint is recorded (present or null). Compares are tier 2 extras,
        needed per reviewed head, so they do not gate tier completeness."""

        recorded = set(self.ledger(number).get("endpoints", {}))
        return {tier for tier, names in TIERS.items() if set(names) <= recorded}

    # --- writing ---------------------------------------------------------------------------
    def write_endpoint(self, number: int, endpoint: str, payload: Any, *, request: str,
                       fetched_at: str, source: str) -> bool:
        """Record one endpoint's response. `payload is None` records a null (failed/absent)
        response with no file. Returns True if anything new was written."""

        if endpoint not in ENDPOINTS:
            raise StoreError(f"unknown endpoint {endpoint!r}")
        tier, filename, shape = ENDPOINTS[endpoint]
        ledger = self.ledger(number)
        if payload is None:
            entry = {"tier": tier, "file": None, "present": False, "rows": None, "sha256": None}
        else:
            content = _payload_bytes(shape, payload)
            entry = {"tier": tier, "file": filename, "present": True,
                     "rows": 1 if shape == "object" else len(payload),
                     "sha256": sha256_bytes(content)}
        existing = ledger["endpoints"].get(endpoint)
        if existing is not None:
            if existing["present"] and payload is None:
                return False                     # a later failure never erases a value
            if existing["present"] and existing["sha256"] != entry["sha256"]:
                raise ImmutableEndpointError(
                    f"PR {number} {endpoint}: already recorded ({existing['sha256']}), now "
                    f"offered ({entry['sha256']}); the store does not rewrite endpoints")
            if existing["present"] or payload is None:
                return False                     # identical, or null offered for a null
            entry["filled_from_null"] = {"fetched_at": existing.get("fetched_at"),
                                         "source": existing.get("source")}
        if payload is not None:
            write_once(self.pr_dir(number) / filename, content)
        entry.update({"request": request, "fetched_at": fetched_at, "source": source})
        ledger["endpoints"][endpoint] = entry
        self._save_ledger(number, ledger)
        return True

    def write_compare(self, number: int, head_sha: str, raw: bytes, *, base_ref: str,
                      request: str, fetched_at: str, source: str) -> bool:
        """A three-dot compare `base_ref...head_sha`, stored byte-verbatim so its sha256 equals
        the file it was fetched or copied as -- the episode builder hashes it into provenance."""

        ledger = self.ledger(number)
        sha = sha256_bytes(raw)
        existing = ledger["compares"].get(head_sha)
        if existing is not None:
            if existing["sha256"] != sha:
                raise ImmutableEndpointError(
                    f"PR {number} compare {head_sha[:12]}: recorded {existing['sha256']}, "
                    f"offered {sha}")
            return False
        relative = f"compares/{head_sha}.json"
        write_once(self.pr_dir(number) / relative, raw)
        ledger["compares"][head_sha] = {"file": relative, "sha256": sha, "base_ref": base_ref,
                                        "request": request, "fetched_at": fetched_at,
                                        "source": source}
        self._save_ledger(number, ledger)
        return True

    def record_legacy_bundle(self, number: int, record: Dict[str, Any]) -> None:
        ledger = self.ledger(number)
        if ledger.get("legacy_bundle") not in (None, record):
            raise ImmutableEndpointError(f"PR {number}: legacy bundle provenance differs")
        if ledger.get("legacy_bundle") == record:
            return
        ledger["legacy_bundle"] = record
        self._save_ledger(number, ledger)

    # --- reading ---------------------------------------------------------------------------
    def read(self, number: int, endpoint: str) -> Any:
        """The endpoint's payload; None for a recorded null. Raises if never fetched."""

        entry = self.ledger(number)["endpoints"].get(endpoint)
        if entry is None:
            raise IncompletePR(f"PR {number}: {endpoint} was never fetched "
                               f"(tiers present: {sorted(self.tiers(number))})")
        if not entry["present"]:
            return None
        path = self.pr_dir(number) / entry["file"]
        if ENDPOINTS[endpoint][2] == "object":
            return json.loads(path.read_text(encoding="utf-8"))
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()]

    def load_bundle(self, number: int) -> Dict[str, Any]:
        """The PR in the legacy bundle shape the funnel and event ledger consume. Requires tier 2."""

        if 2 not in self.tiers(number):
            raise IncompletePR(f"PR {number}: a bundle needs tier 2 "
                               f"(present: {sorted(self.tiers(number))})")
        ledger = self.ledger(number)
        legacy = ledger.get("legacy_bundle") or {}
        stamps = [e["fetched_at"] for e in ledger["endpoints"].values() if e.get("fetched_at")]
        bundle: Dict[str, Any] = {
            "bundle_version": legacy.get("bundle_version", STORE_VERSION),
            "fetched_at": legacy.get("fetched_at", max(stamps) if stamps else None),
        }
        for endpoint in BUNDLE_ENDPOINTS:
            bundle[endpoint] = self.read(number, endpoint)
        return bundle

    def bundle_sha256(self, number: int) -> str:
        """What an episode records as its bundle's hash. For a PR seeded from the legacy cache,
        the legacy file's sha -- which is what lets the store reproduce frozen episodes byte for
        byte. For a PR collected here, the hash of the canonical assembled bundle."""

        legacy = self.ledger(number).get("legacy_bundle")
        if legacy:
            return legacy["sha256"]
        return sha256_bytes(canonical_json_bytes(self.load_bundle(number)))

    def compare(self, number: int, head_sha: str) -> Tuple[Dict[str, Any], str]:
        """`(compare payload, sha256 of its stored bytes)` for a reviewed head."""

        entry = self.ledger(number)["compares"].get(head_sha)
        if entry is None:
            raise IncompletePR(f"PR {number}: no compare for head {head_sha[:12]}")
        raw = (self.pr_dir(number) / entry["file"]).read_bytes()
        return json.loads(raw), sha256_bytes(raw)

    def compares(self, number: int) -> "StoreCompares":
        """This PR's compares as a `diffs.CompareSource`, for the funnel."""
        return StoreCompares(self, number)

    def commit_timestamp(self, number: int, sha: str) -> Optional[str]:
        """Committer date of `sha` among this PR's commits -- the retrieval cutoff's source."""

        if "commits" not in self.ledger(number)["endpoints"]:
            return None
        for commit in self.read(number, "commits") or []:
            if str(commit.get("sha", "")) == sha:
                return ((commit.get("commit") or {}).get("committer") or {}).get("date")
        return None

    def iter_ledgers(self) -> Iterator[Dict[str, Any]]:
        for number in self.numbers():
            yield self.ledger(number)

    def bundle_ref(self, number: int):
        """What the funnel's event index cites as this PR's source. Seeded PRs cite the legacy
        bundle file they came from; collected PRs cite their store directory."""

        from src.mathlib_review.schema import ArtifactRef

        legacy = self.ledger(number).get("legacy_bundle")
        if legacy:
            return ArtifactRef(path=legacy["path"], role="raw_github_bundle", sha256=legacy["sha256"])
        return ArtifactRef(path=self.pr_dir(number).as_posix(), role="pull_review_pr",
                           sha256=self.bundle_sha256(number))

    def content_digest(self) -> str:
        """A deterministic digest of everything in the store: every PR's endpoint and compare
        shas. The index and every projection pin this, so a store that gains or loses one byte
        is a different store to all of them."""

        tree = {}
        for ledger in self.iter_ledgers():
            tree[str(ledger["pr_number"])] = {
                "endpoints": {k: v["sha256"] for k, v in sorted(ledger["endpoints"].items())},
                "compares": {k: v["sha256"] for k, v in sorted(ledger["compares"].items())},
            }
        return sha256_bytes(canonical_json_bytes(tree))


class StoreCompares:
    """A PR's compares from the store, as a `diffs.CompareSource`.

    A missing compare raises with the same message the directory source uses, so a funnel
    `hydration` exclusion reads identically whichever source produced it."""

    def __init__(self, store: PullReviewStore, number: int):
        self.store = store
        self.number = int(number)

    def review_diff(self, reviewed_head_sha: str):
        from src.mathlib_review.diffs import diff_from_compare

        try:
            payload, sha = self.store.compare(self.number, reviewed_head_sha)
        except IncompletePR:
            raise ValueError(
                f"expected one cached compare for {reviewed_head_sha}, found 0") from None
        return diff_from_compare(
            payload, sha, where=self.store.pr_dir(self.number) / "compares" / f"{reviewed_head_sha}.json")
