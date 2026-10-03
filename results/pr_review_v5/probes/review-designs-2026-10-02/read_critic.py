"""Read a D2 (`structured_critic`) run against its first stage's audit: what the critic added.

The union a critic run files is every first-stage finding, labelled with the critic's position on
its cell, plus the critic's own (`stage == "critic"`, always an overturn). So the critic's audit
can differ from its first stage's in two ways, and this keeps them apart:

- an obligation hit by a critic-stage finding that the first stage's audit did not hit: the
  attributable increment;
- an obligation whose hit set changed although only first-stage findings touch it: the judge's
  draw on the same findings (its self-agreement is about 90%), not the critic.

Also counted: positions by kind, overturns by concern and whether they filed, refutations of
first-stage findings, and the critic's filings on the control PRs by concern.

Joins the judge's candidates to the union by (PR, claim): `findings.jsonl` rows carry
`finding_id` and claim, task results carry the stage labels. Reads task results through
`TaskStorage`, spends nothing. Run from the repository root:
    PYTHONPATH=$PWD/src ape/bin/python results/pr_review_v5/probes/review-designs-2026-10-02/read_critic.py \
        <critic run> <critic audit> <first-stage audit>
"""

import asyncio
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))


def short(obligation_id: str) -> str:
    return obligation_id.split(":", 1)[1][:8]


def audit(name: str):
    from src.mathlib_review.io import jsonl_rows

    base = ROOT / "results/pr_review_v5/audits" / name
    report = json.loads((base / "semantic_report.json").read_text())
    hit = {short(row["obligation_id"]) for row in report["per_obligation"]
           if row["issue_status"] == "hit"}
    by_obligation = defaultdict(set)
    for row in jsonl_rows(base / "semantic_matches.jsonl"):
        if row.get("issue_match"):
            by_obligation[short(row["obligation_id"])].add(row["candidate_id"])
    return report, hit, by_obligation


async def main(run_name: str, critic_audit: str, stage_audit: str) -> int:
    from ape.orchestration.persistence import TaskStorage
    from src.mathlib_review.io import jsonl_rows
    from src.mathlib_review.paths import run_dir

    report, hit, hitters = audit(critic_audit)
    stage_report, stage_hit, _ = audit(stage_audit)
    controls = set(report["silent_pr_emission"]["control_pr_numbers"])

    tasks = ROOT / ".ape/runs" / run_name / "tasks"
    results = []
    for task_dir in sorted(path for path in tasks.iterdir() if path.is_dir()):
        raw = await TaskStorage(task_dir, task_dir.name).load_task_result()
        if raw:
            results.append(raw)
    union = {}
    for raw in results:
        for row in raw["findings"]:
            union[(raw["pr_number"], row["claim"])] = row
    label = {}
    unjoined = 0
    for row in jsonl_rows(run_dir(run_name) / "findings.jsonl"):
        found = union.get((row["pr_number"], row["claim"]))
        if found is None:
            unjoined += 1
            continue
        label[row["finding_id"]] = (row["pr_number"], found)

    out = {"run": run_name, "task_results": len(results), "unjoined_findings": unjoined,
           "hits": len(hit), "stage_hits": len(stage_hit), "obligations": report["counts"]["obligations"],
           "findings": report["counts"]["candidates"], "paired": report["counts"]["paired_candidates"],
           "control_per_pr": report["silent_pr_emission"]["candidates_per_control_pr"],
           "stage_control_per_pr": stage_report["silent_pr_emission"]["candidates_per_control_pr"]}

    increment, draw_gained = [], []
    for obligation in sorted(hit - stage_hit):
        stages = {label[c][1].get("stage") for c in hitters[obligation] if c in label}
        (increment if "critic" in stages else draw_gained).append(
            {"obligation": obligation, "stages": sorted(s for s in stages if s),
             "claims": [label[c][1]["claim"][:160] for c in hitters[obligation] if c in label]})
    out["increment"] = increment
    out["judge_draw_gained"] = draw_gained
    out["judge_draw_lost"] = sorted(stage_hit - hit)
    out["critic_stage_hits"] = sorted(
        o for o in hit if any(label[c][1].get("stage") == "critic" for c in hitters[o] if c in label))

    positions = Counter()
    overturn_by_concern = Counter()
    overturn_filed = Counter()
    for raw in results:
        for cell in raw.get("ledger") or []:
            positions[(cell["verdict"], cell["position"])] += 1
            if cell["position"] == "overturn":
                overturn_by_concern[cell["concern"]] += 1
                overturn_filed[str(cell.get("outcome"))] += 1
    out["positions"] = {f"{verdict}/{position}": n for (verdict, position), n in sorted(positions.items())}
    out["overturns_by_concern"] = dict(overturn_by_concern.most_common())
    out["overturn_outcomes"] = dict(overturn_filed.most_common())

    by_stage = Counter()
    critic_findings = []
    control_filings = Counter()
    for raw in results:
        for row in raw["findings"]:
            by_stage[(row.get("stage"), row.get("critic"))] += 1
            if row.get("stage") == "critic":
                critic_findings.append({"pr": raw["pr_number"], "declaration": row.get("declaration"),
                                        "concern": row.get("concern"), "verified": row.get("verification"),
                                        "claim": row["claim"][:200]})
            if raw["pr_number"] in controls:
                control_filings[(row.get("stage"), row.get("concern"))] += 1
    out["union_by_stage_and_position"] = {f"{s}/{c}": n for (s, c), n in sorted(by_stage.items(), key=str)}
    out["critic_findings"] = critic_findings
    out["control_filings"] = {f"{s}/{c}": n for (s, c), n in sorted(control_filings.items(), key=str)}
    out["refuted_at_critic_submission"] = sum(len(raw.get("refuted") or []) for raw in results)
    out["tokens_in_results"] = sum((raw.get("token_usage") or {}).get("total_tokens") or 0 for raw in results)
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(*sys.argv[1:4])))
