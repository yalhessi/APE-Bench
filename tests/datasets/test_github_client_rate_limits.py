"""A rate limit is a wait, not a failure.

The December collection died on `RateLimitError` after 27 successful requests: GitHub meters the
search API at **30 requests per minute**, separately from the 5,000/hour core bucket, and the
client raised on the first 403 instead of waiting ~30 seconds for the window to reset. A `core`
window is an hour long, so the same bug would throw away an hour of collection.
"""

from __future__ import annotations

import logging
import time

import httpx
import pytest

from src.datasets.pr_review_v2.github import GitHubClient, RateLimitError


class FakeResponse:
    def __init__(self, status_code, headers=None, payload=None):
        self.status_code = status_code
        self.headers = headers or {}
        self._payload = payload if payload is not None else []
        self.links = {}

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("boom", request=None, response=None)


def _client(responses, monkeypatch, **kw):
    client = GitHubClient("token", logger=logging.getLogger("rate-test"), **kw)
    queue = list(responses)
    monkeypatch.setattr(client._client, "request", lambda *a, **k: queue.pop(0))
    slept = []
    monkeypatch.setattr(time, "sleep", slept.append)
    return client, slept


SEARCH_429 = FakeResponse(403, {
    "X-RateLimit-Remaining": "0", "X-RateLimit-Resource": "search",
    "X-RateLimit-Reset": str(int(time.time()) + 28),
})
OK = FakeResponse(200, {"X-RateLimit-Remaining": "29"}, [{"number": 1}])


def test_an_exhausted_window_is_waited_out_and_the_request_retried(monkeypatch, caplog):
    client, slept = _client([SEARCH_429, OK], monkeypatch)
    with caplog.at_level(logging.WARNING, logger="rate-test"):
        assert client.get_json("/search/issues") == [{"number": 1}]
    assert len(slept) == 1 and 27 <= slept[0] <= 31      # until the reset, plus a second
    assert "search rate limit" in caplog.text


def test_a_secondary_limits_retry_after_is_honoured(monkeypatch):
    secondary = FakeResponse(403, {"Retry-After": "60", "X-RateLimit-Remaining": "4000",
                                   "X-RateLimit-Resource": "core"})
    client, slept = _client([secondary, OK], monkeypatch)
    assert client.get_json("/repos/x/y/pulls") == [{"number": 1}]
    assert slept == [61.0]


def test_a_403_that_is_not_a_rate_limit_still_raises(monkeypatch):
    """A revoked token or a private repo answers 403 with quota left. Waiting an hour for that
    would hang the run."""

    forbidden = FakeResponse(403, {"X-RateLimit-Remaining": "4999", "X-RateLimit-Resource": "core"})
    client, slept = _client([forbidden], monkeypatch)
    with pytest.raises(RateLimitError) as excinfo:
        client.get_json("/repos/x/y/pulls")
    assert "remaining=4999" in str(excinfo.value)
    assert slept == []


def test_a_wait_longer_than_the_cap_raises_with_the_length_in_the_message(monkeypatch):
    far = FakeResponse(403, {"X-RateLimit-Remaining": "0", "X-RateLimit-Resource": "core",
                             "X-RateLimit-Reset": str(int(time.time()) + 7200)})
    client, slept = _client([far], monkeypatch, max_rate_limit_wait=900.0)
    with pytest.raises(RateLimitError) as excinfo:
        client.get_json("/repos/x/y/pulls")
    assert "would need to wait" in str(excinfo.value)
    assert slept == []


def test_retries_are_finite(monkeypatch):
    client, slept = _client([SEARCH_429] * 3, monkeypatch, max_retries=2)
    with pytest.raises(RateLimitError):
        client.get_json("/search/issues")
    assert len(slept) == 2
