"""Design D1, `structured`: a verdict per declaration and concern, verified before filing.

What is pinned: the design keeps the solo's packet and prompts and appends its contract; its
submission is the arms' verdict contract generalized to the whole PR (every cell answered, every
`would_change` a finding, missing cells pressed then `unstated`); verification at submission is
refutation by fact and nothing else (an edit that does not compile, a duplicate that does not
exist, a rename onto an existing name), an unverified change files as advisory, and the result
carries the ledger the critic stage and the reading consume. The Lean compile and the lookups are
replaced by fakes here; the one-PR smoke against the real reviewed workspace is
results/pr_review_v5/probes/review-designs-2026-10-02/.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from ape.tasks.base import EvaluationResult, get_task_class
from ape.tasks.models import WorkspaceInfo
from ape.tasks.lean_tasks.formal_math.review import DESIGNS
from ape.tasks.lean_tasks.formal_math.review.structured import (
    CONCERNS, LEDGER_PRESSES, REFUTED, STRUCTURED_TASK_TYPE, UNVERIFIED, VERIFIED, LedgerRow,
    StructuredEdit, StructuredFinding, StructuredReviewData, StructuredReviewResult,
    StructuredReviewTask, declarations_of, resolve_declaration,
)
from ape.tasks.lean_tasks.formal_math.review.candidates import UNSTATED_VERDICT

DECLARATIONS = [
    {"name": "Submodule.foo_bar", "kind": "theorem", "path": "Mathlib/A.lean", "change_id": "change:1"},
    {"name": "Submodule.baz", "kind": "lemma", "path": "Mathlib/A.lean", "change_id": "change:2"},
]


def _data(**overrides):
    payload = dict(
        task_id="d1-1", pr_number=33337, pr_title="chore: rename lemmas",
        pr_description="A description.", diff="--- a/Mathlib/A.lean\n+++ b/Mathlib/A.lean\n",
        changed_files=["Mathlib/A.lean"], episode_id="ep:33337",
        invocation_id="ep:33337#solo_agent", declarations=list(DECLARATIONS),
        target_workspace=WorkspaceInfo(name="target", commit_hash="c" * 40, repo_url="x"),
    )
    payload.update(overrides)
    return StructuredReviewData(**payload)


def _task(**data_overrides):
    """A real task under the hygiene settings, with no workspace and a test logger."""

    import logging

    from ape.scaffolds.ape_agent.config import ApeAgentConfig

    config = ApeAgentConfig()
    task_config = StructuredReviewTask.task_config_class(
        filing_bar="request", review_notes=True, notes_form="per_object_family",
        user_prompt="v2", finding_budget=40)
    config = config.model_copy(update={"task_config": task_config}, deep=True)
    task = StructuredReviewTask(_data(**data_overrides), config)
    task.logger = logging.getLogger("structured-test")
    task.termination_callback = None
    return task


def _submit(task, ledger, findings=(), **kwargs):
    return asyncio.run(task._submit([LedgerRow(**row) for row in ledger],
                                    [StructuredFinding(**item) for item in findings],
                                    kwargs.get("confidence"), kwargs.get("message", "")))


def _full_ledger(verdicts=None):
    """Every cell `no_issue`, except the (declaration, concern) pairs in `verdicts`."""

    verdicts = verdicts or {}
    rows = []
    for decl in DECLARATIONS:
        for concern in CONCERNS:
            verdict = verdicts.get((decl["name"], concern), "no_issue")
            rows.append({"declaration": decl["name"], "concerns": [concern],
                         "reason": f"checked {concern}", "verdict": verdict})
    return rows


def _finding(**overrides):
    item = {"declaration": "Submodule.foo_bar", "concern": "proof", "path": "Mathlib/A.lean",
            "line_start": 10, "claim": "foo_bar's proof is three lines of simp.",
            "suggested_fix": "simp [bar]", "severity": "blocking"}
    item.update(overrides)
    return item


# --- registration and inheritance -------------------------------------------------------------


def test_it_is_a_registered_design_with_the_v5_spelling():
    assert STRUCTURED_TASK_TYPE == "lean_pr_review_v5_structured"
    assert get_task_class(STRUCTURED_TASK_TYPE) is StructuredReviewTask
    assert DESIGNS["structured"] is StructuredReviewTask
    assert StructuredReviewTask.reads_stage is False


def test_it_keeps_the_solo_packet_and_satisfies_the_context_tools_contract():
    from tests.datasets.test_pr_review_v5_solo_task import _attributes_the_context_tools_read

    names = [cls.__name__ for cls in StructuredReviewTask.__mro__]
    assert "SoloReviewTask" in names and "LeanPRReviewV4CandidateTask" not in names
    missing = sorted(name for name in _attributes_the_context_tools_read()
                     if name not in StructuredReviewData.model_fields)
    assert not missing, missing


def test_the_result_carries_the_ledger_the_critic_and_the_reading_consume():
    fields = StructuredReviewResult.model_fields
    assert {"ledger", "refuted", "findings", "episode_id", "invocation_id"} <= set(fields)
    assert StructuredReviewResult.model_fields["design"].default == "structured"


# --- the payload -----------------------------------------------------------------------------


def _graph():
    def target(change_id, kind, name, reviewed, path="Mathlib/A.lean"):
        return SimpleNamespace(change_id=change_id, kind=kind, declaration_name=name,
                               declaration_kind="theorem" if kind == "declaration" else None,
                               path=path, reviewed_code=reviewed)
    return SimpleNamespace(targets=[
        target("change:b", "declaration", "Ns.second", "theorem second : True := trivial"),
        target("change:a", "declaration", "Ns.first", "theorem first : True := trivial"),
        target("change:c", "declaration", "Ns.gone", ""),           # removed by the PR
        target("change:d", "doc_comment", None, "/-- doc -/"),      # not a declaration
        target("change:e", "declaration", "Other.x", "def x := 1", path="Mathlib/B.lean"),
    ])


def test_the_payload_lists_the_declarations_the_pr_leaves_in_place_in_the_pr_models_order():
    payload = StructuredReviewTask.design_payload(
        episode=SimpleNamespace(episode_id="ep:1"), graph=_graph(), dataset=None, stage=None)
    assert [row["name"] for row in payload["declarations"]] == ["Ns.first", "Ns.second", "Other.x"]
    assert payload["declarations"][0]["kind"] == "theorem"
    assert "3 declaration(s) x 6 concerns = 18 ledger cells" == \
        StructuredReviewTask.describe_design_payload(payload)


def test_an_episode_without_a_graph_is_refused_not_given_an_empty_ledger():
    with pytest.raises(ValueError, match="no change graph"):
        StructuredReviewTask.design_payload(
            episode=SimpleNamespace(episode_id="ep:1"), graph=None, dataset=None, stage=None)


RELEASE = Path("inputs/pr_review_v4/releases/dev-medium-0.3.0")


@pytest.mark.skipif(not (RELEASE / "derived/change_graphs.jsonl").is_file(),
                    reason="needs the dev-medium release on disk")
def test_on_the_real_release_33337_has_five_declarations_in_place():
    from src.mathlib_review.io import jsonl_rows
    from src.mathlib_review.schema import ChangeGraph

    graph = next(ChangeGraph.model_validate(row)
                 for row in jsonl_rows(RELEASE / "derived/change_graphs.jsonl")
                 if row["pr_number"] == 33337)
    rows = declarations_of(graph)
    assert len(rows) == 5, [row["name"] for row in rows]
    assert "Submodule.coe_starProjection_eq_isComplProjection" in {row["name"] for row in rows}


def test_a_declaration_resolves_by_its_full_name_or_a_unique_dotted_suffix():
    names = ["Submodule.foo_bar", "Other.foo_bar", "Submodule.baz"]
    assert resolve_declaration("Submodule.baz", names) == "Submodule.baz"
    assert resolve_declaration("baz", names) == "Submodule.baz"
    assert resolve_declaration("foo_bar", names) is None, "ambiguous"
    assert resolve_declaration("nothing", names) is None


# --- the prompt ------------------------------------------------------------------------------


def test_the_prompt_is_the_solos_without_the_notes_line_plus_the_contract():
    from ape.tasks.lean_tasks.formal_math.review.solo import NOTES_LINE_FAMILY

    task = _task()
    prompt = asyncio.run(task.create_user_prompt())
    assert task._review_notes() is False
    assert NOTES_LINE_FAMILY.strip() not in prompt, "the account is the ledger, not prose"
    assert "and your `notes`" not in prompt
    assert "## The ledger" in prompt
    for decl in DECLARATIONS:
        assert f"`{decl['name']}`" in prompt
    for concern in CONCERNS:
        assert f"`{concern}`" in prompt
    assert "submit_findings" in prompt
    assert "Nothing ranks or withholds" in prompt
    # The solo's own text is still the body: the diff, the request bar's severity line.
    assert "## The diff" in prompt and "Advisory findings count in full" in prompt


def test_the_system_prompt_is_the_solos():
    from ape.tasks.lean_tasks.formal_math.review.solo import SOLO_SYSTEM

    assert asyncio.run(_task().create_system_prompt()) == SOLO_SYSTEM


# --- the tools -------------------------------------------------------------------------------


class _CapturingMCP:
    def __init__(self):
        self.tools = {}

    def tool(self, **kwargs):
        def decorate(fn):
            self.tools[fn.__name__] = (fn, kwargs)
            return fn
        return decorate


def test_it_registers_its_own_submission_beside_the_base_grant_and_not_the_bases():
    task = _task(context_tools=["declaration_search", "naming_norm"])
    mcp = _CapturingMCP()
    asyncio.run(task.register_task_tools(mcp))
    assert {"lean_verify_edit", "declaration_search", "naming_norm", "submit_findings"} \
        <= set(mcp.tools)
    assert "ledger" in mcp.tools["submit_findings"][1]["description"]


def test_the_submission_schema_has_no_properties_less_object():
    from tests.datasets.test_pr_review_v5_tool_schemas import _freeform_objects, _schemas

    schemas = _schemas(_task())
    assert "submit_findings" in schemas
    assert _freeform_objects(schemas["submit_findings"]) == []
    assert "ledger" in schemas["submit_findings"]["properties"]


# --- the ledger check ------------------------------------------------------------------------


def test_a_complete_consistent_ledger_flattens_to_one_cell_per_declaration_and_concern():
    task = _task()
    cells, refusal = task._check_ledger(
        [LedgerRow(**row) for row in _full_ledger({("Submodule.foo_bar", "proof"): "would_change"})],
        [StructuredFinding(**_finding())])
    assert refusal is None
    assert len(cells) == len(DECLARATIONS) * len(CONCERNS)
    assert cells[0] == {"declaration": "Submodule.foo_bar", "concern": "proof",
                        "verdict": "would_change", "reason": "checked proof"}


def test_a_row_may_decide_several_concerns_at_once_except_a_would_change():
    task = _task()
    rows = [LedgerRow(declaration="Submodule.foo_bar", concerns=list(CONCERNS), reason="all fine",
                      verdict="no_issue"),
            LedgerRow(declaration="Submodule.baz", concerns=list(CONCERNS), reason="all fine",
                      verdict="no_issue")]
    cells, refusal = task._check_ledger(rows, [])
    assert refusal is None and len(cells) == 12
    rows[0] = LedgerRow(declaration="Submodule.foo_bar", concerns=["proof", "name"],
                        reason="two things", verdict="would_change")
    _, refusal = task._check_ledger(rows, [StructuredFinding(**_finding())])
    assert "exactly one concern" in refusal


def test_an_inconsistent_ledger_is_refused_by_name():
    task = _task()
    # A finding at a cell whose verdict is no_issue.
    _, refusal = task._check_ledger([LedgerRow(**row) for row in _full_ledger()],
                                    [StructuredFinding(**_finding())])
    assert "not `would_change`" in refusal
    # A would_change with no finding.
    _, refusal = task._check_ledger(
        [LedgerRow(**row) for row in _full_ledger({("Submodule.baz", "name"): "would_change"})], [])
    assert "no finding" in refusal
    # An unknown declaration, and a duplicate cell.
    rows = _full_ledger() + [{"declaration": "Nope", "concerns": ["proof"], "reason": "r",
                              "verdict": "no_issue"}]
    _, refusal = task._check_ledger([LedgerRow(**row) for row in rows], [])
    assert "not one of this PR's listed declarations" in refusal
    rows = _full_ledger() + [{"declaration": "Submodule.baz", "concerns": ["proof"], "reason": "r",
                              "verdict": "no_issue"}]
    _, refusal = task._check_ledger([LedgerRow(**row) for row in rows], [])
    assert "more than one verdict" in refusal


def test_missing_cells_are_asked_for_a_bounded_number_of_times_then_recorded_unstated():
    task = _task()
    rows = [LedgerRow(**row) for row in _full_ledger()[:-2]]  # two cells of baz missing
    for attempt in range(1, LEDGER_PRESSES + 1):
        cells, refusal = task._check_ledger(rows, [])
        assert cells is None and f"(attempt {attempt} of {LEDGER_PRESSES})" in refusal
        assert "(Submodule.baz, docstring)" in refusal
    cells, refusal = task._check_ledger(rows, [])
    assert refusal is None
    unstated = [cell for cell in cells if cell["verdict"] == UNSTATED_VERDICT]
    assert [(c["declaration"], c["concern"]) for c in unstated] == [
        ("Submodule.baz", "docstring"), ("Submodule.baz", "placement")]


def test_a_file_level_change_names_the_path_and_needs_no_cell():
    task = _task()
    cells, refusal = task._check_ledger(
        [LedgerRow(**row) for row in _full_ledger()],
        [StructuredFinding(**_finding(declaration="Mathlib/A.lean", concern="docstring",
                                      claim="The module doc names the wrong file."))])
    assert refusal is None and len(cells) == 12


# --- verification and recording -------------------------------------------------------------


def _fake_checks(task, monkeypatch, *, compile_outcome=VERIFIED, lookup_count=1, base_hits=0):
    async def compile_edit(finding):
        return compile_outcome, {"check": "compile", "answer": f"fake compile: {compile_outcome}"}

    async def lookup(this, identifier, limit=5, *, trace=True):
        assert trace is False, "a submission-time lookup must not write the reviewer's trace"
        return {"success": True, "count": lookup_count, "declared_before_this_pr": base_hits,
                "declared_in_this_pr": lookup_count - base_hits, "results": f"hits for {identifier}"}

    async def census(this, declaration, *, trace=True):
        assert trace is False
        return {"success": True, "verdict": "emerging", "results": "census text"}

    from ape.tasks.lean_tasks.formal_math.review import context_tools

    monkeypatch.setattr(task, "_compile_edit", compile_edit)
    monkeypatch.setattr(context_tools, "lookup_declaration", lookup)
    monkeypatch.setattr(context_tools, "naming_census", census)


def _captured_result(task):
    captured = {}

    async def terminate(result):
        captured["result"] = result

    task.termination_callback = terminate
    return captured


def test_a_verified_edit_files_with_its_severity_and_the_ledger_records_the_outcome(monkeypatch):
    task = _task()
    _fake_checks(task, monkeypatch, compile_outcome=VERIFIED)
    captured = _captured_result(task)
    finding = _finding(edit={"declaration_name": "Submodule.foo_bar",
                             "new_declaration": "theorem foo_bar : True := by simp [bar]"})
    out = _submit(task, _full_ledger({("Submodule.foo_bar", "proof"): "would_change"}), [finding])
    assert out["evaluation_result"].success, out
    result = captured["result"]
    assert isinstance(result, StructuredReviewResult)
    [filed] = result.findings
    assert filed["severity"] == "blocking" and filed["verified"] is True
    assert filed["concern_label"] == "proof" and filed["declaration"] == "Submodule.foo_bar"
    assert filed["verification"] == VERIFIED
    assert json.loads(filed["evidence"])[0]["check"] == "compile"
    # The solo's v2 stamping, so the review channel reads this design as the baseline.
    assert filed["concern_family"] == "other" and filed["issue_kind"] == "style_norm_violation"
    cell = next(c for c in result.ledger if c["declaration"] == "Submodule.foo_bar" and c["concern"] == "proof")
    assert cell["outcome"] == VERIFIED and result.refuted == []
    assert result.episode_id == "ep:33337" and result.invocation_id == "ep:33337#solo_agent"


def test_an_unverifiable_change_files_as_advisory_and_unverified(monkeypatch):
    task = _task()
    _fake_checks(task, monkeypatch)
    captured = _captured_result(task)
    finding = _finding(concern="docstring", claim="foo_bar has no docstring.", severity="blocking")
    out = _submit(task, _full_ledger({("Submodule.foo_bar", "docstring"): "would_change"}), [finding])
    assert out["evaluation_result"].success
    [filed] = captured["result"].findings
    assert filed["severity"] == "advisory" and filed["verified"] is False
    assert filed["verification"] == UNVERIFIED and filed["evidence"] is None


def test_a_refuted_change_is_handed_back_then_recorded_refuted_and_not_filed(monkeypatch):
    task = _task()
    _fake_checks(task, monkeypatch, compile_outcome=REFUTED)
    captured = _captured_result(task)
    ledger = _full_ledger({("Submodule.foo_bar", "proof"): "would_change"})
    finding = _finding(edit={"declaration_name": "Submodule.foo_bar", "new_declaration": "theorem foo_bar : True := by exact nope"})
    for attempt in range(1, LEDGER_PRESSES + 1):
        out = _submit(task, ledger, [finding])
        assert not out["evaluation_result"].success
        assert "contradicted by the tools" in out["evaluation_result"].message
        assert f"(attempt {attempt} of {LEDGER_PRESSES})" in out["evaluation_result"].message
    out = _submit(task, ledger, [finding])
    assert out["evaluation_result"].success
    result = captured["result"]
    assert result.findings == [], "a refuted change is not filed"
    [refuted] = result.refuted
    assert refuted["declaration"] == "Submodule.foo_bar" and refuted["evidence"][0]["check"] == "compile"
    cell = next(c for c in result.ledger if c["concern"] == "proof" and c["declaration"] == "Submodule.foo_bar")
    assert cell["verdict"] == "would_change" and cell["outcome"] == REFUTED


def test_a_duplicate_that_does_not_exist_is_refuted_and_one_that_does_is_verified(monkeypatch):
    task = _task()
    _fake_checks(task, monkeypatch, lookup_count=0)
    outcome, evidence = asyncio.run(task._verify_finding(StructuredFinding(**_finding(
        concern="library", duplicate_of="Mathlib.Nothing.here"))))
    assert outcome == REFUTED and "no declaration of" in evidence[0]["answer"]
    _fake_checks(task, monkeypatch, lookup_count=2)
    outcome, evidence = asyncio.run(task._verify_finding(StructuredFinding(**_finding(
        concern="library", duplicate_of="Finset.sum_comm"))))
    assert outcome == VERIFIED and evidence[0]["check"] == "duplicate_of"


def test_a_rename_onto_an_existing_name_is_refuted_and_otherwise_unverified_with_the_census(monkeypatch):
    task = _task()
    _fake_checks(task, monkeypatch, lookup_count=1, base_hits=1)
    outcome, evidence = asyncio.run(task._verify_finding(StructuredFinding(**_finding(
        concern="name", rename_to="Submodule.taken"))))
    assert outcome == REFUTED and "already declared" in evidence[0]["answer"]
    _fake_checks(task, monkeypatch, lookup_count=0)
    outcome, evidence = asyncio.run(task._verify_finding(StructuredFinding(**_finding(
        concern="name", rename_to="Submodule.free"))))
    assert outcome == UNVERIFIED
    assert evidence[0]["naming_norm_verdict"] == "emerging", "the census is evidence, never a refutation"


def test_a_refutation_wins_over_a_verification_on_one_finding(monkeypatch):
    task = _task()
    _fake_checks(task, monkeypatch, compile_outcome=VERIFIED, lookup_count=0)
    outcome, evidence = asyncio.run(task._verify_finding(StructuredFinding(**_finding(
        concern="library", duplicate_of="Nope.x",
        edit={"declaration_name": "Submodule.foo_bar", "new_declaration": "theorem foo_bar : True := trivial"}))))
    assert outcome == REFUTED and [e["check"] for e in evidence] == ["compile", "duplicate_of"]


def test_an_edit_that_cannot_be_applied_is_refuted_and_a_compile_that_never_ran_is_unverified(monkeypatch):
    """The real `_compile_edit`, with the compile faked at the Lean tool."""

    task = _task()
    finding = StructuredFinding(**_finding(edit={"declaration_name": "Submodule.foo_bar",
                                                 "new_declaration": "theorem foo_bar : True := trivial"}))
    monkeypatch.setattr(task, "_edited_file_code", lambda *a, **k: (None, "reviewed file not found: Mathlib/A.lean"))
    outcome, evidence = asyncio.run(task._compile_edit(finding))
    assert outcome == REFUTED and "could not be applied" in evidence["answer"]

    monkeypatch.setattr(task, "_edited_file_code", lambda *a, **k: ("theorem foo_bar : True := trivial", ""))

    class Tool:
        def __init__(self, **_kwargs):
            pass

        async def execute(self, code, max_messages=20, options=None):
            assert options == {"weak.linter.mathlibStandardSet": "true"}, "linters on"
            return {"outcome": "timeout", "message": "lean timed out"}

    from ape.toolkits.execute.lean import tools as lean_tools

    monkeypatch.setattr(lean_tools, "LeanVerifyToolsProvider", Tool)
    outcome, evidence = asyncio.run(task._compile_edit(finding))
    assert outcome == UNVERIFIED and "did not finish" in evidence["answer"]

    class Red(Tool):
        async def execute(self, code, max_messages=20, options=None):
            return {"outcome": "compile_errors", "errors": [{"data": "unknown identifier 'nope'"}]}

    async def attribute(path, result):
        return {**result, "errors_introduced_by_your_edit": result["errors"]}

    monkeypatch.setattr(lean_tools, "LeanVerifyToolsProvider", Red)
    monkeypatch.setattr(task, "_attribute_errors", attribute)
    outcome, evidence = asyncio.run(task._compile_edit(finding))
    assert outcome == REFUTED and "unknown identifier" in evidence["answer"]


def test_the_budget_refuses_rather_than_truncates(monkeypatch):
    task = _task()
    task.config.task_config.finding_budget = 1
    _fake_checks(task, monkeypatch)
    ledger = _full_ledger({("Submodule.foo_bar", "proof"): "would_change",
                           ("Submodule.foo_bar", "name"): "would_change"})
    out = _submit(task, ledger, [_finding(), _finding(concern="name", claim="foo_bar is misnamed.")])
    assert not out["evaluation_result"].success and "exceed this review's budget" in out["evaluation_result"].message


# --- downstream: the runner's projection reads the design's concern as a label ------------------


def test_the_runner_projects_the_concern_as_the_candidates_label_not_its_family():
    from src.mathlib_review.review.runner import _solo_candidate

    unit = SimpleNamespace(entity_ids_by_change={}, primary_subjects_by_change={"change:1": "Submodule.foo_bar"})
    finding = {"primary_change_id": "change:1", "change_ids": ["change:1"], "claim": "c",
               "suggested_fix": "f", "severity": "advisory", "concern_family": "other",
               "issue_kind": "style_norm_violation", "concern_label": "proof"}
    candidate = _solo_candidate(finding, unit)
    assert candidate["concern_family"] == "other" and candidate["concern_label"] == "proof"
    # And a solo finding, which carries no label, projects exactly as before.
    del finding["concern_label"]
    assert _solo_candidate(finding, unit)["concern_label"] == "other"
