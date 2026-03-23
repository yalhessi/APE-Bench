"""Core Isabelle verification helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from ape.tasks.models import IsabelleWorkspaceInfo
from ape.toolkits.execute.lean.utils.process_ops import run_command
from ape.utils.logging import create_logger

from .config import IsabelleVerifyToolConfig


def _truncate_messages(
    errors: List[Dict[str, Any]],
    warnings: List[Dict[str, Any]],
    infos: List[Dict[str, Any]],
    max_messages: Optional[int],
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], bool, int]:
    """Truncate messages with error-first priority."""
    total_messages = len(errors) + len(warnings) + len(infos)
    if max_messages is None or max_messages <= 0:
        return errors, warnings, infos, False, total_messages

    remaining = max_messages
    truncated = False

    if len(errors) >= remaining:
        truncated = len(errors) > remaining or len(warnings) > 0 or len(infos) > 0
        return errors[:remaining], [], [], truncated, total_messages

    remaining -= len(errors)

    if len(warnings) >= remaining:
        truncated = len(warnings) > remaining or len(infos) > 0
        return errors, warnings[:remaining], [], truncated, total_messages

    remaining -= len(warnings)
    if len(infos) > remaining:
        truncated = True
        infos = infos[:remaining]

    return errors, warnings, infos, truncated, total_messages


def _classify_isabelle_output(stdout: str, stderr: str) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Classify Isabelle output into error, warning, and info buckets."""
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    infos: List[Dict[str, Any]] = []

    for raw_line in (stdout.splitlines() + stderr.splitlines()):
        line = raw_line.strip()
        if not line:
            continue

        lower = line.lower()
        message = {"severity": "info", "data": line, "code_line": None, "pos": None}

        if line.startswith("***") or "error" in lower or "exception" in lower or "failed" in lower:
            message["severity"] = "error"
            errors.append(message)
        elif "warning" in lower:
            message["severity"] = "warning"
            warnings.append(message)
        else:
            infos.append(message)

    return errors, warnings, infos


def _derive_theory_name(file_path: Path, session_dir: Path) -> str:
    """Convert a theory file path into the theory name Isabelle expects."""
    relative_path = file_path.resolve().relative_to(session_dir.resolve())
    if relative_path.suffix != ".thy":
        raise ValueError(f"Expected a .thy file, got: {file_path}")
    return relative_path.with_suffix("").as_posix()


class IsabelleVerificationEngine:
    """Lightweight Isabelle verification engine based on `isabelle process`."""

    def __init__(
        self,
        config: Optional[IsabelleVerifyToolConfig] = None,
        logger: Optional['logging.LoggerAdapter'] = None,
    ):
        self.config = config or IsabelleVerifyToolConfig()
        self.logger = logger or create_logger()

    async def verify_file(
        self,
        file_path: Path,
        workspace: IsabelleWorkspaceInfo,
        max_messages: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Verify a theory file inside an Isabelle session."""
        if not workspace.path:
            raise ValueError("Workspace path is not initialized")

        session_dir = workspace.effective_working_directory.resolve()
        theory_path = file_path.resolve()

        if not theory_path.exists():
            raise FileNotFoundError(f"Theory file not found: {theory_path}")
        if not theory_path.is_relative_to(workspace.path.resolve()):
            raise ValueError(f"Theory file is outside workspace root: {theory_path}")
        if not theory_path.is_relative_to(session_dir):
            raise ValueError(
                f"Theory file must be inside the Isabelle working directory {session_dir}, got: {theory_path}"
            )

        root_file = session_dir / "ROOT"
        roots_file = session_dir / "ROOTS"
        if not root_file.exists() and not roots_file.exists():
            raise ValueError(
                f"Isabelle working directory must contain ROOT or ROOTS: {session_dir}"
            )

        theory_name = _derive_theory_name(theory_path, session_dir)
        command = [
            self.config.isabelle_bin,
            "process",
            "-d",
            str(session_dir),
            "-l",
            workspace.session_name,
        ]
        if self.config.quick_and_dirty:
            command.extend(["-o", "quick_and_dirty=true"])
        command.extend([
            "-T",
            theory_name,
        ])

        stdout, stderr, return_code = await run_command(
            command,
            cwd=session_dir,
            timeout=self.config.timeout,
            max_memory_gb=self.config.max_memory_gb,
            operation_name=f"isabelle process {workspace.session_name}:{theory_name}",
            logger=self.logger,
        )

        errors, warnings, infos = _classify_isabelle_output(stdout, stderr)
        errors, warnings, infos, truncated, total_messages = _truncate_messages(
            errors,
            warnings,
            infos,
            self.config.max_messages if max_messages is None else max_messages,
        )

        success = return_code == 0 and len(errors) == 0
        response: Dict[str, Any] = {
            "success": success,
            "errors": errors,
            "warnings": warnings,
            "infos": infos,
            "raw_output": stdout,
            "raw_stderr": stderr,
            "exit_code": return_code,
            "session_name": workspace.session_name,
            "theory_name": theory_name,
        }

        if truncated:
            response["messages_truncated"] = True
            response["total_messages_before_truncation"] = total_messages

        if return_code == -15:
            response["timeout"] = True
            response["message"] = f"Isabelle verification timed out after {self.config.timeout}s."
        elif success:
            response["message"] = "Isabelle verification completed successfully"
        else:
            if "Missing heap image for session" in stderr:
                response["message"] = (
                    "Isabelle verification failed because the session heap is missing. "
                    "Use `isabelle build` for that session before relying on `isabelle process`."
                )
            else:
                response["message"] = "Isabelle verification failed"

        return response
