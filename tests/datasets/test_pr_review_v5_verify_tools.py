"""The two compile tools, which are how a review claim becomes evidence.

Both were failing in ways that looked like the agent's fault and were not.

`lean_verify(file_path=...)` refused every call in the rep3 and rep4 review runs — 11 of 11
— because it accepts scratch-workspace files only, and a review task has no scratch file:
the thing worth compiling is the reviewed file under `target/`. The agents were asking the
only sensible question and being told no.

`lean_verify_edit` in declaration mode replaces from the declaration *keyword*, so any
attributes or modifiers already in the file are preserved. When the replacement supplies its
own — which agents do constantly — the two concatenate into `@[simp] @[simp] theorem …`.
That produced 32 of 58 failures on rep4 as `unexpected token '@['`, `'noncomputable'` or
`'public'`: a syntax error in code the agent did not write, on a line it never saw.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ape.tasks.lean_tasks.formal_math.review.base import (
    _declaration_prefix_start,
    _supplies_own_prefix,
)
from ape.toolkits.code.lean.lean_parser import extract_proof_blocks

#: Same-line decoration (`@[simp] theorem foo`) is the common spelling in Mathlib and was
#: the dominant real failure — an earlier version of this fix handled only decoration on its
#: own line, so these tests passed while every real call still broke.
SAME_LINE = """import Mathlib

@[simp] theorem sl : True := trivial

@[simp, norm_cast] private theorem slm : True := trivial
"""

SRC = """import Mathlib

namespace Foo

/-- The doc comment, which must survive. -/
@[simp]
theorem bar : True := trivial

noncomputable def baz : Nat := 0

@[simp, norm_cast]
private theorem qux : True := trivial

theorem plain : True := trivial

