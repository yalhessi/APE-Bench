"""A renderer bump is a new release, and carried artifacts must be copied, not re-serialized.

`renderer_version` sits inside the work-unit identity payload, so `work_unit_id` changes
with it. Rewriting a release in place would break every `wu:…` reference in its run plans,
candidate files and sealed conditions at once.

The carry path had a real bug worth pinning: raw JSONL lines handed to `jsonl_bytes` get
JSON-encoded *as strings*, producing `"{\\"action\\":...}"` and silently corrupting gold.
Only byte copying copies.
"""

from __future__ import annotations

from pathlib import Path

from src.datasets.pr_review_v4.io import jsonl_bytes
from src.datasets.pr_review_v4.releases import ArtifactSpec, write_artifacts

OLD = Path("inputs/pr_review_v4/releases/dev-medium-0.1.0")
NEW = Path("inputs/pr_review_v4/releases/dev-medium-0.3.0")

CARRIED = [
    "source/events.jsonl",
    "input/episodes.jsonl",
    "derived/change_graphs.jsonl",
    "gold/judgments.jsonl",
    "gold/intervention_views.jsonl",
    "gold/pilot_cases.jsonl",
    "gold/outcome_observations.jsonl",
    "gold/episode_boundaries.jsonl",
]


def test_every_carried_artifact_is_byte_identical_to_its_parent():
    """Gold and episodes are the same data; a re-render must not be a chance for them to move."""

    for relative in CARRIED:
        assert (OLD / relative).read_bytes() == (NEW / relative).read_bytes(), relative


def test_only_the_prompt_artifacts_were_rebuilt():
    for relative in ("derived/work_units.jsonl", "derived/rendered_prompts.jsonl"):
        assert (OLD / relative).read_bytes() != (NEW / relative).read_bytes(), relative


def test_raw_bytes_round_trip_exactly(tmp_path):
    """The bug: `jsonl_bytes` on raw lines encodes each line as a JSON *string*."""

    payload = b'{"a": 1}\n{"a": 2}\n'
    refs = write_artifacts(tmp_path, [ArtifactSpec("x.jsonl", raw_bytes=payload)])
    assert (tmp_path / "x.jsonl").read_bytes() == payload
    assert refs[0].records == 2

    corrupted = jsonl_bytes([line for line in payload.decode().splitlines() if line])
    assert corrupted != payload, "this is the failure mode the raw path exists to avoid"


def test_the_new_release_asks_for_issue_kind_and_records_target_paths():
    from src.datasets.pr_review_v4.io import load_jsonl
    from src.datasets.pr_review_v4.schema import RenderedPrompt, ReviewWorkUnit

    prompts = load_jsonl(NEW / "derived/rendered_prompts.jsonl", RenderedPrompt)
    units = load_jsonl(NEW / "derived/work_units.jsonl", ReviewWorkUnit)
    assert all(item.renderer_version == "candidate-prompt/12" for item in prompts)
    assert all("issue_kind" in item.system_prompt for item in prompts)
    assert all(item.paths_by_change for item in units)


def test_the_evaluation_denominator_is_unchanged():
    """Gold is carried, so the 40 included obligations must survive the bump exactly."""

    from src.datasets.pr_review_v4.io import load_jsonl
    from src.datasets.pr_review_v4.schema import InterventionView, JudgmentNode

    def included(release):
        views = load_jsonl(release / "gold/intervention_views.jsonl", InterventionView)
        judgments = load_jsonl(release / "gold/judgments.jsonl", JudgmentNode)
        eligible = {oid for view in views if view.evaluation_eligibility == "included"
                    for oid in view.obligation_ids}
        return {o.obligation_id for j in judgments for o in j.obligations
                if o.obligation_id in eligible}

    assert included(NEW) == included(OLD)
    assert len(included(NEW)) == 40
