"""Design G, `filing_contract`: a cell closes as conforming only on evidence the task verifies.

What is pinned (results/pr_review_v5/probes/filing-contract-2026-10-12/README.md): a `conforms`
without a verified `quote` of the subject's own code or a verified `check` is refused, the whole
call with it; a quote of another declaration's code is not the subject's; a check is an edit in
the session's compile cache or a lookup the task re-runs; every `candidate` and `ask_author` cell
is filed with its evidence and `would_clear_on`; the PR is a subject; a change the tools
contradict is handed back and then filed as a question, never dropped; there is no finding
budget; and the contract replaces the brief's suppressing instructions. The compile and the
lookups are fakes, as in D1's tests.
"""
from __future__ import annotations

import asyncio
import logging

import pytest

from ape.tasks.base import get_task_class
from ape.tasks.models import WorkspaceInfo
from ape.tasks.lean_tasks.formal_math.review import DESIGNS
from ape.tasks.lean_tasks.formal_math.review.base import edit_key
from ape.tasks.lean_tasks.formal_math.review.filing_contract import (
    CONCERNS, FILE_CONCERNS, FILING_TASK_TYPE, PR_CONCERNS, PR_SUBJECT, DeclarationEntry, FileEntry,
    FilingContractData, FilingContractResult, FilingContractTask, FilingFinding, PREntry, own_code_of,
)
from ape.tasks.lean_tasks.formal_math.review.structured import LEDGER_PRESSES, REFUTED, VERIFIED

FILE = "Mathlib/A.lean"
DECLARATIONS = [
    {"name": "Submodule.foo_bar", "kind": "theorem", "path": FILE, "change_id": "change:1",
     "own_code": "/-- Foo. -/\ntheorem foo_bar (h : p) : q := by simp [h]"},
    {"name": "Submodule.baz", "kind": "lemma", "path": FILE, "change_id": "change:2",
     "own_code": "lemma baz : r := rfl"},
]


def _task(**overrides):
    from ape.scaffolds.ape_agent.config import ApeAgentConfig

    payload = dict(
        task_id="g-1", pr_number=33337, pr_title="chore: rename lemmas",
        pr_description="Renames the projection lemmas to follow the convention.",
        diff="--- a/Mathlib/A.lean\n+++ b/Mathlib/A.lean\n", changed_files=[FILE],
        episode_id="ep:33337", invocation_id="ep:33337#solo_agent", declarations=list(DECLARATIONS),
        target_workspace=WorkspaceInfo(name="target", commit_hash="c" * 40, repo_url="x"))
    payload.update(overrides)
    config = ApeAgentConfig()
    task_config = FilingContractTask.task_config_class(
        filing_bar="request", review_notes=True, notes_form="per_object_family", user_prompt="v2",
        finding_budget=2)
    config = config.model_copy(update={"task_config": task_config}, deep=True)
    task = FilingContractTask(FilingContractData(**payload), config)
    task.logger = logging.getLogger("filing-contract-test")
    task.termination_callback = None
    return task


def _cell(disposition="candidate", reason="checked it", evidence=(), would_clear_on="worth"):
    cell = {"reason": reason, "disposition": disposition, "evidence": list(evidence)}
    if disposition != "conforms":
        cell["would_clear_on"] = would_clear_on
    return cell


def _quote(text):
    return {"kind": "quote", "text": text}


def _entry(subject, /, **cells):
    own = DECLARATIONS[0]["own_code"] if subject.endswith("foo_bar") else DECLARATIONS[1]["own_code"]
    return {"declaration": subject, **{concern: cells.get(concern, _cell("conforms", evidence=[_quote(own)]))
                                       for concern in CONCERNS}}


def _file_entry(**cells):
    return {"file": FILE, **{concern: cells.get(concern, _cell("conforms", evidence=[
        {"kind": "check", "lookup": "Submodule.baz", "text": "it exists"}])) for concern in FILE_CONCERNS}}


def _pr_entry(**cells):
    return {"pr": PR_SUBJECT, **{concern: cells.get(concern, _cell("conforms", evidence=[
        _quote("Renames the projection lemmas to follow the convention.")])) for concern in PR_CONCERNS}}


def _typed(entry):
    if "pr" in entry:
        return PREntry(**entry)
    return FileEntry(**entry) if "file" in entry else DeclarationEntry(**entry)


def _record(task, *entries):
    return asyncio.run(task._record_reply_async([_typed(entry) for entry in entries]))


def _finding(**overrides):
    payload = dict(declaration="Submodule.foo_bar", concern="proof", path=FILE, line_start=3,
                   claim="the proof is longer than it needs to be", suggested_fix="use `simpa`")
    payload.update(overrides)
    return FilingFinding(**payload)


