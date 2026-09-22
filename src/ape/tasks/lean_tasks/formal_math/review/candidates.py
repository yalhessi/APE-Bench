"""APE execution task for production-identical v4 candidate prompts."""

import hashlib
import json
from pathlib import Path
from typing import Annotated, Any, Dict, List, Literal, Optional, Tuple, get_args

from pydantic import BaseModel, ConfigDict, Field

from ape.tasks.base import register_task
from ape.tasks.lean_tasks.formal_math.review.base import (
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
        "none", "verify_checkable_edits", "verify_edits_if_present"
    ] = "none"


#: Why an arm submitted nothing.
#:
#: An empty submission was mute: `submit_candidates([])` carried no reason, so "nothing here
#: falls under my concern", "I found something and it did not meet my bar" and "I could not
#: establish it" all arrived as the same empty list. 81% of specialist invocations on
#: `pr5_A_lead_heldout12_rep1` were empty, and the rules file records the consequence —
#: "there was never a rationale to aim a prompt at". These are the five endings a
#: last-action analysis of that run could distinguish from the outside; recording them at the
#: source costs one enum and replaces the inference.
#:
#: Declared once, as a Literal, so the tool schema enumerates it for the model and no second
#: copy can drift: a closed vocabulary maintained in two places is this repo's most expensive
#: recurring bug.
#: How many times `forbid_abstention` presses before it accepts an empty submission anyway.
#:
#: It has to give up eventually. `termination_callback` fires on the success path alone, so an
#: arm that never submits burns its turns and is recorded as failed — and a failed mandatory job
#: is a coverage gap, which would turn "this arm had nothing" into a hole in the run and make the
#: experiment unreadable. Three presses, then the refusal is recorded under its own reason so
#: "pressed and still nothing" stays distinguishable from an ordinary abstention.
_FORCED_SUBMISSION_ATTEMPTS = 3

#: Assigned by the system, never offered to the model: it is not in `AbstentionReason` and does
#: not appear in the tool schema. An arm reaches it only by being pressed
#: `_FORCED_SUBMISSION_ATTEMPTS` times and still submitting nothing, which is the outcome the
#: `forbid_abstention` experiment exists to count.
FORCED_EMPTY_REASON = "nothing_found_under_duress"

AbstentionReason = Literal[
    "nothing_of_this_kind_here",
    "already_correct",
    "below_my_bar",
    "could_not_establish",
    "belongs_to_another_concern",
]
ABSTENTION_REASONS: Tuple[str, ...] = get_args(AbstentionReason)


class LeanPRReviewV4CandidateResult(BasePRReviewResult):
    work_unit_id: str
    rendered_prompt_sha256: str
    candidates: List[Dict[str, Any]] = Field(default_factory=list)
    verification_artifacts: List[Dict[str, Any]] = Field(default_factory=list)
    #: `{"reason": ..., "detail": ...}` when the arm submitted nothing, else None. Declared
    #: here because `BaseTaskResult` is pydantic with the default `extra='ignore'`: an
    #: undeclared keyword reaches `create_result` and is dropped with no error at all.
    abstention: Optional[Dict[str, str]] = None


class ProposedEditSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str
    declaration_name: Optional[str] = None
    new_declaration: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    replacement: Optional[str] = None


class PatchEditSubmission(BaseModel):
    """One edit inside a coordinated fix. Same two modes as `proposed_edit`."""

    model_config = ConfigDict(extra="forbid")
    path: str
    declaration_name: Optional[str] = None
    new_declaration: Optional[str] = None
    line_start: Optional[int] = Field(default=None, ge=1)
    line_end: Optional[int] = Field(default=None, ge=1)
    replacement: Optional[str] = None


