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
        """Accumulated billed cost across every attempt.

        This is what a cap must be checked against, not `get_effective_cost`: a sample that
        paused, resumed and paused again has spent the sum, and charging only the last attempt
        lets a sample loop indefinitely, each attempt staying under the cap on its own.
        Falls back to an attempt's nominal `cost` when no billed figure was recorded, which is
        also the case where the two are equal.
        """
        return sum((a.cached_cost or a.cost) for a in self.attempts)

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
                # Cumulative billed, matching what the conversation enforces. Charging only the
                # last attempt (`get_effective_cost`) let a sample resume forever, and reading
                # billed here while the conversation paused on nominal is what made a paused
                # job look resumable, skip aggregation, and book as failed at $0.00.
                return (sample_max_cost is None
                        or self.get_accumulated_cached_cost() < sample_max_cost)

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
# Subtask execution - one spec per child a task spawns
# ============================================================================
#
# `TaskOrchestrator(` is constructed directly in four files, each with its own convention for
# nesting, and the divergent one cost this project a class of accounting bugs. This is the
# shared shape: what a parent asks for when it spawns a child.


#: Where a task carries limits that differ from the orchestrator's. Read by the worker before
#: it builds the Attempt, and absent on almost every task -- the orchestrator-wide values stay
#: the default.
EXECUTION_LIMITS_KEY = "execution_limits"


class ExecutionLimits(BaseModel):
    """Per-task turn and cost ceilings.

    `Attempt.max_turns` and `Attempt.cost_limit` were already per-attempt fields, and
    `runtime.run_task` already took `cost_limit` per call -- both were simply always filled
    from `config.execution`. Letting a task carry its own is what retires budget *tiers*: the
    tier machinery existed to vary one number, `sample_max_cost`, by running each group in its
    own nested orchestrator.

    The cost is BILLED, matching every other cap in this codebase. Enforcing a cap on the
    no-cache counterfactual is what silently voided a job's work in September.
    """

    max_turns: int
    billed_cost_limit: Optional[float] = None


def task_execution_limits(task_data: Dict[str, Any], execution: Any) -> ExecutionLimits:
    """This task's limits, falling back to the orchestrator's.

    Never raises on a malformed override: a limit that cannot be parsed falls back rather than
    failing the run, because the orchestrator-wide value is always a safe answer.
    """

    raw = (task_data or {}).get(EXECUTION_LIMITS_KEY) or {}
    max_turns = execution.max_turns
    cost_limit = execution.sample_max_cost
    if isinstance(raw, dict):
        try:
            if raw.get("max_turns") is not None:
                max_turns = int(raw["max_turns"])
            if raw.get("billed_cost_limit") is not None:
                cost_limit = float(raw["billed_cost_limit"])
        except (TypeError, ValueError):
            pass
    return ExecutionLimits(max_turns=max_turns, billed_cost_limit=cost_limit)


class TaskExecutionSpec(BaseModel):
    """One child a parent task wants run.

    Carries what the orchestrator needs and what the parent needs back: identity, the typed
    payload, per-task limits, whether the child is required, and which budget scope its spend
    is charged to.
    """

    #: Stable identity within the parent's run, used to join the outcome back to the request.
    spec_id: str
    task_type: str
    task_data: Dict[str, Any]
    sample_count: int = 1
    max_turns: Optional[int] = None
    retries: int = 0
    #: Billed, like every other cap here.
    billed_cost_limit: Optional[float] = None
    #: A required child that does not succeed is a coverage gap, and a coverage gap closes the
    #: run as `partial` rather than complete.
    required: bool = False
    #: Which budget the spend is charged against. The coverage floor is deliberately exempt
    #: from the discretionary cap and must never be exempt from the run total.
    budget_scope: str = "discretionary"

    def with_limits(self) -> Dict[str, Any]:
        """The payload with this spec's limits attached, ready to hand to the orchestrator."""

        payload = dict(self.task_data)
        limits: Dict[str, Any] = {}
        if self.max_turns is not None:
            limits["max_turns"] = self.max_turns
        if self.billed_cost_limit is not None:
            limits["billed_cost_limit"] = self.billed_cost_limit
        if limits:
            payload[EXECUTION_LIMITS_KEY] = limits
        return payload


