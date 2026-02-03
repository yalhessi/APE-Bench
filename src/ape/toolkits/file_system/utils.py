"""
File System Utilities - Common tool functions for file system

Contains common tool functions for file system, independent of language.
Uses asynchronous IO to avoid blocking the event loop.
"""

import re
import difflib
import traceback
import glob
import aiofiles
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    import logging
    from .config import FileSystemToolConfig


# ===== VS Code integration functions =====

def open_file_in_vscode(file_path: Path, line: Optional[int] = None, enabled: bool = True, logger: Optional['logging.LoggerAdapter'] = None) -> None:
    """
    Open file in VS Code

    Args:
        file_path: File absolute path
        line: Optional line number (1-indexed)
        enabled: Whether to enable VS Code open function (default True)
        logger: Optional logger instance
    """
    if not enabled:
        return

    try:
        import subprocess

        # Build command
        if line is not None:
            cmd = ["code", "--reuse-window", "--goto", f"{file_path}:{line}"]
        else:
            cmd = ["code", "--reuse-window", "--goto", str(file_path)]

        # Non-blocking execution, no waiting for result
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

        if logger:
            logger.debug(f"Opened file in VS Code: {file_path}" + (f":{line}" if line else ""))
    except Exception as e:
        # Opening file failure should not affect tool execution, only record debug log
        if logger:
            logger.debug(f"Failed to open file in VS Code: {e}")


def generate_unified_diff(left_content: str, right_content: str, 
                         left_path: Path, right_path: Path, unified: int) -> str:
    """Generate unified difference format"""
    left_lines = left_content.splitlines(keepends=True)
    right_lines = right_content.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        left_lines,
        right_lines,
        fromfile=f"a/{left_path}",
        tofile=f"b/{right_path}",
        n=unified
    )
    
    return ''.join(diff)


def generate_word_diff(left_content: str, right_content: str, 
                      left_path: Path, right_path: Path) -> str:
    """Generate word level difference format"""
    left_words = left_content.split()
    right_words = right_content.split()
    
    diff = difflib.unified_diff(
        left_words,
        right_words,
        fromfile=f"a/{left_path}",
        tofile=f"b/{right_path}",
        lineterm=""
    )
    
    return '\n'.join(diff)


# Remove or comment out timeout_context function (lines 77-98)
# No longer need signal-based timeout

def search_content_with_timeout(content: str, pattern: str, use_regex: bool, timeout: float, 
                               A: Optional[int] = None, B: Optional[int] = None, C: Optional[int] = None,
                               max_matches: Optional[int] = None,
                               logger: Optional['logging.LoggerAdapter'] = None) -> List[Dict[str, Any]]:
    """
    Search pattern in file content, support context display
    
    Note: Timeout control should be implemented by caller through asyncio.wait_for
    
    Args:
        content: File content
        pattern: Search pattern
        use_regex: Whether to use regex
        timeout: Timeout time (seconds) - this parameter is retained for compatibility, but not used internally
        A: Number of lines after matched line
        B: Number of lines before matched line
        C: Number of lines before and after matched line (will override A and B)
        max_matches: Maximum number of matches to return (None means no limit)
        logger: Optional logger instance
        
    Returns:
        Matching result list, each result contains line number, content and context
    """
    lines = content.splitlines()
    matched_lines = set()
    
    # Determine context line number
    if C is not None:
        lines_after = lines_before = C
    else:
        lines_after = A if A is not None else 0
        lines_before = B if B is not None else 0
    
    # Find all matched line numbers
    if use_regex:
        try:
            regex = re.compile(pattern, re.MULTILINE)
            for line_num, line in enumerate(lines, 1):
                match = regex.search(line)
                # Only accept non-empty matches, avoid ≃* type patterns matching empty string causing all lines to be matched
                if match and match.group():
                    matched_lines.add(line_num)
        except re.error as e:
            if logger:
                logger.warning(f"Invalid regex pattern '{pattern}': {e}")
            # Fall back to simple string matching
            for line_num, line in enumerate(lines, 1):
                if pattern in line:
                    matched_lines.add(line_num)
    else:
        for line_num, line in enumerate(lines, 1):
            if pattern in line:
                matched_lines.add(line_num)
    
    # Build result for each match (includes context)
    matches = []
    for line_num in sorted(matched_lines):
        # Check if maximum match limit has been reached
        if max_matches is not None and len(matches) >= max_matches:
            break
        
        start_line = max(1, line_num - lines_before)
        end_line = min(len(lines), line_num + lines_after)
        
        # Build content with context
        context_content = []
        for i in range(start_line, end_line + 1):
            line_content = lines[i - 1]  # lines is 0-indexed
            context_content.append(f"{i:6d}|{line_content}")
        
        matches.append({
            "line_number": line_num,
            "content": "\n".join(context_content)
        })
    
    return matches


def add_line_numbers(content: str) -> str:
    """Add line numbers to content (generic fallback function)
    
    Args:
        content: Original content
        
    Returns:
        Content with line numbers, format: LINE_NUMBER|LINE_CONTENT
    """
    if not content:
        return ""
    
    lines = content.splitlines()
    return '\n'.join(f"{i:6d}|{line}" for i, line in enumerate(lines, 1))


def format_line_with_number(line_num: int, line_content: str) -> str:
    """Format single line content (with line number)

    Args:
        line_num: Line number (1-indexed)
        line_content: Line content

    Returns:
        Formatted line, format: LINE_NUMBER|LINE_CONTENT
    """
    return f"{line_num:6d}|{line_content}"


def format_omission_marker(omission_marker: str, omitted_count: Optional[int] = None) -> str:
    """Format omission marker with line count.

    Args:
        omission_marker: Language-specific comment marker (e.g., "# ... omitted lines ...")
        omitted_count: Number of omitted lines (optional)

    Returns:
        Formatted marker with 7 spaces for alignment and optional count
    """
    if omitted_count is not None and omitted_count > 0:
        return f"       {omission_marker} ({omitted_count} lines omitted)"
    return f"       {omission_marker}"


