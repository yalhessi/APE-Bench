"""
Apply stratum/severity annotations (Step 3) to a v2 extract and report the
distribution that gates the task-definition choice.

Annotations live in a sidecar JSONL keyed by (pr_number, comment_id) so they
survive re-extraction; rows: {pr_number, comment_id, stratum, severity, note}.
Strata are defined in docs/research/stratum-rubric.md.

Usage:
  python -m src.datasets.pr_review_v2.annotate <records.jsonl> <annotations.jsonl> [-o annotated.jsonl]
"""

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

STRATA = ["V1", "V2", "V3", "V4"]
NON_FINDINGS = ["P", "Q"]


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def apply_annotations(records: List[Dict[str, Any]], annotations: List[Dict[str, Any]]) -> Dict[str, int]:
    index = {(a["pr_number"], a["comment_id"]): a for a in annotations}
    applied = 0
    missing: List[str] = []
    for record in records:
        for comment in record["gold"]["comments"]:
            note = index.pop((record["pr_number"], comment["id"]), None)
            if note is None:
                missing.append(f"{record['pr_number']}/{comment['id']}")
                continue
            comment["stratum"] = note["stratum"]
            comment["severity"] = note.get("severity")
            applied += 1
    return {"applied": applied, "unannotated_comments": len(missing), "stale_annotations": len(index)}


def report(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    comments = [c for r in records for c in r["gold"]["comments"] if c.get("stratum")]
    findings = [c for c in comments if c["stratum"] in STRATA]
    stratum_counts = Counter(c["stratum"] for c in comments)
    cross = Counter((c["stratum"], c.get("severity") or "-") for c in findings)
    n_findings = len(findings) or 1
    return {
        "annotated_comments": len(comments),
        "non_findings": {k: stratum_counts.get(k, 0) for k in NON_FINDINGS},
        "findings_total": len(findings),
        "stratum_distribution": {
            k: {"n": stratum_counts.get(k, 0), "pct_of_findings": round(100 * stratum_counts.get(k, 0) / n_findings, 1)}
            for k in STRATA
        },
        "verifiable_or_codifiable_pct": round(
            100 * sum(stratum_counts.get(k, 0) for k in ("V1", "V2", "V3")) / n_findings, 1
        ),
        "stratum_x_severity": {f"{s}/{sev}": n for (s, sev), n in sorted(cross.items())},
        "blocking_share_by_stratum": {
            s: round(
                100 * cross.get((s, "blocking"), 0) / max(1, stratum_counts.get(s, 0)), 1
            )
            for s in STRATA
        },
        "by_kind": dict(Counter(c["kind"] for c in findings)),
        "linked_findings": sum(1 for c in findings if c.get("link_confidence") != "none"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply Step-3 stratum annotations and report distribution")
    parser.add_argument("records", type=Path)
    parser.add_argument("annotations", type=Path)
    parser.add_argument("-o", "--output", type=Path, default=None)
    args = parser.parse_args()

    records = load_jsonl(args.records)
    annotations = load_jsonl(args.annotations)
    merge_stats = apply_annotations(records, annotations)

    if args.output:
        with args.output.open("w") as fh:
            for record in records:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(json.dumps({"merge": merge_stats, "report": report(records)}, indent=2))


if __name__ == "__main__":
    main()