# ============================================================================
# Task Outcome - Persisted to task_outcome.json for EVERY scheduled task
# ============================================================================
#
# `task_result.json` is reserved for a legal successful submission, so a task that paused on
# budget, failed, or was cancelled leaves no trace of the money it spent. That is not
# hypothetical: a `family_design` arm on PR 33117 ran 184s, was billed real money, and reached
# the delegation ledger as `status=failed, cost=0.0` — which then satisfied a mandatory
# coverage check and was reported as an abstention.
#
# The shape follows the framework's own hierarchy, task -> samples -> attempts. It is not
# task -> attempts: the judge runs `sample_count: 3`, and collapsing the sample level would
# lose the majority-vote structure it depends on.


class AttemptOutcome(BaseModel):
    """One execution attempt. Immutable once written."""

    attempt_id: int
    status: ExecutionStatus
    #: What was actually paid. The cap is enforced against this.
    billed_cost: float = 0.0
    #: The no-cache counterfactual, kept for reporting only. Never call this "spend".
    nominal_cost: float = 0.0
    turns: int = 0
    error: Optional[str] = None
    path: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class SampleOutcome(BaseModel):
    """One sample and its retry/resume chain."""

    sample_index: int
    status: ExecutionStatus
    attempts: List[AttemptOutcome] = Field(default_factory=list)
    billed_cost: float = 0.0
    nominal_cost: float = 0.0
    #: Whether this sample may still run given the current limits.
    resumable: bool = False


class UsageBreakdown(BaseModel):
    """What something cost, in every way this project counts cost.

    Three axes get conflated, and each conflation has already cost this project a run:

    * **billed vs nominal.** `cached_total_cost` is what was paid; `total_cost` is the
      no-cache counterfactual. Prompt caching puts them ~2.5x apart -- the specialist4 run was
      $0.1218 billed against $0.3017 nominal. Caps enforce billed; the manifest reported
      nominal; nothing said which was which.
    * **self vs nested.** An agent's own conversation versus what its children spent. A lead
      that does not bubble its children's spend reports a fraction of its cost, which is how a
      floor's $14.52 went missing for a whole run.
    * **charged.** What a *particular* cap counted, which is neither of the above: the coverage
      floor is exempt from `per_pr_cost_cap` by design, so a lead's charged figure is smaller
      than its billed figure and both are correct.

    Every one of those numbers was already computed somewhere. None of them could be stated
    together, because they lived on `TaskOutcome`, on `JobOutcome` and in the manifest as
    bare floats named `cost`.
    """

    #: This agent's own conversation.
    self_billed: float = 0.0
    self_nominal: float = 0.0
    #: Everything its children spent, at any depth.
    nested_billed: float = 0.0
    nested_nominal: float = 0.0
    #: What a cap actually counted. Zero means "no cap looked at this", not "this was free" --
    #: `budget_charged` is only meaningful where a budget was being enforced.
    budget_charged: float = 0.0

    @property
    def billed(self) -> float:
        """Inclusive. The number to compare against a dollar figure."""

        return round(self.self_billed + self.nested_billed, 6)

    @property
    def nominal(self) -> float:
        """Inclusive, and never spend. For reporting cache effectiveness, nothing else."""

        return round(self.self_nominal + self.nested_nominal, 6)

    def with_nested(self, *, billed: float, nominal: float) -> "UsageBreakdown":
        return self.model_copy(update={
            "nested_billed": round(billed, 6), "nested_nominal": round(nominal, 6)})

    @classmethod
    def of_self(cls, *, billed: float, nominal: float) -> "UsageBreakdown":
        return cls(self_billed=round(billed, 6), self_nominal=round(nominal, 6))

    def summary(self) -> Dict[str, float]:
        """The flat form, for a manifest or a report. Every key names its axis."""

        return {
            "self_billed": round(self.self_billed, 6),
            "self_nominal": round(self.self_nominal, 6),
            "nested_billed": round(self.nested_billed, 6),
            "nested_nominal": round(self.nested_nominal, 6),
            "billed": self.billed,
            "nominal": self.nominal,
            "budget_charged": round(self.budget_charged, 6),
        }


