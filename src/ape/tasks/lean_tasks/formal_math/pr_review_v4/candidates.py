"""APE execution task for production-identical v4 candidate prompts."""

import hashlib
import json
from typing import Annotated, Any, Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field

from ape.tasks.base import register_task
from ape.tasks.lean_tasks.formal_math.pr_review_v2.base import (
    BasePRReviewConfig, BasePRReviewData, BasePRReviewResult, BasePRReviewTask,
)


class LeanPRReviewV4CandidateConfig(BasePRReviewConfig):
    finding_budget: int = 20


class LeanPRReviewV4CandidateData(BasePRReviewData):
    task_type: str = "lean_pr_review_v4_candidates"
    work_unit_id: str
    episode_id: str
    change_ids: List[str]
    entity_ids_by_change: Dict[str, List[str]]
    primary_subjects_by_change: Dict[str, str]
    #: change_id -> the file that change lives in, populated from renderer /12 onward and
    #: used by `normalize_candidate_edit` to confine an edit to its own target's file.
    #: Defaults to empty so the frozen /11 task data still loads; a /11 unit carries no
    #: path map and the confinement check falls back to PR-wide `changed_files`.
    paths_by_change: Dict[str, str] = Field(default_factory=dict)
    rendered_system_prompt: str
    rendered_user_prompt: str
    rendered_prompt_sha256: str
    submission_verification_policy: Literal[
        "none", "verify_checkable_edits"
    ] = "none"


class LeanPRReviewV4CandidateResult(BasePRReviewResult):
    work_unit_id: str
    rendered_prompt_sha256: str
    candidates: List[Dict[str, Any]] = Field(default_factory=list)
    verification_artifacts: List[Dict[str, Any]] = Field(default_factory=list)


class ProposedEditSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str
    declaration_name: Optional[str] = None
    new_declaration: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    replacement: Optional[str] = None


class CandidateSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid")
    primary_change_id: str
    primary_entity_id: Optional[str] = None
    primary_subject: str
    change_ids: List[str]
    concern_family: Literal[
        "correctness", "proof-golf", "duplication", "naming", "generalization",
        "documentation", "style", "scope", "other",
    ]
    #: What kind of problem this is, in the vocabulary the deterministic arm and the
    #: coverage census already use. It is the routing key that lets a claim be checked:
    #: `concern_family` names a topic, and no collector can verify a topic.
    #: Optional here so a model that omits it fails at ingestion with a clear reason rather
    #: than losing the whole batch to a schema error.
    issue_kind: Optional[Literal[
        "broken_build", "correctness_policy", "documentation_gap",
        "duplicate_implementation", "generalization_available", "missed_canonical_api",
        "naming_convention_violation", "policy_violation", "proof_simplification",
        "scope_placement", "style_norm_violation",
    ]] = None
    concern_label: str
    severity: Literal["blocking", "advisory"]
    claim: str
    requested_change: str
    suggested_fix: Optional[str] = None
    proposed_edit: Optional[ProposedEditSubmission] = None
    model_confidence: Optional[float] = Field(default=None, ge=0, le=1)


CHECKABLE_CONCERN_FAMILIES = {
    "correctness", "proof-golf", "duplication", "generalization",
}


def normalize_proposed_edit_path(path: str) -> str:
    """Normalize common workspace/diff prefixes to a repository-relative path."""

    normalized = str(path or "").strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    changed = True
    while changed:
        changed = False
        for prefix in ("target/", "a/", "b/"):
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):]
                changed = True
                break
    return normalized


