"""Whole-PR review with optional convention delivery and an ordered list of author-facing findings."""

import json
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ape.tasks.base import EvaluationResult, register_task

from .context_tools import register_context_tools
from .solo import SoloReviewConfig, SoloReviewData, SoloReviewResult, SoloReviewTask


class WholePRConfig(SoloReviewConfig):
    # An inherited historical brief, precomputed precedents, or finding cap would change this design.
    system_prompt_file: None = None
    precedent_file: None = None
    finding_budget: Literal[0] = 0
    review_notes: Literal[False] = False


class WholePRData(SoloReviewData):
    task_type: str = "lean_pr_review_v5_whole_pr"
    context_tools: list[Literal["declaration_search", "precedent_search"]] = Field(default_factory=list)


class WholePRResult(SoloReviewResult):
    # The author's copy. The inherited findings field is the historical matcher's projection.
    submitted_findings: list[dict] | None = None


class SubmittedFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim: str = Field(pattern=r"\S", description="Why you would ask for this change.")
    suggested_fix: str = Field(pattern=r"\S", description="What you would ask the author to change.")
    path: str | None = Field(default=None, pattern=r"\S", description="File, if the finding concerns one.")
    line_start: int | None = Field(default=None, strict=True, ge=1, description="First line, if relevant.")
    line_end: int | None = Field(default=None, strict=True, ge=1, description="Last line, if giving a range.")

    @model_validator(mode="after")
    def _location(self):
        if self.line_start is not None and self.path is None:
            raise ValueError("A line needs its file path.")
        if self.line_end is not None and (self.line_start is None or self.line_end < self.line_start):
            raise ValueError("A line range needs a start at or before its end.")
        return self

    def recorded(self):
        from src.mathlib_review.schema.findings import IMPORT_ISSUE_KIND, UNLABELLED_FAMILY

        anchor = None
        if self.path is not None:
            anchor = {"path": self.path, "line_start": self.line_start, "line_end": self.line_end}
        # Historical anchoring accepts unclassified findings using the same defaults as imported reviews.
        return {"claim": self.claim, "suggested_fix": self.suggested_fix, "anchor": anchor,
                "severity": "advisory", "concern_family": UNLABELLED_FAMILY, "issue_kind": IMPORT_ISSUE_KIND}


class WholePRReviewTask(SoloReviewTask):
    task_type = "lean_pr_review_v5_whole_pr"
    data_class = WholePRData
    task_config_class = WholePRConfig
    task_result_class = WholePRResult
    design_version = "whole-pr/1"

    async def create_system_prompt(self) -> str:
        return ""

    def _conventions(self) -> str:
        from src.mathlib_review.review.inputs import verified_text

        config = self.config.task_config
        if config.context_file is None:
            return ""
        if "precedent_search" in self.data.context_tools:
            raise ValueError("This review design offers either excerpt search or a delivered convention list")
        content = verified_text(config.context_file, config.context_file_sha256, "context_file")
        rows = [json.loads(line) for line in content.split("\n") if line.strip()]
        matches = [row for row in rows if row["pr_number"] == self.data.pr_number]
        if len(matches) != 1:
            raise ValueError(f"Expected one context row for PR {self.data.pr_number}, found {len(matches)}")
        row, = matches
        if (row.get("episode_id") != self.data.episode_id
                or not self.data.snapshot_head_sha
                or row.get("reviewed_head_sha") != self.data.snapshot_head_sha):
            raise ValueError(f"Context is not bound to the reviewed head of {self.data.episode_id}")
        sections = row["sections"]
        if sections == []:
            return ""
        if (not isinstance(sections, list) or len(sections) != 1 or not isinstance(sections[0], dict)
                or sections[0].get("title") != "Conventions" or not isinstance(sections[0].get("text"), str)
                or not sections[0]["text"].strip()):
            raise ValueError("Whole-PR context must contain only the delivered Conventions section")
        return "\n\n## Conventions\n\n" + sections[0]["text"].rstrip()

    async def create_user_prompt(self) -> str:
        data = self.data
        files = "\n".join(f"- `{path}`" for path in data.changed_files)
        return (
            "Review this Mathlib PR at the supplied revision. What changes, if any, would you ask "
            "the author to make? Give an ordered list of findings. For each finding, say what to "
            "change and why. You may return an empty list.\n\n"
            f"Submit with `{self.submit_tool_name}`.\n\n"
            f"## Pull request #{data.pr_number}\n\n{data.pr_title}\n\n{data.pr_description}\n\n"
            f"Reviewed revision: `{data.snapshot_head_sha}`\n\nChanged files:\n{files}\n\n"
            f"```diff\n{data.diff}\n```" + self._conventions()
        )

    async def register_task_tools(self, mcp) -> None:
        self._register_lean_verify_edit(mcp)
        register_context_tools(self, mcp)

        @mcp.tool(description="Submit your ordered review findings. This ends the review.")
        async def submit_findings(
            findings: Annotated[list[SubmittedFinding], Field(description="Ordered findings. An empty list is valid.")],
            message: Annotated[str, Field(description="Optional summary of the findings.")] = "",
        ) -> dict:
            result = self.create_result(
                success=True, score=1.0, pr_number=self.data.pr_number, review_message=message,
                findings=[finding.recorded() for finding in findings],
                submitted_findings=[finding.model_dump(exclude_unset=True) for finding in findings],
            )
            if self.termination_callback:
                await self.termination_callback(result)
            return {"evaluation_result": EvaluationResult(success=True, score=1.0, message="Review recorded"),
                    "message": "Review submitted"}


register_task(WholePRReviewTask.task_type, WholePRReviewTask)
