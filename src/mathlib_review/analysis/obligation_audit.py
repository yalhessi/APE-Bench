"""Check each scored obligation against the comment a maintainer actually wrote.

An obligation in this release is usually a *migration* — 18 of the 20 anchored ones on the
heldout set carry `annotation.status == "migration_proposal"`, meaning an automated pass
turned a review comment into a structured ask, and no curator confirmed the result. That
process can overstate, and when it does the agent is scored against something nobody
requested.

The case that prompted this, verified end to end. PR 33321's module-doc obligation reads:

    Revise the module-level documentation to explicitly account for the need for an ordered
    coefficient set in the proof ... by adding an "Implementation details" discussion
    outlining the approach taken to handle ordered coefficients.

The comment behind it (`event:a1e8242ebbbe634804f4474f`, jcommelin) is a one-line GitHub
suggestion block:

    ```suggestion
    The proof needs a set of ordered coefficients, even though the ultimate existence
    statement does
    ```

A wording fix became a request for a new documentation section. The outcome observation then
records the obligation as **dropped** on the evidence that the module doc was *"unchanged
except for a minor wording tweak ('existence ultimate' → 'ultimate existence')"* — which is
the maintainer's suggestion being **adopted**. So the same row overstates the ask and
misreports its own outcome, and an agent that made exactly the requested edit would score a
miss.

This module does not edit gold. It reports, so the decision to exclude a row is made
deliberately and before results are read, rather than discovered afterwards in a number.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence
from src.mathlib_review.paths import LEGACY_V2_BUNDLES

#: Where the raw GitHub bundles live. `source_object.path` in an event points here.
#: Restated `LEGACY_V2_BUNDLES` until the packages merged and the guard could
#: see it. Two spellings of one directory is how one of them goes stale.
BUNDLE_ROOT = LEGACY_V2_BUNDLES

#: A GitHub suggestion block. Its presence is decisive: a suggestion is a *literal
#: replacement text*, so the ask is bounded by what it contains. An obligation demanding
#: structural work on top of a suggestion block has added something the maintainer did not.
_SUGGESTION = re.compile(r"```suggestion\s*(.*?)```", re.S)

#: Words that turn a request into a larger one. Used only to flag rows for reading, never to
#: decide them: the judgement is made by a person looking at the pair.
_EXPANSION_MARKERS = (
    "by adding", "add a section", "implementation details", "outlining", "discussion",
    "refactor", "restructure", "throughout", "everywhere", "all call sites",
)


@dataclass(frozen=True)
class AuditRow:
    """One obligation beside the comment it came from."""

    pr_number: int
    obligation_id: str
    claim: str
    status: str
    outcome: Optional[str]
    outcome_evidence: str
    comments: Sequence[str]
    suggestion_only: bool
    expansion_markers: Sequence[str]
    length_ratio: float

    @property
    def flagged(self) -> bool:
        """Worth a human read before it is scored.

        Two independent signals, deliberately not combined into a score: the comment was a
        bare suggestion block while the obligation asks for more, or the obligation is much
        longer than the comment *and* uses language that widens scope.
        """

        return bool(
            (self.suggestion_only and self.expansion_markers)
            or (self.length_ratio >= 2.5 and self.expansion_markers)
        )

    def render(self) -> Dict[str, Any]:
        return {
            "pr_number": self.pr_number,
            "obligation_id": self.obligation_id,
            "status": self.status,
            "outcome": self.outcome,
            "flagged": self.flagged,
            "suggestion_only": self.suggestion_only,
            "expansion_markers": list(self.expansion_markers),
            "length_ratio": round(self.length_ratio, 2),
            "claim": self.claim,
            "maintainer_comments": list(self.comments),
            "outcome_evidence": self.outcome_evidence,
        }


def _bundle_comments(pr_number: int, root: Path = BUNDLE_ROOT) -> Dict[str, str]:
    """`source_key` -> comment body, for one PR's raw GitHub bundle.

    Events reference their comment by `source_key` (`/review_comments/2`), so the join is on
    position within the bundle rather than on any id the migration invented.
    """

    path = root / f"pr_{pr_number}.json"
    if not path.is_file():
        return {}
    try:
        bundle = json.loads(path.read_text())
    except (OSError, ValueError):
        return {}
    out: Dict[str, str] = {}
    for name in ("review_comments", "issue_comments", "reviews"):
        for index, comment in enumerate(bundle.get(name) or []):
            body = comment.get("body") or ""
            out[f"/{name}/{index}"] = body
    return out


def _events_by_id(release: Path) -> Dict[str, Dict[str, Any]]:
    """Events carry the `source_key` into the bundle; they live in whichever release shipped
    them, so every release under the same root is searched."""

    found: Dict[str, Dict[str, Any]] = {}
    for candidate in sorted(release.parent.glob("*/source/events.jsonl")):
        for line in candidate.read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            found.setdefault(row.get("event_id"), row)
    return found


def audit(release: Path, pr_numbers: Optional[Iterable[int]] = None) -> List[AuditRow]:
    """Join every anchored obligation to its maintainer comment and its recorded outcome."""

    wanted = set(pr_numbers) if pr_numbers else None
    gold = release / "gold"
    events = _events_by_id(release)

    outcomes: Dict[str, List[Dict[str, Any]]] = {}
    for line in (gold / "outcome_observations.jsonl").read_text().splitlines():
        if line.strip():
            row = json.loads(line)
            outcomes.setdefault(row["judgment_id"], []).append(row)

    bundles: Dict[int, Dict[str, str]] = {}
    rows: List[AuditRow] = []
    for line in (gold / "judgments.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        judgment = json.loads(line)
        pr_number = judgment.get("pr_number")
        if wanted is not None and pr_number not in wanted:
            continue
        if pr_number not in bundles:
            bundles[pr_number] = _bundle_comments(pr_number)
        bodies = []
        for event_id in judgment.get("source_event_ids") or []:
            event = events.get(event_id) or {}
            key = event.get("source_key")
            if key and key in bundles[pr_number]:
                bodies.append(bundles[pr_number][key])
        observed = outcomes.get(judgment["judgment_id"], [])
        for obligation in judgment.get("obligations") or []:
            if not obligation.get("change_ids"):
                continue
            claim = obligation.get("claim") or ""
            joined = "\n".join(bodies)
            suggestions = _SUGGESTION.findall(joined)
            outside = _SUGGESTION.sub(" ", joined).strip()
            rows.append(AuditRow(
                pr_number=pr_number,
                obligation_id=obligation["obligation_id"],
                claim=claim,
                status=(judgment.get("annotation") or {}).get("status", "?"),
                outcome=observed[0].get("outcome") if observed else None,
                outcome_evidence=observed[0].get("evidence", "") if observed else "",
                comments=bodies,
                # A comment that is *only* a suggestion block bounds the ask to its text.
                suggestion_only=bool(suggestions) and len(outside) < 40,
                expansion_markers=[m for m in _EXPANSION_MARKERS if m in claim.lower()],
                length_ratio=(len(claim) / max(len(joined), 1)) if joined else 0.0,
            ))
    return rows


def audit_report(rows: Sequence[AuditRow]) -> Dict[str, Any]:
    """Counts first, then the rows a person needs to read."""

    import collections

    return {
        "obligations": len(rows),
        "by_status": dict(collections.Counter(r.status for r in rows)),
        "by_outcome": dict(collections.Counter(str(r.outcome) for r in rows)),
        "without_a_matched_comment": sum(1 for r in rows if not r.comments),
        "flagged_for_review": [r.render() for r in rows if r.flagged],
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--pr-numbers", type=int, nargs="*")
    args = parser.parse_args()
    rows = audit(args.release, args.pr_numbers)
    print(json.dumps(audit_report(rows), indent=2))


if __name__ == "__main__":
    main()
