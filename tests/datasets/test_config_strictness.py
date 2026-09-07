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
from src.mathlib_review.review.runner import V5DatasetConfig


#: What `judge --of <run_name>` supplies, so a judge config can be validated as it is actually
#: used. The v5 judge configs deliberately carry none of the three: they are one run identity
#: written three times, and writing it three times is what let a judge score rep1's findings
#: under rep2's name.
JUDGE_DERIVED = {"candidates": "results/r/findings.jsonl", "out_dir": "results/audits/r",
                 "run_name": "pr_review_v5_judge_r"}


def _model_for(dataset: dict, path: str):
    """Which dataset model a config belongs to.

    Judge configs are recognised by name rather than by a `candidates` key. Keying on the key
    was fine only while every judge config wrote its own paths; the moment they stopped, four
    of them were silently reclassified as generation configs and validated against the wrong
    model -- which is how a discriminator that reads a field instead of an identity fails.
    """

    if path.endswith("_judge.yaml") or "candidates" in dataset:
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
    if model is JudgeDatasetConfig:
        # As it is actually run. A v5 judge config is incomplete on its own by design, and
        # `--of` is what completes it; validating it without that would test a form nobody
        # uses and would force the paths back into the file.
        dataset = {**JUDGE_DERIVED, **dataset}
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


# --- config inheritance -------------------------------------------------------------------
#
# 13 of 20 keys never vary across the nine v5 generation configs, and 13 of 18 across the six
# judge configs, so most of a config is restated context in which the two or three lines that
# actually differ are hard to find.


def _write(tmp_path, name, text):
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_a_child_inherits_and_overrides_its_parent(tmp_path):
    _write(tmp_path, "base.yaml",
           "llm_config:\n  model_name: gpt_5.2\n  max_tokens: 32000\n"
           "dataset:\n  release: r\n  per_pr_cost_cap: 1.5\n")
    child = _write(tmp_path, "run.yaml",
                   "extends: base.yaml\ndataset:\n  run_name: mine\n  per_pr_cost_cap: 3.0\n")

    merged = load_yaml(child)
    assert merged["llm_config"]["model_name"] == "gpt_5.2"   # inherited
    assert merged["dataset"]["release"] == "r"               # inherited
    assert merged["dataset"]["run_name"] == "mine"           # added
    assert merged["dataset"]["per_pr_cost_cap"] == 3.0       # overridden
    assert "extends" not in merged


def test_lists_are_replaced_not_concatenated(tmp_path):
    """Every list in these configs is a complete statement, not an accumulation: a child that
    says `pr_numbers: [33117]` means those and not those plus the parent's."""

    _write(tmp_path, "base.yaml", "dataset:\n  pr_numbers: [1, 2, 3]\n")
    child = _write(tmp_path, "run.yaml",
                   "extends: base.yaml\ndataset:\n  pr_numbers: [33117]\n")
    assert load_yaml(child)["dataset"]["pr_numbers"] == [33117]


def test_an_explicit_null_overrides_the_parent(tmp_path):
    _write(tmp_path, "base.yaml", "dataset:\n  execution_release: some/path\n")
    child = _write(tmp_path, "run.yaml",
                   "extends: base.yaml\ndataset:\n  execution_release: null\n")
    assert load_yaml(child)["dataset"]["execution_release"] is None


def test_a_cycle_is_refused_rather_than_recursing_forever(tmp_path):
    _write(tmp_path, "a.yaml", "extends: b.yaml\ndataset: {}\n")
    b = _write(tmp_path, "b.yaml", "extends: a.yaml\ndataset: {}\n")
    with pytest.raises(ValueError) as excinfo:
        load_yaml(b)
    assert "circular" in str(excinfo.value)


def test_a_missing_parent_is_reported_by_path(tmp_path):
    child = _write(tmp_path, "run.yaml", "extends: nope.yaml\ndataset: {}\n")
    with pytest.raises(FileNotFoundError) as excinfo:
        load_yaml(child)
    assert "nope.yaml" in str(excinfo.value)


def test_inheritance_is_relative_to_the_child_not_the_cwd(tmp_path):
    _write(tmp_path, "bases/gen.yaml", "dataset:\n  release: r\n")
    child = _write(tmp_path, "runs/one.yaml",
                   "extends: ../bases/gen.yaml\ndataset:\n  run_name: one\n")
    assert load_yaml(child)["dataset"]["release"] == "r"


def test_a_config_without_extends_is_unchanged(tmp_path):
    child = _write(tmp_path, "plain.yaml", "dataset:\n  release: r\n")
    assert load_yaml(child) == {"dataset": {"release": "r"}}


# --- the loading convention itself ---------------------------------------------------------


def test_load_run_has_one_implementation():
    """It existed three times -- v4's runner, v4's judge runner, v5's runner -- byte-identical
    except for which dataset model it validated against, and the unified CLI would have been a
    fourth caller of a nine-line function with three copies.

    The nine statements encode decisions that have to agree: `extends:` resolution, deep-merge
    of overrides *before* validation so a typo is refused rather than ignored, and popping
    `task_config` into `scaffold.task_config_overrides`, which is what puts `enabled_tools`
    inside `scaffold_config_sha256` and so inside the run's provenance.
    """

    import inspect

    from src.datasets.pr_review_v4 import judge_runner, runner as v4_runner
    from src.mathlib_review.review import runner as v5_runner
    from src.mathlib_review.run_config import load_run as shared

    for module in (v4_runner, judge_runner, v5_runner):
        source = inspect.getsource(module.load_run)
        assert "_load_run(" in source, module.__name__
        assert "ApeAgentConfig.model_validate" not in source, (
            f"{module.__name__}.load_run reimplements the convention")

    assert "task_config_overrides" in inspect.getsource(shared)


def test_each_caller_still_validates_against_its_own_model():
    """The one thing that legitimately varies. Sharing the convention must not share the
    schema -- a judge config validated as a generation config would accept the wrong keys."""

    from src.datasets.pr_review_v4.judge_runner import JudgeDatasetConfig
    from src.mathlib_review.run_config import load_run

    dataset, scaffold, overrides = load_run(
        Path("configs/pr_review_v5_specialist4_judge.yaml"), JudgeDatasetConfig,
        {"dataset": dict(JUDGE_DERIVED)})
    assert isinstance(dataset, JudgeDatasetConfig)
    assert scaffold.task_config_overrides == overrides