class TaskExecutionStatus(str, Enum):
    """How a task's execution ended, independent of what it concluded.

    Distinct from `BaseTaskResult.success`, which is the *domain* verdict: a judgment task that
    correctly returns a negative verdict is `execution_status=completed, success=False`. A task
    that ran out of budget is `execution_status=paused` and has no result at all.
    """

    COMPLETED = "completed"
    PAUSED = "paused"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskOutcome(BaseModel):
    """Execution record for one scheduled task. Written whether or not it produced a result."""

    task_id: str
    task_type: str
    global_index: str
    execution_status: TaskExecutionStatus
    #: True when `task_result.json` was written. A paused or failed task has no result, and one
    #: is never synthesized to stand in for the failure.
    has_result: bool = False
    #: Why it ended this way, when that is not "it finished".
    reason: Optional[str] = None
    samples: List[SampleOutcome] = Field(default_factory=list)
    #: This task's own spend. Self-only: a task that spawned children does not see their spend
    #: here, which is what `usage` exists to make sayable.
    billed_cost: float = 0.0
    nominal_cost: float = 0.0
    #: The whole picture, in one place. `billed_cost`/`nominal_cost` are its `self_*` half and
    #: are kept because `task_outcome.json` files in the tree carry them; a parent that runs
    #: children fills in the nested half.
    usage: UsageBreakdown = Field(default_factory=UsageBreakdown)
    turns: int = 0
    wall_seconds: float = 0.0

    @classmethod
    def from_samples(
        cls,
        *,
        task_id: str,
        task_type: str,
        global_index: str,
        samples: Dict[int, "Sample"],
        max_retries: int,
        max_turns: int,
        sample_max_cost: Optional[float],
        has_result: bool,
    ) -> "TaskOutcome":
        """Project the persisted sample records into one execution record."""

        sample_outcomes: List[SampleOutcome] = []
        for index in sorted(samples):
            sample = samples[index]
            attempts = [
                AttemptOutcome(
                    attempt_id=attempt.attempt_id,
                    status=attempt.status,
                    billed_cost=float(attempt.cached_cost or attempt.cost),
                    nominal_cost=float(attempt.cost),
                    turns=attempt.turns,
                    error=getattr(attempt, "error", None),
                    path=str(attempt.path) if getattr(attempt, "path", None) else None,
                    started_at=attempt.started_at,
                    completed_at=attempt.completed_at,
                )
                for attempt in sample.attempts
            ]
            sample_outcomes.append(SampleOutcome(
                sample_index=sample.sample_index,
                status=sample.status,
                attempts=attempts,
                billed_cost=sample.get_accumulated_cached_cost(),
                nominal_cost=sample.get_accumulated_cost(),
                resumable=sample.can_execute(max_retries, max_turns, sample_max_cost),
            ))

        # Precedence is deliberate: a task with any resumable sample is paused rather than
        # failed, because calling it failed is what discards the record of its spend.
        statuses = {item.status for item in sample_outcomes}
        if any(item.resumable for item in sample_outcomes):
            execution_status = TaskExecutionStatus.PAUSED
        elif has_result or statuses == {ExecutionStatus.SUCCESS}:
            execution_status = TaskExecutionStatus.COMPLETED
        else:
            execution_status = TaskExecutionStatus.FAILED

        reason = None
        if execution_status is not TaskExecutionStatus.COMPLETED:
            reason = ", ".join(sorted(item.status.value for item in sample_outcomes)) or None

        wall = 0.0
        for item in sample_outcomes:
            for attempt in item.attempts:
                if attempt.started_at and attempt.completed_at:
                    wall += (attempt.completed_at - attempt.started_at).total_seconds()

        return cls(
            task_id=task_id,
            task_type=task_type,
            global_index=global_index,
            execution_status=execution_status,
            has_result=has_result,
            reason=reason,
            samples=sample_outcomes,
            billed_cost=sum(item.billed_cost for item in sample_outcomes),
            nominal_cost=sum(item.nominal_cost for item in sample_outcomes),
            usage=UsageBreakdown.of_self(
                billed=sum(item.billed_cost for item in sample_outcomes),
                nominal=sum(item.nominal_cost for item in sample_outcomes)),
            turns=sum(a.turns for item in sample_outcomes for a in item.attempts),
            wall_seconds=wall,
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
