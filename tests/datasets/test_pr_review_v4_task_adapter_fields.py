"""Every field the task adapter passes must exist on the model it builds.

`BasePRReviewData` does not set `extra="forbid"`, so a keyword naming a field the model
never declared is silently dropped at construction and only surfaces when something reads
it back. That is exactly how the `/12` smoke was lost: `build_candidate_task_data` passed
`paths_by_change=unit.paths_by_change`, the model had no such field, and all 22 work units
crashed inside `submit_candidates` with `'LeanPRReviewV4CandidateData' object has no
attribute 'paths_by_change'` — after the agents had done their review work and paid for it.

Checked by AST rather than by constructing the models, because the failure is a *missing*
field: a runtime check would need an instance carrying the value, which is precisely what
cannot exist. The adapter's call keywords are the ground truth for what it intends to set.
Every construction site in the module is swept, not a listed few, so a new builder is
covered the day it is written.
"""

import ast
import importlib
import inspect

import pytest

from src.mathlib_review.review import task_adapter


def _resolve(model_name: str):
    """Import the model the way the adapter itself does.

    Some builders import their model inside the function body, so the name is not an
    attribute of `ape.tasks.lean_tasks` and cannot be looked up on the package. The
    adapter's own `from … import …` statements — at any nesting depth — are the map.
    """

    tree = ast.parse(inspect.getsource(task_adapter))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                if (alias.asname or alias.name) == model_name:
                    module = importlib.import_module(
                        node.module if node.level == 0
                        else f"src.mathlib_review.review.{node.module}"
                    )
                    return getattr(module, alias.name)
    raise AssertionError(f"the adapter constructs {model_name} but never imports it")


def _construction_sites():
    """(function, model name, keywords) for every task-data model built in the adapter."""

    tree = ast.parse(inspect.getsource(task_adapter))
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for call in ast.walk(node):
            if (
                isinstance(call, ast.Call)
                and isinstance(call.func, ast.Name)
                and call.func.id.startswith("LeanPRReview")
                and call.func.id.endswith("Data")
            ):
                yield (
                    node.name,
                    call.func.id,
                    frozenset(kw.arg for kw in call.keywords if kw.arg is not None),
                )


_SITES = sorted(set(_construction_sites()))


def test_the_sweep_actually_found_the_builders():
    """A silent zero-site sweep would make every assertion below vacuous."""

    models = {model for _fn, model, _kw in _SITES}
    assert len(_SITES) >= 3, f"expected the adapter's builders, found {_SITES}"
    assert "LeanPRReviewV4CandidateData" in models


@pytest.mark.parametrize("function_name,model_name,passed", _SITES)
def test_adapter_only_sets_fields_the_model_declares(function_name, model_name, passed):
    model = _resolve(model_name)
    undeclared = set(passed) - set(model.model_fields)
    assert undeclared == set(), (
        f"{function_name} passes {sorted(undeclared)}, which {model_name} does not declare. "
        "Pydantic drops them silently and the attribute is missing at read time."
    )


def test_candidate_task_data_carries_the_path_map_the_renderer_added():
    """The specific regression: /12's path map must survive construction.

    Its default must be empty rather than required — frozen /11 task data declares no path
    map, and making it mandatory would stop the locked baseline from loading.
    """

    from ape.tasks.models import WorkspaceInfo

    model = _resolve("LeanPRReviewV4CandidateData")
    assert "paths_by_change" in model.model_fields

    instance = model(
        task_id="t", pr_number=1, work_unit_id="wu:x", episode_id="ep:x", diff="",
        change_ids=[], entity_ids_by_change={}, primary_subjects_by_change={},
        rendered_system_prompt="", rendered_user_prompt="", rendered_prompt_sha256="0" * 64,
        target_workspace=WorkspaceInfo(name="target", commit_hash="0" * 40,
                                       repo_url="https://example.invalid/repo.git"),
    )
    assert instance.paths_by_change == {}
