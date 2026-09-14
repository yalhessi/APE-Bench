"""Loading a run config: the convention, written once.

`load_run` existed three times -- `pr_review_v4/runner.py`, `pr_review_v4/judge_runner.py`,
`mathlib_review/review/runner.py` -- byte-identical except for which dataset model it validates
against. Nine statements, three copies, and each one encodes decisions that have to agree:

* `extends:` is resolved by `load_yaml`, so a child config's inheritance works the same way
  everywhere;
* CLI overrides are deep-merged *before* validation, so a typo in an override is refused by
  the model rather than silently ignored -- `per_pr_cost_capp: 1.50` left the cap at 8.0 and
  authorised five times the intended budget;
* `task_config` is popped out and set as `scaffold.task_config_overrides`, which is what puts
  `enabled_tools` inside `scaffold_config_sha256` and therefore inside the run's provenance;
* `scaffold_type` defaults to `ape_agent`, and **selects the model it is validated against**.

Three copies of that is three chances for one of them to drift, and the fourth caller -- the
unified CLI -- would have been a fourth.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Type

from ape.utils.config_loader import deep_merge, load_yaml


def scaffold_config_class(scaffold_type: str) -> Type:
    """The config model for one scaffold, resolved the way the scaffold factory resolves it.

    `scaffold_type` was a string with one legal value: every config was validated against
    `ApeAgentConfig` whatever it said. `BaseScaffoldConfig` is `extra='forbid'`, so a config
    naming another scaffold was refused outright if it set any of that scaffold's own keys --
    and if it set none, it sealed `scaffold_config_sha256` over the wrong model while the
    worker re-validated the payload against the right one. A run's recorded provenance and the
    config it actually ran under disagreed, silently.

    `ape_agent` is resolved directly rather than through the registry on purpose: the registry
    loads every built-in eagerly and `claude_code` / `codex` import their vendor SDKs at module
    scope, so routing the default through it would make every config load in this project --
    including the judge's and v4's -- depend on an SDK only the baseline conditions need.
    """

    if scaffold_type == "ape_agent":
        from ape.scaffolds.ape_agent.config import ApeAgentConfig

        return ApeAgentConfig

    from ape.scaffolds.registry import get_scaffold_class, list_scaffold_types

    scaffold_class = get_scaffold_class(scaffold_type)
    if scaffold_class is None:
        raise ValueError(
            f"unknown scaffold_type {scaffold_type!r}; "
            f"expected one of {sorted(list_scaffold_types())}")
    return scaffold_class.config_class


def load_run(config_path: Path, dataset_model: Type,
             overrides: Optional[Dict[str, Any]] = None) -> Tuple[Any, Any, Dict[str, Any]]:
    """`(dataset, scaffold, task_overrides)` for one run config.

    `dataset_model` is the only thing that varies between callers: `V4DatasetConfig`,
    `V5DatasetConfig` or `JudgeDatasetConfig`. Everything else about how a config becomes a
    run is the same question with the same answer.
    """

    raw = load_yaml(config_path)
    if overrides:
        raw = deep_merge(raw, overrides)
    dataset = dataset_model.model_validate(raw.pop("dataset"))
    task_overrides = raw.pop("task_config", {}) or {}
    scaffold_type = raw.setdefault("scaffold_type", "ape_agent")
    scaffold = scaffold_config_class(scaffold_type).model_validate(raw)
    # Not merely stashed: this is what puts `enabled_tools` inside the scaffold dump, and so
    # inside `scaffold_config_sha256`, and so inside the run's recorded provenance.
    scaffold.task_config_overrides = task_overrides
    return dataset, scaffold, task_overrides
