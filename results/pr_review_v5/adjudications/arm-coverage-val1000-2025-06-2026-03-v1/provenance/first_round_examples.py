"""Export earlier development PRs paired with the human requests both census readers identified.

Run from the repository root with PYTHONPATH=. ape/bin/python, passing an output JSONL path.
The input omits unverified titles. Locations selected by human reviewers belong only to the
supervision. The cutoff applies to all recorded round-one feedback on a PR.
"""

import argparse
import json
import subprocess
from collections import defaultdict
from pathlib import Path

from src.datasets.pull_requests.definitions import load_roster
from src.datasets.pull_requests.projections.episodes import project_episodes
from src.datasets.pull_requests.store import PullRequestStore, write_atomically
from src.mathlib_review.io import jsonl_bytes, jsonl_rows, sha256_bytes


CENSUS = Path(__file__).resolve().parents[1]
DRAW = Path("inputs/pull_requests/evaluation/val1000-2025-06-2026-03-v1")
RELEASES = Path("inputs/pr_review_v4/releases")
FEEDBACK = ("2245585ab247470e761b3837a730af6d566f4c2e:results/pr_review_v5/probes/"
            "reusable-review-knowledge-2026-10-24/eval/v1k/feedback.json")
CUTOFF = "2026-01-01T00:00:00Z"
REQUEST_FIELDS = ("event_id", "kind", "at", "gh_id", "in_reply_to", "path", "line", "body")


def examples():
    draw = json.loads((DRAW / "draw.json").read_text())
    feedback = json.loads(subprocess.check_output(["git", "show", FEEDBACK]))
    if feedback["seal"] != draw["frame_seal_sha256"]:
        raise ValueError("Feedback and accepted draw have different seals")
    reserved = set()
    for name in ("val-2025-06-2026-03-v1", "eval-2025-06-2026-03-v1"):
        reserved.update(json.loads((RELEASES / name / "manifest.json").read_text())["pr_numbers"])
    if reserved.intersection(row["pr_number"] for row in draw["accepted"]):
        raise ValueError("Reserved PR in development source")

    def ask_ids(reader):
        return {row["cid"] for row in jsonl_rows(CENSUS / f"reader_{reader}.jsonl")
                if row["is_ask"] == "ask"}

    agreed = ask_ids("A") & ask_ids("B")
    events = {r["cid"]: r["event_id"] for r in jsonl_rows(CENSUS / "events.jsonl")}
    by_pr = defaultdict(list)
    for row in feedback["rows"]:
        if events[row["cid"]] != row["event_id"]:
            raise ValueError(f"Request ID mismatch at {row['cid']}")
        by_pr[row["pr"]].append(row)

    store = PullRequestStore()
    roster = load_roster(Path(json.loads((DRAW / "spec.json").read_text())["roster_path"]))
    for item in draw["accepted"]:
        number = item["pr_number"]
        rows = by_pr[number]
        requests = [r for r in rows if r["cid"] in agreed]
        if not requests or any(r["at"] >= CUTOFF for r in rows):
            continue
        projection = project_episodes(store, roster=roster, prs=[number])
        episode, = projection.episodes
        boundary, = projection.boundaries
        if episode.episode_id != item["episode_id"] or episode.base_sha != item["base_sha"]:
            raise ValueError(f"Reviewed snapshot mismatch on PR {number}")
        if sha256_bytes(episode.diff.encode()) != episode.patch_sha256:
            raise ValueError(f"Diff checksum mismatch on PR {number}")
        if episode.description.text and episode.description.provenance != "review_time_verified":
            raise ValueError(f"Unexpected description provenance on PR {number}")
        if not {r["event_id"] for r in requests} <= set(boundary.feedback_event_ids):
            raise ValueError(f"Feedback outside the original review round on PR {number}")
        yield {
            "pr_number": number, "episode_id": episode.episode_id,
            "base_sha": episode.base_sha, "reviewed_head_sha": episode.reviewed_head_sha,
            "patch_sha256": episode.patch_sha256, "review_started_at": boundary.review_started_at,
            "description_provenance": episode.description.provenance,
            "input": {"description": episode.description.text, "diff": episode.diff},
            "requests": [{key: r[key] for key in REQUEST_FIELDS} for r in requests],
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    destination = parser.parse_args().output
    pairs = list(examples())
    write_atomically(destination, jsonl_bytes(pairs))
    print(f"{len(pairs)} reviewed PRs, {sum(len(r['requests']) for r in pairs)} expert requests")
