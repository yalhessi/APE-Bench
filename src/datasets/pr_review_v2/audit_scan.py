"""
Step-2 audit scan: aggregate sanity checks and red-flag counters for a v2
extract (docs/research/pr-review-v2-step2-audit.md).

Usage:
  python -m src.datasets.pr_review_v2.audit_scan <records.jsonl> [--bundles data/pr_review_v2/cache/bundles]

Counters mirror the audit doc sections so successive extracts are directly
comparable. With --bundles it also cross-checks h₀→h₁→final ordering against
the cached commit history (audit issue #7).
"""

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

PROCESS_COMMAND_RE = re.compile(
    r"\bbors\s+(?:merge|r\+|r-|d\+|d=)|\bmaintainer\s+(?:merge|delegate)\b|!bench\b",
    re.IGNORECASE,
)
TEMPLATE_HTML_RE = re.compile(r"<!--")
GITPOD_RE = re.compile(r"gitpod\.io/", re.IGNORECASE)
BORS_TITLE_RE = re.compile(r"^\s*\[(?:merged|closed) by bors\]", re.IGNORECASE)


def load_records(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def scan(records: List[Dict[str, Any]], bundles_dir: Optional[Path]) -> Dict[str, Any]:
    report: Dict[str, Any] = {}
    numbers = [r["pr_number"] for r in records]
    report["rows"] = len(records)
    report["pr_range"] = f"#{min(numbers)}..#{max(numbers)}" if numbers else None

    report["verdicts"] = dict(Counter(r["gold"]["verdict"] for r in records))
    report["h0_resolution"] = dict(Counter(r["input"]["h0_resolution"] for r in records))
    report["slices"] = {
        key: sum(1 for r in records if r["slices"].get(key))
        for key in ("merged", "author_is_maintainer", "multi_reviewer", "ai_authored", "automated_sweep")
    }

    comments = [(r, c) for r in records for c in r["gold"]["comments"]]
    report["comments_total"] = len(comments)
    report["comment_kinds"] = dict(Counter(c["kind"] for _, c in comments))
    report["link_confidence"] = dict(Counter(c["link_confidence"] for _, c in comments))

    # --- input hygiene (audit issues #2/#3) ---
    report["input_hygiene"] = {
        "bors_title_in_input": sum(1 for r in records if BORS_TITLE_RE.search(r["input"]["title"])),
        "template_html_in_description": sum(
            1 for r in records if TEMPLATE_HTML_RE.search(r["input"]["description"])
        ),
        "gitpod_badge_in_description": sum(
            1 for r in records if GITPOD_RE.search(r["input"]["description"])
        ),
        "description_maybe_post_edited": sum(
            1 for r in records if r["input"]["description_maybe_post_edited"]
        ),
        "empty_description": sum(1 for r in records if not r["input"]["description"].strip()),
    }

    # --- process commands in gold (audit issue #5) ---
    process_hits = [(r["pr_number"], c["id"]) for r, c in comments if PROCESS_COMMAND_RE.search(c["body"])]
    report["process_commands_in_gold"] = {
        "comments": len(process_hits),
        "prs": sorted({n for n, _ in process_hits}),
    }

    # --- delta stats + anomalies (audit issues #6/#7) ---
    def hunks(r: Dict[str, Any], key: str) -> List[Dict[str, Any]]:
        return r["gold"].get(key) or []

    report["delta"] = {
        "prs_with_near": sum(1 for r in records if hunks(r, "delta_near")),
        "near_hunks_total": sum(len(hunks(r, "delta_near")) for r in records),
        "near_ops": dict(Counter(h["op"] for r in records for h in hunks(r, "delta_near"))),
        "near_nonempty_total_empty": sorted(
            r["pr_number"] for r in records if hunks(r, "delta_near") and not hunks(r, "delta_total")
        ),
        "near_empty_total_nonempty": sorted(
            r["pr_number"] for r in records if not hunks(r, "delta_near") and hunks(r, "delta_total")
        ),
        "hydration_errors": sum(1 for r in records if r["validation"].get("hydration_error")),
    }

    # --- push-order risk (audit issue #4) ---
    fallback = [r for r in records if r["input"]["h0_resolution"] == "pushed_before_t1"]
    forced = [r for r in records if r["validation"]["force_push_before_t1"]]
    report["push_order_risk"] = {
        "pushed_before_t1": len(fallback),
        "force_push_before_t1": len(forced),
        "both": sum(1 for r in fallback if r["validation"]["force_push_before_t1"]),
    }

    # --- h₀→h₁→final ordering cross-check against cached commits (issue #7) ---
    if bundles_dir:
        violations = []
        for r in records:
            bundle_file = bundles_dir / f"pr_{r['pr_number']}.json"
            if not bundle_file.exists():
                continue
            bundle = json.loads(bundle_file.read_text())
            order = {}
            for idx, item in enumerate(bundle.get("commits") or []):
                if item.get("sha"):
                    order[item["sha"]] = idx
            h0 = order.get(r["input"]["head_sha"])
            h1 = order.get(r["validation"]["h1_sha"])
            final = order.get(r["validation"]["final_head_sha"])
            if None in (h0, h1, final) or not (h0 <= h1 <= final):
                violations.append(
                    {"pr": r["pr_number"], "h0": h0, "h1": h1, "final": final}
                )
        report["head_ordering_violations"] = violations

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Step-2 audit scan for a v2 extract")
    parser.add_argument("records", type=Path)
    parser.add_argument("--bundles", type=Path, default=None)
    args = parser.parse_args()
    report = scan(load_records(args.records), args.bundles)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
