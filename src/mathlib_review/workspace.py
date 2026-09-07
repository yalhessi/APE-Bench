"""Running a tool inside a review workspace.

Two functions, and they were private names in `pr_review_v4/evidence.py` that four modules
across two generations imported anyway:

    opportunity_executor      from .evidence import _tool_env
    operators/canonical_api   from ..evidence import _tool_env
    v4 candidates            from .evidence import _tool_env as evidence_tool_env
    pr_review_v5/patchset     from src.mathlib_review.evidence.evidence import _run

A leading underscore is a claim that a name is nobody else's business, and four callers had
already decided otherwise. That is not a naming quibble: `evidence.py` is where the evidence
chain lives, and it cannot be refactored without breaking a coordinated-patch verifier in
another package that has no reason to care about evidence at all.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Dict, List

#: Long enough for a Lean elaboration of a single file, short enough that a hung tool fails
#: the job rather than the run.
DEFAULT_TIMEOUT = 180


def tool_env(workspace: Path) -> Dict[str, str]:
    """Recover project-local elan tools when the orchestrator supplies a minimal PATH.

    Searched from the workspace upward and then from the home directory, because a review
    workspace is a symlink farm over a shared snapshot and the toolchain may be installed at
    any level above it.
    """

    env = os.environ.copy()
    roots = [workspace, *workspace.parents, Path.home()]
    tool_dirs = [root / ".elan" / "bin" for root in roots if (root / ".elan" / "bin").is_dir()]
    if tool_dirs:
        env["PATH"] = os.pathsep.join([*(str(path) for path in tool_dirs), env.get("PATH", "")])
    return env


def run(command: List[str], workspace: Path, timeout: int = DEFAULT_TIMEOUT):
    """One subprocess call, in the workspace, with the toolchain on PATH."""

    return subprocess.run(command, cwd=workspace, text=True, capture_output=True,
                          timeout=timeout, env=tool_env(workspace))
