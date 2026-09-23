"""The ceiling that survives a price of zero.

Every budget in this codebase is denominated in dollars, and the four locally hosted `elm_*`
models are priced `0.0` because that is what they cost. `standard_budget_cap`, `lead_cost_cap`,
`per_pr_cost_cap` and `run_total_cost_cap` are therefore all satisfied by any run whatsoever on
one of them, and before `ExecutionLimits.token_limit` a lead on `elm_qwen_3.5` could delegate
`max_delegations` jobs of `max_turns` turns each with nothing in the run plan bounding it.

What these tests pin is that the token ceiling is the *same* mechanism as the dollar one rather
than a second one beside it -- another field on `ExecutionLimits`, read by the same
`task_execution_limits`, enforced at the same checkpoint, resumed by the same rule -- and that
it counts the one thing a cache discount cannot move.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from types import SimpleNamespace

import pytest

from ape.llm_clients.config import CostExhaustedError, TokenBudgetExhaustedError
from ape.llm_clients.models import TokenUsage
from ape.orchestration.models import (
    EXECUTION_LIMITS_KEY,
    Attempt,
    ExecutionStatus,
    Sample,
    TaskExecutionSpec,
    TaskOutcome,
    UsageBreakdown,
    execution_limits_payload,
    task_execution_limits,
)
from ape.scaffolds.base import ScaffoldTerminationReason


# --- what gets counted -------------------------------------------------------------------


def test_processed_tokens_is_not_discounted_for_caching():
    """The dollar ceiling reads `cached_total_cost` because that is what was paid. The token
    ceiling must not have a cache-shaped equivalent: a cached prompt token is still a token
    the model read, and the models this ceiling exists for report no cache at all."""

    cached = TokenUsage(input_tokens=100_000, output_tokens=1_000,
                        total_tokens=101_000, cache_read_input_tokens=90_000)
    uncached = TokenUsage(input_tokens=100_000, output_tokens=1_000, total_tokens=101_000)
    assert cached.processed_tokens == uncached.processed_tokens == 101_000


def test_processed_tokens_falls_back_when_a_provider_omits_the_total():
    """`parse_usage` defaults a missing `total_tokens` to 0, not None, so `model_post_init`
    never backfills it -- and a ceiling that reads zero is a ceiling that never binds."""

    assert TokenUsage(input_tokens=10, output_tokens=2, total_tokens=0).processed_tokens == 12
    assert TokenUsage(input_tokens=10, output_tokens=2).processed_tokens == 12


# --- the limit travels the way the cost limit does ----------------------------------------


def test_a_task_may_carry_a_token_ceiling_of_its_own():
    execution = SimpleNamespace(max_turns=40, sample_max_cost=0.30, sample_max_tokens=360_000)
    limits = task_execution_limits(
        {EXECUTION_LIMITS_KEY: {"token_limit": 120_000}}, execution)
    assert limits.token_limit == 120_000
    assert limits.billed_cost_limit == 0.30


def test_a_task_without_an_override_gets_the_orchestrator_token_ceiling():
    execution = SimpleNamespace(max_turns=40, sample_max_cost=0.30, sample_max_tokens=360_000)
    assert task_execution_limits({}, execution).token_limit == 360_000


def test_an_execution_config_without_the_field_is_read_as_no_ceiling():
    """`task_execution_limits` is called with duck-typed execution objects in three places,
    and one that predates the field must not raise."""

    execution = SimpleNamespace(max_turns=40, sample_max_cost=0.30)
    assert task_execution_limits({}, execution).token_limit is None


def test_a_malformed_token_ceiling_falls_back_rather_than_failing_the_run():
    execution = SimpleNamespace(max_turns=40, sample_max_cost=0.30, sample_max_tokens=360_000)
    limits = task_execution_limits(
        {EXECUTION_LIMITS_KEY: {"token_limit": "plenty"}}, execution)
    assert limits.token_limit == 360_000


def test_zero_means_no_ceiling_rather_than_a_ceiling_of_zero():
    """A config disables a cap with 0. `task_execution_limits` reads a key's *absence* as
    "use the orchestrator's value", so writing `token_limit: 0` would pin the ceiling at zero
    and stop the task before its first turn."""

    assert execution_limits_payload(token_limit=0) == {}
    assert execution_limits_payload(billed_cost_limit=0.0) == {}
    assert execution_limits_payload(token_limit=360_000) == {"token_limit": 360_000}


def test_a_spec_carries_its_token_ceiling_into_the_task_data():
    spec = TaskExecutionSpec(spec_id="s", task_type="t", task_data={"task_type": "t"},
                             billed_cost_limit=0.30, token_limit=360_000)
    assert spec.with_limits()[EXECUTION_LIMITS_KEY] == {
        "billed_cost_limit": 0.30, "token_limit": 360_000}


# --- stopping, and saying so --------------------------------------------------------------


def test_the_token_stop_has_its_own_reason_all_the_way_to_the_sample_status():
    """"Paused on budget" without saying which budget is not actionable: on a zero-priced
    model the cost ceiling cannot fire, so the two are never interchangeable."""

    from ape.orchestration.worker import SampleWorker

    mapped = SampleWorker._map_status(
        SimpleNamespace(), ScaffoldTerminationReason.TOKENS_EXHAUSTED)
    assert mapped is ExecutionStatus.PAUSED_TOKEN_LIMIT
    assert mapped.is_paused()
    assert not mapped.is_terminal()


def test_the_scaffold_maps_the_token_error_to_its_own_termination_reason():
    """`TokenBudgetExhaustedError` must not fall through to ERROR, which is retryable: the
    ceiling is exhausted and a retry would exhaust it again."""

    import inspect

    from ape.scaffolds.base import BaseScaffold

    source = inspect.getsource(BaseScaffold.solve)
    assert "TokenBudgetExhaustedError" in source
    assert "TOKENS_EXHAUSTED" in source
    # Not the same class, so an `except CostExhaustedError` cannot swallow it silently.
    assert not issubclass(TokenBudgetExhaustedError, CostExhaustedError)


def _attempt(tokens: int, status: ExecutionStatus, attempt_id: int = 1) -> Attempt:
    return Attempt(attempt_id=attempt_id, path="/tmp/x", status=status,
                   created_at=datetime.now(), tokens=tokens, max_turns=40,
                   cost_limit=0.30, token_limit=360_000)


def _sample(*attempts: Attempt) -> Sample:
    now = datetime.now()
    return Sample(sample_id="s_0", sample_index=0, task_global_index="s",
                  attempts=list(attempts), created_at=now, updated_at=now)


def test_a_token_paused_sample_resumes_only_if_the_ceiling_was_raised():
    sample = _sample(_attempt(360_000, ExecutionStatus.PAUSED_TOKEN_LIMIT))
    assert not sample.can_execute(3, 40, 0.30, sample_max_tokens=360_000)
    assert sample.can_execute(3, 40, 0.30, sample_max_tokens=500_000)


def test_resumption_charges_every_attempt_not_just_the_last():
    """The cost branch's lesson: charging only the last attempt lets a sample resume forever,
    each attempt under the ceiling on its own."""

    sample = _sample(_attempt(200_000, ExecutionStatus.PAUSED_TOKEN_LIMIT, 1),
                     _attempt(200_000, ExecutionStatus.PAUSED_TOKEN_LIMIT, 2))
    assert sample.get_accumulated_tokens() == 400_000
    assert not sample.can_execute(3, 40, 0.30, sample_max_tokens=360_000)


def test_an_outcome_reports_the_tokens_its_samples_processed():
    sample = _sample(_attempt(120_000, ExecutionStatus.SUCCESS))
    outcome = TaskOutcome.from_samples(
        task_id="t", task_type="tt", global_index="g", samples={0: sample},
        max_retries=3, max_turns=40, sample_max_cost=0.30, has_result=True,
        sample_max_tokens=360_000)
    assert outcome.tokens == 120_000
    assert outcome.samples[0].tokens == 120_000
    assert outcome.samples[0].attempts[0].tokens == 120_000
    assert outcome.usage.self_tokens == 120_000


def test_usage_keeps_self_and_nested_tokens_apart():
    """Costs bubble from children to parents and token counts do not, so a lead's recorded
    `token_usage` held its children's dollars and only its own tokens -- read as recorded,
    leads came out at 107,528 tokens/$ against their arms' 1,241,326."""

    usage = UsageBreakdown.of_self(billed=0.08, nominal=0.14, tokens=65_471)
    usage = usage.with_nested(billed=0.89, nominal=2.40, tokens=900_000)
    assert usage.self_tokens == 65_471
    assert usage.nested_tokens == 900_000
    assert usage.tokens == 965_471
    assert usage.summary()["tokens"] == 965_471


