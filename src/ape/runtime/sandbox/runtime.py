"""Sandbox Runtime - Isolated execution on host machine.

Provides sandbox implementations using platform-specific isolation:
- Linux: bubblewrap (lightweight namespace isolation)
- macOS: sandbox-exec (Seatbelt policy enforcement)

Design: All paths remain consistent between sandbox and host.
No path conversion is performed.
"""

import asyncio
import json
import os
import sys
import traceback
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Tuple, Literal

from pydantic import Field

from ape.runtime.base import BaseRuntime, RuntimeConfig
from ape.runtime.utils import get_global_writable_paths, collect_blocked_paths, collect_readonly_paths
from ape.tasks.base import get_task_class, BaseTaskResult

if TYPE_CHECKING:
    import logging
    from ape.tasks.base import BaseTaskResult
    from ape.scaffolds.base import ScaffoldTerminationResult
    from ape.scaffolds.config import BaseScaffoldConfig


# =============================================================================
# Configuration
# =============================================================================

class SandboxRuntimeConfig(RuntimeConfig):
    """Sandbox runtime configuration."""

    runtime_type: Literal['sandbox'] = Field(
        default='sandbox',
        description="Sandbox runtime type"
    )
    sandbox_enable_network: bool = Field(
        default=True,
        description="Enable network access inside sandbox"
    )
    sandbox_timeout: int = Field(
        default=7200,
        description="Maximum execution time in seconds"
    )


# =============================================================================
# Base Sandbox Implementation
# =============================================================================

class BaseSandbox(BaseRuntime):
    """Base class for sandbox implementations."""

    config_class = SandboxRuntimeConfig

    def get_sandbox_name(self) -> str:
        """Return sandbox name for logging."""
        raise NotImplementedError

    def build_sandbox_command(
        self,
        attempt_path: Path,
        runner_args: list,
        blocked_paths: list = None,
        readonly_paths: list = None
    ) -> list:
        """Build platform-specific sandbox command with access control."""
        raise NotImplementedError

    async def execute_subprocess(self, command: list, task_id: str) -> Tuple[str, str, int]:
        """Execute command as subprocess with timeout and cancellation support."""
        process = None
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.config.sandbox_timeout
                )
                stdout = stdout_bytes.decode('utf-8', errors='replace')
                stderr = stderr_bytes.decode('utf-8', errors='replace')
                returncode = process.returncode

            except asyncio.TimeoutError:
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
                raise RuntimeError(
                    f"Task execution timeout after {self.config.sandbox_timeout}s"
                )

        except asyncio.CancelledError:
            if process and process.returncode is None:
                self.logger.info(f"[{self.get_sandbox_name()}] Task {task_id} cancelled, terminating subprocess")
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    self.logger.warning(f"[{self.get_sandbox_name()}] Subprocess didn't terminate, killing")
                    process.kill()
                    await process.wait()
            raise

        except Exception as e:
            if process and process.returncode is None:
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=2.0)
                except:
                    process.kill()
            raise RuntimeError(f"Failed to execute {self.get_sandbox_name()}: {e}\n{traceback.format_exc()}")

        return stdout, stderr, returncode

    def parse_task_result(self, stdout: str, task_type: str) -> Tuple['BaseTaskResult', Optional['ScaffoldTerminationResult']]:
        """Parse task result from stdout.

        Attempts to parse with task-specific result class first, falls back to
        BaseTaskResult if parsing fails (e.g., when task failed/was cancelled).
        """
        from ape.scaffolds.base import ScaffoldTerminationResult
        from ape.tasks.base import BaseTaskResult

        task_result = None
        termination = None
        errors = []

        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                result_data = json.loads(line)
                task_result_cls = get_task_class(task_type).task_result_class

                # Try task-specific result class first
                try:
                    task_result = task_result_cls.model_validate(result_data['task_result'])
                except Exception as e:
                    # Fall back to BaseTaskResult if task-specific class fails
                    # This is normal when task failed/was cancelled
                    if self.logger:
                        self.logger.warning(
                            f"Failed to parse with {task_result_cls.__name__}, "
                            f"falling back to BaseTaskResult: {e}"
                        )
                    task_result = BaseTaskResult.model_validate(result_data['task_result'])

                termination = ScaffoldTerminationResult.model_validate(
                    result_data['termination']
                ) if result_data.get('termination') else None
                break
            except Exception as e:
                errors.append(f"Line: {line[:100]}... Error: {e}")
                continue

        if task_result is None:
            error_details = "\n".join(errors[:5])
            raise RuntimeError(
                f"Failed to parse and validate task result from any line in stdout.\n"
                f"First {min(5, len(errors))} errors:\n{error_details}\n"
                f"Full stdout: {stdout}"
            )

        return task_result, termination

    async def run_task(
        self,
        task_data: dict,
        config: 'BaseScaffoldConfig',
        scaffold_type: str,
        orchestrator_id: str,
        attempt_path: Path,
        cost_limit: Optional[float] = None,
    ) -> Tuple['BaseTaskResult', Optional['ScaffoldTerminationResult']]:
        """Execute task in sandbox."""
        from ape.utils.logging import create_logger
        from datetime import datetime

        if not task_data.get('task_type'):
            raise ValueError("task_data must contain 'task_type' field")

        task_id = task_data.get('task_id', 'unknown')
        attempt_path.mkdir(parents=True, exist_ok=True)

        # Setup runtime-specific logger
        logs_dir = attempt_path / config.logs_dir_name
        logs_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        runtime_log_file = logs_dir / f"runtime_{timestamp}.log"

        original_logger = self.logger
        self.logger = create_logger(log_file=runtime_log_file, to_console=False)

        try:
            # Setup attempt directory and workspaces to get access control info
            task_class = get_task_class(task_data['task_type'])
            _, scratch_workspace, target_workspace, reference_workspaces = await task_class.setup_attempt(
                data=task_class.create_data_from_dict(task_data),
                config=config,
                orchestrator_id=orchestrator_id,
                attempt_path=attempt_path,
                logger=self.logger
            )

            # Collect blocked and readonly paths from all workspaces
            blocked_paths = []
            readonly_paths = []

            if scratch_workspace:
                blocked_paths.extend(collect_blocked_paths(scratch_workspace, self.logger))
                readonly_paths.extend(collect_readonly_paths(scratch_workspace, self.logger))

            if target_workspace:
                blocked_paths.extend(collect_blocked_paths(target_workspace, self.logger))
                readonly_paths.extend(collect_readonly_paths(target_workspace, self.logger))

            if reference_workspaces:
                for ref_ws in reference_workspaces:
                    blocked_paths.extend(collect_blocked_paths(ref_ws, self.logger))
                    readonly_paths.extend(collect_readonly_paths(ref_ws, self.logger))

            # Prepare runner parameters
            params = {
                'task_data': task_data,
                'config': config.model_dump(mode='json'),
                'scaffold_type': scaffold_type,
                'orchestrator_id': orchestrator_id,
                'cost_limit': cost_limit,
                'attempt_path': str(attempt_path)
            }

            # Build sandbox command with access control paths
            runner_cmd = [sys.executable, '-m', 'ape.scaffolds.runner', json.dumps(params)]
            sandbox_cmd = self.build_sandbox_command(attempt_path, runner_cmd, blocked_paths, readonly_paths)

            # Execute
            self.logger.info(f"[{self.get_sandbox_name()}] Executing task: {task_id}")
            stdout, stderr, returncode = await self.execute_subprocess(sandbox_cmd, task_id)

            if returncode != 0:
                raise RuntimeError(
                    f"Task execution failed (exit code: {returncode})\n"
                    f"stdout: {stdout}\nstderr: {stderr}"
                )

            # Parse result
            task_result, termination = self.parse_task_result(stdout, task_data['task_type'])

            self.logger.info(
                f"[{self.get_sandbox_name()}] Task completed: success={task_result.success}, score={task_result.score}"
            )

            return task_result, termination

        finally:
            if self.logger:
                for handler in self.logger.logger.handlers[:]:
                    try:
                        handler.close()
                        self.logger.logger.removeHandler(handler)
                    except Exception:
                        pass
            self.logger = original_logger