def normalize_candidate_edit(
    candidate: Dict[str, Any], changed_files: List[str], problems: List[str],
    paths_by_change: Optional[Dict[str, str]] = None,
) -> None:
    """Normalize and confine a proposed edit.

    `changed_files` is a PR-wide list, so checking membership in it only established that
    the edit touched *some* file the PR changed. An agent scheduled on file A could submit
    an edit to file B, declare a `primary_change_id` in A, and pass every check — the
    verification then compiled B and awarded `verified_compile`. When the release records
    per-target paths, the edit is confined to the target it claims to be about.
    """
    proposed_edit = candidate.get("proposed_edit")
    if not isinstance(proposed_edit, dict):
        return
    path = normalize_proposed_edit_path(proposed_edit.get("path", ""))
    proposed_edit["path"] = path
    if not path:
        problems.append("proposed_edit.path is empty")
    elif path not in set(changed_files):
        problems.append("proposed_edit.path is not one of the PR's changed files")
    else:
        expected = (paths_by_change or {}).get(candidate.get("primary_change_id") or "")
        if expected and path != expected:
            problems.append(
                f"proposed_edit.path {path!r} is not the file of its primary change target "
                f"({expected!r}); an edit must change the target it is about"
            )
    declaration_mode = bool(
        proposed_edit.get("declaration_name") and proposed_edit.get("new_declaration")
    )
    line_mode = (
        proposed_edit.get("line_start") is not None
        and proposed_edit.get("line_end") is not None
        and proposed_edit.get("replacement") is not None
    )
    if declaration_mode == line_mode:
        problems.append(
            "proposed_edit must use exactly one complete mode: declaration_name + "
            "new_declaration, or line_start + line_end + replacement"
        )


