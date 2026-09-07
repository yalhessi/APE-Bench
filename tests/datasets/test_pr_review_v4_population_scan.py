"""The naming population scan must be supplied, shared, and refused when it is a sample.

Two separate defects meet here.

**It was never supplied.** `collect_candidate` took `naming_population_scan=None` and its one
caller never passed it, so `verify_naming_convention` abstained on every naming claim in
production regardless of merit — 5 of 30 candidates on the 4-PR `/12` smoke.

**Supplying the obvious thing would have been worse.** The review workspaces materialize the
full directory tree but only the files a task touches: measured at 59, 81, 113 and 229 `.lean`
files against Mathlib's ~6000, with `Mathlib.lean` itself truncated to three imports. A scan
of ~2% of the corpus is not merely thin — 30 subjects across those four workspaces still
cleared `MIN_SUPPORT`, so it would have published sampling artifacts as repository
measurements, at a tier that outranks every lexical rule in the merge.

So the scan is wired in *and* guarded, and the guard's message distinguishes "the corpus could
not be read" from "the corpus shows no norm" — only the second is a fact about the name.
"""

from pathlib import Path

import pytest

from src.mathlib_review.evidence.evidence import LazyPopulationScan
from src.mathlib_review.evidence.operators.naming_norm import (
    MIN_CORPUS_FILES,
    PopulationScan,
    SubjectPopulation,
)


def _scan(parsed_files: int, subjects=None) -> PopulationScan:
    return PopulationScan(
        by_subject=subjects or {},
        all_fullnames=set(),
        parsed_files=parsed_files,
        parse_failures=[],
    )


def test_a_partial_checkout_is_not_a_snapshot():
    assert not _scan(81).is_representative()
    assert not _scan(MIN_CORPUS_FILES - 1).is_representative()
    assert _scan(MIN_CORPUS_FILES).is_representative()


def test_the_evidence_path_refuses_an_unrepresentative_scan(monkeypatch):
    """Built, measured, then discarded — the verifier must see no scan rather than a sample."""

    import src.mathlib_review.evidence.operators.naming_norm as naming_norm

    sparse = _scan(81, {"encard": SubjectPopulation("encard", {"encard": 40}, 40)})
    monkeypatch.setattr(naming_norm, "scan_population", lambda *_a, **_k: sparse)

    lazy = LazyPopulationScan(Path("/nonexistent-but-unused"), {})
    assert lazy.available() is False
    assert lazy.population("encard") is None, (
        "a sample must not answer population questions; it clears MIN_SUPPORT by accident"
    )


def test_a_full_scan_is_used(monkeypatch):
    import src.mathlib_review.evidence.operators.naming_norm as naming_norm

    population = SubjectPopulation("encard", {"encard": 87, "card": 4}, 91)
    full = _scan(6000, {"encard": population})
    monkeypatch.setattr(naming_norm, "scan_population", lambda *_a, **_k: full)

    lazy = LazyPopulationScan(Path("/nonexistent-but-unused"), {})
    assert lazy.available() is True
    assert lazy.population("encard") is population


def test_the_scan_is_built_once_per_workspace(monkeypatch):
    """It is a full parse of the source tree; per-candidate rebuilds would dominate the run."""

    import src.mathlib_review.evidence.operators.naming_norm as naming_norm

    calls = []

    def _counting(workspace, _sha):
        calls.append(str(workspace))
        return _scan(6000)

    monkeypatch.setattr(naming_norm, "scan_population", _counting)
    cache = {}
    for _ in range(5):
        LazyPopulationScan(Path("/workspace-a"), cache).population("x")
    for _ in range(3):
        LazyPopulationScan(Path("/workspace-b"), cache).population("x")
    assert len(calls) == 2, f"expected one scan per workspace, got {calls}"


def test_an_unbuildable_scan_abstains_with_its_own_reason(monkeypatch):
    """Not "the corpus shows no norm" — that would report a broken workspace as evidence."""

    import src.mathlib_review.evidence.operators.naming_norm as naming_norm
    from src.mathlib_review.evidence.verifiers import verify_naming_convention

    monkeypatch.setattr(
        naming_norm, "scan_population",
        lambda *_a, **_k: (_ for _ in ()).throw(FileNotFoundError("no Mathlib")),
    )

    class _Candidate:
        issue_kind = "naming_convention_violation"
        spec_id = None
        claim = "the name is wrong"
        requested_change = "rename it"
        proposed_edit = None

    class _Target:
        reviewed_code = "theorem Set.encard_foo (s : Set α) : s.encard = 0 := by simp"
        base_code = None

    result = verify_naming_convention(
        _Candidate(), _Target(),
        population_scan=LazyPopulationScan(Path("/nonexistent"), {}),
    )
    assert result.verdict == "abstain"
    assert "could not be built" in result.detail or "no resolvable subject" in result.detail


def test_the_caller_actually_passes_a_scan():
    """The whole defect was a parameter nobody filled; assert the wiring, not the signature."""

    import ast
    import inspect

    from src.mathlib_review.evidence import evidence

    tree = ast.parse(inspect.getsource(evidence))
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "collect_candidate"):
            passed = len(node.args) + len(node.keywords)
            assert passed >= 7, (
                "collect_candidate is called without a population scan; naming claims will "
                "abstain in production no matter what they say"
            )
            return
    pytest.fail("no call to collect_candidate found in evidence.py")


def test_the_population_comes_from_the_commit_cache_not_the_run_workspace():
    """The complete trees already exist; the fix is reading the right one, not copying more.

    `RestoreManager` keeps one compiled checkout per commit under `<repo>/workspaces/<sha>`,
    shared across runs. Run workspaces are partial by design — the runtime hardlinks the
    unmodified tree and materializes on demand — so the corpus measurement must not read from
    them. This asserts the resolver prefers the cache and refuses anything else.
    """

    from src.mathlib_review.evidence.evidence import snapshot_workspace

    assert snapshot_workspace(None) is None
    assert snapshot_workspace("not-a-real-commit-sha") is None


def test_a_cached_snapshot_resolves_to_a_complete_checkout():
    """Skipped when the cache is cold; when warm, it must be a corpus and not a sample."""

    from ape.toolkits.execute.lean.config import LeanVerifyToolConfig

    from src.mathlib_review.evidence.evidence import snapshot_workspace
    from src.mathlib_review.evidence.operators.naming_norm import MIN_CORPUS_FILES

    config = LeanVerifyToolConfig()
    repo_name, _url = config.resolve_repo(None)
    cache_dir = config.get_workspace_dir(repo_name)
    if not cache_dir.is_dir():
        pytest.skip("no Lean workspace cache on this machine")
    cached = [item for item in sorted(cache_dir.iterdir()) if (item / "Mathlib").is_dir()]
    if not cached:
        pytest.skip("the workspace cache holds no complete checkout")

    resolved = snapshot_workspace(cached[0].name)
    assert resolved == cached[0]
    modules = sum(1 for _ in (resolved / "Mathlib").rglob("*.lean"))
    assert modules >= MIN_CORPUS_FILES, (
        f"the cached checkout has {modules} modules, below the floor that separates a "
        "corpus from a partial run workspace"
    )
