"""v4 must not import earlier pipeline generations, and must name their data in one place.

v4's gold legitimately *descends* from v2/v3 artifacts, and twelve release manifests
record those files as provenance. That data edge is permanent and correct. What must not
exist is a *code* edge — it is what would keep v2/v3 un-archivable — or path literals
scattered across modules, which make the generation boundary invisible.
"""

import ast
import re
from pathlib import Path

import pytest

#: The merged package. This was `src/datasets/pr_review_v4`; globbing a
#: directory that no longer exists finds nothing and passes vacuously, which
#: is how a guard becomes decoration.
PACKAGE = Path("src/mathlib_review")
PRIOR_GENERATIONS = ("pr_review_v2", "pr_review_v3")
PRIOR_GENERATION_DATA = re.compile(r"(?:inputs|data)/pr_review_v[23]|pr_review_v2/data")


def _imported_modules(source: str):
    """Yield every module name imported by a source file, via the AST.

    Parsed rather than grepped so that prose mentioning a module name — as this
    package's own `paths.py` docstring does — is not mistaken for an import.
    """

    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module


def _package_sources():
    return sorted(
        path for path in PACKAGE.rglob("*.py")
        if "legacy_pipeline" not in path.relative_to(PACKAGE).parts
    )


def test_no_module_imports_a_prior_generation():
    offenders = {}
    for path in _package_sources():
        hits = sorted({
            module
            for module in _imported_modules(path.read_text())
            if any(generation in module for generation in PRIOR_GENERATIONS)
        })
        if hits:
            offenders[path.as_posix()] = hits
    assert offenders == {}, (
        f"v4 modules import a prior generation: {offenders}. Promote the symbol into "
        "this package (see io.extract_json_object) instead of reaching across."
    )


def test_prior_generation_data_paths_live_only_in_paths_module():
    """Checked against string literals in the code, not the file text.

    Scanning raw text flags a docstring that *cites* where an artifact lives -- the precedent
    index names the Stage-1 report it was calibrated against -- which is documentation doing
    its job, not a path being spelled twice. A guard that cannot tell those apart gets
    silenced rather than obeyed.
    """

    import ast

    offenders = {}
    for path in _package_sources():
        if path.name == "paths.py":
            continue
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:
            continue
        docstrings = {
            id(node) for parent in ast.walk(tree)
            if isinstance(parent, (ast.Module, ast.ClassDef, ast.FunctionDef,
                                   ast.AsyncFunctionDef))
            for node in [ast.get_docstring(parent, clean=False)] if node
        }
        hits = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if node.value in {ast.get_docstring(p, clean=False) for p in ast.walk(tree)
                                  if isinstance(p, (ast.Module, ast.ClassDef, ast.FunctionDef,
                                                    ast.AsyncFunctionDef))}:
                    continue
                hits |= set(PRIOR_GENERATION_DATA.findall(node.value))
        if hits:
            offenders[path.as_posix()] = sorted(hits)
    assert offenders == {}, (
        f"legacy-generation data paths spelled outside paths.py: {offenders}. "
        "Import the named constant from .paths instead."
    )


def test_paths_module_declares_the_legacy_inputs_that_manifests_record():
    from src.mathlib_review import paths

    for name in (
        "LEGACY_INTERVENTIONS_V5",
        "LEGACY_V2_ANNOTATED",
        "LEGACY_V2_BUNDLES",
        "LEGACY_V2_COMPARES",
        "LEGACY_V2_ROSTER",
    ):
        assert hasattr(paths, name), f"paths.py must declare {name}"


def test_assert_repo_root_rejects_a_foreign_working_directory(tmp_path, monkeypatch):
    from src.mathlib_review.paths import assert_repo_root

    assert_repo_root()  # the suite runs from the repo root
    monkeypatch.chdir(tmp_path)
    with pytest.raises(RuntimeError, match="repository root"):
        assert_repo_root()
