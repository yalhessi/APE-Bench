"""
Core configuration for retrieval systems
"""

from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

from ape.utils.file_ops import normalize_repo_url
from ape.utils.project import PROJECT_ROOT


class BaseRetrieveConfig(BaseModel):
    """Base configuration for retrieval systems"""

    model_config = ConfigDict(extra='forbid')

    # Storage paths
    base_dir: Path = Field(
        default_factory=lambda: PROJECT_ROOT / "data" / "retrieve",
        description="Base storage directory"
    )

    repos_dir: Path = Field(
        default_factory=lambda: PROJECT_ROOT / "data" / "retrieve" / "repos",
        description="Per-repo storage directory"
    )

    # Embedding model
    embedding_model: Path = Field(
        default_factory=lambda: "sentence-transformers/all-MiniLM-L6-v2",
        description="Embedding model path"
    )

    # ChromaDB settings
    collection_name: str = Field("items", description="ChromaDB collection name")

    # Query settings
    default_limit: int = Field(10, description="Default result limit")
    max_limit: int = Field(50, description="Maximum result limit")
    max_query_size: int = Field(20000, description="Maximum query size")
    batch_size: int = Field(512, description="Batch size for processing")

    def get_repo_name(self, repo_url: Optional[str] = None) -> str:
        """Get normalized repo name"""
        if not repo_url:
            raise ValueError("repo_url is required")
        return normalize_repo_url(repo_url)

    def get_repo_base_dir(self, repo_url: str) -> Path:
        """Get repo-specific base directory"""
        repo_name = self.get_repo_name(repo_url)
        return self.repos_dir / repo_name

    def get_storage_dir(self, repo_url: str) -> Path:
        """Get repo-specific storage directory"""
        return self.get_repo_base_dir(repo_url) / "storage"

    def get_commit_index_dir(self, repo_url: str) -> Path:
        """Get repo-specific commit index directory"""
        return self.get_repo_base_dir(repo_url) / "commit_index"

    def get_indexed_ids_file(self, repo_url: str) -> Path:
        """Get repo-specific indexed IDs file"""
        return self.get_storage_dir(repo_url) / "indexed_ids.txt"

    def model_post_init(self, __context) -> None:
        """Ensure directories exist"""
        self.repos_dir.mkdir(parents=True, exist_ok=True)
