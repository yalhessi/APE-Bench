"""Standing integrity gate over frozen v4 research artifacts.

Every reported number traces to an immutable artifact, so any refactor must be able to
prove it changed none of them. This test is the proof, and it is deliberately blunt:
it re-hashes everything and fails on the first byte of drift.
"""

from src.datasets.pr_review_v4.verify_frozen import (
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
        "`python -m src.datasets.pr_review_v4.verify_frozen build-lock`"
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
