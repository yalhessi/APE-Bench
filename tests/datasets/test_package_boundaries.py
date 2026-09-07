"""Boundaries that are currently violated, measured so they cannot get worse.

Mapping the tree turned up the coupling that makes one experiment touch thirteen source files
across six packages:

* 97 names imported from v4 into v5 across 41 statements, and **backward** edges where v4
  imports v5 — so "v4 is frozen and imported as a library" is not true. 13 -> 4: `paths` and
  `patchset` moved to `src/mathlib_review/`, which is what that package is for;
* 42 imports of `_`-private symbols across module boundaries, six of them across generations.
  37 now, after `evidence._tool_env`/`_run` became `mathlib_review.workspace` and
  `corpus._eval_pr_numbers` became `mathlib_review.corpus`;
* one shared review base (`pr_review_v2/base.py`) edited on the strength of a v5-only
  observation, which changed the tool contract for every v2 checker and every v4 arm. That one
  is fixed: it lives at `formal_math/review_task.py` now, owned by no generation, and v5 -> v2
  fell from 6 edges to 2.

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
    # 13 -> 4. Two clusters went to `src/mathlib_review/`, which is what that package is for:
    # `paths` (the judge deriving its own paths from the generation run it scores) and
    # `patchset` (the coordinated multi-file edit, used by the shared candidate contract).
    # Neither belonged to v5; both were imported backwards because that is where they were
    # first written.
    #
    # What is left is one real case: v4's `review_overlay` renders a v5 run. That is a reader
    # reaching forward to the generation whose output it displays, and it goes away when there
    # is one generation rather than by being moved.
    assert len(edges) <= 4, (
        "new backward v4 -> v5 import(s):\n" +
        "\n".join(f"  {p}: {m}.{n}" for p, m, n in edges))


def test_v5_does_not_reach_back_into_v2_at_all():
    """6 -> 0, and this one gets to assert zero.

    Four were the shared review base, which v5's lead inherited from inside v2 and which now
    lives beside the generations. Two were `corpus._eval_pr_numbers` and
    `precedent_bench.hunk_code` -- the eval-set exclusion and the diff-hunk reader, both of
    which are about what a reviewer may see and neither of which is v2's.
    """

    edges = _cross_generation_edges("v5", "v2")
    assert edges == [], (
        "v5 reaches back into v2:\n" +
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
    # 42 -> 37: `_tool_env` and `_run` were private names in `pr_review_v4/evidence.py` that
    # four modules across two packages imported anyway, so `evidence.py` -- where the evidence
    # chain lives -- could not be refactored without breaking a coordinated-patch verifier
    # that has no reason to care about evidence. They are `mathlib_review.workspace` now.
    assert len(found) <= 37, (
        f"{len(found)} private cross-module imports (was 37):\n" +
        "\n".join(f"  {p}: {m}.{n}" for p, m, n in sorted(found)[:12]))


def test_the_shared_review_base_belongs_to_no_generation():
    """It was `pr_review_v2/base.py`, and all three generations inherited it from there, so a
    v5-only observation about `lean_verify_edit` changed the tool contract for every v2
    checker and every v4 arm. This session did exactly that before moving it.

    Now it is `formal_math/review_task.py`, beside the generations. Inside the task tree
    rather than in `src/mathlib_review/`, because `ape/tasks/__init__.py` imports every task
    package eagerly and a `BaseLeanTask` subclass outside that tree cannot import
    `ape.tasks.base` without a cycle.
    """

    shared = Path("src/ape/tasks/lean_tasks/formal_math/review_task.py")
    assert shared.is_file()
    assert not Path("src/ape/tasks/lean_tasks/formal_math/pr_review_v2/base.py").exists()

    importers = {
        str(path) for path in _modules(sum(GENERATIONS.values(), ()))
        for module, _name in _imports(path)
        if module.endswith("formal_math.review_task")
    }
    for generation in ("pr_review_v2", "pr_review_v4", "pr_review_v5"):
        assert any(generation in item for item in importers), generation

    # And no generation re-exports it. Doing so is what made `ape.tasks` pull v2 in to reach a
    # class v2 does not own.
    init = Path("src/ape/tasks/lean_tasks/formal_math/pr_review_v2/__init__.py")
    assert "BasePRReviewTask" not in init.read_text(encoding="utf-8").split('"""')[-1]


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
