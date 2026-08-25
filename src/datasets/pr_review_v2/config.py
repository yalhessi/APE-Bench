"""
Configuration for the v2 first-round-review collector.

Aligned with docs/research/review-task-spec.md. Compared to the legacy collector
config, this drops everything related to multi-round snapshots, skill variants,
and the pr_split task; the v2 pipeline emits exactly one record type.
"""

from datetime import datetime
from pathlib import Path
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, model_validator

from ape.utils.project import PROJECT_ROOT


class PRReviewV2Config(BaseModel):
    repo_owner: str = Field(default="leanprover-community")
    repo_name: str = Field(default="mathlib4")

    # --- storage ---
    cache_dir: Path = Field(
        default=PROJECT_ROOT / "data" / "pr_review_v2" / "cache",
        description="Raw per-PR bundle cache; lets derive/delta re-run without re-fetching",
    )
    output_dir: Path = Field(default=PROJECT_ROOT / "inputs" / "pr_review_v2")
    output_file: Optional[Path] = None

    # --- candidate selection (stage A) ---
    start_date: Optional[str] = Field(default=None, description="YYYY-MM-DD, inclusive")
    end_date: Optional[str] = Field(default=None, description="YYYY-MM-DD, inclusive")
    include_unmerged: bool = Field(default=True, description="Also collect the closed-unmerged slice")
    max_prs: int = Field(default=200)
    max_search_pages: int = Field(default=10)
    pr_numbers: List[int] = Field(default_factory=list, description="Explicit PRs; bypasses search")
    pr_order: Literal["newest", "oldest"] = "newest"

    # --- eligibility funnel (spec §3.8) ---
    min_changed_files: int = 1
    max_changed_files: int = 30
    min_diff_lines: int = 10
    max_diff_lines: int = 800
    require_mathlib_lean_file: bool = Field(
        default=True, description="Require ≥1 changed .lean file under Mathlib/"
    )

    # --- reviewer identity (spec §3.1) ---
    roster_file: Optional[Path] = Field(
        default=None,
        description="Newline-separated GitHub logins of Mathlib maintainers+reviewers (curated roster)",
    )
    use_association_fallback: bool = Field(
        default=True,
        description="Treat author_association MEMBER/OWNER/COLLABORATOR as reviewer when not in roster",
    )

    # --- GitHub access ---
    github_token: Optional[str] = Field(default=None, description="Falls back to GITHUB_TOKEN env")
    timeout_seconds: float = 30.0
    request_interval_seconds: float = 0.0
    use_graphql_enrichment: bool = Field(
        default=True,
        description="Fetch thread resolution + body edit history via GraphQL (needs a token)",
    )

    # --- delta stage (spec §3.6/§3.7) ---
    linkage_line_slack: int = Field(default=5, description="± lines for comment↔hunk overlap")
    refetch_compares: bool = Field(default=False, description="Bypass compare-API cache")

    @property
    def repo_slug(self) -> str:
        return f"{self.repo_owner}/{self.repo_name}"

    @model_validator(mode="after")
    def _validate(self) -> "PRReviewV2Config":
        for value in (self.start_date, self.end_date):
            if value:
                datetime.strptime(value, "%Y-%m-%d")
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("start_date must be <= end_date")
        if self.max_prs <= 0 or self.max_search_pages <= 0:
            raise ValueError("max_prs and max_search_pages must be positive")
        if self.min_changed_files > self.max_changed_files:
            raise ValueError("min_changed_files must be <= max_changed_files")
        if self.min_diff_lines > self.max_diff_lines:
            raise ValueError("min_diff_lines must be <= max_diff_lines")
        self.pr_numbers = sorted({int(n) for n in self.pr_numbers})
        if any(n <= 0 for n in self.pr_numbers):
            raise ValueError("pr_numbers must be positive")
        return self
