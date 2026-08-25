"""Regression gates for the oracle evidence-sufficiency probe."""

from collections import Counter
from pathlib import Path

from src.datasets.pr_review_v4.oracle_evidence_probe import build_artifacts
from src.datasets.pr_review_v4.oracle_opportunities import ADJUDICATION_SYSTEM_PROMPT
from src.datasets.pr_review_v4.schema import (
    ChangeGraph,
    ReviewEpisodeInput,
    ReviewWorkUnit,
)


PILOT = Path("inputs/pr_review_v4/releases/dev-pilot-0.9.0")


def _load(relative, cls):
    return [
        cls.model_validate_json(line)
        for line in (PILOT / relative).read_text().splitlines()
        if line
    ]


def _artifacts():
    return build_artifacts(
        _load("derived/work_units.jsonl", ReviewWorkUnit),
        _load("derived/change_graphs.jsonl", ChangeGraph),
        _load("input/episodes.jsonl", ReviewEpisodeInput),
    )


def test_evidence_probe_is_two_calls_with_five_opportunities_per_arm():
    units, prompts, opportunities = _artifacts()
    assert len(units) == len(prompts) == 2
    assert Counter(item.selection_provenance for item in opportunities) == {
        "oracle_gold_targeted": 5,
        "matched_control": 5,
    }
    assert all(prompt.user_prompt.count("## Opportunity `") == 5 for prompt in prompts)
    assert all(prompt.system_prompt == ADJUDICATION_SYSTEM_PROMPT for prompt in prompts)
    assert all(prompt.renderer_version == "oracle-evidence-sufficiency/1" for prompt in prompts)


def test_intervention_packets_add_mechanical_or_quantitative_evidence():
    _units, _prompts, opportunities = _artifacts()
    intervention = [
        item for item in opportunities if item.selection_provenance == "oracle_gold_targeted"
    ]
    assert all(
        {evidence.kind for evidence in item.evidence}
        & {"mechanical_check", "quantitative_pattern"}
        for item in intervention
    )
    assert sum(
        evidence.kind == "mechanical_check"
        for item in intervention
        for evidence in item.evidence
    ) == 4
    assert sum(
        evidence.kind == "quantitative_pattern"
        for item in intervention
        for evidence in item.evidence
    ) == 2


def test_control_packets_receive_equally_explicit_negative_evidence():
    _units, _prompts, opportunities = _artifacts()
    controls = [item for item in opportunities if item.selection_provenance == "matched_control"]
    assert all(
        {evidence.kind for evidence in item.evidence}
        & {"mechanical_check", "quantitative_pattern"}
        for item in controls
    )
    assert any("semantic steps removed=0" in evidence.content
               for item in controls for evidence in item.evidence)
    assert any("Inconsistent facets=0" in evidence.content
               for item in controls for evidence in item.evidence)


def test_rendered_probe_discloses_no_comment_or_adoption_signal():
    _units, prompts, opportunities = _artifacts()
    rendered = "\n".join(prompt.user_prompt for prompt in prompts).lower()
    assert "maintainer comment" not in rendered
    assert "gold obligation" not in rendered
    assert "accepted later" not in rendered
    assert "post-review" not in rendered
    assert all(
        evidence.snapshot_sha
        for opportunity in opportunities
        for evidence in opportunity.evidence
    )
