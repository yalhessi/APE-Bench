"""Run semantic judgment as registered tasks through a top-level orchestrator.

The judge reads gold, so it gets its **own** orchestrator run rather than being nested
inside a reviewer task — the reviewer's run tree must stay gold-free.

The pair records built here carry exactly the fields the script's `_pair_key` hashes, so
a pair's framework identity and the script's cache key denote the same unit of work. That
is what makes resume behave as the cache and lets `R0` compare the two arms
verdict-for-verdict.

Usage (see `configs/pr_review_v4_judge.yaml`):
    python -m src.datasets.pr_review_v4.judge_runner --config configs/pr_review_v4_judge.yaml
"""

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from ape.orchestration import TaskOrchestrator
from ape.tasks.base import create_task_from_data
from ape.utils import deep_merge, load_yaml, parse_cli_args
from ape.utils.logging import create_logger

from .io import canonical_json_bytes, jsonl_bytes, load_jsonl, pretty_json_bytes, sha256_bytes, write_once
from .paths import assert_repo_root
from .schema import (
    CandidateClaim,
    ChangeGraph,
    InterventionView,
    JudgmentNode,
    ReviewFinding,
    SemanticMatch,
)
from .judge_protocol import code_block as target_code_block
from .judge_protocol import render_prompt


def render_prompt_for(record: Dict) -> str:
    """Render exactly the prompt the task will build, for sealing before execution."""

    return render_prompt(
        gold_code=record["target_code"],
        gold_concerns=record["gold_concerns"],
        gold_action=record["gold_action"],
        gold_claim=record["gold_claim"],
        resolution_criteria=record["resolution_criteria"],
        primary_subject=record["primary_subject"],
        candidate_family=record["candidate_family"],
        candidate_claim=record["candidate_claim"],
        requested_change=record["requested_change"],
        suggested_fix=record["suggested_fix"],
        proposed_edit=record["proposed_edit"],
        candidate_code=record.get("candidate_code", ""),
        maintainer_comment=record.get("maintainer_comment", ""),
        sibling_claims=tuple(record.get("sibling_claims", ())),
    )
from .judge_protocol import ContextProfile, judge_identity
from .obligation_context import load_context
from .schema import PRRelation, SemanticPair
from .semantic_judge import (
    JUDGE_VERSION,
    build_null_pairs,
    build_pairs,
    seal_pair,
    semantic_report,
)


class JudgeDatasetConfig(BaseModel):
    release: Path
    candidates: Path
    #: Final-output evaluation must judge the text that survives synthesis.  `candidate`
    #: remains available for legacy/R0 runs; production conditions use `finding`.
    input_kind: Literal["candidate", "finding"] = "candidate"
    out_dir: Path
    run_name: str = "pr_review_v4_judge"
    dry_run: bool = False
    #: Restrict to specific obligations/candidates when replaying a subset for R0.
    obligation_ids: List[str] = Field(default_factory=list)
    pr_numbers: List[int] = Field(default_factory=list)
    #: `anchor` only by default. Widening can only raise recall, so it is a deliberate,
    #: recorded choice rather than something a config silently inherits.
    pairing_tiers: List[str] = Field(default_factory=lambda: ["anchor"])
    #: Same-PR near negatives, judged alongside and excluded from every recall.
    null_pairs_per_obligation: int = 0
    #: PRs where maintainers asked for nothing, for the silent-PR emission count.
    control_pr_numbers: List[int] = Field(default_factory=list)
    #: Independent context ablations. Off by default: each changes what the judge is shown,
    #: and therefore its identity, so enabling one is a deliberate, recorded experiment.
    include_maintainer_comment: bool = False
    include_sibling_claims: bool = False


