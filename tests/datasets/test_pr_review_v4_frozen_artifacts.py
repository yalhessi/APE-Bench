"""Standing integrity gate over frozen v4 research artifacts.

Every reported number traces to an immutable artifact, so any refactor must be able to
prove it changed none of them. This test is the proof, and it is deliberately blunt:
it re-hashes everything and fails on the first byte of drift.
"""

from src.mathlib_review.release.verify_frozen import (
    LOCK_PATH,
    verify_lock,
    verify_manifests,
)


def test_every_declared_artifact_reference_still_hashes_correctly():
    failures, checked = verify_manifests()
    assert checked > 400, f"expected the manifest sweep to find artifacts, checked only {checked}"
    assert failures == [], f"frozen artifact drift in declared manifest references: {failures[:5]}"


def test_locked_files_are_unchanged_and_lock_covers_the_frozen_roots():
    assert LOCK_PATH.is_file(), (
        f"{LOCK_PATH} is missing; run "
        "`python -m src.mathlib_review.release.verify_frozen build-lock`"
    )
    failures, unlocked, checked = verify_lock()
    assert checked > 900, f"lock covers only {checked} files; expected the full frozen corpus"
    assert failures == [], f"frozen artifact drift against FROZEN.lock: {failures[:5]}"
    # New artifacts are normal progress, but they must be sealed deliberately rather
    # than accumulating unnoticed — rebuild the lock when adding results.
    assert unlocked == [], (
        f"{len(unlocked)} frozen-root files are not in FROZEN.lock: {unlocked[:5]}. "
        "Re-run `verify_frozen build-lock` to seal them."
    )


def test_the_v2_roster_stays_where_nine_frozen_manifests_say_it_is():
    """An input living inside a code package, which cannot be moved out of it.

    `src/datasets/pr_review_v2/data/mathlib_roster.txt` is the wrong place for data and it is
    where nine frozen release manifests under `inputs/pr_review_v4/` declare it, by path, with
    a hash. That root is frozen, so the manifests cannot be rewritten, so the file cannot be
    relocated. Moving it to `inputs/pr_review_v2/` was tried and nine manifests reported it
    missing.

    The consequence reaches past the file: **deleting `src/datasets/pr_review_v2/` breaks the
    frozen-artifact gate for every v4 release.** Whatever happens to v2's code, this path has
    to survive, and that is a constraint on the collapse rather than a preference about it.
    """

    from pathlib import Path

    roster = Path("src/datasets/pr_review_v2/data/mathlib_roster.txt")
    assert roster.is_file(), "moved; nine frozen manifests declare it here"

    declaring = [
        manifest for manifest in sorted(Path("inputs/pr_review_v4/releases").glob("*/manifest.json"))
        if str(roster) in manifest.read_text(encoding="utf-8")
    ]
    assert len(declaring) >= 5, (
        f"only {len(declaring)} manifests reference the roster; if that reached zero the file "
        "could finally move, and this test should be deleted rather than relaxed")
