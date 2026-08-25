"""Rich display helpers for the APE-Agent CLI."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from rich.console import Console
from rich.live import Live
from rich.rule import Rule
from rich.text import Text

from ape.utils.logging import create_logger

from .colors import colors


class CLIDisplay:
    """CLI display manager."""

    def __init__(self, console: Console, logger=None):
        """Initialize the CLI display manager."""
        self.console = console
        self.logger = logger or create_logger()
        self.current_live: Optional[Live] = None
        self.message_history: List[Dict[str, Any]] = []

    def show_welcome(self, subtitle: str) -> None:
        """Show the standard CLI welcome banner."""
        welcome_text = Text()
        welcome_text.append("APE Agent", style="bold")
        welcome_text.append(f" - {subtitle}", style=colors.gray)
        self.console.print(welcome_text)
        self.console.print()

        self.console.print("[bold]Commands[/bold]")
        self.console.print(self._build_command_line("/help", "Show detailed help"))
        self.console.print(self._build_command_line("/clear", "Clear screen"))
        self.console.print(self._build_command_line("/quit", "Exit session"))
        self.console.print()

        self.console.print("[bold]Keyboard Controls[/bold]")
        self.console.print(self._build_key_line("ESC", "Interrupt AI response/tool execution and return to input"))
        self.console.print(self._build_key_line("Ctrl+D", "Exit system"))
        self.console.print()

    def show_quick_help(self) -> None:
        """Show a short getting-started guide."""
        help_text = Text()
        help_text.append("Quick Start:", style="bold")
        help_text.append("\n- Ask Ape Agent to help with theorem proving", style=colors.gray)
        help_text.append("\n- Try: ", style=colors.gray)
        help_text.append('"Help me prove that n + 0 = n in Lean"', style=colors.accent_green)
        help_text.append("\n- Try: ", style=colors.gray)
        help_text.append('"Create a Lean file for basic arithmetic theorems"', style=colors.accent_green)
        help_text.append("\n- Try: ", style=colors.gray)
        help_text.append('"Explain this Lean proof step by step"', style=colors.accent_green)
        help_text.append("\n\nCommands:", style="bold")
        help_text.append("\n- ", style=colors.gray)
        help_text.append("/help", style=colors.accent_cyan)
        help_text.append(" - Show all available commands", style=colors.gray)
        help_text.append("\n- ", style=colors.gray)
        help_text.append("/clear", style=colors.accent_cyan)
        help_text.append(" - Clear the screen", style=colors.gray)
        help_text.append("\n- ", style=colors.gray)
        help_text.append("/quit", style=colors.accent_cyan)
        help_text.append(" or ", style=colors.gray)
        help_text.append("/exit", style=colors.accent_cyan)
        help_text.append(" - Exit the session", style=colors.gray)
        help_text.append("\n\nKeyboard shortcuts:", style="bold")
        help_text.append("\n- Press ", style=colors.gray)
        help_text.append("ESC", style=colors.accent_yellow)
        help_text.append(" to interrupt AI response/tool execution and return to input", style=colors.gray)
        help_text.append("\n- Press ", style=colors.gray)
        help_text.append("Ctrl+D", style=colors.accent_yellow)
        help_text.append(" to exit\n", style=colors.gray)
        self.console.print(help_text)

    def show_tree_section(
        self,
        title: str,
        lines: Sequence[str],
        *,
        accent_color: Optional[str] = None,
        margin_top: bool = True,
        margin_bottom: bool = True,
    ) -> None:
        """Show a titled section with tree-style detail rows."""
        if margin_top:
            self.console.print()

        heading = Text()
        heading.append("● ", style=accent_color or colors.accent_cyan)
        heading.append(title, style="bold")
        self.console.print(heading)

        section_lines = list(lines) or ["(none)"]
        for index, line in enumerate(section_lines):
            connector = "  └─ " if index == len(section_lines) - 1 else "  ├─ "
            row = Text()
            row.append(connector, style=colors.gray)
            row.append(line, style=colors.gray)
            self.console.print(row)

        if margin_bottom:
            self.console.print()

    def show_message_preview(
        self,
        title: str,
        message: str,
        *,
        accent_color: Optional[str] = None,
        max_lines: int = 6,
        max_width: int = 100,
    ) -> None:
        """Show a truncated preview of a long message."""
        preview_lines, was_truncated = self._build_message_preview(
            message,
            max_lines=max_lines,
            max_width=max_width,
        )
        if was_truncated:
            preview_lines.append("... prompt truncated in the terminal; the full prompt is still sent to the agent")

        self.show_tree_section(
            title,
            preview_lines,
            accent_color=accent_color or colors.accent_blue,
        )

    def show_status(self, message: str) -> None:
        """Show a status message."""
        is_progress_update = message.startswith("Lean retrieval indexing ")
        self._show_prefixed_message("● ", message, colors.gray, margin_top=not is_progress_update)

    def show_success(self, message: str) -> None:
        """Show a success message."""
        self._show_prefixed_message("● ", message, colors.accent_green, margin_bottom=True)

    def show_error(self, message: str) -> None:
        """Show an error message."""
        self._show_prefixed_message("● ", message, colors.accent_red, margin_bottom=True)

    def show_warning(self, message: str) -> None:
        """Show a warning message."""
        self._show_prefixed_message("● ", message, colors.accent_yellow, margin_top=True)

    def _show_prefixed_message(
        self,
        prefix: str,
        message: str,
        color: str,
        margin_top: bool = False,
        margin_bottom: bool = False,
    ) -> None:
        """Show a message with a colored prefix."""
        if margin_top:
            self.console.print()

        text = Text()
        text.append(prefix, style=color)
        text.append(message, style=color)
        self.console.print(text)

        if margin_bottom:
            self.console.print()

    def show_help(self) -> None:
        """Show the detailed CLI help message."""
        self.console.print(Text("APE Agent CLI", style="bold"))
        self.console.print()

        self.console.print(Text("Commands:", style="bold"))
        self.console.print(self._build_command_line("/help", "Show this help message"))
        self.console.print(self._build_command_line("/quit", "Exit the CLI"))
        self.console.print(self._build_command_line("/clear", "Clear the screen"))
        self.console.print()

        self.console.print(Text("Keyboard Controls:", style="bold"))
        self.console.print(self._build_key_line("ESC", "Interrupt AI response/tool execution and return to input"))
        self.console.print(self._build_key_line("Ctrl+D", "Exit the system"))
        self.console.print()

        self.console.print(Text("Workflow:", style="bold"))
        for line in [
            "Ask AI to help with Lean theorem proving tasks",
            "AI automatically executes tool calls and completes tasks",
            "Wait for AI to finish, then provide new instructions",
            "When applying artifacts to files, you'll be prompted for confirmation",
            "Use /quit to exit and restart the CLI to begin a new conversation",
        ]:
            self.console.print(self._build_bullet_line(line))
        self.console.print()

        self.console.print(Text("Examples:", style="bold"))
        for example in [
            '"Browse my Lean files and help me prove theorem X"',
            '"Create a proof for commutativity of addition"',
            '"Read MyFile.lean and fix the compilation errors"',
            '"List all my artifacts and show their verification status"',
        ]:
            self.console.print(Text(f"  {example}", style=colors.gray))
        self.console.print()

        self.console.print(Text("File Operations:", style="bold"))
        for line in [
            "AI can browse your workspace files automatically",
            "Artifacts are created and verified in a safe environment",
            "File modifications require your explicit confirmation",
            "Backup files are created automatically when overwriting",
        ]:
            self.console.print(self._build_bullet_line(line))

    def show_conversation_reset(self) -> None:
        """Show a conversation-reset separator."""
        self.console.print()
        rule_style = colors.accent_yellow if colors.accent_yellow else "yellow"
        self.console.print(Rule("Conversation Reset", style=rule_style))
        self.console.print()
        self.message_history.clear()

    def clear_screen(self) -> None:
        """Clear the screen and re-show the short title."""
        import os

        os.system("clear" if os.name == "posix" else "cls")

        title_text = Text()
        title_text.append("APE Agent", style="bold")
        title_text.append(" — Automated Proof Engineering", style=colors.gray)
        self.console.print(title_text)
        self.console.print()

    def _build_message_preview(
        self,
        message: str,
        *,
        max_lines: int,
        max_width: int,
    ) -> tuple[list[str], bool]:
        """Build preview lines for a long message."""
        raw_lines = message.splitlines() or [message]
        preview_lines: list[str] = []
        was_truncated = False

        for line in raw_lines:
            display_line = line if line else " "
            if len(display_line) > max_width:
                display_line = f"{display_line[: max_width - 3]}..."
                was_truncated = True
            preview_lines.append(display_line)

        if len(preview_lines) > max_lines:
            preview_lines = preview_lines[:max_lines]
            was_truncated = True

        return preview_lines or ["(empty)"], was_truncated

    def _build_command_line(self, command: str, description: str) -> Text:
        """Build a styled command/help row."""
        line = Text("  ")
        line.append(command, style=colors.accent_cyan)
        line.append(f"      {description}")
        return line

    def _build_key_line(self, key_name: str, description: str) -> Text:
        """Build a styled keyboard-shortcut row."""
        line = Text("  ")
        line.append(key_name, style=colors.accent_yellow)
        line.append(f"     {description}")
        return line

    def _build_bullet_line(self, text: str) -> Text:
        """Build a muted bullet line."""
        line = Text("  • ", style=colors.gray)
        line.append(text, style=colors.gray)
        return line
