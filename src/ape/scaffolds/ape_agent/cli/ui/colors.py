"""
Color system for core CLI, based on gemini-cli design.

Provides a consistent color palette that adapts to terminal capabilities.
"""

import os
from typing import Dict, Any
from rich.console import Console

class ColorTheme:
    """Base color theme class"""
    
    def __init__(self, theme_type: str = "dark"):
        self.type = theme_type
        self._console = Console()
        self._supports_truecolor = self._console.color_system == "truecolor"
        
    def _get_color(self, truecolor: str, fallback: str) -> str:
        """Get color based on terminal capabilities"""
        if self._supports_truecolor:
            return truecolor
        return fallback

class GeminiColors:
    """Gemini-CLI compatible color system"""
    
    def __init__(self):
        self._console = Console()
        self._theme_type = self._detect_theme()
        self._theme = self._get_theme()
    
    def _detect_theme(self) -> str:
        """Detect theme based on environment"""
        # Check NO_COLOR environment variable
        if os.environ.get('NO_COLOR'):
            return 'no_color'
        
        # Check TERM for basic color support
        term = os.environ.get('TERM', '').lower()
        if 'ansi' in term or self._console.color_system == 'standard':
            return 'ansi'
        
        # Default to dark theme for rich color support
        return 'dark'
    
    def _get_theme(self) -> Dict[str, str]:
        """Get theme colors based on detected theme type"""
        if self._theme_type == 'no_color':
            return {
                'Foreground': '',
                'Background': '',
                'AccentPurple': '',
                'AccentCyan': '',
                'AccentGreen': '',
                'AccentYellow': '',
                'AccentRed': '',
                'AccentBlue': '',
                'Gray': '',
                'Comment': '',
            }
        elif self._theme_type == 'ansi':
            return {
                'Foreground': 'white',
                'Background': 'black',
                'AccentPurple': 'magenta',
                'AccentCyan': 'cyan',
                'AccentGreen': 'green',
                'AccentYellow': 'yellow', 
                'AccentRed': 'red',
                'AccentBlue': 'blue',
                'Gray': 'bright_black',
                'Comment': 'green',
            }
        elif self._theme_type == 'light':
            return {
                'Foreground': '#3C3C43',
                'Background': '#FAFAFA',
                'AccentPurple': '#8B5CF6',
                'AccentCyan': '#06B6D4',
                'AccentGreen': '#3CA84B',
                'AccentYellow': '#D5A40A',
                'AccentRed': '#DD4C4C',
                'AccentBlue': '#3B82F6',
                'Gray': '#B7BECC',
                'Comment': '#008000',
            }
        else:  # dark theme (default)
            return {
                'Foreground': '#CDD6F4',
                'Background': '#1E1E2E',
                'AccentPurple': '#CBA6F7',
                'AccentCyan': '#89DCEB',
                'AccentGreen': '#A6E3A1',
                'AccentYellow': '#F9E2AF',
                'AccentRed': '#F38BA8',
                'AccentBlue': '#89B4FA',
                'Gray': '#6C7086',
                'Comment': '#6C7086',
            }
    
    @property
    def foreground(self) -> str:
        return self._theme['Foreground']
    
    @property
    def background(self) -> str:
        return self._theme['Background']
    
    @property
    def accent_purple(self) -> str:
        """Gemini message prefix color"""
        return self._theme['AccentPurple']
    
    @property
    def accent_cyan(self) -> str:
        """Shell command prefix color"""
        return self._theme['AccentCyan']
    
    @property
    def accent_green(self) -> str:
        """Success message color"""
        return self._theme['AccentGreen']
    
    @property
    def accent_yellow(self) -> str:
        """Info/warning message color"""
        return self._theme['AccentYellow']
    
    @property
    def accent_red(self) -> str:
        """Error message color"""
        return self._theme['AccentRed']
    
    @property
    def accent_blue(self) -> str:
        """Link/accent color"""
        return self._theme['AccentBlue']
    
    @property
    def gray(self) -> str:
        """Subdued text and borders"""
        return self._theme['Gray']
    
    @property
    def comment(self) -> str:
        """Comments and secondary text"""
        return self._theme['Comment']

# Global color instance
colors = GeminiColors() 