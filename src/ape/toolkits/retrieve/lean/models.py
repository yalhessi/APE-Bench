"""
Lean-specific data models
"""

from typing import Optional, List
from pydantic import Field

from ape.toolkits.retrieve.core import BaseItem, SearchResult


class LeanItem(BaseItem):
    """Lean declaration item with semantic annotation"""

    # Lean-specific fields
    kind: str = Field(..., description="Declaration type: def/theorem/lemma/example...")
    name: Optional[str] = Field(None, description="Declaration name (can be empty)")
    fullname: Optional[str] = Field(None, description="Fully qualified declaration name (namespace-qualified)")
    variables: List[str] = Field(default_factory=list, description="Variables in scope at declaration")
    signature: str = Field(..., description="Signature (contains keywords, name, parameters and types)")
    proof: str = Field(..., description="Proof/implementation body, can be empty string")

    # Semantic annotation (LLM-generated)
    semantic: str = Field(..., description="Natural language semantic representation (for vectorization)")
    keywords: str = Field(..., description="Comma-separated technical keyword list (3-7 items)")

    # Override content to use semantic for embedding
    @property
    def content(self) -> str:
        """For Lean, content for embedding is the semantic field"""
        return self.semantic


# Re-export SearchResult for convenience
__all__ = ["LeanItem", "SearchResult"]
