"""The leak invariant (2026-07-11 postmortem): worklist construction must be a pure function of
the REVIEW-TIME record (`input.*`) — deleting every `gold.*` field must leave the generated sites
and battery identical. The previous construction preferred `gold.delta_total` (the post-review
revision delta), which showed the system the author's eventual fixes and shrank the search space
~2x toward gold regions. Every future site source must keep this test green."""

import copy
import json
from pathlib import Path

from src.datasets.pr_review_v2.site_worklist import pr_sites_with_spans, FACETS, FACET_HINTS

RECORDS = Path("inputs/pr_review_v2/mathlib_pr_review_v2_annotated_20260612.jsonl")


def _records(n=8):
    rows = [json.loads(l) for l in RECORDS.read_text().splitlines() if l.strip()]
    # spread: include the known extremes (33294 big, 33104 small) plus the first few
    picked = {r["pr_number"]: r for r in rows if r["pr_number"] in (33294, 33104, 33421, 33081)}
    for r in rows:
        if len(picked) >= n:
            break
        picked.setdefault(r["pr_number"], r)
    return list(picked.values())


def test_worklist_sites_are_gold_independent():
    for rec in _records():
        stripped = copy.deepcopy(rec)
        stripped["gold"] = {}
        assert pr_sites_with_spans(rec) == pr_sites_with_spans(stripped), (
            f"PR {rec['pr_number']}: sites depend on gold.* — future-state leak")


def test_worklist_sites_nonempty_and_reviewtime_sized():
    """The raw diff yields the full review-time surface (PR 33294 has ~51 sites, not the 6 the
    leaked delta produced)."""
    rows = {r["pr_number"]: r for r in _records()}
    assert len(pr_sites_with_spans(rows[33294])) >= 40
    assert all(len(pr_sites_with_spans(r)) >= 1 for r in rows.values())


def test_battery_covers_all_facets_with_hints():
    assert set(FACET_HINTS) == set(FACETS) and len(FACETS) == 8
