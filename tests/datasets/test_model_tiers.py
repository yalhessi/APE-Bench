"""Invariants for the two model tiers, checked at CI time rather than at plan time.

The project runs two tiers: `elm_qwen_3.5` for iteration (free, local, its numbers are a
signal) and `gpt_5.2` / `gpt_5_mini` for keeps (paid, pinned, its numbers are results). The
runtime already refuses the worst outcome -- `_assert_a_ceiling_binds` stops a run on a
zero-priced model with no token ceiling -- but that fires at `plan`, once someone has written
a config and gone to use it. These lift the same conditions to the config files themselves.
"""

from __future__ import annotations

import glob
from pathlib import Path

import pytest

from ape.llm_clients.config import MODEL_MAPPINGS, LLMProvider
from ape.utils.config_loader import load_yaml

CONFIGS = sorted(glob.glob("configs/*.yaml")) + sorted(glob.glob("configs/bases/*.yaml"))


def _model(raw: dict) -> str | None:
    return (raw.get("llm_config") or {}).get("model_name")


def _is_free(name: str | None) -> bool:
    entry = MODEL_MAPPINGS.get(name or "")
    return bool(entry) and not (entry.get("input_per_1M") or entry.get("output_per_1M"))


def _is_elm(name: str | None) -> bool:
    entry = MODEL_MAPPINGS.get(name or "")
    return bool(entry) and entry["provider"] is LLMProvider.ELM


def _loaded():
    for path in CONFIGS:
        raw = load_yaml(Path(path))
        if isinstance(raw, dict) and raw.get("llm_config"):
            yield path, raw


def _free_configs():
    return [(p, r) for p, r in _loaded() if _is_free(_model(r))]


def _elm_configs():
    return [(p, r) for p, r in _loaded() if _is_elm(_model(r))]


def test_the_sweep_finds_something():
    """Both sweeps below would pass vacuously if the globs matched nothing."""

    assert _free_configs(), "no config on a zero-priced model; the ceiling test is vacuous"
    assert _elm_configs(), "no config on an ELM model; the reasoning test is vacuous"


@pytest.mark.parametrize("path,raw", _free_configs(), ids=lambda v: Path(v).name if isinstance(v, str) else "")
def test_a_zero_priced_config_sets_a_ceiling_that_can_bind(path, raw):
    """On a model priced 0.0 every dollar cap is satisfied by any run whatsoever.

    `standard_budget_cap`, `lead_cost_cap`, `per_pr_cost_cap` and `run_total_cost_cap` all
    bind billed spend and there is none, so a config that sets only those is unbounded in the
    only sense that matters. This is the same condition `_assert_a_ceiling_binds` enforces at
    plan time, asserted here so a config cannot be committed in that state.
    """

    dataset = raw.get("dataset") or {}
    execution = raw.get("execution") or {}

    if dataset.get("input_kind") == "finding" or "judge" in Path(path).name:
        assert execution.get("sample_max_tokens"), (
            f"{path} judges on a zero-priced model but sets no execution.sample_max_tokens; "
            f"its sample_max_cost={execution.get('sample_max_cost')!r} cannot bind."
        )
        return

    mode = dataset.get("routing_mode")
    if mode == "solo":
        required = ("solo_token_cap",)
    elif mode == "lead":
        required = ("standard_budget_tokens", "per_pr_token_cap")
    else:
        required = ("standard_budget_tokens",)

    missing = [key for key in required if not dataset.get(key)]
    assert not missing, (
        f"{path} runs {_model(raw)} (priced 0.0) in routing_mode={mode!r} with {missing} "
        f"unset, so nothing bounds it but max_turns x max_delegations."
    )


@pytest.mark.parametrize("path,raw", _elm_configs(), ids=lambda v: Path(v).name if isinstance(v, str) else "")
def test_an_elm_config_states_its_reasoning_effort(path, raw):
    """There is no "the ELM default" to leave unstated.

    `elm_qwen_3.5` reasons when nothing is sent and `elm_mistral_small_4` does not, so an
    absent `reasoning_effort` is not a neutral default -- it is a different setting per model,
    unrecorded. It is worth ~100x in completion tokens and ~23x in latency, which is larger
    than any effect these runs are trying to measure.
    """

    effort = raw["llm_config"].get("reasoning_effort")
    assert effort is not None, (
        f"{path} runs {_model(raw)} without stating llm_config.reasoning_effort. "
        f"Whether it reasons then depends on the model, and the run plan records a value "
        f"nobody chose."
    )

    entry = MODEL_MAPPINGS[_model(raw)]
    supported = entry.get("reasoning_efforts")
    if supported is not None:
        assert effort in supported, (
            f"{path} sets reasoning_effort={effort!r}, which ELM does not honour for "
            f"{_model(raw)}; measured values are {sorted(supported)}."
        )


def test_the_iteration_judge_differs_from_the_pinned_one_only_where_it_must():
    """The iteration judge is allowed to be a different model. It is not allowed to be a
    different judge.

    Its whole value is telling you the pipeline ran -- pairs built, verdicts came back, the
    stage chain held. That is only informative if the rubric, the pairing tier, the sample
    count and the toolset are the ones the real judge uses. A drift in `pairing_tiers` or
    `sample_count` would make the cheap signal stop predicting the expensive one, silently.
    """

    pinned = load_yaml(Path("configs/bases/v5_judge.yaml"))
    iteration = load_yaml(Path("configs/bases/v5_judge_qwen.yaml"))

    allowed = {
        ("llm_config", "model_name"),
        ("llm_config", "reasoning_effort"),
        ("execution", "sample_max_tokens"),
    }

    differences = set()
    for section in set(pinned) | set(iteration):
        left, right = pinned.get(section), iteration.get(section)
        if isinstance(left, dict) and isinstance(right, dict):
            for key in set(left) | set(right):
                if left.get(key) != right.get(key):
                    differences.add((section, key))
        elif left != right:
            differences.add((section, None))

    assert differences <= allowed, (
        f"the iteration judge diverges from the pinned judge at {sorted(differences - allowed)}. "
        f"Only the model, its reasoning setting and the token ceiling may differ."
    )


def test_the_pinned_judge_is_still_pinned_and_paid():
    """The keeps tier is what every historical number was measured with; it does not move
    because a cheaper option now exists."""

    pinned = load_yaml(Path("configs/bases/v5_judge.yaml"))
    assert pinned["llm_config"]["model_name"] == "gpt_5_mini"
    assert not _is_free("gpt_5_mini")
    assert MODEL_MAPPINGS["gpt_5_mini"]["model_name"] == "gpt-5-mini-2025-08-07", (
        "the pinned judge must keep a dated snapshot; ELM's bare `gpt-5-mini` alias is not "
        "guaranteed to be the same weights."
    )
