"""
Project path utilities shared across the APE package.

Provides a single authoritative project root discovery that other modules
can import instead of re-implementing their own logic.
"""

from pathlib import Path
from functools import lru_cache


@lru_cache(maxsize=1)
def get_project_root() -> Path:
    """Find the project root directory (the directory containing src/)."""
    current = Path(__file__).resolve()
    while current != current.parent:
        if (current / "src").is_dir():
            return current
        current = current.parent
    raise RuntimeError("Could not locate project root containing 'src' directory")


# Eagerly evaluate for modules that just need the constant.
PROJECT_ROOT = get_project_root()