def resolve_search_paths(path_input: Path, base_workspace: Path, recursive: bool,
                        logger: Optional['logging.LoggerAdapter'] = None) -> List[Path]:
    """
    Resolve search paths, support file, directory and wildcard
    
    Args:
        path_input: Path pattern object
        base_workspace: Base workspace path (uniform interface)
        recursive: Whether to search recursively (only effective when path is a directory)
        logger: Optional logger instance
        
    Returns:
        List of file paths to search
    """
    try:
        path_pattern = str(path_input)
        
        # Check if contains wildcard
        if '*' in path_pattern or '?' in path_pattern or '[' in path_pattern:
            # Use glob pattern search
            glob_pattern = str(base_workspace / path_pattern)
            
            files_to_search = []
            for match in glob.glob(glob_pattern, recursive=True):
                match_path = Path(match)
                if match_path.is_file():
                    files_to_search.append(match_path)
            return files_to_search
        
        # Non-wildcard path: resolve single file or directory
        if path_input.is_absolute():
            raise ValueError(f"Expected relative path, got absolute path: {path_input}")
        
        resolved_path = base_workspace / path_input
        
        files_to_search = []
        
        if resolved_path.exists():
            if resolved_path.is_file():
                # Single file
                files_to_search.append(resolved_path)
            elif resolved_path.is_dir():
                # Directory: iterate through files
                if recursive:
                    file_iter = resolved_path.rglob('*')
                else:
                    file_iter = resolved_path.iterdir()
                
                for file_path in file_iter:
                    if file_path.is_file():
                        files_to_search.append(file_path)
        
        return files_to_search
        
    except Exception as e:
        if logger:
            logger.error(f"Error resolving search paths for '{path_input}': {traceback.format_exc()}")
        return []


# ===== Workspace path processing tool =====

def calculate_relative_path(absolute_path: Path, base_workspace: Path) -> Path:
    """Calculate relative path, return original path if failed"""
    try:
        return absolute_path.relative_to(base_workspace)
    except ValueError:
        return absolute_path


# ===== File validation and checking tools =====

def validate_file_exists_and_is_file(file_path: Path, relative_path: Path) -> Optional[Dict[str, Any]]:
    """
    Validate file exists and is a file
    
    Returns:
        None: Validation passed
        Dict: Error information
    """
    if not file_path.exists():
        return {
            "success": False,
            "error": f"File not found: {relative_path}"
        }
    
    if not file_path.is_file():
        return {
            "success": False,
            "error": f"Path is not a file: {relative_path}"
        }
    
    return None


def check_file_size_limit(file_path: Path, max_size: Optional[int], relative_path: Path) -> Optional[Dict[str, Any]]:
    """
    Check file size limit
    
    Returns:
        None: Validation passed
        Dict: Error information
    """
    if max_size is None:
        return None
    
    try:
        file_size = file_path.stat().st_size
        if file_size > max_size:
            return {
                "success": False,
                "error": f"File too large for reading ({file_size} bytes): {relative_path}"
            }
    except OSError:
        pass
    
    return None


async def read_file_content_safe(file_path: Path, relative_path: Path) -> Tuple[bool, str, Optional[str]]:
    """
    Safe read file content (asynchronous, avoid blocking event loop)
    
    Returns:
        Tuple[success, content_or_error_message, error_type]:
        - success: Whether successful
        - content_or_error_message: File content or error message
        - error_type: Error type (None, 'decode', 'io')
    """
    try:
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
        return True, content, None
    except UnicodeDecodeError:
        return False, f"Cannot read file as text (binary file or unsupported encoding): {relative_path}", 'decode'
    except OSError as e:
        return False, f"Cannot read file: {relative_path} - {e}", 'io'


def normalize_line_range(line_range: Optional[List], total_lines: int) -> Tuple[int, int]:
    """
    Normalize line range to positive 1-indexed values following Python slicing semantics.

    Python-style features:
    - Negative indices count from end: -1 is last line, -2 is second-to-last, etc.
    - None for start means "from the beginning"
    - None for end means "to the end"
    - Range is [start, end) - end is exclusive
    - 1-indexed for line numbers (line 1 is first line)

    Examples with 10 total lines:
    - [None, None] or [:] → [1, 11] (all lines)
    - [None, 5] or [:5] → [1, 5] (first 4 lines)
    - [5, None] or [5:] → [5, 11] (from line 5 to end)
    - [-5, None] or [-5:] → [6, 11] (last 5 lines)
    - [None, -1] or [:-1] → [1, 10] (all except last line)
    - [-10, -5] → [1, 6] (lines 1-5, using negative indexing)

    Args:
        line_range: Line range as [start, end], where both can be None/null
        total_lines: Total number of lines in content

    Returns:
        Tuple of (start_line, end_line) as positive 1-indexed values
    """
    if not line_range or len(line_range) != 2:
        return 1, total_lines + 1

    start_line, end_line = line_range

    # Handle None for start (means "from the beginning")
    if start_line is None:
        start_line = 1

    # Handle None for end (means "to the end")
    if end_line is None:
        end_line = total_lines + 1

    # Handle negative indexing (Python style on 1-indexed values)
    # -1 means last line (line total_lines), -2 means second-to-last, etc.
    if isinstance(start_line, int) and start_line < 0:
        start_line = total_lines + start_line + 1
    if isinstance(end_line, int) and end_line < 0:
        end_line = total_lines + end_line + 1

    # Clamp to valid range
    start_line = max(1, start_line)
    end_line = min(total_lines + 1, max(1, end_line))

    return start_line, end_line


def apply_line_range_to_content(content: str, line_range: Optional[List], with_line_numbers: bool = True) -> str:
    """
    Apply line range filtering to content and optionally add line numbers

    Args:
        content: Original content
        line_range: Line range [start, end) using 1-indexed Python-style slicing (end exclusive).
                    Supports negative indices and None for both start and end. Examples:
                    - [None, None] = all lines
                    - [None, 10] = first 9 lines
                    - [10, None] = from line 10 to end
                    - [-10, None] = last 10 lines
                    - [None, -1] = all except last line
        with_line_numbers: Whether to add line numbers

    Returns:
        Processed content
    """
    lines = content.splitlines()
    total_lines = len(lines)

    start_line, end_line = normalize_line_range(line_range, total_lines)

    if start_line < end_line:
        start_idx = start_line - 1
        end_idx = end_line - 1
        filtered_lines = lines[start_idx:end_idx]
        if with_line_numbers:
            return '\n'.join(f"{i+start_line:6d}|{line}" for i, line in enumerate(filtered_lines))
        return '\n'.join(filtered_lines)
    return ""


# ===== Pattern matching tools =====

