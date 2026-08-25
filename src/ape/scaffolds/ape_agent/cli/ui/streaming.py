"""
Streaming Output Handler for CLI - Real Streaming Display

Handles real-time streaming output for AI responses, providing simple and 
efficient real-time display without simulation or complex buffering.
Supports displaying reasoning content with different styling.
"""

import time
import json
from typing import Dict, Any
from rich.console import Console
from rich.text import Text
from ape.utils.logging import create_logger

from .colors import colors


class StreamingOutputHandler:
    """Streaming output handler, handle real-time streaming display, support reasoning content distinction display"""
    
    def __init__(self, console: Console, logger=None):
        """
        Initialize streaming output handler
        
        Args:
            console: Rich Console object
            logger: Logger instance, if None, create console logger
        """
        self.console = console
        self.logger = logger or create_logger()
        self.is_streaming = False
        self.accumulated_content = ""
        self.accumulated_reasoning = ""
        self.has_shown_prefix = False
        self.has_shown_reasoning_prefix = False
        
    def start_streaming_response(self) -> Dict[str, Any]:
        """
        Start streaming display AI response
        
        Returns:
            message object, for tracking status
        """
        # create message object
        message_obj = {
            "type": "assistant",
            "content": "",
            "reasoning_content": "",
            "is_complete": False,
            "timestamp": time.time()
        }
        
        self.is_streaming = True
        self.accumulated_content = ""
        self.accumulated_reasoning = ""
        self.has_shown_prefix = False
        self.has_shown_reasoning_prefix = False
        
        return message_obj
    
    def show_tool_call(self, tool_call: Dict[str, Any]):
        """
        Display tool call information, using function call format

        Args:
            tool_call: tool call information, contains name, arguments etc.
        """
        tool_name = tool_call.get("name", "unknown")
        # note: it may be "arguments" or "input"
        tool_input = tool_call.get("arguments") or tool_call.get("input", {})

        from rich.text import Text

        # first line: ⏺ ToolName(param1="value1", param2="value2")
        text = Text()
        text.append("⏺ ", style=colors.accent_cyan)
        text.append(tool_name, style="bold")

        # build parameter list, display as function call format
        if tool_input:
            params = []
            for key, value in tool_input.items():
                if isinstance(value, str):
                    # string parameter, truncate and add quotes
                    value_str = self._truncate_string(value, max_length=50)
                    params.append(f'{key}="{value_str}"')
                elif isinstance(value, (dict, list)):
                    # complex object, display type
                    params.append(f'{key}={{...}}' if isinstance(value, dict) else f'{key}=[...]')
                elif isinstance(value, bool):
                    # boolean value
                    params.append(f'{key}={str(value)}')
                elif value is None:
                    # None value
                    params.append(f'{key}=None')
                else:
                    params.append(f'{key}={value}')

            # concatenate parameters (if too long, only display the first few parameters)
            if len(params) <= 3:
                params_str = ", ".join(params)
            else:
                params_str = ", ".join(params[:3]) + ", ..."

            text.append(f"({params_str})", style=colors.gray)
        else:
            text.append("()", style=colors.gray)

        self.console.print(text)
        # do not print empty line, wait for tool result to continue
    
    def _truncate_string(self, text: str, max_length: int = 60) -> str:
        """
        Truncate string, if too long, display ellipsis
        
        Args:
            text: string to truncate
            max_length: maximum length
            
        Returns:
            truncated string
        """
        if len(text) <= max_length:
            return text
        
        return text[:max_length-3] + "..."
    
    def _format_json_result(self, result: Any, max_lines: int = 10, max_width: int = 80) -> str:
        """
        Format JSON result, perform truncation display to avoid too much content, smartly handle multiple items cases
        
        Args:
            result: result to format (string or dictionary)
            max_lines: maximum display lines
            max_width: maximum width per line
            
        Returns:
            formatted string
        """
        try:
            # if result is a string, try to parse as JSON
            if isinstance(result, str):
                try:
                    parsed_result = json.loads(result)
                except json.JSONDecodeError:
                    # if not JSON, process as plain text
                    return self._format_plain_text(result, max_lines, max_width)
            else:
                parsed_result = result
            
            # smartly handle data structures containing items
            if isinstance(parsed_result, dict):
                return self._format_dict_with_items(parsed_result, max_lines, max_width)
            elif isinstance(parsed_result, list):
                return self._format_list_with_items(parsed_result, max_lines, max_width)
            else:
                # other types, use standard JSON formatting
                return self._format_standard_json(parsed_result, max_lines, max_width)
            
        except Exception as e:
            # if formatting fails, fall back to string truncation
            result_str = str(result)
            if len(result_str) > max_width * max_lines:
                return result_str[:max_width * max_lines - 3] + "..."
            return result_str
    
    def _format_plain_text(self, text: str, max_lines: int, max_width: int) -> str:
        """Format plain text, handle too long content"""
        lines = text.split('\n')
        if len(lines) <= max_lines:
            # check line width
            result_lines = []
            for line in lines:
                if len(line) > max_width:
                    result_lines.append(line[:max_width-3] + "...")
                else:
                    result_lines.append(line)
            return '\n'.join(result_lines)
        
        truncated_lines = lines[:max_lines]
        truncated_lines.append(f"... ({len(lines) - max_lines} more lines)")
        return '\n'.join(truncated_lines)
    
    def _format_dict_with_items(self, data: dict, max_lines: int, max_width: int) -> str:
        """Smartly format dictionary containing items"""
        result_lines = []
        used_lines = 0
        
        # first handle non-items fields
        for key, value in data.items():
            if key.lower() in ['items', 'results', 'data', 'content']:
                continue  # later special handling
            
            if used_lines >= max_lines - 2:  # reserve space for items
                break
                
            if isinstance(value, str) and len(value) > max_width - len(key) - 4:
                truncated_value = value[:max_width - len(key) - 7] + "..."
                result_lines.append(f'"{key}": "{truncated_value}"')
            else:
                value_str = json.dumps(value, ensure_ascii=False)
                if len(value_str) > max_width - len(key) - 4:
                    value_str = value_str[:max_width - len(key) - 7] + "..."
                result_lines.append(f'"{key}": {value_str}')
            used_lines += 1
        
        # special handling for items field
        items_key = None
        items_value = None
        for key in ['items', 'results', 'data', 'content']:
            if key in data:
                items_key = key
                items_value = data[key]
                break
        
        if items_value is not None and isinstance(items_value, list) and len(items_value) > 0:
            if result_lines:
                result_lines.append("")  # empty line to separate
                used_lines += 1
            
            remaining_lines = max_lines - used_lines
            
            # display the first item
            first_item = items_value[0]
            first_item_lines = self._format_single_item(first_item, remaining_lines - 2, max_width)
            
            result_lines.append(f'"{items_key}": [')
            for line in first_item_lines:
                result_lines.append(f"  {line}")
            
            # display remaining items information
            if len(items_value) > 1:
                result_lines.append(f"  ... and {len(items_value) - 1} more items")
            
            result_lines.append("]")
        
        return '\n'.join(result_lines)
    
    def _format_list_with_items(self, data: list, max_lines: int, max_width: int) -> str:
        """Format list, display the first item first"""
        if not data:
            return "[]"
        
        result_lines = ["["]
        
        # display the first item
        first_item_lines = self._format_single_item(data[0], max_lines - 3, max_width)
        for line in first_item_lines:
            result_lines.append(f"  {line}")
        
        # display remaining items information
        if len(data) > 1:
            result_lines.append(f"  ... and {len(data) - 1} more items")
        
        result_lines.append("]")
        return '\n'.join(result_lines)
    
    def _format_single_item(self, item: Any, max_lines: int, max_width: int) -> list:
        """Format single item, return line list"""
        if isinstance(item, str):
            if len(item) > max_width - 4:
                return [f'"{item[:max_width-7]}..."']
            else:
                return [f'"{item}"']
        elif isinstance(item, dict):
            lines = []
            lines.append("{")
            item_count = 0
            for key, value in item.items():
                if item_count >= max_lines - 2:  # reserve space for closing bracket
                    lines.append("  ...")
                    break
                
                if isinstance(value, str):
                    if len(value) > max_width - len(key) - 8:
                        truncated_value = value[:max_width - len(key) - 11] + "..."
                        lines.append(f'  "{key}": "{truncated_value}"')
                    else:
                        lines.append(f'  "{key}": "{value}"')
                else:
                    value_str = json.dumps(value, ensure_ascii=False)
                    if len(value_str) > max_width - len(key) - 6:
                        value_str = value_str[:max_width - len(key) - 9] + "..."
                    lines.append(f'  "{key}": {value_str}')
                item_count += 1
            lines.append("}")
            return lines
        else:
            item_str = json.dumps(item, ensure_ascii=False)
            if len(item_str) > max_width - 4:
                return [item_str[:max_width-7] + "..."]
            else:
                return [item_str]
    
    def _format_standard_json(self, data: Any, max_lines: int, max_width: int) -> str:
        """Standard JSON formatting, for non-special structure data"""
        formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
        lines = formatted_json.split('\n')
        
        # handle too long JSON
        if len(lines) > max_lines:
            # reserve the first few lines and the last line, use ellipsis in between
            keep_start = max_lines // 2
            keep_end = max_lines - keep_start - 1
            
            result_lines = []
            result_lines.extend(lines[:keep_start])
            result_lines.append(f"  ... ({len(lines) - max_lines} more lines)")
            if keep_end > 0:
                result_lines.extend(lines[-keep_end:])
            
            formatted_json = '\n'.join(result_lines)
        
        # handle too wide lines
        final_lines = []
        for line in formatted_json.split('\n'):
            if len(line) > max_width:
                final_lines.append(line[:max_width-3] + "...")
            else:
                final_lines.append(line)
        
        return '\n'.join(final_lines)
    
    def show_tool_result(self, tool_result: Dict[str, Any]):
        """
        Display tool call result, continue below tool call, using tree-like tab

        Args:
            tool_result: tool result information, contains tool_name, tool_use_id, result, success etc.
        """
        result = tool_result.get("result", "")
        success = tool_result.get("success", True)

        from rich.text import Text

        # directly use tree-like tab to list result details
        if result:
            if isinstance(result, dict):
                # dictionary result: display success and message first
                items = []

                # handle success and message first
                if "success" in result:
                    items.append(("success", result["success"]))
                if "message" in result:
                    items.append(("message", result["message"]))

                # add other fields
                for key, value in result.items():
                    if key not in ["success", "message"]:
                        items.append((key, value))

                # display all fields
                for i, (key, value) in enumerate(items):
                    result_text = Text()
                    # the last item uses └─, others use ├─
                    if i == len(items) - 1:
                        result_text.append("  └─ ", style=colors.gray)
                    else:
                        result_text.append("  ├─ ", style=colors.gray)

                    if isinstance(value, str):
                        display_value = self._truncate_string(value, max_length=70)
                    else:
                        display_value = self._truncate_string(str(value), max_length=70)
                    result_text.append(f"{key}: {display_value}", style=colors.gray)
                    self.console.print(result_text)

            elif isinstance(result, str):
                # string result: display line by line (up to 5 lines)
                lines = result.split('\n')[:5]
                for i, line in enumerate(lines):
                    if line.strip():
                        result_text = Text()
                        # the last item uses └─, others use ├─
                        if i == len(lines) - 1 and len(result.split('\n')) <= 5:
                            result_text.append("  └─ ", style=colors.gray)
                        else:
                            result_text.append("  ├─ ", style=colors.gray)
                        result_text.append(self._truncate_string(line, max_length=80), style=colors.gray)
                        self.console.print(result_text)

                if len(result.split('\n')) > 5:
                    more_text = Text()
                    more_text.append("  └─ ", style=colors.gray)
                    more_text.append("... and {} more lines".format(len(result.split('\n')) - 5), style=colors.gray)
                    self.console.print(more_text)

        self.console.print()  # empty line
    
    def update_streaming_content(self, content_chunk: str = None, content_type: str = 'content'):
        """
        Update streaming content, display new content block in real-time, support distinguishing reasoning, regular content and tool_result
        
        Args:
            content_chunk: new content block
            content_type: content type, 'content', 'reasoning', 'tool_result', 'signature', 'thinking', 'stream_end' or 'tool_call'
        """
        if not self.is_streaming:
            return
        
        # handle streaming output end signal
        if content_type == 'stream_end':
            self._handle_stream_end()
            return
        
        # handle tool result display
        if content_type == 'tool_result':
            if content_chunk:
                # content_chunk is now a dictionary, directly use
                self.show_tool_result(content_chunk)
            return
        
        # filter out content types that should not be displayed (signature etc. internal data)
        if content_type in ['signature']:
            # these are internal processing data, should not be displayed to users
            return
        
        if not content_chunk:
            return
        
        if content_type in ['reasoning', 'thinking']:
            self._handle_reasoning_content(content_chunk)
        else:
            self._handle_regular_content(content_chunk)
    
    def _handle_reasoning_content(self, reasoning_chunk: str):
        """Handle reasoning content display"""
        self.accumulated_reasoning += reasoning_chunk

        # build display text
        text = Text()

        # if reasoning prefix has not been displayed, mark as displayed
        if not self.has_shown_reasoning_prefix:
            # if regular content has been displayed, first newline
            if self.has_shown_prefix and self.accumulated_content:
                self.console.print()  # newline to separate
            self._show_role_prefix("◌ ", "Thinking", colors.accent_cyan)
            self.has_shown_reasoning_prefix = True

        # add reasoning content block
        text.append(reasoning_chunk, style=colors.accent_cyan)

        # display reasoning content in real-time
        self.console.print(text, end="")
    
    def _handle_regular_content(self, content_chunk: str):
        """Handle regular content display"""
        self.accumulated_content += content_chunk

        # build display text
        text = Text()

        # if reasoning content has been displayed, need to newline to separate
        if self.has_shown_reasoning_prefix and self.accumulated_reasoning and not self.has_shown_prefix:
            self.console.print()  # newline to separate

        # mark as displayed prefix
        if not self.has_shown_prefix:
            self._show_role_prefix("● ", "Ape Agent", colors.accent_purple)
            self.has_shown_prefix = True

        # add content block, use default color
        text.append(content_chunk)

        # display new content in real-time (no newline, keep streaming effect)
        self.console.print(text, end="")
    
    def _handle_stream_end(self):
        """Handle streaming output end signal, immediately newline"""
        if self.has_shown_prefix or self.has_shown_reasoning_prefix:
            # only newline if content has been displayed
            self.console.print()
    
    def finish_streaming_response(self):
        """Finish streaming response display"""
        if not self.is_streaming:
            return
        
        self.is_streaming = False
        
        # reset state (newline is handled in _handle_stream_end)
        self.has_shown_prefix = False
        self.has_shown_reasoning_prefix = False
        self.accumulated_content = ""
        self.accumulated_reasoning = ""

    def _show_role_prefix(self, symbol: str, label: str, color: str) -> None:
        """Print a streaming role prefix before assistant/reasoning text."""
        prefix = Text()
        prefix.append(symbol, style=color)
        prefix.append(label, style="bold")
        prefix.append(" ", style=color)
        self.console.print(prefix, end="")
    
