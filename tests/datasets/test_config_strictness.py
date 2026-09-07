"""Configs are validated strictly, and overrides that do not parse are refused.

The half of the config that spends money was the unvalidated half. `V5DatasetConfig` ignored
unknown keys, so `per_pr_cost_capp: 1.50` left the cap at its default of 8.0 -- authorising
five times the intended budget -- while `ExecutionConfig`, one block away in the same file,
rejected the same class of typo.

The override parser had the mirror-image defect: any token without `=` was silently discarded.
The command checked into `docs/research/medium-end-to-end-runbook.md` spells overrides as
`--dataset.dry_run false`, so every one of its overrides was dropped and the run executed with
the YAML's `dry_run: true` and the previous run's output path.

Only two of fifteen v5 configs were parsed by any test before this file.
"""

from __future__ import annotations

import glob
from pathlib import Path

import pytest

from ape.utils.config_loader import load_yaml, parse_cli_args
from src.datasets.pr_review_v4.judge_runner import JudgeDatasetConfig
from src.datasets.pr_review_v4.runner import V4DatasetConfig
from src.datasets.pr_review_v5.runner import V5DatasetConfig


def _model_for(dataset: dict, path: str):
    """Which dataset model a config belongs to, by the keys only that model has."""

    if "candidates" in dataset:
        return JudgeDatasetConfig
    if "routing_mode" in dataset or "v5" in path:
        return V5DatasetConfig
    if "arm" in dataset or "v4" in path:
        return V4DatasetConfig
    return None


def _dataset_configs():
    for path in sorted(glob.glob("configs/*.yaml")):
        raw = load_yaml(Path(path))
        dataset = raw.get("dataset")
        if not dataset:
            continue
        model = _model_for(dataset, path)
        if model is not None:
            yield path, model, dataset


@pytest.mark.parametrize("path,model,dataset", list(_dataset_configs()),
                         ids=lambda v: Path(v).name if isinstance(v, str) else "")
def test_every_shipped_config_validates(path, model, dataset):
    model.model_validate(dataset)


def test_at_least_the_known_configs_were_exercised():
    """Guards the discovery above: a glob that silently matches nothing would pass every
    parametrised case by vacuity."""

    assert len(list(_dataset_configs())) >= 20


@pytest.mark.parametrize("model,required", [
    (V5DatasetConfig, {"release": "r", "modification_inventory": "m"}),
    (JudgeDatasetConfig, {"release": "r", "candidates": "c", "out_dir": "o"}),
])
def test_a_misspelled_key_is_refused_rather_than_ignored(model, required):
    with pytest.raises(Exception) as excinfo:
        model.model_validate({**required, "per_pr_cost_capp": 999})
    assert "per_pr_cost_capp" in str(excinfo.value)


def test_a_misspelled_budget_key_used_to_authorise_five_times_the_budget():
    """The concrete case: the typo left the cap at 8.0 against the 1.50 every config sets."""

    good = V5DatasetConfig.model_validate(
        {"release": "r", "modification_inventory": "m", "per_pr_cost_cap": 1.50})
    assert good.per_pr_cost_cap == 1.50
    with pytest.raises(Exception):
        V5DatasetConfig.model_validate(
            {"release": "r", "modification_inventory": "m", "per_pr_cost_capp": 1.50})


def test_overrides_that_do_not_parse_are_refused():
    with pytest.raises(ValueError) as excinfo:
        parse_cli_args(["--dataset.dry_run", "false"])
    assert "--dataset.dry_run" in str(excinfo.value)
    assert "key.path=value" in str(excinfo.value)


def test_the_working_override_spelling_still_parses():
    assert parse_cli_args(["dataset.dry_run=False"]) == {"dataset": {"dry_run": False}}


def test_the_runbook_command_form_is_the_one_that_was_being_dropped():
    """Pins the exact shape from docs/research/medium-end-to-end-runbook.md."""

    argv = ["--dataset.dry_run", "false",
            "--dataset.run_name", "pr_review_v4_medium_010_rep1"]
    with pytest.raises(ValueError):
        parse_cli_args(argv)