def glob_to_regex(pattern: str) -> str:
    """
    Convert glob pattern to regular expression

    Supported glob syntax:
    - * : Match any character (not including path separator /), allow matching 0 characters
    - ** : Match any character (including path separator /, i.e. recursive matching)
    - ? : Match single character (not including path separator /)
    - [abc] : Match any character in the character set

    Examples:
        **/*        -> ^(?:.+/)?[^/]+$          (Match all files at any depth, do not match empty path)
        *.lean      -> ^[^/]*\\.lean$            (Match .lean files in the root directory)
        Mathlib/**/* -> ^Mathlib/(?:.+/)?[^/]+$ (Match all files in Mathlib)
        **          -> ^.*$                     (Match any path, including empty)
    """
    # Escape special characters in regular expression (except glob patterns)
    regex = re.escape(pattern)

    # Convert glob patterns to regular expressions
    # First handle ** (recursive pattern), must be processed before *
    regex = regex.replace(r'\*\*', '<!DOUBLE_STAR!>')  # Temporary placeholder

    # Handle single * (not matching path separator)
    # The * at the end of the path should match at least 1 character (to avoid matching empty string)
    # Other * can match 0 characters
    # Simplify processing: use [^/]* (0 or more), handle **/* separately
    regex = regex.replace(r'\*', r'<!SINGLE_STAR!>')  # Temporary placeholder

    # Handle ** (recursive pattern, match any depth of path)
    # **/* special case: match any depth of files, do not match empty path
    regex = regex.replace(r'<!DOUBLE_STAR!>/<!SINGLE_STAR!>', r'(?:.+/)?[^/]+')
    # **/ match zero or more directory levels
    regex = regex.replace(r'<!DOUBLE_STAR!>/', r'(?:.*/)?')
    # /** match any depth of subpath
    regex = regex.replace(r'/<!DOUBLE_STAR!>', r'/.*')
    # Standalone ** matches any content including empty
    regex = regex.replace(r'<!DOUBLE_STAR!>', r'.*')

    # Handle remaining single * (0 or more non-path separator characters)
    regex = regex.replace(r'<!SINGLE_STAR!>', r'[^/]*')

    # Handle ? (match single character, not including path separator)
    regex = regex.replace(r'\?', r'[^/]')

    # Add anchor: match entire path
    regex = f'^{regex}$'

    return regex


def get_default_config_values(config: Optional['FileSystemToolConfig']) -> Tuple[int, float]:
    """Get default configuration values"""
    max_results = config.performance.default_max_results if config else 50
    timeout = config.performance.default_timeout if config else 5.0
    return max_results, timeout


# ===== Difference processing tools =====

def apply_whitespace_processing(content: str, ignore_all_space: bool = False, ignore_space_change: bool = False, ignore_blank_lines: bool = False) -> str:
    """
    Apply whitespace processing options to content
    
    Args:
        content: Original content
        ignore_all_space: Ignore all whitespace character differences
        ignore_space_change: Ignore whitespace character quantity changes
        ignore_blank_lines: Ignore the addition and deletion of empty lines
        
    Returns:
        Processed content
    """
    processed = content
    
    if ignore_all_space:
        # Remove all whitespace characters
        processed = re.sub(r"\s+", "", processed)
    elif ignore_space_change:
        # Normalize consecutive whitespace to a single space
        processed = re.sub(r"\s+", " ", processed)
    
    if ignore_blank_lines:
        # Remove completely blank lines
        lines = processed.splitlines()
        non_empty_lines = [ln for ln in lines if ln.strip() != ""]
        processed = "\n".join(non_empty_lines)
        if content.endswith("\n"):
            processed += "\n"
    
    return processed


# ===== Fuzzy Matching =====

def find_fuzzy_matches(content: str, pattern: str, threshold: float = 0.85, ambiguity_margin: float = 0.05) -> List[Tuple[int, int, float]]:
    """
    Use fuzzy matching to find similar strings
    
    Args:
        content: Content to search
        pattern: Search pattern
        threshold: Similarity threshold (0-1), matches below this value are ignored
        ambiguity_margin: Fuzzy boundary, if the best match and second best match similarity difference is less than this value, considered fuzzy
        
    Returns:
        List[(start_pos, end_pos, similarity)], sorted by similarity in descending order, with overlapping removed
    """
    if not pattern or not content:
        return []
    
    pattern_len = len(pattern)
    candidates = []
    
    # Sliding window to find possible candidates
    # Allow length variation within ±20% range
    min_len = max(1, int(pattern_len * 0.8))
    max_len = int(pattern_len * 1.2)
    
    for window_len in range(min_len, max_len + 1):
        for i in range(len(content) - window_len + 1):
            candidate = content[i:i + window_len]
            similarity = difflib.SequenceMatcher(None, pattern, candidate).ratio()
            
            if similarity >= threshold:
                candidates.append((i, i + window_len, similarity))
    
    # Sort by similarity in descending order
    candidates.sort(key=lambda x: x[2], reverse=True)
    
    # Remove overlapping candidates: keep high similarity, remove overlapping low similarity
    non_overlapping = []
    for cand in candidates:
        start, end, sim = cand
        # Check if overlaps with selected candidates
        overlaps = False
        for selected_start, selected_end, _ in non_overlapping:
            # Overlap check: two intervals have intersection
            if not (end <= selected_start or start >= selected_end):
                overlaps = True
                break
        
        if not overlaps:
            non_overlapping.append(cand)
    
    return non_overlapping


def select_best_fuzzy_match(candidates: List[Tuple[int, int, float]], ambiguity_margin: float = 0.05) -> Optional[Tuple[int, int, float, str]]:
    """
    Select the best match from candidates, detect if there is ambiguity
    
    Args:
        candidates: [(start_pos, end_pos, similarity), ...], should be sorted by similarity in descending order
        ambiguity_margin: If the best and second best similarity difference is less than this value, considered fuzzy
        
    Returns:
        (start_pos, end_pos, similarity, status) or None
        status: "unique" (unique best) or "ambiguous" (fuzzy)
    """
    if not candidates:
        return None
    
    if len(candidates) == 1:
        return (*candidates[0], "unique")
    
    best = candidates[0]
    second_best = candidates[1]
    
    # Check if there is ambiguity
    if best[2] - second_best[2] < ambiguity_margin:
        return (*best, "ambiguous")
    
    return (*best, "unique")


# ===== Line Range Editing Tool Functions =====

