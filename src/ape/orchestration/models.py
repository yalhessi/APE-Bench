"""
Orchestration Data Models - Resume and retry aware execution state.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, AliasChoices


# ============================================================================
# Execution Status Enums
# ============================================================================

class ExecutionStatus(str, Enum):
    """Execution status applicable to all levels."""

    # Before/during execution
    PENDING = "pending"
    RUNNING = "running"

    # Successfully completed
    SUCCESS = "success"

    # Paused states (resumable)
    PAUSED_MAX_TURNS = "paused_max_turns"
    PAUSED_COST_LIMIT = "paused_cost_limit"

    # Failed states (not continuable)
    FAILED_MODEL = "failed_model"
    FAILED_EARLY_STOP = "failed_early_stop"
    FAILED_ERROR = "failed_error"

    def is_terminal(self) -> bool:
        """Check if this is a terminal state (will not execute again)."""
        return self in {
            ExecutionStatus.SUCCESS,
            ExecutionStatus.FAILED_MODEL,
            ExecutionStatus.FAILED_EARLY_STOP
        }

    def is_paused(self) -> bool:
        """Check if this is a paused state (resumable)."""
        return self in {
            ExecutionStatus.PAUSED_MAX_TURNS,
            ExecutionStatus.PAUSED_COST_LIMIT
        }

    def is_system_error(self) -> bool:
        """Check if this is a system error (retryable)."""
        return self == ExecutionStatus.FAILED_ERROR


def make_sample_id(task_global_index: str, sample_index: int) -> str:
    """Generate sample ID uniformly (maintains compatibility with old format)."""
    return f"{task_global_index}_{sample_index}"


# ============================================================================
# Attempt - Single execution attempt
# ============================================================================

class Attempt(BaseModel):
    """Single execution attempt - corresponds to one workspace."""
    
    attempt_id: int
    path: Path = Field(validation_alias=AliasChoices('path', 'workspace_path'))
    status: ExecutionStatus = ExecutionStatus.PENDING
    
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    result: Optional[Any] = None  # BaseTaskResult
    error_message: Optional[str] = None
    
    cost: float = 0.0
    cached_cost: float = 0.0
    turns: int = 0
    
    max_turns: int
    cost_limit: Optional[float]


# ============================================================================
# Sample - Sample execution record
# ============================================================================

class Sample(BaseModel):
    """Sample execution record - contains retry chain."""

    sample_id: str
    sample_index: int
    task_global_index: str

    attempts: List[Attempt] = Field(default_factory=list)

    created_at: datetime
    updated_at: datetime

    @property
    def current_attempt(self) -> Optional[Attempt]:
        """Get current valid attempt."""
        return self.attempts[-1] if self.attempts else None

    @property
    def successful_attempt(self) -> Optional[Attempt]:
        """Most recent attempt that succeeded, if any.

        Consumers that need the artifacts a sample produced (its workspace, logs, or
        conversation) want this rather than `current_attempt`, which may be a later
        failed retry. Exposed so callers locate attempt directories through the model
        instead of globbing the run tree's layout.
        """
        for attempt in reversed(self.attempts):
            if attempt.status == ExecutionStatus.SUCCESS:
                return attempt
        return None

    @property
    def status(self) -> ExecutionStatus:
        """Sample status = current attempt's status."""
        return self.current_attempt.status if self.current_attempt else ExecutionStatus.PENDING

    def get_effective_cost(self) -> float:
        """Effective cost: cost of last non-system-error attempt.

        Purpose: Determine if cost_limit is exceeded (resource control).

        Reads `cached_cost` — what was actually billed — rather than `cost`, which is the
        no-cache counterfactual. The resource being controlled is money, and prompt caching
        means the two differ by a lot: one lead was terminated at a $1.00 cap on a counted
        $1.164 having actually spent $0.200, so it lost four fifths of its budget to an
        accounting convention. Falls back to `cost` when no cached figure was recorded, which
        is also the case where the two are equal.
        """
        for attempt in reversed(self.attempts):
            if not attempt.status.is_system_error():
                cached = getattr(attempt, "cached_cost", None)
                return float(cached) if cached else attempt.cost
        return 0.0

    def get_accumulated_cost(self) -> float:
        """Accumulated cost: sum of all attempt costs.

        Purpose: Track actual spending.
        """
        return sum(a.cost for a in self.attempts)

    def get_accumulated_cached_cost(self) -> float:
        """Get accumulated cached cost."""
        return sum(a.cached_cost for a in self.attempts)

    def get_current_turns(self) -> int:
        """Get current conversation turns."""
        for attempt in reversed(self.attempts):
            if not attempt.status.is_system_error():
                return attempt.turns
        return 0

    def get_error_count(self) -> int:
        """Get system error count."""
        return sum(1 for a in self.attempts if a.status.is_system_error())

    def get_attempt_count(self) -> int:
        """Get total attempt count."""
        return len(self.attempts)

    def is_retryable(self, max_retries: int) -> bool:
        """Check if retry is still possible (for system errors)."""
        if not self.attempts:
            return True
        current = self.current_attempt
        if not current:
            return True
        if not current.status.is_system_error():
            return False
        return self.get_error_count() <= max_retries

    def can_execute(self, max_retries: int, max_turns: int, sample_max_cost: Optional[float]) -> bool:
        """Check if execution is possible (first time/retry/resume).

        Returns False when:
        1. Already terminated
        2. System error and retries exhausted
        3. Paused and cannot resume (resource limits)
        """
        if not self.attempts:
            return True

        current = self.current_attempt

        if current.status.is_terminal():
            return False

        if current.status.is_system_error():
            return self.get_error_count() <= max_retries

        if current.status.is_paused():
            if current.status == ExecutionStatus.PAUSED_MAX_TURNS:
                return self.get_current_turns() < max_turns
            elif current.status == ExecutionStatus.PAUSED_COST_LIMIT:
                return sample_max_cost is None or self.get_effective_cost() < sample_max_cost

        return current.status in {ExecutionStatus.PENDING, ExecutionStatus.RUNNING}

    def to_progress(
        self,
        max_retries: int,
        max_turns: int,
        sample_max_cost: Optional[float]
    ) -> "SampleProgress":
        """Construct SampleProgress snapshot."""
        attempt = self.current_attempt
        status = attempt.status if attempt else ExecutionStatus.PENDING
        can_retry = status.is_system_error() and self.get_error_count() <= max_retries
        can_resume = status.is_paused() and self.can_execute(max_retries, max_turns, sample_max_cost)
        last_error = attempt.error_message if attempt else None

        return SampleProgress(
            sample_id=self.sample_id,
            task_global_index=self.task_global_index,
            sample_index=self.sample_index,
            status=status,
            attempt_count=self.get_attempt_count(),
            error_count=self.get_error_count(),
            cost=self.get_accumulated_cost(),
            cached_cost=self.get_accumulated_cached_cost(),
            can_retry=can_retry,
            can_resume=can_resume,
            last_error=last_error,
            last_updated=self.updated_at
        )

