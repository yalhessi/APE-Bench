"""The ELM budget reader, against `GET /api/v1/costs` as ELM's OpenAPI spec documents it.

Recorded live on 2026-10-05: `{"usage":0.10094,"limit":500.00000,"currency":"GBP",
"asOf":"2026-10-05T00:00:00Z"}`. A bad key is a 401 with an OpenAI-shaped error body.
"""

from __future__ import annotations

import json
import os
from unittest import mock

import httpx
import pytest

from ape.llm_clients import elm_budget

RECORDED = {"usage": 0.10094, "limit": 500.0, "currency": "GBP", "asOf": "2026-10-05T00:00:00Z"}


def answering(status, body):
    sent = []

    def handler(request):
        sent.append(request)
        return httpx.Response(status, json=body)

    return httpx.MockTransport(handler), sent


def test_the_costs_are_read_with_the_key_from_the_documented_route():
    transport, sent = answering(200, RECORDED)
    costs = elm_budget.key_costs("elm-test-key", transport=transport)

    (request,) = sent
    assert str(request.url) == "https://elm.edina.ac.uk/api/v1/costs"
    assert request.method == "GET"
    assert request.headers["authorization"] == "Bearer elm-test-key"
    assert costs == {**RECORDED, "remaining": pytest.approx(499.89906)}


def test_the_line_gives_what_is_left_and_when_elm_last_synced():
    costs = {**RECORDED, "remaining": 499.89906}
    assert elm_budget.describe(costs) == (
        "ELM key: £499.90 left of £500.00 (spent £0.10, 0.0% used; "
        "as of 2026-10-05T00:00:00Z, later spend not included)")
    never = {"usage": 0, "limit": 0, "currency": "GBP", "asOf": None, "remaining": 0}
    assert elm_budget.describe(never).endswith("(spent £0.00; as of never synced, later spend not included)")


def test_a_refused_key_is_named_not_retried():
    transport, sent = answering(401, {"error": {"message": "Invalid authentication credentials",
                                                "type": "invalid_request_error", "code": 401}})
    with pytest.raises(elm_budget.ElmCostsError, match="refused the key"):
        elm_budget.key_costs("bad", transport=transport)
    assert len(sent) == 1


def test_an_answer_without_figures_is_refused():
    transport, _ = answering(200, {"error": "maintenance"})
    with pytest.raises(elm_budget.ElmCostsError, match="without numeric usage and limit"):
        elm_budget.key_costs("k", transport=transport)


def test_main_prints_one_line_or_json_and_never_the_key(capsys):
    transport, _ = answering(200, RECORDED)
    real = elm_budget.key_costs
    with mock.patch.dict(os.environ, {"ELM_API_KEY": "elm-secret-key"}), \
            mock.patch.object(elm_budget, "key_costs", lambda k: real(k, transport=transport)):
        assert elm_budget.main([]) == 0
        assert elm_budget.main(["--json"]) == 0
    line, as_json = capsys.readouterr().out.strip().split("\n")
    assert line.startswith("ELM key: £499.90 left of £500.00")
    assert json.loads(as_json)["remaining"] == pytest.approx(499.89906)
    assert "elm-secret-key" not in line + as_json


def test_main_without_a_key_says_which_variable(capsys):
    with mock.patch.dict(os.environ, {}, clear=True):
        assert elm_budget.main([]) == 2
    assert "ELM_API_KEY is not set" in capsys.readouterr().err
