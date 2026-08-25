"""
D3 evaluation: did the model's review localize WHERE the revision happened?
(spec §4 D3). No LLM — pure geometric overlap, so this is the judge-free anchor
of the suite.

Coordinate basis (confirmed with the researcher 2026-06-12):
  Predicted finding anchors are in h0 coordinates (the model sees δ₀ = diff(base, h0),
  whose new side is the h0 file). The gold "code that had to change" is therefore the
  `removed_in_revision` hunks of Δ — code present in P0 = diff(base, h0) but gone in the
  revision — whose new_start/new_lines are in h0 coordinates and align with predicted anchors.
  `added_in_revision` hunks live in h1/merged coordinates and have no clean h0 line, so they
  are NOT used as localization targets.

Gold:
  delta_near (h0→h1, review-round-1) removed_in_revision spans = primary target.
  delta_total (h0→merged) removed_in_revision spans = "everything review eventually required",
  and its complement within δ₀ = code that survived untouched = the false-positive control.

Metrics (per PR and aggregate; primary on the review_commit_id slice per the Step-2 audit):
  recall    = gold removed-spans covered by ≥1 line-anchored prediction / all gold removed-spans
  precision = line-anchored predictions hitting ≥1 gold removed-span / all line-anchored predictions
  control_fp_rate = predictions landing only on untouched δ₀ code / line-anchored predictions
  (delta_near primary; delta_total reported alongside.)

Usage:
  python -m src.datasets.pr_review_v2.evaluate_d3 <gold_annotated.jsonl> <preds.jsonl> [target=near|total]
"""

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

Span = Tuple[int, int]
_HUNK_HEADER_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
_NEWFILE_RE = re.compile(r"^\+\+\+ b/(.+)$")


# ---------------------------------------------------------------------------
# span extraction
# ---------------------------------------------------------------------------

def removed_spans(hunks: Optional[List[Dict[str, Any]]]) -> Dict[str, List[Span]]:
    """h0-coordinate spans of removed_in_revision hunks, per file."""
    by_path: Dict[str, List[Span]] = {}
    for hunk in hunks or []:
        if hunk.get("op") != "removed_in_revision":
            continue
        start = hunk.get("new_start")
        if start is None:
            continue
        length = hunk.get("new_lines") or 1
        by_path.setdefault(hunk["path"], []).append((start, start + max(length, 1) - 1))
    return by_path


def diff_new_side_spans(diff_text: Optional[str]) -> Dict[str, List[Span]]:
    """New-side (h0) line spans of every hunk in the assembled δ₀ unified diff, per file.

    This is the set of lines the model could legitimately anchor to; its part not in
    delta_total removed-spans is the untouched-code control region.
    """
    by_path: Dict[str, List[Span]] = {}
    current: Optional[str] = None
    for line in (diff_text or "").splitlines():
        m_file = _NEWFILE_RE.match(line)
        if m_file:
            current = m_file.group(1)
            continue
        m_hunk = _HUNK_HEADER_RE.match(line)
        if m_hunk and current:
            start = int(m_hunk.group(1))
            length = int(m_hunk.group(2) or 1)
            by_path.setdefault(current, []).append((start, start + max(length, 1) - 1))
    return by_path


def _overlaps(a: Span, spans: List[Span]) -> bool:
    return any(a[0] <= b[1] and b[0] <= a[1] for b in spans)


def _pred_spans(finding: Dict[str, Any]) -> Optional[Tuple[str, Span]]:
    anchor = finding.get("anchor")
    if not anchor or not anchor.get("path") or anchor.get("line_start") is None:
        return None
    start = anchor["line_start"]
    end = anchor.get("line_end") or start
    return anchor["path"], (min(start, end), max(start, end))


# ---------------------------------------------------------------------------
# evaluation
# ---------------------------------------------------------------------------

