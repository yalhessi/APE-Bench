"""
APE (Autonomous Proof Engineering) - A Boundary-Controlled Agent System.

This package provides a framework for autonomous proof engineering tasks,
including theorem proving, proof engineering, and code judgment in Lean 4.
"""

__version__ = "0.1.0"

# Core module exports
from ape.tasks.base import BaseTask, register_task
from ape.orchestration.orchestrator import TaskOrchestrator, run_orchestrator_from_file
from ape.scaffolds.base import BaseScaffold

__all__ = [
    "BaseTask",
    "register_task",
    "TaskOrchestrator",
    "run_orchestrator_from_file",
    "BaseScaffold",
]
