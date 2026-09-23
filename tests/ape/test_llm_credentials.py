"""The API key must not be serialized, and the provenance hash must not depend on it.

`LLMConfig.model_dump` feeds four consumers: the on-disk run snapshot written by
`save_orchestrator_config`, the container runtime's `--scaffold-config-json` argv, the
`scaffold_config_sha256` provenance hash, and the handoff to worker processes. Only the last
wants a credential, and it reconstructs one by re-resolving the environment.

Before this was fixed, 640 files under `.ape/runs/` across 289 runs held a live
`"api_key": "sk-..."`, and rotating a key changed the sealed plan hash of two runs that were
otherwise the same experiment.
"""

import os
from unittest import mock

import pytest

from ape.llm_clients.config import (
    PROVIDER_KEY_ENV_VARS,
    LLMConfig,
    LLMProvider,
)


@pytest.fixture
def openai_key():
    with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-aaaa"}, clear=False):
        yield "sk-test-aaaa"


def test_api_key_resolves_from_the_environment(openai_key):
    """The behaviour the exclusion must not break: the key still reaches the provider."""

    assert LLMConfig(model_name="gpt_5_mini").api_key == openai_key


def test_api_key_is_absent_from_every_dump(openai_key):
    """Not `None`, not redacted -- absent, in both dump modes and in JSON."""

    config = LLMConfig(model_name="gpt_5_mini")
    assert config.api_key == openai_key

    assert "api_key" not in config.model_dump()
    assert "api_key" not in config.model_dump(mode="json")
    assert openai_key not in config.model_dump_json()


def test_scaffold_dump_carries_no_key(openai_key):
    """The scaffold dump is what `save_orchestrator_config` writes and what gets hashed."""

    from ape.scaffolds.ape_agent.config import ApeAgentConfig

    dumped = ApeAgentConfig(llm_config=LLMConfig(model_name="gpt_5_mini")).model_dump(mode="json")
    assert "api_key" not in dumped["llm_config"]
    assert openai_key not in str(dumped)


def test_rotating_the_key_does_not_move_the_provenance_hash():
    """Two runs of the same experiment either side of a key rotation must compare equal."""

    from ape.scaffolds.ape_agent.config import ApeAgentConfig
    from src.mathlib_review.io import canonical_json_bytes, sha256_bytes

    def digest(key: str) -> str:
        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": key}, clear=False):
            scaffold = ApeAgentConfig(llm_config=LLMConfig(model_name="gpt_5_mini"))
            assert scaffold.llm_config.api_key == key  # the key really did change
            return sha256_bytes(canonical_json_bytes(scaffold.model_dump(mode="json")))

    assert digest("sk-test-aaaa") == digest("sk-test-bbbb")


def test_worker_rebuild_recovers_the_key_from_the_environment(openai_key):
    """`model_validate` of the dump is exactly what `main_from_params` does in the worker."""

    dumped = LLMConfig(model_name="gpt_5_mini").model_dump(mode="json")
    assert LLMConfig.model_validate(dumped).api_key == openai_key


def test_worker_rebuild_cannot_recover_a_yaml_supplied_key():
    """The case preflight has to refuse: a key with no environment variable behind it."""

    with mock.patch.dict(os.environ, {}, clear=True):
        config = LLMConfig(model_name="gpt_5_mini", api_key="sk-from-yaml")
        assert config.api_key == "sk-from-yaml"
        assert LLMConfig.model_validate(config.model_dump(mode="json")).api_key is None


def test_preflight_refuses_a_key_that_would_not_reach_the_worker():
    from ape.scaffolds.ape_agent.config import ApeAgentConfig
    from src.mathlib_review.review.preflight import _check_model_credential

    with mock.patch.dict(os.environ, {}, clear=True):
        scaffold = ApeAgentConfig(
            llm_config=LLMConfig(model_name="gpt_5_mini", api_key="sk-from-yaml"))
        unmet = _check_model_credential(scaffold)

    assert unmet is not None
    assert unmet.name == "model credential source"
    assert "OPENAI_API_KEY" in unmet.remedy


def test_preflight_accepts_a_key_from_the_environment(openai_key):
    from ape.scaffolds.ape_agent.config import ApeAgentConfig
    from src.mathlib_review.review.preflight import _check_model_credential

    scaffold = ApeAgentConfig(llm_config=LLMConfig(model_name="gpt_5_mini"))
    assert _check_model_credential(scaffold) is None


def test_missing_credential_remedy_names_the_variable():
    from ape.scaffolds.ape_agent.config import ApeAgentConfig
    from src.mathlib_review.review.preflight import _check_model_credential

    with mock.patch.dict(os.environ, {}, clear=True):
        scaffold = ApeAgentConfig(llm_config=LLMConfig(model_name="gpt_5_mini"))
        unmet = _check_model_credential(scaffold)

    assert unmet is not None
    assert unmet.name == "model credential"
    assert "OPENAI_API_KEY" in unmet.remedy


def test_every_provider_has_a_key_variable():
    """A provider missing from the table resolves no key and reports no variable to export."""

    assert set(PROVIDER_KEY_ENV_VARS) == set(LLMProvider)
