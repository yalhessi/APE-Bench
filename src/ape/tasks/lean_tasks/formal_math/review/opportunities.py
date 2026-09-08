"""APE task for adjudicating frozen PR-review opportunity records."""

import hashlib
import json
from typing import Annotated, Any, Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field

from ape.tasks.base import register_task
from ape.tasks.lean_tasks.formal_math.review.base import (
    BasePRReviewConfig,
    BasePRReviewData,
    BasePRReviewResult,
    BasePRReviewTask,
)

from .candidates import CandidateSubmission, normalize_candidate_edit


class LeanPRReviewV4OpportunityConfig(BasePRReviewConfig):
    finding_budget: int = 20


class LeanPRReviewV4OpportunityData(BasePRReviewData):
    task_type: str = "lean_pr_review_v4_opportunity_adjudication"
    work_unit_id: str
    episode_id: str
    change_ids: List[str]
    entity_ids_by_change: Dict[str, List[str]]
    primary_subjects_by_change: Dict[str, str]
    opportunity_ids: List[str]
    evidence_ids_by_opportunity: Dict[str, List[str]]
    change_ids_by_opportunity: Dict[str, List[str]]
    verification_required_opportunity_ids: List[str] = Field(default_factory=list)
    rendered_system_prompt: str
    rendered_user_prompt: str
    rendered_prompt_sha256: str


class LeanPRReviewV4OpportunityResult(BasePRReviewResult):
    work_unit_id: str
    rendered_prompt_sha256: str
    adjudications: List[Dict[str, Any]] = Field(default_factory=list)
    candidates: List[Dict[str, Any]] = Field(default_factory=list)
    verification_artifacts: List[Dict[str, Any]] = Field(default_factory=list)


class OpportunitySubmission(BaseModel):
    model_config = ConfigDict(extra="forbid")
    opportunity_id: str
    disposition: Literal["request", "no_request", "inconclusive"]
    validity: Literal["valid", "invalid", "uncertain"]
    norm_strength: Literal[
        "required", "canonical", "conventional", "common", "preference", "unsupported", "uncertain"
    ]
    review_worthiness: Literal["blocking", "advisory", "not_worth_mentioning", "uncertain"]
    evidence_ids: List[str]
    rationale: str
    candidate: Optional[CandidateSubmission] = None


