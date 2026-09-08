"""
Agentic selector (`lean_pr_review_selector`).

A per-PR triage task: given a LIST of candidate review findings (pooled from prior
review runs) and a WORKSPACE (read / search / verify), the agent investigates each
candidate the way a maintainer would — is the proposed golf genuinely worthwhile? does
the claimed duplicate lemma actually exist? does the generalization hold? — and then
assigns each candidate a probability 0-100 that a Mathlib maintainer would actually
RAISE it on this PR.

This is the tool-grounded counterpart to the diff-only LLM selector
(src/datasets/pr_review_v2/selector.py mode=pointwise|listwise). It tests whether the
ability to inspect the proof and the library lifts selection — especially on V2
(golf/dup/generality), where the diff-only selector is at chance because "is this golf
worth raising" is not visible in the diff hunk. It reuses BasePRReviewTask's
materialization (merge base + δ₀, read-only) and toolset; it only swaps the prompt and
the submit contract (scores, not findings). Scored externally; the task never scores.
"""

from typing import Any, Dict, List, Optional, Tuple

from pydantic import ConfigDict, Field

from ape.tasks.base import BaseTaskResult, EvaluationResult, register_task

from ape.tasks.lean_tasks.formal_math.review.base import BasePRReviewConfig, BasePRReviewData, BasePRReviewTask

SELECTOR_SYSTEM = """You are a Mathlib maintainer triaging a pull request, deciding which review
comments are worth raising. The PR already COMPILES — correctness is settled by the kernel — so your
question is acceptability: of the candidate findings below, which would a maintainer actually flag?

Mathlib maintainers are highly SELECTIVE. On any PR there are many *valid* improvements (a proof could
be shortened, a lemma made more general, a name tweaked) that a maintainer simply does NOT comment
on — they raise only the few worth the author's time given this PR's scope and the surrounding code.

You have a WORKSPACE — investigate before you decide. Read the changed files in `target/`, search the
library (content_search), and check Lean code (lean_verify). Use the tools to ground each call: is a
suggested golf genuinely shorter and more idiomatic, or a lateral rewrite? does a claimed duplicate
lemma actually exist in the library? does a proposed generalization actually hold? A finding that is
*valid but trivial* should score LOW; a finding that a maintainer would genuinely stop to request
should score HIGH.

After investigating, assign every candidate a probability (0-100) that a maintainer would raise it.
Be calibrated and comparative: spread the scores, reserve high values for the few you would truly
flag. Then call {submit_tool_name} exactly once with a score for every candidate index."""

SELECTOR_USER = """## PR #{pr_number} — {title}

## Description

{description}

## Diff under review (against the merge base; line numbers refer to the reviewed state)

```diff
{diff}
```

## Workspace

- `target/` holds the full repository at the reviewed state (read-only). Changed files:
{changed_files}
- Available tools: {tool_summary}

## Candidate findings to score

{findings_block}

## Your task

Investigate each candidate with your tools, then call `{submit_tool_name}` exactly once with a score
(0-100, probability a maintainer would raise it) for EVERY candidate index above. Be selective: most
candidates should score low."""


class PRReviewSelectorData(BasePRReviewData):
    """Review data plus the candidate findings to triage. Each candidate:
    {index, path, line_start, line_end, severity, claim, suggested_fix}."""

    task_type: str = Field(default="lean_pr_review_selector")
    candidate_findings: List[Dict[str, Any]] = Field(default_factory=list)


class PRReviewSelectorResult(BaseTaskResult):
    """Per-finding maintainer-worthiness scores, for external metric assembly."""

    model_config = ConfigDict()

    pr_number: int
    scores: List[Dict[str, Any]] = Field(default_factory=list)  # {index, score, reason}
    review_message: str = ""