def candidate_from_finding(finding: ReviewFinding) -> CandidateClaim:
    """Project final finding text into the judge's established comparison interface.

    The synthetic work-unit identifier is deliberately not lineage: all real lineage stays
    in the source `ReviewFinding`.  The judge only needs a stable identifier, anchors and
    the final claim/transformation.  Most importantly, both the ID and source hash denote
    the *finding*, so a verdict on discarded pre-merge wording cannot be joined here.
    """

    return CandidateClaim(
        candidate_id=finding.finding_id,
        producer=(
            "deterministic"
            if finding.sources and all(item.arm == "deterministic" for item in finding.sources)
            else "model"
        ),
        work_unit_id=f"final-finding:{finding.finding_id}",
        episode_id=finding.episode_id,
        pr_number=finding.pr_number,
        change_ids=list(finding.change_ids),
        primary_change_id=finding.primary_change_id,
        primary_subject=finding.primary_subject,
        requested_change=finding.requested_change,
        concern_family=finding.concern_family,
        issue_kind=finding.issue_kind,
        spec_id=next(
            (item.spec_id for item in finding.sources if item.spec_id is not None), None
        ),
        concern_label=finding.concern_family,
        severity=finding.severity,
        claim=finding.claim,
        suggested_fix=finding.requested_change,
        proposed_edit=finding.proposed_edit,
        evidence_requests=[],
        source_sha256=finding.source_sha256,
    )


def load_judge_candidates(dataset: JudgeDatasetConfig) -> List[CandidateClaim]:
    if dataset.input_kind == "candidate":
        return load_jsonl(dataset.candidates, CandidateClaim)
    return [
        candidate_from_finding(item)
        for item in load_jsonl(dataset.candidates, ReviewFinding)
    ]


def publication_summary(findings: List[ReviewFinding], pre: Dict, post: Dict) -> Dict:
    """The four requested headline counts, with their denominator and exact population."""

    def hit_counts(item: Dict) -> Dict[str, int]:
        if not item.get("scored"):
            raise ValueError("cannot report publication metrics from an unscored judge run")
        counts = item["obligation_status_counts"]
        return {
            "issue_hits": counts["issue"]["hit"],
            "resolution_hits": counts["resolution"]["hit"],
        }

    published_ids = {item.finding_id for item in findings if item.admission == "published"}
    return {
        "schema_version": "v4-publication-report1",
        "obligations": pre["counts"]["obligations"],
        "definition": (
            "pre_publication judges every merged ReviewFinding in its final serialized "
            "wording; post_publication is the admission=published subset of those same "
            "findings and verdicts"
        ),
        "findings": {
            "pre_publication": len(findings),
            "post_publication": len(published_ids),
        },
        "pre_publication": hit_counts(pre),
        "post_publication": hit_counts(post),
    }


def load_run(config_path: Path, overrides: Optional[Dict[str, Any]] = None):
    from ape.scaffolds.ape_agent.config import ApeAgentConfig

    raw = load_yaml(config_path)
    if overrides:
        raw = deep_merge(raw, overrides)
    dataset = JudgeDatasetConfig.model_validate(raw.pop("dataset"))
    task_overrides = raw.pop("task_config", {}) or {}
    raw.setdefault("scaffold_type", "ape_agent")
    scaffold = ApeAgentConfig.model_validate(raw)
    scaffold.task_config_overrides = task_overrides
    return dataset, scaffold, task_overrides


def _proposed_edit_text(candidate) -> str:
    edit = getattr(candidate, "proposed_edit", None)
    if edit is None:
        return "(none)"
    return (
        f"{edit.declaration_name or edit.path}:\n{edit.new_declaration}"
        if getattr(edit, "new_declaration", None) else "(none)"
    )


