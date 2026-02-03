"""Lean utility functions

Contains LSP utility functions and Lean code parsing/formatting functions.
"""

from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from leanclient import LeanLSPClient


def find_project_path(file_path: Path) -> Optional[Path]:
    """
    Find Lean project path (search upwards for lean-toolchain file)

    Args:
        file_path: File path

    Returns:
        Project root directory path, None if not found
    """
    current = file_path.parent if file_path.is_file() else file_path

    while current != current.parent:
        if (current / "lean-toolchain").exists():
            return current
        current = current.parent

    return None


def setup_lean_client(project_path: Path) -> LeanLSPClient:
    """
    Set up Lean LSP client

    Args:
        project_path: Lean project path

    Returns:
        Lean LSP client instance
    """
    return LeanLSPClient(
        project_path,
        initial_build=False,
        prevent_cache_get=False
    )


def find_position_by_content(
    file_content: str,
    line: int,
    content_snippet: str
) -> Optional[Tuple[int, int]]:
    """
    Find content snippet in specified line, return (line_0indexed, character) position

    Args:
        file_content: File content
        line: Line number (1-indexed)
        content_snippet: Content snippet to find

    Returns:
        (line_idx, char_idx) or None
    """
    lines = file_content.splitlines()
    line_idx = line - 1

    if line_idx < 0 or line_idx >= len(lines):
        return None

    line_text = lines[line_idx]
    char_idx = line_text.find(content_snippet)

    if char_idx == -1:
        return None

    return (line_idx, char_idx)


def get_line_context(
    file_content: str,
    line: int,
    context_lines: int = 3
) -> Dict[str, Any]:
    """
    Get context around specified line

    Args:
        file_content: File content
        line: Line number (1-indexed)
        context_lines: Number of context lines

    Returns:
        {
            "target_line": str,
            "context": [{"line_number": int, "content": str}, ...]
        }
    """
    lines = file_content.splitlines()
    line_idx = line - 1

    if line_idx < 0 or line_idx >= len(lines):
        return {"target_line": "", "context": []}

    start = max(0, line_idx - context_lines)
    end = min(len(lines), line_idx + context_lines + 1)

    return {
        "target_line": lines[line_idx],
        "context": [
            {"line_number": i + 1, "content": lines[i]}
            for i in range(start, end)
        ]
    }


def extract_goals_list(goal_response: Optional[Dict]) -> List[str]:
    """Extract goals list from LSP response"""
    if goal_response is None:
        return []
    return goal_response.get("goals", [])


def extract_range(content: str, range_dict: Dict) -> str:
    """Extract range from content - reuse lean-lsp-mcp implementation"""
    from lean_lsp_mcp.utils import extract_range as lsp_extract_range
    return lsp_extract_range(content, range_dict)


def filter_diagnostics_by_position(
    diagnostics: List[Dict],
    line: int,
    column: Optional[int]
) -> List[Dict]:
    """Filter diagnostics at specified position - reuse lean-lsp-mcp implementation"""
    from lean_lsp_mcp.utils import filter_diagnostics_by_position as lsp_filter
    return lsp_filter(diagnostics, line, column)


def format_diagnostics(diagnostics: List[Dict]) -> List[Dict[str, Any]]:
    """
    Format diagnostic information

    Args:
        diagnostics: LSP diagnostics list

    Returns:
        Formatted diagnostics list
    """
    DIAGNOSTIC_SEVERITY = {1: "error", 2: "warning", 3: "info", 4: "hint"}

    result = []
    for diag in diagnostics:
        r = diag.get("fullRange", diag.get("range"))
        if not r:
            continue

        severity_int = diag.get("severity", 1)
        result.append({
            "line": r["start"]["line"] + 1,
            "column": r["start"]["character"] + 1,
            "severity": DIAGNOSTIC_SEVERITY.get(severity_int, f"unknown({severity_int})"),
            "message": diag.get("message", "")
        })

    return result
