"""Python utility functions"""

from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple


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
        range_info = diag.get("range")
        if not range_info:
            continue

        severity_int = diag.get("severity", 1)
        result.append({
            "line": range_info["start"]["line"] + 1,
            "column": range_info["start"]["character"] + 1,
            "severity": DIAGNOSTIC_SEVERITY.get(severity_int, f"unknown({severity_int})"),
            "message": diag.get("message", "")
        })

    return result


def extract_range_content(
    file_content: str,
    range_dict: Dict[str, Any]
) -> str:
    """
    Extract text content from file within specified range

    Args:
        file_content: File content
        range_dict: LSP range object {"start": {"line": int, "character": int}, "end": {...}}

    Returns:
        Extracted text content
    """
    lines = file_content.splitlines(keepends=True)

    start_line = range_dict["start"]["line"]
    start_char = range_dict["start"]["character"]
    end_line = range_dict["end"]["line"]
    end_char = range_dict["end"]["character"]

    if start_line == end_line:
        # Single line
        line_text = lines[start_line] if start_line < len(lines) else ""
        return line_text[start_char:end_char]
    else:
        # Multiple lines
        result = []
        # First line
        if start_line < len(lines):
            result.append(lines[start_line][start_char:])
        # Middle lines
        for i in range(start_line + 1, end_line):
            if i < len(lines):
                result.append(lines[i])
        # Last line
        if end_line < len(lines):
            result.append(lines[end_line][:end_char])

        return ''.join(result)
