"""
Input Handler for CLI

Handles user input, keyboard events, and command processing.
"""

import asyncio
import sys
import traceback
from typing import Optional, Callable, Dict, Any, Tuple, List, TYPE_CHECKING
from prompt_toolkit import prompt
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.shortcuts import confirm
from prompt_toolkit.input import create_input
from prompt_toolkit.keys import Keys
from rich.console import Console
from ape.utils.logging import create_logger

from .colors import colors

if TYPE_CHECKING:
    from prompt_toolkit.key_binding.key_processor import KeyPressEvent
    import logging


class InputHandler:
    """Input handler, handles user input and keyboard events"""

    def __init__(self, console: Console, logger=None):
        """
        Initialize input handler

        Args:
            console: Rich Console object
            logger: Logger instance, if None, create console logger
        """
        self.console = console
        self.logger = logger or create_logger()
        self.command_handlers: Dict[str, Callable] = {}
        self.key_bindings = None
        self._setup_key_bindings()

        # interrupt mechanism
        self.interrupt_requested = asyncio.Event()
        self._interrupt_listener_task: Optional[asyncio.Task] = None
        
    def _setup_key_bindings(self):
        """Setup keyboard bindings"""
        self.key_bindings = KeyBindings()

        @self.key_bindings.add('c-d')
        def _(event: 'KeyPressEvent') -> None:
            """Ctrl+D handling - directly exit system"""
            event.app.exit(exception=EOFError)

    def start_interrupt_listener(self):
        """Start ESC key interrupt listener (listen during model execution)"""
        if self._interrupt_listener_task is not None:
            return  # already running

        self.interrupt_requested.clear()
        self._interrupt_listener_task = asyncio.create_task(self._listen_for_interrupt())
        self.logger.debug("ESC interrupt listener started")

    def stop_interrupt_listener(self):
        """Stop interrupt listener"""
        if self._interrupt_listener_task is not None:
            self._interrupt_listener_task.cancel()
            self._interrupt_listener_task = None
            self.interrupt_requested.clear()
            self.logger.debug("ESC interrupt listener stopped")

    async def _listen_for_interrupt(self):
        """Background task: listen for ESC key press"""
        try:
            import termios
            import tty

            # save original terminal settings
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)

            try:
                # set to cbreak mode (non-blocking single character read)
                tty.setcbreak(fd)

                while True:
                    # non-blocking check for input
                    import select
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        ch = sys.stdin.read(1)
                        # ASCII code for ESC key is 27 (0x1b)
                        if ord(ch) == 27:
                            self.logger.info("ESC key pressed - interrupt requested")
                            self.interrupt_requested.set()
                            # show prompt information
                            self.console.print(f"\n[{colors.accent_yellow}]● Interrupt requested (ESC pressed)...[/{colors.accent_yellow}]")
                            break

                    await asyncio.sleep(0.05)  # brief sleep to avoid high CPU usage

            finally:
                # restore terminal settings
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

        except asyncio.CancelledError:
            self.logger.debug("Interrupt listener cancelled")
        except Exception as e:
            self.logger.error(f"Error in interrupt listener: {traceback.format_exc()}")
    
    
    def register_command_handler(self, command: str, handler: Callable):
        """
        Register slash command handler
        
        Args:
            command: command name (without slash)
            handler: command handler function
        """
        self.command_handlers[command] = handler
    
    async def get_user_input(self, prompt_text: str = "> ", show_top_separator: bool = True) -> Optional[str]:
        """
        Get user input, support different types of interrupt handling

        Args:
            prompt_text: prompt text
            show_top_separator: whether to display top separator (default True)

        Returns:
            user input text, if interrupted, return None, special interrupt will raise corresponding exception
        """
        from rich.rule import Rule

        try:
            # display top separator (black, full width)
            if show_top_separator:
                self.console.print(Rule(style="black"))
            else:
                # return from confirmation dialog: clear empty line, then display top separator
                import sys
                sys.stdout.write('\033[1A')  # move up 1 line
                sys.stdout.write('\033[K')   # clear current line
                sys.stdout.flush()
                self.console.print(Rule(style="black"))

            # run prompt in a separate thread to avoid blocking
            user_input = await asyncio.to_thread(
                lambda: prompt(
                    prompt_text,
                    key_bindings=self.key_bindings,
                    complete_style="answer",
                    enable_history_search=True,  # enable history search
                    wrap_lines=True,  # auto wrap lines
                    mouse_support=False,  # disable mouse support to allow terminal scrolling
                    color_depth="DEPTH_8_BIT"  # better color support
                )
            )

            # display bottom separator (black, full width)
            self.console.print(Rule(style="black"))

            return user_input.strip() if user_input else None

        except EOFError:
            # Ctrl+D: directly exit
            text = f"[{colors.accent_cyan}]Goodbye![/{colors.accent_cyan}]"
            self.console.print(text)
            raise  # re-throw to let upper layer handle

        except KeyboardInterrupt:
            # old-style keyboard interrupt, as forced interrupt handling
            return None
        except Exception as e:
            self.logger.error(f"Error getting user input: {traceback.format_exc()}")
            return None
    
    async def get_multiline_input(self, prompt_text: str = "> (multi-line) ") -> Optional[str]:
        """
        Get multiline user input, for complex content input
        
        Args:
            prompt_text: prompt text
            
        Returns:
            multiline user input text
        """
        try:
            tip_text = f"[{colors.gray}]💡 Tip: Press Meta+Enter or Ctrl+Enter to submit, ESC to cancel[/{colors.gray}]"
            self.console.print(tip_text)
            
            user_input = await asyncio.to_thread(
                lambda: prompt(
                    prompt_text,
                    multiline=True,
                    key_bindings=self.key_bindings,
                    complete_style="answer",
                    wrap_lines=True,
                    mouse_support=False  # disable mouse support to allow terminal scrolling
                )
            )
            
            return user_input.strip() if user_input else None
            
        except KeyboardInterrupt:
            cancel_text = f"[{colors.accent_yellow}]Multiline input cancelled[/{colors.accent_yellow}]"
            self.console.print(cancel_text)
            return None
        except EOFError:
            return None
        except Exception as e:
            self.logger.error(f"Error getting multiline input: {traceback.format_exc()}")
            return None
    
    def is_command(self, user_input: str) -> bool:
        """
        Check if input is a slash command
        
        Args:
            user_input: user input
            
        Returns:
            whether it is a command
        """
        return user_input.startswith("/") and len(user_input) > 1
    
    def parse_command(self, user_input: str) -> Tuple[str, List[str]]:
        """
        Parse slash command, support quoted parameters
        
        Args:
            user_input: user input
            
        Returns:
            (command name, parameter list)
        """
        import shlex
        
        # remove the leading slash
        command_line = user_input[1:]
        
        try:
            # use shlex to correctly handle quotes and escapes
            parts = shlex.split(command_line)
        except ValueError:
            # if parsing fails, fall back to simple split
            parts = command_line.split()
        
        command = parts[0] if parts else ""
        args = parts[1:] if len(parts) > 1 else []
        
        return command, args
    
    async def handle_command(self, command: str, args: List[str]) -> bool:
        """
        Handle slash command
        
        Args:
            command: command name
            args: command parameters
            
        Returns:
            whether the command is successfully handled
        """
        if command in self.command_handlers:
            try:
                handler = self.command_handlers[command]
                
                # check if the handler is an asynchronous function
                if asyncio.iscoroutinefunction(handler):
                    await handler(args)
                else:
                    handler(args)
                
                return True
                
            except Exception as e:
                self.logger.error(f"Error handling command '{command}': {traceback.format_exc()}")
                error_text = f"[{colors.accent_red}]Error executing command '{command}': {traceback.format_exc()}[/{colors.accent_red}]"
                self.console.print(error_text)
                return False
        else:
            unknown_text = f"[{colors.accent_yellow}]Unknown command: /{command}[/{colors.accent_yellow}]"
            help_text = f"[{colors.gray}]Type /help for available commands[/{colors.gray}]"
            self.console.print(unknown_text)
            self.console.print(help_text)
            return False
    
    async def confirm_action(self, message: str, default: bool = False) -> bool:
        """
        Confirm user operation
        
        Args:
            message: confirmation message
            default: default value
            
        Returns:
            user confirmation result
        """
        try:
            result = await asyncio.to_thread(
                lambda: confirm(message, default=default)
            )
            return result
        except (KeyboardInterrupt, EOFError):
            return False
        except Exception as e:
            self.logger.error(f"Error getting confirmation: {traceback.format_exc()}")
            return False
    
    async def get_choice(self, message: str, choices: List[str], default: Optional[str] = None) -> Optional[str]:
        """
        Get user choice
        
        Args:
            message: choice prompt message
            choices: choice options list
            default: default choice
            
        Returns:
            user selected choice
        """
        try:
            # display choice options
            self.console.print(f"[bold]{message}[/bold]")
            for i, choice in enumerate(choices, 1):
                default_marker = " (default)" if choice == default else ""
                self.console.print(f"  {i}. {choice}{default_marker}")
            
            # get user input
            while True:
                user_input = await self.get_user_input("Choose [1-{0}]: ".format(len(choices)))
                
                if user_input is None:
                    return None
                
                if not user_input and default:
                    return default
                
                try:
                    choice_index = int(user_input) - 1
                    if 0 <= choice_index < len(choices):
                        return choices[choice_index]
                    else:
                        error_text = f"[{colors.accent_red}]Please choose a number between 1 and {len(choices)}[/{colors.accent_red}]"
                        self.console.print(error_text)
                except ValueError:
                    # try to match text
                    user_input_lower = user_input.lower()
                    for choice in choices:
                        if choice.lower().startswith(user_input_lower):
                            return choice
                    
                    invalid_text = f"[{colors.accent_red}]Invalid choice: {user_input}[/{colors.accent_red}]"
                    self.console.print(invalid_text)
                    
        except Exception as e:
            self.logger.error(f"Error getting user choice: {traceback.format_exc()}")
            return None
    
