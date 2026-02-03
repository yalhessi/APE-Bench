"""
Core data models for retrieval systems
"""

from typing import Optional
from pydantic import BaseModel, Field


class BaseItem(BaseModel):
    """Base class for retrieval items"""

    item_id: str = Field(..., description="Unique item ID (content hash)")
    filename: str = Field(..., description="Source file path")
    span_start: int = Field(..., description="Start line number (1-based)")
    span_end: int = Field(..., description="End line number (1-based)")

    # Content for embedding
    content: str = Field(..., description="Text content for embedding")


class SearchResult(BaseModel):
    """Search result wrapper"""

    item: BaseItem = Field(..., description="Matched item")
    score: float = Field(..., description="Match score")
    reason: str = Field("", description="Match reason")
