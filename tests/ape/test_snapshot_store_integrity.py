"""A base snapshot is all of the built workspace or nothing.

2026-09-24: the pilot build of mathlib4@1927b6e6 stored 58,256 of 58,259 files and reported success.
Among the three missing files was `Mathlib/Data/Set/Basic.olean`. Each failure was a rename whose
temporary source had vanished on the NFSv3 store, and each time the object was already present.
"""

from __future__ import annotations

import asyncio

import pytest

import ape.toolkits.execute.lean.core.storage as storage_module
from ape.toolkits.execute.lean.config import LeanVerifyToolConfig
from ape.toolkits.execute.lean.core.build_manager import BuildManager
from ape.toolkits.execute.lean.core.storage import ContentStore


def _config(tmp_path):
    return LeanVerifyToolConfig(base_dir=tmp_path, storage_dir=tmp_path / "storage",
                                repos_dir=tmp_path / "repos")


def _vanishing_rename(write_object: bool):
    """A rename whose source is gone; optionally another writer stored the object first."""

    async def replace(src, dst):
        if write_object:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(src.read_bytes())
        src.unlink()
        raise FileNotFoundError(2, "No such file or directory", str(src))

    return replace


def test_a_vanished_rename_with_the_object_present_is_a_store(tmp_path, monkeypatch):
    source = tmp_path / "Basic.olean"
    source.write_bytes(b"olean bytes")
    store = ContentStore(_config(tmp_path))
    monkeypatch.setattr(storage_module.aiofiles.os, "replace", _vanishing_rename(write_object=True))
    digest = asyncio.run(store.store_file(source))
    assert store._get_object_path(digest).read_bytes() == b"olean bytes"
    assert not list(store._get_object_path(digest).parent.glob(".*.tmp"))


def test_a_vanished_rename_with_no_object_still_fails(tmp_path, monkeypatch):
    source = tmp_path / "Basic.olean"
    source.write_bytes(b"olean bytes")
    store = ContentStore(_config(tmp_path))
    monkeypatch.setattr(storage_module.aiofiles.os, "replace", _vanishing_rename(write_object=False))
    with pytest.raises(FileNotFoundError):
        asyncio.run(store.store_file(source))


def _workspace(tmp_path):
    workspace = tmp_path / "ws"
    (workspace / ".lake/build/lib/lean/Mathlib").mkdir(parents=True)
    for name in ("A.olean", "B.olean", "C.olean"):
        (workspace / ".lake/build/lib/lean/Mathlib" / name).write_bytes(name.encode())
    return workspace


def _flaky_store(manager, fail_times):
    real = manager.content_store.store_file
    calls = {"n": 0}

    async def store_file(file_path, file_type="regular"):
        if file_path.name == "B.olean" and calls["n"] < fail_times:
            calls["n"] += 1
            raise OSError("transient")
        return await real(file_path, file_type)

    manager.content_store.store_file = store_file


def test_a_transient_store_failure_is_retried_and_the_snapshot_is_whole(tmp_path):
    manager = BuildManager(_config(tmp_path))
    _flaky_store(manager, fail_times=1)
    assert asyncio.run(manager._create_snapshot("c0ffee", _workspace(tmp_path))) == 3


def test_a_persistent_store_failure_refuses_the_snapshot(tmp_path):
    manager = BuildManager(_config(tmp_path))
    _flaky_store(manager, fail_times=99)
    with pytest.raises(RuntimeError, match="Create snapshot failed") as info:
        asyncio.run(manager._create_snapshot("c0ffee", _workspace(tmp_path)))
    assert "refusing a partial snapshot" in str(info.value.__cause__)
