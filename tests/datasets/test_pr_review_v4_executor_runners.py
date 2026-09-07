"""Every registered implementation must have a runner, and every runner must actually run.

Three separate crashes reached a full medium execution before these tests existed: a
misspelled dataclass field, and two evidence `kind` values that were not in the schema's
literal set. All three were invisible until execution because the executor catches runner
exceptions and records only the exception *type* in the ledger, so 86 tasks reported
`execution_failed` with no traceback anywhere.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import get_args

import pytest

from src.mathlib_review.evidence import evidence

from src.mathlib_review.opportunities import executor as opportunity_executor
from src.mathlib_review.evidence.operators import canonical_api
from src.mathlib_review.opportunities.implementation_registry import default_implementations
from src.mathlib_review.opportunities.executor import (
    DEFAULT_RUNNERS,
    _lint_runner,
    _policy_runner,
)
from src.mathlib_review.schema import (
    CapabilityAssessment,
    ChangeGraph,
    ChangedRange,
    ChangeTarget,
    InvestigationTask,
    LineSpan,
    OperatorRun,
    OpportunityEvidenceArtifact,
    ReviewEpisodeInput,
    VisibleText,
)


def test_every_registered_implementation_has_a_runner():
    registered = {item.implementation_id for item in default_implementations()}
    assert registered == set(DEFAULT_RUNNERS), (
        "registry and executor disagree: "
        f"missing runners={sorted(registered - set(DEFAULT_RUNNERS))} "
        f"orphan runners={sorted(set(DEFAULT_RUNNERS) - registered)}"
    )


def _fixture(code: str, *, kind: str = "declaration", name: str = "Test.lemma"):
    target = ChangeTarget(
        change_id="change:test",
        episode_id="episode:test",
        pr_number=1,
        kind="declaration",
        path="Mathlib/Test.lean",
        declaration_name=name,
        declaration_kind=kind,
        changed_range_ids=["range:test"],
        diff_fragments=[],
        reviewed_code=code,
        parse_status="semantic",
        source_sha256="0" * 64,
    )
    graph = ChangeGraph(
        graph_id="graph:test",
        episode_id="episode:test",
        repo="leanprover-community/mathlib4",
        pr_number=1,
        round_index=1,
        patch_sha256="3" * 64,
        parser_version="test/1",
        changed_ranges=[],
        entities=[],
        targets=[target],
        file_coverage=[],
        source_sha256="1" * 64,
    )
    task = InvestigationTask(
        investigation_id="investigation:test",
        method_id="lint_norm.v1",
        work_unit_id="work-unit:test",
        episode_id="episode:test",
        pr_number=1,
        modification_ids=["modification:test"],
        primary_change_id=target.change_id,
        expected_operators=["text_style_lint"],
        method_registry_sha256="6" * 64,
        source_sha256="2" * 64,
    )
    episode = ReviewEpisodeInput(
        episode_id="episode:test",
        repo="leanprover-community/mathlib4",
        pr_number=1,
        round_index=1,
        title=VisibleText(text="t", provenance="review_time_verified"),
        description=VisibleText(text="d", provenance="review_time_verified"),
        base_sha="a" * 40,
        reviewed_head_sha="b" * 40,
        diff="",
        changed_files=[],
        patch_sha256="3" * 64,
        source_projection_sha256="4" * 64,
    )
    return task, graph, episode


@pytest.mark.parametrize(
    "runner, code, kind, expect_opportunity",
    [
        # A long line is a finding; clean code is not.
        (_lint_runner, "x" * 101, "theorem", True),
        (_lint_runner, "theorem foo : True := trivial\n", "theorem", False),
        # A newly introduced axiom is a finding; an ordinary theorem is not.
        (_policy_runner, "axiom foo : True", "axiom", True),
        (_policy_runner, "theorem foo : True := trivial", "theorem", False),
    ],
)
def test_lexical_runners_execute_and_emit_valid_evidence(runner, code, kind, expect_opportunity, tmp_path):
    """These runners are workspace-free, so a full execution is testable in-process.

    Constructing the evidence is the point: `OpportunityEvidenceArtifact.kind` is a closed
    literal, and an unregistered value raises only when the artifact is built.
    """

    task, graph, episode = _fixture(code, kind=kind)
    outcome = runner(task, graph, episode, tmp_path, {})
    assert bool(outcome.opportunities) is expect_opportunity
    assert outcome.disposition == ("opportunities" if expect_opportunity else "checked_no_opportunity")
    assert outcome.execution_status == "completed"
    # Every artifact validated on construction; assert they were actually produced.
    assert outcome.evidence


def _literal_values(model, field):
    return set(get_args(model.model_fields[field].annotation))


def _string_arg(call, index):
    """The literal string passed positionally at `index`, or None if it is not a literal."""

    if len(call.args) <= index:
        return None
    node = call.args[index]
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


@pytest.mark.parametrize(
    "callee, arg_index, model, field",
    [
        # `_operator_run(task, operator, status, ...)`
        ("_operator_run", 2, OperatorRun, "status"),
        # `evidence_artifact(task, kind, source_ref, ...)`
        ("evidence_artifact", 1, OpportunityEvidenceArtifact, "kind"),
    ],
)
def test_runner_literals_are_declared_in_the_schema(callee, arg_index, model, field):
    """Statically check every literal a runner passes into a closed schema enum.

    Runners that need a workspace cannot be executed in a unit test, so their invented
    literals stayed invisible until a full medium run: three separate values
    (`lint_report`, `policy_report`, `skipped`) each cost one execution over 2,253 tasks to
    discover, because the executor records only the exception type. This walks the source
    instead, so every runner is covered whether or not it is executable here.
    """

    source = Path(opportunity_executor.__file__).read_text(encoding="utf-8")
    allowed = _literal_values(model, field)
    used = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == callee:
            value = _string_arg(node, arg_index)
            if value is not None:
                used.add(value)
    assert used, f"no literal {callee} calls found — has the signature changed?"
    assert used <= allowed, (
        f"{callee} passes {field} values absent from {model.__name__}: {sorted(used - allowed)}"
    )


def test_every_temporary_compile_site_normalises_the_filename():
    """No stored diagnostic may carry the random name of the file Lean compiled.

    Lean reports diagnostics against the throwaway file it was handed, so any artifact
    storing raw output re-hashes on every run and silently destroys byte-reproducibility of
    everything derived from it. Under executor /2 this affected 129 of 410 evidence
    artifacts in a medium run: identical findings, different opportunity IDs.

    Checking the property per *module* rather than at one call site is deliberate — the
    first fix caught only `_baseline_runner`, and a full re-run was needed to discover that
    `canonical_api.check_applicability` and `evidence.py` had the same defect.
    """

    for module in (opportunity_executor, canonical_api, evidence):
        source = Path(module.__file__).read_text(encoding="utf-8")
        if "NamedTemporaryFile" not in source or ".lean" not in source:
            continue
        assert "COMPILED_TARGET" in source, (
            f"{module.__name__} compiles a temporary .lean file but never substitutes "
            f"COMPILED_TARGET, so its diagnostics are not reproducible"
        )


def test_compiled_target_placeholder_is_substituted_before_truncation():
    """A long compile log must not keep a path fragment after slicing."""

    source = Path(opportunity_executor.__file__).read_text(encoding="utf-8")
    substitution = source.index("replace(str(temporary), COMPILED_TARGET)")
    truncation = source.index("diagnostics[-4000:]")
    assert substitution < truncation


def test_error_lines_match_tagged_lean_diagnostics():
    """Lean writes `error(lean.unknownIdentifier):`, not a bare `error:`.

    A first measurement of diagnostic attribution used `error:` and reported zero errors on
    files that plainly failed, which made line attribution look far less usable than it is.
    """

    diagnostics = (
        "exit_code=1\n"
        "<compiled-target>:523:10: error(lean.unknownIdentifier): Unknown identifier `f`\n"
        "<compiled-target>:99:4: error: unsolved goals\n"
        "<compiled-target>:12:1: warning: `g` has been deprecated\n"
        "/some/other/file.lean:7:1: error: not our file\n"
    )
    assert opportunity_executor._error_lines(diagnostics) == [99, 523]


def test_file_claimant_prefers_a_scheduled_target_over_the_first_change_target():
    """The anchor must come from the supported task set, not from the change graph.

    On medium, 3 of 85 files have a lowest-`change_id` target that is not scheduled for the
    implementation; anchoring on the graph alone would drop those files' findings entirely.
    """

    task_a, graph, episode = _fixture("x", name="A")
    # Two targets in one file; the alphabetically-first change target is NOT scheduled.
    first = graph.targets[0].model_copy(update={"change_id": "change:aaa", "declaration_name": "A"})
    second = graph.targets[0].model_copy(update={"change_id": "change:bbb", "declaration_name": "B"})
    graph = graph.model_copy(update={"targets": [first, second]})
    scheduled = task_a.model_copy(update={
        "investigation_id": "investigation:second", "primary_change_id": "change:bbb",
    })
    assessment = CapabilityAssessment(
        assessment_id="assessment:test",
        implementation_id="baseline_failure.target_compile.v1",
        investigation_id="investigation:second",
        method_id="baseline_failure.v1",
        episode_id=episode.episode_id,
        pr_number=1,
        primary_change_id="change:bbb",
        status="supported",
        reason_code="test",
        source_sha256="7" * 64,
    )
    claimants = opportunity_executor.file_claimants([scheduled], [assessment], [graph])
    key = ("baseline_failure.target_compile.v1", episode.episode_id, "Mathlib/Test.lean")
    assert claimants[key] == "investigation:second"


def test_file_claimants_ignore_unsupported_assessments():
    task, graph, episode = _fixture("x")
    assessment = CapabilityAssessment(
        assessment_id="assessment:test",
        implementation_id="baseline_failure.target_compile.v1",
        investigation_id=task.investigation_id,
        method_id="baseline_failure.v1",
        episode_id=episode.episode_id,
        pr_number=1,
        primary_change_id=task.primary_change_id,
        status="unsupported_shape",
        reason_code="test",
        source_sha256="7" * 64,
    )
    assert opportunity_executor.file_claimants([task], [assessment], [graph]) == {}


def test_unnamed_targets_are_labelled_by_kind_not_by_hash():
    """Imports, module docs and bare commands have no declaration name.

    The implicated-declaration list is rendered into the adjudication prompt, so falling
    back to `change_id` would print a sha256 into a review comment.
    """

    _, graph, _ = _fixture("x")
    target = graph.targets[0]
    unnamed = target.model_copy(update={
        "change_id": "change:unnamed", "declaration_name": None, "kind": "command",
        "changed_range_ids": ["range:test"],
    })
    span = ChangedRange(
        range_id="range:test", path=target.path, hunk_index=1, range_index=1,
        change_kind="replacement", reviewed_span=LineSpan(line_start=10, line_end=20),
        diff_fragment="", source_sha256="8" * 64,
    )
    graph = graph.model_copy(update={"targets": [unnamed], "changed_ranges": [span]})
    names = opportunity_executor._targets_covering(graph, target.path, [15])
    assert names == ["<command>"]
