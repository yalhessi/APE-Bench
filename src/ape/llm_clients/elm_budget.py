"""What is left of the ELM key's spend limit, as ELM reports it.

    ape/bin/python -m ape.llm_clients.elm_budget          # one line
    ape/bin/python -m ape.llm_clients.elm_budget --json   # ELM's figures plus `remaining`

ELM's proxy documents `GET /api/v1/costs` ("Get API key usage and spend limit", in its OpenAPI
spec at https://elm.edina.ac.uk/api-docs/elm-proxy-api.yaml, served by /swagger-ui/). It takes
the API key itself and answers `{usage, limit, currency, asOf}`. Both figures are pounds, so
the project's allocation is £500 (`limit: 500.0` on 2026-10-05), and `usage` is synced
periodically, not per call: `asOf` says when, and spend since then is not in it. The run
caps price calls at OpenAI's list rates in dollars, so they do not add up to this figure.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, Optional

import httpx

from .config import LLMConfig, LLMProvider, PROVIDER_KEY_ENV_VARS
from .providers.elm_provider import ElmProvider

COSTS_URL = ElmProvider.DEFAULT_BASE_URL.rsplit("/chat/completions", 1)[0] + "/costs"


class ElmCostsError(RuntimeError):
    """ELM did not answer with the key's costs, and why."""


def key_costs(api_key: str, *, transport: Optional[httpx.BaseTransport] = None) -> Dict[str, Any]:
    """ELM's `{usage, limit, currency, asOf}` for this key, with `remaining` added."""

    with httpx.Client(timeout=60, transport=transport, follow_redirects=False) as http:
        response = http.get(COSTS_URL, headers={"Authorization": f"Bearer {api_key}",
                                                "Accept": "application/json"})
    if response.status_code == 401:
        raise ElmCostsError("ELM refused the key (HTTP 401): ELM_API_KEY is missing, revoked or mistyped.")
    if response.status_code != 200:
        raise ElmCostsError(f"ELM answered HTTP {response.status_code} on /costs: {response.text[:300]}")
    costs = response.json()
    if not isinstance(costs.get("usage"), (int, float)) or not isinstance(costs.get("limit"), (int, float)):
        raise ElmCostsError(f"/costs answered without numeric usage and limit: {costs}")
    return {**costs, "remaining": costs["limit"] - costs["usage"]}


def describe(costs: Dict[str, Any]) -> str:
    symbol = {"GBP": "£"}.get(costs.get("currency"), f"{costs.get('currency', '')} ")
    used = f", {costs['usage'] / costs['limit']:.1%} used" if costs["limit"] else ""
    as_of = costs.get("asOf") or "never synced"
    return (f"ELM key: {symbol}{costs['remaining']:,.2f} left of {symbol}{costs['limit']:,.2f} "
            f"(spent {symbol}{costs['usage']:,.2f}{used}; as of {as_of}, later spend not included)")


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m ape.llm_clients.elm_budget",
                                     description="The ELM key's spend and remaining limit.")
    parser.add_argument("--json", action="store_true", help="print ELM's figures as JSON")
    args = parser.parse_args(argv)

    api_key = LLMConfig._resolve_api_key_from_environment(LLMProvider.ELM)
    if not api_key:
        print(f"{PROVIDER_KEY_ENV_VARS[LLMProvider.ELM][0]} is not set "
              "(source ~/.config/secrets/env.zsh in the same command).", file=sys.stderr)
        return 2
    try:
        costs = key_costs(api_key)
    except (ElmCostsError, httpx.HTTPError) as error:
        print(error, file=sys.stderr)
        return 2
    print(json.dumps(costs) if args.json else describe(costs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
