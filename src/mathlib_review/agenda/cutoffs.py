"""The temporal cutoff every context read is gated on, derived without touching gold.

Retrieval that can see the future is not retrieval; it is the answer. Both existing corpora
already know this — `zulip.store.gate` drops messages at or after an instant *and* messages
referencing the PR under review, and `pr_review_v4.retrieval.validate_precedents` raises
rather than returning a future event. What neither supplies is *which* instant, for a
generation-side caller that is not allowed to look at gold.

`ReviewEpisodeBoundary.review_started_at` is the natural answer and the wrong one: it lives
under `gold/` because it is derived from the review events themselves, and a reviewer that
reads it is reading the thing it is supposed to predict the timing of.

So the cutoff is **the committer timestamp of `reviewed_head_sha`** — the commit the
reviewer is looking at. Three properties make it the right choice:

* It is *visible*. `reviewed_head_sha` is a field of `ReviewEpisodeInput`, the physically
  isolated reviewer-visible half of the episode.
* It is *conservative*. Review starts after the code was pushed, so this instant is at or
  before `review_started_at`; gating here can only ever be stricter than gating on the real
  boundary, never looser.
* It is *offline*. It comes from immutable collected data: the PR store's commit list, or for a
  PR the store does not hold, the cached v2 bundle.

**Where it is read from.** The store first, then the tracked v2 bundle cache. It used to be the
cache alone -- and eleven frozen release manifests hash that cache as a tree, so it is
append-forbidden, so no PR outside the 201 it holds could ever resolve a cutoff, so no new PR could
become a reviewable task. The store holds the same bytes for those 201 (seeded from the cache), so
every existing cutoff is unchanged -- `test_pull_requests_cutoffs` checks every episode of every
release both ways -- and the cache stays as the fallback because it is tracked in git while the store
is not: a fresh clone must still run the existing releases.

The cutoff is not the whole mechanism. `exclude_pr` is the other half, and it is the half
time cannot do: a thread *about* this PR can predate the reviewed commit and still give the
answer away.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, Optional

from src.mathlib_review.paths import LEGACY_V2_BUNDLES, PULL_REQUESTS_STORE
from src.mathlib_review.schema import ReviewEpisodeInput

#: Sentinel: "use the default store if it exists". `None` means "no store".
_DEFAULT = object()


class CutoffUnavailable(RuntimeError):
    """No cutoff could be derived, so no gated read may proceed.

    Raised rather than defaulting to "no cutoff" or to `now`. An ungated read is a silent
    leak, and a leak that fails loudly during a dry run costs nothing.
    """


def _bundle_path(pr_number: int, legacy_bundles: Path = LEGACY_V2_BUNDLES) -> Path:
    return legacy_bundles / f"pr_{pr_number}.json"


def _default_store():
    from src.datasets.pull_requests.store import PullRequestStore

    return PullRequestStore() if PULL_REQUESTS_STORE.is_dir() else None


def commit_timestamp(pr_number: int, sha: str, *, store=_DEFAULT,
                     legacy_bundles: Optional[Path] = LEGACY_V2_BUNDLES) -> Optional[str]:
    """Committer timestamp of `sha` among this PR's commits, as ISO-8601 Z: from the PR store,
    else from the cached v2 bundle. `store=None` / `legacy_bundles=None` disable a source."""

    if store is _DEFAULT:
        store = _default_store()
    if store is not None and store.has(pr_number) and \
            "commits" in store.ledger(pr_number)["endpoints"]:
        stamp = store.commit_timestamp(pr_number, sha)
        if stamp:
            return stamp
    if legacy_bundles is None:
        return None
    path = _bundle_path(pr_number, legacy_bundles)
    if not path.is_file():
        return None
    bundle = json.loads(path.read_text())
    for commit in bundle.get("commits") or []:
        if str(commit.get("sha", "")) == sha:
            committer = (commit.get("commit") or {}).get("committer") or {}
            return committer.get("date")
    return None


def episode_cutoff(episode: ReviewEpisodeInput) -> str:
    """The gate instant for one episode. Raises if it cannot be resolved."""

    stamp = commit_timestamp(episode.pr_number, episode.reviewed_head_sha)
    if stamp:
        return stamp
    raise CutoffUnavailable(
        f"cannot resolve a retrieval cutoff for episode {episode.episode_id}: "
        f"{episode.reviewed_head_sha[:12]} is in neither the PR store's commits for "
        f"#{episode.pr_number} ({PULL_REQUESTS_STORE}/pr/{episode.pr_number}) nor the cached v2 "
        f"bundle ({_bundle_path(episode.pr_number)}). Refusing to run an ungated context read -- "
        "collect the PR to tier 2 first (`python -m src.datasets.pull_requests.collect`)."
    )


def cutoffs_by_episode(episodes: Iterable[ReviewEpisodeInput]) -> Dict[str, str]:
    """`episode_id -> cutoff`, resolved for every episode or not at all.

    All-or-nothing on purpose: a partial map would let some arms run gated and others run
    ungated inside one comparison, and the ungated ones would look better.
    """

    resolved: Dict[str, str] = {}
    failures = []
    for episode in episodes:
        try:
            resolved[episode.episode_id] = episode_cutoff(episode)
        except CutoffUnavailable as exc:
            failures.append(str(exc))
    if failures:
        raise CutoffUnavailable(
            f"{len(failures)} episode(s) have no resolvable retrieval cutoff:\n  "
            + "\n  ".join(failures[:5])
        )
    return resolved
