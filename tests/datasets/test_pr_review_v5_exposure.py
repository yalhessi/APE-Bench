"""Library exposure: the half of importance the diff cannot see.

The properties that matter are about what the index refuses to claim. A reach of zero read
off a partial build is indistinguishable from a declaration nothing uses, and an index read
from a reviewed workspace is silently the *base* index — an attempt's `.lake` is a symlink
straight to the base snapshot's — so it would look PR-specific while being nothing of the
kind.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.datasets.pr_review_v5.exposure import (
    LazyExposureScan, exposed_changes, exposure_report,
)


def build(tmp_path, modules, *, sources=None):
    """A fake workspace carrying `.ilean` files for `modules`."""

    ws = tmp_path / "ws"
    lean = ws / ".lake" / "build" / "lib" / "lean"
    lean.mkdir(parents=True)
    src = ws / "Mathlib"
    src.mkdir(parents=True)
    for i in range(sources if sources is not None else len(modules)):
        (src / f"M{i}.lean").write_text("-- source\n")
    for name, payload in modules.items():
        (lean / f"{name}.ilean").write_text(json.dumps(payload))
    return ws


def module(name, decls=(), refs=(), imports=()):
    return {
        "module": name,
        "decls": {d: [0, 0, 0, 0, 0, 0, 0, 0] for d in decls},
        "references": {json.dumps({"c": {"m": "X", "n": r}}): {} for r in refs},
        "directImports": [[i, False, False, False] for i in imports],
        "version": 5,
    }


def test_reach_counts_referencing_modules_not_mentions(tmp_path):
    ws = build(tmp_path, {
        "A": module("A", decls=["N.core"]),
        "B": module("B", refs=["N.core"]),
        "C": module("C", refs=["N.core"]),
    })
    scan = LazyExposureScan(ws, {})
    assert scan.reach("N.core") == 2
    assert scan.reach("N.absent") == 0


def test_a_partial_build_abstains_rather_than_reporting_zero(tmp_path):
    """A reach of zero from a partial index is not a small number, it is a wrong one."""

    ws = build(tmp_path, {"A": module("A", decls=["N.core"])}, sources=50)
    scan = LazyExposureScan(ws, {})
    assert scan.available() is False
    assert scan.reach("N.core") is None
    assert exposed_changes({"change:1": "N.core"}, scan) == {}


def test_no_workspace_abstains(tmp_path):
    scan = LazyExposureScan(None, {})
    assert scan.available() is False
    assert exposure_report(scan, ["N.core"])["available"] is False


def test_reverse_import_reach_counts_everything_downstream(tmp_path):
    ws = build(tmp_path, {
        "Core": module("Core", decls=["N.core"]),
        "Mid": module("Mid", imports=["Core"]),
        "Leaf": module("Leaf", imports=["Mid"]),
        "Other": module("Other"),
    })
    built = LazyExposureScan(ws, {}).scan()
    assert built.reverse_import_reach("N.core") == 2
    assert built.reverse_import_reach("N.unknown") is None


def test_only_changes_at_or_above_the_floor_are_flagged(tmp_path):
    mods = {"D": module("D", decls=["N.hot", "N.cold"])}
    for i in range(6):
        mods[f"U{i}"] = module(f"U{i}", refs=["N.hot"])
    ws = build(tmp_path, mods)
    scan = LazyExposureScan(ws, {})
    flagged = exposed_changes({"change:hot": "N.hot", "change:cold": "N.cold"}, scan)
    assert set(flagged) == {"change:hot"}


def test_the_scan_is_built_once_per_snapshot(tmp_path):
    ws = build(tmp_path, {"A": module("A", decls=["N.core"])}, sources=1)
    cache = {}
    first = LazyExposureScan(ws, cache).scan()
    second = LazyExposureScan(ws, cache).scan()
    assert first is second
