"""Keep the shared helpers shared.

Twenty-two copies of `_load`, seventeen of `_display`, six byte-identical `_git_state`,
and eight `_artifact` builders accumulated because each new module copied its neighbour.
That is how the two sealing conventions silently diverged (`io.sealed_from_payload` vs
`io.sealed_model`), which is a hashing bug waiting to happen in a project whose claims
rest on artifact hashes. These assertions make the next copy fail loudly.
"""

import ast
from pathlib import Path

PACKAGE = Path("src/datasets/pr_review_v4")

#: Helper name -> the primitive that replaced it.
CONSOLIDATED = {
    "_load": "io.load_jsonl",
    "_display": "io.display_path",
    "_display_path": "io.display_path",
    "_git_state": "io.git_state",
}

#: Deliberate exceptions, each for a reason that would be a bug to "fix" mechanically.
ALLOWED = {
    # A different function that merely shares the name: it builds an EvidenceArtifact,
    # not an ArtifactRef.
    ("evidence.py", "_artifact"),
    # Takes `schema` before `role`; renaming it onto releases.artifact_ref would
    # transpose those fields in a frozen manifest.
    ("phase9_fixed_orchestration.py", "_artifact_ref"),
}


def _defined_functions(path: Path):
    tree = ast.parse(path.read_text())
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _package_sources():
    return sorted(
        path for path in PACKAGE.rglob("*.py")
        if "legacy" not in path.relative_to(PACKAGE).parts
    )


def test_consolidated_helpers_are_not_redefined_locally():
    offenders = {}
    for path in _package_sources():
        hits = sorted(_defined_functions(path) & set(CONSOLIDATED))
        if hits:
            offenders[path.name] = {name: CONSOLIDATED[name] for name in hits}
    assert offenders == {}, (
        f"locally redefined shared helpers: {offenders}. Import the primitive instead."
    )


def test_artifact_ref_builders_are_not_reintroduced():
    offenders = {}
    for path in _package_sources():
        hits = sorted(
            name for name in _defined_functions(path)
            if name in {"_artifact", "_artifact_ref"}
            and (path.name, name) not in ALLOWED
        )
        if hits:
            offenders[path.name] = hits
    assert offenders == {}, (
        f"new ArtifactRef builders: {offenders}. Use releases.artifact_ref, or add an "
        f"entry to ALLOWED here explaining why the signature genuinely differs."
    )


def test_the_two_sealing_conventions_are_the_only_ones():
    """Sealing must go through io, so a third convention cannot appear unnoticed."""

    offenders = {}
    for path in _package_sources():
        if path.name == "io.py":
            continue
        hits = sorted(
            name for name in _defined_functions(path)
            if name in {"_sealed", "_method"}
        )
        if hits:
            offenders[path.name] = hits
    assert offenders == {}, (
        f"local record-sealing helpers: {offenders}. Use io.sealed_from_payload or "
        "io.sealed_model — they hash different things and are not interchangeable."
    )