# ============================================================================
# Progress State - Persisted to progress.json
# ============================================================================

class SampleProgress(BaseModel):
    """Sample progress snapshot (for progress.json)."""
    sample_id: str
    task_global_index: str
    sample_index: int
    status: ExecutionStatus
    attempt_count: int = 0
    error_count: int = 0
    cost: float = 0.0
    cached_cost: float = 0.0
    can_retry: bool = True
    can_resume: bool = False  # Whether a paused sample can be resumed
    last_error: Optional[str] = None
    last_updated: datetime = Field(default_factory=datetime.now)


class OrchestratorProgress(BaseModel):
    """Orchestrator progress state (for progress.json)."""

    last_updated: datetime
    total_tasks: int
    total_samples: int

    completed_tasks: int = 0
    successful_tasks: int = 0
    passed_tasks: int = 0
    completed_task_indices: List[str] = Field(default_factory=list)

    task_custom_metrics: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    samples: Dict[str, SampleProgress] = Field(default_factory=dict)

    def get_status_counts(self) -> Dict[str, int]:
        """Count samples by status."""
        from collections import Counter
        return dict(Counter(s.status.value for s in self.samples.values()))

    def get_total_cost(self) -> float:
        return sum(s.cost for s in self.samples.values())

    def get_total_cached_cost(self) -> float:
        return sum(s.cached_cost for s in self.samples.values())

    def get_resumable_count(self) -> int:
        return sum(1 for s in self.samples.values()
                   if s.status.is_paused() and s.can_resume)

    def get_retryable_count(self) -> int:
        return sum(1 for s in self.samples.values()
                   if s.status.is_system_error() and s.can_retry)

    def get_failed_count(self) -> int:
        count = 0
        for s in self.samples.values():
            if s.status in {
                ExecutionStatus.FAILED_MODEL,
                ExecutionStatus.FAILED_EARLY_STOP,
                ExecutionStatus.FAILED_ERROR
            }:
                count += 1
            elif s.status.is_paused() and not s.can_resume:
                count += 1
        return count

    def get_aggregated_custom_metrics(self) -> Optional[Dict[str, float]]:
        if not self.task_custom_metrics:
            return None
        
        from collections import defaultdict
        metrics_by_key: Dict[str, List[float]] = defaultdict(list)
        
        for task_metrics in self.task_custom_metrics.values():
            for key, value in task_metrics.items():
                if isinstance(value, (int, float)):
                    metrics_by_key[key].append(float(value))
        
        if not metrics_by_key:
            return None
        
        aggregated = {}
        for key, values in metrics_by_key.items():
            if values:
                aggregated[key] = sum(values) / len(values)
        
        return aggregated if aggregated else None


# ============================================================================
# Final Results Model
# ============================================================================

class OrchestratorResults(BaseModel):
    """Task orchestration results."""

    orchestrator_id: str
    scaffold_type: str
    task_results: List[Any]

    total_tasks: int
    completed_tasks: int
    successful_tasks: int
    passed_tasks: int

    completion_rate: float
    success_rate: float
    pass_rate_local: float
    pass_rate_global: float
    average_score: float

    wall_clock_time: float
    cumulative_execution_time: float
    average_task_time: float
    started_at: datetime
    completed_at: datetime

    config_snapshot: Dict[str, Any] = Field(default_factory=dict)
    total_token_usage: Optional[Any] = None
    workspace_path: Path

    # Simplified statistics
    total_samples: int
    successful_samples: int
    total_cost: float
    total_cached_cost: float
