"""Freeze the evidence and claim state before systematic-opportunity implementation."""

import argparse
import json
from pathlib import Path
from typing import Dict, List

from .io import canonical_json_bytes, pretty_json_bytes, sha256_bytes, sha256_file, write_once


BASELINE_LOCK_VERSION = "systematic-opportunity-baseline/1"
AS_OF = "2026-07-17"
DEFAULT_OUT = Path("results/pr_review_v4/audits/systematic-opportunities-v1-baseline-preflight")


ARTIFACTS = [
    ("stable_release", "inputs/pr_review_v4/releases/dev-pilot-0.9.0/manifest.json", True),
    ("stable_run1_manifest", "results/pr_review_v4/runs/dev-pilot-0.9.0-stable-smoke3/run_manifest.json", True),
    ("stable_run1_semantic", "results/pr_review_v4/runs/dev-pilot-0.9.0-stable-smoke3/semantic-judge-v1/report.json", True),
    ("stable_run2_manifest", "results/pr_review_v4/runs/dev-pilot-0.9.0-stable-smoke3-rep2/run_manifest.json", True),
    ("stable_run2_semantic", "results/pr_review_v4/runs/dev-pilot-0.9.0-stable-smoke3-rep2/semantic-judge-v1/report.json", True),
    ("stable_run3_manifest", "results/pr_review_v4/runs/dev-pilot-0.9.0-stable-smoke3-rep3/run_manifest.json", True),
    ("stable_run3_semantic", "results/pr_review_v4/runs/dev-pilot-0.9.0-stable-smoke3-rep3/semantic-judge-v1/report.json", True),
    ("manual_agenda_verdict", "results/pr_review_v4/audits/manual-agenda-probe-0.1.1-verdict.md", True),
    ("retrieval_replication_verdict", "results/pr_review_v4/audits/dev-pilot-0.8.9-vs-0.8.11-paired-three-sample-verdict.md", True),
    ("oracle_opportunity_treatment", "inputs/pr_review_v4/treatments/oracle-opportunity-probe-0.1.0/manifest.json", True),
    ("oracle_opportunity_adjudications", "results/pr_review_v4/runs/oracle-opportunity-probe-0.1.0-manual/adjudications.jsonl", True),
    ("oracle_opportunity_semantic", "results/pr_review_v4/runs/oracle-opportunity-probe-0.1.0-manual/semantic-judge-v1/report.json", True),
    ("oracle_evidence_treatment", "inputs/pr_review_v4/treatments/oracle-evidence-probe-0.2.0/manifest.json", True),
    ("oracle_evidence_adjudications", "results/pr_review_v4/runs/oracle-evidence-probe-0.2.0/adjudications.jsonl", True),
    ("oracle_evidence_candidates", "results/pr_review_v4/runs/oracle-evidence-probe-0.2.0/candidates.jsonl", True),
    ("oracle_evidence_semantic", "results/pr_review_v4/runs/oracle-evidence-probe-0.2.0/semantic-judge-v1/report.json", True),
]


CLAIMS = [
    {
        "claim_id": "stable_core_replayable",
        "status": "proven",
        "claim": "The stable v4 smoke has immutable run accounting and semantic reports for three repetitions.",
        "evidence_roles": [
            "stable_release", "stable_run1_manifest", "stable_run1_semantic",
            "stable_run2_manifest", "stable_run2_semantic", "stable_run3_manifest",
            "stable_run3_semantic",
        ],
    },
    {
        "claim_id": "single_call_generation_is_stochastic",
        "status": "proven",
        "claim": "Identical treatment prompts recover different obligations across repetitions.",
        "evidence_roles": ["stable_run1_semantic", "stable_run2_semantic", "stable_run3_semantic"],
    },
    {
        "claim_id": "generic_specialist_split_improves_recovery",
        "status": "refuted_for_tested_design",
        "claim": "The tested generic specialist split did not improve semantic recovery and increased control pressure.",
        "evidence_roles": ["manual_agenda_verdict"],
    },
    {
        "claim_id": "lexical_context_to_ask_is_stable",
        "status": "refuted_for_tested_design",
        "claim": "The tested lexical context-to-ask retrieval policy did not produce a replicated semantic gain.",
        "evidence_roles": ["retrieval_replication_verdict"],
    },
    {
        "claim_id": "canonical_api_application_can_recover_target",
        "status": "proven_diagnostic",
        "claim": "Given the exact canonical API opportunity, adjudication recovered an issue and resolution match.",
        "evidence_roles": [
            "oracle_opportunity_treatment", "oracle_opportunity_adjudications",
            "oracle_opportunity_semantic",
        ],
    },
    {
        "claim_id": "naming_and_wrapper_evidence_can_recover_targets",
        "status": "pending_semantic_confirmation",
        "claim": "Oracle naming and wrapper-composition evidence produced two requests whose issue and resolution coverage is fixed by the semantic report.",
        "evidence_roles": [
            "oracle_evidence_treatment", "oracle_evidence_adjudications",
            "oracle_evidence_candidates", "oracle_evidence_semantic",
        ],
    },
    {
        "claim_id": "compilation_establishes_review_worthiness",
        "status": "refuted_for_tested_cases",
        "claim": "Compiling proof-compression and small syntax alternatives remained optional rather than request-worthy.",
        "evidence_roles": ["oracle_evidence_adjudications"],
    },
    {
        "claim_id": "automatic_source_recovery",
        "status": "unproven",
        "claim": "Production retrieval has not yet automatically recovered the oracle API, naming population, or wrapper sources.",
        "evidence_roles": [],
    },
]


