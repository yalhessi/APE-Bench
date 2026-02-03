"""
Lean Retrieve Config - Lean-specific configuration
"""

from pathlib import Path
from pydantic import Field, ConfigDict
from typing import Optional

from ape.toolkits.retrieve.core import BaseRetrieveConfig
from ape.utils.file_ops import normalize_repo_url
from ape.utils.project import PROJECT_ROOT


class LeanRetrieveToolConfig(BaseRetrieveConfig):
    """Lean-specific retrieval configuration"""

    model_config = ConfigDict(extra='forbid')

    # Override base_dir for lean
    base_dir: Path = Field(
        default_factory=lambda: PROJECT_ROOT / "data" / "lean_retrieve",
        description="Lean semantic search data root directory"
    )

    repos_dir: Path = Field(
        default_factory=lambda: PROJECT_ROOT / "data" / "lean_retrieve" / "repos",
        description="Lean repo-specific data directory"
    )

    # Override collection name
    collection_name: str = Field("lean_items", description="Lean items collection name")

    # Default Lean repo settings
    default_commit_hash: str = Field(
        "2df2f0150c275ad53cb3c90f7c98ec15a56a1a67",
        description="Default Lean commit"
    )
    default_repo_url: str = Field(
        default="https://github.com/leanprover-community/mathlib4.git",
        description="Default Lean repository URL"
    )

    # Lean-specific methods (support default_repo_url)
    def resolve_repo(
        self,
        repo_url: Optional[str] = None
    ) -> tuple[str, str]:
        """Resolve repository name/url with defaults."""
        url = repo_url or self.default_repo_url
        name = normalize_repo_url(url)
        return name, url

    def get_repo_name(self, repo_url: Optional[str] = None) -> str:
        """Get repository name from repo_url"""
        url = repo_url or self.default_repo_url
        return normalize_repo_url(url)

    def get_repo_base_dir(self, repo_url: Optional[str] = None) -> Path:
        """Get repo-specific base directory"""
        repo_name = self.get_repo_name(repo_url)
        return self.repos_dir / repo_name

    def get_storage_dir(self, repo_url: Optional[str] = None) -> Path:
        """Get repo-specific storage directory"""
        return self.get_repo_base_dir(repo_url) / "storage"

    def get_commit_index_dir(self, repo_url: Optional[str] = None) -> Path:
        """Get repo-specific commit index directory"""
        return self.get_repo_base_dir(repo_url) / "commit_index"

    def get_annotated_ids_file(self, repo_url: Optional[str] = None) -> Path:
        """Get repo-specific annotated ID file"""
        return self.get_storage_dir(repo_url) / "annotated_ids.txt"

    def model_post_init(self, __context) -> None:
        """Ensure directories exist"""
        self.repos_dir.mkdir(parents=True, exist_ok=True)
        self.get_storage_dir().mkdir(parents=True, exist_ok=True)
        self.get_commit_index_dir().mkdir(parents=True, exist_ok=True)
