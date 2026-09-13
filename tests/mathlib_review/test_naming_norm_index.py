"""The snapshot's norms, cached: a scan is ~36s and a naming question must not pay it.

`scan_population` walks Mathlib's 7,400 modules. That is fine once per base commit and not
fine once per arm invocation, so the part a naming question needs -- per-subject prefix counts
and the notation map -- is persisted per snapshot sha. Measured on the real 33337 base: cold
36.0s, warm 0.004s, 6,394 subjects, 319 notation operators, 430 KB.

`all_fullnames` is deliberately NOT persisted: 214k strings, wanted only by the collision
check in the executor, where the whole scan is already in hand.

Every path degrades rather than fails, because a naming question without counts is still a
question, while a run that dies because a snapshot is absent is not.
"""

from __future__ import annotations

from src.mathlib_review.evidence.operators.naming_norm import (
    NORM_INDEX_VERSION, norm_for, norm_index,
)


def _snapshot(root):
    mathlib = root / "snap" / "Mathlib"
    mathlib.mkdir(parents=True)
    (mathlib / "A.lean").write_text(
        'infixl:80 " \'\' " => Set.image\n'
        "theorem encard_one (s : Set α) : (f s).encard = 1 := by simp\n"
        "theorem encard_two (s : Set α) : (g s).encard = 2 := by simp\n"
        "theorem card_three (s : Set α) : (h s).encard = 3 := by simp\n")
    return root / "snap"


def test_the_index_records_counts_and_notation(tmp_path):
    index = norm_index(_snapshot(tmp_path), "sha1", tmp_path / "cache")
    assert index["version"] == NORM_INDEX_VERSION and index["snapshot_sha"] == "sha1"
    assert index["subjects"]["encard"] == {"encard": 2, "card": 1}
    assert index["notation"]["''"] == "image"
    assert "all_fullnames" not in index, "214k strings must not be persisted"


def test_the_second_call_reads_the_cache(tmp_path):
    snap = _snapshot(tmp_path)
    cache = tmp_path / "cache"
    first = norm_index(snap, "sha1", cache)
    assert (cache / "sha1.json").is_file()
    # Make the snapshot unreadable; a cached answer must still come back.
    (snap / "Mathlib" / "A.lean").unlink()
    assert norm_index(snap, "sha1", cache) == first


def test_a_missing_snapshot_degrades_to_none(tmp_path):
    assert norm_index(tmp_path / "absent", "sha9", tmp_path / "cache") is None


def test_build_if_missing_false_never_scans(tmp_path):
    """What a dry run passes: read a norm that exists, never spend 36s building one."""

    snap = _snapshot(tmp_path)
    cache = tmp_path / "cache"
    assert norm_index(snap, "sha1", cache, build_if_missing=False) is None
    assert not (cache / "sha1.json").exists()
    norm_index(snap, "sha1", cache)
    assert norm_index(snap, "sha1", cache, build_if_missing=False) is not None


def test_a_stale_version_is_rebuilt_not_trusted(tmp_path):
    import json
    snap, cache = _snapshot(tmp_path), tmp_path / "cache"
    cache.mkdir()
    (cache / "sha1.json").write_text(json.dumps({"version": "naming-norm-index/0", "subjects": {}}))
    assert norm_index(snap, "sha1", cache)["version"] == NORM_INDEX_VERSION


def test_a_population_is_rebuilt_from_the_index(tmp_path):
    index = norm_index(_snapshot(tmp_path), "sha1", tmp_path / "cache")
    population = norm_for(index, "encard")
    assert population.members == 3 and population.dominant_prefix == "encard"
    assert population.support == 2
    assert norm_for(index, "nosuchsubject") is None
    assert norm_for(None, "encard") is None