def _fake_checks(task, monkeypatch, *, compile_outcome=VERIFIED, lookup_count=1):
    async def compile_edit(finding):
        return compile_outcome, {"check": "compile", "answer": f"fake compile: {compile_outcome}"}

    async def lookup(this, identifier, limit=5, *, trace=True):
        assert trace is False
        return {"success": True, "count": lookup_count, "declared_before_this_pr": 0,
                "declared_in_this_pr": lookup_count, "results": f"hits for {identifier}"}

    async def census(this, declaration, *, trace=True):
        return {"success": True, "verdict": "emerging", "results": "census"}

    from ape.tasks.lean_tasks.formal_math.review import context_tools

    monkeypatch.setattr(task, "_compile_edit", compile_edit)
    monkeypatch.setattr(context_tools, "lookup_declaration", lookup)
    monkeypatch.setattr(context_tools, "naming_census", census)


def _captured(task):
    captured = {}

    async def terminate(result):
        captured["result"] = result

    task.termination_callback = terminate
    return captured


def test_it_is_a_registered_design_with_the_v5_spelling():
    assert DESIGNS["filing_contract"] is FilingContractTask
    assert get_task_class(FILING_TASK_TYPE) is FilingContractTask
    assert FilingContractTask.design_version == "filing_contract/1"
    assert {"ledger", "conforms_refused", "contradicted_filed_as_questions"} <= set(
        FilingContractResult.model_fields)


def test_the_contract_replaces_the_briefs_suppressing_instructions_and_lists_the_pr():
    text = _task().contract_text()
    assert "replaces the brief's instructions to predict only the changes" in text
    assert "not to report questions or what was checked" in text
    assert "there is no limit on the number of findings" in text
    assert "named `PR`" in text and "`description`" in text and "`scope`" in text
    assert "a tactic, an attribute or a generator" in text and "not only what this file does" in text


def test_a_conforms_without_verified_evidence_is_refused_and_the_call_records_nothing(monkeypatch):
    task = _task()
    _fake_checks(task, monkeypatch)
    bare = _entry("Submodule.foo_bar", name=_cell("conforms", reason="consistent with the file"))
    reply = _record(task, bare, _entry("Submodule.baz"))
    assert reply["success"] is False and "(Submodule.foo_bar, name) is `conforms` without verified evidence" in reply["error"]
    assert task._recorded() == {}
    assert task._conforms_refused == 1


def test_a_quote_must_come_from_the_subjects_own_code_not_a_siblings(monkeypatch):
    task = _task()
    _fake_checks(task, monkeypatch)
    sibling = _entry("Submodule.baz", name=_cell("conforms", evidence=[_quote("theorem foo_bar (h : p) : q := by simp [h]")]))
    assert _record(task, sibling)["success"] is False
    own = _entry("Submodule.baz", name=_cell("conforms", evidence=[_quote("lemma baz : r := rfl")]))
    assert _record(task, own)["success"] is True


def test_a_quote_too_short_to_identify_a_line_does_not_close_a_cell(monkeypatch):
    task = _task()
    _fake_checks(task, monkeypatch)
    short = _entry("Submodule.baz", name=_cell("conforms", evidence=[_quote("rfl")]))
    assert _record(task, short)["success"] is False


def test_a_check_is_a_compile_in_the_sessions_cache_or_a_lookup_the_task_finds(monkeypatch):
    task = _task()
    _fake_checks(task, monkeypatch, lookup_count=0)
    compiled = {"kind": "check", "text": "compiled the golf; it fails",
                "edit": {"path": FILE, "declaration_name": "Submodule.baz", "new_declaration": "lemma baz : r := by simp"}}
    entry = _entry("Submodule.baz", proof=_cell("conforms", evidence=[compiled]))
    assert _record(task, entry)["success"] is False, "an edit never compiled in the session is no check"
    task._edit_compiles()[edit_key(FILE, None, None, None, "Submodule.baz", "lemma baz : r := by simp")] = {
        "outcome": "compile_errors"}
    assert _record(task, entry)["success"] is True
    looked_up = _entry("Submodule.foo_bar", library=_cell("conforms", evidence=[
        {"kind": "check", "lookup": "Submodule.nonexistent", "text": "no duplicate"}]))
    assert _record(task, looked_up)["success"] is False, "a lookup the task cannot find closes nothing"


def test_a_count_or_a_convention_alone_cannot_close_a_cell(monkeypatch):
    task = _task()
    _fake_checks(task, monkeypatch)
    for evidence in ({"kind": "own", "text": "84 of 88 lemmas use this prefix"},
                     {"kind": "form", "text": "the library uses coe_"},
                     {"kind": "convention", "text": "A lemma's name states its conclusion and nothing else at all."}):
        entry = _entry("Submodule.foo_bar", name=_cell("conforms", evidence=[evidence]))
        assert _record(task, entry)["success"] is False, evidence["kind"]


