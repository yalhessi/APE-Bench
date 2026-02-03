"""
Simplified data model definition
"""

from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from pydantic import BaseModel, Field


class DeclarationInfo(BaseModel):
    """Declaration information"""
    item_id: str
    kind: str
    name: Optional[str] = None
    fullname: Optional[str] = None
    variables: List[str] = Field(default_factory=list, description="Variables in scope at declaration")
    signature: str
    proof: str
    span: Tuple[int, int] = Field(..., description="Line number range (1-based)")

    # Source location information
    commit_hash: Optional[str] = None
    repo_url: Optional[str] = None
    file_path: Optional[str] = Field(default=None, description="Repo-root relative file path")
    default_target: Optional[str] = None


class CommitFileMapping(BaseModel):
    """Commit file mapping"""
    content_to_files: Dict[str, List[Tuple[str, str]]] = Field(default_factory=dict)
    commit_file_lists: Dict[str, List[str]] = Field(default_factory=dict)


class ScanResult(BaseModel):
    """Scan result"""
    global_declarations: Dict[str, DeclarationInfo] = Field(default_factory=dict)
    # repo_url -> commit_hash -> [(item_id, decl_name, filename, variables)]
    # filename is the file path for THIS SPECIFIC commit (relative to repo root)
    commit_index: Dict[str, Dict[str, List[Tuple[str, Optional[str], str, List[str]]]]] = Field(default_factory=dict)
    
    # Statistics information
    total_declarations: int = 0
    existing_skipped: int = 0
    unique_blobs: int = 0


class AnnotationStats(BaseModel):
    """Execution statistics"""
    commits_processed: int = 0
    annotated: int = 0
    indexed: int = 0
    skipped: int = 0
    duration_sec: float = 0.0
    mode: str = "normal"
