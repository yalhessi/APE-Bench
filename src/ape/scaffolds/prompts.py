"""
Unified System Prompts for All Scaffolds

This module provides a centralized system prompt management system.
All scaffold-specific prompts are built here, eliminating the need for
prompt logic in the Task layer or scattered across individual scaffolds.

Design Principles:
1. Task layer provides workspace structure with symlinks
2. Scaffold layer builds complete system prompts
3. File tools work with relative paths from workspaces/ directory
"""

from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from ape.tasks.models import WorkspaceInfo
    import logging


# =============================================================================
# Base System Prompt - Common to All Scaffolds
# =============================================================================

BATCH_MODE_SYSTEM_PROMPT = """You are an AI assistant that operates through tools. Tools are your only means of perceiving and acting in the world. Every tool call is a deliberate extension of your reasoning into reality.

<FUNDAMENTAL_PRINCIPLE>
**VERY IMPORTANT - CRITICAL REQUIREMENT: Every response MUST include TOOL CALLS.**

Responses without TOOL CALLS are immediately rejected as errors. There are NO exceptions.

**Text explains your thinking. Tools execute your actions.**

**VERY IMPORTANT:** ONLY TOOL CALLS have real effects. TEXT ALONE—no matter how detailed or correct—accomplishes NOTHING. If you respond with only text and no tool calls, you have FAILED to complete your task.

**VERY IMPORTANT - Task completion:** Other tools modify scratch workspace state, but ONLY the SUBMISSION TOOL (such as `submit_result`) formally concludes the task. You MUST call it WHEN AND ONLY WHEN the task is COMPLETED and VALIDATED.
</FUNDAMENTAL_PRINCIPLE>

<PARALLEL_TOOL_CALLS>
**CRITICAL: Call ALL needed tools in EACH response.**

Default behavior: batch ALL tool calls together in each response. Tools execute sequentially in the order you list them.
</PARALLEL_TOOL_CALLS>
"""

CLI_MODE_SYSTEM_PROMPT = """You are a helpful assistant. You must **strictly** follow the user's instructions, and you mustn't do anything the user didn't ask you to do.

<TOOL_USAGE>
**Use tools IF and ONLY IF appropriate and necessary.**

Tools are available to help you complete tasks, but you should use them judiciously:
- Use tools when you need to read files, write code, execute commands, or interact with the workspace
- Don't use tools unnecessarily when a direct answer suffices
- Explain your reasoning before calling tools
</TOOL_USAGE>

<PARALLEL_TOOL_CALLS>
When you need multiple tools, call ALL needed tools together in each response. Tools execute sequentially in the order you list them.
</PARALLEL_TOOL_CALLS>
"""


# =============================================================================
# Workspace Prompt Building Functions
# =============================================================================