# =============================================================================
# Linux Sandbox (bubblewrap)
# =============================================================================

class LinuxSandbox(BaseSandbox):
    """Linux sandbox implementation using bubblewrap."""

    def get_sandbox_name(self) -> str:
        return "LinuxSandbox"

    def build_sandbox_command(
        self,
        attempt_path: Path,
        runner_args: list,
        blocked_paths: list = None,
        readonly_paths: list = None
    ) -> list:
        """Build complete bwrap command with mount isolation and access control.

        All paths are mounted to same location as on host (no path conversion).
        Blocked paths are completely inaccessible, readonly paths cannot be written.
        """
        cmd = ['sudo', 'bwrap']

        # System mounts (read-only)
        cmd.extend([
            '--ro-bind', '/', '/',
            '--proc', '/proc',
            '--dev', '/dev',
            '--tmpfs', '/tmp',
        ])

        # Agent workspace (read-write, bind to same path)
        attempt_path = attempt_path.resolve()
        cmd.extend(['--bind', str(attempt_path), str(attempt_path)])

        # Global writable paths
        for global_path in get_global_writable_paths():
            global_path.mkdir(parents=True, exist_ok=True)
            cmd.extend(['--bind', str(global_path), str(global_path)])

        # Apply readonly paths first, then blocked paths
        # In bwrap, later mounts override earlier ones, so blocked paths will take precedence
        if readonly_paths:
            for readonly_path in readonly_paths:
                readonly_path = Path(readonly_path).resolve()
                if readonly_path.exists():
                    # Override with read-only bind mount
                    cmd.extend(['--ro-bind', str(readonly_path), str(readonly_path)])

        # Apply blocked paths by bind-mounting tmpfs/devnull
        # These take precedence over earlier bindings (including readonly)
        if blocked_paths:
            for blocked_path in blocked_paths:
                blocked_path = Path(blocked_path).resolve()
                if blocked_path.exists():
                    if blocked_path.is_dir():
                        # Block directory with tmpfs
                        cmd.extend(['--tmpfs', str(blocked_path)])
                    else:
                        # Block file by binding /dev/null
                        cmd.extend(['--ro-bind', '/dev/null', str(blocked_path)])

        # Namespace isolation
        cmd.extend([
            '--unshare-user',
            '--unshare-pid',
            '--unshare-ipc',
            '--unshare-uts',
            '--die-with-parent',
            '--new-session',
        ])

        # Network configuration
        if not self.config.sandbox_enable_network:
            cmd.append('--unshare-net')

        # User permissions
        cmd.extend([
            '--uid', str(os.getuid()),
            '--gid', str(os.getgid()),
        ])

        # Working directory and runner command
        cmd.extend(['--chdir', str(attempt_path), '--'])
        cmd.extend(runner_args)

        return cmd


