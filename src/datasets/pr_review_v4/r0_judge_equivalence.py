"""R0: does the registered-task judge agree with the script judge?

The judge migration is only safe if it moves no numbers. This compares, pair by pair, the
verdicts cached by `semantic_judge` (the script arm) against those produced by
`judge_runner` (the task arm), joined on the script's cache key — which is exactly the
identity the task record carries.

Two gates, both pre-registered in the roadmap:

1. **Agreement** — at least 95% of pairs must receive identical `issue_match` and
   `resolution_match`. Below that the arms are different judges and every downstream
   comparison would be measuring the migration rather than the treatment.
2. **Stability** — with `sample_count=3`, no pair may split its votes. The known 2-of-3
   flip on byte-identical artifacts is worth ~4pp at n=8 denominators, which is why the
   migration is worth doing at all; this measures whether voting removed it.

Usage:
    python -m src.datasets.pr_review_v4.r0_judge_equivalence \\
        --release inputs/pr_review_v4/releases/dev-pilot-0.9.0 \\
        --candidates results/.../candidates.jsonl \\
        --task-arm results/pr_review_v4/audits/r0-judge-equivalence/task-arm-rep1 \\
        --out results/pr_review_v4/audits/r0-judge-equivalence/report-rep1.json
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List

from .io import canonical_json_bytes, load_jsonl, pretty_json_bytes, sha256_bytes, write_once
from .schema import CandidateClaim, InterventionView, JudgmentNode, SemanticMatch
from .legacy.judge_v71 import LEGACY_CACHE_DIR, LEGACY_JUDGE_VERSION
from .semantic_judge import build_pairs

AGREEMENT_THRESHOLD = 0.95


def _legacy_pair_key(pair, model: str) -> str:
    """The v7.1 cache key. Pinned to the retired rubric on purpose: this comparator exists
    to join against verdicts written under it, and would find nothing under the active one."""

    return sha256_bytes(canonical_json_bytes({
        "candidate_source_sha256": pair["candidate"].source_sha256,
        "obligation_source_sha256": pair["obligation"].source_sha256,
        "model": model, "judge_version": LEGACY_JUDGE_VERSION,
    }))


def compare(
    release: Path,
    candidates_path: Path,
    task_arm_dir: Path,
    model: str,
    cache_dir: Path = LEGACY_CACHE_DIR,
) -> Dict:
    judgments = load_jsonl(release / "gold/judgments.jsonl", JudgmentNode)
    views = load_jsonl(release / "gold/intervention_views.jsonl", InterventionView)
    candidates = load_jsonl(candidates_path, CandidateClaim)
    pairs = build_pairs(judgments, views, candidates)

    task_matches = {
        (item.candidate_id, item.obligation_id): item
        for item in load_jsonl(task_arm_dir / "semantic_matches.jsonl", SemanticMatch)
    }
    votes = {}
    votes_path = task_arm_dir / "sample_votes.jsonl"
    if votes_path.is_file():
        for row in (json.loads(l) for l in votes_path.read_text().splitlines() if l.strip()):
            votes[(row.get("candidate_id"), row.get("obligation_id"))] = row

    rows: List[Dict] = []
    for pair in pairs:
        key = _legacy_pair_key(pair, model)
        cache_path = cache_dir / f"{key}.json"
        pair_id = (pair["candidate"].candidate_id, pair["obligation"].obligation_id)
        script = json.loads(cache_path.read_text()) if cache_path.is_file() else None
        task = task_matches.get(pair_id)
        vote = votes.get(pair_id, {})
        rows.append({
            "candidate_id": pair_id[0],
            "obligation_id": pair_id[1],
            "cache_key": key,
            "script_present": script is not None,
            "task_present": task is not None,
            "script_issue": None if script is None else bool(script["issue_match"]),
            "script_resolution": None if script is None else bool(script["resolution_match"]),
            "task_issue": None if task is None else task.issue_match,
            "task_resolution": None if task is None else task.resolution_match,
            "issue_agrees": (
                None if script is None or task is None
                else bool(script["issue_match"]) == task.issue_match
            ),
            "resolution_agrees": (
                None if script is None or task is None
                else bool(script["resolution_match"]) == task.resolution_match
            ),
            "issue_votes": vote.get("issue_votes"),
            "samples": vote.get("samples"),
            "unanimous": vote.get("unanimous"),
        })

    comparable = [r for r in rows if r["issue_agrees"] is not None]
    issue_agree = sum(r["issue_agrees"] for r in comparable)
    resolution_agree = sum(r["resolution_agrees"] for r in comparable)
    split = [r for r in rows if r["unanimous"] is False]
    agreement = issue_agree / len(comparable) if comparable else None

    gates = {
        "agreement": {
            "observed": agreement,
            "required": AGREEMENT_THRESHOLD,
            "pass": agreement is not None and agreement >= AGREEMENT_THRESHOLD,
        },
        "no_split_votes": {
            "observed_split_pairs": len(split),
            "required": 0,
            "pass": not split,
        },
        "coverage": {
            "pairs": len(rows),
            "comparable": len(comparable),
            "missing_script": sum(not r["script_present"] for r in rows),
            "missing_task": sum(not r["task_present"] for r in rows),
            "pass": len(comparable) == len(rows),
        },
    }
    return {
        "schema_version": "r0-judge-equivalence1",
        "judge_version": LEGACY_JUDGE_VERSION,
        "judge_model": model,
        "release": release.as_posix(),
        "candidates": candidates_path.as_posix(),
        "task_arm": task_arm_dir.as_posix(),
        "issue_agreement": agreement,
        "resolution_agreement": (
            resolution_agree / len(comparable) if comparable else None
        ),
        "gates": gates,
        "decision": (
            "judge_migration_equivalent"
            if all(g["pass"] for g in gates.values())
            else "judge_migration_not_equivalent"
        ),
        "disagreements": [
            r for r in rows if r["issue_agrees"] is False or r["resolution_agrees"] is False
        ],
        "split_vote_pairs": split,
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="R0 judge-equivalence comparison")
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--task-arm", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--model", default="gpt_5_mini")
    parser.add_argument("--cache-dir", type=Path, default=LEGACY_CACHE_DIR)
    args = parser.parse_args()
    report = compare(args.release, args.candidates, args.task_arm, args.model, args.cache_dir)
    write_once(args.out, pretty_json_bytes(report))
    print(json.dumps({
        "decision": report["decision"],
        "issue_agreement": report["issue_agreement"],
        "resolution_agreement": report["resolution_agreement"],
        "gates": {k: v["pass"] for k, v in report["gates"].items()},
        "disagreements": len(report["disagreements"]),
        "split_vote_pairs": len(report["split_vote_pairs"]),
        "out": str(args.out),
    }, indent=2))


if __name__ == "__main__":
    main()
