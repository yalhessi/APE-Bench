"""The strict-model base, and the schema version constants every record carries."""

from typing import Dict, List, Literal, Optional, get_args
from pydantic import BaseModel, ConfigDict, Field, model_validator



MANIFEST_SCHEMA_VERSION = "pr4-manifest-1"


EVENT_SCHEMA_VERSION = "event1"


EPISODE_SCHEMA_VERSION = "episode1"


CHANGE_GRAPH_SCHEMA_VERSION = "cg1"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
