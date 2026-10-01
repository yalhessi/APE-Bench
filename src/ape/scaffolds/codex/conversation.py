"""
Codex Conversation Manager - drives `codex exec`, one process per turn.

Each turn is `codex exec --json <prompt>`, or `codex exec resume <thread> --json <prompt>` after
the first, run in the attempt's workspace with `HOME` and `CODEX_HOME` pointing into it. The CLI's
model calls go to this attempt's relay through the `config.toml` the scaffold writes there. Its
events are appended to `codex_events.jsonl` in the attempt directory. A submission sets the stop
event, which ends the process.

This replaces a CodexBridge HTTP service, a git submodule of a third-party repository pinned to a
2025 commit, which was never checked out here; `codex exec` needs no Node service.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING

from ape.scaffolds.utils.base_conversation import BaseConversationManager

#: The longest event line read from the CLI. One `item.completed` carries a whole tool result on one
#: line, and asyncio's default (64 KiB) ended a session on a `content_search` result
#: (probe_postcutoff_gpt52_Grc_codex_rep2, LimitOverrunError; the orchestrator's retry ran clean).
EVENT_LINE_LIMIT = 64 * 1024 * 1024

if TYPE_CHECKING:
    import logging
    from .relay import CodexRelaySession


class CodexConversationManager(BaseConversationManager):
    """One `codex exec` process per turn, resumed by thread id."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pending_prompt: Optional[str] = None
        self._thread_id: Optional[str] = None
        self._proc: Optional[asyncio.subprocess.Process] = None

    async def _create_relay_session(
        self,
        port: int,
        conversations_dir: Path,
        cwd: str,
        logger: 'logging.LoggerAdapter',
        conversation_trees_path: Path
    ) -> 'CodexRelaySession':
        from .relay import CodexRelaySession

        return CodexRelaySession(
            port=port,
            llm_config=self.config.llm_config,
            conversations_dir=conversations_dir,
            cwd=cwd,
            logger=logger,
            conversation_trees_path=conversation_trees_path,
            max_turns=self.config.execution.max_turns,
            cost_limit=self.cost_limit,
            token_limit=self.token_limit,
            relayed_builtin_tools=self.config.relayed_builtin_tools,
        )

    @property
    def thread_id(self) -> Optional[str]:
        return self._thread_id

    def exec_command(self, prompt: str) -> List[str]:
        """The `codex exec` command for one turn: a new thread, or the existing one resumed.
        Everything else (provider, features, sandbox, MCP server) is in the attempt's config.toml."""
        head = ["codex", "exec"]
        if self._thread_id:
            head += ["resume", self._thread_id]
        return head + ["--json", "--skip-git-repo-check", "--ignore-rules", prompt]

    def _environment(self) -> dict:
        workspaces = self.task.workspaces_dir.resolve()
        env = {k: v for k, v in os.environ.items()
               # The relay holds the model's credentials; the CLI must never call a model itself.
               if k not in ("OPENAI_API_KEY", "OPENAI_BASE_URL", "CODEX_API_KEY")}
        env.update(HOME=str(workspaces), CODEX_HOME=str(workspaces / ".codex"))
        return env

    async def run_conversation(self, initial_prompt: str) -> bool:
        self._pending_prompt = initial_prompt
        return await super().run_conversation()

    async def _execute_turn(self) -> bool:
        prompt, self._pending_prompt = self._pending_prompt, None
        if not prompt:
            self.logger.warning("[CodexConversationManager] No pending prompt for this turn; skipping")
            return False

        events_path = self.task.attempt_path / "codex_events.jsonl"
        stderr_path = self.task.attempt_path / self.config.logs_dir_name / "codex_stderr.log"
        stderr_path.parent.mkdir(parents=True, exist_ok=True)
        with open(stderr_path, "ab") as stderr:
            self._proc = await asyncio.create_subprocess_exec(
                *self.exec_command(prompt), cwd=str(self.task.workspaces_dir.resolve()),
                env=self._environment(), stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE, stderr=stderr, limit=EVENT_LINE_LIMIT)
            stop_watch = asyncio.create_task(self._stop_when_submitted())
            try:
                with open(events_path, "a", encoding="utf-8") as events:
                    async for line in self._proc.stdout:
                        text = line.decode("utf-8", errors="replace").strip()
                        if not text:
                            continue
                        events.write(text + "\n")
                        try:
                            event = json.loads(text)
                        except ValueError:
                            continue
                        if event.get("type") == "thread.started" and not self._thread_id:
                            self._thread_id = event.get("thread_id")
                            self.logger.info(f"[CodexConversationManager] thread {self._thread_id}")
                await self._proc.wait()
            finally:
                stop_watch.cancel()
        self.logger.info(f"[CodexConversationManager] turn ended, exit {self._proc.returncode}")
        self._proc = None
        return self._stop_event.is_set()

    async def _stop_when_submitted(self) -> None:
        """End the CLI once the task's submission tool has fired: the review is in."""
        await self._stop_event.wait()
        await self._terminate()

    async def _terminate(self) -> None:
        proc = self._proc
        if proc is None or proc.returncode is not None:
            return
        proc.terminate()
        try:
            await asyncio.wait_for(proc.wait(), timeout=10)
        except asyncio.TimeoutError:
            proc.kill()

    async def _send_retry_prompt(self, prompt: str) -> None:
        self._pending_prompt = prompt

    def _create_retry_prompt(self) -> str:
        submit_tool_name = f"{self.config.mcp_server_name}submit_result"
        return (
            f"Continue. You must submit your final result using the `{submit_tool_name}` tool "
            "when you have completed the task. "
            "Leverage all available tools to thoroughly complete the task. "
            "Analyze, create, modify, verify, and iterate as needed. "
            f"When the task is fully completed, use `{submit_tool_name}`."
        )

    async def _interrupt_internal(self) -> None:
        await self._terminate()

    async def _cleanup_internal(self) -> None:
        await self._terminate()
