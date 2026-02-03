"""
File System Tools Configuration

Note: Access control has been moved to WorkspaceInfo (ape.tasks.models.WorkspaceInfo)
Each workspace has its own access control configuration.
"""

from typing import List
from pydantic import BaseModel, ConfigDict


class FileFilterConfig(BaseModel):
    """File list filtering configuration"""
    model_config = ConfigDict(extra='forbid')
    # Whether to enable filtering
    enabled: bool = True
    
    # File extension filtering
    blocked_extensions: List[str] = [
        # Binary files
        ".so", ".dylib", ".dll", ".exe", ".bin", ".db", ".sqlite", ".sqlite3",
        # Compressed files
        ".gz", ".tar", ".zip", ".7z",
        # Image and multimedia files
        ".png", ".jpg", ".jpeg", ".gif", ".pdf",
        # Lean specific build files
        ".olean", ".ilean", ".hash", ".trace",
        # Compilation artifacts
        ".pyc", ".pyo", ".class", ".o", ".obj"
    ]
    
    # Directory filtering
    blocked_directories: List[str] = [
        # Version control
        ".git", ".svn", ".hg", ".bzr",
        # IDE and editors
        ".vscode", ".idea", ".vs", "__pycache__", ".mypy_cache",
        # Build and dependency management (note: removed "target", it may be workspace name)
        "node_modules", ".npm", "build", "dist", ".gradle", ".maven",
        # Containers and deployment
        ".docker", ".devcontainer", 
        # Lean specific cache and build directories
        ".lake", "Cache", "cache",
        # Other cache and temporary directories
        ".cache", "tmp", "temp", ".tmp", ".temp", "logs", ".logs",
        # Ape workspace directory
        ".ape"
    ]
    
    # File name pattern filtering (glob pattern)
    blocked_filename_patterns: List[str] = [
        # Temporary files
        "*.tmp", "*.temp", "*~", "#*#", ".#*", "*.bak", "*.backup", "*.swp", "*.swo",
        # Log files
        "*.log", "*.out", "*.err",
        # Configuration and hidden files (selective filtering)
        ".DS_Store", "Thumbs.db", "desktop.ini",
        # Lean specific pattern
        "lakefile.olean*", ".olean*"
    ]
    
    # Path pattern filtering (full path pattern)
    blocked_path_patterns: List[str] = [
        # GitHub specific directory
        "*/.github/*", "*/.git/*",
        # Some subdirectories in test directory (keep test files but filter build artifacts)
        "*/test/**/build/*", "*/tests/**/build/*",
        # Lean project specific paths
        "*/.lake/*", "*/Cache/*", "*/cache/*"
    ]


class FileSystemPerformanceConfig(BaseModel):
    """File system performance configuration"""
    model_config = ConfigDict(extra='forbid')
    # File size limit
    max_file_size_for_content_search: int = 1024 * 1024  # 1MB
    max_file_size_for_reading: int = 10 * 1024 * 1024    # 10MB

    # Search configuration
    default_max_results: int = 50
    default_timeout: float = 5.0

    # Output editing controls
    max_context_lines: int = 10  # Maximum context lines when editing (large edit)
    # Note: max_verification_messages has been moved to LeanVerifyToolConfig.max_messages

    # Fuzzy matching configuration
    enable_fuzzy_matching: bool = True  # Enable/disable fuzzy matching (disable for performance)
    fuzzy_match_threshold: float = 0.85  # Similarity threshold (0.0-1.0)
    fuzzy_match_ambiguity_margin: float = 0.05  # Ambiguity detection boundary


class FileSystemToolConfig(BaseModel):
    """Unified file system configuration

    Note: Access control has been moved to WorkspaceInfo level, no longer global configuration
    """
    model_config = ConfigDict(extra='forbid')

    # Output controls
    show_modified_content: bool = True

    # File list filtering
    file_filter: FileFilterConfig = FileFilterConfig()

    # Performance configuration
    performance: FileSystemPerformanceConfig = FileSystemPerformanceConfig()