def pair_task_data(pair: Dict, model: str, rubric: str = JUDGE_VERSION,
                   targets_by_change_id: Optional[Dict] = None,
                   context: Optional[Dict] = None,
                   *, include_maintainer_comment: bool = False,
                   include_sibling_claims: bool = False) -> Dict:
    """Project one judged pair into a task record.

    The record carries the reviewed code, the gold action and the candidate's proposed
    edit, so the task needs no change-graph access at run time.

    **Widened pairs get two code blocks.** `target_code` was rendered from the pair's
    *overlap*, which at any tier but `anchor` is empty — so widening alone would have put
    the judge back in front of "(reviewed code unavailable for this target)", the exact
    defect the protocol exists to prevent, on precisely the new tier. Gold code comes from
    the obligation's own targets; the candidate's targets are rendered separately when they
    differ.
    """

    judgment, obligation, candidate = pair["judgment"], pair["obligation"], pair["candidate"]
    targets = targets_by_change_id or {}
    tier = pair.get("pairing_tier", "anchor")
    gold_change_ids = pair["overlap_change_ids"] or sorted(obligation.change_ids)
    candidate_code = (
        target_code_block(sorted(candidate.change_ids), targets) if tier != "anchor" else ""
    )
    row = (context or {}).get(obligation.obligation_id, {})
    return {
        "target_code": target_code_block(gold_change_ids, targets),
        "candidate_code": candidate_code,
        "maintainer_comment": (
            row.get("maintainer_comment", "") if include_maintainer_comment else ""
        ),
        "sibling_claims": (
            list(row.get("sibling_claims", ())) if include_sibling_claims else []
        ),
        "pairing_tier": tier,
        "candidate_change_ids": sorted(candidate.change_ids),
        "gold_action": f"{judgment.action.kind} {judgment.action.object}".strip(),
        "proposed_edit": _proposed_edit_text(candidate),
        "task_type": "lean_pr_review_v4_semantic_judgment",
        "task_id": f"judge_{candidate.candidate_id[:16]}_{obligation.obligation_id[-16:]}",
        "candidate_id": candidate.candidate_id,
        "obligation_id": obligation.obligation_id,
        "candidate_source_sha256": candidate.source_sha256,
        "obligation_source_sha256": obligation.source_sha256,
        "judge_version": rubric,
        "gold_concerns": ", ".join(judgment.concern_labels) or "(none)",
        "gold_claim": obligation.claim,
        "resolution_criteria": (
            obligation.resolution_criteria or "The requested transformation is made."
        ),
        "primary_subject": candidate.primary_subject or "(unspecified)",
        "candidate_family": candidate.concern_family,
        "candidate_claim": candidate.claim,
        "requested_change": candidate.requested_change or candidate.suggested_fix or "(none)",
        "suggested_fix": candidate.suggested_fix or "(none)",
        "pr_number": judgment.pr_number,
        "overlap_change_ids": pair["overlap_change_ids"],
    }


def script_cache_key(pair: Dict, model: str, rubric: str = JUDGE_VERSION) -> str:
    """The key the script form would use for this pair — the R0 join column.

    The rubric is part of the key, so v8 verdicts can never be joined against v7.1 ones.
    """

    return sha256_bytes(canonical_json_bytes({
        "candidate_source_sha256": pair["candidate"].source_sha256,
        "obligation_source_sha256": pair["obligation"].source_sha256,
        "model": model, "judge_version": rubric,
    }))


def _match_from_result(raw: Dict, model: str, source_hashes: Dict,
                       rubric: str = JUDGE_VERSION) -> SemanticMatch:
    """Project one task result into a SemanticMatch.

    The judged content hashes live on the task *data*, not the result — the result
    carries only the verdict — so they are looked up from the pair records by
    (candidate, obligation). Keeping them out of the result is deliberate: the result
    should not be able to disagree with the record about what was judged.
    """

    key = (raw["candidate_id"], raw["obligation_id"])
    candidate_sha, obligation_sha, pair_id, tier, role = source_hashes[key]
    payload = {
        "candidate_id": raw["candidate_id"],
        "obligation_id": raw["obligation_id"],
        "issue_match": bool(raw.get("issue_match")),
        "resolution_match": bool(raw.get("resolution_match")) and bool(raw.get("issue_match")),
        "abstain": bool(raw.get("abstain")),
        "reason": str(raw.get("reason") or ""),
        "judge_model": model,
        "judge_version": rubric,
        "candidate_source_sha256": candidate_sha,
        "obligation_source_sha256": obligation_sha,
        "pair_id": pair_id,
        "pairing_tier": tier,
        "role": role,
    }
    digest = sha256_bytes(canonical_json_bytes(payload))
    return SemanticMatch(match_id=f"semantic-match:{digest[:24]}", source_sha256=digest, **payload)


def load_targets(release: Path) -> Dict:
    return {
        target.change_id: target
        for graph in load_jsonl(release / "derived/change_graphs.jsonl", ChangeGraph)
        for target in graph.targets
    }