async def build_workspace_paths_section(
    scratch_workspace: Optional['WorkspaceInfo'],
    target_workspace: Optional['WorkspaceInfo'],
    reference_workspaces: Optional[List['WorkspaceInfo']],
    use_absolute_paths: bool = False,
) -> str:
    """
    Build WORKSPACE_PATHS section using relative or absolute path syntax.

    Args:
        scratch_workspace: Scratch workspace info
        target_workspace: Target workspace info
        reference_workspaces: List of reference workspaces
        use_absolute_paths: Whether to use absolute paths instead of relative paths

    Returns:
        Formatted workspace paths section
    """
    lines = [
        "<WORKSPACE_PATHS>",
        "**Your working directory contains:**",
        ""
    ]

    # Generate path descriptions based on use_absolute_paths
    if use_absolute_paths:
        # Use absolute paths
        if scratch_workspace:
            abs_path = str(scratch_workspace.path.resolve())
            lines.append(f"- **{abs_path}**: Your workspace (read-write)")
            lines.append("  - Your primary workspace for creating and editing files")

        if target_workspace:
            abs_path = str(target_workspace.path.resolve())
            lines.append(f"- **{abs_path}**: Lean project (read-only)")
            lines.append("  - The library environment for verification")

        if reference_workspaces:
            lines.append("- **Reference workspaces** (read-only):")
            for ws in reference_workspaces:
                abs_path = str(ws.path.resolve())
                lines.append(f"  - **{abs_path}**: {ws.name}")

        lines.extend([
            "",
            "**Use absolute paths in file operations:**",
        ])

        if scratch_workspace:
            abs_path = str(scratch_workspace.path.resolve())
            lines.append(f"- Your files: `{abs_path}/...`")

        if target_workspace:
            abs_path = str(target_workspace.path.resolve())
            lines.append(f"- Target files: `{abs_path}/...`")

        if reference_workspaces:
            for ws in reference_workspaces:
                abs_path = str(ws.path.resolve())
                lines.append(f"- Reference files ({ws.name}): `{abs_path}/...`")
    else:
        # Use relative paths (original behavior)
        if scratch_workspace:
            lines.append("- **scratch/**: Your workspace (read-write)")
            lines.append("  - Your primary workspace for creating and editing files")

        if target_workspace:
            lines.append("- **target/**: Lean project (read-only)")
            lines.append("  - The library environment for verification")

        if reference_workspaces:
            lines.append("- **reference/**: Reference workspaces (read-only)")
            for ws in reference_workspaces:
                lines.append(f"  - **{ws.name}/**: Reference version")

        lines.extend([
            "",
            "**Use relative paths in file operations:**",
            "- Your files: `scratch/...`",
        ])

        if target_workspace:
            lines.append("- Target files: `target/...`")

        if reference_workspaces:
            for ws in reference_workspaces:
                lines.append(f"- Reference files: `reference/{ws.name}/...`")

    lines.extend([
        "",
        "</WORKSPACE_PATHS>"
    ])

    return "\n".join(lines)


