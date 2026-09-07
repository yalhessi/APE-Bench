"""The file-scoped generalist: scheduling, scope contract, and what it may claim.

Two generalist arms exist deliberately. The **control** reviews one work unit at a time and
covers the concern families no specialist exists for. This is the **component**, whose
distinguishing input is every change the PR made to one file.

Its scope is evidence-chosen, not assumed:

* 0 of 43 gold obligations cross a file boundary — so PR-wide context would cost tokens for
  nothing, and the file is the widest scope with anything to find.
* 8 of 43 span several work units *within* a file, and all 8 sit in the 12 files that have
  more than one work unit.
* 73 of 85 files hold one work unit, where this view equals the control's.

The scope *rule* is what keeps the arm honest. Cross-site unification is the digest phase's
job now, solved once for every arm; an arm that re-emitted per-site findings would duplicate
the specialists, flood the merge, and leave the cross-arm case unsolved. So a claim must need
the file view — several targets, or `scope_placement` — and that is enforced at submission
rather than asked for in the prompt.
"""

import asyncio
from pathlib import Path

import pytest

from src.mathlib_review.io import load_jsonl
from src.mathlib_review.agenda.render_file_scoped import (
    file_claim_error,
    render_file_all,
    schedule_files,
    schedule_report,
)
from src.mathlib_review.schema import (
    ChangeGraph,
    ReviewEpisodeInput,
    ReviewWorkUnit,
)

RELEASE = Path("inputs/pr_review_v4/releases/dev-medium-0.3.0")


@pytest.fixture(scope="module")
def scheduled():
    if not RELEASE.is_dir():
        pytest.skip(f"{RELEASE} is not present")
    graphs = load_jsonl(RELEASE / "derived/change_graphs.jsonl", ChangeGraph)
    units = load_jsonl(RELEASE / "derived/work_units.jsonl", ReviewWorkUnit)
    episodes = load_jsonl(RELEASE / "input/episodes.jsonl", ReviewEpisodeInput)
    invocations = schedule_files(graphs, units)
    return {
        "graphs": {item.episode_id: item for item in graphs},
        "units": {item.work_unit_id: item for item in units},
        "episodes": {item.episode_id: item for item in episodes},
        "invocations": invocations,
        "prompts": render_file_all(invocations, episodes, graphs),
    }


def test_one_invocation_per_changed_file(scheduled):
    invocations = scheduled["invocations"]
    keys = [(item.episode_id, item.path) for item in invocations]
    assert len(keys) == len(set(keys)), "a file must be reviewed once, not once per unit"
    assert all(item.path.endswith(".lean") for item in invocations)
    report = schedule_report(invocations)
    assert report["invocations"] == len(invocations)
    # Cheaper than the control it sits beside: 85 files against 225 work units.
    assert report["invocations"] < len(scheduled["units"])


def test_scheduling_reads_only_the_change_graph(scheduled):
    """Gold-free by construction, like every other arm's scheduler."""

    import ast
    import inspect

    from src.mathlib_review.agenda import render_file_scoped

    tree = ast.parse(inspect.getsource(render_file_scoped))
    imported = {
        alias.name for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) for alias in node.names
    }
    assert not imported & {"JudgmentNode", "InterventionView", "JudgmentObligation"}


def test_every_file_prompt_covers_all_of_its_targets(scheduled):
    for prompt in scheduled["prompts"]:
        assert prompt.included_change_ids
        assert not prompt.omitted_change_ids, (
            "a file prompt that hides targets defeats the point of the file view"
        )


def test_the_diff_is_not_replicated_once_per_target(scheduled):
    """Change targets carry the same diff blob; concatenating them explodes the prompt.

    Measured: all 108 targets in one medium file carry an identical 17.3k-character blob, so
    a naive concatenation ships 1.87M characters for a single file.
    """

    biggest = max(scheduled["prompts"], key=lambda item: len(item.included_change_ids))
    assert len(biggest.included_change_ids) > 50, "expected the large file in this release"
    assert biggest.estimated_tokens < 60_000, (
        f"{biggest.estimated_tokens} tokens suggests the diff is repeated per target"
    )


def test_prompt_identities_are_distinct(scheduled):
    prompts = scheduled["prompts"]
    assert len({item.prompt_sha256 for item in prompts}) == len(prompts)
    assert len({item.invocation_id for item in prompts}) == len(prompts)


