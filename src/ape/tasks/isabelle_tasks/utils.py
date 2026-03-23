"""Utilities for Isabelle task submissions."""

import time
import traceback
from pathlib import Path
from typing import Optional, Tuple, TYPE_CHECKING

import aiofiles

from ape.tasks.base import EvaluationResult

if TYPE_CHECKING:
    import logging


async def get_submission_text(
    submission_content: Optional[str],
    submission_file_path: Optional[Path],
    workspaces_dir: Path,
    logger: Optional["logging.LoggerAdapter"] = None,
) -> Tuple[bool, str, Optional[str]]:
    """Get submission text from content or file path."""
    if not submission_content and not submission_file_path:
        return False, "Either submission_content or submission_file_path must be provided", None

    if submission_content and submission_file_path:
        return False, "Only one of submission_content or submission_file_path can be provided", None

    if submission_content:
        if not submission_content.strip():
            return False, "Submission cannot be empty", None
        return True, submission_content, submission_content

    file_path = (workspaces_dir / submission_file_path).resolve()
    if not file_path.is_relative_to(workspaces_dir.resolve()):
        return False, f"File path outside workspaces directory: {submission_file_path}", None

    if not file_path.exists():
        return False, f"File not found: {submission_file_path}", None

    try:
        async with aiofiles.open(file_path, "r", encoding="utf-8") as handle:
            submission_text = await handle.read()
    except Exception:
        if logger:
            logger.error(
                f"Failed to read file {submission_file_path}: {traceback.format_exc()}"
            )
        return (
            False,
            f"Failed to read file {submission_file_path}: {traceback.format_exc()}",
            None,
        )

    if not submission_text.strip():
        return False, "Submission cannot be empty", None

    return True, submission_text, submission_text


async def validate_submission_params(
    submission_content: Optional[str],
    submission_file_path: Optional[Path],
    workspaces_dir: Path,
    start_time: Optional[float] = None,
) -> Tuple[bool, Optional[str], Optional[EvaluationResult]]:
    """Validate and retrieve submission text parameters."""
    if start_time is None:
        start_time = time.time()

    del start_time

    success, result, submission_text = await get_submission_text(
        submission_content,
        submission_file_path,
        workspaces_dir,
    )

    if not success:
        return False, None, EvaluationResult(
            success=False,
            score=0.0,
            message=result,
        )

    return True, submission_text, None
