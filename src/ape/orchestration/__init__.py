"""
Orchestration Layer - Task orchestration and execution management.

Simplified exports:
- Core classes: TaskOrchestrator
- Configuration: ExecutionConfig, EarlyStopMode
- Convenience functions: run_orchestrator_from_file
"""

__all__ = [
    'TaskOrchestrator',
    'run_orchestrator_from_file',
    'ExecutionConfig',
    'EarlyStopMode',
    'ExecutionStatus',
    'OrchestratorResults',
]


def __getattr__(name: str):
    """Lazily load orchestration exports to avoid circular imports during submodule import."""
    if name in {'TaskOrchestrator', 'run_orchestrator_from_file'}:
        from .orchestrator import TaskOrchestrator, run_orchestrator_from_file

        exports = {
            'TaskOrchestrator': TaskOrchestrator,
            'run_orchestrator_from_file': run_orchestrator_from_file,
        }
        return exports[name]

    if name in {'ExecutionConfig', 'EarlyStopMode'}:
        from .config import ExecutionConfig, EarlyStopMode

        exports = {
            'ExecutionConfig': ExecutionConfig,
            'EarlyStopMode': EarlyStopMode,
        }
        return exports[name]

    if name in {'ExecutionStatus', 'OrchestratorResults'}:
        from .models import ExecutionStatus, OrchestratorResults

        exports = {
            'ExecutionStatus': ExecutionStatus,
            'OrchestratorResults': OrchestratorResults,
        }
        return exports[name]

    raise AttributeError(f"module 'ape.orchestration' has no attribute {name!r}")