def validate_line_range(line_range: Optional[List], content: str) -> Optional[Dict[str, Any]]:
    """
    Validate line range parameter format (tolerant handling of out of range, support negative indexing and None)

    Args:
        line_range: Line range [start, end) using 1-indexed Python-style slicing (end exclusive).
                    Supports negative indexing and None for both start and end. Examples:
                    - [None, None] or [:] = all lines
                    - [None, 10] or [:10] = first 9 lines
                    - [10, None] or [10:] = from line 10 to end
                    - [None, -1] or [:-1] = all except last line
                    - [-10, None] or [-10:] = last 10 lines
        content: Content of the file (used for negative indexing conversion)

    Returns:
        None: Validation passed
        Dict: Error information (contains 'success' and 'error' fields)
    """
    if line_range is None:
        return None

    if not isinstance(line_range, list) or len(line_range) != 2:
        return {
            "success": False,
            "error": "line_range must be a list with exactly 2 elements [start_line, end_line]"
        }

    start_line, end_line = line_range

    # Validate start_line must be int or None
    if start_line is not None and not isinstance(start_line, int):
        return {
            "success": False,
            "error": f"line_range start must be an integer or None, got {type(start_line).__name__}"
        }

    # Validate end_line must be int or None
    if end_line is not None and not isinstance(end_line, int):
        return {
            "success": False,
            "error": f"line_range end must be an integer or None, got {type(end_line).__name__}"
        }
    
    lines = content.splitlines()
    total_lines = len(lines)

    # Handle negative indexing (Python style)
    if start_line is not None and start_line < 0:
        start_line = total_lines + start_line + 1
    if end_line is not None and end_line < 0:
        end_line = total_lines + end_line + 1

    # Tolerant handling: out of range negative numbers are automatically adjusted to 1
    if start_line is not None:
        start_line = max(1, start_line)
    if end_line is not None:
        end_line = max(1, end_line)
    
    # Tolerant handling: allow end_line to exceed total lines, automatically adjust
    # Note: line_range is a reference type, directly modifying it will affect the caller, here we do not modify the original data
    # Adjust logic is handled in actual use (apply_line_range_to_content has already handled)
    
    # Only report an error if the adjustment is still unreasonable after adjustment, otherwise return None (validation passed)
    if total_lines == 0:
        return None

    # Allow line ranges that start past EOF so callers can append content gracefully (validation passed)
    if start_line is not None and start_line > total_lines:
        return None

    adjusted_end = min(end_line, total_lines + 1) if end_line is not None else total_lines + 1
    if start_line is not None and adjusted_end < start_line:
        return {
            "success": False,
            "error": f"Adjusted end line ({adjusted_end}) is before start_line ({start_line})"
        }
    
    return None


def validate_string_in_range(content: str, old_str: str, old_line_range: Optional[List[int]] = None, replace_all: bool = False, fuzzy_threshold: float = 0.85, ambiguity_margin: float = 0.05, enable_fuzzy_matching: bool = True) -> Optional[Dict[str, Any]]:
    """
    Validate string replacement operation in specified range (three-stage matching: exact -> flexible -> fuzzy)

    Args:
        content: Content of the file
        old_str: String to find
        old_line_range: Line range [start, end) using 1-indexed Python-style slicing (end exclusive),
                        support negative indexing like -1 means last line (end exclusive), None means entire file
        replace_all: Whether to replace all matches (False when multiple matches will report an error)
        fuzzy_threshold: Fuzzy matching similarity threshold
        ambiguity_margin: Fuzzy matching ambiguity margin
        enable_fuzzy_matching: Enable fuzzy matching (if False, skip fuzzy matching stage)

    Returns:
        None: Validation passed
        Dict: Error information (contains 'success' and 'error' fields)
    """
    # Step 1: Determine search range
    if old_line_range is not None:
        lines = content.splitlines(keepends=True)
        total_lines = len(lines)
        start_line, end_line = old_line_range

        # Handle None values (use normalize_line_range for consistency)
        if start_line is None:
            start_line = 1
        if end_line is None:
            end_line = total_lines + 1

        # Handle negative indexing
        if isinstance(start_line, int) and start_line < 0:
            start_line = total_lines + start_line + 1
        if isinstance(end_line, int) and end_line < 0:
            end_line = total_lines + end_line + 1

        # Adjust out of range line numbers
        start_line = max(1, start_line)
        end_line = min(end_line, len(lines) + 1)
        
        # Calculate character position and slice
        start_pos = sum(len(lines[j]) for j in range(start_line - 1))
        end_pos = sum(len(lines[j]) for j in range(end_line - 1))
        search_content = content[start_pos:end_pos]
        range_desc = f"in line range ({start_line}-{end_line})"
    else:
        search_content = content
        range_desc = "in file"
    
    # Step 2: Try three-stage matching, get match count and type
    match_count = 0
    match_type = None
    
    # Stage 1: Exact matching
    exact_count = search_content.count(old_str)
    if exact_count > 0:
        match_count = exact_count
        match_type = "exact match"
    else:
        # Stage 2: Flexible matching
        flexible_matches = find_all_with_whitespace_flexibility(search_content, old_str)
        if flexible_matches:
            match_count = len(flexible_matches)
            match_type = "flexible whitespace matching"
        else:
            # Stage 3: Fuzzy matching (only if enabled)
            if enable_fuzzy_matching:
                fuzzy_candidates = find_fuzzy_matches(search_content, old_str, threshold=fuzzy_threshold, ambiguity_margin=ambiguity_margin)
                if fuzzy_candidates:
                    fuzzy_result = select_best_fuzzy_match(fuzzy_candidates, ambiguity_margin=ambiguity_margin)
                    if fuzzy_result:
                        if fuzzy_result[3] == "ambiguous":
                            return {
                                "success": False,
                                "error": f"Ambiguous fuzzy matches found {range_desc}. Best match has {fuzzy_result[2]:.1%} similarity, but multiple similar candidates exist. Please be more specific."
                            }
                        # fuzzy_result[3] == "unique"
                        match_count = 1
                        match_type = "fuzzy match"
    
    # Step 3: Check match result
    if match_count == 0:
        # All matches failed
        old_str_lines = old_str.count('\n') + 1
        if enable_fuzzy_matching:
            error_msg = f"String to replace not found {range_desc} (tried exact, flexible whitespace, and fuzzy matching)"
        else:
            error_msg = f"String to replace not found {range_desc} (tried exact and flexible whitespace matching)"
        if old_str_lines > 3:
            error_msg += f"\n\nTIP: For multi-line replacements ({old_str_lines} lines), use 'old_line_range' instead of 'old_str' for reliability."
        return {"success": False, "error": error_msg}
    
    if not replace_all and match_count > 1:
        # Found multiple matches but not allowed to replace all
        return {
            "success": False,
            "error": f"Ambiguous: String appears {match_count} times {range_desc} ({match_type}). Please be more specific for unique replacement."
        }
    
    # Validation passed
    return None