async def build_workspace_content_section(
    scratch_workspace: Optional['WorkspaceInfo'],
    target_workspace: Optional['WorkspaceInfo'],
    reference_workspaces: Optional[List['WorkspaceInfo']],
    is_cli_mode: bool = False,
    logger: Optional['logging.LoggerAdapter'] = None
) -> str:
    """
    Build workspace content descriptions with optional file trees.

    Args:
        scratch_workspace: Scratch workspace info
        target_workspace: Target workspace info
        reference_workspaces: List of reference workspaces
        is_cli_mode: Whether in CLI interactive mode (affects permission descriptions)
        logger: Logger for debug info

    Returns:
        Formatted workspace content section
    """
    parts = []
    blocked_notes = []

    def _collect_blocked_note(
        workspace: 'WorkspaceInfo',
        workspace_label: str
    ) -> None:
        if not workspace.blocked_path_patterns:
            return
        patterns = workspace.blocked_path_patterns
        for pattern in patterns[:5]:
            blocked_notes.append(
                f"{workspace_label}/{pattern}"
            )
        if len(patterns) > 5:
            blocked_notes.append(f'(...and other {len(patterns) - 5} files in {workspace_label}/)')

    # Scratch workspace
    if scratch_workspace:
        if is_cli_mode:
            desc = "**Scratch Workspace**: Your primary development environment for writing and testing code. Files can be created and modified here without user confirmation, enabling rapid iteration and experimentation."
        else:
            desc = "**Scratch Workspace**: Your primary development environment for writing and testing code. Files can be freely created and modified here, enabling rapid iteration and experimentation."
        parts.append(desc)
        _collect_blocked_note(scratch_workspace, "scratch")

    # Target workspace
    if target_workspace:
        # Check if target workspace is read-only based on access control patterns
        is_target_readonly = bool(target_workspace.read_only_path_patterns and "**/*" in target_workspace.read_only_path_patterns)

        if is_target_readonly:
            # Batch mode: target workspace is read-only
            desc = "**Target Workspace** (read-only): The library environment where code is verified. Verification executes against the actual library definitions in this workspace. Files in this workspace cannot be modified."
        else:
            # Target workspace is writable (may require user confirmation in CLI mode)
            if is_cli_mode:
                desc = "**Target Workspace**: The production environment containing the formal project structure. Verification runs against the actual library definitions in this workspace. File editing tools will automatically prompt for user confirmation before applying any modifications to this workspace.\n\n**IMPORTANT WARNING**: Do NOT directly write or edit files in target workspace. Always develop and verify your code in scratch workspace first, then copy verified files to target workspace only after verification confirms they are correct."
            else:
                desc = "**Target Workspace**: The production environment containing the formal project structure. Verification runs against the actual library definitions in this workspace.\n\n**IMPORTANT WARNING**: Do NOT directly write or edit files in target workspace. Always develop and verify your code in scratch workspace first, then copy verified files to target workspace only after verification confirms they are correct."

        parts.append(desc)
        _collect_blocked_note(target_workspace, "target")

    # Reference workspaces
    if reference_workspaces:
        ref_names = [f"'{ws.name}'" for ws in reference_workspaces]
        ref_list_text = ", ".join(ref_names)
        desc = f"**Reference Workspaces** ({ref_list_text}): Additional read-only library environments for cross-referencing. These provide supplementary context and examples."

        parts.append(desc)
        for ws in reference_workspaces:
            _collect_blocked_note(ws, f"reference/{ws.name}")

    if not parts:
        return ""

    # Build full section with environment tags
    workspace_section = "<environment>\n\n"
    workspace_section += "You operate within a workspace architecture designed to balance creative freedom with system safety:\n\n"
    workspace_section += "\n\n".join(parts)
    if blocked_notes:
        workspace_section += (
            "\n\n**Blocked Paths - Independent Implementation Required**: The following paths are intentionally blocked to ensure independent implementation. These files often contain reference implementations that you must NOT use or depend on. Your task is to implement the required functionality from scratch, without accessing these files:\n"
            + "\n".join(blocked_notes)
            + "\n\n**Critical Understanding**: "
            + "If you encounter a blocked file that seems necessary for your task, this means you should implement that functionality independently rather than depending on the blocked file. "
            + "Blocked files are typically the subject of the implementation task itself - you must create your own version without accessing them. "
            + "When searching, exclude blocked paths explicitly. Example: `grep -r \"pattern\" target --exclude=\"PATH\"`.\n\n"
        )

    workspace_section += "\n\n</environment>"

    return workspace_section


# =============================================================================
# Main System Prompt Builder
# =============================================================================

async def build_system_prompt(
    scratch_workspace: Optional['WorkspaceInfo'],
    target_workspace: Optional['WorkspaceInfo'],
    reference_workspaces: Optional[List['WorkspaceInfo']],
    is_cli_mode: bool = False,
    use_absolute_paths: bool = False,
    logger: Optional['logging.LoggerAdapter'] = None
) -> str:
    """
    Build complete system prompt for any scaffold.

    Args:
        scratch_workspace: Scratch workspace info
        target_workspace: Target workspace info
        reference_workspaces: List of reference workspaces
        is_cli_mode: Whether in CLI interactive mode
        use_absolute_paths: Whether to use absolute paths instead of relative paths
        logger: Logger for debug info

    Returns:
        Complete system prompt string
    """
    # Build components
    paths_section = await build_workspace_paths_section(
        scratch_workspace,
        target_workspace,
        reference_workspaces,
        use_absolute_paths=use_absolute_paths,
    )

    content_section = await build_workspace_content_section(
        scratch_workspace,
        target_workspace,
        reference_workspaces,
        is_cli_mode,
        logger
    )

    # Assemble final prompt - select base prompt based on mode
    base_prompt = CLI_MODE_SYSTEM_PROMPT if is_cli_mode else BATCH_MODE_SYSTEM_PROMPT
    prompt_parts = [base_prompt]

    if paths_section:
        prompt_parts.append(paths_section)

    if content_section:
        prompt_parts.append(content_section)

    return "\n\n".join(prompt_parts)