def test_every_candidate_and_question_is_filed_with_its_evidence_and_ground(monkeypatch):
    task = _task()
    _fake_checks(task, monkeypatch)
    captured = _captured(task)
    ledger = [
        _entry("Submodule.foo_bar",
               proof=_cell("candidate", evidence=[{"kind": "construction", "text": "simpa closes it"}],
                           would_clear_on="worth"),
               statement=_cell("ask_author", evidence=[{"kind": "own", "text": "is h needed?"}],
                               would_clear_on="change_may_be_wrong")),
        _entry("Submodule.baz", name=_cell("candidate", would_clear_on="file_or_siblings")),
        _file_entry(), _pr_entry(scope=_cell("candidate", would_clear_on="maintainers_might_not_ask")),
    ]
    findings = [_finding(), _finding(concern="statement", claim="Is `h` needed here?"),
                _finding(declaration="Submodule.baz", concern="name", claim="baz is not descriptive",
                         suggested_fix="rename"),
                _finding(declaration=PR_SUBJECT, concern="scope", claim="the dual is missing",
                         suggested_fix="add the dual")]
    reply = asyncio.run(task._submit(findings, [_typed(entry) for entry in ledger], None, ""))
    assert reply["message"] == "Review submitted"
    result = captured["result"]
    assert len(result.findings) == 4, "nothing is withheld, and the budget of 2 is not enforced"
    cells = {(cell["declaration"], cell["concern"]): cell for cell in result.ledger}
    assert len(cells) == 2 * len(CONCERNS) + len(FILE_CONCERNS) + len(PR_CONCERNS)
    assert cells[("Submodule.foo_bar", "proof")]["would_clear_on"] == "worth"
    assert cells[("Submodule.foo_bar", "proof")]["evidence"][0]["kind"] == "construction"
    assert cells[("Submodule.foo_bar", "statement")]["disposition"] == "ask_author"
    assert cells[(PR_SUBJECT, "scope")]["outcome"] in (VERIFIED, "unverified")


def test_a_filing_cell_needs_a_finding_and_a_finding_needs_a_filing_cell(monkeypatch):
    task = _task()
    _fake_checks(task, monkeypatch)
    ledger = [_entry("Submodule.foo_bar", proof=_cell("candidate")), _entry("Submodule.baz"),
              _file_entry(), _pr_entry()]
    reply = asyncio.run(task._submit([], [_typed(entry) for entry in ledger], None, ""))
    assert "(Submodule.foo_bar, proof) is a `candidate` with no finding" in reply["evaluation_result"].message
    reply = asyncio.run(task._submit([_finding(concern="name")], [], None, ""))
    assert "not `candidate` or `ask_author`" in reply["evaluation_result"].message


def test_a_contradicted_change_is_handed_back_then_filed_as_a_question(monkeypatch):
    task = _task()
    _fake_checks(task, monkeypatch, compile_outcome=REFUTED)
    captured = _captured(task)
    ledger = [_entry("Submodule.foo_bar", proof=_cell("candidate")), _entry("Submodule.baz"),
              _file_entry(), _pr_entry()]
    finding = _finding(edit={"declaration_name": "Submodule.foo_bar",
                             "new_declaration": "theorem foo_bar (h : p) : q := by simpa"})
    for attempt in range(LEDGER_PRESSES):
        reply = asyncio.run(task._submit([finding], [_typed(entry) for entry in ledger] if attempt == 0 else [], None, ""))
        assert reply["message"] == "Contradicted changes"
    reply = asyncio.run(task._submit([finding], [], None, ""))
    assert reply["message"] == "Review submitted"
    result = captured["result"]
    assert len(result.findings) == 1 and "Question to the author" in result.findings[0]["suggested_fix"]
    assert len(result.contradicted_filed_as_questions) == 1


def test_the_payload_carries_each_declarations_own_code_with_its_attached_docstring():
    from types import SimpleNamespace as NS

    targets = [
        NS(change_id="c1", kind="declaration", declaration_name="A.foo", declaration_kind="theorem",
           path=FILE, reviewed_code="theorem foo : p := x", attached_to=None),
        NS(change_id="c2", kind="doc_comment", declaration_name=None, declaration_kind=None,
           path=FILE, reviewed_code="/-- The foo lemma. -/", attached_to="c1"),
        NS(change_id="c3", kind="declaration", declaration_name="A.bar", declaration_kind="lemma",
           path=FILE, reviewed_code="lemma bar : q := y", attached_to=None),
    ]
    own = own_code_of(NS(targets=targets))
    assert "/-- The foo lemma. -/" in own["A.foo"] and "theorem foo" in own["A.foo"]
    assert "The foo lemma" not in own["A.bar"]