def test_the_delegation_ledger_separates_a_token_stop_from_a_cost_stop():
    """The ledger's job is to separate "declined" from "cut off"; on a zero-priced model
    every cut-off is a token one and mapping it to `failed` would erase that."""

    from ape.tasks.lean_tasks.formal_math.review.delegation import _LEDGER_STATUS

    assert _LEDGER_STATUS[ExecutionStatus.PAUSED_TOKEN_LIMIT] == "paused_tokens"
    assert _LEDGER_STATUS[ExecutionStatus.PAUSED_COST_LIMIT] == "paused_cost"


def test_an_unbooked_attempt_includes_the_token_pause():
    """A token-paused attempt on a zero-priced model spent no money and is just as unbooked:
    it consumed the run's budget and wrote no result."""

    from src.mathlib_review.analysis.corrections import _UNBOOKED

    assert "paused_token_limit" in _UNBOOKED


# --- the checkpoint itself ----------------------------------------------------------------


class _Relay:
    """The relay's limit checkpoint, with only what it reads."""

    def __init__(self, usage: TokenUsage, **limits):
        from ape.scaffolds.utils.base_relay import BaseRelaySession

        self._check = BaseRelaySession._check_limits_and_shutdown_if_needed.__get__(self)
        self._usage = usage
        self._server = None
        self.last_error = None
        self.max_turns = limits.get("max_turns")
        self.cost_limit = limits.get("cost_limit")
        self.token_limit = limits.get("token_limit")
        self.logger = SimpleNamespace(warning=lambda *a, **k: None)

    def get_current_turns(self):
        return 0

    def get_token_usage(self):
        return self._usage


