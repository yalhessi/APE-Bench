"""Logging Utilities.

Provides unified `create_logger` interface:
- No log_dir → output to stdout
- Provide directory → write to separate log file in that directory

Also maintains `create_mcp_log_handler` compatibility method.
"""

import inspect
import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Union


class ModuleNameFormatter(logging.Formatter):
    """Formatter that automatically marks caller module name."""

    _LOGGING_MODULES = {
        'logging', 'logging.handlers', 'logging.config',
        'ape.utils.logging'
    }

    def format(self, record: logging.LogRecord) -> str:
        frame = inspect.currentframe()
        try:
            while frame:
                module = frame.f_globals.get('__name__', '')
                if module and module not in self._LOGGING_MODULES:
                    record.module = module
                    break
                frame = frame.f_back
            else:
                record.module = 'unknown'
        finally:
            del frame

        return super().format(record)


class SimpleLoggerAdapter(logging.LoggerAdapter):
    """Minimal wrapper: passes through message and context."""

    def process(self, msg, kwargs):
        return msg, kwargs


def _resolve_module_name() -> str:
    frame = inspect.currentframe()
    try:
        caller = frame.f_back
        if caller:
            return caller.f_globals.get('__name__', 'unknown')
        return 'unknown'
    finally:
        del frame


def create_logger(
    log_file: Optional[Union[str, Path]] = None,
    to_console: bool = True,
    console_stream = sys.stdout
) -> logging.LoggerAdapter:
    """Create logger with independent control of file and console output.

    Args:
        log_file: Full path to log file (caller controls filename). None = no file output.
        to_console: Whether to output to console (default True).

    Returns:
        LoggerAdapter instance.

    Examples:
        # Console output only (default behavior)
        logger = create_logger()

        # Write to specified file
        logger = create_logger(log_file="logs/scaffold_abc123.log", to_console=False)

        # Output to both file and console
        logger = create_logger(log_file=Path("logs/relay.log"), to_console=True)
    """

    module_name = _resolve_module_name()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    logger_name = f"{module_name}.{timestamp}"

    base_logger = logging.getLogger(logger_name)
    base_logger.setLevel(logging.DEBUG)
    base_logger.handlers.clear()

    formatter = ModuleNameFormatter(
        '%(asctime)s | %(levelname)-8s | %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Add file handler (if log_file is specified)
    if log_file is not None:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            str(log_path),
            maxBytes=10 * 1024 * 1024,
            backupCount=30
        )
        file_handler.setFormatter(formatter)
        base_logger.addHandler(file_handler)
        setattr(base_logger, '_ape_logger_log_file', str(log_path))
    else:
        setattr(base_logger, '_ape_logger_log_file', None)

    # Add console handler (if to_console=True)
    if to_console:
        console_handler = logging.StreamHandler(console_stream)
        console_handler.setFormatter(formatter)
        base_logger.addHandler(console_handler)

    base_logger.propagate = False

    return SimpleLoggerAdapter(base_logger, {'module': module_name})


def create_mcp_log_handler(logger: logging.LoggerAdapter):
    """Wrap FastMCP-compatible log handler."""

    async def log_handler(message):
        level = getattr(logging, message.level.upper(), logging.INFO)
        msg = (message.data or {}).get('msg', '')
        prefix = f"[MCP:{message.logger}] " if message.logger else "[MCP] "
        logger.log(level, prefix + msg)

    return log_handler
