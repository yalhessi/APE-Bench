"""Runtime Utilities.

Common utilities shared across runtime implementations:
- Access control: Blocked/readonly path resolution
- Global writable paths
"""

import glob
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING

from ape.utils.project import PROJECT_ROOT

if TYPE_CHECKING:
    import logging
    from ape.tasks.models import WorkspaceInfo


# =============================================================================
# Global Writable Paths
# =============================================================================

def get_global_writable_paths() -> List[Path]:
    """Get global writable paths that all runtimes should allow.

    These paths are required for system-wide logging and state persistence:
    - data/llm_logs: LLM request/response logs
    - data/relay_conversations: Relay conversation history

    Returns:
        List of absolute paths that should be writable in all runtimes
    """
    return [
        PROJECT_ROOT / "data" / "llm_logs",
        PROJECT_ROOT / "data" / "relay_conversations",
    ]


# =============================================================================
# Access Control
# =============================================================================

def _resolve_paths_from_patterns(
    workspace_info: 'WorkspaceInfo',
    patterns: List[str],
    logger: Optional['logging.LoggerAdapter'] = None
) -> List[Path]:
    """Resolve path patterns to minimal covering parent paths.

    This function returns the minimal set of parent directories that cover all
    matching files, instead of expanding patterns to all individual files.
    This is critical for performance when applying overlays (e.g., mount operations).

    Args:
        workspace_info: Workspace information
        patterns: List of path patterns (glob patterns or concrete paths)
        logger: Optional logger

    Returns:
        List of minimal parent paths that cover all patterns.

    Examples:
        - "**/*" -> [base_dir]
        - "dir/**/*.txt" -> [base_dir/dir]
        - "specific/file.txt" -> [base_dir/specific/file.txt] (if exists)
        - "/absolute/path" -> [/absolute/path] (if exists)
    """
    results: List[Path] = []
    # Always use workspace root as base - patterns are relative to workspace root, not target_path
    # target_path is only for filtering the workspace scope, not for path resolution
    base = workspace_info.path
    base = base.resolve()

    for pattern in patterns:
        path_obj = Path(pattern)

        if path_obj.is_absolute():
            # Absolute path: use as-is if it exists
            resolved = path_obj.resolve()
            if not resolved.exists():
                if logger:
                    logger.debug(f"Skipping non-existent absolute path: {pattern}")
                continue
            results.append(resolved)
        else:
            # Relative pattern: find the minimal covering parent
            # Split pattern into parts and find first wildcard
            parts = Path(pattern).parts

            # Find the first part containing wildcards
            first_wildcard_idx = None
            for idx, part in enumerate(parts):
                if '*' in part or '?' in part or '[' in part:
                    first_wildcard_idx = idx
                    break

            if first_wildcard_idx is None:
                # No wildcards: this is a concrete path
                concrete_path = (base / pattern).resolve()
                if not concrete_path.exists():
                    if logger:
                        logger.debug(f"Skipping non-existent concrete path: {pattern}")
                    continue
                results.append(concrete_path)
            elif first_wildcard_idx == 0:
                # Pattern starts with wildcard (e.g., "**/*", "*.txt")
                # The minimal covering path is the base directory itself
                results.append(base)
            else:
                # Pattern has prefix before wildcard (e.g., "dir/**/*.txt", "dir/*/file.txt")
                # The minimal covering path is the last non-wildcard parent directory
                parent_parts = parts[:first_wildcard_idx]
                parent_path = base.joinpath(*parent_parts).resolve()

                if not parent_path.exists():
                    if logger:
                        logger.debug(f"Skipping non-existent parent path: {parent_path} (from pattern {pattern})")
                    continue

                results.append(parent_path)

    # Deduplicate and remove redundant parent-child relationships
    results = _deduplicate_parent_paths(results, logger)

    if logger:
        logger.debug(f"Resolved {len(results)} minimal parent paths from {len(patterns)} patterns")

    return results


def _deduplicate_parent_paths(
    paths: List[Path],
    logger: Optional['logging.LoggerAdapter'] = None
) -> List[Path]:
    """Remove redundant child paths that are covered by parent directories.

    Args:
        paths: List of absolute paths
        logger: Optional logger

    Returns:
        Deduplicated list with only minimal covering parent paths

    Example:
        Input:  [/a, /a/b, /a/b/c, /d]
        Output: [/a, /d]
    """
    if not paths:
        return []

    # Resolve all paths and sort by depth (shallower first)
    resolved_paths = [p.resolve() for p in paths]
    sorted_paths = sorted(
        resolved_paths,
        key=lambda p: (len(p.parts), str(p))
    )

    kept: List[Path] = []
    for path in sorted_paths:
        # Check if this path is contained in any already-kept parent
        is_redundant = any(
            path.is_relative_to(kept_path)
            for kept_path in kept
        )

        if is_redundant:
            if logger:
                logger.debug(
                    f"Skipping redundant path {path} (covered by parent)"
                )
            continue

        kept.append(path)

    return kept


def collect_blocked_paths(
    workspace: 'WorkspaceInfo',
    logger: Optional['logging.LoggerAdapter'] = None
) -> List[Path]:
    """Collect all blocked paths from scratch workspace."""
    if not workspace.blocked_path_patterns:
        return []
    return _resolve_paths_from_patterns(
        workspace,
        workspace.blocked_path_patterns,
        logger
    )


def collect_readonly_paths(
    workspace: 'WorkspaceInfo',
    logger: Optional['logging.LoggerAdapter'] = None
) -> List[Path]:
    """Collect all read-only paths from scratch workspace."""
    if not workspace.read_only_path_patterns:
        return []
    return _resolve_paths_from_patterns(
        workspace,
        workspace.read_only_path_patterns,
        logger
    )
