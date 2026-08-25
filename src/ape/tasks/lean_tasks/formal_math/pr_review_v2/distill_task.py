"""
Workspace-grounded PR distillation (`lean_pr_review_distill`).

The promotion of the diff-only distillation probe (src/datasets/pr_review_v2/distillation.py)
into a first-class review task. It materializes the reviewed PR state (merge base + δ₀,
read-only) and gives the agent the workspace, so it reads the FULL proof of each changed
declaration and the lemmas it leans on — not just the diff hunk — before judging how directly
the Lean proof follows the natural mathematical argument. That grounding is what the diff-only
pass lacked: from a hunk the model rated almost every proof highly legible (median 93), washing
out the signal; with the whole proof in view it can tell a transparent proof from one that
obscures the idea.

It emits the SAME `PRDistillation` artifact (pr_summary + per-declaration nl_statement /
nl_proof_sketch / legibility / divergence) as the probe, so every consumer — the selector probe
now, the holistic review agent and the checkers later — reads one shared shape. Scored/consumed
externally; the task never scores.
"""

from typing import Annotated, Any, Dict, List, Tuple

from pydantic import ConfigDict, Field

from ape.tasks.base import BaseTaskResult, EvaluationResult, register_task

from .base import BasePRReviewConfig, BasePRReviewData, BasePRReviewTask

DISTILL_SYSTEM = """You are reading a Mathlib pull request to understand the MATHEMATICS behind each
proof it adds or changes — the intended idea — and to judge how transparently the Lean proof expresses
it. You have a WORKSPACE: `target/` holds the full repository at the reviewed state (read-only). USE
it — read the complete proof of each changed declaration (not just the diff hunk), follow the lemmas it
invokes (content_search / code navigation), and check Lean snippets with lean_verify if it helps you
judge. The diff alone is not enough to assess a proof's clarity.

For each theorem/lemma/def the PR ADDS or MEANINGFULLY CHANGES that has a non-trivial proof, determine:
- `name`: the declaration name.
- `nl_statement`: what it asserts, in plain mathematical English.
- `nl_proof_sketch`: the natural argument a mathematician would give — the intended idea.
- `legibility` (0-100): how DIRECTLY the actual Lean proof follows that natural argument. Be
  DISCRIMINATING — do not default to high. 90-100 only when the Lean proof transparently mirrors the
  math step for step. Drop well below that when the proof is convoluted, indirect, or hides the idea
  relative to the clean argument: heavy bespoke `rw` chains, metavariable gymnastics, redundant case
  work, an opaque one-shot `grind`/`simp` that buries the real case split, or a `calc` that hides why
  it works. Judge the PROOF's transparency against the idea, having actually read the full proof.
- `divergence`: one sentence on where/why the Lean proof departs from or obscures the natural argument
  — empty string only if the proof genuinely follows the idea directly."""

DISTILL_USER = """## PR #{pr_number} — {title}

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

## Your task

For each non-trivial declaration this PR adds or changes, READ its full proof in `target/`, understand
the intended argument, and judge how directly the Lean proof follows it. Then call `{submit_tool_name}`
exactly once with `pr_summary` and `declarations` (one entry per declaration with `name`,
`nl_statement`, `nl_proof_sketch`, `legibility`, `divergence`). Be discriminating with legibility —
reserve high scores for proofs that transparently mirror the math."""


class PRDistillResult(BaseTaskResult):
    """The PR distillation artifact (mirrors distillation.PRDistillation)."""

    model_config = ConfigDict()

    pr_number: int
    pr_summary: str = ""
    declarations: List[Dict[str, Any]] = Field(default_factory=list)


class LeanPRReviewDistillTask(BasePRReviewTask):
    """Workspace-grounded distillation — reads full proofs, emits the PRDistillation artifact."""

    task_type = "lean_pr_review_distill"
    data_class = BasePRReviewData
    task_config_class = BasePRReviewConfig
    task_result_class = PRDistillResult

    def _get_prompts(self, version: str) -> Tuple[str, str]:
        return DISTILL_SYSTEM, DISTILL_USER

    async def create_user_prompt(self) -> str:
        _system, user_template = self._get_prompts(self.config.task_config.prompt_version)
        changed = "\n".join(f"  - `{p}`" for p in self.data.changed_files) or "  (none listed)"
        submit_tool_name = f"{self.config.mcp_server_name}submit_distillation"
        return user_template.format(
            pr_number=self.data.pr_number, title=self.data.pr_title,
            description=self.data.pr_description.strip() or "(no description provided)",
            diff=self.data.diff, changed_files=changed,
            tool_summary=self._tool_summary(), submit_tool_name=submit_tool_name,
        )

    async def register_task_tools(self, mcp) -> None:
        @mcp.tool(
            description=(
                "Submit the PR distillation. Call exactly once when done, after reading the proofs. "
                "A text-only response is INVALID."
            )
        )
        async def submit_distillation(
            declarations: Annotated[List[Dict[str, Any]], Field(
                description=(
                    "One entry per non-trivial changed declaration: {name, nl_statement, "
                    "nl_proof_sketch, legibility (0-100 int), divergence}."
                )
            )] = [],
            pr_summary: Annotated[str, Field(description="One sentence on what the PR does.", default="")] = "",
        ) -> Dict[str, Any]:
            self.logger.info("submit_distillation: %d declarations", len(declarations or []))
            try:
                normalized = self._normalize_declarations(declarations or [])
                result = self.create_result(
                    success=True, score=1.0, pr_number=self.data.pr_number,
                    pr_summary=pr_summary or "", declarations=normalized,
                )
                if self.termination_callback:
                    try:
                        await self.termination_callback(result)
                    except Exception as exc:  # noqa: BLE001
                        self.logger.warning("Failed to trigger termination: %s", exc)
                return {
                    "evaluation_result": EvaluationResult(
                        success=True, score=1.0, message=f"Distillation recorded: {len(normalized)} decls."),
                    "message": "Distillation submitted",
                }
            except Exception:  # noqa: BLE001
                import traceback
                self.logger.error("submit_distillation failed: %s", traceback.format_exc())
                return {
                    "evaluation_result": EvaluationResult(success=False, score=0.0, message="submit failed"),
                    "message": "Submit failed",
                }

    @staticmethod
    def _normalize_declarations(decls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for raw in decls:
            if not isinstance(raw, dict):
                continue
            name = str(raw.get("name") or "").strip()
            if not name:
                continue
            try:
                legib = int(float(raw.get("legibility")))
            except (ValueError, TypeError):
                legib = 50
            out.append({
                "name": name,
                "nl_statement": str(raw.get("nl_statement") or ""),
                "nl_proof_sketch": str(raw.get("nl_proof_sketch") or ""),
                "legibility": max(0, min(100, legib)),
                "divergence": str(raw.get("divergence") or ""),
            })
        return out


register_task("lean_pr_review_distill", LeanPRReviewDistillTask)
