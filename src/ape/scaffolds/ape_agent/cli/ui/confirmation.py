"""
User Confirmation Bridge - user confirmation bridge

Uses arrow key selection in the command line input position.
Completely matches the visual style of InputHandler.get_user_input(), no extra decorations.
"""

import asyncio
from typing import Dict, Any, List
from rich.console import Console
from rich.rule import Rule
from prompt_toolkit import prompt
from prompt_toolkit.key_binding import KeyBindings


class UserDeclinedConfirmation(Exception):
    """User declined the operation, should return to the user input interface"""
    pass


class UserConfirmationBridge:
    """User confirmation bridge - use arrow keys in the input interface"""

    def __init__(self, console: Console, input_handler=None):
        """
        Initialize user confirmation bridge

        Args:
            console: Rich Console object
            input_handler: InputHandler instance, used to temporarily stop the interrupt listener
        """
        self.console = console
        self.input_handler = input_handler
        # record the approved "Always" operation types
        self._always_approved: set[str] = set()
        # mark whether just selected "No" from the confirmation dialog (used to control whether to display the top separator next time)
        self.just_declined = False

    async def request_confirmation(self,
                                 tool_name: str,
                                 action_description: str,
                                 details: Dict[str, Any]) -> bool:
        """
        Request user confirmation operation

        Args:
            tool_name: tool name
            action_description: operation description
            details: operation details

        Returns:
            whether the user confirmed
        """
        # check if "Always" is set
        operation_key = self._get_operation_key(tool_name, details)
        if operation_key in self._always_approved:
            return True

        # get user choice
        choice = await self._get_user_choice(action_description)

        # handle choice
        if choice == "always":
            self._always_approved.add(operation_key)
            self.just_declined = False
            return True
        elif choice == "yes":
            self.just_declined = False
            return True
        else:  # "no"
            # set flag to indicate just declined confirmation
            self.just_declined = True
            # throw special exception, let the conversation manager return to the user input interface
            raise UserDeclinedConfirmation("User declined the operation")

    def _get_operation_key(self, tool_name: str, details: Dict[str, Any]) -> str:
        """
        Generate operation key, used to record Always option

        For target workspace operation, the key is "tool_name:target"
        """
        workspace = details.get("workspace") or details.get("target_workspace")
        if workspace == "target":
            return f"{tool_name}:target"
        return tool_name

    async def _get_user_choice(self, action_description: str) -> str:
        """
        Get user choice, using prompt_toolkit to implement pure text arrow key selection

        Completely matches the visual style of InputHandler.get_user_input():
        - display black separator above and below
        - display pure text, no decorations
        - only use > to mark the current selected item

        Args:
            action_description: operation description

        Returns:
            "yes", "no", or "always"
        """
        choices = [
            ("yes", "Yes"),
            ("always", "Always (skip all future confirmations for target workspace)"),
            ("no", "No (decline and return to input prompt)")
        ]

        selected_index = [0]  # current selected index

        # temporarily stop the interrupt listener (to avoid ESC key being captured by the listener)
        interrupt_was_active = False
        if self.input_handler is not None:
            # check if the listener is active
            if self.input_handler._interrupt_listener_task is not None:
                interrupt_was_active = True
                self.input_handler.stop_interrupt_listener()

        try:
            # display top separator (black, full width) - consistent with get_user_input()
            self.console.print(Rule(style="black"))

            # display question (pure text, no bold)
            print(action_description)

            # display option list
            self._print_choices(choices, selected_index[0])

            # create key bindings
            kb = KeyBindings()

            @kb.add('up')
            def move_up(event):
                selected_index[0] = (selected_index[0] - 1) % len(choices)
                self._update_choices(choices, selected_index[0])

            @kb.add('down')
            def move_down(event):
                selected_index[0] = (selected_index[0] + 1) % len(choices)
                self._update_choices(choices, selected_index[0])

            @kb.add('enter')
            def select_choice(event):
                event.app.exit(result=choices[selected_index[0]][0])

            @kb.add('escape')
            def handle_escape(event):
                """Handle ESC key - should do nothing, not trigger interrupt"""
                # ESC in confirmation dialog should not trigger interrupt, just be ignored
                # if user wants to cancel, should use Ctrl+C or select "No"
                pass

            @kb.add('c-c')
            def cancel_c(event):
                """Ctrl+C: exit the entire system"""
                event.app.exit(exception=KeyboardInterrupt)

            @kb.add('c-d')
            def cancel_d(event):
                """Ctrl+D: exit the entire system"""
                event.app.exit(exception=EOFError)

            # use prompt to wait for user choice (no prompt, only accept key bindings)
            # do not use default and accept_default, force user to select through key bindings
            result = await asyncio.to_thread(
                lambda: prompt(
                    "",
                    key_bindings=kb,
                    mouse_support=False,
                    multiline=False,
                    enable_system_prompt=False,
                    prompt_continuation=None
                )
            )

            # clear empty lines left by prompt (move cursor up, clear current line)
            import sys
            sys.stdout.write('\033[1A')  # move cursor up 1 line
            sys.stdout.write('\033[K')   # Clear the current line
            sys.stdout.flush()

            # only display bottom separator when user selects Yes/Always
            # do not display when user selects No, because it will directly return to user input (will display its own top separator)
            if result and result != "no":
                self.console.print(Rule(style="black"))

            return result if result else "no"

        except (EOFError, KeyboardInterrupt) as e:
            # Ctrl+C/D: clear interface and re-throw exception, let the system exit
            self.console.print(Rule(style="black"))
            # restore interrupt listener
            if interrupt_was_active and self.input_handler is not None:
                self.input_handler.start_interrupt_listener()
            raise  # re-throw exception to exit system
        except Exception:
            import traceback
            import sys
            print(f"Confirmation error: {traceback.format_exc()}", file=sys.stderr)
            self.console.print(Rule(style="black"))
            return "no"
        finally:
            # restore interrupt listener (normal flow)
            if interrupt_was_active and self.input_handler is not None:
                self.input_handler.start_interrupt_listener()

    def _print_choices(self, choices: List, selected_index: int):
        """Print option list for the first time"""
        import sys
        for i, (_, label) in enumerate(choices):
            if i == selected_index:
                sys.stdout.write(f"> {label}\n")
            else:
                sys.stdout.write(f"  {label}\n")
        sys.stdout.flush()

    def _update_choices(self, choices: List, selected_index: int):
        """Update option display (move cursor up and redraw)"""
        import sys
        # move cursor up n lines to the start of the option list
        # the cursor is currently on the empty line below the option list, so need to move up n lines
        sys.stdout.write(f'\033[{len(choices)}A')

        # redraw each line
        for i, (_, label) in enumerate(choices):
            sys.stdout.write('\r')      # move to the start of the line
            sys.stdout.write('\033[K')  # clear current line
            if i == selected_index:
                sys.stdout.write(f"> {label}")
            else:
                sys.stdout.write(f"  {label}")
            sys.stdout.write('\n')      # move to the next line

        sys.stdout.flush()