def evaluate_pr(
    record: Dict[str, Any], prediction: Dict[str, Any], *, target: str
) -> Optional[Dict[str, Any]]:
    if not prediction.get("parse_ok"):
        return None
    gold_key = "delta_near" if target == "near" else "delta_total"
    gold = removed_spans(record["gold"].get(gold_key))
    total = removed_spans(record["gold"].get("delta_total"))
    diff_spans = diff_new_side_spans(record["input"].get("diff"))

    gold_span_list = [(path, span) for path, spans in gold.items() for span in spans]
    covered = [False] * len(gold_span_list)

    line_anchored = pr_level = file_only = 0
    hits = control_fp = off_diff = 0
    finding_rows: List[Dict[str, Any]] = []

    for finding in prediction["findings"]:
        parsed = _pred_spans(finding)
        anchor = finding.get("anchor")
        if parsed is None:
            if not anchor or not anchor.get("path"):
                pr_level += 1
            else:
                file_only += 1
            continue
        line_anchored += 1
        path, span = parsed

        hit = False
        for i, (gpath, gspan) in enumerate(gold_span_list):
            if gpath == path and _overlaps(span, [gspan]):
                covered[i] = True
                hit = True
        if hit:
            hits += 1

        in_total = path in total and _overlaps(span, total[path])
        in_diff = path in diff_spans and _overlaps(span, diff_spans[path])
        classification = "hit" if hit else (
            "needed_by_merge" if in_total else
            "control_fp" if in_diff else "off_diff"
        )
        if classification == "control_fp":
            control_fp += 1
        elif classification == "off_diff":
            off_diff += 1
        finding_rows.append({
            "path": path, "span": list(span),
            "severity": finding.get("severity"),
            "class": classification,
            "claim": finding.get("claim", "")[:160],
        })

    n_gold = len(gold_span_list)
    return {
        "pr_number": prediction["pr_number"],
        "h0_resolution": record["input"]["h0_resolution"],
        "verdict": record["gold"]["verdict"],
        "gold_removed_spans": n_gold,
        "gold_covered": sum(covered),
        "line_anchored": line_anchored,
        "pr_level": pr_level,
        "file_only": file_only,
        "hits": hits,
        "control_fp": control_fp,
        "off_diff": off_diff,
        "is_control_pr": n_gold == 0,
        "findings": finding_rows,
    }


def aggregate(per_pr: List[Dict[str, Any]], *, slice_name: str) -> Dict[str, Any]:
    t = Counter()
    for pr in per_pr:
        for key in ("gold_removed_spans", "gold_covered", "line_anchored",
                    "hits", "control_fp", "off_diff", "pr_level", "file_only"):
            t[key] += pr[key]
    control_prs = [pr for pr in per_pr if pr["is_control_pr"]]
    control_findings = sum(
        pr["line_anchored"] + pr["pr_level"] + pr["file_only"] for pr in control_prs
    )
    return {
        "slice": slice_name,
        "prs": len(per_pr),
        "gold_removed_spans": t["gold_removed_spans"],
        "recall": round(t["gold_covered"] / t["gold_removed_spans"], 3) if t["gold_removed_spans"] else None,
        "line_anchored_predictions": t["line_anchored"],
        "precision": round(t["hits"] / t["line_anchored"], 3) if t["line_anchored"] else None,
        "control_fp_rate": round(t["control_fp"] / t["line_anchored"], 3) if t["line_anchored"] else None,
        "off_diff_rate": round(t["off_diff"] / t["line_anchored"], 3) if t["line_anchored"] else None,
        "unlocalized": {"pr_level": t["pr_level"], "file_only": t["file_only"]},
        "approval_control_prs": {
            "n": len(control_prs),
            "findings_per_pr": round(control_findings / len(control_prs), 2) if control_prs else None,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="D3 localization evaluation (no LLM)")
    parser.add_argument("gold", type=Path)
    parser.add_argument("predictions", type=Path)
    parser.add_argument("--target", choices=["near", "total"], default="near")
    args, remaining = parser.parse_known_args()
    # allow `target=near` style too
    for tok in remaining:
        if tok.startswith("target="):
            args.target = tok.split("=", 1)[1]

    gold_records = {
        (r := json.loads(line))["pr_number"]: r
        for line in args.gold.read_text().splitlines() if line.strip()
    }
    predictions = [json.loads(line) for line in args.predictions.read_text().splitlines() if line.strip()]

    per_pr: List[Dict[str, Any]] = []
    for pred in predictions:
        record = gold_records.get(pred["pr_number"])
        if record is None:
            continue
        result = evaluate_pr(record, pred, target=args.target)
        if result is not None:
            per_pr.append(result)

    review_commit = [pr for pr in per_pr if pr["h0_resolution"] == "review_commit_id"]
    report = {
        "target": args.target,
        "coordinate_basis": "predicted anchors (h0) vs removed_in_revision spans (h0)",
        "all": aggregate(per_pr, slice_name="all"),
        "review_commit_id_primary": aggregate(review_commit, slice_name="review_commit_id"),
        "per_pr": per_pr,
    }

    stem = f"{args.predictions.stem}_d3_{args.target}"
    report_file = args.predictions.parent / f"{stem}_report.json"
    report_file.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(json.dumps({k: v for k, v in report.items() if k != "per_pr"}, indent=2, ensure_ascii=False))
    print(f"\nReport: {report_file}")


if __name__ == "__main__":
    main()
