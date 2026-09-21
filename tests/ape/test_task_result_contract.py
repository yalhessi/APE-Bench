"""A result field that is not declared must fail loudly, not vanish.

`BaseTaskResult` is pydantic with the default `extra="ignore"`, and `create_result(**kwargs)`
forwarded whatever it was given. So a task could record something, the field could be absent
from the result model, and the value disappeared with the suite green. This repository has paid
for that six times -- `abstention` on a candidate result, `model_confidence` and
`rejected_alternatives` between candidates and findings, `execution_limits` and `session_replay`
between the orchestrator and the worker, `documentation` vs `docs` in the concern vocabulary --
and each one presented as a working feature reading zero downstream.

Construction is strict; *loading* stays lenient, and the distinction is the whole design. A
`task_result.json` written before a field existed must keep loading, or every historical run in
the tree becomes unreadable.
"""

from __future__ import annotations

import ast
import asyncio
import importlib
import pathlib
from typing import List, Optional, Tuple

import pytest
from pydantic import Field

import ape.tasks  # noqa: F401  -- eagerly registers every task package
from datetime import datetime

from ape.orchestration.models import Attempt, ExecutionStatus, Sample
from ape.orchestration.persistence import TaskStorage
from ape.scaffolds.ape_agent.config import ApeAgentConfig
from ape.tasks.base import BaseTask, BaseTaskData, BaseTaskResult


class _Data(BaseTaskData):
    task_type: str = "contract_probe"


class _Result(BaseTaskResult):
    declared: Optional[str] = None


class _Task(BaseTask):
    task_type = "contract_probe"
    data_class = _Data
    task_result_class = _Result


def _task() -> _Task:
    return _Task(_Data(task_id="t1"), ApeAgentConfig())


def test_a_declared_field_is_accepted_and_identity_is_stamped():
    result = _task().create_result(success=True, score=1.0, declared="kept")
    assert result.declared == "kept"
    assert (result.task_id, result.task_type) == ("t1", "contract_probe")
    assert result.global_index == _Data(task_id="t1").global_index


def test_an_undeclared_field_is_refused_rather_than_dropped():
    with pytest.raises(TypeError) as error:
        _task().create_result(success=True, score=1.0, model_confidence=0.7)
    message = str(error.value)
    assert "model_confidence" in message and "_Result" in message


def test_the_refusal_names_every_undeclared_field_at_once():
    """One at a time would mean one edit, one run, one more failure."""

    with pytest.raises(TypeError) as error:
        _task().create_result(success=True, score=1.0, alpha=1, beta=2)
    assert "'alpha'" in str(error.value) and "'beta'" in str(error.value)


def test_loading_a_persisted_result_with_an_unknown_field_still_works(tmp_path):
    """The other half, on a real registered task. A result written before a field existed --
    or after one was removed -- must keep loading, so strictness at construction cannot make
    old runs unreadable. `TaskStorage._normalize_sample` re-validates persisted results, and
    that path stays lenient by design."""

    storage = TaskStorage(tmp_path / "0", "0")
    sample = Sample(
        sample_id="s", task_global_index="0", sample_index=0,
        status=ExecutionStatus.SUCCESS, created_at=datetime.now(), updated_at=datetime.now(),
        attempts=[Attempt(
            attempt_id=0, path=tmp_path / "attempt", status=ExecutionStatus.SUCCESS,
            created_at=datetime.now(), max_turns=10, cost_limit=None, result={
                "task_id": "t1", "task_type": "lean_pr_review_v5_arm", "global_index": "0",
                "success": True, "score": 1.0, "pr_number": 33098,
                "work_unit_id": "wu:a", "rendered_prompt_sha256": "a" * 64,
                "candidates": [], "a_field_this_class_no_longer_has": 42,
            })],
    )
    asyncio.run(storage.save_sample(sample))
    loaded = asyncio.run(storage.load_all_samples("lean_pr_review_v5_arm"))
    result = loaded[0].attempts[0].result
    assert result.work_unit_id == "wu:a" and result.pr_number == 33098
    assert not hasattr(result, "a_field_this_class_no_longer_has")


def _enclosing_class(tree: ast.AST, lineno: int) -> Optional[str]:
    best = None
    for node in ast.walk(tree):
        if (isinstance(node, ast.ClassDef) and node.lineno <= lineno <= (node.end_lineno or 0)
                and (best is None or node.lineno > best.lineno)):
            best = node
    return best.name if best else None


def _enclosing_method(tree: ast.AST, class_name: str, lineno: int) -> Optional[str]:
    """The method of `class_name` that contains this line, even when the call is in a closure
    inside it -- `submit_findings` is a nested function inside `register_task_tools`."""

    for node in ast.walk(tree):
        if not (isinstance(node, ast.ClassDef) and node.name == class_name):
            continue
        for member in node.body:
            if (isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and member.lineno <= lineno <= (member.end_lineno or 0)):
                return member.name
    return None


def _result_classes_for(cls, method: Optional[str]) -> List[Tuple[str, type]]:
    """The result models this call site can actually construct.

    A `create_result` in an abstract base is executed by its concrete subclasses, and those
    declare the richer model -- `ReviewPRCoreTask` passes nine fields `BaseTaskResult` does not
    have and every registered subclass declares all nine, so checking the base against its own
    default would report a defect that cannot happen.

    A leaf that *overrides* the enclosing method never runs this code, and checking it would
    report the opposite kind of phantom: `LeanPRReviewSelectorTask` registers its own tools and
    its narrower result model has no `findings` field, but the base's `submit_findings` closure
    is not its. So a leaf counts only when the definition it inherits is this one.
    """

    leaves = []

    def walk(node):
        subclasses = node.__subclasses__()
        if not subclasses:
            leaves.append(node)
        for sub in subclasses:
            walk(sub)

    walk(cls)
    resolved = []
    for leaf in leaves:
        if leaf.task_result_class is None:
            continue
        if method is not None:
            owner = next((item for item in leaf.__mro__ if method in item.__dict__), None)
            if owner is None or owner.__name__ != cls.__name__:
                continue
        resolved.append((leaf.__name__, leaf.task_result_class))
    return resolved


def test_every_create_result_call_site_passes_only_declared_fields():
    """The guard that makes the refusal cheap: a call site that would raise is found here,
    statically, instead of at the end of a paid attempt inside a `try` that logs a warning."""

    offenders = []
    for path in sorted(pathlib.Path("src/ape").rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        if "create_result(" not in source:
            continue
        tree = ast.parse(source)
        module = importlib.import_module(str(path).replace("src/", "").replace("/", ".")[:-3])
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "create_result"):
                continue
            keywords = {item.arg for item in node.keywords if item.arg}
            class_name = _enclosing_class(tree, node.lineno)
            owner = getattr(module, class_name or "", None)
            if owner is None or not isinstance(owner, type) or not issubclass(owner, BaseTask):
                continue
            method = _enclosing_method(tree, class_name, node.lineno)
            for leaf_name, result_class in _result_classes_for(owner, method):
                undeclared = sorted(keywords - set(result_class.model_fields))
                if undeclared:
                    offenders.append(
                        f"{path}:{node.lineno} run as {leaf_name} -> "
                        f"{result_class.__name__} lacks {undeclared}")
    assert offenders == [], (
        "create_result would raise at these call sites:\n  " + "\n  ".join(offenders))
