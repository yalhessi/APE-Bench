"""Drive the real `submit_candidates` handler on real release data.

Nothing exercised this handler before, which is why a `/12` renderer change that read a
field the task model did not declare reached a paid run: every offline check passed, and
all 22 work units then crashed inside the tool with `AttributeError` *after* the agents had
done their review work. Contract tests on the prompt and on the schema cannot catch that —
only calling the tool can.

The handler is registered through an MCP decorator, so it is captured with a recording stub
rather than a live server. Work units are chosen with `submission_verification_policy ==
"none"` so no Lean toolchain is needed; the compile path has its own coverage.
"""

import asyncio
from pathlib import Path

import pytest

from src.datasets.pr_review_v4.io import load_jsonl
from src.datasets.pr_review_v4.schema import (
    RenderedPrompt,
    ReviewEpisodeInput,
    ReviewWorkUnit,
)
from src.datasets.pr_review_v4.task_adapter import build_candidate_task_data

RELEASE = Path("inputs/pr_review_v4/releases/dev-medium-0.3.0")


class _RecordingMCP:
    """Captures the functions a task registers, in place of a live MCP server."""

    def __init__(self):
        self.tools = {}

    def tool(self, *_args, **_kwargs):
        def decorator(function):
            self.tools[function.__name__] = function
            return function
        return decorator


def _handler_for(unit, episode, prompt):
    from ape.tasks.lean_tasks.formal_math.pr_review_v4.candidates import (
        LeanPRReviewV4CandidateConfig,
        LeanPRReviewV4CandidateTask,
    )

    data = build_candidate_task_data(unit, episode, prompt)
    task = LeanPRReviewV4CandidateTask(data, LeanPRReviewV4CandidateConfig())
    mcp = _RecordingMCP()
    asyncio.run(task.register_task_tools(mcp))
    assert "submit_candidates" in mcp.tools, "the task registered no submission tool"
    return data, mcp.tools["submit_candidates"]


@pytest.fixture(scope="module")
def unverified_unit():
    if not RELEASE.is_dir():
        pytest.skip(f"{RELEASE} is not present")
    units = load_jsonl(RELEASE / "derived/work_units.jsonl", ReviewWorkUnit)
    episodes = {
        item.episode_id: item
        for item in load_jsonl(RELEASE / "input/episodes.jsonl", ReviewEpisodeInput)
    }
    prompts = {
        item.work_unit_id: item
        for item in load_jsonl(RELEASE / "derived/rendered_prompts.jsonl", RenderedPrompt)
    }
    unit = next(
        (
            item for item in units
            if item.paths_by_change
            and prompts[item.work_unit_id].submission_verification_policy == "none"
        ),
        None,
    )
    if unit is None:
        pytest.skip("no unverified work unit carrying a path map in this release")
    return unit, episodes[unit.episode_id], prompts[unit.work_unit_id]


def _valid_candidate(data):
    change_id = data.change_ids[0]
    subject = data.primary_subjects_by_change[change_id]
    entities = data.entity_ids_by_change.get(change_id) or []
    leaf = subject.rsplit(".", 1)[-1]
    return {
        "change_ids": [change_id],
        "primary_change_id": change_id,
        "primary_subject": subject,
        "primary_entity_id": entities[0] if entities else None,
        "claim": f"{leaf} restates an existing lemma",
        "requested_change": f"replace {leaf} with the existing declaration",
        "issue_kind": "duplicate_implementation",
        "concern_family": "duplication",
        "concern_label": "duplicates an existing lemma",
        "severity": "advisory",
        "model_confidence": 0.5,
    }


def test_an_empty_submission_is_accepted(unverified_unit):
    """`[]` is a valid review outcome and must not error."""

    _data, submit = _handler_for(*unverified_unit)
    result = asyncio.run(submit(candidates=[]))
    evaluation = result.get("evaluation_result")
    assert evaluation is None or evaluation.success


def test_a_well_formed_candidate_is_accepted(unverified_unit):
    """The regression that cost a paid run: this call raised AttributeError at /12."""

    unit, episode, prompt = unverified_unit
    data, submit = _handler_for(unit, episode, prompt)
    from ape.tasks.lean_tasks.formal_math.pr_review_v4.candidates import (
        CandidateSubmission,
    )

    submission = CandidateSubmission(**_valid_candidate(data))
    result = asyncio.run(submit(candidates=[submission]))
    evaluation = result.get("evaluation_result")
    assert evaluation is None or evaluation.success, (
        f"a well-formed candidate was rejected: {getattr(evaluation, 'message', result)}"
    )


def test_a_candidate_naming_a_foreign_change_id_is_rejected(unverified_unit):
    """The work-unit confinement contract still bites through the real handler."""

    unit, episode, prompt = unverified_unit
    data, submit = _handler_for(unit, episode, prompt)
    from ape.tasks.lean_tasks.formal_math.pr_review_v4.candidates import (
        CandidateSubmission,
    )

    payload = _valid_candidate(data)
    payload["change_ids"] = ["change:" + "0" * 64]
    payload["primary_change_id"] = "change:" + "0" * 64
    result = asyncio.run(submit(candidates=[CandidateSubmission(**payload)]))
    evaluation = result.get("evaluation_result")
    assert evaluation is not None and not evaluation.success
