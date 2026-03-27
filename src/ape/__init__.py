"""
APE (Autonomous Proof Engineering) - A Boundary-Controlled Agent System.

This package provides a framework for autonomous proof engineering tasks,
including theorem proving, proof engineering, and code judgment in Lean 4.
"""

__version__ = "0.1.0"

__all__ = [
    "BaseTask",
    "register_task",
    "TaskOrchestrator",
    "run_orchestrator_from_file",
    "BaseScaffold",
]


def __getattr__(name: str):
    """Lazily load top-level exports to avoid circular imports during package startup."""
    if name in {"BaseTask", "register_task"}:
        from ape.tasks.base import BaseTask, register_task

        exports = {
            "BaseTask": BaseTask,
            "register_task": register_task,
        }
        return exports[name]

    if name in {"TaskOrchestrator", "run_orchestrator_from_file"}:
        from ape.orchestration.orchestrator import TaskOrchestrator, run_orchestrator_from_file

        exports = {
            "TaskOrchestrator": TaskOrchestrator,
            "run_orchestrator_from_file": run_orchestrator_from_file,
        }
        return exports[name]

    if name == "BaseScaffold":
        from ape.scaffolds.base import BaseScaffold

        return BaseScaffold

    raise AttributeError(f"module 'ape' has no attribute {name!r}")
