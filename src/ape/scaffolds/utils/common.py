"""
Common utility functions shared across scaffolds
"""

import socket
import subprocess
from pathlib import Path
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import logging


def allocate_port() -> int:
    """
    Allocate a usable port - let OS automatically select

    Use port=0 to let OS automatically allocate a usable port, which is more reliable than manually checking ranges:
    - Avoid race conditions (ports may be occupied between checking and usage)
    - No need to maintain port ranges
    - OS guarantees the port is immediately available

    Returns:
        int: Usable port number

    Raises:
        RuntimeError: Failed to allocate port
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('localhost', 0))  # 0 = let OS automatically select a usable port
            port = s.getsockname()[1]  # Get OS allocated port number
            return port
    except OSError as e:
        raise RuntimeError(f"Failed to allocate port: {e}")


def open_file_in_vscode(
    file_path: Path,
    enabled: bool = False,
    logger: Optional['logging.LoggerAdapter'] = None
) -> None:
    """
    Open file in VS Code (optional)

    Args:
        file_path: File path
        enabled: Whether to enable this feature
        logger: Logger instance
    """
    if not enabled:
        return

    try:
        subprocess.run(
            ["code", str(file_path)],
            capture_output=True,
            timeout=5
        )
        if logger:
            logger.debug(f"Opened in VS Code: {file_path}")
    except Exception as e:
        if logger:
            logger.debug(f"Failed to open in VS Code: {e}")