def collect_pairs(dataset: JudgeDatasetConfig) -> List[Dict]:
    release = dataset.release
    judgments = load_jsonl(release / "gold/judgments.jsonl", JudgmentNode)
    views = load_jsonl(release / "gold/intervention_views.jsonl", InterventionView)
    candidates = load_judge_candidates(dataset)
    relations_path = release / "derived/pr_relations.jsonl"
    relations = (
        load_jsonl(relations_path, PRRelation) if relations_path.is_file() else []
    )
    pairs = build_pairs(
        judgments, views, candidates,
        scoped_obligation_ids=dataset.obligation_ids or None,
        tiers=tuple(dataset.pairing_tiers),
        targets_by_change_id=load_targets(release),
        relations=relations,
    )
    if dataset.pr_numbers:
        wanted = set(dataset.pr_numbers)
        pairs = [item for item in pairs if item["judgment"].pr_number in wanted]
    if dataset.null_pairs_per_obligation:
        pairs = pairs + build_null_pairs(
            pairs, candidates, dataset.null_pairs_per_obligation
        )
    return pairs


async def run(dataset: JudgeDatasetConfig, scaffold, task_overrides, logger):
    assert_repo_root()
    model = scaffold.llm_config.model_name
    execution = getattr(scaffold, "execution", None)
    llm = scaffold.llm_config
    identity = judge_identity(
        model=model,
        sample_count=getattr(execution, "sample_count", 1),
        max_tokens=getattr(llm, "max_tokens", None),
        thinking_budget_tokens=getattr(llm, "thinking_budget_tokens", None),
        temperature=getattr(llm, "temperature", None),
        aggregation_policy="majority_issue_then_resolution_among_issue_matching",
        context_profile=ContextProfile(
            candidate_code=len(dataset.pairing_tiers) > 1
            or "anchor" not in dataset.pairing_tiers,
            maintainer_comment=dataset.include_maintainer_comment,
            sibling_obligations=dataset.include_sibling_claims,
        ),
    )
    pairs = collect_pairs(dataset)
    targets = load_targets(dataset.release)
    context = (
        load_context()
        if (dataset.include_maintainer_comment or dataset.include_sibling_claims) else {}
    )
    records = [
        pair_task_data(
            pair, model, JUDGE_VERSION, targets, context,
            include_maintainer_comment=dataset.include_maintainer_comment,
            include_sibling_claims=dataset.include_sibling_claims,
        )
        for pair in pairs
    ]

    # Seal what will be asked, before asking it. The prompt hash is inside the pair, so a
    # pair whose prompt lost its code section can never be mistaken for one that kept it.
    sealed = [
        seal_pair(
            pair,
            judge_identity=identity,
            prompt=render_prompt_for(record),
            gold_code=record["target_code"],
            candidate_code=record.get("candidate_code", ""),
        )
        for pair, record in zip(pairs, records)
    ]
    for pair, sealed_pair in zip(pairs, sealed):
        pair["pair_id"] = sealed_pair.pair_id

    logger.info(
        "Semantic pairs to judge: %d observed + %d null (model=%s, rubric=%s, tiers=%s)",
        sum(item.role == "observed" for item in sealed),
        sum(item.role == "null" for item in sealed),
        model, JUDGE_VERSION, ",".join(dataset.pairing_tiers),
    )

    if dataset.dry_run:
        for record, sealed_pair in zip(records, sealed):
            logger.info(
                "%s tier=%s role=%s gold=%dch cand=%dch pair=%s",
                record["task_id"], sealed_pair.pairing_tier, sealed_pair.role,
                len(record.get("target_code", "")), len(record.get("candidate_code", "")),
                sealed_pair.pair_id[-12:],
            )
        missing_code = [
            item.pair_id for item, record in zip(sealed, records)
            if "reviewed code unavailable" in record["target_code"]
        ]
        if missing_code:
            raise ValueError(
                f"{len(missing_code)} pairs would be judged without their reviewed code; "
                "this is the defect the judge protocol exists to prevent"
            )
        return None

    tasks = [
        create_task_from_data(record, scaffold, task_config_overrides=task_overrides)
        for record in records
    ]
    orchestrator = TaskOrchestrator(
        config=scaffold, orchestrator_id=dataset.run_name, logger=logger
    )
    results = await orchestrator.run(tasks)

    raws = [
        item.model_dump(mode="json") if hasattr(item, "model_dump") else item
        for item in results.task_results
    ]
    source_hashes = {
        (pair["candidate"].candidate_id, pair["obligation"].obligation_id): (
            pair["candidate"].source_sha256, pair["obligation"].source_sha256,
            pair["pair_id"], pair.get("pairing_tier", "anchor"), pair.get("role", "observed"),
        )
        for pair in pairs
    }
    matches = [
        _match_from_result(raw, model, source_hashes, JUDGE_VERSION)
        for raw in raws if raw.get("candidate_id")
    ]

    dataset.out_dir.mkdir(parents=True, exist_ok=True)
    write_once(dataset.out_dir / "semantic_pairs.jsonl", jsonl_bytes(sealed))
    write_once(dataset.out_dir / "semantic_matches.jsonl", jsonl_bytes(matches))
    judgments = load_jsonl(dataset.release / "gold/judgments.jsonl", JudgmentNode)
    views = load_jsonl(dataset.release / "gold/intervention_views.jsonl", InterventionView)
    candidates = load_judge_candidates(dataset)
    report = semantic_report(
        judgments, views, candidates, matches,
        scoped_obligation_ids=dataset.obligation_ids or None,
        planned_pairs=sealed,
        control_pr_numbers=dataset.control_pr_numbers,
        null_pairs_requested=(
            dataset.null_pairs_per_obligation
            * len({item.obligation_id for item in sealed if item.role == "observed"})
        ),
    )
    votes = []
    for raw in raws:
        if not raw.get("candidate_id"):
            continue
        metrics = raw.get("custom_metrics") or {}
        # `custom_metrics` is a float map, so booleans arrive as 1.0/0.0; normalize here
        # rather than leaving every consumer to guess the type.
        votes.append({
            "candidate_id": raw["candidate_id"],
            "obligation_id": raw["obligation_id"],
            "issue_votes": int(metrics.get("issue_votes", 0)),
            "resolution_votes": int(metrics.get("resolution_votes", 0)),
            "resolution_denominator": int(metrics.get("resolution_denominator", 0)),
            "abstain_votes": int(metrics.get("abstain_votes", 0)),
            "samples_requested": int(metrics.get("samples_requested", 0)),
            "samples_succeeded": int(metrics.get("samples_succeeded", 0)),
            "issue_unanimous": bool(metrics.get("issue_unanimous", 0)),
            "resolution_unanimous": bool(metrics.get("resolution_unanimous", 0)),
        })
    write_once(dataset.out_dir / "semantic_report.json", pretty_json_bytes({
        **report, "arm": "registered_task", "judge_identity": identity,
        "pairing_tiers": list(dataset.pairing_tiers),
    }))
    if dataset.input_kind == "finding":
        findings = load_jsonl(dataset.candidates, ReviewFinding)
        published_ids = {
            item.finding_id for item in findings if item.admission == "published"
        }
        published_candidates = [
            item for item in candidates if item.candidate_id in published_ids
        ]
        published_matches = [
            item for item in matches if item.candidate_id in published_ids
        ]
        published_pairs = [
            item for item in sealed if item.candidate_id in published_ids
        ]
        post_report = semantic_report(
            judgments, views, published_candidates, published_matches,
            scoped_obligation_ids=dataset.obligation_ids or None,
            planned_pairs=published_pairs,
            control_pr_numbers=dataset.control_pr_numbers,
            null_pairs_requested=None,
        )

        write_once(
            dataset.out_dir / "publication_report.json",
            pretty_json_bytes(publication_summary(findings, report, post_report)),
        )
    write_once(dataset.out_dir / "sample_votes.jsonl", jsonl_bytes(votes))
    logger.info("Wrote %d matches to %s", len(matches), dataset.out_dir)
    return dataset.out_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Judge candidate/obligation pairs as tasks")
    parser.add_argument("--config", type=Path, required=True)
    args, rest = parser.parse_known_args()
    dataset, scaffold, task_overrides = load_run(args.config, parse_cli_args(rest))
    out = asyncio.run(run(dataset, scaffold, task_overrides, create_logger()))
    if out:
        print(out)


if __name__ == "__main__":
    main()
