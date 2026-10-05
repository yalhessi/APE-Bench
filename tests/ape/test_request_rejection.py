"""A request that cannot succeed as sent is not retried.

`probe_postcutoff_gpt5{4,5}_Gr_rep1` (2026-09-30) were rejected with HTTP 400 on every call --
Chat Completions refuses tools with a reasoning effort on gpt-5.4 and gpt-5.5 -- and the client
retried each 27 and 25 times in ten minutes, billing nothing, until the runs were stopped by
hand. The bodies under `fixtures/openai/` are the real responses, recorded 2026-09-30.

These drive the real `LLMClient` against an `httpx.MockTransport`, so the retry loop, the
exception wrapping and the provider's error parsing are all the production path.
"""

import asyncio
import json
import os
from pathlib import Path
from unittest import mock

import httpx
import pytest

from ape.llm_clients.client import LLMClient
from ape.llm_clients.config import LLMConfig, ProviderError, RequestRejectedError
from ape.llm_clients.models import ContentBlock, ConversationSession

FIXTURES = Path(__file__).parent / "fixtures" / "openai"
TOOL = {"type": "function", "function": {"name": "f", "parameters": {"type": "object"}}}


def fixture(name):
    return json.loads((FIXTURES / name).read_text())


@pytest.fixture(autouse=True)
def keys():
    with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test", "ELM_API_KEY": "elm-test"}):
        yield


@pytest.fixture
def no_backoff(monkeypatch):
    """tenacity sleeps through `asyncio.sleep`; a retried call must not wait out real backoff."""

    real_sleep = asyncio.sleep

    async def instant(_seconds, *args, **kwargs):
        await real_sleep(0)

    monkeypatch.setattr(asyncio, "sleep", instant)


def call(config, status, body, *, stream=False, tools=(TOOL,)):
    """Run one `call_api` against a transport that always answers `status, body`."""

    requests = []

    def answer(request):
        requests.append(request)
        return httpx.Response(status, json=body)

    async def go():
        client = LLMClient(config, enable_raw_logging=False)
        client.provider._session = httpx.AsyncClient(transport=httpx.MockTransport(answer))
        session = ConversationSession(session_id="rejection-test")
        session.add_user_message([ContentBlock.text_block("hi")], cwd="/")
        try:
            return await client.call_api(session, tools=list(tools), streaming=stream)
        finally:
            await client.close()

    try:
        asyncio.run(go())
    except Exception as error:  # noqa: BLE001 - the test inspects it
        return error, requests
    return None, requests


def config(model="gpt_5.4", **overrides):
    """An OpenAI model on the one path it may take: Responses, reasoning carried."""

    if model.startswith(("gpt_", "elm_gpt_")):
        overrides.setdefault("openai_api", "responses")
        if overrides["openai_api"] == "responses":
            overrides.setdefault("openai_responses_reasoning_carryover", True)
    return LLMConfig(model_name=model, retry_max_attempts=3, **overrides)


@pytest.mark.parametrize("stream", [False, True])
def test_a_400_naming_a_parameter_is_sent_once(stream):
    error, requests = call(config(), 400, fixture("chat_400_tools_with_reasoning_gpt54.json"),
                           stream=stream)

    assert isinstance(error, RequestRejectedError)
    assert len(requests) == 1
    assert "'reasoning_effort'" in str(error)
    assert "use /v1/responses" in str(error), "the provider's own remedy must reach the log"


def test_every_parameter_rejection_recorded_is_caught():
    for name in ("chat_400_unsupported_value_gpt52.json",
                 "responses_400_temperature_with_reasoning.json"):
        error, requests = call(config(), 400, fixture(name))
        assert isinstance(error, RequestRejectedError), name
        assert len(requests) == 1, name


def test_a_400_naming_no_parameter_is_still_retried(no_backoff):
    """The judge's "Could not finish the message because max_tokens or model output limit was
    reached" 400 succeeded on retry (pr_review_v4_judge_r0pinned_rep1, 2026-08-05)."""

    body = {"error": {"message": "Could not finish the message because max_tokens or model "
                                 "output limit was reached. Please try again with higher "
                                 "max_tokens.", "type": "invalid_request_error", "param": None,
                      "code": None}}
    error, requests = call(config(), 400, body)

    assert isinstance(error, ProviderError) and not isinstance(error, RequestRejectedError)
    assert len(requests) == 3


def test_a_server_error_is_still_retried(no_backoff):
    error, requests = call(config(), 500, {"error": {"message": "boom", "param": "x"}})

    assert not isinstance(error, RequestRejectedError)
    assert len(requests) == 3