end Foo
"""


def _decl(name):
    return next(d for d in extract_proof_blocks(SRC) if d.name == name)


# --------------------------------------------------------------------------------------
# where a declaration really starts
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("name,expected", [
    ("bar", "@[simp]\n"),
    ("baz", "noncomputable "),
    ("qux", "@[simp, norm_cast]\nprivate "),
    ("plain", ""),
])
def test_the_decoration_block_is_located(name, expected):
    decl = _decl(name)
    start = _declaration_prefix_start(SRC, decl.header_span[0])
    assert SRC[start:decl.header_span[0]] == expected


def test_a_docstring_is_never_swallowed():
    """The reason this is line-based. A character offset mid-line would take the newline
    ending the docstring with it, joining `/-- doc -/` onto the replacement — one parse
    error traded for another."""

    decl = _decl("bar")
    start = _declaration_prefix_start(SRC, decl.header_span[0])
    assert SRC[:start].rstrip().endswith("-/")


def test_an_unrecognised_prefix_falls_back_to_the_keyword():
    """Anything unfamiliar keeps the old behaviour, which is always safe."""

    src = "theorem a : True := trivial\n"
    decl = next(d for d in extract_proof_blocks(src))
    assert _declaration_prefix_start(src, decl.header_span[0]) == 0


@pytest.mark.parametrize("text,expected", [
    ("@[simp]\ntheorem bar : True := trivial", True),
    ("noncomputable def baz : Nat := 1", True),
    ("private theorem qux : True := trivial", True),
    ("theorem bar : True := trivial", False),
    ("lemma bar : True := trivial", False),
    ("", False),
])
def test_self_decorated_replacements_are_recognised(text, expected):
    assert _supplies_own_prefix(text) is expected


# --------------------------------------------------------------------------------------
# the splice itself
# --------------------------------------------------------------------------------------

@pytest.fixture
def task(tmp_path):
    from ape.llm_clients.config import LLMConfig
    from ape.scaffolds.ape_agent.config import ApeAgentConfig
    from ape.tasks.lean_tasks.formal_math.review.arm import (
        ReviewArmData,
        ReviewArmTask,
    )
    from ape.tasks.models import WorkspaceInfo

    root = tmp_path / "target"
    (root / "Mathlib").mkdir(parents=True)
    (root / "Mathlib" / "A.lean").write_text(SRC)
    item = ReviewArmTask(
        ReviewArmData(
            task_id="t", invocation_id="wu:a#proof_golf", arm_id="proof_golf",
            spec_id="proof_golf", work_unit_id="wu:a", episode_id="ep:1", pr_number=1,
            diff="d", changed_files=["Mathlib/A.lean"], change_ids=["change:a"],
            entity_ids_by_change={"change:a": ["e"]},
            primary_subjects_by_change={"change:a": "Foo.bar"},
            paths_by_change={"change:a": "Mathlib/A.lean"},
            rendered_system_prompt="s", rendered_user_prompt="u",
            rendered_prompt_sha256="a" * 64,
            target_workspace={"name": "target", "commit_hash": "c" * 40,
                              "repo_url": "https://e.invalid/m.git",
                              "default_target": "Mathlib"}),
        ApeAgentConfig(llm_config=LLMConfig(model_name="gpt_5.2")))
    item.target_workspace = WorkspaceInfo(name="target", path=root)
    return item


def test_a_self_decorated_replacement_does_not_double_its_attributes(task):
    """The rep4 failure, reproduced and fixed."""

    code, err = task._edited_file_code(
        "target/Mathlib/A.lean", declaration_name="bar",
        new_declaration="@[simp]\ntheorem bar : True := by trivial")
    assert err == ""
    assert "@[simp]\n@[simp]" not in code
    assert code.count("@[simp]\ntheorem bar") == 1
    # and the docstring is still attached to it
    assert "/-- The doc comment, which must survive. -/\n@[simp]\ntheorem bar" in code


def test_a_self_decorated_modifier_does_not_double(task):
    code, err = task._edited_file_code(
        "target/Mathlib/A.lean", declaration_name="baz",
        new_declaration="noncomputable def baz : Nat := 1")
    assert err == ""
    assert "noncomputable noncomputable" not in code
    assert code.count("noncomputable def baz") == 1


def test_attributes_and_modifiers_together(task):
    code, err = task._edited_file_code(
        "target/Mathlib/A.lean", declaration_name="qux",
        new_declaration="@[simp, norm_cast]\nprivate theorem qux : True := by trivial")
    assert err == ""
    assert code.count("@[simp, norm_cast]") == 1
    assert code.count("private theorem qux") == 1


def test_an_undecorated_replacement_still_keeps_the_files_decoration(task):
    """The contract's original path, which must not regress: an agent that follows the
    instruction and omits attributes still gets them preserved."""

    code, err = task._edited_file_code(
        "target/Mathlib/A.lean", declaration_name="bar",
        new_declaration="theorem bar : True := by trivial")
    assert err == ""
    assert code.count("@[simp]") == 1
    assert "@[simp]\ntheorem bar : True := by trivial" in code


def test_workspace_prefixes_are_accepted(task):
    """Agents write `target/Mathlib/...`, `a/Mathlib/...`, or the bare path."""

    for path in ("target/Mathlib/A.lean", "Mathlib/A.lean", "a/Mathlib/A.lean",
                 "./Mathlib/A.lean"):
        code, err = task._edited_file_code(path)
        assert err == "", path
        assert code.startswith("import Mathlib"), path


def test_a_missing_declaration_says_so(task):
    code, err = task._edited_file_code(
        "Mathlib/A.lean", declaration_name="nope", new_declaration="theorem nope : True := trivial")
    assert code is None and "not found" in err


# --------------------------------------------------------------------------------------
# lean_verify's allowed roots
# --------------------------------------------------------------------------------------

def test_review_tasks_opt_in_to_reading_the_reviewed_file():
    from ape.tasks.lean_tasks.formal_math.review.base import BasePRReviewTask
    from ape.tasks.lean_tasks.formal_math.review.arm import ReviewArmTask

    assert BasePRReviewTask.lean_verify_allows_target is True
    assert ReviewArmTask.lean_verify_allows_target is True


def test_other_tasks_do_not():
    """proof_engineering's task genuinely requires a self-contained snippet — its whole
    premise is that a submission may not depend on the surrounding file."""

    from ape.tasks.lean_tasks.formal_math.proof_engineering.task import (
        LeanProofEngineeringTask,
    )

    assert getattr(LeanProofEngineeringTask, "lean_verify_allows_target", False) is False


def test_the_tool_consults_the_flag():
    import inspect

    from ape.toolkits.execute.lean import tools

    source = inspect.getsource(tools.LeanVerifyToolsProvider.register_tools)
    assert "lean_verify_allows_target" in source
    # and the refusal names the alternative rather than just saying no
    assert "lean_verify_edit" in source


# --------------------------------------------------------------------------------------
# decoration on the keyword's own line
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("name,expected", [
    ("sl", "@[simp] "),
    ("slm", "@[simp, norm_cast] private "),
])
def test_same_line_decoration_is_located(name, expected):
    decl = next(d for d in extract_proof_blocks(SAME_LINE) if d.name == name)
    start = _declaration_prefix_start(SAME_LINE, decl.header_span[0])
    assert SAME_LINE[start:decl.header_span[0]] == expected


def test_a_same_line_self_decorated_replacement_does_not_double(tmp_path):
    """The exact rep4 failure: `@[simp] theorem coe_ofAlgEquiv …` supplied against a file
    that already had `@[simp] ` on the same line, producing `@[simp] @[simp] theorem`."""

    import re

    from ape.llm_clients.config import LLMConfig
    from ape.scaffolds.ape_agent.config import ApeAgentConfig
    from ape.tasks.lean_tasks.formal_math.review.arm import (
        ReviewArmData, ReviewArmTask,
    )
    from ape.tasks.models import WorkspaceInfo

    root = tmp_path / "target"
    (root / "Mathlib").mkdir(parents=True)
    (root / "Mathlib" / "B.lean").write_text(SAME_LINE)
    task = ReviewArmTask(
        ReviewArmData(
            task_id="t", invocation_id="wu:a#proof_golf", arm_id="proof_golf",
            spec_id="proof_golf", work_unit_id="wu:a", episode_id="ep:1", pr_number=1,
            diff="d", changed_files=["Mathlib/B.lean"], change_ids=["change:a"],
            entity_ids_by_change={"change:a": ["e"]},
            primary_subjects_by_change={"change:a": "sl"},
            paths_by_change={"change:a": "Mathlib/B.lean"},
            rendered_system_prompt="s", rendered_user_prompt="u",
            rendered_prompt_sha256="a" * 64,
            target_workspace={"name": "target", "commit_hash": "c" * 40,
                              "repo_url": "https://e.invalid/m.git",
                              "default_target": "Mathlib"}),
        ApeAgentConfig(llm_config=LLMConfig(model_name="gpt_5.2")))
    task.target_workspace = WorkspaceInfo(name="target", path=root)

    code, err = task._edited_file_code(
        "target/Mathlib/B.lean", declaration_name="sl",
        new_declaration="@[simp] theorem sl : True := by trivial")
    assert err == ""
    assert not re.search(r"@\[[^\]]*\]\s*@\[", code), "attribute was duplicated"
    assert code.count("@[simp] theorem sl") == 1


def test_a_repeated_modifier_is_not_produced(tmp_path):
    import re

    src = "import Mathlib\n\nnoncomputable def d : Nat := 0\n"
    decl = next(x for x in extract_proof_blocks(src) if x.name == "d")
    start = _declaration_prefix_start(src, decl.header_span[0])
    spliced = src[:start] + "noncomputable def d : Nat := 1" + "\n\n" + src[decl.body_span[1]:]
    assert not re.search(r"\bnoncomputable\s+noncomputable\b", spliced)


# --------------------------------------------------------------------------------------
# what the agent is told when a compile fails
# --------------------------------------------------------------------------------------

def test_rejection_detail_carries_line_and_source():
    """A rejected submission used to say less than the exploration tool had already shown:
    the `data` field alone, no position, no source text — against a spliced file the agent
    never sees. `unexpected token '@['` with nothing else is a riddle, not a diagnostic."""

    from ape.tasks.lean_tasks.formal_math.review.candidates import (
        LeanPRReviewV4CandidateTask,
    )

    detail = LeanPRReviewV4CandidateTask._verification_detail({
        "success": False,
        "errors": [{"severity": "error", "data": "unexpected token '@['; expected 'lemma'",
                    "code_line": "@[simp] theorem foo : True := trivial",
                    "pos": {"line": 251, "column": 13}}],
    })
    assert "unexpected token" in detail
    assert "line 251" in detail and "col 13" in detail
    assert "@[simp] theorem foo" in detail


def test_rejection_detail_prefers_errors_the_edit_caused():
    from ape.tasks.lean_tasks.formal_math.review.candidates import (
        LeanPRReviewV4CandidateTask,
    )

    detail = LeanPRReviewV4CandidateTask._verification_detail({
        "success": False,
        "errors": [{"data": "pre-existing"}, {"data": "mine"}],
        "errors_introduced_by_your_edit": [{"data": "mine"}],
        "errors_already_in_the_file": [{"data": "pre-existing"}],
        "note": "1 error(s) came from your edit; 1 were already in the file.",
    })
    assert "mine" in detail and "pre-existing" not in detail.split("(")[0]
    assert "already in the file" in detail


def test_errors_are_split_by_whether_the_edit_caused_them(task, monkeypatch):
    """Compiling the whole file mixes three things: errors the edit introduced, errors the
    file already had, and cascade from a damaged splice. Without the split an agent reads
    errors about declarations it never touched and revises the wrong one."""

    import asyncio

    calls = {"n": 0}

    class FakeLean:
        def __init__(self, **kwargs):
            pass

        async def execute(self, code, max_messages=20):
            calls["n"] += 1
            if "by trivial" in code:          # the edited compile
                return {"success": False, "errors": [
                    {"data": "old problem elsewhere"},
                    {"data": "new problem from the edit"},
                ]}
            return {"success": False, "errors": [{"data": "old problem elsewhere"}]}

    import ape.toolkits.execute.lean.tools as tools_module

    monkeypatch.setattr(tools_module, "LeanVerifyToolsProvider", FakeLean)
    result = asyncio.run(task._attribute_errors("Mathlib/A.lean", {
        "success": False,
        "errors": [{"data": "old problem elsewhere"}, {"data": "new problem from the edit"}],
    }))
    assert [e["data"] for e in result["errors_introduced_by_your_edit"]] == [
        "new problem from the edit"]
    assert [e["data"] for e in result["errors_already_in_the_file"]] == [
        "old problem elsewhere"]
    assert "came from your edit" in result["note"]


def test_an_already_broken_file_is_named_as_such(task, monkeypatch):
    """The PR 33057 situation: the reviewed file does not compile before any edit. An agent
    told only 'compilation failed' will keep revising a correct edit."""

    import asyncio

    class FakeLean:
        def __init__(self, **kwargs):
            pass

        async def execute(self, code, max_messages=20):
            return {"success": False, "errors": [{"data": "unsolved goals at expand_apply"}]}

    import ape.toolkits.execute.lean.tools as tools_module

    monkeypatch.setattr(tools_module, "LeanVerifyToolsProvider", FakeLean)
    result = asyncio.run(task._attribute_errors("Mathlib/A.lean", {
        "success": False, "errors": [{"data": "unsolved goals at expand_apply"}]}))
    assert result["errors_introduced_by_your_edit"] == []
    assert "introduced no new errors" in result["note"]


def test_the_baseline_is_compiled_once_per_file(task, monkeypatch):
    """A full-file compile is the expensive operation; paying it once per file rather than
    once per exploratory edit is what keeps the split free."""

    import asyncio

    calls = {"n": 0}

    class FakeLean:
        def __init__(self, **kwargs):
            pass

        async def execute(self, code, max_messages=20):
            calls["n"] += 1
            return {"success": True, "errors": []}

    import ape.toolkits.execute.lean.tools as tools_module

    monkeypatch.setattr(tools_module, "LeanVerifyToolsProvider", FakeLean)
    asyncio.run(task._baseline_errors("Mathlib/A.lean"))
    asyncio.run(task._baseline_errors("target/Mathlib/A.lean"))
    asyncio.run(task._baseline_errors("Mathlib/A.lean"))
    assert calls["n"] == 1, "the baseline must be cached across calls and path spellings"


def test_error_identity_ignores_position(task):
    """Line numbers move when the file is edited, so keying on position would make every
    pre-existing error look new."""

    same = task._error_key({"data": "boom", "pos": {"line": 10}})
    moved = task._error_key({"data": "boom", "pos": {"line": 250}})
    assert same == moved


def test_a_pre_existing_error_is_never_reported_as_the_pr_failing_to_build(task, monkeypatch):
    """The note used to end "The file does not compile as it stands" -- a claim about the PR
    that this tool cannot make. On a multi-file PR the compile resolves imports through the
    base commit's build products, so a declaration the PR renames in a *sibling* file is
    `Unknown constant` here whatever the PR's real state. 41 of 321 arm sessions on the
    held-out run received exactly that; 16 findings asserted a build failure on PRs that all
    build, 4 of them published. The tool now states what was measured and names the
    environment, and stops there."""

    import asyncio

    class FakeLean:
        def __init__(self, **kwargs):
            pass

        async def execute(self, code, max_messages=20):
            return {"success": False, "errors": [
                {"data": "Unknown constant `Submodule.coe_starProjection_eq_isComplProjection`"}]}

    import ape.toolkits.execute.lean.tools as tools_module

    monkeypatch.setattr(tools_module, "LeanVerifyToolsProvider", FakeLean)
    result = asyncio.run(task._attribute_errors("Mathlib/A.lean", {
        "success": False, "errors": [
            {"data": "Unknown constant `Submodule.coe_starProjection_eq_isComplProjection`"}]}))

    assert "does not compile" not in result["note"]
    assert "in this environment" in result["note"]
    assert "base commit's build products" in result["environment"]
    assert "This PR compiles" in result["environment"]


def test_the_environment_note_is_absent_when_every_error_is_the_edits_own(task, monkeypatch):
    """No pre-existing errors, nothing to explain: the model should not be handed a caveat
    about the environment when the errors are simply its edit's."""

    import asyncio

    class FakeLean:
        def __init__(self, **kwargs):
            pass

        async def execute(self, code, max_messages=20):
            return {"success": True, "errors": []}

    import ape.toolkits.execute.lean.tools as tools_module

    monkeypatch.setattr(tools_module, "LeanVerifyToolsProvider", FakeLean)
    result = asyncio.run(task._attribute_errors("Mathlib/A.lean", {
        "success": False, "errors": [{"data": "type mismatch"}]}))

    assert result["errors_already_in_the_file"] == []
    assert "environment" not in result


