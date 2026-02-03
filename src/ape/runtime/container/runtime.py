"""Container Runtime - Container-based execution using Docker.

Provides isolated execution in Docker containers.

Key Design:
1. Setup Phase (on host):
   - Create temp_task to resolve workspaces and collect resource paths
   - Sync required resources (src/, lean workspaces, etc.) to container

2. Execution Phase (in container):
   - Container runs scaffolds/runner.py which calls task.setup() again
   - This creates fresh workspaces inside container at the same relative paths
   - Scaffolds execute and produce results in container's attempt_path/

3. Sync Back Phase (to host):
   - Download attempt_path/ from container (excluding read-only target/reference)
   - Recreate workspace symlinks on host
   - Final result "looks like" it was executed directly on host

Path Alignment:
   - Host: PROJECT_ROOT/runs/{orchestrator_id}/{attempt_id}/
   - Container: /workspace/runs/{orchestrator_id}/{attempt_id}/
   - Relative paths are preserved so container results can be synced back to host
"""

import asyncio
import base64
import json
import os
import shutil
import tarfile
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, Literal

import docker
from docker.errors import DockerException
from pydantic import Field

from ape.runtime.base import BaseRuntime, RuntimeConfig
from ape.runtime.utils import collect_blocked_paths, collect_readonly_paths
from ape.tasks.base import get_task_class
from ape.utils.project import PROJECT_ROOT

if TYPE_CHECKING:
    import logging
    from ape.scaffolds.base import ScaffoldTerminationResult
    from ape.scaffolds.config import BaseScaffoldConfig
    from ape.tasks.base import BaseTaskResult
    from ape.tasks.models import WorkspaceInfo


# =============================================================================
# Configuration
# =============================================================================

class ContainerRuntimeConfig(RuntimeConfig):
    """Configuration for Docker-backed container runtime."""

    runtime_type: Literal['container'] = Field(
        default='container',
        description="Docker runtime type"
    )
    docker_image: str = Field(
        default="python:3.11",
        description="Container image for execution"
    )
    docker_python_path: str = Field(
        default='python',
        description="Python executable inside container"
    )
    docker_environment: Dict[str, str] = Field(
        default_factory=dict,
        description="Extra environment variables injected into container"
    )
    container_project_root: str = Field(
        default='/workspace',
        description="Project root path inside container"
    )
    timeout: int = Field(
        default=3600,
        description="Timeout in seconds for container execution"
    )

# =============================================================================
# Docker Runtime
# =============================================================================

