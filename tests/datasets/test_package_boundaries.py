"""Boundaries that are currently violated, measured so they cannot get worse.

Mapping the tree turned up the coupling that makes one experiment touch thirteen source files
across six packages:

* 97 names imported from v4 into v5 across 41 statements, and **backward** edges where v4
  imports v5 — so "v4 is frozen and imported as a library" is not true;
* 42 imports of `_`-private symbols across module boundaries, six of them across generations;
* one shared review base (`pr_review_v2/base.py`) edited on the strength of a v5-only
  observation, which changes the tool contract for every v2 checker and every v4 arm.

The consolidation these tests belong to has not happened yet, so they do not assert zero.
They **pin the current counts**: a new violation fails the build, and fixing one is expected
to require lowering a number here. That is the point — the budget only moves in one direction,
and moving it is a deliberate edit rather than a silent drift.

Counts are of imported *names*, not import statements, which is why they run higher than a
count of `from ... import` lines: v4 -> v5 is 13 names across 4 statements.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

SRC = Path("src")

#: Packages that make up the review system, newest first.
GENERATIONS = {
    "v5": ("src/datasets/pr_review_v5",
           "src/ape/tasks/lean_tasks/formal_math/pr_review_v5"),
    "v4": ("src/datasets/pr_review_v4",
           "src/ape/tasks/lean_tasks/formal_math/pr_review_v4"),
    "v2": ("src/datasets/pr_review_v2",
           "src/ape/tasks/lean_tasks/formal_math/pr_review_v2"),
}


def _modules(prefixes):
    for prefix in prefixes:
        root = Path(prefix)
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            yield path


def _imports(path: Path):
    """Every imported dotted name in a file, including function-local imports."""

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:  # pragma: no cover - a syntax error is a different test's problem
        return
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                yield node.module, alias.name
        elif isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name, ""


def _cross_generation_edges(source: str, target: str):
    pattern = re.compile(rf"pr_review_{target}\b")
    edges = []
    for path in _modules(GENERATIONS[source]):
        for module, name in _imports(path):
            if pattern.search(module):
                edges.append((str(path), module, name))
    return edges


def test_v4_does_not_import_v5_beyond_the_known_backward_edges():
    """`v4 is frozen and imported as a library` is the stated contract and is not true.

    Three backward edges exist: v4's overlay top-level-imports a v5 view, and the shared v4
    candidate task imports v5's `patchset` for a capability that exists only for v5's
    `family_design` arm. Importing v4's overlay therefore pulls in v5.
    """

    edges = _cross_generation_edges("v4", "v5")
    # 11 -> 13: `judge_runner.derive_from_run` imports `pr_review_v5.paths.run_dir` so that a
    # judge run's paths come from the generation run's name instead of three free-form strings
    # that must agree by hand -- which they did not: one config was bumped to rep2 while its
    # judge still read rep1. That the judge must know where generation writes is an
    # unavoidable *data* dependency; the code dependency goes away in the collapse, when path
    # conventions move to a shared core. Raised deliberately rather than worked around by
    # duplicating the path, which is the two-sources-of-truth problem this session keeps
    # finding.
    assert len(edges) <= 13, (
        "new backward v4 -> v5 import(s):\n" +
        "\n".join(f"  {p}: {m}.{n}" for p, m, n in edges))


def test_v5_does_not_reach_further_back_into_v2():
    """v5 imports v2 in exactly two places -- `corpus._eval_pr_numbers` and
    `precedent_bench.hunk_code` -- plus the shared review base every generation inherits."""

    edges = _cross_generation_edges("v5", "v2")
    assert len(edges) <= 6, (
        "new v5 -> v2 import(s):\n" +
        "\n".join(f"  {p}: {m}.{n}" for p, m, n in edges))


def _private_cross_module_imports():
    found = []
    for prefixes in GENERATIONS.values():
        for path in _modules(prefixes):
            for module, name in _imports(path):
                if not name.startswith("_") or name.startswith("__"):
                    continue
                # A sibling module inside the same package is not a boundary crossing.
                own_package = ".".join(str(path.parent).split("/"))
                if module.startswith(".") or own_package.endswith(module.rsplit(".", 1)[0]):
                    continue
                found.append((str(path), module, name))
    return found


def test_private_cross_boundary_imports_do_not_increase():
    """Treating another module's `_`-prefixed names as API is how a refactor of one file
    breaks three others. `evidence_chain` imports `_candidate_spans` and `_diagnostic_lines`
    from v4's evidence module; `patchset` imports `_run`; `report` imports
    `_SUBMISSION_CONTRACT`."""

    found = _private_cross_module_imports()
    assert len(found) <= 42, (
        f"{len(found)} private cross-module imports (was 42):\n" +
        "\n".join(f"  {p}: {m}.{n}" for p, m, n in sorted(found)[:12]))


def test_the_shared_review_base_is_shared_by_all_three_generations():
    """Pins why editing it is consequential: `pr_review_v2/base.py` is the base class for
    every review task in v2, v4 and v5, so a v5-only observation that changes it changes the
    tool contract for every v2 checker and every v4 arm. This session did exactly that."""

    importers = [
        str(path) for path in _modules(sum(GENERATIONS.values(), ()))
        for module, _name in _imports(path)
        if module.endswith("pr_review_v2.base")
    ]
    assert any("pr_review_v4" in item for item in importers)
    assert any("pr_review_v5" in item for item in importers)


def test_tier_multipliers_has_exactly_one_definition():
    """It was defined verbatim in two packages with neither importing the other, so the task
    layer could price jobs differently from the plan that budgeted them."""

    definitions = [
        str(path) for path in SRC.rglob("*.py")
        if "__pycache__" not in path.parts
        and re.search(r"^TIER_MULTIPLIERS\s*=", path.read_text(encoding="utf-8"), re.M)
    ]
    assert definitions == ["src/datasets/pr_review_v5/schema.py"], definitions


def test_the_context_tool_grant_has_one_owner():
    """The vocabulary lives in `schema`, the policy in `arms`. The schema comment used to
    assert the opposite of what `arms` does."""

    schema = Path("src/datasets/pr_review_v5/schema.py").read_text(encoding="utf-8")
    arms = Path("src/datasets/pr_review_v5/arms.py").read_text(encoding="utf-8")
    assert re.search(r"^_CONTEXT_GRANTS\s*:", arms, re.M)
    # The policy is defined in one place; `schema` may refer to it but must not restate it.
    assert not re.search(r"^_CONTEXT_GRANTS\s*[:=]", schema, re.M)
    # The stale claim that every arm gets all four must not come back.
    assert "Defaulting every arm to all four is" not in schema
