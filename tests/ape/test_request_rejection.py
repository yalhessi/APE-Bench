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
