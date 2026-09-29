"""The reviewer-model probe, as one harness over any set (`docs/plans/2026-09-29-probe-harness.md`).

The probe compares reviewers on one PR at a time against the asks its maintainers made in round 1:
Claude sessions driven through `cli tool`, the pipeline's `gpt_5.2` conditions through `cli run`, and
blind matchers between them. Until 2026-09-29 each step was a script under `results/…/probes/`
hard-coded to one set. This module is those steps with the set as a parameter; the scripts stay where
they are as the record of what ran, and the tests hold this module to their committed outputs on the
post-cutoff set.

A set is a `ProbeSet`, read from `configs/probe_sets/<name>.yaml`.

**Order is part of the method.** Feedback is extracted only after every reviewer session on the set
has finished, and nothing a reviewer reads is written by a step that has seen feedback. The
extractor refuses a test-set PR, as the one it replaces did.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import yaml
from pydantic import BaseModel, ConfigDict, model_validator

#: The sealed test set: run once, never probed.
TEST_MANIFEST = Path("inputs/pr_review_v4/releases/eval-2025-06-2026-03-v1/manifest.json")
#: The roster the post-cutoff and validation extractions used; a PR-list source reads it too.
DEFAULT_ROSTER = Path("inputs/pull_requests/rosters/mathlib_roster_2026-09-11.txt")
REPO = "leanprover-community/mathlib4"


class FeedbackSource(BaseModel):
    """Where a set's round-1 episodes come from: a sealed draw, or a release's PR list."""

    model_config = ConfigDict(extra="forbid")
    draw: Optional[str] = None
    prs_of_release: bool = False

    @model_validator(mode="after")
    def _exactly_one(self):
        if bool(self.draw) == self.prs_of_release:
            raise ValueError("feedback: name a sealed `draw`, or set `prs_of_release: true`, not both")
        return self


class ProbeSet(BaseModel):
    """One set the probe runs on. Paths are repo-relative."""

    model_config = ConfigDict(extra="forbid")
    name: str
    release: Path
    #: The dataset config `cli tool` reads for the tool grant and the retrieval cutoff.
    dataset_config: Path
    #: The PRs reviewed. Asks are matched only on these.
    pr_numbers: List[int]
    feedback: FeedbackSource
    #: Comment ids are `<prefix><4 digits>`, numbered over the whole source.
    cid_prefix: str = "v"
    #: Where this set's packets, sessions, feedback and asks live.
    probe_dir: Path
    #: Claude sessions made before this harness, by PR: {pr: directory holding pr<N>/<session>/}.
    sessions_from: Dict[int, Path] = {}

    @property
    def feedback_file(self) -> Path:
        return self.probe_dir / "feedback.json"

    @property
    def asks_file(self) -> Path:
        return self.probe_dir / "asks.json"

    def session_dir(self, pr: int, session: str) -> Path:
        return Path(self.sessions_from.get(pr, self.probe_dir)) / f"pr{pr}" / session


def load_probe_set(path: Path) -> ProbeSet:
    return ProbeSet.model_validate(yaml.safe_load(Path(path).read_text()))


def _test_prs() -> set:
    return set(json.loads(TEST_MANIFEST.read_text())["pr_numbers"])


def _round1_episodes(spec: ProbeSet) -> List[Dict[str, Any]]:
    """[{pr_number, episode_id, stratum, month, targets, ai, author}] in the source's order."""

    if spec.feedback.draw:
        from src.datasets.pull_requests.projections.frame import Draw, load_sealed, seal_dir

        _spec, _members, seal_sha = load_sealed(spec.feedback.draw)
        draw = Draw.model_validate_json((seal_dir(spec.feedback.draw) / "draw.json").read_text())
        if draw.frame_seal_sha256 != seal_sha or not draw.complete:
            raise ValueError(f"{spec.feedback.draw}: the draw does not match its seal, or is incomplete")
        return [{"pr_number": a.pr_number, "episode_id": a.episode_id, "stratum": a.stratum,
                 "month": a.month, "targets": a.targets, "ai": bool(a.ai_evidence),
                 "author": a.author} for a in draw.accepted]
    rows = []
    for line in (spec.release / "input" / "episodes.jsonl").read_text().splitlines():
        e = json.loads(line)
        rows.append({"pr_number": e["pr_number"], "episode_id": e["episode_id"], "stratum": None,
                     "month": None, "targets": None, "ai": None, "author": None})
    return rows


