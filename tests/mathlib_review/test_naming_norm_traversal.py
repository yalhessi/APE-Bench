"""The snapshot scan must see the whole snapshot, including through symlinks.

`scan_population` walked the tree with `Path.rglob`, which does not descend a symlinked
directory — and a review attempt's workspace is an overlay of symlinks into the shared base
with only the PR's own subtree materialised. So inside an attempt the scan saw one
neighbourhood of a complete tree and reported no sign of it: measured on the real 33337
reviewed workspace, `rglob` finds 66 `.lean` files where the tree holds 7,443.

That is why `MIN_CORPUS_FILES` exists. The floor was read at the time as "the workspace is a
partial checkout"; it was a traversal defect, the same one that blinded `content_search`
(commit `c14fa9b`). With the walk fixed the same workspace parses 7,443 files and
`is_representative()` is True, so the deterministic naming operator can run inside a review
attempt at all — which it never could before.

The floor stays: `Mathlib.lean` can itself be truncated, so there is no self-describing module
count to check a scan against.
"""

from __future__ import annotations

from src.mathlib_review.evidence.operators.naming_norm import MIN_CORPUS_FILES, scan_population


def _snapshot(root, *, files):
    """A base tree of `files` modules, and an overlay of symlinks into it with one real file."""

    base = root / "base" / "Mathlib"
    (base / "Area").mkdir(parents=True)
    for i in range(files):
        (base / "Area" / f"M{i}.lean").write_text(
            f"theorem encard_thing{i} (s : Set α) : (f s).encard = 0 := by simp\n")
    overlay = root / "overlay" / "Mathlib"
    overlay.mkdir(parents=True)
    (overlay / "Area").symlink_to(base / "Area")          # untouched area: a symlink
    (overlay / "Touched").mkdir()                          # the PR's own subtree: real
    (overlay / "Touched" / "Edited.lean").write_text(
        "theorem card_thing (s : Set α) : (f s).encard = 0 := by simp\n")
    return root / "base", root / "overlay"


def test_the_scan_descends_symlinked_directories(tmp_path):
    base, overlay = _snapshot(tmp_path, files=3)
    assert len(list((overlay / "Mathlib").rglob("*.lean"))) == 1, (
        "precondition: rglob sees only the materialised file")
    scan = scan_population(overlay, "overlay-sha")
    assert scan.parsed_files == 4, (
        f"the symlinked area must be scanned too, got {scan.parsed_files}")


def test_a_scan_that_saw_one_neighbourhood_is_not_representative(tmp_path):
    """The guard that stopped a 2% sample being published as a repository measurement."""

    base, overlay = _snapshot(tmp_path, files=3)
    assert not scan_population(overlay, "overlay-sha").is_representative()
    assert MIN_CORPUS_FILES == 1000


def test_the_overlay_counts_the_prs_own_declarations(tmp_path):
    """Why a norm must be scanned at the BASE, not in the reviewed tree: measured on 33337,
    subject `toLinearMap` has `coe_` at 7 in the base and 8 in the reviewed tree, because the
    PR's own new `coe_` declaration is there. A norm scanned in the reviewed tree would count
    the names it is judging."""

    base, overlay = _snapshot(tmp_path, files=3)
    at_base = scan_population(base, "base-sha").population("encard")
    at_overlay = scan_population(overlay, "overlay-sha").population("encard")
    assert at_base.prefix_counts.get("card", 0) == 0
    assert at_overlay.prefix_counts.get("card", 0) == 1, (
        "the PR's own declaration is present in the reviewed tree")
