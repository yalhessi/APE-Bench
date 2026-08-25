"""Compare two judge rubrics on the same pairs, same model, same harness.

There are no cached *script* verdicts under v8, so v8 cannot be scored with
`r0_judge_equivalence` — that comparator joins against the v7.1 script cache. The
comparison that isolates the rubric is v7.1-task vs v8-task: identical model, identical
orchestrator, identical pairs, rubric as the only variable.

Reports the three quantities the v8 change was predicted to move, all measurable from the
task arms alone (`audits/judge-prompt-regression.md` states the predictions in advance):

1. **Two-level separation** — how often the judge returns `issue=True, resolution=False`.
   v7.1-as-implemented dropped the clause instructing this; `gpt_5.2` never produced it.
2. **Bimodality** — pairs where the judge splits its own `sample_count` votes, and the
   implied self-agreement ceiling of a single-sample judge.
3. **Watch pairs** — the specific obligations R0 flagged: the stable rename-vs-proof-change
   error and the two coin-flip obligations.

Usage:
    python -m src.datasets.pr_review_v4.judge_rubric_report \\
        --arm v7.1=results/.../budgeted-rep1 --arm v7.1=results/.../budgeted-rep2 \\
        --arm v8=results/.../v8-rep1 ... --out results/.../rubric-comparison.json
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

from .io import load_jsonl, pretty_json_bytes, write_once
from .schema import SemanticMatch

#: Obligations R0 singled out, by id suffix.
WATCH = {
    "e373aeb72a4b": "stable error: gold wants a proof change, candidate asks for a rename",
    "0898b0478443": "bimodal: 'split is dead code' vs 'empty-branch binder should be rfl'",
    "4bfe0de1d5f6": "bimodal",
}


def _load_arm(dirs: List[Path]) -> Dict:
    matches, votes = [], {}
    for d in dirs:
        matches += load_jsonl(d / "semantic_matches.jsonl", SemanticMatch)
        vp = d / "sample_votes.jsonl"
        if vp.is_file():
            for row in (json.loads(l) for l in vp.read_text().splitlines() if l.strip()):
                votes[(row["candidate_id"], row["obligation_id"])] = row
    return {"matches": matches, "votes": votes}


def summarize(arm: Dict) -> Dict:
    matches, votes = arm["matches"], arm["votes"]
    n = len(matches)
    issue = sum(m.issue_match for m in matches)
    resolution = sum(m.resolution_match for m in matches)
    issue_only = sum(m.issue_match and not m.resolution_match for m in matches)
    collapsed = sum(m.issue_match == m.resolution_match for m in matches)

    split = [k for k, v in votes.items() if not v.get("unanimous", True)]
    ceiling = None
    if votes:
        total = 0.0
        for v in votes.values():
            p = v["issue_votes"] / max(v["samples"], 1)
            total += p * p + (1 - p) * (1 - p)
        ceiling = total / len(votes)

    return {
        "pairs": n,
        "issue_match": issue,
        "resolution_match": resolution,
        "issue_only_verdicts": issue_only,
        "levels_collapsed_pairs": collapsed,
        "levels_collapsed": collapsed == n,
        "split_vote_pairs": len(split),
        "self_agreement_ceiling": ceiling,
    }


def watch_rows(arm: Dict) -> List[Dict]:
    rows = []
    by_obl = defaultdict(list)
    for m in arm["matches"]:
        suffix = m.obligation_id[-12:]
        if suffix in WATCH:
            by_obl[suffix].append(m)
    for suffix, ms in sorted(by_obl.items()):
        votes = [
            arm["votes"].get((m.candidate_id, m.obligation_id), {}).get("issue_votes")
            for m in ms
        ]
        rows.append({
            "obligation_suffix": suffix,
            "note": WATCH[suffix],
            "pairs": len(ms),
            "issue_true": sum(m.issue_match for m in ms),
            "issue_votes_by_pair": votes,
            "reasons": [m.reason[:160] for m in ms],
        })
    return rows


def compare(arms: Dict[str, List[Path]]) -> Dict:
    loaded = {name: _load_arm(dirs) for name, dirs in arms.items()}
    report = {
        "schema_version": "judge-rubric-comparison1",
        "arms": {name: summarize(a) for name, a in loaded.items()},
        "watch_pairs": {name: watch_rows(a) for name, a in loaded.items()},
    }
    # The three pre-registered predictions, evaluated only when both arms are present.
    if len(loaded) == 2 and "v7.1" in loaded and "v8" in loaded:
        a, b = report["arms"]["v7.1"], report["arms"]["v8"]
        report["predictions"] = {
            "two_level_separation_appears": {
                "v7.1_issue_only": a["issue_only_verdicts"],
                "v8_issue_only": b["issue_only_verdicts"],
                "moved": b["issue_only_verdicts"] != a["issue_only_verdicts"],
            },
            "bimodality_falls": {
                "v7.1_split_pairs": a["split_vote_pairs"],
                "v8_split_pairs": b["split_vote_pairs"],
                "fell": b["split_vote_pairs"] < a["split_vote_pairs"],
                "note": (
                    "persistence means the contested asks are genuinely ambiguous and "
                    "need a human ruling, not a better prompt"
                ),
            },
            "self_agreement_ceiling": {
                "v7.1": a["self_agreement_ceiling"], "v8": b["self_agreement_ceiling"],
            },
        }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare judge rubrics on the same pairs")
    parser.add_argument("--arm", action="append", required=True,
                        help="NAME=path/to/task-arm-dir (repeatable)")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    arms: Dict[str, List[Path]] = defaultdict(list)
    for spec in args.arm:
        name, _, path = spec.partition("=")
        arms[name].append(Path(path))

    report = compare(dict(arms))
    write_once(args.out, pretty_json_bytes(report))
    print(json.dumps({
        "arms": {k: {kk: vv for kk, vv in v.items() if kk != "pairs"}
                 for k, v in report["arms"].items()},
        "predictions": report.get("predictions"),
        "out": str(args.out),
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
