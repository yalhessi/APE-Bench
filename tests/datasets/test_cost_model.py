"""How a call is priced, and the one question the two cost models disagree about.

Is `cache_read_input_tokens` a **subset of** `prompt_tokens`, or **disjoint from** it?

`prompt_exclusive` — the original APE assumption — says disjoint, and adds them. If cached
tokens are in fact part of the prompt count, that charges them twice: once at full rate
inside `input_tokens`, and again at the cache rate. Both returned figures inflate, not just
the nominal one.

The evidence for `prompt_inclusive` is this repo's own logs, and it is pinned below as a
regression fixture: a real 9-turn lead conversation whose recorded figures reproduce exactly
under the legacy model, so switching between them is lossless in both directions.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from ape.llm_clients.config import COST_MODELS, DEFAULT_COST_MODEL, LLMConfig
from ape.llm_clients.providers.base import BaseProvider

GPT52 = "gpt-5.2-2025-12-11"
IN_PER_M, OUT_PER_M, CACHED_PER_M = 1.75, 14.0, 0.125

#: A real conversation: the PR 33066 lead from the rep5 smoke run, 9 turns, terminated at a
#: $1.00 cap. Recorded by the framework as $1.16441 nominal / $0.69995 billed.
FIXTURE = {"input": 328_601, "cached": 285_824, "output": 6_369}
RECORDED_NOMINAL, RECORDED_BILLED = 1.16440975, 0.69994575


class _Provider(BaseProvider):
    def __init__(self, cost_model=DEFAULT_COST_MODEL, model=GPT52):
        self.config = SimpleNamespace(formal_model_name=model, cost_model=cost_model)

    def build_request_payload(self, *a, **k): ...
    async def make_request(self, *a, **k): ...
    async def make_streaming_request(self, *a, **k): ...


def _price(cost_model, *, inp=None, cached=None, out=None, creation=0):
    return _Provider(cost_model)._calculate_cost(
        FIXTURE["input"] if inp is None else inp,
        FIXTURE["output"] if out is None else out,
        FIXTURE["cached"] if cached is None else cached,
        creation,
    )


def test_the_legacy_model_reproduces_the_recorded_figures_exactly():
    """The point of keeping it: every historical number stays reproducible."""

    nominal, billed = _price("prompt_exclusive")
    assert nominal == pytest.approx(RECORDED_NOMINAL, abs=1e-6)
    assert billed == pytest.approx(RECORDED_BILLED, abs=1e-6)


def test_the_new_model_prices_each_token_once():
    nominal, billed = _price("prompt_inclusive")
    uncached = FIXTURE["input"] - FIXTURE["cached"]
    expected = (uncached / 1e6 * IN_PER_M
                + FIXTURE["cached"] / 1e6 * CACHED_PER_M
                + FIXTURE["output"] / 1e6 * OUT_PER_M)
    assert billed == pytest.approx(expected, abs=1e-9)
    # The nominal figure is the no-cache counterfactual: the whole prompt at full rate.
    assert nominal == pytest.approx(
        FIXTURE["input"] / 1e6 * IN_PER_M + FIXTURE["output"] / 1e6 * OUT_PER_M, abs=1e-9)


def test_the_legacy_model_overcharges_by_exactly_the_cached_tokens():
    """Naming the size of the error rather than just its direction."""

    _, legacy_billed = _price("prompt_exclusive")
    _, new_billed = _price("prompt_inclusive")
    double_charged = FIXTURE["cached"] / 1e6 * IN_PER_M
    assert legacy_billed - new_billed == pytest.approx(double_charged, abs=1e-9)


def test_the_new_model_is_the_default():
    assert DEFAULT_COST_MODEL == "prompt_inclusive"
    assert LLMConfig(model_name="gpt_5.2").cost_model == "prompt_inclusive"
    assert set(COST_MODELS) == {"prompt_inclusive", "prompt_exclusive"}


def test_the_legacy_model_stays_selectable():
    assert LLMConfig(model_name="gpt_5.2",
                     cost_model="prompt_exclusive").cost_model == "prompt_exclusive"


def test_an_unknown_cost_model_is_rejected():
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        LLMConfig(model_name="gpt_5.2", cost_model="whatever_you_like")


# --------------------------------------------------------------------------------------
# degenerate inputs
# --------------------------------------------------------------------------------------

def test_with_no_cache_the_two_models_agree():
    """They only diverge on cached tokens, so a call with none must price identically."""

    assert _price("prompt_inclusive", cached=0) == _price("prompt_exclusive", cached=0)


def test_a_fully_cached_prompt_costs_almost_nothing():
    nominal, billed = _price("prompt_inclusive", inp=50_000, cached=50_000, out=0)
    assert billed == pytest.approx(50_000 / 1e6 * CACHED_PER_M, abs=1e-9)
    assert nominal > billed


def test_more_cached_than_prompt_tokens_falls_back_instead_of_going_negative():
    """A provider reporting that is not describing a subset, whatever the docs say."""

    nominal, billed = _price("prompt_inclusive", inp=1_000, cached=5_000, out=0)
    assert billed >= 0
    assert billed == pytest.approx(
        1_000 / 1e6 * IN_PER_M + 5_000 / 1e6 * CACHED_PER_M, abs=1e-9)
    assert nominal >= 0


def test_an_empty_call_is_free():
    assert _price("prompt_inclusive", inp=0, cached=0, out=0) == (0.0, 0.0)


def test_output_is_never_discounted():
    """Output tokens are not cacheable; only the input side may differ between models."""

    _, a = _price("prompt_inclusive", inp=10_000, cached=10_000, out=1_000)
    _, b = _price("prompt_inclusive", inp=10_000, cached=10_000, out=2_000)
    assert b - a == pytest.approx(1_000 / 1e6 * OUT_PER_M, abs=1e-9)


# --------------------------------------------------------------------------------------
# what the budget is enforced against
# --------------------------------------------------------------------------------------

def test_the_budget_is_enforced_on_what_was_billed():
    """The lead this fixture came from was terminated at a $1.00 cap on a counted $1.164
    having actually spent $0.200 — four fifths of its budget lost to an accounting
    convention."""

    from datetime import datetime

    from ape.orchestration.models import Attempt, ExecutionStatus, Sample

    now = datetime.now()
    sample = Sample(
        sample_id="s", sample_index=0, task_global_index="g",
        attempts=[Attempt(attempt_id=1, path="/tmp/x", status=ExecutionStatus.SUCCESS,
                          created_at=now, updated_at=now, max_turns=40, cost_limit=1.0,
                          cost=1.164, cached_cost=0.200)],
        created_at=now, updated_at=now,
    )
    assert sample.get_effective_cost() == pytest.approx(0.200)


def test_it_falls_back_when_nothing_was_cached():
    from datetime import datetime

    from ape.orchestration.models import Attempt, ExecutionStatus, Sample

    now = datetime.now()
    sample = Sample(
        sample_id="s", sample_index=0, task_global_index="g",
        attempts=[Attempt(attempt_id=1, path="/tmp/x", status=ExecutionStatus.SUCCESS,
                          created_at=now, updated_at=now, max_turns=40, cost_limit=1.0,
                          cost=0.5, cached_cost=0.0)],
        created_at=now, updated_at=now,
    )
    assert sample.get_effective_cost() == pytest.approx(0.5)
