"""Isabelle conjecturing task."""

import re
import traceback
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Literal

import aiofiles
from pydantic import ConfigDict, Field, field_validator

from ape.tasks.base import BaseTaskConfig, BaseTaskResult, EvaluationResult, register_task
from ape.tasks.isabelle_tasks.base import BaseIsabelleTask, BaseIsabelleTaskData
from ape.tasks.isabelle_tasks.utils import validate_submission_params
from ape.toolkits.execute.isabelle.core import IsabelleVerificationEngine

if TYPE_CHECKING:
    from ape.scaffolds.config import BaseScaffoldConfig
    import logging


class IsabelleConjecturingConfig(BaseTaskConfig):
    """Configuration for Isabelle conjecturing tasks."""

    allow_sorry: bool = True
    terminate_on_submission: bool = False
    max_validation_messages: int = 20
    draft_filename: str = "conjecture.txt"
    enabled_tools: Optional[List[str]] = [
        "file_read",
        "file_search",
        "content_search",
        "file_write",
        "file_edit",
        "file_multi_edit",
        "file_diff",
    ]


class IsabelleConjecturingData(BaseIsabelleTaskData):
    """Data model for Isabelle conjecturing tasks."""

    task_type: Literal["isabelle_conjecturing"] = Field(
        default="isabelle_conjecturing",
        description="Task type identifier",
    )
    symbols: List[str] = Field(
        ...,
        min_length=1,
        description="Symbols that must appear in the conjecture",
    )
    imports: List[str] = Field(
        default_factory=lambda: ["Main"],
        min_length=1,
        description="Imports used when wrapping a conjecture snippet into a temporary theory",
    )
    task_description: Optional[str] = Field(
        default=None,
        description="Optional natural-language guidance for the conjecture",
    )
    theory_prelude: Optional[str] = Field(
        default=None,
        description="Optional Isabelle text inserted before the submitted conjecture snippet",
    )
    conjecture_name: str = Field(
        default="generated_conjecture",
        description="Suggested conjecture name for draft templates",
    )
    expected_conjecture_name: Optional[str] = Field(
        default=None,
        description="Optional expected theorem name used for exact-match evaluation",
    )
    expected_conjecture_statement: Optional[str] = Field(
        default=None,
        description="Optional expected proposition used for exact-match evaluation",
    )

    @field_validator("symbols")
    @classmethod
    def validate_symbols(cls, value: List[str]) -> List[str]:
        """Require non-empty trimmed symbols."""
        cleaned = [symbol.strip() for symbol in value if symbol and symbol.strip()]
        if not cleaned:
            raise ValueError("symbols must contain at least one non-empty symbol")
        return cleaned

    @field_validator("imports")
    @classmethod
    def validate_imports(cls, value: List[str]) -> List[str]:
        """Require non-empty trimmed imports."""
        cleaned = [item.strip() for item in value if item and item.strip()]
        if not cleaned:
            raise ValueError("imports must contain at least one non-empty import")
        return cleaned

    @field_validator("expected_conjecture_name", "expected_conjecture_statement")
    @classmethod
    def validate_optional_expected_text(cls, value: Optional[str]) -> Optional[str]:
        """Trim optional exact-match evaluation targets."""
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class IsabelleConjecturingResult(BaseTaskResult):
    """Result model for Isabelle conjecturing tasks."""

    model_config = ConfigDict()

    conjecture_code: str = Field(..., description="Submitted conjecture content")
    validation_status: str = Field(default="", description="Validation status summary")
    compiled_successfully: bool = Field(
        default=False,
        description="Whether Isabelle accepted the submitted conjecture"
    )
    matched_expected_conjecture: Optional[bool] = Field(
        default=None,
        description="Whether the submitted conjecture matches the optional expected target"
    )
    submitted_conjecture_name: Optional[str] = Field(
        default=None,
        description="Extracted theorem name from the submitted conjecture"
    )
    submitted_conjecture_statement: Optional[str] = Field(
        default=None,
        description="Extracted proposition from the submitted conjecture"
    )


