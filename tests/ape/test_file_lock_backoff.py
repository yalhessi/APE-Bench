"""The file lock's retry backoff must not overflow on a long wait.

`_sync_acquire_lock` polled with `min(0.05 * (2 ** attempt), 3.0)`, which raises OverflowError once
`attempt` passes 1,024: about 51 minutes behind other holders at 3s a retry. A base build queued
behind a shared cache lock hit it on 2026-09-29, and the caller retried from zero.
"""

from __future__ import annotations

import fcntl
import os
import time

import pytest

from ape.utils import file_ops


def test_the_backoff_doubles_from_50ms_and_caps_at_3s_for_any_attempt():
    assert file_ops._lock_backoff(0) == 0.05
    assert file_ops._lock_backoff(3) == 0.4
    assert file_ops._lock_backoff(6) == 3.0
    assert file_ops._lock_backoff(5000) == 3.0


def test_a_wait_past_1024_attempts_times_out_instead_of_overflowing(tmp_path, monkeypatch):
    path = tmp_path / "held.lock"
    path.touch()
    holder = os.open(path, os.O_RDWR)
    fcntl.flock(holder, fcntl.LOCK_EX)    # a second open file description conflicts, as another process's would
    clock = {"now": 0.0}

    def fake_time():
        clock["now"] += 0.001             # 2,000 polls before a 2s timeout: far past attempt 1,024
        return clock["now"]

    monkeypatch.setattr(time, "time", fake_time)
    monkeypatch.setattr(time, "sleep", lambda _seconds: None)
    try:
        with pytest.raises(TimeoutError):
            file_ops._sync_acquire_lock(path, timeout=2.0, shared=False, blocking=True)
    finally:
        fcntl.flock(holder, fcntl.LOCK_UN)
        os.close(holder)