def find_string_with_two_stage_matching(content: str, pattern: str, replace_all: bool = False, start: int = 0, fuzzy_threshold: float = 0.85, ambiguity_margin: float = 0.05, enable_fuzzy_matching: bool = True) -> List[Tuple[int, int]]:
    """
    Use three-stage matching to find string position (exact -> flexible -> fuzzy)

    Args:
        content: Content to search
        pattern: Pattern to find
        replace_all: Whether to find all matches
        start: Start search position
        fuzzy_threshold: Fuzzy matching similarity threshold
        ambiguity_margin: Fuzzy matching ambiguity margin
        enable_fuzzy_matching: Enable fuzzy matching (if False, skip fuzzy matching stage)

    Returns:
        List of match positions, each element is (start_pos, end_pos)
    """
    if replace_all:
        # Find all matches
        # Stage 1: Try exact matching
        exact_matches = []
        pos = start
        while True:
            pos = content.find(pattern, pos)
            if pos == -1:
                break
            exact_matches.append((pos, pos + len(pattern)))
            pos += len(pattern)
        
        if exact_matches:
            return exact_matches
        
        # Stage 2: Exact matching failed, use flexible matching
        flexible_matches = find_all_with_whitespace_flexibility(content, pattern)
        if flexible_matches:
            return flexible_matches

        # Stage 3: Flexible matching failed, try fuzzy matching (only if enabled)
        if enable_fuzzy_matching:
            fuzzy_candidates = find_fuzzy_matches(content[start:], pattern, threshold=fuzzy_threshold, ambiguity_margin=ambiguity_margin)
            if fuzzy_candidates:
                # In replace_all mode, return all candidates
                return [(s + start, e + start) for s, e, _ in fuzzy_candidates]

        return []
    else:
        # Find the first match
        # Stage 1: Try exact matching
        pos = content.find(pattern, start)
        if pos != -1:
            return [(pos, pos + len(pattern))]
        
        # Stage 2: Exact matching failed, use flexible matching
        flexible_match = find_with_whitespace_flexibility(content, pattern, start)
        if flexible_match:
            return [flexible_match]

        # Stage 3: Flexible matching failed, try fuzzy matching (only if enabled)
        if enable_fuzzy_matching:
            fuzzy_candidates = find_fuzzy_matches(content[start:], pattern, threshold=fuzzy_threshold, ambiguity_margin=ambiguity_margin)
            if fuzzy_candidates:
                match_result = select_best_fuzzy_match(fuzzy_candidates, ambiguity_margin=ambiguity_margin)
                if match_result and match_result[3] == "unique":
                    # Only accept unique fuzzy matches
                    return [(match_result[0] + start, match_result[1] + start)]

        return []


def normalize_whitespace_for_matching(text: str) -> str:
    """
    Normalize text, remove all whitespace characters for matching
    
    Args:
        text: Original text
        
    Returns:
        Text with all whitespace characters removed
    """
    import re
    return re.sub(r'\s+', '', text)


def find_with_whitespace_flexibility(content: str, pattern: str, start: int = 0) -> Optional[Tuple[int, int]]:
    """
    Find pattern in content, ignore whitespace character differences
    
    Args:
        content: Content to search
        pattern: Pattern to find
        start: Start search position (position in original content)
        
    Returns:
        If found, return (start_pos, end_pos) representing the range of positions in the original content
        If not found, return None
    """
    # Normalize pattern and content
    normalized_pattern = normalize_whitespace_for_matching(pattern)
    normalized_content = normalize_whitespace_for_matching(content)
    
    # If pattern or content is empty, cannot match
    if not normalized_pattern or not normalized_content:
        return None
    
    # Build position mapping: normalized_pos -> original_pos
    position_map = []
    for i, char in enumerate(content):
        if not char.isspace():
            position_map.append(i)
    
    if not position_map:
        return None
    
    # Calculate start search position in normalized content
    normalized_start = 0
    for i, orig_pos in enumerate(position_map):
        if orig_pos >= start:
            normalized_start = i
            break
    
    # Find in normalized content
    normalized_pos = normalized_content.find(normalized_pattern, normalized_start)
    
    if normalized_pos == -1:
        return None
    
    # Map back to original position
    start_pos = position_map[normalized_pos]
    
    # Find end position of match
    end_index = normalized_pos + len(normalized_pattern) - 1
    if end_index >= len(position_map):
        end_pos = len(content)
    else:
        # End position is the next position after the last matching character
        end_pos = position_map[end_index] + 1
    
    return (start_pos, end_pos)


def find_all_with_whitespace_flexibility(content: str, pattern: str) -> List[Tuple[int, int]]:
    """
    Find all matches in content, ignore whitespace character differences
    
    Args:
        content: Content to search
        pattern: Pattern to find
        
    Returns:
        List of match positions, each element is (start_pos, end_pos)
    """
    matches = []
    start = 0
    
    while start < len(content):
        result = find_with_whitespace_flexibility(content, pattern, start)
        if result is None:
            break
        
        # Prevent infinite loop: ensure next search starts after current match
        if result[1] <= start:
            # If end position does not progress, force progress at least 1 character
            start = start + 1
        else:
            matches.append(result)
            start = result[1]
    
    return matches


def generate_versioned_filename(original_path: Path, workspace: Path) -> Path:
    """
    Generate new versioned filename for read-only files, smartly handle existing version numbers
    
    Args:
        original_path: Original file path (relative path)
        workspace: Workspace path
        
    Returns:
        New file path (relative path), format: "filename_v1.ext", "filename_v2.ext", ...
        
    Examples:
        - "theorem.lean" -> "theorem_v1.lean"
        - "theorem_v1.lean" -> "theorem_v2.lean"
        - "theorem_v5.lean" -> "theorem_v6.lean"
    """
    import re
    
    stem = original_path.stem
    suffix = original_path.suffix
    parent = original_path.parent
    
    # Check if filename already contains version number (format: _vN)
    version_pattern = r'^(.+)_v(\d+)$'
    match = re.match(version_pattern, stem)
    
    if match:
        # File already has version number, extract base name and current version
        base_stem = match.group(1)
        current_version = int(match.group(2))
        start_version = current_version + 1
    else:
        # File has no version number, start from v1
        base_stem = stem
        start_version = 1
    
    # Find available filename from start version
    version = start_version
    while True:
        new_filename = f"{base_stem}_v{version}{suffix}"
        new_path = parent / new_filename
        
        # Check if file exists
        absolute_new_path = workspace / new_path
        if not absolute_new_path.exists():
            return new_path
        
        version += 1
        
        # Prevent infinite loop
        if version > 1000:
            raise ValueError(f"Too many versions for file: {original_path}")