class RejectedAlternative(BaseModel):
    model_config = ConfigDict(extra="forbid")

    """One verified edit that lost, and why.

    `compiled` is the arm's own report and is not trusted as evidence -- nothing admits a
    finding on the strength of it. It is here so a rejection can be told apart from an
    attempt that simply failed, which is the whole distinction that made rung 3c readable.
    """

    replacement: str = Field(description="The edit text that was not chosen")
    compiled: bool = Field(description="Whether lean_verify_edit accepted it")
    why_not: str = Field(description=(
        "Why this lost to the submitted candidate. Required: a rejection with no reason is "
        "the state the artifacts were already in."))

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
    #: Several edits that stand or fall together, for a fix one edit cannot express — rename
    #: a pair, add a lemma and prove it from its dual, attribute a family and delete the
    #: siblings it generates. Refused by default: `_patch_set_error` rejects it unless the
    #: task opts in, so the v4 contract is unchanged and no arm gains the capability by
    #: accident.
    patch_set: Optional[List[PatchEditSubmission]] = None
    model_confidence: Optional[float] = Field(default=None, ge=0, le=1)
    #: Edits the arm wrote, compiled, and did NOT choose.
    #:
    #: Added because the system could not see its own most consequential failure. On PR 33098,
    #: rung 3c, the arm produced `grind [minimalCover]` -- the maintainer's request character
    #: for character -- watched it compile, and submitted `simpa [minimalCover, h] using ...`
    #: instead. Nothing recorded the discarded alternative: the submission carries one
    #: candidate per site, `verification_artifacts` keeps only the edit that was chosen, and
    #: the run reported a plain miss. Detecting it took a gold-derived oracle and a hand read
    #: of the transcript.
    #:
    #: So this is a measurement field before it is a behaviour one. It is optional -- making it
    #: required would have arms inventing rejections to satisfy a schema -- and it is scored
    #: nowhere: it exists so that "the arm had the right answer and did not pick it" is a
    #: question the artifacts can answer.
    rejected_alternatives: Optional[List[RejectedAlternative]] = None





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

        from src.mathlib_review.evidence.statement_gate import (
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

    async def _verify_patch_set(
        self, candidate_ordinal: int, candidate: Dict[str, Any]
    ) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """Apply and compile a coordinated patch, producing one artifact for the whole thing.

        Deliberately one artifact rather than one per file: `focused_findings` joins a
        warrant to a candidate, and a candidate whose warrant covered three of its four files
        would be publishable while unverified in the fourth.
        """

        from src.mathlib_review.patchset import (
            PatchEdit, PatchSet, verification_artifact, verify,
        )

        workspace = self._patch_set_workspace()
        if workspace is None:
            return [], ("no workspace is available to compile a coordinated patch in; "
                        "submit a single proposed_edit instead")
        patch = PatchSet(tuple(
            PatchEdit(path=r.get("path", ""), declaration_name=r.get("declaration_name"),
                      new_declaration=r.get("new_declaration"),
                      line_start=r.get("line_start"), line_end=r.get("line_end"),
                      replacement=r.get("replacement"))
            for r in (candidate.get("patch_set") or [])))
        ok, report, touched = verify(patch, workspace)
        if not ok:
            return [], (
                "the coordinated patch does not compile, so the whole candidate is refused "
                f"— fix every edit or drop the candidate:\n{report[-2000:]}")
        return [verification_artifact(
            work_unit_id=self.data.work_unit_id, candidate_ordinal=candidate_ordinal,
            patch=patch, success=True, content=report[-4000:],
            snapshot_sha=self.data.snapshot_head_sha or "", touched=touched,
        )], None

    def _patch_set_workspace(self):
        """The reviewed workspace this task compiles in, or `None`.

        `target_workspace` is a `WorkspaceInfo`, not a path (`ape/tasks/base.py`), so this read
        `.path` the way every other consumer does -- `_edited_file_code`, `_resolve_decl_lines`
        and through them `lean_verify_edit`. It used to call `Path(root)` on the model, which
        raises `TypeError` on the first real coordinated patch; the test that guarded it
        assigned a *string*, so it agreed with itself and not with the class.
        """

        workspace = getattr(self, "target_workspace", None)
        root = getattr(workspace, "path", None) if workspace is not None else None
        return Path(root) if root else None

    async def _verify_candidate_submission(
        self, candidate_ordinal: int, candidate: Dict[str, Any]
    ) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """Recompile reviewed code using lean_verify_edit semantics at terminal submission."""

        edit = candidate.get("proposed_edit")
        checkable = candidate.get("concern_family") in CHECKABLE_CONCERN_FAMILIES
        policy = self.data.submission_verification_policy
        if policy not in {"verify_checkable_edits", "verify_edits_if_present"}:
            return [], None
        # A coordinated fix earns its warrant as one thing: every touched file is compiled
        # and the candidate stands or falls on the whole result. It cannot fall back to the
        # single-edit path, because the halves of a coordinated fix are individually wrong —
        # deleting a generated sibling without the attribute that regenerates it does not
        # compile, and correctly should not.
        if candidate.get("patch_set"):
            artifacts, error = await self._verify_patch_set(candidate_ordinal, candidate)
            return artifacts, error
        # The rule this policy exists to relax. Under `verify_checkable_edits` an arm that has
        # the maintainer's answer and cannot make it compile must abstain: on the 2026-09-21
        # read of the held-out run, that is what the largest group of in-remit gold-site
        # silences says happened, including PR 33149, where the ask was "replace the
        # axiomatized Parseval identity with the existing one", the arm found the existing
        # lemma, and could not connect the PR's own setup to it. `verify_edits_if_present`
        # still compiles every edit it is given and still refuses one that fails; what it
        # allows is the unverified ask, which `finalize` admits as `diagnostic` and never
        # publishes. It does not ask for more findings -- an empty submission stays exactly as
        # cheap -- so the control-PR property is untouched by the rule itself.
        if checkable and edit is None:
            if policy == "verify_edits_if_present":
                return [], None
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

    #: Files a coordinated patch may touch. Empty means the task does not accept one at all,
    #: which is the default: a capability nothing granted is a capability nothing can misuse.
    patch_set_paths: tuple = ()

    def _patch_set_error(self, candidate: Dict[str, Any]) -> Optional[str]:
        """Refuse a patch set unless this task accepts one, and unless it is confined.

        Default-deny. The v4 contract has no coordinated edits and gains none by a field
        appearing on a shared model; a task that wants them says so by setting
        `patch_set_paths`, which is also exactly the confinement boundary.
        """

        rows = candidate.get("patch_set")
        if not rows:
            return None
        if not self.patch_set_paths:
            return ("patch_set is not accepted by this check; submit a single proposed_edit")
        from src.mathlib_review.patchset import PatchEdit, PatchSet, validate

        patch = PatchSet(tuple(
            PatchEdit(path=r.get("path", ""), declaration_name=r.get("declaration_name"),
                      new_declaration=r.get("new_declaration"),
                      line_start=r.get("line_start"), line_end=r.get("line_end"),
                      replacement=r.get("replacement"))
            for r in rows))
        problems = validate(patch, self.patch_set_paths)
        return "; ".join(problems) if problems else None

    def _extra_candidate_error(self, candidate: Dict[str, Any]) -> Optional[str]:
        """A hook for scope rules a subclass adds to the shared submission contract.

        The contract itself stays one implementation — `change_ids ⊆ unit`, subject equality,
        the entity check, the statement gate, edit confinement. An arm whose *scope* differs
        adds its rule here rather than reimplementing the rest and drifting from it.
        """

        return None

    def _annotate_candidate(self, candidate: Dict[str, Any]) -> None:
        """A hook for metadata a subclass records about a submission without refusing it.

        The sibling of `_extra_candidate_error`, and the difference is the whole point. That
        one decides whether a claim may be made; this one records something true about a claim
        that is being made anyway. A rule that belongs here and is put there costs findings —
        v5's concern gate refused correct claims for using the wrong word for them.

        Mutates `candidate` in place, before validation, so anything written here is part of
        what validation sees and part of what is recorded.
        """

    async def register_task_tools(self, mcp) -> None:
        self._register_lean_verify_edit(mcp)

        @mcp.tool(description="Submit zero or more candidate claims for this exact work unit.")
        async def submit_candidates(
            candidates: Annotated[List[CandidateSubmission], Field(
                description="Candidate objects matching the JSON contract in the prompt; [] is valid."
            )] = [],
            abstention_reason: Annotated[Optional[AbstentionReason], Field(
                description=(
                    "REQUIRED when `candidates` is empty, ignored otherwise. Submitting "
                    "nothing is a correct and common outcome; this only records which "
                    "outcome it was. `nothing_of_this_kind_here`: no target falls under "
                    "this check. `already_correct`: the check applies and the code already "
                    "satisfies it. `below_my_bar`: you found a candidate issue and it did "
                    "not meet the evidence or severity bar. `could_not_establish`: you "
                    "needed evidence your tools could not produce. "
                    "`belongs_to_another_concern`: you saw a real issue that is not this "
                    "check's business."
                )
            )] = None,
            abstention_detail: Annotated[str, Field(
                description=(
                    "One sentence, when abstaining: name the specific thing you considered "
                    "and what was missing. 'Checked the three new lemma names against the "
                    "counted population; all three match the dominant prefix.' Not 'nothing "
                    "found'."
                )
            )] = "",
        ) -> Dict[str, Any]:
            from ape.tasks.base import EvaluationResult

            raw_candidates = [item.model_dump(mode="json") for item in candidates or []]
            # Silence has to say which silence it is, or it cannot be read afterwards and
            # cannot be aimed at. Refusing here rather than accepting a mute submission is
            # the same treatment every other contract violation gets, and it costs one short
            # round trip with no re-investigation.
            #
            # The wording carries real weight and is not decoration. An arm that reads this
            # as pressure to produce something would destroy the one result this project has
            # that nothing else replaces: 0 candidates per control PR, per rep. Abstention
            # must stay exactly as cheap as submitting.
            #
            # Asked once, and once only. `termination_callback` fires on the success path
            # alone, so an arm that keeps omitting the reason would never submit legally: it
            # would burn its turns and be recorded as a failed job, and a failed *mandatory*
            # job is a coverage gap. That would convert the cleanest outcome an arm has —
            # looking properly and finding nothing — into a hole in the run, which is a far
            # worse error than an unlabelled silence. So the second empty submission is
            # accepted and labelled `unstated`, which the report already counts and shows.
            # The diagnostic path. Press for a candidate rather than accept the abstention,
            # a bounded number of times, and keep "pressed and still nothing" as its own
            # outcome — collapsing it into `already_correct` would destroy the only signal
            # that separates a high bar from an arm with nothing to say.
            if not raw_candidates and getattr(self.data, "forbid_abstention", False):
                self._forced_presses = getattr(self, "_forced_presses", 0) + 1
                if self._forced_presses <= _FORCED_SUBMISSION_ATTEMPTS:
                    return {"evaluation_result": EvaluationResult(
                        success=False, score=0.0,
                        message=(
                            "This run is not accepting abstentions: submit the single best "
                            "candidate you considered, even if you judged it below your "
                            "usual bar, and set model_confidence to reflect how weak it is. "
                            "Say what you would flag if you had to flag exactly one thing. "
                            f"(attempt {self._forced_presses} of "
                            f"{_FORCED_SUBMISSION_ATTEMPTS})"
                        )),
                        "message": "Abstention not accepted in this run"}
                abstention_reason = FORCED_EMPTY_REASON
            if not raw_candidates and abstention_reason is None:
                self._mute_abstentions = getattr(self, "_mute_abstentions", 0) + 1
                if self._mute_abstentions == 1:
                    return {"evaluation_result": EvaluationResult(
                        success=False, score=0.0,
                        message=(
                            "Submitting nothing is a valid and expected outcome, and this is "
                            "NOT a request to find something — do not add a candidate to "
                            "satisfy it. Only the label is missing. Call submit_candidates "
                            "again with the same empty list, plus abstention_reason set to "
                            f"one of: {', '.join(ABSTENTION_REASONS)}; and one sentence in "
                            "abstention_detail saying what you considered."
                        )),
                        "message": "Abstention recorded without a reason"}
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
                self._annotate_candidate(candidate)
                patch_problem = self._patch_set_error(candidate)
                if patch_problem:
                    problems.append(patch_problem)
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
                abstention=({"reason": abstention_reason or "unstated",
                             "detail": (abstention_detail or "").strip()}
                            if not raw_candidates else None),
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
