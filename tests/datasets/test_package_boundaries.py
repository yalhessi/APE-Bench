"""Boundaries, measured so they cannot get worse.

Mapping the tree once turned up the coupling that made one experiment touch thirteen source
files across six packages: 97 names imported from v4 into v5, **backward** edges where v4
imported v5, 42 private cross-module imports, and a shared review base living inside the
oldest generation so that a v5-only observation changed the tool contract for every v2 checker.

There is one review pipeline now (`src/mathlib_review/`) and one review task package
(`ape/tasks/lean_tasks/formal_math/review/`). **v2 is the only thing left carrying a
generation name**, which is why the cross-generation checks below have little left to compare:
that is the result, not a gap in the test. They stay because they are cheap and because the
next thing that reintroduces a generation should fail loudly.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

SRC = Path("src")

#: What still carries a generation name. v4 and v5 are gone from both layers: the pipeline is
#: `src/mathlib_review/`, the tasks are `formal_math/review/`.
GENERATIONS = {
    "v2": ("src/datasets/pr_review_v2",
           "src/ape/tasks/lean_tasks/formal_math/pr_review_v2"),
}

#: Where the review system lives now, for the checks that are about it rather than about
#: what it replaced.
PIPELINE = Path("src/mathlib_review")
TASKS = Path("src/ape/tasks/lean_tasks/formal_math/review")


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


def test_the_review_system_does_not_import_v2():
    """13 backward edges, then 4, then 0 -- and now the question has changed shape.

    There is no later generation for an older one to import, so what is left to check is the
    direction between the review system and the one package still carrying a generation name.
    It is one-way: `mathlib_review` and `formal_math/review` import nothing from v2, and v2
    imports the shared primitives (`model_output.extract_json_object`, `corpus.hunk_code` and
    `corpus.eval_pr_numbers`) from them.

    That is the right direction. v2 depending on a shared primitive is ordinary; the review
    system depending on v2 would mean v2 cannot be deleted.
    """

    offenders = []
    for root in (PIPELINE, TASKS):
        for path in sorted(root.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            for module, name in _imports(path):
                if re.search(r"pr_review_v2\b", module):
                    offenders.append((str(path), module, name))
    assert offenders == [], (
        "the review system imports v2, which is what would stop v2 being deletable:\n" +
        "\n".join(f"  {p}: {m}.{n}" for p, m, n in offenders))


def test_v2_reaches_forward_for_the_shared_primitives():
    """The other half, and it is what makes the previous test meaningful rather than vacuous:
    the two packages *do* share code, and every edge runs the same way."""

    edges = [
        (str(path), module)
        for path in _modules(GENERATIONS["v2"])
        for module, _name in _imports(path)
        if module.startswith("src.mathlib_review")
    ]
    assert edges, "v2 shares nothing, so the direction test proves nothing"


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

    It is `review/base.py` now -- inside the task package, because `ape/tasks/__init__.py`
    imports every task package eagerly and a `BaseLeanTask` subclass outside that tree cannot
    import `ape.tasks.base` without a cycle. That is the framework's layout saying where task
    classes go.
    """

    assert (TASKS / "base.py").is_file()
    for gone in ("src/ape/tasks/lean_tasks/formal_math/pr_review_v2/base.py",
                 "src/ape/tasks/lean_tasks/formal_math/review_task.py"):
        assert not Path(gone).exists(), f"{gone} came back"

    # v2 still inherits it, from its new home rather than from inside itself.
    importers = {
        str(path) for path in _modules(GENERATIONS["v2"])
        for module, _name in _imports(path)
        if module.endswith("formal_math.review.base")
    }
    assert importers, "v2 no longer inherits the shared base"


def test_the_generation_packages_are_gone():
    """The collapse, asserted rather than described. Both layers: the pipeline packages and
    the task packages."""

    for gone in ("src/datasets/pr_review_v4", "src/datasets/pr_review_v5",
                 "src/ape/tasks/lean_tasks/formal_math/pr_review_v4",
                 "src/ape/tasks/lean_tasks/formal_math/pr_review_v5"):
        assert not Path(gone).exists(), f"{gone} came back"
    assert PIPELINE.is_dir() and TASKS.is_dir()


def test_tier_multipliers_has_exactly_one_definition():
    """It was defined verbatim in two packages with neither importing the other, so the task
    layer could price jobs differently from the plan that budgeted them."""

    definitions = [
        str(path) for path in SRC.rglob("*.py")
        if "__pycache__" not in path.parts
        and re.search(r"^TIER_MULTIPLIERS\s*=", path.read_text(encoding="utf-8"), re.M)
    ]
    assert definitions == ["src/mathlib_review/schema/review.py"], definitions


def test_the_tactic_vocabulary_has_exactly_one_definition():
    """Three hand-written tactic keyword lists already exist in this tree and they disagree.

    `datasets/taxonomy/ape_bench_parser_taxonomy.py` counts ten families for ape_bench's edit
    taxonomy and `agenda/census.py` lists twenty names for the agenda's "manual tactic chain"
    signal (its own docstring: "deliberately crude"). Those answer different questions for
    different consumers and are left alone. What must not happen is a fourth: the list used to
    classify *agent queries* and the list used to classify *Mathlib proofs* have to be the same
    list, or a finding about one cannot be compared with a measurement of the other.
    """

    definitions = [
        str(path) for path in SRC.rglob("*.py")
        if "__pycache__" not in path.parts
        and re.search(r"^TACTIC_VOCABULARY\s*=", path.read_text(encoding="utf-8"), re.M)
    ]
    assert definitions == ["src/mathlib_review/tactics.py"], definitions


def test_the_wide_tactic_vocabulary_is_a_superset_of_the_strict_one():
    """The strict/wide pair exists so a result cannot rest on where the line was drawn. If the
    wide list ever stopped containing the strict one, "survives widening" would mean nothing."""

    from src.mathlib_review.tactics import TACTIC_VOCABULARY, WIDE_TACTIC_VOCABULARY

    assert set(TACTIC_VOCABULARY) < set(WIDE_TACTIC_VOCABULARY)


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
