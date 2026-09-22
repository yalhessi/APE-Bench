"""Routing, pricing and tool capability for the Edinburgh ELM gateway.

Every wire-level fact asserted here was measured against the live endpoint on 2026-09-22;
the probe output is quoted in `ElmProvider`'s module docstring. These tests pin the parts
that live in this repository -- which provider class handles ELM, which endpoint and header
it uses, which model ids it sends, and which models it refuses to send tools to.
"""

import os
from unittest import mock

import pytest

from ape.llm_clients.client import LLMClient
from ape.llm_clients.config import (
    MODEL_MAPPINGS,
    LLMConfig,
    LLMProvider,
    ProviderError,
)
from ape.llm_clients.providers import BaseProvider, ElmProvider, OpenAIProvider

ELM_MODELS = sorted(k for k, v in MODEL_MAPPINGS.items() if v["provider"] is LLMProvider.ELM)
TOOL = {"type": "function", "function": {"name": "f", "parameters": {"type": "object"}}}


@pytest.fixture(autouse=True)
def elm_key():
    with mock.patch.dict(os.environ, {"ELM_API_KEY": "elm-test-key"}, clear=False):
        yield "elm-test-key"


def client_for(model: str) -> LLMClient:
    return LLMClient(LLMConfig(model_name=model), enable_raw_logging=False)


def test_the_table_is_not_empty():
    assert ELM_MODELS, "no ELM models registered; the rest of this file would vacuously pass"


@pytest.mark.parametrize("model", ELM_MODELS)
def test_every_elm_model_routes_to_the_elm_provider(model):
    """Never `BaseProvider`: that path puts the key in the query string and has no endpoint."""

    provider = client_for(model).provider
    assert isinstance(provider, ElmProvider)
    assert not isinstance(provider, BaseProvider) or isinstance(provider, OpenAIProvider)


@pytest.mark.parametrize("model", ELM_MODELS)
def test_every_elm_model_posts_to_the_gateway_with_a_bearer_header(model, elm_key):
    url, headers = client_for(model).provider.get_request_info("session")

    assert url == "https://elm.edina.ac.uk/api/v1/chat/completions"
    assert headers["Authorization"] == f"Bearer {elm_key}"
    assert elm_key not in url, "the key must never travel in the query string"


@pytest.mark.parametrize("model", ELM_MODELS)
def test_every_elm_model_resolves_its_key_from_elm_api_key(model, elm_key):
    assert LLMConfig(model_name=model).api_key == elm_key


def test_the_openai_key_is_not_accepted_for_elm():
    """The two keys coexist in one shell; neither may stand in for the other."""

    with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-not-elm"}, clear=True):
        assert LLMConfig(model_name="elm_gpt_5.2").api_key is None
        assert LLMConfig(model_name="gpt_5_mini").api_key == "sk-not-elm"


def test_elm_sends_the_bare_alias_not_the_dated_snapshot():
    """ELM publishes no dated snapshots; `gpt-5-mini-2025-08-07` would be rejected."""

    assert LLMConfig(model_name="elm_gpt_5_mini").formal_model_name == "gpt-5-mini"
    assert LLMConfig(model_name="gpt_5_mini").formal_model_name == "gpt-5-mini-2025-08-07"


def test_base_url_can_be_overridden_per_run():
    config = LLMConfig(model_name="elm_gpt_5.2", base_url="https://example.invalid/v1/chat")
    url, _ = ElmProvider(config).get_request_info("s")
    assert url == "https://example.invalid/v1/chat"


def test_direct_openai_models_are_untouched():
    provider = client_for("gpt_5_mini").provider
    assert isinstance(provider, OpenAIProvider) and not isinstance(provider, ElmProvider)
    assert provider.DEFAULT_BASE_URL == "https://api.openai.com/v1/chat/completions"


# --------------------------------------------------------------------------------------
# payload: measured against the live gateway, so these pin what it accepts
# --------------------------------------------------------------------------------------