class IsabelleConjecturingTask(BaseIsabelleTask):
    """Task that asks the agent to generate a symbol-constrained Isabelle conjecture."""

    task_type = "isabelle_conjecturing"
    data_class = IsabelleConjecturingData
    task_config_class = IsabelleConjecturingConfig
    task_result_class = IsabelleConjecturingResult

    def __init__(self, data: IsabelleConjecturingData, config: "BaseScaffoldConfig"):
        """Initialize the task."""
        super().__init__(data, config)
        self.draft_file_path: Optional[Path] = None

    async def setup(
        self,
        termination_callback,
        orchestrator_id: str,
        attempt_path: Optional[Path] = None,
    ) -> "logging.LoggerAdapter":
        """Set up workspaces and create an initial draft file in scratch."""
        logger = await super().setup(termination_callback, orchestrator_id, attempt_path)
        if not self.scratch_workspace or not self.scratch_workspace.path:
            raise RuntimeError("Scratch workspace not initialized for Isabelle conjecturing task")

        task_config: IsabelleConjecturingConfig = self.config.task_config
        draft_relative = Path(task_config.draft_filename)
        if draft_relative.is_absolute() or ".." in draft_relative.parts:
            raise ValueError("draft_filename must be a relative path inside scratch workspace")

        self.draft_file_path = self.scratch_workspace.path / draft_relative
        self.draft_file_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(self.draft_file_path, "w", encoding="utf-8") as handle:
            await handle.write(self._build_draft_template())

        self.logger.info(
            f"Initialized Isabelle conjecture draft at {self.draft_file_path.relative_to(self.scratch_workspace.path)}"
        )
        return logger

    def _build_draft_template(self) -> str:
        """Create an initial scratch template for the conjecture."""
        symbol_lines = "\n".join(f"  - {symbol}" for symbol in self.data.symbols)
        conjecture_name = re.sub(r"\W+", "_", self.data.conjecture_name).strip("_") or "generated_conjecture"
        prelude_block = ""
        if self.data.theory_prelude:
            prelude_block = (
                "\n(* Validation will insert the following prelude before your conjecture:\n"
                f"{self.data.theory_prelude.strip()}\n*)\n"
            )

        return (
            "(* Draft an Isabelle conjecture here.\n"
            "Required symbols (must appear literally):\n"
            f"{symbol_lines}\n"
            "You may submit either this snippet or a full theory file.\n"
            "For snippet submissions, `sorry` is allowed.\n"
            "*)\n"
            f"{prelude_block}\n"
            f"lemma {conjecture_name}:\n"
            '  "<replace with your conjecture>"\n'
            "  sorry\n"
        )

    async def create_user_prompt(self) -> str:
        """Create the user prompt for the conjecturing task."""
        from .prompt import ISABELLE_CONJECTURING_USER_PROMPT

        submit_tool_name = f"{self.config.mcp_server_name}submit_result"
        validate_tool_name = f"{self.config.mcp_server_name}validate_conjecture"
        draft_path = (
            f"scratch/{self.draft_file_path.relative_to(self.scratch_workspace.path)}"
            if self.draft_file_path and self.scratch_workspace and self.scratch_workspace.path
            else "scratch/conjecture.txt"
        )
        symbols_block = "\n".join(f"- `{symbol}`" for symbol in self.data.symbols)

        task_description_block = ""
        if self.data.task_description:
            task_description_block = (
                "<task_description>\n"
                f"{self.data.task_description.strip()}\n"
                "</task_description>\n\n"
            )

        theory_prelude_block = ""
        if self.data.theory_prelude:
            theory_prelude_block = (
                "\nAdditional theory text inserted before your snippet during validation:\n"
                "```isabelle\n"
                f"{self.data.theory_prelude.strip()}\n"
                "```\n"
            )

        return ISABELLE_CONJECTURING_USER_PROMPT.format(
            symbols_block=symbols_block,
            task_description_block=task_description_block,
            session_name=self.data.target_workspace.session_name,
            imports_line=" ".join(self.data.imports),
            draft_file_path=draft_path,
            theory_prelude_block=theory_prelude_block,
            validate_tool_name=validate_tool_name,
            submit_tool_name=submit_tool_name,
        )

    async def register_task_tools(self, mcp) -> None:
        """Register conjecture validation and submission tools."""
        from typing import Annotated
        from pydantic import Field

        @mcp.tool(
            description=(
                "Validate a conjecture candidate by staging it inside the target Isabelle session and "
                "running Isabelle process checks. Accepts either direct content or a workspace file path."
            )
        )
        async def validate_conjecture(
            conjecture_content: Annotated[Optional[str], Field(
                description="Conjecture snippet or full theory content to validate"
            )] = None,
            conjecture_file_path: Annotated[Optional[str], Field(
                description="Workspace file path containing the conjecture candidate, e.g. 'scratch/conjecture.txt'"
            )] = None,
        ) -> Dict[str, Any]:
            """Validate a conjecture candidate without submitting the final answer."""
            self.logger.info("Tool validate_conjecture: execution started")
            try:
                success, candidate_text, error_result = await validate_submission_params(
                    conjecture_content,
                    Path(conjecture_file_path) if conjecture_file_path else None,
                    self.workspaces_dir,
                )
                if not success:
                    return {
                        "evaluation_result": error_result,
                        "message": "Validation failed or not ready",
                    }

                evaluation_result, details = await self._evaluate_conjecture(candidate_text)
                self.logger.info(
                    f"Tool validate_conjecture: execution completed (score={evaluation_result.score})"
                )
                return {
                    "evaluation_result": evaluation_result,
                    "validation_details": details,
                    "message": "Validation completed",
                }
            except Exception:
                self.logger.error(
                    f"Isabelle conjecture validation failed: {traceback.format_exc()}"
                )
                evaluation_result = EvaluationResult(
                    success=False,
                    score=0.0,
                    message=traceback.format_exc(),
                )
                return {
                    "evaluation_result": evaluation_result,
                    "message": "Validation failed or not ready",
                }

        @mcp.tool(
            description=(
                "Submit your final Isabelle conjecture. Provide either content directly or a workspace file path. "
                "The conjecture must contain all required symbols and be accepted by Isabelle."
            )
        )
        async def submit_result(
            conjecture_content: Annotated[Optional[str], Field(
                description="Final conjecture snippet or full theory content"
            )] = None,
            conjecture_file_path: Annotated[Optional[str], Field(
                description="Workspace file path containing the final conjecture"
            )] = None,
            message: Annotated[str, Field(
                description="Optional message describing the conjecture",
                default="",
            )] = "",
        ) -> Dict[str, Any]:
            """Submit the final conjecture for evaluation."""
            del message
            self.logger.info("Tool submit_result: execution started")
            try:
                success, candidate_text, error_result = await validate_submission_params(
                    conjecture_content,
                    Path(conjecture_file_path) if conjecture_file_path else None,
                    self.workspaces_dir,
                )
                if not success:
                    return {
                        "evaluation_result": error_result,
                        "message": "Evaluation failed or not ready",
                    }

                evaluation_result, details = await self._evaluate_conjecture(candidate_text)

                should_terminate = (
                    self.should_terminate(evaluation_result)
                    or self.config.task_config.terminate_on_submission
                )
                if should_terminate and self.termination_callback:
                    custom_metrics = {
                        "compiled_successfully": (
                            1.0 if details.get("compiled_successfully") else 0.0
                        ),
                    }
                    if details.get("matched_expected_conjecture") is not None:
                        custom_metrics["matched_expected_conjecture"] = (
                            1.0 if details.get("matched_expected_conjecture") else 0.0
                        )
                    task_result = self.create_result(
                        success=evaluation_result.success,
                        score=evaluation_result.score,
                        conjecture_code=candidate_text,
                        validation_status=evaluation_result.message or "",
                        compiled_successfully=bool(details.get("compiled_successfully", False)),
                        matched_expected_conjecture=details.get("matched_expected_conjecture"),
                        submitted_conjecture_name=details.get("submitted_conjecture_name"),
                        submitted_conjecture_statement=details.get("submitted_conjecture_statement"),
                        custom_metrics=custom_metrics,
                    )
                    await self.termination_callback(task_result)

                self.logger.info(
                    f"Tool submit_result: execution completed (score={evaluation_result.score})"
                )
                return {
                    "evaluation_result": evaluation_result,
                    "validation_details": details,
                    "message": "Result submitted and evaluated",
                }
            except Exception:
                self.logger.error(
                    f"Isabelle conjecture evaluation failed: {traceback.format_exc()}"
                )
                evaluation_result = EvaluationResult(
                    success=False,
                    score=0.0,
                    message=traceback.format_exc(),
                )
                return {
                    "evaluation_result": evaluation_result,
                    "message": "Evaluation failed or not ready",
                }

    async def _evaluate_conjecture(
        self,
        conjecture_code: str,
    ) -> tuple[EvaluationResult, Dict[str, Any]]:
        """Evaluate a conjecture candidate."""
        task_config: IsabelleConjecturingConfig = self.config.task_config
        stripped_code = self._strip_isabelle_comments(conjecture_code)
        missing_symbols = [
            symbol for symbol in self.data.symbols
            if symbol not in stripped_code
        ]

        details: Dict[str, Any] = {
            "missing_symbols": missing_symbols,
            "used_sorry": bool(re.search(r"\bsorry\b", stripped_code)),
            "compiled_successfully": False,
        }

        submitted_name, submitted_statement = self._extract_named_conjecture(conjecture_code)
        details["submitted_conjecture_name"] = submitted_name
        details["submitted_conjecture_statement"] = submitted_statement
        details["matched_expected_conjecture"] = self._matches_expected_conjecture(
            submitted_name,
            submitted_statement,
        )

        if missing_symbols:
            return EvaluationResult(
                success=True,
                score=0.0,
                message=(
                    "Conjecture is missing required symbols: "
                    + ", ".join(missing_symbols)
                ),
            ), details

        if not task_config.allow_sorry and details["used_sorry"]:
            return EvaluationResult(
                success=True,
                score=0.0,
                message="This task configuration does not allow `sorry` in the final conjecture.",
            ), details

        try:
            verification_result = await self._stage_and_validate_conjecture(conjecture_code)
        except Exception:
            return EvaluationResult(
                success=False,
                score=0.0,
                message=traceback.format_exc(),
            ), details

        details["verification_result"] = verification_result
        details["staged_theory_name"] = verification_result.get("theory_name")
        details["compiled_successfully"] = bool(verification_result.get("success", False))

        if verification_result.get("success", False):
            if details["matched_expected_conjecture"] is False:
                return EvaluationResult(
                    success=True,
                    score=0.0,
                    message=self._format_expected_mismatch(details),
                ), details

            return EvaluationResult(
                success=True,
                score=1.0,
                message="Conjecture validated successfully in Isabelle.",
            ), details

        return EvaluationResult(
            success=True,
            score=0.0,
            message=self._format_verification_failure(verification_result),
        ), details

    async def _stage_and_validate_conjecture(self, conjecture_code: str) -> Dict[str, Any]:
        """Write a temporary theory into the target session and verify it."""
        if not self.target_workspace or not self.target_workspace.path:
            raise RuntimeError("Target Isabelle workspace is not initialized")

        session_dir = self.target_workspace.effective_working_directory.resolve()
        session_dir.mkdir(parents=True, exist_ok=True)

        theory_name = f"APE_Conjecture_{uuid.uuid4().hex[:12]}"
        theory_content = self._prepare_theory_content(conjecture_code, theory_name)
        theory_path = session_dir / f"{theory_name}.thy"

        async with aiofiles.open(theory_path, "w", encoding="utf-8") as handle:
            await handle.write(theory_content)

        try:
            engine_config = self.config.tools_config.isabelle_verify.model_copy(
                update={"quick_and_dirty": self.config.task_config.allow_sorry}
            )
            verification_engine = IsabelleVerificationEngine(
                engine_config,
                self.logger,
            )
            return await verification_engine.verify_file(
                file_path=theory_path,
                workspace=self.target_workspace,
                max_messages=self.config.task_config.max_validation_messages,
            )
        finally:
            if theory_path.exists():
                theory_path.unlink()

    def _prepare_theory_content(self, conjecture_code: str, theory_name: str) -> str:
        """Normalize the submission into a temporary Isabelle theory."""
        if re.search(r"^\s*theory\b", conjecture_code, re.MULTILINE):
            rewritten = re.sub(
                r"^\s*theory\s+\S+",
                f"theory {theory_name}",
                conjecture_code,
                count=1,
                flags=re.MULTILINE,
            )
            if rewritten.endswith("\n"):
                return rewritten
            return rewritten + "\n"

        parts = [
            f"theory {theory_name}",
            "imports " + " ".join(self.data.imports),
            "begin",
            "",
        ]

        if self.data.theory_prelude:
            parts.extend([self.data.theory_prelude.strip(), ""])

        parts.extend([
            conjecture_code.strip(),
            "",
            "end",
            "",
        ])
        return "\n".join(parts)

    def _strip_isabelle_comments(self, text: str) -> str:
        """Remove simple Isabelle block comments for symbol checks."""
        return re.sub(r"\(\*.*?\*\)", "", text, flags=re.DOTALL)

    def _format_verification_failure(self, verification_result: Dict[str, Any]) -> str:
        """Format Isabelle verification feedback for the model."""
        message_parts = [
            verification_result.get("message", "Isabelle validation failed."),
        ]

        errors = [item.get("data", "") for item in verification_result.get("errors", [])]
        warnings = [item.get("data", "") for item in verification_result.get("warnings", [])]

        if errors:
            message_parts.append("Errors:\n" + "\n".join(f"- {item}" for item in errors))
        if warnings:
            message_parts.append("Warnings:\n" + "\n".join(f"- {item}" for item in warnings))

        return "\n\n".join(part for part in message_parts if part)

    def _extract_named_conjecture(
        self,
        conjecture_code: str,
    ) -> tuple[Optional[str], Optional[str]]:
        """Extract a simple theorem name and proposition from the submission."""
        clean = self._strip_isabelle_comments(conjecture_code)
        match = re.search(
            r"\b(?:lemma|theorem)\s+([A-Za-z_][A-Za-z0-9_']*)\s*:\s*\"([^\"]+)\"",
            clean,
            flags=re.DOTALL,
        )
        if not match:
            return None, None
        return match.group(1), match.group(2)

    def _normalize_statement(self, statement: Optional[str]) -> Optional[str]:
        """Normalize theorem propositions for exact-match comparison."""
        if statement is None:
            return None
        return re.sub(r"\s+", "", statement)

    def _matches_expected_conjecture(
        self,
        submitted_name: Optional[str],
        submitted_statement: Optional[str],
    ) -> Optional[bool]:
        """Return whether the submission matches the optional expected target."""
        expected_name = self.data.expected_conjecture_name
        expected_statement = self.data.expected_conjecture_statement

        if expected_name is None and expected_statement is None:
            return None

        name_matches = (
            True if expected_name is None else submitted_name == expected_name
        )
        statement_matches = (
            True
            if expected_statement is None
            else self._normalize_statement(submitted_statement)
            == self._normalize_statement(expected_statement)
        )
        return name_matches and statement_matches

    def _format_expected_mismatch(self, details: Dict[str, Any]) -> str:
        """Explain an exact-match mismatch after successful compilation."""
        expected_parts: List[str] = []
        if self.data.expected_conjecture_name is not None:
            expected_parts.append(f"name={self.data.expected_conjecture_name}")
        if self.data.expected_conjecture_statement is not None:
            expected_parts.append(
                f'statement="{self.data.expected_conjecture_statement}"'
            )

        found_parts: List[str] = []
        if details.get("submitted_conjecture_name") is not None:
            found_parts.append(f"name={details['submitted_conjecture_name']}")
        if details.get("submitted_conjecture_statement") is not None:
            found_parts.append(
                f'statement="{details["submitted_conjecture_statement"]}"'
            )

        expected_summary = ", ".join(expected_parts) if expected_parts else "unknown"
        found_summary = ", ".join(found_parts) if found_parts else "could not parse theorem head"
        return (
            "Conjecture compiled successfully but does not match the expected target.\n\n"
            f"Expected: {expected_summary}\n"
            f"Found: {found_summary}"
        )

    def create_result(
        self,
        success: bool,
        score: float,
        conjecture_code: str,
        validation_status: str = "",
        compiled_successfully: bool = False,
        matched_expected_conjecture: Optional[bool] = None,
        submitted_conjecture_name: Optional[str] = None,
        submitted_conjecture_statement: Optional[str] = None,
        **kwargs,
    ) -> IsabelleConjecturingResult:
        """Create the task result."""
        return IsabelleConjecturingResult(
            task_id=self.data.task_id,
            task_type=self.task_type,
            global_index=self.data.global_index,
            success=success,
            score=score,
            conjecture_code=conjecture_code,
            validation_status=validation_status,
            compiled_successfully=compiled_successfully,
            matched_expected_conjecture=matched_expected_conjecture,
            submitted_conjecture_name=submitted_conjecture_name,
            submitted_conjecture_statement=submitted_conjecture_statement,
            **kwargs,
        )

    @classmethod
    def is_best_result(cls, result: BaseTaskResult) -> bool:
        """Treat successful Isabelle validation as an optimal result."""
        return result.success and result.score == 1.0


register_task("isabelle_conjecturing", IsabelleConjecturingTask)
