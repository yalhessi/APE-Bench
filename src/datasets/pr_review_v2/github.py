"""
Minimal GitHub client for the v2 collector: REST (works unauthenticated for
small smoke tests) plus optional GraphQL (requires a token; used only for
enrichment — thread resolution and body edit history).
"""

import os
import time
from typing import Any, Dict, Iterator, List, Optional

import httpx

API_ROOT = "https://api.github.com"
TIMELINE_ACCEPT = "application/vnd.github+json"


class GitHubError(RuntimeError):
    pass


class RateLimitError(GitHubError):
    pass


class GitHubClient:
    def __init__(
        self,
        token: Optional[str],
        *,
        timeout_seconds: float = 30.0,
        request_interval_seconds: float = 0.0,
        max_retries: int = 5,
        retry_backoff: float = 2.0,
        logger=None,
    ):
        self.token = token or os.environ.get("GITHUB_TOKEN") or None
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "ape-bench-pr-review-v2",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        self._client = httpx.Client(headers=headers, timeout=timeout_seconds)
        self._interval = max(0.0, request_interval_seconds)
        self._max_retries = max(0, max_retries)
        self._retry_backoff = max(0.0, retry_backoff)
        self._logger = logger

    @property
    def authenticated(self) -> bool:
        return self.token is not None

    def close(self) -> None:
        self._client.close()

    def _backoff_sleep(self, attempt: int, reason: str, retry_after: Optional[str] = None) -> None:
        delay = self._retry_backoff * (2 ** attempt)
        if retry_after:
            try:
                delay = max(delay, float(retry_after))
            except ValueError:
                pass
        delay = min(delay, 60.0)
        if self._logger:
            self._logger.warning("GitHub %s; retry %d in %.0fs", reason, attempt + 1, delay)
        time.sleep(delay)

    def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        # Retry transient failures (5xx, network/timeout) with exponential backoff so one 502 does
        # not kill a long paginated collection. 403/429 stay a RateLimitError (caller's concern).
        for attempt in range(self._max_retries + 1):
            try:
                response = self._client.request(method, url, **kwargs)
            except httpx.TransportError as exc:
                if attempt >= self._max_retries:
                    raise
                self._backoff_sleep(attempt, f"transport error ({type(exc).__name__})")
                continue
            if self._interval:
                time.sleep(self._interval)
            if response.status_code in {403, 429}:
                remaining = response.headers.get("X-RateLimit-Remaining")
                reset_at = response.headers.get("X-RateLimit-Reset")
                raise RateLimitError(
                    f"GitHub rate limit (status={response.status_code}, remaining={remaining}, reset={reset_at})"
                )
            if response.status_code in {500, 502, 503, 504} and attempt < self._max_retries:
                self._backoff_sleep(attempt, f"HTTP {response.status_code}",
                                    response.headers.get("Retry-After"))
                continue
            response.raise_for_status()
            return response
        # unreachable: loop either returns or raises
        raise GitHubError(f"exhausted retries for {method} {url}")

    def get_json(self, path: str, *, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request("GET", f"{API_ROOT}{path}", params=params).json()

    def paginate(
        self,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        per_page: int = 100,
        max_pages: int = 50,
    ) -> Iterator[Any]:
        page_params = dict(params or {})
        page_params["per_page"] = per_page
        url: Optional[str] = f"{API_ROOT}{path}"
        pages = 0
        while url and pages < max_pages:
            response = self._request("GET", url, params=page_params if pages == 0 else None)
            payload = response.json()
            if isinstance(payload, dict):  # search API wraps items
                payload = payload.get("items", [])
            yield from payload
            url = response.links.get("next", {}).get("url")
            pages += 1

    def paginate_all(self, path: str, **kwargs) -> List[Any]:
        return list(self.paginate(path, **kwargs))

    def graphql(self, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        if not self.authenticated:
            raise GitHubError("GraphQL requires an authenticated client")
        response = self._request(
            "POST", f"{API_ROOT}/graphql", json={"query": query, "variables": variables}
        )
        payload = response.json()
        if payload.get("errors"):
            raise GitHubError(f"GraphQL errors: {payload['errors']}")
        return payload["data"]