def build_verification_artifact(
    opportunity_id: str,
    edit: Dict[str, Any],
    source_evidence_ids: List[str],
    snapshot_sha: str,
) -> Dict[str, Any]:
    canonical_edit = json.dumps(edit, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    edit_sha = hashlib.sha256(canonical_edit.encode()).hexdigest()
    identity = {
        "opportunity_id": opportunity_id,
        "kind": "lean_compile",
        "success": True,
        # Keep the source lineage immutable when the decision later cites this artifact.
        "source_evidence_artifact_ids": list(source_evidence_ids),
        "edit_sha256": edit_sha,
        "content": "Lean successfully recompiled the reviewed file with the submitted edit.",
        "snapshot_sha": snapshot_sha,
    }
    encoded = json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(encoded.encode()).hexdigest()
    return {
        "schema_version": "adjudication-verification-artifact1",
        "artifact_id": f"adjudication-verification:{digest[:24]}",
        **identity,
        "source_sha256": digest,
    }


class LeanPRReviewV4OpportunityTask(BasePRReviewTask):
    task_type = "lean_pr_review_v4_opportunity_adjudication"
    data_class = LeanPRReviewV4OpportunityData
    task_config_class = LeanPRReviewV4OpportunityConfig
    task_result_class = LeanPRReviewV4OpportunityResult

    def _get_prompts(self, version: str) -> Tuple[str, str]:
        return self.data.rendered_system_prompt, self.data.rendered_user_prompt

    async def create_system_prompt(self) -> str:
        return self.data.rendered_system_prompt

    async def create_user_prompt(self) -> str:
        return self.data.rendered_user_prompt

    def _validate_candidate(self, candidate: Dict[str, Any], allowed: set[str]) -> List[str]:
        allowed_by_suffix = {item.removeprefix("change:"): item for item in allowed}
        change_ids = [allowed_by_suffix.get(item, item) for item in candidate.get("change_ids") or []]
        candidate["change_ids"] = change_ids
        primary_change_id = allowed_by_suffix.get(
            candidate.get("primary_change_id"), candidate.get("primary_change_id")
        )
        candidate["primary_change_id"] = primary_change_id
        problems = []
        if not change_ids:
            problems.append("change_ids is empty")
        elif not set(change_ids).issubset(allowed):
            problems.append(f"unknown change_ids={sorted(set(change_ids) - allowed)}")
        if primary_change_id not in change_ids:
            problems.append("primary_change_id must be one of change_ids")
        expected_subject = self.data.primary_subjects_by_change.get(primary_change_id)
        if candidate.get("primary_subject") != expected_subject:
            problems.append(f"primary_subject must equal {expected_subject!r}")
        allowed_entities = set(self.data.entity_ids_by_change.get(primary_change_id, []))
        primary_entity_id = candidate.get("primary_entity_id")
        if allowed_entities and primary_entity_id not in allowed_entities:
            problems.append("primary_entity_id is not attached to primary_change_id")
        if not allowed_entities and primary_entity_id is not None:
            problems.append("primary_entity_id must be null for a target without entities")
        if not str(candidate.get("claim") or "").strip():
            problems.append("claim is empty")
        if not str(candidate.get("requested_change") or "").strip():
            problems.append("requested_change is empty")
        normalize_candidate_edit(candidate, self.data.changed_files, problems)
        if expected_subject and "/" not in expected_subject:
            short_subject = expected_subject.rsplit(".", 1)[-1]
            grounded = f"{candidate.get('claim', '')} {candidate.get('requested_change', '')}"
            if short_subject not in grounded:
                problems.append(f"claim/requested_change must name {short_subject!r}")
        return problems

    async def _verify_candidate_edit(
        self, opportunity_id: str, candidate: Dict[str, Any], source_evidence_ids: List[str]
    ) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
        edit = candidate.get("proposed_edit") or {}
        has_edit = bool(
            edit.get("new_declaration")
            or edit.get("replacement")
        )
        if not has_edit:
            return None, None
        code, error = self._edited_file_code(
            edit.get("path") or "",
            edit.get("line_start"),
            edit.get("line_end"),
            edit.get("replacement"),
            declaration_name=edit.get("declaration_name"),
            new_declaration=edit.get("new_declaration"),
        )
        if code is None:
            return None, error
        from ape.toolkits.execute.lean.tools import LeanVerifyToolsProvider

        lean_tool = LeanVerifyToolsProvider(task=self, config=self.config, logger=self.logger)
        try:
            result = await lean_tool.execute(code=code, max_messages=20)
        except Exception as exc:  # noqa: BLE001
            return None, f"verification raised: {exc}"
        if not result.get("success"):
            messages = result.get("errors") or []
            detail = "; ".join(str(item.get("data") or item) for item in messages[:5])
            return None, detail or str(result.get("error") or "Lean verification failed")

        return build_verification_artifact(
            opportunity_id, edit, source_evidence_ids, self.data.snapshot_head_sha
        ), None

    async def register_task_tools(self, mcp) -> None:
        self._register_lean_verify_edit(mcp)

        @mcp.tool(description="Adjudicate every supplied opportunity exactly once, then terminate.")
        async def submit_opportunity_adjudications(
            adjudications: Annotated[List[OpportunitySubmission], Field(
                description="One terminal adjudication per opportunity; a request requires a candidate."
            )] = [],
        ) -> Dict[str, Any]:
            from ape.tasks.base import EvaluationResult

            raw = [item.model_dump(mode="json") for item in adjudications or []]
            expected = set(self.data.opportunity_ids)
            submitted = [item.get("opportunity_id") for item in raw]
            if len(submitted) != len(set(submitted)) or set(submitted) != expected:
                missing = sorted(expected - set(submitted))
                extra = sorted(set(submitted) - expected)
                return {"evaluation_result": EvaluationResult(
                    success=False,
                    score=0.0,
                    message=f"Opportunity coverage mismatch: missing={missing}, extra={extra}, duplicates={len(submitted) != len(set(submitted))}.",
                ), "message": "Invalid opportunity coverage"}

            raw_candidates = []
            normalized = []
            verification_artifacts = []
            for index, decision in enumerate(raw):
                opportunity_id = decision["opportunity_id"]
                problems = []
                allowed_evidence = set(self.data.evidence_ids_by_opportunity[opportunity_id])
                evidence_ids = list(dict.fromkeys(decision.get("evidence_ids") or []))
                decision["evidence_ids"] = evidence_ids
                if not set(evidence_ids).issubset(allowed_evidence):
                    problems.append("evidence_ids contains evidence from another opportunity")
                if not str(decision.get("rationale") or "").strip():
                    problems.append("rationale is empty")
                candidate = decision.pop("candidate", None)
                if decision["disposition"] == "request" and candidate is None:
                    problems.append("request disposition requires a candidate")
                if decision["disposition"] != "request" and candidate is not None:
                    problems.append("non-request disposition must not include a candidate")
                if candidate is not None:
                    allowed_changes = set(self.data.change_ids_by_opportunity[opportunity_id])
                    problems.extend(self._validate_candidate(candidate, allowed_changes))
                    if (
                        opportunity_id in set(self.data.verification_required_opportunity_ids)
                        and candidate.get("proposed_edit") is None
                    ):
                        problems.append(
                            "this opportunity requires a structured proposed_edit that Lean can verify"
                        )
                if problems:
                    return {"evaluation_result": EvaluationResult(
                        success=False,
                        score=0.0,
                        message=f"Adjudication {index} is invalid: {'; '.join(problems)}. Fix and resubmit.",
                    ), "message": "Invalid opportunity adjudication"}
                if candidate is not None:
                    artifact, verification_error = await self._verify_candidate_edit(
                        opportunity_id, candidate, evidence_ids
                    )
                    if verification_error:
                        return {"evaluation_result": EvaluationResult(
                            success=False,
                            score=0.0,
                            message=(
                                f"Adjudication {index} submitted an edit that failed Lean "
                                f"verification: {verification_error}. Fix or remove the edit."
                            ),
                        ), "message": "Opportunity edit verification failed"}
                    if artifact is not None:
                        verification_artifacts.append(artifact)
                        decision["evidence_ids"].append(artifact["artifact_id"])
                decision["candidate_ordinal"] = None
                if candidate is not None:
                    decision["candidate_ordinal"] = len(raw_candidates)
                    raw_candidates.append(candidate)
                normalized.append(decision)

            result = self.create_result(
                success=True,
                score=1.0,
                pr_number=self.data.pr_number,
                work_unit_id=self.data.work_unit_id,
                rendered_prompt_sha256=self.data.rendered_prompt_sha256,
                adjudications=normalized,
                candidates=raw_candidates,
                verification_artifacts=verification_artifacts,
                findings=[],
                review_message="",
            )
            if self.termination_callback:
                await self.termination_callback(result)
            return {"evaluation_result": EvaluationResult(
                success=True,
                score=1.0,
                message=(
                    f"Recorded {len(normalized)} adjudications, {len(raw_candidates)} candidates, "
                    f"and {len(verification_artifacts)} verification artifacts."
                ),
            ), "message": "Opportunity adjudications submitted"}


register_task("lean_pr_review_v4_opportunity_adjudication", LeanPRReviewV4OpportunityTask)
