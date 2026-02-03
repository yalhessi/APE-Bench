"""
Semantic annotation pipeline configuration
"""

from pathlib import Path
from pydantic import BaseModel, Field, model_validator

from ape.toolkits.execute.lean.config import LeanVerifyToolConfig
from ape.toolkits.retrieve.lean.config import LeanRetrieveToolConfig
from ape.utils.project import PROJECT_ROOT


class AnnotationConfig(BaseModel):
    """Semantic annotation pipeline configuration"""
    
    # Input file (required)
    input_file: Path = Field(..., description="Input JSONL file path")
    
    # Cache and storage
    cache_dir: Path = Field(
        default=PROJECT_ROOT / "data" / "lean_retrieve" / "semantic_annotation",
        description="Cache directory"
    )
    use_cache: bool = Field(default=True, description="Enable phase 1 cache load/save")
    
    # Execution control  
    max_files_scan: int = Field(default=None, description="Maximum number of files to scan (None means unlimited)")
    max_declarations_per_task: int = Field(default=20, description="Maximum number of declarations per task")
    num_processes: int = Field(default=32, description="Maximum number of concurrent processes")
    max_retries: int = Field(default=3, description="Maximum number of retries")
    
    # Parallel processing
    batch_size: int = Field(default=16, description="Batch size")
    io_workers: int = Field(default=32, description="Number of IO operations concurrent")
    
    # File filtering
    required_file_extension: str = Field(default=".lean", description="File extension")
    
    # Model configuration
    scaffold_type: str = Field(default="ape_agent", description="Scaffold name")
    model: str = Field(default="gpt_5_mini")
    
    # Running mode
    index_only_mode: bool = Field(default=False, description="Index only mode")
    
    # Lean tool configuration
    lean_verify_config: LeanVerifyToolConfig = Field(
        default_factory=LeanVerifyToolConfig,
        description="Lean verification tool configuration"
    )
    
    lean_retrieve_config: LeanRetrieveToolConfig = Field(
        default_factory=LeanRetrieveToolConfig,
        description="Lean retrieval tool configuration"
    )
    
    @model_validator(mode='after')
    def validate_input_file_exists(self):
        if not self.input_file.exists():
            raise ValueError(f"Input file does not exist: {self.input_file}")
        return self
