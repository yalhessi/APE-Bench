"""
APE Agent Scaffold Module.

Provides conversation-based scaffold implementation with support
for both batch processing and CLI modes.
"""

import asyncio
import traceback
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from pathlib import Path
import uuid

from ape.scaffolds.base import BaseScaffold
from ape.scaffolds.skills import (
    APE_AGENT_REPO_SKILL_DIRS,
    SKILL_TOOL_NAMES,
    materialize_task_skills,
)
from rich.console import Console

from .conversation import ApeAgentConversationManager
from ape.toolkits.mcp_manager import MCPManager
from ape.toolkits.registry import get_all_tool_names
import ape.toolkits.skills  # noqa: F401
from .config import ApeAgentConfig

if TYPE_CHECKING:
    from ape.tasks.base import BaseTask
    from ape.llm_clients.models import TokenUsage
    from .cli.ui.input import InputHandler
    from .cli.ui.display import CLIDisplay
    from .cli.ui.streaming import StreamingOutputHandler
    from .cli.ui.confirmation import UserConfirmationBridge


class ApeAgentScaffold(BaseScaffold):
    """APE Agent Scaffold implementation.

    Manages LLM conversation flow and tool coordination,
    supporting both batch processing and CLI modes.
    """

    config_class = ApeAgentConfig

    def __init__(self):
        """Initialize ApeAgent-specific components."""
        super().__init__()
        self.console: Optional[Console] = None
        self.confirmation_bridge = None
        self.conversation_manager: Optional[ApeAgentConversationManager] = None
        self.mcp_manager: Optional[MCPManager] = None
        self.conversation_session = None
        self.managed_skills = None
    
    async def run_interactive_session(
        self,
        task: 'BaseTask',
        initial_prompt: Optional[str] = None,
        oneshot_mode: bool = False
    ) -> None:
        """Convenience entry point for CLI mode."""
        async def termination_callback(_result) -> None:
            """Stop the interactive conversation when a task submits a final result."""
            if self.conversation_manager is not None:
                self.conversation_manager.request_stop()
                if self.logger:
                    self.logger.info("[ApeAgentScaffold] Interactive task submitted a result; stopping session")

        task._cli_initial_prompt = initial_prompt
        task._cli_oneshot_mode = oneshot_mode
        await self.solve(
            task=task,
            termination_callback=termination_callback,
            orchestrator_id="cli",
            attempt_path=None,
            cost_limit=None
        )

    async def _setup_components(self) -> None:
        """Set up ApeAgent-specific components."""
        await self._emit_progress("Initializing APE Agent conversation manager...")
        if self.is_cli_mode:
            from .cli.ui.confirmation import UserConfirmationBridge
            self.console = Console()
            self.confirmation_bridge = UserConfirmationBridge(self.console)
            self.logger.debug("CLI mode: initialized console and UserConfirmationBridge")

        self.managed_skills = materialize_task_skills(
            self.task,
            self.logger,
            repo_skill_dirs=APE_AGENT_REPO_SKILL_DIRS,
        )

        self.conversation_manager = ApeAgentConversationManager(
            config=self.task.config,
            task=self.task,
            cost_limit=self.cost_limit,
            logger=self.logger,
            interrupt_event=None,
            is_cli_mode=self.is_cli_mode
        )
        await self.conversation_manager.initialize()

        await self._emit_progress("Registering tools and starting the in-process MCP server...")
        await self._setup_tools()
        self.conversation_session = None

    async def _setup_tools(self) -> None:
        """Set up MCP tools using MCPManager."""
        enabled_tools = self._calculate_enabled_tools()

        # Create MCPManager
        self.mcp_manager = MCPManager(
            task=self.task,
            logger=self.logger,
            config=self.task.config,
            confirmation_bridge=self.confirmation_bridge,
            is_cli_mode=self.is_cli_mode,
            use_native_tools=True,  # ApeAgent uses our native MCP tools
        )

        # Setup in direct mode (FastMCP + Client)
        await self.mcp_manager.setup_direct_mode(custom_enabled_tools=enabled_tools)

        self.logger.info(f"[ApeAgentScaffold] MCPManager setup complete with {len(enabled_tools)} tools")

    def _calculate_enabled_tools(self) -> set[str]:
        """Calculate enabled tool set."""
        config = self.task.config
        task_config = config.task_config
        all_available_tools = set(get_all_tool_names())
        has_managed_skills = bool(self.managed_skills and self.managed_skills.skills)
        if not has_managed_skills:
            all_available_tools -= SKILL_TOOL_NAMES
        
        if task_config.enabled_tools is not None:
            base_enabled = set(task_config.enabled_tools) & all_available_tools
        else:
            base_enabled = all_available_tools - set(task_config.disabled_tools or [])

        if has_managed_skills:
            disabled_tools = set(task_config.disabled_tools or [])
            base_enabled |= (SKILL_TOOL_NAMES - disabled_tools) & all_available_tools
        
        return base_enabled

    async def _run_batch_mode(self) -> None:
        """Execute batch processing mode."""
        initial_prompt = await self.task.create_user_prompt()
        self.logger.info(f"[ApeAgentScaffold] Starting batch conversation")

        await self.conversation_manager.run_conversation(
            prompt=initial_prompt,
            mcp_instance=self.mcp_manager.get_client(),
            force_tool_use=True
        )

        self.logger.info("[ApeAgentScaffold] Conversation terminated externally (submit_result)")

    async def _run_cli_mode(self) -> None:
        """Execute CLI mode."""
        from .cli.ui.display import CLIDisplay
        from .cli.ui.input import InputHandler
        from .cli.ui.streaming import StreamingOutputHandler

        display = CLIDisplay(self.console)
        input_handler = InputHandler(self.console, self.logger)
        streaming_handler = StreamingOutputHandler(self.console)

        if self.confirmation_bridge is not None:
            self.confirmation_bridge.input_handler = input_handler

        async def user_input_callback() -> Optional[str]:
            """Get user input, handle commands and special cases."""
            input_handler.stop_interrupt_listener()

            while True:
                try:
                    show_separator = True
                    if self.confirmation_bridge and self.confirmation_bridge.just_declined:
                        show_separator = False
                        self.confirmation_bridge.just_declined = False

                    user_input = await input_handler.get_user_input("> ", show_top_separator=show_separator)

                    if user_input is None or not user_input:
                        continue

                    if input_handler.is_command(user_input):
                        command, args = input_handler.parse_command(user_input)

                        if command in ['quit', 'exit']:
                            return None

                        await input_handler.handle_command(command, args)
                        continue

                    input_handler.start_interrupt_listener()
                    return user_input

                except EOFError:
                    self.logger.info("CLI session ended by EOF")
                    return None

                except KeyboardInterrupt:
                    display.show_warning("Session interrupted by user")
                    self.logger.info("CLI session interrupted by user (KeyboardInterrupt)")
                    return None

                except Exception as e:
                    display.show_error(f"Error getting input: {e}")
                    self.logger.error(f"Error in input loop:\n{traceback.format_exc()}")
                    continue

        def streaming_callback(content, content_type: str = 'content'):
            if content_type == 'tool_call':
                streaming_handler.show_tool_call(content)
            elif content_type == 'tool_result':
                streaming_handler.show_tool_result(content)
            else:
                streaming_handler.update_streaming_content(
                    content_chunk=content,
                    content_type=content_type
                )

        try:
            self.conversation_manager.interrupt_event = input_handler.interrupt_requested

            self._setup_cli_commands(input_handler, display)

            initial_prompt = self.task._cli_initial_prompt
            oneshot_mode = self.task._cli_oneshot_mode

            if not initial_prompt and not oneshot_mode:
                while True:
                    try:
                        user_input = await input_handler.get_user_input("> ")

                        if user_input is None or not user_input:
                            continue

                        if input_handler.is_command(user_input):
                            command, args = input_handler.parse_command(user_input)

                            if command in ['quit', 'exit']:
                                self.logger.info("User quit before starting conversation")
                                return

                            await input_handler.handle_command(command, args)
                            continue

                        initial_prompt = user_input
                        break

                    except EOFError:
                        self.logger.info("CLI session ended by EOF before starting")
                        return

                    except KeyboardInterrupt:
                        display.show_warning("Session interrupted by user")
                        return

                    except Exception as e:
                        display.show_error(f"Error getting initial input: {e}")
                        self.logger.error(f"Error:\n{traceback.format_exc()}")
                        continue

            from ape.scaffolds.base import ConversationStoppedError
            from ape.llm_clients.config import CostExhaustedError

            streaming_handler.start_streaming_response()
            input_handler.start_interrupt_listener()

            await self.conversation_manager.run_conversation(
                prompt=initial_prompt,
                mcp_instance=self.mcp_manager.get_client(),
                force_tool_use=getattr(self.task, "_cli_force_tool_use", False),
                streaming=True,
                streaming_callback=streaming_callback,
                user_input_callback=user_input_callback if not oneshot_mode else None
            )

        except ConversationStoppedError as e:
            error_msg = f"\n⚠️  Conversation stopped: {str(e)}"
            streaming_handler.update_streaming_content(
                content_chunk=error_msg, content_type='content'
            )
            self.logger.warning(f"CLI conversation stopped: {e}")
        except CostExhaustedError as e:
            error_msg = f"\n💰 Cost limit exceeded: {str(e)}"
            streaming_handler.update_streaming_content(
                content_chunk=error_msg, content_type='content'
            )
            self.logger.warning(f"CLI cost exhausted: {e}")
        except Exception as e:
            error_msg = f"\nError during conversation: {e}"
            streaming_handler.update_streaming_content(
                content_chunk=error_msg, content_type='content'
            )
            self.logger.error(f"Error in CLI session: {traceback.format_exc()}")
            raise
        finally:
            input_handler.stop_interrupt_listener()
            streaming_handler.finish_streaming_response()

    def _setup_cli_commands(self, input_handler: 'InputHandler', display: 'CLIDisplay'):
        """Set up CLI command handlers."""
        input_handler.register_command_handler(
            'help', lambda args: display.show_help()
        )
        input_handler.register_command_handler(
            'clear', lambda args: display.clear_screen()
        )

    def _get_token_usage(self) -> Optional['TokenUsage']:
        """Get token usage statistics."""
        return self.conversation_manager.get_token_usage()

    def _get_current_turns(self) -> int:
        """Get current conversation turns."""
        return self.conversation_manager.get_current_turns()

    async def _interrupt_execution(self) -> None:
        """Interrupt internal execution."""
        self.conversation_manager.request_stop()
        self.logger.info("[ApeAgentScaffold] Interrupt signal sent to conversation manager")

    async def _cleanup_components(self) -> None:
        """Clean up ApeAgent-specific components."""
        if self.conversation_manager:
            try:
                await self.conversation_manager.cleanup()
                self.logger.debug("Conversation manager cleaned up successfully")
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Error cleaning conversation manager: {e}")

        # Clean up MCPManager (this will clean up all tool instances and MCP client)
        if self.mcp_manager:
            try:
                await self.mcp_manager.cleanup()
                self.logger.debug("MCPManager cleaned up successfully")
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Error cleaning MCPManager: {e}")

        self.conversation_manager = None
        self.mcp_manager = None
        self.conversation_session = None


from ape.scaffolds.registry import register_scaffold
register_scaffold("ape_agent", ApeAgentScaffold)
