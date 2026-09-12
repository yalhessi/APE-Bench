"""A rate limit is a wait, not a failure, and a 5xx that outlives the retries is a `GitHubError`.

The December collection died on `RateLimitError` after 27 successful requests: GitHub meters the
search API at **30 requests per minute**, separately from the 5,000/hour core bucket, and the
client raised on the first 403 instead of waiting ~30 seconds for the window to reset. A `core`
window is an hour long, so the same bug would throw away an hour of collection.

The September collection died differently: `/pulls/4197/comments` is a 1.2 MB page GitHub 502s
while generating, and the raw `httpx.HTTPStatusError` escaped every caller that guards an endpoint.
So whatever outlives the retries is a `GitHubHTTPError` -- a `GitHubError` -- and the caller defers
that endpoint. Retrying harder was tried and does not work: 242 s of backoff failed where 62 s had.
The budget therefore stays short, because giving up is now cheap and the collector pays the wait
once per dead endpoint.
"""

from __future__ import annotations

import logging
import time

import httpx
import pytest

from src.datasets.pr_review_v2.github import (
    GitHubClient, GitHubError, GitHubHTTPError, RateLimitError,
)


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


def search_429():
    """A search window that resets 28 seconds from now.

    Built per call, not once at import: as a module-level constant the window drained while
    the rest of the suite was collected, so the wait asserted below came out short in a full
    run (25.4s against a 27-31s band) and correct when the file ran on its own.
    """

    return FakeResponse(403, {
        "X-RateLimit-Remaining": "0", "X-RateLimit-Resource": "search",
        "X-RateLimit-Reset": str(int(time.time()) + 28),
    })

OK = FakeResponse(200, {"X-RateLimit-Remaining": "29"}, [{"number": 1}])


def test_an_exhausted_window_is_waited_out_and_the_request_retried(monkeypatch, caplog):
    client, slept = _client([search_429(), OK], monkeypatch)
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
    client, slept = _client([search_429()] * 3, monkeypatch, max_retries=2)
    with pytest.raises(RateLimitError):
        client.get_json("/search/issues")
    assert len(slept) == 2


# --- a 5xx that outlives the retries ---------------------------------------------------------

SERVER_ERROR = FakeResponse(502, {"X-RateLimit-Remaining": "4000"})


def test_a_transient_5xx_is_retried_and_never_reaches_the_caller(monkeypatch):
    client, slept = _client([SERVER_ERROR, SERVER_ERROR, OK], monkeypatch)
    assert client.get_json("/repos/x/y/pulls/4197/comments") == [{"number": 1}]
    assert slept == [2.0, 4.0]


def test_the_5xx_budget_stays_short_because_deferring_is_the_defence(monkeypatch):
    """Retrying harder is not the fix and this pins that: raising it to 242 s did not rescue
    4197, and a longer budget is paid *per dead endpoint* by a collection walking 32k PRs.
    The caller defers the endpoint instead, so giving up quickly is the cheap move."""

    client, slept = _client([SERVER_ERROR] * 6, monkeypatch)
    with pytest.raises(GitHubHTTPError):
        client.get_json("/repos/x/y/pulls/4197/comments")
    assert sum(slept) < 90


def test_a_persistent_5xx_raises_a_githuberror_carrying_the_status(monkeypatch):
    """Not `httpx.HTTPStatusError`: the collector guards one endpoint with `except GitHubError`,
    and a raw httpx exception walked straight through that guard and ended a 12-hour collection."""

    client, _ = _client([SERVER_ERROR] * 6, monkeypatch)
    with pytest.raises(GitHubError) as excinfo:
        client.get_json("/repos/x/y/pulls/4197/comments")
    assert isinstance(excinfo.value, GitHubHTTPError)
    assert excinfo.value.status_code == 502
    assert "502" in str(excinfo.value)


def test_a_404_raises_a_githuberror_without_retrying(monkeypatch):
    client, slept = _client([FakeResponse(404, {"X-RateLimit-Remaining": "4000"})], monkeypatch)
    with pytest.raises(GitHubHTTPError) as excinfo:
        client.get_json("/repos/x/y/pulls/999999")
    assert excinfo.value.status_code == 404
    assert slept == []


def test_a_transport_error_that_outlives_the_retries_is_also_a_githuberror(monkeypatch):
    client = GitHubClient("token", logger=logging.getLogger("rate-test"), max_retries=1)
    def boom(*a, **k):
        raise httpx.ConnectError("connection reset")
    monkeypatch.setattr(client._client, "request", boom)
    monkeypatch.setattr(time, "sleep", lambda s: None)
    with pytest.raises(GitHubError):
        client.get_json("/repos/x/y/pulls")


# --- the quota counter -------------------------------------------------------------------------

def _paged(n_pages):
    """n pages of 100, linked by `next` -- what a big PR's /files or /commits looks like."""
    pages = []
    for i in range(n_pages):
        r = FakeResponse(200, {"X-RateLimit-Remaining": "4000"}, [{"i": i}] * 100)
        r.links = {"next": {"url": f"https://api.github.com/next/{i+1}"}} if i < n_pages - 1 else {}
        pages.append(r)
    return pages


def test_every_page_counts_as_a_request(monkeypatch):
    """The under-count this replaces: tier 2 scored a `paginate_all` as one request no matter how
    many pages it pulled, so a quota estimate was optimistic exactly on the largest PRs."""

    client, _ = _client(_paged(4), monkeypatch)
    assert len(client.paginate_all("/repos/x/y/pulls/1/files", max_pages=None)) == 400
    assert client.request_count == 4


def test_a_retried_5xx_counts_every_attempt_because_github_meters_them(monkeypatch):
    client, _ = _client([SERVER_ERROR, SERVER_ERROR, OK], monkeypatch)
    client.get_json("/repos/x/y/pulls/1")
    assert client.request_count == 3


def test_a_rate_limit_wait_counts_the_rejected_request(monkeypatch):
    client, _ = _client([search_429(), OK], monkeypatch)
    client.get_json("/search/issues")
    assert client.request_count == 2
