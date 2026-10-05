"""
Claude Code Conversation Manager - SDK coordination layer

Inherits from BaseConversationManager and implements Claude SDK specific:
1. SDK client management
2. Message stream processing
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from ape.llm_clients.models import TokenUsage
from ape.scaffolds.utils.base_conversation import BaseConversationManager, limit_error
from ape.scaffolds.utils.common import open_file_in_vscode

if TYPE_CHECKING:
    import logging
    from claude_agent_sdk import ClaudeSDKClient
    from .relay import ClaudeCodeRelaySession


class ClaudeSessionError(Exception):
    """The CLI reported what a review attempt can neither continue past nor be read through:
    a spent usage limit, a refused login, an API error it stopped retrying, a safety refusal,
    or a session serving something other than what the config pins.

    Raised so the attempt fails. Left alone, the session ends with no submission and the
    retry prompts meet the same error, so the record says "no submission" about a session
    that was stopped, or, where findings were filed first, reads as a short review.
    """


def anthropic_usage(usage: Dict[str, Any]) -> TokenUsage:
    """One Messages API usage record as APE's: cache reads and writes counted inside the
    prompt (Anthropic reports them beside `input_tokens`), and nothing billed."""
    read = usage.get("cache_read_input_tokens") or 0
    written = usage.get("cache_creation_input_tokens") or 0
    prompt = (usage.get("input_tokens") or 0) + read + written
    output = usage.get("output_tokens") or 0
    thinking = (usage.get("output_tokens_details") or {}).get("thinking_tokens")
    return TokenUsage(input_tokens=prompt, output_tokens=output, total_tokens=prompt + output,
                      reasoning_tokens=thinking or None,
                      cache_creation_input_tokens=written or None,
                      cache_read_input_tokens=read or None)


def model_usage_total(model_usage: Dict[str, Dict[str, Any]]) -> TokenUsage:
    """A result message's `model_usage`, every model summed, as one `anthropic_usage`.

    It covers the CLI's own background calls (titles and the like, on Haiku), which reach
    the SDK as no stream event, and it is cumulative over the session.
    """
    return sum_usage([anthropic_usage({
        "input_tokens": u.get("inputTokens"), "output_tokens": u.get("outputTokens"),
        "cache_read_input_tokens": u.get("cacheReadInputTokens"),
        "cache_creation_input_tokens": u.get("cacheCreationInputTokens"),
        "output_tokens_details": {"thinking_tokens": u.get("thinkingTokens")},
    }) for u in model_usage.values()])


def sum_usage(usages: List[TokenUsage]) -> TokenUsage:
    def total(field):
        return sum(getattr(u, field) or 0 for u in usages)

    return TokenUsage(
        input_tokens=total("input_tokens"), output_tokens=total("output_tokens"),
        total_tokens=total("input_tokens") + total("output_tokens"),
        reasoning_tokens=total("reasoning_tokens") or None,
        cache_creation_input_tokens=total("cache_creation_input_tokens") or None,
        cache_read_input_tokens=total("cache_read_input_tokens") or None,
        total_cost=total("total_cost"), cached_total_cost=total("cached_total_cost"))


class ClaudeCodeConversationManager(BaseConversationManager):
    """
    Claude Code conversation manager - SDK coordination

    Specific responsibilities:
    1. Manage Claude SDK client lifecycle
    2. Process SDK message stream
    3. Create hardlinks for SDK conversation files
    """

    def __init__(self, *args, resume_session_id: Optional[str] = None, **kwargs):
        super().__init__(*args, **kwargs)

        # Claude SDK specific
        self._claude_client: Optional['ClaudeSDKClient'] = None
        self.resume_session_id = resume_session_id

        # Hardlink creation status
        self._hardlink_created = bool(resume_session_id)

        # The subscription route has no relay, so the session's usage, turns, id and failures
        # are read off the SDK's own messages instead. Usage is per API reply, keyed by its
        # message id, from the stream events: an AssistantMessage carries only the usage its
        # reply opened with (16 output tokens of a reply that ended at 124, in the first probe).
        self._sdk_session_id: Optional[str] = None
        self._sdk_replies: Dict[str, Dict[str, Any]] = {}
        self._sdk_reply: Optional[str] = None
        self._sdk_result_usage: Optional[TokenUsage] = None
        self._sdk_replies_at_result = 0
        self.session_record: Dict[str, Any] = {"rate_limits": [], "results": []}

        if resume_session_id:
            self.logger.debug(f"[ClaudeCodeConversationManager] Resume mode: {resume_session_id}")

    async def _create_relay_session(
        self,
        port: int,
        conversations_dir: Path,
        cwd: str,
        logger: 'logging.LoggerAdapter',
        conversation_trees_path: Path
    ) -> 'ClaudeCodeRelaySession':
        """Create Claude Code relay session"""
        from .relay import ClaudeCodeRelaySession

        return ClaudeCodeRelaySession(
            port=port,
            llm_config=self.config.llm_config,
            fast_llm_config=self.config.fast_llm_config,
            conversations_dir=conversations_dir,
            cwd=cwd,
            logger=logger,
            conversation_trees_path=conversation_trees_path,
            max_turns=self.config.execution.max_turns,  # Pass max_turns to relay
            cost_limit=self.cost_limit,  # Pass cost_limit to relay
            token_limit=self.token_limit  # and the same ceiling in tokens
        )

    async def _cleanup_internal(self) -> None:
        """Clean up SDK client reference"""
        if self._claude_client:
            self._claude_client = None
            self.logger.debug("[ClaudeCodeConversationManager] SDK client reference cleared")

    async def run_conversation(
        self,
        claude_client: 'ClaudeSDKClient',
        initial_prompt: Optional[str] = None
    ) -> bool:
        """
        Run conversation with Claude SDK

        Args:
            claude_client: ClaudeSDK client instance
            initial_prompt: Initial prompt (optional)

        Returns:
            True if submission detected, False otherwise
        """
        # Save client reference
        self._claude_client = claude_client

        # Send initial prompt if provided
        if initial_prompt:
            await claude_client.query(initial_prompt)
            self.logger.info("[ClaudeCodeConversationManager] Sent initial query")

        # Call base conversation loop (monitor is started in base class)
        return await super().run_conversation()

    async def _execute_turn(self) -> bool:
        """
        Execute single turn using Claude SDK

        Key difference from receive_messages():
        - receive_response() automatically returns after receiving ResultMessage
        - This ensures one complete turn (request -> response -> tool execution -> result)
        - Without this, receive_messages() would wait indefinitely for new messages

        Returns:
            True if submission detected, False otherwise
        """
        async for message in self._claude_client.receive_response():
            if self._relay_session is None and self.config.subscription_route:
                self._read_sdk_message(message)

            # Check termination
            if self._stop_event.is_set():
                self.logger.debug("[ClaudeCodeConversationManager] Termination detected during stream")
                break

            # Try to create hardlink
            await self._try_create_hardlink()

        # Check if submission was detected (stop event was set by termination callback)
        if self._stop_event.is_set():
            self.logger.info("[ClaudeCodeConversationManager] Submission detected via termination callback")
            return True

        # No submission detected in this turn
        return False

    async def _send_retry_prompt(self, prompt: str) -> None:
        """Send retry prompt to SDK"""
        await self._claude_client.query(prompt)

    async def _interrupt_internal(self) -> None:
        """Interrupt SDK message stream"""
        if self._claude_client:
            try:
                await self._claude_client.interrupt()
                self.logger.info("[ClaudeCodeConversationManager] SDK interrupt signal sent")
            except Exception as e:
                self.logger.warning(f"[ClaudeCodeConversationManager] Error sending interrupt: {e}")

    def get_claude_code_session_id(self) -> Optional[str]:
        """Claude Code's session ID: the relay's, or the SDK's own on the subscription route."""
        if self._relay_session:
            return self._relay_session.claude_code_session_id
        return self._sdk_session_id

    def get_token_usage(self) -> TokenUsage:
        """The relay's record, or on the subscription route the last result's cumulative
        total plus every reply streamed since it."""
        if self._relay_session or not self.config.subscription_route:
            return super().get_token_usage()
        since = [anthropic_usage(raw) for raw in
                 list(self._sdk_replies.values())[self._sdk_replies_at_result:]]
        if self._sdk_result_usage is None:
            return sum_usage(since)
        return sum_usage([self._sdk_result_usage, *since])

    def get_current_turns(self) -> int:
        """The relay's request count, or the main model's replies on the subscription route."""
        if self._relay_session or not self.config.subscription_route:
            return super().get_current_turns()
        return len(self._sdk_replies)

    # --- the subscription route: the SDK's messages in place of the relay ---------------------

    def _read_sdk_message(self, message: Any) -> None:
        from claude_agent_sdk import (
            AssistantMessage, RateLimitEvent, ResultMessage, StreamEvent, SystemMessage)

        if isinstance(message, SystemMessage) and message.subtype == "init":
            self._check_session_identity(message.data)
        elif isinstance(message, StreamEvent):
            self._count_stream_event(message.event)
        elif isinstance(message, AssistantMessage):
            self._check_reply(message)
        elif isinstance(message, RateLimitEvent):
            self._check_rate_limit(message.rate_limit_info)
        elif isinstance(message, ResultMessage):
            self._read_result(message)

    def _check_session_identity(self, data: Dict[str, Any]) -> None:
        """What the CLI says this session is, recorded, and refused unless it is the pin."""
        self._sdk_session_id = data.get("session_id")
        identity = {key: data.get(key) for key in (
            "session_id", "model", "claude_code_version", "apiKeySource", "permissionMode",
            "tools", "mcp_servers", "memory_paths", "cwd")}
        self.session_record.setdefault("init", identity)
        expected = {"model": self.config.claude_model,
                    "claude_code_version": self.config.cli_version,
                    # The login, not an API key: an OAuth session reports "none" here.
                    "apiKeySource": "none"}
        wrong = {key: (identity[key], value) for key, value in expected.items()
                 if identity[key] != value}
        if wrong:
            raise ClaudeSessionError(
                "the CLI's session is not the one configured: "
                + "; ".join(f"{key} is {got!r}, expected {want!r}"
                            for key, (got, want) in wrong.items()))
        self.logger.info("[ClaudeCodeConversationManager] subscription session %s: %s on CLI %s",
                         identity["session_id"], identity["model"],
                         identity["claude_code_version"])

    def _count_stream_event(self, event: Dict[str, Any]) -> None:
        """Usage per main-model reply, and the limits checked as each new one starts."""
        kind = event.get("type")
        if kind == "message_start":
            reply = event.get("message") or {}
            error = limit_error(self.get_token_usage(), self.get_current_turns(),
                                max_turns=self.config.execution.max_turns,
                                cost_limit=self.cost_limit, token_limit=self.token_limit)
            if error is not None:
                self.logger.warning("[ClaudeCodeConversationManager] %s - stopping", error)
                raise error
            self._sdk_reply = reply.get("id")
            self._sdk_replies[self._sdk_reply] = dict(reply.get("usage") or {})
        elif kind == "message_delta" and self._sdk_reply is not None:
            # Cumulative for the reply; the final output count arrives here.
            self._sdk_replies[self._sdk_reply].update(
                {key: value for key, value in (event.get("usage") or {}).items()
                 if value is not None})

    def _check_reply(self, message: Any) -> None:
        if message.error is not None:
            raise ClaudeSessionError(
                f"the CLI ended a reply with error {message.error!r} (rate_limit is a spent "
                "subscription limit)")
        if message.parent_tool_use_id is None and message.model != self.config.claude_model:
            raise ClaudeSessionError(
                f"a reply came from {message.model!r}, not the pinned "
                f"{self.config.claude_model!r}: the CLI fell back to another model")
        if message.stop_reason == "refusal":
            raise ClaudeSessionError("the model's reply stopped on a safety refusal")

    def _check_rate_limit(self, info: Any) -> None:
        state = {"status": info.status, "type": info.rate_limit_type,
                 "resets_at": info.resets_at}
        # The CLI repeats the state with every request; record and warn on a change only (the
        # first dev repetition logged the same warning several times a minute per session).
        changed = (not self.session_record["rate_limits"]
                   or self.session_record["rate_limits"][-1] != state)
        if changed:
            self.session_record["rate_limits"].append(state)
        if info.status == "rejected":
            raise ClaudeSessionError(
                f"the subscription's {info.rate_limit_type} usage limit is spent "
                f"(resets at {info.resets_at})")
        if info.status == "allowed_warning" and changed:
            self.logger.warning("[ClaudeCodeConversationManager] subscription usage near its "
                                "%s limit (resets at %s)", info.rate_limit_type, info.resets_at)

    def _read_result(self, message: Any) -> None:
        self._sdk_session_id = message.session_id
        self.session_record["results"].append({
            "subtype": message.subtype, "is_error": message.is_error,
            "num_turns": message.num_turns, "stop_reason": message.stop_reason,
            "api_error_status": message.api_error_status,
            # What the same tokens would have cost on the API. Nothing was billed.
            "notional_cost_usd": message.total_cost_usd,
            "model_usage": message.model_usage,
            "permission_denials": len(message.permission_denials or []),
        })
        if message.model_usage:
            self._sdk_result_usage = model_usage_total(message.model_usage)
            self._sdk_replies_at_result = len(self._sdk_replies)
        if message.is_error:
            if message.subtype == "error_max_turns":
                from ape.scaffolds.base import MaxTurnsReachedError

                raise MaxTurnsReachedError(f"the CLI stopped at its turn limit "
                                           f"({message.num_turns} turns)")
            raise ClaudeSessionError(
                f"the CLI ended the session with an error ({message.subtype}, API status "
                f"{message.api_error_status}): {(message.result or '')[:300]}")

    @staticmethod
    def find_latest_hardlink(attempt_path: Path) -> Optional[str]:
        """
        Find latest hardlink file and extract session ID

        Args:
            attempt_path: Agent workspace path

        Returns:
            Session ID or None
        """
        if not attempt_path.exists():
            return None

        hardlink_files = list(attempt_path.glob("claude_code_conversation_*__*.jsonl"))
        if not hardlink_files:
            return None

        hardlink_files.sort(key=lambda f: f.name)
        latest_file = hardlink_files[-1]

        filename = latest_file.stem
        if "__" in filename:
            return filename.split("__")[-1]

        return None

    @staticmethod
    def find_session_file(claude_home: Path, session_id: str) -> Optional[Path]:
        """Claude Code's own transcript of `session_id`, under `claude_home/.claude/projects/`.

        Found by its name rather than by re-deriving the project directory. That directory is
        the CLI's working directory (`workspaces/`) with every non-alphanumeric character turned
        to `-`; this used to encode the `scratch/` path and only `/`, `.` and `_`, so the file
        was never found, no transcript reached the attempt, and nothing could audit the session.
        """
        found = sorted((Path(claude_home) / ".claude" / "projects").glob(f"*/{session_id}.jsonl"))
        return found[0] if found else None

    async def _try_create_hardlink(self) -> None:
        """
        Try to create hardlink for SDK conversation file (only once)

        SDK automatically creates {session_id}.jsonl in ~/.claude/projects/{encoded_cwd}/
        Since HOME is set to workspaces/, the actual path is:
        workspaces/.claude/projects/{encoded_cwd}/
        """
        if self._hardlink_created:
            return

        session_id = self.get_claude_code_session_id()
        if not session_id:
            return

        try:
            if not self.task.workspaces_dir or not self.task.attempt_path:
                raise RuntimeError("Task workspace not initialized for Claude conversation")
            sdk_session_file = self.find_session_file(self.task.workspaces_dir, session_id)
            if sdk_session_file is None:
                return

            # Create hardlink
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            attempt_path = self.task.attempt_path
            hardlink_path = attempt_path / f"claude_code_conversation_{timestamp}__{session_id}.jsonl"

            if hardlink_path.exists():
                hardlink_path.unlink()

            hardlink_path.hardlink_to(sdk_session_file)

            self._hardlink_created = True
            self.logger.info(f"[ClaudeCodeConversationManager] Created hardlink: {hardlink_path.name}")

            # Optionally open in VS Code (only in CLI mode)
            if self.is_cli_mode:
                open_file_in_vscode(hardlink_path, enabled=self.config.open_in_vscode, logger=self.logger)

        except Exception as e:
            self.logger.debug(f"[ClaudeCodeConversationManager] Failed to create hardlink: {e}")