# =============================================================================
# macOS Sandbox (sandbox-exec)
# =============================================================================

class MacOSSandbox(BaseSandbox):
    """macOS sandbox implementation using sandbox-exec (Seatbelt)."""

    def get_sandbox_name(self) -> str:
        return "MacOSSandbox"

    def build_sandbox_command(
        self,
        attempt_path: Path,
        runner_args: list,
        blocked_paths: list = None,
        readonly_paths: list = None
    ) -> list:
        """Build complete sandbox-exec command with access control."""
        profile = self.generate_sandbox_profile(attempt_path, blocked_paths, readonly_paths)
        return ['sandbox-exec', '-p', profile, '--'] + runner_args

    def generate_sandbox_profile(
        self,
        attempt_path: Path,
        blocked_paths: list = None,
        readonly_paths: list = None
    ) -> str:
        """Generate Seatbelt sandbox profile for file access control."""
        profile_lines = [
            '(version 1)',
            '(allow default)',
            '',
        ]

        # Deny all file writes by default
        profile_lines.extend([
            '; Deny all writes by default',
            '(deny file-write*)',
            '',
        ])

        # Allow writes to /dev/null
        profile_lines.extend([
            '; Allow writes to /dev/null (required by git)',
            '(allow file-write* (literal "/dev/null"))',
            '',
        ])

        # Allow writes to temp directories
        tmpdir = os.environ.get('TMPDIR', '')
        if tmpdir:
            profile_lines.extend([
                '; Allow writes to system temp directory (TMPDIR)',
                f'(allow file-write* (subpath "{Path(tmpdir).resolve()}"))',
                '',
            ])

        # Allow writes to /tmp (needed by browser-use and other tools)
        profile_lines.extend([
            '; Allow writes to /tmp',
            '(allow file-write* (subpath "/tmp"))',
            '',
        ])

        # Allow writes to agent workspace
        if attempt_path:
            profile_lines.extend([
                '; Allow writes to agent workspace',
                f'(allow file-write* (subpath "{attempt_path.resolve()}"))',
                '',
            ])

        # Allow writes to global writable paths
        for global_path in get_global_writable_paths():
            global_path.mkdir(parents=True, exist_ok=True)
            profile_lines.extend([
                f'; Allow writes to {global_path.name}',
                f'(allow file-write* (subpath "{global_path.resolve()}"))',
                '',
            ])

        # Readonly paths - allow reads but deny writes (override earlier write permissions)
        if readonly_paths:
            profile_lines.extend([
                '; Readonly paths - deny writes but allow reads',
            ])
            for readonly_path in readonly_paths:
                readonly_path = Path(readonly_path).resolve()
                if readonly_path.exists():
                    profile_lines.append(f'(deny file-write* (subpath "{readonly_path}"))')
            profile_lines.append('')

        # Blocked paths - deny all access (declared after readonly to ensure priority)
        if blocked_paths:
            profile_lines.extend([
                '; Blocked paths - deny all access (takes precedence over readonly)',
            ])
            for blocked_path in blocked_paths:
                blocked_path = Path(blocked_path).resolve()
                if blocked_path.exists():
                    profile_lines.append(f'(deny file-read* file-write* (subpath "{blocked_path}"))')
            profile_lines.append('')

        return '\n'.join(profile_lines)


# =============================================================================
# Registration
# =============================================================================

from ape.runtime.registry import register_runtime

# Register platform-specific sandbox runtime
if sys.platform == 'linux':
    register_runtime('sandbox', LinuxSandbox)
elif sys.platform == 'darwin':
    register_runtime('sandbox', MacOSSandbox)