def test_the_payload_uses_max_completion_tokens():
    """ELM's OpenAI models reject `max_tokens` outright ("not supported with this model")."""

    payload = client_for("elm_gpt_5.2").provider.build_request_payload([], stream=False)
    assert payload["max_completion_tokens"]
    assert "max_tokens" not in payload


def test_streaming_asks_for_usage():
    """Without this the streamed response carries no usage and billed cost reads zero."""

    payload = client_for("elm_gpt_5.2").provider.build_request_payload([], stream=True)
    assert payload["stream_options"] == {"include_usage": True}


@pytest.mark.parametrize("model", ["elm_gpt_5.2", "elm_qwen_3.5", "elm_mistral_small_4"])
def test_tool_capable_models_pass_tools_through(model):
    payload = client_for(model).provider.build_request_payload([], tools=[TOOL])
    assert payload["tools"] == [TOOL]


@pytest.mark.parametrize("model", ["elm_llama_3.3", "elm_eurollm_22b"])
def test_tool_incapable_models_are_refused_by_name(model):
    """ELM runs these on vLLM without --enable-auto-tool-choice; the raw failure is a 400
    on the first call of every task, which is expensive to diagnose once per run."""

    provider = client_for(model).provider
    assert provider.supports_tools() is False

    with pytest.raises(ProviderError, match="without tool-calling enabled"):
        provider.build_request_payload([], tools=[TOOL])

    # ...but the same model is fine for a scaffold that sends none.
    assert "tools" not in provider.build_request_payload([])


# --------------------------------------------------------------------------------------
# pricing
# --------------------------------------------------------------------------------------

def test_shared_formal_names_price_from_their_own_row():
    """`gpt_5.4` and `elm_gpt_5.4` both send `gpt-5.4`; a formal-name scan cannot tell them
    apart, and would price whichever was declared first."""

    assert (LLMConfig(model_name="gpt_5.4").formal_model_name
            == LLMConfig(model_name="elm_gpt_5.4").formal_model_name == "gpt-5.4")

    for canonical in ("gpt_5.4", "elm_gpt_5.4"):
        entry = BaseProvider(LLMConfig(model_name=canonical))._pricing_entry()
        assert entry is MODEL_MAPPINGS[canonical]


@pytest.mark.parametrize("model", ELM_MODELS)
def test_every_elm_model_can_be_priced(model):
    """`_calculate_cost` raises on an unpriced model, on every call, at usage-parse time."""

    nominal, billed = BaseProvider(LLMConfig(model_name=model))._calculate_cost(1000, 100)
    assert nominal >= 0 and billed >= 0


def test_locally_hosted_models_are_priced_at_zero_and_that_is_deliberate():
    """A fictional rate here would make every reported cost a mix of money and metaphor.
    The consequence -- that the dollar caps are vacuous for these models -- is the subject
    of docs/todo/token-based-execution-limits.md, and is not fixed by pretending."""

    for model in ("elm_qwen_3.5", "elm_mistral_small_4", "elm_llama_3.3", "elm_eurollm_22b"):
        entry = MODEL_MAPPINGS[model]
        assert entry["input_per_1M"] == 0.0 and entry["output_per_1M"] == 0.0
        assert BaseProvider(LLMConfig(model_name=model))._calculate_cost(10**6, 10**6) == (0.0, 0.0)


def test_local_model_usage_without_cache_details_parses():
    """Every locally hosted model returns `prompt_tokens_details: null`."""

    usage = BaseProvider(LLMConfig(model_name="elm_llama_3.3")).parse_usage(
        {"prompt_tokens": 42, "total_tokens": 44, "completion_tokens": 2,
         "prompt_tokens_details": None})

    assert (usage.input_tokens, usage.output_tokens) == (42, 2)
    assert usage.cache_read_input_tokens is None


