"""Registry of supported interactive agent CLI entrypoints."""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from typing import Any, Callable, Optional

from ape.cli.launchers import build_external_launcher, launch_ape_agent
from ape.scaffolds.ape_agent.cli.config import ApeAgentCLIConfig
from ape.scaffolds.ape_agent.cli.task import CLITask, CLITaskConfig, CLITaskData
from ape.scaffolds.claude_code.cli.config import ClaudeCodeCLIConfig
from ape.scaffolds.claude_code.cli.task import CLITask as ClaudeCodeCLITask
from ape.scaffolds.claude_code.cli.task import CLITaskConfig as ClaudeCodeCLITaskConfig
from ape.scaffolds.claude_code.cli.task import CLITaskData as ClaudeCodeCLITaskData
from ape.scaffolds.codex.cli.config import CodexCLIConfig
from ape.scaffolds.codex.cli.task import CodexCLITask, CodexCLITaskConfig, CodexCLITaskData


ParserHook = Callable[[argparse.ArgumentParser], None]
ConfigOverrideHook = Callable[[dict[str, Any], argparse.Namespace], None]
Launcher = Callable[[Any, Any, argparse.Namespace], int]


@dataclass(frozen=True)
class AgentCliSpec:
    """Metadata and builders for a supported agent CLI."""

    command_name: str
    scaffold_type: str
    alias_name: str
    description: str
    help_text: str
    epilog: str
    config_class: type
    task_config_class: type
    task_data_class: type
    task_class: type
    task_id_prefix: str
    model_default: Optional[str]
    model_help: str
    retrieve_commit_hash_default: Optional[str] = None
    retrieve_repo_url_default: Optional[str] = None
    retrieve_default_target_default: Optional[str] = None
    add_agent_arguments: Optional[ParserHook] = None
    apply_argument_overrides: Optional[ConfigOverrideHook] = None
    launch: Optional[Launcher] = None


def _add_ape_agent_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--oneshot_mode",
        action="store_true",
        help="Exit after processing initial prompt",
    )
    parser.add_argument(
        "--open_in_vscode",
        action="store_true",
        default=None,
        help="Open files in VS Code after editing (default: True, auto-disabled if not in VS Code terminal)",
    )


def _add_external_cli_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--extra-arg",
        action="append",
        default=[],
        dest="extra_args",
        help="Extra arguments passed to the underlying agent command (can be repeated)",
    )


def _apply_ape_agent_overrides(config_dict: dict[str, Any], args: argparse.Namespace) -> None:
    if args.model is not None:
        llm_config = config_dict.setdefault("llm_config", {})
        llm_config["model_name"] = args.model

    if args.log_level is not None:
        config_dict["log_level"] = args.log_level

    term_program = os.environ.get("TERM_PROGRAM", "")
    if args.open_in_vscode is not None:
        open_in_vscode_enabled = term_program == "vscode"
        config_dict["open_in_vscode"] = open_in_vscode_enabled
    elif config_dict.get("open_in_vscode"):
        config_dict["open_in_vscode"] = term_program == "vscode"
    elif "open_in_vscode" not in config_dict:
        config_dict["open_in_vscode"] = term_program == "vscode"


def _apply_external_overrides(config_dict: dict[str, Any], args: argparse.Namespace) -> None:
    if args.model is not None:
        llm_config = config_dict.setdefault("llm_config", {})
        llm_config["model_name"] = args.model

    if args.log_level is not None:
        config_dict["log_level"] = args.log_level


APE_AGENT_EPILOG = """
An AI assistant based on dialogue, specialized for Lean theorem proving and formal mathematics.

Configuration Override Examples (use Python literal syntax):
  ape chat ape-agent --workspace /path/to/workspace llm_config.model_name=gpt_5_mini
  ape chat ape-agent --prompt "Help me prove theorem X" llm_config.temperature=0.7
  ape chat ape-agent llm_config.max_tokens=8000
  ape chat ape-agent llm_config.streaming=False
  ape chat ape-agent --log-level WARNING  # Reduce log output (default)
  ape chat ape-agent --log-level DEBUG    # Full debug logging

Workspace and Retrieve Tool Examples:
  ape chat ape-agent --workspace /path/to/lean/project  # Use local workspace
  ape chat ape-agent --verify_commit_hash abc123 --verify_repo_url https://github.com/user/repo.git
  ape chat ape-agent  # Use current directory as workspace
"""