@pytest.mark.parametrize("tokens,limit,stopped", [
    (359_999, 360_000, False),
    (360_000, 360_000, True),
    (400_000, 360_000, True),
])
def test_the_relay_stops_at_the_token_ceiling(tokens, limit, stopped):
    """Both scaffold families check both ceilings, so a run cannot acquire a limit that binds
    under `ape_agent` and is silently absent under `claude_code`."""

    relay = _Relay(TokenUsage(input_tokens=tokens, output_tokens=0, total_tokens=tokens),
                   token_limit=limit)
    response = asyncio.run(relay._check())
    assert (response is not None) is stopped
    if stopped:
        assert isinstance(relay.last_error, TokenBudgetExhaustedError)


def test_the_relay_leaves_a_free_model_alone_when_no_token_ceiling_is_set():
    relay = _Relay(TokenUsage(input_tokens=10_000_000, output_tokens=0,
                              total_tokens=10_000_000, cached_total_cost=0.0),
                   cost_limit=0.30)
    assert asyncio.run(relay._check()) is None


def test_the_agent_loop_checks_tokens_beside_cost_off_the_same_records():
    """Both ceilings read `self._conversation_usage` at the same point in the same loop --
    one mechanism with two denominations, not two limiters."""

    import inspect

    from ape.scaffolds.ape_agent.conversation import ApeAgentConversationManager

    source = inspect.getsource(ApeAgentConversationManager.run_conversation)
    assert "self.token_limit is not None" in source
    assert "TokenBudgetExhaustedError" in source
    assert "u.processed_tokens for u in self._conversation_usage" in source


# --- the loop actually stops ---------------------------------------------------------------


def _manager(**limits):
    """The real conversation manager with a truthy client, so `initialize` is skipped."""

    from ape.scaffolds.ape_agent.config import ApeAgentConfig
    from ape.scaffolds.ape_agent.conversation import ApeAgentConversationManager

    config = ApeAgentConfig()
    config.execution.max_turns = limits.pop("max_turns", 100)
    manager = ApeAgentConversationManager(config=config, task=None, **limits)
    manager.llm_client = object()
    return manager


def _drive(manager, *, tokens_per_turn: int, billed_per_turn: float = 0.0):
    """Run the real loop with a stubbed turn, and report how many turns it took."""

    from ape.llm_clients.models import ContentBlock, ConversationSession

    session = ConversationSession()
    taken = {"turns": 0}

    async def one_turn(**_kwargs):
        taken["turns"] += 1
        usage = TokenUsage(input_tokens=tokens_per_turn - 1, output_tokens=1,
                           total_tokens=tokens_per_turn,
                           cached_total_cost=billed_per_turn,
                           total_cost=billed_per_turn)
        session.add_assistant_message(
            content_blocks=[ContentBlock.text_block("...")], usage=usage, cwd=".")
        manager._conversation_usage.append(usage)

    manager._single_turn = one_turn
    asyncio.run(manager.run_conversation(prompt="go", session=session, mcp_instance=None))
    return taken["turns"]


def test_a_conversation_that_costs_nothing_still_stops():
    """The hole, closed. On a model priced 0.0 the billed figure never moves, so the cost
    ceiling can never fire and `max_turns` is the only other bound -- 100 turns here."""

    manager = _manager(token_limit=250_000, cost_limit=0.30, max_turns=100)
    with pytest.raises(TokenBudgetExhaustedError) as caught:
        _drive(manager, tokens_per_turn=101_000, billed_per_turn=0.0)
    assert "303,000 >= 250,000" in str(caught.value)


def test_without_a_token_ceiling_a_free_conversation_runs_to_max_turns():
    """The same conversation with only the dollar ceiling: it is what the todo describes, and
    it is why `token_limit` had to exist rather than the caps being retuned."""

    from ape.scaffolds.base import MaxTurnsReachedError

    manager = _manager(cost_limit=0.30, max_turns=8)
    with pytest.raises(MaxTurnsReachedError):
        _drive(manager, tokens_per_turn=101_000, billed_per_turn=0.0)


def test_the_cost_ceiling_still_fires_first_when_it_is_the_tighter_one():
    """Two ceilings, whichever binds first. A paid model must not have its behaviour changed
    by a token ceiling set loosely beside a dollar one."""

    manager = _manager(token_limit=10_000_000, cost_limit=0.10, max_turns=100)
    with pytest.raises(CostExhaustedError):
        _drive(manager, tokens_per_turn=1_000, billed_per_turn=0.04)
