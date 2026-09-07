"""Loading a run config: the convention, written once.

`load_run` existed three times -- `pr_review_v4/runner.py`, `pr_review_v4/judge_runner.py`,
`pr_review_v5/runner.py` -- byte-identical except for which dataset model it validates
against. Nine statements, three copies, and each one encodes decisions that have to agree:

* `extends:` is resolved by `load_yaml`, so a child config's inheritance works the same way
  everywhere;
* CLI overrides are deep-merged *before* validation, so a typo in an override is refused by
  the model rather than silently ignored -- `per_pr_cost_capp: 1.50` left the cap at 8.0 and
  authorised five times the intended budget;
* `task_config` is popped out and set as `scaffold.task_config_overrides`, which is what puts
  `enabled_tools` inside `scaffold_config_sha256` and therefore inside the run's provenance;
* `scaffold_type` defaults to `ape_agent`.

Three copies of that is three chances for one of them to drift, and the fourth caller -- the
unified CLI -- would have been a fourth.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Type

from ape.utils.config_loader import deep_merge, load_yaml


def load_run(config_path: Path, dataset_model: Type,
             overrides: Optional[Dict[str, Any]] = None) -> Tuple[Any, Any, Dict[str, Any]]:
    """`(dataset, scaffold, task_overrides)` for one run config.

    `dataset_model` is the only thing that varies between callers: `V4DatasetConfig`,
    `V5DatasetConfig` or `JudgeDatasetConfig`. Everything else about how a config becomes a
    run is the same question with the same answer.
    """

    from ape.scaffolds.ape_agent.config import ApeAgentConfig

    raw = load_yaml(config_path)
    if overrides:
        raw = deep_merge(raw, overrides)
    dataset = dataset_model.model_validate(raw.pop("dataset"))
    task_overrides = raw.pop("task_config", {}) or {}
    raw.setdefault("scaffold_type", "ape_agent")
    scaffold = ApeAgentConfig.model_validate(raw)
    # Not merely stashed: this is what puts `enabled_tools` inside the scaffold dump, and so
    # inside `scaffold_config_sha256`, and so inside the run's recorded provenance.
    scaffold.task_config_overrides = task_overrides
    return dataset, scaffold, task_overrides