CLAUDE_CODE_EPILOG = """
Claude Code CLI is an enhanced version of the claude command line tool, providing:
- Automatically configure relay mode and conversation tracking
- Automatically configure MCP server
- Record complete conversation history

Examples:
  ape chat claude-code --workspace /path/to/workspace
  ape chat claude-code --prompt "Help me with this task"
  ape chat claude-code --model deepseek_v3.1 --workspace .

Configuration Override (use Python literal syntax):
  ape chat claude-code llm_config.temperature=0.7
  ape chat claude-code llm_config.streaming=False
  ape chat claude-code llm_config.max_tokens=8000
  ape chat claude-code task_config.enabled_tools='["Read","Write"]'
"""

CODEX_EPILOG = """
Codex CLI is an enhanced version of the codex command line tool, providing:
- Automatically configure relay mode and conversation tracking
- Automatically configure MCP server
- Automatically configure ~/.codex/config.toml
- Record complete conversation history

Examples:
  ape chat codex --workspace /path/to/workspace
  ape chat codex --prompt "Help me with this task"
  ape chat codex --model gpt_5 --workspace .

Configuration Override (use Python literal syntax):
  ape chat codex llm_config.temperature=0.7
  ape chat codex llm_config.streaming=False
  ape chat codex llm_config.max_tokens=8000
"""


AGENT_CLI_SPECS: dict[str, AgentCliSpec] = {
    "ape-agent": AgentCliSpec(
        command_name="ape-agent",
        scaffold_type="ape_agent",
        alias_name="apea",
        description="APE-Agent CLI - Interactive AI Assistant for Formal Mathematics",
        help_text="Launch the built-in APE-Agent interactive session",
        epilog=APE_AGENT_EPILOG,
        config_class=ApeAgentCLIConfig,
        task_config_class=CLITaskConfig,
        task_data_class=CLITaskData,
        task_class=CLITask,
        task_id_prefix="cli-",
        model_default="gpt_5_mini",
        model_help="Model name to use (default: gpt_5_mini, overrides model in configuration)",
        retrieve_commit_hash_default="2df2f0150c275ad53cb3c90f7c98ec15a56a1a67",
        retrieve_repo_url_default="https://github.com/leanprover-community/mathlib4.git",
        retrieve_default_target_default="Mathlib",
        add_agent_arguments=_add_ape_agent_arguments,
        apply_argument_overrides=_apply_ape_agent_overrides,
        launch=launch_ape_agent,
    ),
    "claude-code": AgentCliSpec(
        command_name="claude-code",
        scaffold_type="claude_code",
        alias_name="ape-claude",
        description="Claude Code CLI - Enhanced claude command with MCP and conversation tracking",
        help_text="Launch the Claude Code-backed interactive session",
        epilog=CLAUDE_CODE_EPILOG,
        config_class=ClaudeCodeCLIConfig,
        task_config_class=ClaudeCodeCLITaskConfig,
        task_data_class=ClaudeCodeCLITaskData,
        task_class=ClaudeCodeCLITask,
        task_id_prefix="claude-cli-",
        model_default=None,
        model_help="Model name to use (default: None - use official Claude Code models, overrides model in configuration)",
        add_agent_arguments=_add_external_cli_arguments,
        apply_argument_overrides=_apply_external_overrides,
        launch=build_external_launcher(
            "ape.scaffolds.claude_code.scaffold",
            "ClaudeCodeScaffold",
        ),
    ),
    "codex": AgentCliSpec(
        command_name="codex",
        scaffold_type="codex",
        alias_name="ape-codex",
        description="Codex CLI - Enhanced codex command with MCP and conversation tracking",
        help_text="Launch the Codex-backed interactive session",
        epilog=CODEX_EPILOG,
        config_class=CodexCLIConfig,
        task_config_class=CodexCLITaskConfig,
        task_data_class=CodexCLITaskData,
        task_class=CodexCLITask,
        task_id_prefix="codex-cli-",
        model_default=None,
        model_help="Model name to use (default: None - use official Codex models, overrides model in configuration)",
        add_agent_arguments=_add_external_cli_arguments,
        apply_argument_overrides=_apply_external_overrides,
        launch=build_external_launcher(
            "ape.scaffolds.codex.scaffold",
            "CodexScaffold",
        ),
    ),
}


def get_agent_cli_spec(command_name: str) -> AgentCliSpec:
    """Return the CLI spec for a supported agent command."""
    try:
        return AGENT_CLI_SPECS[command_name]
    except KeyError as exc:
        available = ", ".join(sorted(AGENT_CLI_SPECS))
        raise ValueError(f"Unknown interactive agent '{command_name}'. Available: {available}") from exc


def list_agent_cli_specs() -> list[AgentCliSpec]:
    """Return all supported agent CLI specs in display order."""
    return [AGENT_CLI_SPECS[name] for name in ("ape-agent", "claude-code", "codex")]
