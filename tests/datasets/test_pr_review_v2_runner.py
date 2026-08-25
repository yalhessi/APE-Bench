"""Unit tests for the v2 runner's prediction contract (prompt + parser). No network."""

import json

import pytest

from src.datasets.pr_review_v2.predictions import (
    build_user_prompt,
    parse_prediction_text,
)
from src.datasets.pr_review_v2.schema import (
    GoldBlock,
    InputBlock,
    Outcome,
    PRReviewV2Record,
    SliceFlags,
    ValidationBlock,
)


def make_record(**input_overrides) -> PRReviewV2Record:
    input_kwargs = dict(
        title="feat: add a lemma",
        description="Adds `Foo.bar`.",
        base_sha="base000",
        head_sha="c1",
        h0_resolution="review_commit_id",
        diff="diff --git a/Mathlib/A.lean b/Mathlib/A.lean\n+lemma foo : 1 = 1 := rfl",
    )
    input_kwargs.update(input_overrides)
    return PRReviewV2Record(
        repo="leanprover-community/mathlib4",
        pr_number=1,
        slices=SliceFlags(merged=True),
        input=InputBlock(**input_kwargs),
        gold=GoldBlock(verdict="APPROVED", comments=[], outcome=Outcome(merged=True)),
        validation=ValidationBlock(),
    )


VALID_PAYLOAD = {
    "merge_ready_as_is": False,
    "confidence": 0.7,
    "findings": [
        {
            "path": "Mathlib/A.lean",
            "line_start": 2,
            "line_end": 2,
            "severity": "blocking",
            "claim": "This duplicates an existing lemma.",
            "suggested_fix": None,
        },
        {
            "path": None,
            "line_start": None,
            "line_end": None,
            "severity": "advisory",
            "claim": "PR description could mention the motivation.",
        },
    ],
}


class TestPrompt:
    def test_contains_inputs_and_budget(self):
        record = make_record()
        prompt = build_user_prompt(record, budget=10)
        assert "feat: add a lemma" in prompt
        assert "lemma foo" in prompt
        assert "At most 10 findings" in prompt

    def test_empty_description_placeholder(self):
        prompt = build_user_prompt(make_record(description=""), budget=5)
        assert "(no description provided)" in prompt


class TestParser:
    def test_clean_json(self):
        merge_ready, confidence, findings = parse_prediction_text(
            json.dumps(VALID_PAYLOAD), budget=10
        )
        assert merge_ready is False
        assert confidence == 0.7
        assert len(findings) == 2
        assert findings[0].anchor.path == "Mathlib/A.lean"
        assert findings[1].anchor is None  # PR-level finding

    def test_fenced_json_with_prose(self):
        text = "Here is my review:\n```json\n" + json.dumps(VALID_PAYLOAD) + "\n```\nDone."
        merge_ready, _, findings = parse_prediction_text(text, budget=10)
        assert merge_ready is False
        assert len(findings) == 2

    def test_budget_truncates(self):
        payload = dict(VALID_PAYLOAD, findings=VALID_PAYLOAD["findings"] * 8)
        _, _, findings = parse_prediction_text(json.dumps(payload), budget=3)
        assert len(findings) == 3

    def test_invalid_severity_downgraded_and_empty_claims_dropped(self):
        payload = {
            "merge_ready_as_is": True,
            "findings": [
                {"path": "a.lean", "severity": "critical", "claim": "x"},
                {"path": "a.lean", "severity": "blocking", "claim": "  "},
            ],
        }
        merge_ready, confidence, findings = parse_prediction_text(json.dumps(payload), budget=10)
        assert merge_ready is True
        assert confidence is None
        assert len(findings) == 1
        assert findings[0].severity == "advisory"

    def test_no_json_raises(self):
        with pytest.raises(ValueError):
            parse_prediction_text("I think this PR looks fine.", budget=10)

    def test_nested_braces_in_claim(self):
        payload = dict(VALID_PAYLOAD)
        payload["findings"] = [
            {"path": "a.lean", "severity": "blocking", "claim": "use `{x | p x}` here"}
        ]
        _, _, findings = parse_prediction_text(json.dumps(payload), budget=10)
        assert "{x | p x}" in findings[0].claim