@pytest.mark.parametrize("model,overrides", [
    ("elm_llama_3.3", {}),                              # tools on a model served without them
    ("elm_qwen_3.5", {"reasoning_effort": "low"}),      # an effort the gateway refuses
])
def test_a_provider_refusal_before_sending_is_not_retried(model, overrides):
    """These refusals were raised inside the retried call as plain `ProviderError`, so each
    was repeated a hundred times with backoff before the attempt failed."""

    error, requests = call(config(model, **overrides), 200, {})

    assert isinstance(error, RequestRejectedError)
    assert requests == []


# --- an OpenAI model's reasoning is never dropped between turns ---------------------------
#
# `reasoning_drop_refusal` is the one check, used by both OpenAI providers before sending and by
# `cli plan` before any spend. Chat Completions returns no reasoning to carry; Responses with
# carry-over off drops it. Either is refused for an OpenAI model, direct or through ELM.

OPENAI_MODELS = ["gpt_5.2", "gpt_5.4", "gpt_5.5", "gpt_5_mini",
                 "elm_gpt_5.2", "elm_gpt_5.4", "elm_gpt_5.5", "elm_gpt_5_mini"]


@pytest.mark.parametrize("model", OPENAI_MODELS)
@pytest.mark.parametrize("effort,tools", [("high", (TOOL,)), ("none", (TOOL,)), (None, ())])
def test_an_openai_model_on_chat_completions_is_refused_unsent(model, effort, tools):
    """Whatever the effort and whether or not tools are sent: gpt-5.2 accepted tools with
    reasoning there, and its reasoning was still dropped every turn."""

    error, requests = call(config(model, openai_api="chat_completions", reasoning_effort=effort),
                           200, {}, tools=tools)
    assert isinstance(error, RequestRejectedError)
    assert requests == []
    assert "openai_api: responses" in str(error)


@pytest.mark.parametrize("model", OPENAI_MODELS)
def test_an_openai_model_on_responses_without_carryover_is_refused_unsent(model):
    error, requests = call(config(model, openai_responses_reasoning_carryover=False), 200, {})
    assert isinstance(error, RequestRejectedError)
    assert requests == []
    assert "openai_responses_reasoning_carryover: true" in str(error)


def test_an_openai_model_with_its_reasoning_carried_is_sent():
    from ape.llm_clients.providers.openai_provider import reasoning_drop_refusal

    ok = {"output": [{"type": "message", "role": "assistant",
                      "content": [{"type": "output_text", "text": "hi"}]}],
          "status": "completed", "usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2}}
    for model in OPENAI_MODELS:
        assert reasoning_drop_refusal(config(model, reasoning_effort="high")) is None, model
        error, requests = call(config(model, reasoning_effort="high"), 200, ok)
        assert error is None and len(requests) == 1, model


def test_a_model_that_is_not_openai_keeps_chat_completions():
    ok = {"choices": [{"message": {"role": "assistant", "content": "hi"}}],
          "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}}
    error, requests = call(config("elm_mistral_small_4", reasoning_effort="high"), 200, ok)
    assert error is None and len(requests) == 1
    assert "messages" in json.loads(requests[0].content)


def test_every_elm_row_serving_a_gpt_model_is_marked():
    """The mark is how the check knows a row is an OpenAI model; an unmarked ELM `gpt-` row
    would slip back onto Chat Completions."""

    from ape.llm_clients.config import MODEL_MAPPINGS, LLMProvider

    unmarked = [name for name, row in MODEL_MAPPINGS.items()
                if row["provider"] is LLMProvider.ELM and row["model_name"].startswith("gpt-")
                and not row.get("openai_responses")]
    assert unmarked == []


def test_cli_plan_refuses_the_run_before_building_anything():
    """Every review task sends tools, so the run could not make one call. The refusal comes
    before the agenda build, which is the slow part of a plan."""

    from src.mathlib_review.review.runner import load_run, run

    dataset, scaffold, overrides = load_run(
        Path("configs/pr_review_v5_specialist4.yaml"),
        {"llm_config": {"model_name": "gpt_5.4", "reasoning_effort": "high",
                        "openai_api": "chat_completions"}})
    dataset.dry_run = True
    quiet = mock.Mock()
    with mock.patch("src.mathlib_review.review.runner.load_release",
                    side_effect=AssertionError("reached the agenda build")):
        with pytest.raises(ValueError, match="openai_api: responses"):
            asyncio.run(run(dataset, scaffold, overrides, quiet))
