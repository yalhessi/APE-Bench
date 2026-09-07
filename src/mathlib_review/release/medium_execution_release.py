"""Fold a deterministic executor run over medium into a child release.

The medium release (`dev-medium-0.1.0`) carries change graphs, work units and rendered
prompts, but no `opportunities.jsonl` — so the downstream stages that consume systematic
opportunities (candidate linking, selection, adjudication) had nothing to read at medium
tier. This builds the child release that closes that gap.

It composes rather than computes: the executor already wrote the artifacts, and this copies
them into a sealed release with a manifest that names the parent, the treatment, and the
executor version. Nothing is recomputed, so the release cannot disagree with the run it
came from.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from src.mathlib_review.io import load_jsonl, pretty_json_bytes, sha256_file, write_once
from src.mathlib_review.opportunities.executor import EXECUTOR_VERSION
from src.mathlib_review.paths import assert_repo_root
from src.mathlib_review.release.releases import ArtifactSpec, build_release, parent_release_ref
from src.mathlib_review.schema import (
    InvestigationRecord,
    OperatorRun,
    OpportunityEvidenceArtifact,
    ReviewOpportunity,
)


VERSION = "medium-execution-release/1"
DEFAULT_PARENT = Path("inputs/pr_review_v4/releases/dev-medium-0.1.0")
DEFAULT_TREATMENT = Path("inputs/pr_review_v4/treatments/systematic-opportunities-v3-medium")
DEFAULT_RUN = Path("results/pr_review_v4/audits/phase10-medium-executor-v5")
DEFAULT_OUT = Path("inputs/pr_review_v4/releases/dev-medium-0.2.1-systematic")

#: A superseded release is preserved, never rebuilt in place. 0.2.0 sealed the executor `/3`
#: run, whose `baseline_failure` output restated one file-level compile failure once per
#: declaration in the file; 0.2.1 seals the `/4` run that reports it once. Both releases and
#: both runs remain on disk so each manifest's provenance stays resolvable.
SUPERSEDES = Path("inputs/pr_review_v4/releases/dev-medium-0.2.0-systematic")

#: Executor output file -> (release-relative path, schema, manifest role).
_ARTIFACTS = (
    ("opportunities", "derived/opportunities.jsonl",
     "review-opportunity1", "automatic_review_opportunities", ReviewOpportunity),
    ("opportunity_evidence", "derived/opportunity_evidence.jsonl",
     "opportunity-evidence-artifact1", "opportunity_evidence", OpportunityEvidenceArtifact),
    ("operator_runs", "derived/operator_runs.jsonl",
     "operator-run1", "operator_runs", OperatorRun),
    ("investigation_records", "derived/investigation_records.jsonl",
     "investigation-record1", "investigation_records", InvestigationRecord),
)


def build_execution_release(
    parent: Path = DEFAULT_PARENT,
    treatment: Path = DEFAULT_TREATMENT,
    run: Path = DEFAULT_RUN,
    out: Path = DEFAULT_OUT,
    supersedes: Optional[Path] = SUPERSEDES,
) -> Dict:
    """Seal an executor run as a child release of the medium benchmark release."""

    assert_repo_root()
    run_report = json.loads((run / "report.json").read_text(encoding="utf-8"))
    if run_report["executor_version"] != EXECUTOR_VERSION:
        raise ValueError(
            f"run was produced by {run_report['executor_version']}, "
            f"but the current executor is {EXECUTOR_VERSION}"
        )
    failed = run_report["terminal_stages"].get("execution_failed", 0)
    if failed:
        # A crashed runner yields no opportunity but also no `checked_no_opportunity`, so a
        # release built over one would silently under-report the arm's coverage.
        raise ValueError(f"refusing to seal a run with {failed} failed tasks: {run}")

    specs = [
        ArtifactSpec(
            rel_path=rel_path,
            rows=load_jsonl(run / f"{name}.jsonl", model),
            schema_version=schema,
            role=role,
        )
        for name, rel_path, schema, role, model in _ARTIFACTS
    ]
    parent_manifest = json.loads((parent / "manifest.json").read_text(encoding="utf-8"))

    build_release(
        out,
        dataset_id=parent_manifest["dataset_id"],
        release="0.2.1-medium-systematic",
        pr_numbers=parent_manifest["pr_numbers"],
        corpus_cutoff_policy=parent_manifest["corpus_cutoff_policy"],
        generator_versions={
            **parent_manifest["generator_versions"],
            "systematic_execution": EXECUTOR_VERSION,
            "execution_release": VERSION,
        },
        created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        sources=[
            parent_release_ref(parent),
            parent_release_ref(treatment, role="treatment"),
            # Recorded as provenance, not prose: the manifest itself names what this release
            # replaces, so the supersession survives independently of any README.
            *(
                [parent_release_ref(supersedes, role="supersedes")]
                if supersedes is not None and (supersedes / "manifest.json").is_file()
                else []
            ),
        ],
        derived_artifacts=specs,
        split=parent_manifest.get("split", "development"),
    )
    report = {
        "schema_version": "medium-execution-release-report1",
        "version": VERSION,
        "executor_version": EXECUTOR_VERSION,
        "parent": str(parent),
        "treatment": str(treatment),
        "run": str(run),
        "supersedes": str(supersedes) if supersedes is not None else None,
        "counts": {spec.rel_path: spec.records for spec in specs},
        "manifest_sha256": sha256_file(out / "manifest.json"),
    }
    write_once(out / "execution_report.json", pretty_json_bytes(report))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seal a deterministic executor run as a medium child release"
    )
    parser.add_argument("--parent", type=Path, default=DEFAULT_PARENT)
    parser.add_argument("--treatment", type=Path, default=DEFAULT_TREATMENT)
    parser.add_argument("--run", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    print(json.dumps(
        build_execution_release(args.parent, args.treatment, args.run, args.out), indent=2
    ))


if __name__ == "__main__":
    main()
