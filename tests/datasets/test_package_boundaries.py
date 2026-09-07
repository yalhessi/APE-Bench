"""Boundaries, measured so they cannot get worse.

Mapping the tree once turned up the coupling that made one experiment touch thirteen source
files across six packages: 97 names imported from v4 into v5, **backward** edges where v4
imported v5, 42 private cross-module imports, and a shared review base living inside the
oldest generation so that a v5-only observation changed the tool contract for every v2 checker.

The review pipeline is one package now -- `src/mathlib_review/` -- and these pin what that
bought, plus the boundaries inside it:

* no generation imports a later one, asserted as zero rather than budgeted;
* v5 -> v2 is zero;
* private names do not cross a generation;
* inside `mathlib_review`, three private imports cross a module boundary (down from 42 across
  the tree, though most of that 42 became legitimate sibling imports when the packages
  merged -- the honest comparison is the three, not the drop).

What remains under a generation name is the *task* packages: the classes an orchestrator
schedules. v2 keeps its data work, which has not moved.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

SRC = Path("src")

#: Packages that make up the review system, newest first.
#: What is left that is generation-shaped. The *pipeline* is no longer: v4 and v5 both moved
#: into `src/mathlib_review/`, so these are the task packages -- the classes an orchestrator
#: schedules -- plus v2, whose data work has not moved yet.
GENERATIONS = {
    "v5": ("src/ape/tasks/lean_tasks/formal_math/pr_review_v5",),
    "v4": ("src/ape/tasks/lean_tasks/formal_math/pr_review_v4",),
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


def test_no_generation_imports_a_later_one():
    """13 -> 0, and this asserts zero.

    Two clusters moved to `src/mathlib_review/` as shared primitives: `paths` (the judge
    deriving its own paths from the run it scores) and `patchset` (the coordinated multi-file
    edit, used by the shared candidate contract). The last four were v4's `review_overlay`
    importing `delegation_view` to render a v5 run -- a reader reaching forward to the
    generation whose output it displays -- and they went when the pipeline stopped being a
    generation at all. `delegation_view` is `mathlib_review.analysis.delegation_view` now, and
    v4 importing it is an ordinary forward edge to shared code.

    v5 -> v4 remains, and is fine: the newer task package builds on the older one's candidate
    contract, which is what inheritance is.
    """

    backward = (_cross_generation_edges("v4", "v5")
                + _cross_generation_edges("v2", "v4")
                + _cross_generation_edges("v2", "v5"))
    assert backward == [], (
        "an older generation imports a newer one:\n" +
        "\n".join(f"  {p}: {m}.{n}" for p, m, n in backward))


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
    """In what is left of the generation packages: v2's `evaluate_d2` and `selector`, mostly.

    42 -> 14, and most of that drop is scope rather than improvement -- when v4 and v5 merged,
    imports that used to cross a package became sibling imports inside one. The number that
    did not shrink by definition is in the next test.
    """

    found = _private_cross_module_imports()
    assert len(found) <= 14, (
        f"{len(found)} private cross-module imports (was 14):\n" +
        "\n".join(f"  {p}: {m}.{n}" for p, m, n in sorted(found)[:12]))


def test_private_imports_inside_mathlib_review_do_not_increase():
    """The honest number: a private name reached across a module boundary *within* the merged
    package, where a sibling import would be legitimate and this is not.

    Three, and each is a real one -- `wrapper_composition._changed_roles` and `._target_goal`
    read by the implementation registry, and `lean_parser._build_top_level_index` read by the
    change-graph builder.
    """

    root = Path("src/mathlib_review")
    found = []
    for path in root.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        own = ".".join(path.relative_to(root).parent.parts)
        for module, name in _imports(path):
            if not name.startswith("_") or name.startswith("__"):
                continue
            if not module.startswith("src.mathlib_review."):
                continue
            target = module.replace("src.mathlib_review.", "")
            if target.rsplit(".", 1)[0] == own:
                continue
            found.append((str(path), module, name))
    assert len(found) <= 3, (
        f"{len(found)} private imports cross a module boundary inside mathlib_review "
        f"(was 3):\n" + "\n".join(f"  {p}: {m}.{n}" for p, m, n in sorted(found)))


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
    assert definitions == ["src/mathlib_review/schema/review.py"], definitions


def test_the_context_tool_grant_has_one_owner():
    """The vocabulary lives in `schema`, the policy in `arm_registry`.

    `arms.py` held `_CONTEXT_GRANTS = context_grants()`, a module-level snapshot taken at
    import. Correct, since the registry is static in a running process, and still a copy of a
    table the registry exists to stop copying -- a derived view that stops tracking its source
    is the same defect as the four hand-maintained dictionaries it replaced, one import
    earlier. `_grant_for` reads the registry per call now.
    """

    schema = Path("src/mathlib_review/schema/review.py").read_text(encoding="utf-8")
    arms = Path("src/mathlib_review/agenda/arms.py").read_text(encoding="utf-8")
    assert "context_grants().get(arm_id" in arms
    # No module-level copy in either file.
    assert not re.search(r"^_CONTEXT_GRANTS\s*[:=]", arms, re.M)
    assert not re.search(r"^_CONTEXT_GRANTS\s*[:=]", schema, re.M)
    # The stale claim that every arm gets all four must not come back.
    assert "Defaulting every arm to all four is" not in schema



def test_no_private_name_crosses_a_generation():
    """The half that blocks the collapse, and it is closed.

    Five v4 names were imported by v5 through their underscore: `evidence.candidate_spans`,
    `diagnostic_lines` and `declares_identifier`, `focused_specs.prompt_hashes`, and
    `render_focused.SUBMISSION_CONTRACT`. Moving them was not available -- `candidate_spans`
    takes a `CandidateClaim` and a `ChangeGraph`, both still v4 schema types, so a shared home
    would have imported v4 -- but the underscore was the part that was wrong. A name two
    packages import is API, whatever file it sits in.

    What is left is intra-generation, where a private name is a real statement about scope.
    """

    generations = {name: prefixes for name, prefixes in GENERATIONS.items()}
    crossing = []
    for source, prefixes in generations.items():
        for path in _modules(prefixes):
            for module, name in _imports(path):
                if not name.startswith("_") or name.startswith("__"):
                    continue
                for target in generations:
                    if target != source and re.search(rf"pr_review_{target}\b", module):
                        crossing.append((str(path), module, name))
    assert crossing == [], (
        "private name(s) imported across a generation boundary:\n" +
        "\n".join(f"  {p}: {m}.{n}" for p, m, n in crossing))


def test_the_structural_guards_are_pointed_at_a_directory_that_exists():
    """A guard that globs a deleted directory finds nothing and passes.

    Three did after the merge -- `no_prior_generation`, `no_duplicate_helpers` and the task
    adapter's field check all still named `src/datasets/pr_review_v4`. Vacuous passes are
    worse than no test, because the suite reports them as coverage.
    """

    import re

    for name in ("test_pr_review_v4_no_prior_generation.py",
                 "test_pr_review_v4_no_duplicate_helpers.py"):
        source = Path("tests/datasets") / name
        for match in re.finditer(r'Path\("(src/[^"]+)"\)', source.read_text(encoding="utf-8")):
            assert Path(match.group(1)).is_dir(), f"{name} globs {match.group(1)}, which is gone"