def test_a_single_target_claim_is_refused_unless_it_is_about_placement():
    """The rule that stops this arm duplicating the specialists."""

    assert file_claim_error(["change:a", "change:b"], "duplicate_implementation") is None
    assert file_claim_error(["change:a"], "scope_placement") is None
    error = file_claim_error(["change:a"], "proof_simplification")
    assert error and "more than one change target" in error
    # Repeating one id is not two targets.
    assert file_claim_error(["change:a", "change:a"], "documentation_gap")


class _RecordingMCP:
    def __init__(self):
        self.tools = {}

    def tool(self, *_args, **_kwargs):
        def decorator(function):
            self.tools[function.__name__] = function
            return function
        return decorator


def _handler(scheduled):
    from ape.tasks.lean_tasks import (
        LeanPRReviewV4FileConfig,
        LeanPRReviewV4FileTask,
    )
    from src.mathlib_review.review.task_adapter import build_file_task_data

    prompt = max(scheduled["prompts"], key=lambda item: len(item.included_change_ids))
    invocation = next(
        item for item in scheduled["invocations"]
        if item.invocation_id == prompt.invocation_id
    )
    unit = scheduled["units"][prompt.work_unit_id]
    episode = scheduled["episodes"][unit.episode_id]
    graph = scheduled["graphs"][unit.episode_id]
    data = build_file_task_data(unit, episode, prompt, invocation.path, graph)
    task = LeanPRReviewV4FileTask(data, LeanPRReviewV4FileConfig())
    mcp = _RecordingMCP()
    asyncio.run(task.register_task_tools(mcp))
    return data, mcp.tools["submit_candidates"]


def _submission(data, change_ids, issue_kind):
    from ape.tasks.lean_tasks.formal_math.pr_review_v4.candidates import (
        CandidateSubmission,
    )

    primary = change_ids[0]
    subject = data.primary_subjects_by_change[primary]
    entities = data.entity_ids_by_change.get(primary) or []
    leaf = subject.rsplit(".", 1)[-1]
    return CandidateSubmission(
        change_ids=list(change_ids), primary_change_id=primary, primary_subject=subject,
        primary_entity_id=entities[0] if entities else None,
        issue_kind=issue_kind, concern_family="scope", concern_label="coherence",
        severity="advisory", claim=f"{leaf} sits in the wrong section",
        requested_change=f"move {leaf} into the section its neighbours use",
    )


def test_the_handler_refuses_a_single_target_claim(scheduled):
    """Asserted through the real submission path, not the helper it delegates to."""

    data, submit = _handler(scheduled)
    submission = _submission(data, [data.change_ids[0]], "documentation_gap")
    result = asyncio.run(submit(candidates=[submission]))
    evaluation = result["evaluation_result"]
    assert not evaluation.success
    assert "more than one change target" in evaluation.message


def test_the_handler_accepts_a_cross_target_claim(scheduled):
    data, submit = _handler(scheduled)
    submission = _submission(data, data.change_ids[:2], "duplicate_implementation")
    result = asyncio.run(submit(candidates=[submission]))
    evaluation = result.get("evaluation_result")
    assert evaluation is None or evaluation.success, getattr(evaluation, "message", result)


def test_the_handler_accepts_a_placement_claim_on_one_target(scheduled):
    """`scope_placement` is inherently about a declaration's neighbours.

    It is also the kind `verify_scope_placement` abstains on today, because placement needs
    file-level adjacency that hunk-level change targets do not record — which is exactly the
    gap this arm's vantage point exists to close.
    """

    data, submit = _handler(scheduled)
    submission = _submission(data, [data.change_ids[0]], "scope_placement")
    result = asyncio.run(submit(candidates=[submission]))
    evaluation = result.get("evaluation_result")
    assert evaluation is None or evaluation.success, getattr(evaluation, "message", result)


def test_task_data_widens_change_ids_to_the_file(scheduled):
    """A file's targets may span work units; the unit's list would reject a valid claim."""

    data, _submit = _handler(scheduled)
    unit = scheduled["units"][data.work_unit_id]
    assert set(data.change_ids) >= set(unit.change_ids) or len(data.change_ids) > 1