# ===== Git helper functions =====

def get_relative_path_from_workspace(file_path: Path, workspace: Path) -> Path:
    """Get relative path of file from workspace"""
    if file_path.is_absolute():
        return file_path.relative_to(workspace)
    return file_path

# ===== Content display formatting functions =====

def format_content_display(
    content: str,
    omission_marker: str,
    max_lines: Optional[int] = None
) -> str:
    """
    Format content display (for file_write)

    Args:
        content: File content
        omission_marker: Language-specific omission marker (e.g., "# ... omitted lines ...")
        max_lines: Maximum display lines (if exceeded, display max_lines lines before and after)

    Returns:
        Formatted content string, including line numbers
    """
    lines = content.splitlines()
    total_lines = len(lines)

    # If no limit or content is short, display all
    if max_lines is None or total_lines <= max_lines * 2:
        return '\n'.join(format_line_with_number(i+1, line) for i, line in enumerate(lines))

    # Content is long, display max_lines lines before and after
    output_lines = []

    # Lines before
    for i in range(max_lines):
        if i < total_lines:
            output_lines.append(format_line_with_number(i+1, lines[i]))

    # Omission marker
    omitted_count = total_lines - max_lines * 2
    if omitted_count > 0:
        output_lines.append(format_omission_marker(omission_marker, omitted_count))

    # Lines after
    for i in range(total_lines - max_lines, total_lines):
        if i >= 0:
            output_lines.append(format_line_with_number(i+1, lines[i]))

    return '\n'.join(output_lines)


def generate_modified_content_display(
    current_content: str,
    edit_results: List[Dict[str, Any]],
    omission_marker: str,
    context_lines_before: int,
    context_lines_after: int,
    max_context_lines: Optional[int]
) -> str:
    """
    Generate display of modified content, including context and omission marker (for file_edit)

    Args:
        current_content: Modified complete content
        edit_results: Successful edit result list
        omission_marker: Language-specific omission marker (e.g., "/- ... omitted lines ... -/")
        context_lines_before: Context lines before
        context_lines_after: Context lines after
        max_context_lines: Use omission marker if exceeded this number of lines

    Returns:
        Formatted content string, including line numbers
    """
    if not edit_results:
        return ""
    
    lines = current_content.splitlines()
    total_lines = len(lines)
    
    # Collect all ranges to display
    display_ranges = []
    for edit_result in edit_results:
        new_line_range = edit_result.get("new_line_range")
        if not new_line_range:
            continue
        
        start_line, end_line = new_line_range
        
        # Calculate range with context
        context_start = max(1, start_line - context_lines_before)
        context_end = min(total_lines, end_line + context_lines_after)
        
        display_ranges.append((context_start, context_end, start_line, end_line))
    
    # Merge overlapping ranges
    if not display_ranges:
        return ""
    
    display_ranges.sort(key=lambda x: x[0])
    merged_ranges = [display_ranges[0]]
    
    for current_range in display_ranges[1:]:
        last_range = merged_ranges[-1]
        # If current range overlaps or is adjacent to previous range, merge
        if current_range[0] <= last_range[1] + 1:
            merged_ranges[-1] = (
                last_range[0],
                max(last_range[1], current_range[1]),
                last_range[2],  # Keep start line of first edit
                max(last_range[3], current_range[3])  # Use largest end line
            )
        else:
            merged_ranges.append(current_range)
    
    # Generate display content
    output_lines = []
    
    for i, (context_start, context_end, edit_start, edit_end) in enumerate(merged_ranges):
        # Add separator between ranges (if not first range)
        if i > 0:
            prev_end = merged_ranges[i-1][1]
            gap = context_start - prev_end - 1
            if gap > 0:
                output_lines.append(format_omission_marker(omission_marker, gap))
        
        # Display content of this range
        for line_num in range(context_start, context_end + 1):
            if line_num < 1 or line_num > total_lines:
                continue
            
            line_content = lines[line_num - 1]
            
            # If in edit range, may need to handle omission
            if edit_start <= line_num <= edit_end:
                # Check if need to omit middle lines
                if max_context_lines is not None:
                    lines_in_edit = edit_end - edit_start + 1
                    if lines_in_edit > max_context_lines:
                        # Average allocation to front and back parts
                        lines_per_section = max_context_lines // 2
                        first_section_end = edit_start + lines_per_section - 1
                        last_section_start = edit_end - lines_per_section + 1
                        
                        # Only display front and back parts, omit middle
                        if line_num <= first_section_end:
                            # Front part
                            output_lines.append(format_line_with_number(line_num, line_content))
                        elif line_num == first_section_end + 1:
                            # Omission marker (only add when first reaching omission area)
                            omitted_in_edit = last_section_start - first_section_end - 1
                            output_lines.append(format_omission_marker(omission_marker, omitted_in_edit))
                        elif line_num >= last_section_start:
                            # Back part
                            output_lines.append(format_line_with_number(line_num, line_content))
                        # Middle part skipped
                    else:
                        output_lines.append(format_line_with_number(line_num, line_content))
                else:
                    output_lines.append(format_line_with_number(line_num, line_content))
            else:
                # Context lines
                output_lines.append(format_line_with_number(line_num, line_content))
    
    return '\n'.join(output_lines)


# ===== Line number detection and removal =====

def detect_and_remove_line_numbers(text: str) -> Tuple[str, bool, Optional[str]]:
    """
    Detect and remove line numbers from text (format: LINE_NUMBER|CONTENT)

    Args:
        text: Input text that may contain line numbers

    Returns:
        Tuple[cleaned_text, had_line_numbers, warning_message]:
        - cleaned_text: Text with line numbers removed
        - had_line_numbers: Whether line numbers were detected and removed
        - warning_message: Warning message for the model (None if no line numbers detected)
    """
    if not text:
        return text, False, None

    lines = text.splitlines(keepends=True)
    cleaned_lines = []
    line_number_pattern = re.compile(r'^\s*\d{1,6}\s*\|')
    lines_with_numbers = 0

    for line in lines:
        match = line_number_pattern.match(line)
        if match:
            lines_with_numbers += 1
            # Remove the line number prefix
            cleaned_line = line[match.end():]
            cleaned_lines.append(cleaned_line)
        else:
            cleaned_lines.append(line)

    cleaned_text = ''.join(cleaned_lines)

    # Only consider it as having line numbers if most lines (>50%) have the pattern
    # This avoids false positives from code that happens to start with numbers
    total_lines = len(lines)
    has_line_numbers = lines_with_numbers > 0 and (lines_with_numbers / total_lines) > 0.5

    if has_line_numbers:
        warning_msg = (
            f"WARNING: Detected and automatically removed line number prefixes from {lines_with_numbers}/{total_lines} lines. "
            f"Line numbers (e.g., '123|') are display-only metadata from file_read output. "
            f"When editing files, provide only the actual code content without line number prefixes."
        )
        return cleaned_text, True, warning_msg

    return text, False, None