# --- the two questions one tool name answers ----------------------------------------------
#
# `lean_verify_edit(path=...)` with no edit arguments asks "does this file compile?". With an
# edit it asks "is my change sound?". Both used to come back as
# `{"success": true, ..., "Lean verification completed successfully"}`, and because the
# reviewed file compiles by construction the first is a guaranteed green shaped exactly like
# a discharged verification. Measured on `pr5_A_lead_heldout12_rep1`: all 86 no-edit calls
# carried the `note` warning that they proved nothing, and the call was still the last act
# before 33 of 82 empty arm submissions — 9 of 9 for `docs`, 10 of 19 for `naming`.


class _FakeMCP:
    def __init__(self):
        self.tools = {}

    def tool(self, **_kwargs):
        def decorate(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorate


@pytest.fixture
def verify_edit(task, monkeypatch):
    """The registered tool closure, not the helper underneath it. The distinction is the
    point: `_edited_file_code` and `_baseline_errors` legitimately compile the unedited file
    and must keep working, so the refusal to *claim verification* belongs in the tool."""

    import asyncio

    compiled = {"errors": []}

    class FakeLean:
        def __init__(self, **kwargs):
            pass

        async def execute(self, code, max_messages=20):
            errors = compiled["errors"]
            return {"success": not errors, "errors": list(errors), "warnings": [],
                    "message": "Lean verification completed successfully"}

    import ape.toolkits.execute.lean.tools as tools_module
    monkeypatch.setattr(tools_module, "LeanVerifyToolsProvider", FakeLean)
    mcp = _FakeMCP()
    task._register_lean_verify_edit(mcp)
    return mcp.tools["lean_verify_edit"], compiled, asyncio


def test_a_no_edit_call_does_not_report_success(verify_edit):
    """The whole defect in one assertion. Nothing was verified, so there is no `success` to
    report, and an agent scanning for one finds no green to stop on."""

    tool, _compiled, asyncio = verify_edit
    result = asyncio.run(tool(path="Mathlib/A.lean"))
    assert "success" not in result
    assert "Lean verification completed successfully" not in str(result)


def test_a_no_edit_call_answers_the_status_question_in_its_own_vocabulary(verify_edit):
    tool, _compiled, asyncio = verify_edit
    result = asyncio.run(tool(path="Mathlib/A.lean"))
    assert result["mode"] == "as_is_compile_check"
    assert result["compiles"] is True
    assert result["errors_already_in_the_file"] == []


def test_a_no_edit_call_says_what_it_does_not_warrant(verify_edit):
    """`correctness` is told to open with this call, so it must stay available and must stay
    honest. Removing the capability would cost 33057's obligation, whose gold finding is that
    the reviewed file does not compile."""

    tool, _compiled, asyncio = verify_edit
    result = asyncio.run(tool(path="Mathlib/A.lean"))
    assert "not evidence" in result["warrants"].lower()
    assert "no edit was applied" in result["warrants"].lower()


def test_a_red_file_is_reported_as_red_with_every_error_pre_existing(verify_edit):
    """The one outcome of this call that is a finding. With no edit applied there is nothing
    for an error to have come from, so the split is true by construction — which is what the
    `correctness` prompt promised all along and never delivered, because `_attribute_errors`
    is skipped on this path."""

    tool, compiled, asyncio = verify_edit
    compiled["errors"] = [{"data": "unsolved goals at expand_apply"}]
    result = asyncio.run(tool(path="Mathlib/A.lean"))
    assert result["compiles"] is False
    assert [e["data"] for e in result["errors_already_in_the_file"]] == [
        "unsolved goals at expand_apply"]
    assert result["errors_introduced_by_your_edit"] == []


def test_an_edit_call_still_reports_success_and_is_labelled_a_verified_edit(verify_edit):
    """The other half of the contract: the mode that *can* warrant a claim is unchanged, so
    the submission gate keeps reading the field it has always read."""

    tool, _compiled, asyncio = verify_edit
    result = asyncio.run(tool(
        path="Mathlib/A.lean", declaration_name="Foo.bar",
        new_declaration="theorem bar : True := trivial"))
    assert result["mode"] == "verified_edit"
    assert result["success"] is True


def test_the_two_modes_are_not_confusable(verify_edit):
    """`schema/evidence.py:88` for the arm layer: "we did not check" and "we checked and
    found nothing" must not look alike. Same file, same green compile, two shapes."""

    tool, _compiled, asyncio = verify_edit
    as_is = asyncio.run(tool(path="Mathlib/A.lean"))
    verified = asyncio.run(tool(
        path="Mathlib/A.lean", declaration_name="Foo.bar",
        new_declaration="theorem bar : True := trivial"))
    assert set(as_is) != set(verified)
    assert "success" in verified and "success" not in as_is
    assert "warrants" in as_is and "warrants" not in verified
