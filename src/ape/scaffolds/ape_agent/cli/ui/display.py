"""
CLI Display Components

Rich-based display components that precisely mimic gemini-cli's design.
"""

from typing import Dict, List, Optional, Any
from rich.console import Console
from rich.text import Text
from rich.live import Live
from rich.rule import Rule
from ape.utils.logging import create_logger

from .colors import colors


class CLIDisplay:
    """CLI display manager"""
    
    def __init__(self, console: Console, logger=None):
        """
        Initialize CLI display manager
        
        Args:
            console: Rich Console object
            logger: Logger instance, if None, create console logger
        """
        self.console = console
        self.logger = logger or create_logger()
        self.current_live: Optional[Live] = None
        self.message_history: List[Dict[str, Any]] = []
        
    def show_status(self, message: str):
        """Show status message"""
        self._show_prefixed_message("● ", message, colors.gray, margin_top=True)

    def show_success(self, message: str):
        """Show success message"""
        self._show_prefixed_message("● ", message, colors.accent_green, margin_bottom=True)

    def show_error(self, message: str):
        """Show error message"""
        self._show_prefixed_message("● ", message, colors.accent_red, margin_bottom=True)

    def show_warning(self, message: str):
        """Show warning message"""
        self._show_prefixed_message("● ", message, colors.accent_yellow, margin_top=True)
    
    def _show_prefixed_message(self, prefix: str, message: str, color: str, 
                              margin_top: bool = False, margin_bottom: bool = False):
        """Show message with prefix"""
        if margin_top:
            self.console.print()
        
        # build complete text line
        text = Text()
        text.append(prefix, style=color)
        text.append(message, style=color)
        
        self.console.print(text)
        
        if margin_bottom:
            self.console.print()
    
    def show_help(self):
        """Show help message"""
        help_text = f"""[bold]APE Agent CLI[/bold]

[bold]Commands:[/bold]
  [{colors.accent_cyan}]/help[/{colors.accent_cyan}]      Show this help message
  [{colors.accent_cyan}]/quit[/{colors.accent_cyan}]      Exit the CLI
  [{colors.accent_cyan}]/clear[/{colors.accent_cyan}]     Clear the screen

[bold]Keyboard Controls:[/bold]
  • Press [{colors.accent_yellow}]ESC[/{colors.accent_yellow}] to interrupt AI response/tool execution and return to input
  • Press [{colors.accent_yellow}]Ctrl+D[/{colors.accent_yellow}] to exit the system

[bold]Workflow:[/bold]
  • Ask AI to help with Lean theorem proving tasks
  • AI automatically executes tool calls and completes tasks
  • Wait for AI to finish, then provide new instructions
  • When applying artifacts to files, you'll be prompted for confirmation
  • Use /quit to exit and restart the CLI to begin a new conversation

[bold]Examples:[/bold]
  [{colors.gray}]"Browse my Lean files and help me prove theorem X"[/{colors.gray}]
  [{colors.gray}]"Create a proof for commutativity of addition"[/{colors.gray}]
  [{colors.gray}]"Read MyFile.lean and fix the compilation errors"[/{colors.gray}]
  [{colors.gray}]"List all my artifacts and show their verification status"[/{colors.gray}]

[bold]File Operations:[/bold]
  • AI can browse your workspace files automatically
  • Artifacts are created and verified in a safe environment
  • File modifications require your explicit confirmation
  • Backup files are created automatically when overwriting"""

        self.console.print(help_text)
    
    def show_conversation_reset(self):
        """Show conversation reset message"""
        self.console.print()
        rule_style = colors.accent_yellow if colors.accent_yellow else "yellow"
        self.console.print(Rule("Conversation Reset", style=rule_style))
        self.console.print()
        self.message_history.clear()
    
    def clear_screen(self):
        """Clear screen and show title"""
        import os
        os.system('clear' if os.name == 'posix' else 'cls')

        # show title
        title_text = Text()
        title_text.append("APE Agent", style="bold")
        title_text.append(" — Automated Proof Engineering", style=colors.gray)

        self.console.print(title_text)
        self.console.print() 