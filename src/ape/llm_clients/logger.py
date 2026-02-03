"""
LLM Raw Message Logger Module.

Provides logging functionality for raw LLM request and response messages.
"""

import asyncio
import json
import uuid
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import aiofiles

from ape.utils.project import PROJECT_ROOT


class LLMLogger:
    """LLM raw message logger with per-instance log file."""

    def __init__(self, client_uid: Optional[str] = None):
        """Initialize logger and determine log file path.

        Args:
            client_uid: Client unique identifier, auto-generated if None.
        """
        self.client_uid = client_uid or str(uuid.uuid4())[:8]

        now = datetime.now()
        timestamp = int(time.time() * 1000)

        date_dir = now.strftime("%Y-%m-%d")
        hour_dir = now.strftime("%H")
        minute_dir = now.strftime("%M")

        log_base_dir = PROJECT_ROOT / "data" / "llm_logs"
        log_dir = log_base_dir / date_dir / hour_dir / minute_dir
        log_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{timestamp}_{self.client_uid}.jsonl"
        self.log_file_path = log_dir / filename
    
    async def log_request(self, payload: Dict[str, Any], request_type: str = "request"):
        """Log request data asynchronously.

        Args:
            payload: Raw request payload.
            request_type: Request type ("request" or "streaming_request").
        """
        log_entry = {
            "timestamp": time.time(),
            "client_uid": self.client_uid,
            "type": request_type,
            "direction": "request",
            "data": payload
        }

        await self._append_log_entry(log_entry)

    async def log_response(self, response_data: Dict[str, Any], request_type: str = "request"):
        """Log response data asynchronously.

        Args:
            response_data: Raw response data from response.json().
            request_type: Request type ("request" or "streaming_request").
        """
        log_entry = {
            "timestamp": time.time(),
            "client_uid": self.client_uid,
            "type": request_type,
            "direction": "response",
            "data": response_data
        }

        await self._append_log_entry(log_entry)

    async def log_streaming_chunk(self, chunk_data: Dict[str, Any]):
        """Log streaming response chunk asynchronously.

        Args:
            chunk_data: Raw chunk data.
        """
        log_entry = {
            "timestamp": time.time(),
            "client_uid": self.client_uid,
            "type": "streaming_chunk",
            "direction": "response",
            "data": chunk_data
        }

        await self._append_log_entry(log_entry)

    async def _append_log_entry(self, log_entry: Dict[str, Any]):
        """Append log entry to file asynchronously."""
        try:
            async with aiofiles.open(self.log_file_path, 'a', encoding='utf-8') as f:
                await f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception:
            pass
