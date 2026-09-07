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
* It is *offline*. It comes from the cached PR bundle, which is immutable and already the
  provenance root of v4's whole event ledger.

The cutoff is not the whole mechanism. `exclude_pr` is the other half, and it is the half
time cannot do: a thread *about* this PR can predate the reviewed commit and still give the
answer away.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, Optional

from src.datasets.pr_review_v4.paths import LEGACY_V2_BUNDLES
from src.datasets.pr_review_v4.schema import ReviewEpisodeInput


class CutoffUnavailable(RuntimeError):
    """No cutoff could be derived, so no gated read may proceed.

    Raised rather than defaulting to "no cutoff" or to `now`. An ungated read is a silent
    leak, and a leak that fails loudly during a dry run costs nothing.
    """


def _bundle_path(pr_number: int) -> Path:
    return LEGACY_V2_BUNDLES / f"pr_{pr_number}.json"


def commit_timestamp(pr_number: int, sha: str) -> Optional[str]:
    """Committer timestamp of `sha` within this PR's cached bundle, as ISO-8601 Z."""

    path = _bundle_path(pr_number)
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
        f"{episode.reviewed_head_sha[:12]} is not in the cached bundle for PR "
        f"#{episode.pr_number} ({_bundle_path(episode.pr_number)}). Refusing to run an "
        "ungated context read — fetch the bundle first "
        "(`python -m src.datasets.pr_review_v2.fetch`)."
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
