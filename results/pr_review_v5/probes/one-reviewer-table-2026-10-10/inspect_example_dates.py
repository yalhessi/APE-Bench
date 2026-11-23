"""Compare the historical examples in the saved Opus briefs to each target's reviewed-head date.

Run from the repository root with PYTHONPATH=. ape/bin/python and this file's path.
Each row counts example appearances in one target brief. A source can appear on multiple PRs.
"""

import json
from functools import lru_cache
from pathlib import Path

from src.datasets.pull_requests.store import PullRequestStore
from src.mathlib_review.agenda.cutoffs import episode_cutoff
from src.mathlib_review.io import load_jsonl
from src.mathlib_review.release.events import events_from_bundle
from src.mathlib_review.retrieval_gate import RetrievalGate
from src.mathlib_review.schema import ReviewEpisodeInput


TABLE = Path(__file__).resolve().parent
BRIEFS = TABLE.parent / "conventions-ceiling-2026-10-04"
RELEASES = {
    "P14_val": Path("inputs/pr_review_v4/releases/val-2025-06-2026-03-v1"),
    "P14_post": Path("inputs/probes/probe-2026-07-08-v1"),
    "D12b": Path("inputs/pr_review_v4/releases/dev-medium-0.3.0"),
}


def main():
    examples = json.loads((BRIEFS / "examples_apt.json").read_text())["entries"]
    picks = json.loads((BRIEFS / "briefs_applicable_t.json").read_text())["prs"]
    store = PullRequestStore()

    @lru_cache(maxsize=None)
    def source_dates(number):
        events = events_from_bundle(
            store.load_bundle(number),
            repo="leanprover-community/mathlib4",
            source_object=store.bundle_ref(number),
        )
        return {event.event_id: event.occurred_at for event in events}

    print("panel PR reviewed_head_utc late_examples all_examples")
    for panel, release in RELEASES.items():
        scored = json.loads((TABLE / f"match_{panel}/session_stats.json").read_text())
        episodes = {
            episode.pr_number: episode
            for episode in load_jsonl(release / "input/episodes.jsonl", ReviewEpisodeInput)
        }
        late_total = example_total = affected = 0
        for target in sorted(map(int, scored)):
            cutoff = episode_cutoff(episodes[target])
            gate = RetrievalGate(as_of=cutoff, exclude_pr=target)
            shown = [row for entry in picks[str(target)] for row in examples[entry]]
            late = 0
            for row in shown:
                if gate.excludes_pr(pr_number=row["pr"]):
                    raise ValueError(f"Example {row['cid']} comes from its target PR {target}")
                timestamp = source_dates(row["pr"])[row["event_id"]]
                late += not gate.allows_time(timestamp)
            print(panel, target, cutoff, late, len(shown))
            late_total += late
            example_total += len(shown)
            affected += bool(late)
        print(f"{panel} total {late_total}/{example_total} at or after cutoff on {affected}/{len(scored)} PRs")


if __name__ == "__main__":
    main()
