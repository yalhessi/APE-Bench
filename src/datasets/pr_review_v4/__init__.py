"""PR Review v4 benchmark foundation.

The benchmark release is physically separated from experimental reviewer runs. Generation consumes
only `input/episodes.jsonl`; hidden feedback, judgment graphs, and outcomes live under `gold/`.
"""

from .schema import DatasetManifest, ReviewEpisodeInput

__all__ = ["DatasetManifest", "ReviewEpisodeInput"]