class LeanPRReviewSelectorTask(BasePRReviewTask):
    """Per-PR agentic selector — scores candidate findings with workspace grounding."""

    task_type = "lean_pr_review_selector"
    data_class = PRReviewSelectorData
    task_config_class = BasePRReviewConfig
    task_result_class = PRReviewSelectorResult

    def _get_prompts(self, version: str) -> Tuple[str, str]:
        return SELECTOR_SYSTEM, SELECTOR_USER

    def _findings_block(self) -> str:
        lines = []
        for c in self.data.candidate_findings:
            loc = f"{c.get('path')}:{c.get('line_start')}" if c.get("path") else "PR-level"
            line = f"[{c.get('index')}] ({loc}; {c.get('severity', '?')}) {str(c.get('claim') or '')[:500]}"
            if c.get("suggested_fix"):
                line += f"\n      Suggested fix: {str(c['suggested_fix'])[:300]}"
            lines.append(line)
        return "\n".join(lines) if lines else "(no candidates)"

    async def create_user_prompt(self) -> str:
        _system, user_template = self._get_prompts(self.config.task_config.prompt_version)
        changed = "\n".join(f"  - `{p}`" for p in self.data.changed_files) or "  (none listed)"
        submit_tool_name = f"{self.config.mcp_server_name}submit_scores"
        return user_template.format(
            pr_number=self.data.pr_number,
            title=self.data.pr_title,
            description=self.data.pr_description.strip() or "(no description provided)",
            diff=self.data.diff,
            changed_files=changed,
            tool_summary=self._tool_summary(),
            findings_block=self._findings_block(),
            submit_tool_name=submit_tool_name,
        )

    async def create_system_prompt(self) -> str:
        system, _user = self._get_prompts(self.config.task_config.prompt_version)
        submit_tool_name = f"{self.config.mcp_server_name}submit_scores"
        return system.format(submit_tool_name=submit_tool_name)

    async def register_task_tools(self, mcp) -> None:
        from typing import Annotated

        @mcp.tool(
            description=(
                "Submit a maintainer-worthiness score (0-100) for EACH candidate finding, by its "
                "index. Call exactly once when done. Include every index shown. A text-only response "
                "is INVALID."
            )
        )
        async def submit_scores(
            scores: Annotated[List[Dict[str, Any]], Field(
                description="One entry per candidate: {index: int, score: 0-100, reason?: str}."
            )] = [],
            message: Annotated[str, Field(description="Optional summary.", default="")] = "",
        ) -> Dict[str, Any]:
            self.logger.info("submit_scores: %d scores", len(scores or []))
            try:
                normalized = self._normalize_scores(scores or [])
                result = self.create_result(
                    success=True, score=1.0, pr_number=self.data.pr_number,
                    scores=normalized, review_message=message or "",
                )
                if self.termination_callback:
                    try:
                        await self.termination_callback(result)
                    except Exception as exc:  # noqa: BLE001
                        self.logger.warning("Failed to trigger termination: %s", exc)
                return {
                    "evaluation_result": EvaluationResult(
                        success=True, score=1.0, message=f"Scores recorded: {len(normalized)}."),
                    "message": "Scores submitted",
                }
            except Exception:  # noqa: BLE001
                import traceback
                self.logger.error("submit_scores failed: %s", traceback.format_exc())
                return {
                    "evaluation_result": EvaluationResult(success=False, score=0.0, message="submit failed"),
                    "message": "Submit failed",
                }

    def _normalize_scores(self, scores: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        n = len(self.data.candidate_findings)
        out: List[Dict[str, Any]] = []
        seen = set()
        for raw in scores:
            if not isinstance(raw, dict):
                continue
            try:
                idx = int(raw.get("index"))
            except (ValueError, TypeError):
                continue
            if idx < 0 or idx >= n or idx in seen:
                continue
            seen.add(idx)
            try:
                sc = float(raw.get("score"))
            except (ValueError, TypeError):
                sc = 0.0
            sc = max(0.0, min(100.0, sc))
            out.append({"index": idx, "score": sc, "reason": str(raw.get("reason") or "")[:300]})
        return out


register_task("lean_pr_review_selector", LeanPRReviewSelectorTask)