# ===== Single edit processing function =====

def process_single_edit(
    edit: Dict[str, Any],
    original_content: str,
    edit_index: int,
    fuzzy_threshold: float = 0.85,
    ambiguity_margin: float = 0.05,
    enable_fuzzy_matching: bool = True
) -> Tuple[Dict[str, Any], List[Tuple[int, int, str]]]:
    """
    Process single edit operation, validate and convert to character positions

    Args:
        edit: Edit dictionary, contains old_str, new_str, old_line_range, replace_all
        original_content: Original file content
        edit_index: Edit index (starting from 0)
        fuzzy_threshold: Fuzzy match similarity threshold
        ambiguity_margin: Fuzzy match ambiguity margin
        enable_fuzzy_matching: Enable fuzzy matching (if False, skip fuzzy matching stage)

    Returns:
        Tuple[edit_result, position_edits]:
        - edit_result: Edit result dictionary
        - position_edits: Position edit list [(start_pos, end_pos, new_str), ...]
    """
    edit_result = {
        "edit_index": edit_index + 1,
        "success": False,
        "error": None,
        "old_line_range": None,
        "new_line_range": None,
        "old_str": None,
        "new_str": None
    }
    
    # Validate edit format
    if not isinstance(edit, dict):
        edit_result["error"] = "Edit must be a dictionary"
        return edit_result, []
    
    # Get parameters
    old_str = edit.get('old_str')
    new_str = edit.get('new_str')
    old_line_range = edit.get('old_line_range')
    replace_all = edit.get('replace_all', False)

    # Validate new_str
    if new_str is None:
        edit_result["error"] = "Must contain 'new_str' field"
        return edit_result, []

    if not isinstance(new_str, str):
        edit_result["error"] = f"'new_str' must be a string, got {type(new_str).__name__}"
        return edit_result, []

    # Validate old_str type
    if old_str is not None and not isinstance(old_str, str):
        edit_result["error"] = f"'old_str' must be a string, got {type(old_str).__name__}"
        return edit_result, []

    # Auto-detect and remove line numbers from new_str
    cleaned_new_str, had_new_line_numbers, new_warning = detect_and_remove_line_numbers(new_str)
    if had_new_line_numbers:
        edit_result["warning"] = new_warning
        new_str = cleaned_new_str

    # Auto-detect and remove line numbers from old_str (if provided)
    if old_str is not None:
        cleaned_old_str, had_old_line_numbers, old_warning = detect_and_remove_line_numbers(old_str)
        if had_old_line_numbers:
            # Append to existing warning or create new one
            old_warning_msg = (
                f"WARNING: Detected and automatically removed line number prefixes from old_str. "
                f"Line numbers are display-only metadata. Provide only actual code content."
            )
            if "warning" in edit_result:
                edit_result["warning"] += f"\n{old_warning_msg}"
            else:
                edit_result["warning"] = old_warning_msg
            old_str = cleaned_old_str
    
    # Validate at least one parameter
    if old_str is None and old_line_range is None:
        edit_result["error"] = "Must contain either 'old_str' or 'old_line_range' field"
        return edit_result, []
    
    # Validate old_line_range format
    if old_line_range is not None:
        if not isinstance(old_line_range, list) or len(old_line_range) != 2:
            edit_result["error"] = "old_line_range must be a list with exactly 2 elements [start_line, end_line]"
            return edit_result, []

        start_line, end_line = old_line_range
        # Both start_line and end_line can be int or None
        if start_line is not None and not isinstance(start_line, int):
            edit_result["error"] = f"old_line_range start must be an integer or None, got {type(start_line).__name__}"
            return edit_result, []
        if end_line is not None and not isinstance(end_line, int):
            edit_result["error"] = f"old_line_range end must be an integer or None, got {type(end_line).__name__}"
            return edit_result, []

        # Validate line range validity
        line_range_error = validate_line_range(old_line_range, original_content)
        if line_range_error:
            edit_result["error"] = line_range_error['error']
            return edit_result, []
    
    # Validate old_str if provided
    if old_str is not None:
        string_validation_error = validate_string_in_range(
            original_content, old_str, old_line_range, replace_all,
            fuzzy_threshold=fuzzy_threshold,
            ambiguity_margin=ambiguity_margin,
            enable_fuzzy_matching=enable_fuzzy_matching
        )
        if string_validation_error:
            edit_result["error"] = string_validation_error['error']
            return edit_result, []
    
    # Validate new and old strings cannot be identical
    if old_str is not None and old_str == new_str:
        edit_result["error"] = "old_str and new_str cannot be identical"
        return edit_result, []
    
    # Convert to character positions
    position_edits = []
    lines_with_ends = original_content.splitlines(keepends=True)
    
    try:
        if old_line_range:
            # Convert old_line_range to character positions using normalize_line_range
            total_lines = len(lines_with_ends)
            requested_start_line, requested_end_line = old_line_range

            # Normalize to positive 1-indexed values (handles negative indexing and None)
            start_line, end_line = normalize_line_range(old_line_range, total_lines)
            effective_end_line = end_line
            append_at_eof = start_line > total_lines + 1

            if append_at_eof:
                if old_str is not None:
                    edit_result["error"] = (
                        f"start_line ({requested_start_line}) exceeds total lines ({total_lines}); "
                        "cannot combine with 'old_str' for append operations"
                    )
                    return edit_result, []
                start_pos = len(original_content)
                end_pos = len(original_content)
                edit_result["info"] = (
                    f"Requested line_range [{requested_start_line}, {requested_end_line}] "
                    f"starts after end of file ({total_lines} lines); appended new content at EOF."
                )
            else:
                # Calculate start character position
                start_pos = sum(len(lines_with_ends[j]) for j in range(start_line - 1))
                end_pos = sum(len(lines_with_ends[j]) for j in range(effective_end_line - 1))
            
            if old_str is None:
                # Only old_line_range: direct replacement
                position_edits.append((start_pos, end_pos, new_str))
            else:
                # old_line_range + old_str: find within range (three-stage matching)
                range_content = original_content[start_pos:end_pos]
                matches = find_string_with_two_stage_matching(
                    range_content, old_str, replace_all=False,
                    fuzzy_threshold=fuzzy_threshold,
                    ambiguity_margin=ambiguity_margin,
                    enable_fuzzy_matching=enable_fuzzy_matching
                )
                for match_start, match_end in matches:
                    position_edits.append((start_pos + match_start, start_pos + match_end, new_str))

        elif old_str:
            # Only old_str: find all occurrences (three-stage matching)
            matches = find_string_with_two_stage_matching(
                original_content, old_str, replace_all=replace_all,
                fuzzy_threshold=fuzzy_threshold,
                ambiguity_margin=ambiguity_margin,
                enable_fuzzy_matching=enable_fuzzy_matching
            )
            for match_start, match_end in matches:
                position_edits.append((match_start, match_end, new_str))
        
        edit_result["success"] = True
        return edit_result, position_edits
        
    except Exception as e:
        edit_result["error"] = f"Failed to process edit: {str(e)}"
        return edit_result, []