class ContainerRuntime(BaseRuntime):
    """Runtime implementation that executes tasks inside Docker containers."""

    config_class = ContainerRuntimeConfig

    def __init__(self, config: ContainerRuntimeConfig, logger: Optional['logging.LoggerAdapter'] = None):
        super().__init__(config, logger)
        self.docker_client = None
        self.container = None
        self.container_python = config.docker_python_path

        # Task execution context
        self.task_data: Optional[dict] = None
        self.scaffold_config: Optional['BaseScaffoldConfig'] = None
        self.orchestrator_id: Optional[str] = None
        self.attempt_path: Optional[Path] = None

    async def run_task(
        self,
        task_data: dict,
        config: 'BaseScaffoldConfig',
        scaffold_type: str,
        orchestrator_id: str,
        attempt_path: Path,
        cost_limit: Optional[float] = None,
    ) -> Tuple['BaseTaskResult', Optional['ScaffoldTerminationResult']]:
        """Execute task within docker container.

        Workflow:
        1. Setup Phase: Prepare resources on host and sync to container
        2. Execution Phase: Run task in container
        3. Sync Back Phase: Download results from container to host
        """
        from ape.utils.logging import create_logger
        from datetime import datetime

        if not task_data.get('task_type'):
            raise ValueError("task_data must contain 'task_type' field")

        if not orchestrator_id:
            raise RuntimeError("orchestrator_id is required for container runtime")

        # Setup runtime-specific logger
        logs_dir = attempt_path / config.logs_dir_name
        logs_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        runtime_log_file = logs_dir / f"runtime_{timestamp}.log"

        original_logger = self.logger
        self.logger = create_logger(log_file=runtime_log_file, to_console=False)

        # Initialize Docker client
        self.docker_client = docker.from_env()
        
        try:
            # Store context
            self.task_data = task_data
            self.scaffold_config = config
            self.orchestrator_id = orchestrator_id
            self.attempt_path = attempt_path

            if self.logger:
                self.logger.info(f"[ContainerRuntime] Starting task execution in Docker container")

            # Create and start container
            self.container = self.docker_client.containers.run(
                self.config.docker_image,
                command='tail -f /dev/null',  # Keep container alive
                detach=True,
                remove=False,
                working_dir=self.config.container_project_root,
                environment=self.config.docker_environment,
            )

            if self.logger:
                self.logger.info(f"[ContainerRuntime] Container started: {self.container.id[:12]}")

            # Phase 1: Setup and sync resources to container
            await self.setup_phase()

            # Phase 2: Execute task in container
            exec_result = await self.execution_phase(scaffold_type, cost_limit)

            # Phase 3: Sync results back to host
            await self.sync_back_phase()

            # Phase 4: Parse result
            task_result, termination = self.parse_task_result(exec_result, task_data['task_type'])

            if self.logger:
                self.logger.info(
                    f"[ContainerRuntime] Task {task_data.get('task_id', 'unknown')} completed: "
                    f"success={task_result.success}, score={task_result.score:.3f}"
                )

            return task_result, termination

        finally:
            # Clean up container
            if self.container:
                try:
                    self.container.stop(timeout=10)
                    self.container.remove()
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"[ContainerRuntime] Error cleaning up container: {e}")

            # Clean up Docker client
            if self.docker_client:
                self.docker_client.close()

            # Restore logger
            if self.logger:
                for handler in self.logger.logger.handlers[:]:
                    handler.close()
                    self.logger.logger.removeHandler(handler)

            self.logger = original_logger

    def parse_task_result(self, stdout: str, task_type: str) -> Tuple['BaseTaskResult', Optional['ScaffoldTerminationResult']]:
        """Parse task result from stdout."""
        from ape.scaffolds.base import ScaffoldTerminationResult
        from ape.tasks.base import BaseTaskResult

        task_result = None
        termination = None

        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            
            try:
                data = json.loads(line)
                if 'task_result' in data:
                    task_class = get_task_class(task_type)
                    try:
                        task_result = task_class.result_class(**data['task_result'])
                    except Exception:
                        task_result = BaseTaskResult(**data['task_result'])
                
                if 'termination' in data and data['termination']:
                    termination = ScaffoldTerminationResult(**data['termination'])
                
                if task_result:
                    break
            except json.JSONDecodeError:
                continue

        if not task_result:
            raise RuntimeError(f"Failed to parse task result from stdout")

        return task_result, termination

    async def setup_phase(self):
        """Setup phase: prepare and sync resources to container."""
        if self.logger:
            self.logger.info("[ContainerRuntime] Starting setup phase")

        # Create temp task to resolve workspace paths
        task_class = get_task_class(self.task_data['task_type'])
        temp_task = task_class(
            task_data=self.task_data,
            attempt_path=self.attempt_path,
            scaffold_config=self.scaffold_config
        )
        temp_task.setup()

        # Sync project source code
        await self._sync_directory_to_container(
            PROJECT_ROOT / "src",
            Path(self.config.container_project_root) / "src"
        )

        if self.logger:
            self.logger.info("[ContainerRuntime] Setup phase completed")

    async def execution_phase(self, scaffold_type: str, cost_limit: Optional[float]) -> str:
        """Execution phase: run task in container."""
        if self.logger:
            self.logger.info("[ContainerRuntime] Starting execution phase")

        # Build runner command
        runner_cmd = [
            self.container_python,
            "-m", "ape.scaffolds.runner",
            "--scaffold-type", scaffold_type,
            "--task-data-json", json.dumps(self.task_data),
            "--scaffold-config-json", self.scaffold_config.model_dump_json(),
            "--orchestrator-id", self.orchestrator_id,
            "--attempt-path", str(Path(self.config.container_project_root) / "runs" / self.orchestrator_id / self.attempt_path.name),
        ]

        if cost_limit is not None:
            runner_cmd.extend(["--cost-limit", str(cost_limit)])

        # Execute in container
        exit_code, output = self.container.exec_run(
            runner_cmd,
            workdir=self.config.container_project_root,
            environment=self.config.docker_environment,
        )

        stdout = output.decode('utf-8', errors='replace')

        if self.logger:
            self.logger.info(f"[ContainerRuntime] Execution completed with exit code: {exit_code}")

        return stdout

    async def sync_back_phase(self):
        """Sync back phase: download results from container to host."""
        if self.logger:
            self.logger.info("[ContainerRuntime] Starting sync back phase")

        # Download attempt directory from container
        container_attempt_path = Path(self.config.container_project_root) / "runs" / self.orchestrator_id / self.attempt_path.name

        try:
            # Get tar archive from container
            bits, stat = self.container.get_archive(str(container_attempt_path))
            
            # Extract to host
            with tempfile.NamedTemporaryFile(suffix='.tar', delete=False) as tmp_file:
                for chunk in bits:
                    tmp_file.write(chunk)
                tmp_tar_path = tmp_file.name

            with tarfile.open(tmp_tar_path, 'r') as tar:
                tar.extractall(path=self.attempt_path.parent)

            os.unlink(tmp_tar_path)

            if self.logger:
                self.logger.info("[ContainerRuntime] Sync back completed")

        except Exception as e:
            if self.logger:
                self.logger.warning(f"[ContainerRuntime] Sync back failed: {e}")

    async def _sync_directory_to_container(self, host_path: Path, container_path: Path):
        """Sync a directory from host to container."""
        if not host_path.exists():
            if self.logger:
                self.logger.warning(f"[ContainerRuntime] Host path does not exist: {host_path}")
            return

        # Create tar archive
        with tempfile.NamedTemporaryFile(suffix='.tar', delete=False) as tmp_file:
            with tarfile.open(fileobj=tmp_file, mode='w') as tar:
                tar.add(str(host_path), arcname=host_path.name)
            tmp_tar_path = tmp_file.name

        # Upload to container
        with open(tmp_tar_path, 'rb') as f:
            self.container.put_archive(str(container_path.parent), f.read())

        os.unlink(tmp_tar_path)

        if self.logger:
            self.logger.debug(f"[ContainerRuntime] Synced {host_path} to {container_path}")


# Register runtime
from ape.runtime.registry import register_runtime
register_runtime('container', ContainerRuntime)
