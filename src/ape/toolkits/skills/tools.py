"""Managed skill MCP tools for APE-Agent."""

from __future__ import annotations

from typing import Any, Annotated, Optional, TYPE_CHECKING

from fastmcp import FastMCP
from pydantic import Field

from ape.scaffolds.skills import (
    get_task_managed_skills,
    list_skill_relative_files,
    read_materialized_skill_file,
)
from ape.toolkits.base import BaseToolsProvider
from ape.utils.logging import create_logger

if TYPE_CHECKING:
    import logging
    from ape.tasks.base import BaseTask


class SkillToolsProvider(BaseToolsProvider):
    """Read-only access to managed skills materialized for the current attempt."""

    SUPPORTED_TOOLS = ["list_skills", "read_skill"]

    def __init__(
        self,
        task: Optional["BaseTask"] = None,
        config: Optional[Any] = None,
        logger: Optional["logging.LoggerAdapter"] = None,
        confirmation_bridge: Optional[Any] = None,
        is_cli_mode: bool = False,
    ):
        super().__init__(
            task=task,
            config=config,
            logger=logger,
            confirmation_bridge=confirmation_bridge,
            is_cli_mode=is_cli_mode,
        )
        if not self.logger:
            self.logger = create_logger()

    def register_tools(self, mcp: FastMCP, enabled_tools: set[str]) -> None:
        if "list_skills" in enabled_tools:
            @mcp.tool(
                description=(
                    "List managed skills available for this task. "
                    "Use this to inspect the skill index before reading a specific skill."
                )
            )
            async def list_skills() -> dict[str, Any]:
                skill_set = get_task_managed_skills(self.task)
                skills = [] if skill_set is None else [
                    {
                        "skill_id": skill.skill_id,
                        "name": skill.name,
                        "description": skill.description,
                    }
                    for skill in skill_set.skills
                ]
                self.logger.info("Tool list_skills: returned %s skills", len(skills))
                return {"skills": skills}

        if "read_skill" in enabled_tools:
            @mcp.tool(
                description=(
                    "Read a managed skill file by skill id. "
                    "Defaults to SKILL.md and can also read supporting files referenced by the skill."
                )
            )
            async def read_skill(
                skill_id: Annotated[str, Field(description="Managed skill identifier from list_skills")],
                relative_path: Annotated[str, Field(
                    description="Relative file path inside the skill directory (default: SKILL.md)"
                )] = "SKILL.md",
            ) -> dict[str, Any]:
                skill_set = get_task_managed_skills(self.task)
                if skill_set is None:
                    raise ValueError("No managed skills are available for this task")

                skill = skill_set.by_id(skill_id)
                if skill is None:
                    raise ValueError(f"Unknown skill_id: {skill_id}")

                content = read_materialized_skill_file(skill, relative_path=relative_path)
                files = list_skill_relative_files(skill)
                self.logger.info(
                    "Tool read_skill: read %s from %s",
                    relative_path,
                    skill_id,
                )
                return {
                    "skill_id": skill.skill_id,
                    "name": skill.name,
                    "description": skill.description,
                    "relative_path": relative_path,
                    "available_files": files,
                    "content": content,
                }


from ape.toolkits.registry import register_tool

register_tool(SkillToolsProvider)
