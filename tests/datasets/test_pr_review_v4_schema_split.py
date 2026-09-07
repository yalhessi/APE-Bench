"""The schema is split by lifecycle, and the split has to stay a DAG.

It was one 2,187-line module holding 106 models and 22 type aliases, imported by 83 other
modules -- the single largest coupling point in the tree. Every importer depended on all of
it, so a change to any record risked all of them.

Split by lifecycle rather than by concern. Concern was the obvious cut and would have been
wrong: the concern taxonomy is itself unreliable (11 of the 19 gold obligations labelled
`style` are `grind` simplifications and `encard_` renames), so cutting the domain model along
it would bake an unstable vocabulary into the structure.

These tests keep three properties: the façade still resolves every name, the module graph has
no cycles, and gold stays out of generation.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

PACKAGE = Path("src/datasets/pr_review_v4/schema")
MODULES = ["base", "identity", "gold", "findings", "evidence", "opportunities",
           "runs", "scoring"]


def _internal_imports(module: str):
    text = (PACKAGE / f"{module}.py").read_text(encoding="utf-8")
    return {m.group(1) for m in re.finditer(r"^from \.(\w+) import", text, re.M)}


def test_every_lifecycle_module_exists():
    for module in MODULES:
        assert (PACKAGE / f"{module}.py").is_file(), module


def test_the_facade_still_resolves_every_name():
    """83 modules import `from .schema import X`. The split must not have moved any of them."""

    from src.datasets.pr_review_v4 import schema

    assert len(schema.__all__) == 129
    for name in schema.__all__:
        assert hasattr(schema, name), name


@pytest.mark.parametrize("name", [
    "StrictModel", "ChangeGraph", "ReviewWorkUnit", "RenderedPrompt",   # identity
    "JudgmentNode", "InterventionView", "PilotCase",                     # gold
    "CandidateClaim", "ReviewFinding", "ReviewIssue", "ARMS",            # findings
    "EvidenceArtifact", "EVIDENCE_TIERS", "evidence_rank",               # evidence
    "RunPlan", "RunManifest", "GenerationPlanV2",                        # runs
    "SemanticPair", "SemanticMatch",                                     # scoring
])
def test_load_bearing_names_are_importable_from_the_package(name):
    from src.datasets.pr_review_v4 import schema

    assert getattr(schema, name) is not None


def test_the_module_graph_is_acyclic():
    """A cycle here would make import order load-bearing and the split useless."""

    graph = {module: _internal_imports(module) for module in MODULES}
    state: dict = {}

    def visit(node, stack):
        if state.get(node) == "done":
            return
        if node in stack:
            raise AssertionError(f"import cycle: {' -> '.join(stack + [node])}")
        for nxt in sorted(graph.get(node, ())):
            visit(nxt, stack + [node])
        state[node] = "done"

    for module in MODULES:
        visit(module, [])


def test_base_depends_on_nothing_in_the_package():
    assert _internal_imports("base") == set()


def test_gold_is_not_imported_by_any_other_schema_module():
    """`gold` is the only gold-bearing module. Generation must not reach it, and the cheapest
    way for that to break silently is a sibling schema module importing it and being pulled in
    by something in the generation path."""

    for module in MODULES:
        if module == "gold":
            continue
        assert "gold" not in _internal_imports(module), module


def test_no_module_is_as_large_as_the_file_it_replaced():
    """The point was to break up a 2,187-line coupling point, not to move it."""

    sizes = {
        module: len((PACKAGE / f"{module}.py").read_text(encoding="utf-8").splitlines())
        for module in MODULES
    }
    assert max(sizes.values()) < 1000, sizes


def test_every_class_landed_in_exactly_one_module():
    """A model defined twice would make `isinstance` depend on which import path was used."""

    seen: dict = {}
    for module in MODULES:
        tree = ast.parse((PACKAGE / f"{module}.py").read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                assert node.name not in seen, (
                    f"{node.name} defined in both {seen.get(node.name)} and {module}")
                seen[node.name] = module
    assert len(seen) == 106