def _seal_of(spec: ProbeSet) -> Optional[str]:
    if not spec.feedback.draw:
        return None
    from src.datasets.pull_requests.projections.frame import load_sealed

    return load_sealed(spec.feedback.draw)[2]


def extract_feedback(spec: ProbeSet, roster_path: Path = DEFAULT_ROSTER) -> Dict[str, Any]:
    """Round-1 reviewer feedback for every episode of the set's source, numbered `<prefix>0000…`.

    This is `arm-coverage-val1000-…/provenance/extract_draw_feedback.py` with the source and the id
    prefix as parameters, and it produces the same rows. A release episode whose id the store's
    projection does not reproduce is refused rather than matched loosely.
    """

    from src.datasets.pull_requests.definitions import load_roster
    from src.datasets.pull_requests.projections.episodes import project_episodes
    from src.datasets.pull_requests.store import PullRequestStore
    from src.mathlib_review.release.events import events_from_bundle

    episodes = _round1_episodes(spec)
    clash = {e["pr_number"] for e in episodes} & _test_prs()
    if clash:
        raise ValueError(f"test-set PRs in the source: {sorted(clash)}")
    if spec.feedback.draw:
        from src.datasets.pull_requests.projections.frame import load_sealed

        roster_path = Path(load_sealed(spec.feedback.draw)[0].roster_path)
    store, roster = PullRequestStore(), load_roster(roster_path)
    rows, no_feedback = [], []
    for a in episodes:
        n = a["pr_number"]
        proj = project_episodes(store, roster=roster, prs=[n])
        matches = [x for x in proj.boundaries if x.episode_id == a["episode_id"]]
        if len(matches) != 1:
            raise ValueError(f"PR {n}: the store projects no episode {a['episode_id']}")
        want = set(matches[0].feedback_event_ids)
        if not want:
            no_feedback.append(n)
            continue
        bundle = store.load_bundle(n)
        ids = {e.source_key: e.event_id
               for e in events_from_bundle(bundle, source_object=store.bundle_ref(n), repo=REPO)}
        got = []
        for kind, key in (("review", "reviews"), ("review_comment", "review_comments"),
                          ("issue_comment", "issue_comments")):
            for i, item in enumerate(bundle.get(key) or []):
                eid = ids.get(f"/{key}/{i}")
                if eid not in want:
                    continue
                got.append({
                    "pr": n, "event_id": eid, "kind": kind,
                    "author": (item.get("user") or {}).get("login"),
                    "at": item.get("submitted_at") or item.get("created_at"),
                    "state": item.get("state"), "path": item.get("path"),
                    "line": item.get("line") or item.get("original_line"),
                    "gh_id": item.get("id"), "in_reply_to": item.get("in_reply_to_id"),
                    "diff_hunk": (item.get("diff_hunk") or "")[-600:], "body": item.get("body") or "",
                    "pr_title": bundle["pr"].get("title"), "stratum": a["stratum"], "month": a["month"],
                    "targets": a["targets"], "ai": a["ai"], "pr_author": a["author"]})
        if len(got) != len(want):
            print("MISMATCH", n, len(got), len(want), file=sys.stderr)
        got.sort(key=lambda r: (r["at"] or "", r["kind"]))
        rows.extend(got)
    rows.sort(key=lambda r: (r["pr"], r["at"] or ""))
    ghmap = {}
    for i, r in enumerate(rows):
        r["cid"] = f"{spec.cid_prefix}{i:04d}"
        if r["gh_id"] is not None and r["kind"] == "review_comment":
            ghmap[r["gh_id"]] = r["cid"]
    for r in rows:
        r["reply_to_cid"] = (ghmap.get(r["in_reply_to"], "(parent outside round 1)")
                             if r["in_reply_to"] else None)
    return {"name": spec.feedback.draw or spec.name, "seal": _seal_of(spec),
            "accepted": len(episodes), "no_feedback": no_feedback, "rows": rows}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1))
