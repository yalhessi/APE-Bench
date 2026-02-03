"""
Lean Tasks Utilities Module.

Provides common utility functions for Lean task processing and evaluation.
"""

import time
import traceback
import aiofiles
from typing import Optional, Tuple, TYPE_CHECKING
from pathlib import Path
from ape.tasks.base import EvaluationResult

if TYPE_CHECKING:
    import logging

async def get_final_code(
    final_code_content: Optional[str],
    final_code_file_path: Optional[Path],
    workspaces_dir: Path,
    logger: Optional['logging.LoggerAdapter'] = None
) -> Tuple[bool, str, Optional[str]]:
    """Get final code from content or file path.

    Args:
        final_code_content: Code content provided directly.
        final_code_file_path: File path relative to workspaces_dir (e.g., 'scratch/solution.lean').
        workspaces_dir: Workspaces directory root path.
        logger: Optional logger instance.

    Returns:
        Tuple of (success, message_or_code, final_code_or_none):
        - On success: (True, final_code, final_code)
        - On failure: (False, error_message, None)
    """
    if not final_code_content and not final_code_file_path:
        return False, "Either final_code_content or final_code_file_path must be provided", None

    if final_code_content and final_code_file_path:
        return False, "Only one of final_code_content or final_code_file_path can be provided", None

    if final_code_content:
        if not final_code_content.strip():
            return False, "Final code cannot be empty", None
        return True, final_code_content, final_code_content

    if final_code_file_path:
        # Resolve file path
        file_path = (workspaces_dir / final_code_file_path).resolve()

        # Security check: ensure path is within workspaces_dir
        if not file_path.is_relative_to(workspaces_dir):
            return False, f"File path outside workspaces directory: {final_code_file_path}", None

        if not file_path.exists():
            return False, f"File not found: {final_code_file_path}", None

        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                final_code = await f.read()
        except Exception as e:
            if logger:
                logger.error(f"Failed to read file {final_code_file_path}: {traceback.format_exc()}")
            return False, f"Failed to read file {final_code_file_path}: {traceback.format_exc()}", None

        if not final_code.strip():
            return False, "Final code cannot be empty", None

        return True, final_code, final_code

    return False, "Internal error: no valid input provided", None


async def validate_final_code_params(
    final_code_content: Optional[str],
    final_code_file_path: Optional[Path],
    workspaces_dir: Path,
    start_time: Optional[float] = None
) -> Tuple[bool, Optional[str], Optional['EvaluationResult']]:
    """Validate and retrieve final code parameters.

    Args:
        final_code_content: Code content provided directly.
        final_code_file_path: File path with workspace prefix.
        workspaces_dir: Workspaces directory root path.
        start_time: Optional start time for timing.

    Returns:
        Tuple of (success, final_code_or_none, error_result_or_none):
        - On success: (True, final_code, None)
        - On failure: (False, None, EvaluationResult)
    """
    if start_time is None:
        start_time = time.time()

    success, result, final_code = await get_final_code(
        final_code_content, final_code_file_path, workspaces_dir
    )

    if not success:
        error_result = EvaluationResult(
            success=False,
            score=0.0,
            message=result
        )
        return False, None, error_result

    return True, final_code, None