def build_candidate_verification_artifact(
    *, work_unit_id: str, candidate_ordinal: int, stage: Literal["baseline", "proposed_edit"],
    path: str, success: bool, content: str, snapshot_sha: str,
    edit: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    edit_sha = None
    if edit is not None:
        encoded_edit = json.dumps(edit, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        edit_sha = hashlib.sha256(encoded_edit.encode()).hexdigest()
    identity = {
        "work_unit_id": work_unit_id,
        "candidate_ordinal": candidate_ordinal,
        "stage": stage,
        "kind": "lean_compile",
        "success": success,
        "path": path,
        "edit_sha256": edit_sha,
        "content": content,
        "snapshot_sha": snapshot_sha,
    }
    encoded = json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(encoded.encode()).hexdigest()
    return {
        "schema_version": "residual-candidate-verification1",
        "artifact_id": f"residual-candidate-verification:{digest[:24]}",
        **identity,
        "source_sha256": digest,
    }


class LeanPRReviewV4CandidateTask(BasePRReviewTask):
    task_type = "lean_pr_review_v4_candidates"
    data_class = LeanPRReviewV4CandidateData
    task_config_class = LeanPRReviewV4CandidateConfig
    task_result_class = LeanPRReviewV4CandidateResult

    def _get_prompts(self, version: str) -> Tuple[str, str]:
        return self.data.rendered_system_prompt, self.data.rendered_user_prompt

    async def create_system_prompt(self) -> str:
        return self.data.rendered_system_prompt

    async def create_user_prompt(self) -> str:
        return self.data.rendered_user_prompt

    @staticmethod
    def _verification_detail(result: Dict[str, Any]) -> str:
        """Render compile diagnostics for the agent, with enough to act on.

        This used to emit the `data` field alone, so a rejected submission told the agent
        less than the exploration tool had already shown it: "unexpected token \'@[\'" with no
        line and no source text, against a spliced file it never sees. Carrying `code_line`
        and `pos` costs a few tokens and is the difference between a fixable report and a
        riddle. Prefers errors the edit actually introduced when that split is available.
        """

        messages = (
            result.get("errors_introduced_by_your_edit")
            or result.get("errors")
            or result.get("messages")
            or []
        )
        details = []
        for item in messages[:5]:
            if not isinstance(item, dict):
                details.append(str(item))
                continue
            text = str(item.get("data") or item.get("message") or item).strip()
            position = item.get("pos") or {}
            where = ""
            if position.get("line"):
                where = f" [line {position['line']}"
                if position.get("column") is not None:
                    where += f", col {position['column']}"
                where += "]"
            source = str(item.get("code_line") or "").strip()
            if source:
                text = f"{text}{where} in `{source[:120]}`"
            else:
                text = f"{text}{where}"
            details.append(text)
        rendered = "; ".join(details) or str(result.get("error") or "no diagnostics")
        note = result.get("note")
        return f"{rendered} ({note})" if note else rendered

    def _statement_gate_error(
        self, candidate: Dict[str, Any], path: str, edit: Dict[str, Any], baseline_code: str
    ) -> Optional[str]:
        """Enforce what the claim says about the statement, before spending a compile.

        golf/idiom claim the statement is untouched; generality claims it moved. Both are
        checkable from the same comparison, and neither was checked.
        """

        from src.datasets.pr_review_v4.statement_gate import (
            compare_statements,
            declaration_source,
            gate_error,
        )

        issue_kind = candidate.get("issue_kind")
        if issue_kind not in {"proof_simplification", "generalization_available"}:
            return None
        declaration_name = edit.get("declaration_name")
        replacement = edit.get("new_declaration")
        if not declaration_name or not replacement:
            return (
                f"a {issue_kind} finding must be submitted as declaration_name + "
                "new_declaration so its statement can be compared with the original"
            )
        original = declaration_source(baseline_code, declaration_name)
        if original is None:
            return (
                f"`{declaration_name}` could not be uniquely located in {path}, so the "
                "statement cannot be compared"
            )
        return gate_error(issue_kind, compare_statements(original, replacement))

    async def _verify_candidate_submission(
        self, candidate_ordinal: int, candidate: Dict[str, Any]
    ) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """Recompile reviewed code using lean_verify_edit semantics at terminal submission."""

        edit = candidate.get("proposed_edit")
        checkable = candidate.get("concern_family") in CHECKABLE_CONCERN_FAMILIES
        if self.data.submission_verification_policy != "verify_checkable_edits":
            return [], None
        if checkable and edit is None:
            return [], (
                f"{candidate.get('concern_family')} candidates require a structured proposed_edit "
                "under the verification-backed residual policy"
            )
        if edit is None:
            return [], None

        path = edit.get("path") or ""
        baseline_code, baseline_error = self._edited_file_code(path)
        if baseline_code is None:
            return [], baseline_error
        edited_code, edited_error = self._edited_file_code(
            path,
            edit.get("line_start"),
            edit.get("line_end"),
            edit.get("replacement"),
            declaration_name=edit.get("declaration_name"),
            new_declaration=edit.get("new_declaration"),
        )
        if edited_code is None:
            return [], edited_error

        # The statement/proof split the claim asserts. `verified_compile` otherwise means
        # only "some theorem compiles here": the splice replaces the whole declaration,
        # signature included, and nothing else compares the two signatures.
        statement_error = self._statement_gate_error(candidate, path, edit, baseline_code)
        if statement_error:
            return [], statement_error

        from ape.toolkits.execute.lean.tools import LeanVerifyToolsProvider

        lean_tool = LeanVerifyToolsProvider(task=self, config=self.config, logger=self.logger)
        try:
            baseline_result = await lean_tool.execute(code=baseline_code, max_messages=20)
            edited_result = await lean_tool.execute(code=edited_code, max_messages=20)
        except Exception as exc:  # noqa: BLE001
            return [], f"verification raised: {exc}"

        baseline_success = bool(baseline_result.get("success"))
        baseline_detail = self._verification_detail(baseline_result)
        artifacts = [build_candidate_verification_artifact(
            work_unit_id=self.data.work_unit_id,
            candidate_ordinal=candidate_ordinal,
            stage="baseline",
            path=path,
            success=baseline_success,
            content=(
                "Reviewed file compiled successfully without an edit."
                if baseline_success else f"Reviewed file failed compilation: {baseline_detail}"
            ),
            snapshot_sha=self.data.snapshot_head_sha,
        )]
        if not edited_result.get("success"):
            return artifacts, (
                "proposed edit failed reviewed-file compilation: "
                f"{self._verification_detail(edited_result)}"
            )
        artifacts.append(build_candidate_verification_artifact(
            work_unit_id=self.data.work_unit_id,
            candidate_ordinal=candidate_ordinal,
            stage="proposed_edit",
            path=path,
            success=True,
            content="Reviewed file compiled successfully with the submitted structured edit.",
            snapshot_sha=self.data.snapshot_head_sha,
            edit=edit,
        ))
        return artifacts, None

    def _extra_candidate_error(self, candidate: Dict[str, Any]) -> Optional[str]:
        """A hook for scope rules a subclass adds to the shared submission contract.

        The contract itself stays one implementation — `change_ids ⊆ unit`, subject equality,
        the entity check, the statement gate, edit confinement. An arm whose *scope* differs
        adds its rule here rather than reimplementing the rest and drifting from it.
        """

        return None

    async def register_task_tools(self, mcp) -> None:
        self._register_lean_verify_edit(mcp)

        @mcp.tool(description="Submit zero or more candidate claims for this exact work unit.")
        async def submit_candidates(
            candidates: Annotated[List[CandidateSubmission], Field(
                description="Candidate objects matching the JSON contract in the prompt; [] is valid."
            )] = [],
        ) -> Dict[str, Any]:
            from ape.tasks.base import EvaluationResult

            raw_candidates = [item.model_dump(mode="json") for item in candidates or []]
            allowed = set(self.data.change_ids)
            allowed_by_suffix = {item.removeprefix("change:"): item for item in allowed}
            for index, candidate in enumerate(raw_candidates):
                change_ids = [allowed_by_suffix.get(item, item)
                              for item in candidate.get("change_ids") or []]
                candidate["change_ids"] = change_ids
                primary_change_id = allowed_by_suffix.get(
                    candidate.get("primary_change_id"), candidate.get("primary_change_id"))
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
                normalize_candidate_edit(
                    candidate, self.data.changed_files, problems,
                    self.data.paths_by_change,
                )
                extra = self._extra_candidate_error(candidate)
                if extra:
                    problems.append(extra)
                if expected_subject and "/" not in expected_subject:
                    short_subject = expected_subject.rsplit(".", 1)[-1]
                    grounded_text = f"{candidate.get('claim', '')} {candidate.get('requested_change', '')}"
                    if short_subject not in grounded_text:
                        problems.append(f"claim/requested_change must name {short_subject!r}")
                if problems:
                    return {"evaluation_result": EvaluationResult(
                        success=False, score=0.0,
                        message=f"Candidate {index} is invalid: {'; '.join(problems)}. Fix and resubmit."),
                        "message": "Invalid candidate submission"}
            verification_artifacts = []
            for index, candidate in enumerate(raw_candidates):
                artifacts, verification_error = await self._verify_candidate_submission(
                    index, candidate
                )
                if verification_error:
                    return {"evaluation_result": EvaluationResult(
                        success=False,
                        score=0.0,
                        message=(
                            f"Candidate {index} failed verification-backed submission: "
                            f"{verification_error}. Fix the edit or omit the candidate."
                        ),
                    ), "message": "Candidate verification failed"}
                verification_artifacts.extend(artifacts)
            result = self.create_result(
                success=True, score=1.0, pr_number=self.data.pr_number,
                work_unit_id=self.data.work_unit_id,
                rendered_prompt_sha256=self.data.rendered_prompt_sha256,
                candidates=raw_candidates,
                verification_artifacts=verification_artifacts,
                findings=[], review_message="",
            )
            if self.termination_callback:
                await self.termination_callback(result)
            return {"evaluation_result": EvaluationResult(success=True, score=1.0,
                    message=(
                        f"Recorded {len(raw_candidates)} candidates and "
                        f"{len(verification_artifacts)} verification artifacts."
                    )),
                    "message": "Candidates submitted"}


register_task("lean_pr_review_v4_candidates", LeanPRReviewV4CandidateTask)