# --- reasoning effort ----------------------------------------------------------------------
#
# Measured on the live gateway 2026-09-22, 3 samples per cell, completion tokens on one
# arithmetic prompt:
#
#     elm_qwen_3.5          none 4    absent 451   high 395    low/medium: HTTP 400
#     elm_mistral_small_4   none 4    absent 4     high 143    low/medium: HTTP 400
#     elm_llama_3.3         2 in every cell, every value accepted
#     elm_eurollm_22b       4 in every cell, every value accepted
#
# The two agent-capable models have OPPOSITE defaults, which is why this cannot be left to
# the endpoint: a token ceiling calibrated under one is meaningless under the other.


def test_nothing_is_sent_when_no_effort_is_stated():
    """Absent means the provider's default, which is what every run before the field did."""

    payload = client_for("elm_qwen_3.5").provider.build_request_payload([])
    assert "reasoning_effort" not in payload


def test_a_stated_effort_reaches_the_payload():
    config = LLMConfig(model_name="elm_qwen_3.5", reasoning_effort="none")
    payload = OpenAIProvider(config).build_request_payload([])
    assert payload["reasoning_effort"] == "none"


@pytest.mark.parametrize("model,effort", [
    ("elm_qwen_3.5", "none"), ("elm_qwen_3.5", "high"),
    ("elm_mistral_small_4", "none"), ("elm_mistral_small_4", "high"),
])
def test_a_measured_effort_is_sent(model, effort):
    config = LLMConfig(model_name=model, reasoning_effort=effort)
    assert ElmProvider(config).build_request_payload([])["reasoning_effort"] == effort


@pytest.mark.parametrize("model,effort", [
    ("elm_qwen_3.5", "low"), ("elm_qwen_3.5", "medium"),
    ("elm_mistral_small_4", "low"), ("elm_mistral_small_4", "medium"),
])
def test_an_effort_the_gateway_refuses_is_named_here_instead(model, effort):
    """A raw 400 on the first call of every task, once per run, is how this was discovered."""

    config = LLMConfig(model_name=model, reasoning_effort=effort)
    with pytest.raises(ProviderError, match="not honoured"):
        ElmProvider(config).build_request_payload([])


@pytest.mark.parametrize("model", ["elm_llama_3.3", "elm_eurollm_22b"])
@pytest.mark.parametrize("effort", ["none", "low", "medium", "high"])
def test_a_model_with_no_reasoning_mode_refuses_the_knob(model, effort):
    """These ACCEPT every value and honour none -- 200 with nothing changed. A knob the run
    plan records and the endpoint ignores is worse than one that is refused."""

    config = LLMConfig(model_name=model, reasoning_effort=effort)
    with pytest.raises(ProviderError, match="no reasoning mode"):
        ElmProvider(config).build_request_payload([])


def test_an_unmeasured_model_passes_the_knob_through():
    """An untested model cannot be asserted to lack a reasoning mode. The OpenAI models
    proxied by ELM carry no measured row, so nothing here may refuse them."""

    config = LLMConfig(model_name="elm_gpt_5.2", reasoning_effort="high")
    assert ElmProvider(config).build_request_payload([])["reasoning_effort"] == "high"


def test_the_reasoning_table_covers_every_open_weight_model():
    """A model added without a row would silently gain an unchecked knob."""

    for model in ("elm_qwen_3.5", "elm_mistral_small_4", "elm_llama_3.3", "elm_eurollm_22b"):
        assert "reasoning_efforts" in MODEL_MAPPINGS[model], model


def test_reasoning_effort_is_inside_the_provenance_hash():
    """It moves token consumption ~100x, so two runs that differ in it are different
    experiments. `scaffold_config_sha256` hashes the llm_config dump, so the field has to
    survive serialization -- unlike `api_key`, which is deliberately excluded."""

    dumped = LLMConfig(model_name="elm_qwen_3.5", reasoning_effort="none").model_dump(
        mode="json")
    assert dumped["reasoning_effort"] == "none"