def _oracle_evidence_confirmation(path: Path) -> Dict:
    if not path.is_file():
        return {"status": "pending", "issue_hits": 0, "resolution_hits": 0}
    report = json.loads(path.read_text())
    if report.get("schema_version") != "v4-semantic-report1":
        return {
            "status": "invalid_report",
            "issue_hits": 0,
            "resolution_hits": 0,
            "schema_version": report.get("schema_version"),
        }
    obligations = report.get("per_obligation", [])
    issue_hits = sum(bool(item.get("issue_hit")) for item in obligations)
    resolution_hits = sum(bool(item.get("resolution_hit")) for item in obligations)
    counts = report.get("counts", {})
    complete = counts.get("candidates") == 2 and counts.get("paired_candidates") == 2
    return {
        "status": "complete" if complete else "invalid_report",
        "issue_hits": issue_hits,
        "resolution_hits": resolution_hits,
        "schema_version": report.get("schema_version"),
        "judge_version": report.get("judge_version"),
    }


def inspect_baseline(root: Path = Path(".")) -> Dict:
    rows: List[Dict] = []
    for role, relative, required in ARTIFACTS:
        path = root / relative
        rows.append({
            "role": role,
            "path": relative,
            "required": required,
            "status": "available" if path.is_file() else "missing",
            "sha256": sha256_file(path) if path.is_file() else None,
        })
    available = {item["role"] for item in rows if item["status"] == "available"}
    missing_required = [item["role"] for item in rows if item["required"] and item["status"] == "missing"]
    semantic_confirmation = _oracle_evidence_confirmation(
        root / "results/pr_review_v4/runs/oracle-evidence-probe-0.2.0/semantic-judge-v1/report.json"
    )
    claims = []
    for claim in CLAIMS:
        unresolved = sorted(set(claim["evidence_roles"]) - available)
        row = {**claim, "unresolved_evidence_roles": unresolved}
        if row["claim_id"] == "naming_and_wrapper_evidence_can_recover_targets":
            row["observed_semantic_result"] = {
                "issue_hits": semantic_confirmation["issue_hits"],
                "resolution_hits": semantic_confirmation["resolution_hits"],
            }
            if semantic_confirmation["status"] == "complete":
                row["status"] = (
                    "proven_diagnostic_full_resolution"
                    if semantic_confirmation["issue_hits"] == 2
                    and semantic_confirmation["resolution_hits"] == 2
                    else "proven_diagnostic_partial_resolution"
                )
            elif semantic_confirmation["status"] == "invalid_report":
                row["status"] = "pending_invalid_semantic_report"
        if unresolved and row["status"] not in {"unproven", "pending_semantic_confirmation"}:
            row["status"] = "pending_missing_evidence"
        claims.append(row)
    if missing_required:
        gate_status = "pending"
    elif semantic_confirmation["status"] == "complete":
        gate_status = "complete"
    else:
        gate_status = "failed"
    lock_source = {
        "schema_version": "systematic-baseline-lock1",
        "version": BASELINE_LOCK_VERSION,
        "as_of": AS_OF,
        "gate_status": gate_status,
        "missing_required_roles": missing_required,
        "oracle_evidence_semantic_confirmation": semantic_confirmation,
        "artifacts": rows,
    }
    lock = {**lock_source, "source_sha256": sha256_bytes(canonical_json_bytes(lock_source))}
    claim_source = {
        "schema_version": "systematic-claim-matrix1",
        "version": BASELINE_LOCK_VERSION,
        "as_of": AS_OF,
        "claims": claims,
    }
    matrix = {**claim_source, "source_sha256": sha256_bytes(canonical_json_bytes(claim_source))}
    return {"lock": lock, "claims": matrix}


def write_baseline(out_dir: Path, allow_pending: bool = False) -> Dict:
    result = inspect_baseline()
    if result["lock"]["gate_status"] != "complete" and not allow_pending:
        missing = result["lock"]["missing_required_roles"]
        confirmation = result["lock"]["oracle_evidence_semantic_confirmation"]
        raise ValueError(
            f"baseline evidence gate is {result['lock']['gate_status']}: "
            f"missing={missing} semantic_confirmation={confirmation}"
        )
    write_once(out_dir / "baseline_lock.json", pretty_json_bytes(result["lock"]))
    write_once(out_dir / "claim_matrix.json", pretty_json_bytes(result["claims"]))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Freeze systematic-opportunity baseline evidence")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--allow-pending", action="store_true")
    args = parser.parse_args()
    result = write_baseline(args.out_dir, args.allow_pending)
    print(json.dumps({
        "out_dir": str(args.out_dir),
        "gate_status": result["lock"]["gate_status"],
        "missing_required_roles": result["lock"]["missing_required_roles"],
        "claims": len(result["claims"]["claims"]),
    }, indent=2))


if __name__ == "__main__":
    main()