def apply_position_edits_to_content(
    original_content: str,
    position_edits: List[Tuple[int, int, str, int, Dict[str, Any]]]
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Apply position edits to content, and record detailed information

    Args:
        original_content: Original content
        position_edits: Position edit list [(start_pos, end_pos, new_str, edit_index, edit_result), ...]
                        sorted by position in descending order

    Returns:
        Tuple[current_content, edit_results]:
        - current_content: Modified content
        - edit_results: Updated edit result list
    """
    current_content = original_content

    for start_pos, end_pos, new_str, edit_index, edit_result in position_edits:
        # Record information before modification
        old_content_segment = original_content[start_pos:end_pos]

        # Calculate line number (starting from 1, line number counting based on newline)
        old_line_start = original_content[:start_pos].count('\n') + 1

        if end_pos > start_pos:
            old_line_end = original_content[:end_pos - 1].count('\n') + 1
        else:
            old_line_end = old_line_start

        # Replace from back to front, position will not shift
        current_content = current_content[:start_pos] + new_str + current_content[end_pos:]

        # Record information after modification
        new_content_segment = new_str

        # Calculate number of lines occupied by new content
        if not new_str:
            new_line_end = old_line_start - 1
        else:
            newline_count = new_str.count('\n')
            if new_str.endswith('\n'):
                occupied_lines = newline_count
            else:
                occupied_lines = newline_count + 1
            new_line_end = old_line_start + occupied_lines - 1

        # Generate prefix (first 10 non-whitespace characters, but preserve original format)
        def get_prefix(text, max_chars=10):
            if not text:
                return "<empty>"
            result = []
            non_whitespace_count = 0
            for char in text:
                result.append(char)
                if char not in ' \n\r\t':
                    non_whitespace_count += 1
                    if non_whitespace_count >= max_chars:
                        break
            if non_whitespace_count == 0:
                return "<empty>"
            prefix = ''.join(result)
            if non_whitespace_count >= max_chars and len(text) > len(result):
                return prefix + "..."
            return prefix

        edit_result["old_line_range"] = [old_line_start, old_line_end]
        edit_result["new_line_range"] = [old_line_start, new_line_end]
        edit_result["old_str"] = get_prefix(old_content_segment)
        edit_result["new_str"] = get_prefix(new_content_segment)

    return current_content, [e[4] for e in position_edits]


# ===== PDF text extraction functions =====

async def extract_pdf_text_to_file(
    pdf_path: Path,
    output_path: Path,
    extraction_mode: str = "text",
    sort_text: bool = True,
    logger: Optional['logging.LoggerAdapter'] = None
) -> Dict[str, Any]:
    """
    Extract text content from PDF file and save to output file.

    Args:
        pdf_path: Absolute path to PDF file
        output_path: Absolute path to output file
        extraction_mode: Extraction mode - "text" for plain text, "dict" for structured dict
        sort_text: Whether to sort text by position (only for text mode)
        logger: Optional logger instance

    Returns:
        Dict with:
        - success: bool
        - preview_start: str (first ~500 chars of extracted text)
        - preview_end: str (last ~500 chars of extracted text)
        - total_pages: int
        - total_chars: int
        - output_path: str
        - error: str (if failed)
    """
    try:
        import pymupdf
        import json

        # Open PDF
        doc = pymupdf.open(pdf_path)
        total_pages = len(doc)

        if total_pages == 0:
            doc.close()
            return {
                "success": False,
                "error": "PDF has no pages"
            }

        # Extract text based on mode
        if extraction_mode == "text":
            # Plain text mode
            all_text_parts = []
            for page in doc:
                page_text = page.get_text("text", sort=sort_text)
                all_text_parts.append(page_text)

            full_text = "\n\n".join(all_text_parts)
            total_chars = len(full_text)

            # Save to file
            async with aiofiles.open(output_path, 'w', encoding='utf-8') as f:
                await f.write(full_text)

            # Generate previews
            preview_start = full_text[:500] if len(full_text) > 500 else full_text
            preview_end = full_text[-500:] if len(full_text) > 500 else ""

        elif extraction_mode == "dict":
            # Structured dict mode
            all_pages_data = []
            for page_num, page in enumerate(doc, start=1):
                page_dict = page.get_text("dict")
                all_pages_data.append({
                    "page_number": page_num,
                    "data": page_dict
                })

            full_data = {
                "total_pages": total_pages,
                "pages": all_pages_data
            }

            # Save as JSON
            json_str = json.dumps(full_data, indent=2, ensure_ascii=False)
            async with aiofiles.open(output_path, 'w', encoding='utf-8') as f:
                await f.write(json_str)

            total_chars = len(json_str)

            # Generate previews (from JSON string)
            preview_start = json_str[:500] if len(json_str) > 500 else json_str
            preview_end = json_str[-500:] if len(json_str) > 500 else ""

        else:
            doc.close()
            return {
                "success": False,
                "error": f"Invalid extraction_mode: {extraction_mode}. Must be 'text' or 'dict'"
            }

        doc.close()

        return {
            "success": True,
            "preview_start": preview_start,
            "preview_end": preview_end,
            "total_pages": total_pages,
            "total_chars": total_chars,
            "output_path": str(output_path)
        }

    except Exception as e:
        if logger:
            logger.error(f"Error extracting PDF text: {traceback.format_exc()}")
        return {
            "success": False,
            "error": f"Failed to extract PDF text: {str(e)}"
        }
