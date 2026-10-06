"""The whole-PR reviewer: one agent, the entire diff, no work units and no arms.

Two properties carry the experiment and are pinned here.

**It must not inherit the work-unit submission contract.** `LeanPRReviewV4CandidateTask`
enforces `change_ids` drawn from the unit, subject equality and entity membership -- a
vocabulary the baseline is deliberately never given. Inheriting it would smuggle the
decomposition into the condition that exists to do without it, and the resulting number would
be a measurement of a half-decomposed reviewer that nobody proposed.

**It must be scaffold-agnostic.** The same task runs under `ape_agent` and `claude_code`, so
those two conditions differ only in the harness and send byte-identical prompt text. That is
what makes the harness contrast interpretable at all; a whole-PR-vs-work-unit contrast cannot
have byte-identity, so this is the only place the invariant of commit 43e9d88 survives.
"""

from __future__ import annotations

import pytest

from ape.tasks.base import get_task_class
from ape.tasks.models import WorkspaceInfo
from ape.tasks.lean_tasks.formal_math.review import (
    SOLO_TASK_TYPE, SoloReviewData, SoloReviewTask,
)


def _data(**overrides):
    payload = dict(
        task_id="solo-1", pr_number=33098, pr_title="feat: minimal covers",
        pr_description="A description.", diff="--- a/Mathlib/A.lean\n+++ b/Mathlib/A.lean\n",
        changed_files=["Mathlib/A.lean"], episode_id="ep:33098",
        invocation_id="ep:33098#solo_agent",
        target_workspace=WorkspaceInfo(name="target", commit_hash="c" * 40, repo_url="x"),
    )
    payload.update(overrides)
    return SoloReviewData(**payload)


def test_the_task_type_is_registered_and_keeps_its_v5_spelling():
    """A task type is a recorded identity, not a class name -- see the package `__init__`."""

    assert SOLO_TASK_TYPE == "lean_pr_review_v5_solo"
    assert get_task_class(SOLO_TASK_TYPE) is SoloReviewTask


def test_it_does_not_inherit_the_work_unit_submission_contract():
    names = [cls.__name__ for cls in SoloReviewTask.__mro__]
    assert "BasePRReviewTask" in names
    assert "LeanPRReviewV4CandidateTask" not in names, (
        "the baseline would be handed the change-id vocabulary it exists to do without")


def test_its_data_carries_a_pr_and_an_episode_but_no_work_unit():
    data = _data()
    assert data.pr_number == 33098
    assert data.episode_id == "ep:33098"
    for smuggled in ("work_unit_id", "change_ids", "primary_subjects_by_change",
                     "rendered_user_prompt"):
        assert smuggled not in type(data).model_fields, smuggled


def test_the_prompt_names_the_pr_the_diff_and_the_submit_tool():
    """`create_user_prompt` fills a fixed set of placeholders; a template naming one it does
    not supply raises at run time, on a paid run, after the workspace is built."""

    from ape.tasks.lean_tasks.formal_math.review.solo import SOLO_SYSTEM, solo_user_template

    for bar in ("merge", "request"):
        rendered = solo_user_template(bar).format(
            pr_number=1, title="t", description="d", diff="DIFFBODY", changed_files="  - `a`",
            tool_summary="none (diff only)", submit_tool_name="submit_findings", budget=20,
        )
        assert "DIFFBODY" in rendered and "submit_findings" in rendered
    assert "maintainer" in SOLO_SYSTEM


def test_the_prompt_asks_for_a_path_and_a_line_because_anchoring_depends_on_it():
    """The baseline is judged by resolving `file:line` onto change targets. A prompt that does
    not ask for a location produces findings that cannot be anchored, and an unanchored finding
    is a measured loss -- so this is the one prompt requirement the scoring chain depends on."""

    from ape.tasks.lean_tasks.formal_math.review.solo import SOLO_USER

    assert "path" in SOLO_USER and "line_start" in SOLO_USER


def test_the_result_takes_its_episode_from_the_data_not_the_model():
    """The arms' rule, for the arms' reason: an identity the model can state is one it can get
    wrong, and every downstream join is keyed on it."""

    import inspect

    source = inspect.getsource(SoloReviewTask.create_result)
    assert "self.data.episode_id" in source


def test_the_task_is_scaffold_agnostic():
    """No *executable* line may name a scaffold. The two baseline conditions are this one task
    under two scaffolds, so a scaffold-specific branch here would silently make the harness
    contrast a prompt contrast as well -- and the prompt text is part of the executable source,
    so a scaffold named in either would do it.

    Docstrings are excluded deliberately: this module's docstring explains *why* it must run
    under both, which is the opposite of a violation. Comments never reach the AST.
    """

    import ast
    import inspect

    from ape.tasks.lean_tasks.formal_math.review import solo

    tree = ast.parse(inspect.getsource(solo))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                node.body = body[1:] or [ast.Pass()]
    executable = ast.unparse(ast.fix_missing_locations(tree))
    for scaffold_type in ("ape_agent", "claude_code", "codex"):
        assert scaffold_type not in executable, scaffold_type


# --- the contract the retrieval tools read off task.data ------------------------------------


def _attributes_the_context_tools_read():
    """Every `task.data.<attr>` in `context_tools.py`, read off the AST rather than listed."""

    import ast
    import inspect

    from ape.tasks.lean_tasks.formal_math.review import context_tools

    names = set()
    for node in ast.walk(ast.parse(inspect.getsource(context_tools))):
        if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Attribute)
                and node.value.attr == "data"
                and isinstance(node.value.value, ast.Name)
                and node.value.value.id == "task"):
            names.add(node.attr)
    return names


def test_the_solo_task_satisfies_the_contract_the_context_tools_read():
    """Granting a tool is not the same as being able to call it.

    The tools read attributes straight off `task.data` while building their trace row, and
    that happens *before* the best-effort trace write can swallow anything -- so a missing
    field is not a missing trace, it is an exception returned to the agent as the tool's
    result. Measured on the first paid run: `invocation_id` was absent, and all 3 retrieval
    calls the agent made came back as
    `'SoloReviewData' object has no attribute 'invocation_id'`. The run still closed
    `complete` with findings on disk, so nothing downstream could tell that the condition had
    reviewed the PR with its retrieval grant silently revoked.

    Derived from the AST rather than a hand-written list, so the next attribute added to a
    context tool fails here instead of in a paid run.
    """

    required = _attributes_the_context_tools_read()
    assert "invocation_id" in required, "the AST scan found nothing; the guard is vacuous"

    missing = sorted(name for name in required
                     if name not in SoloReviewData.model_fields)
    assert not missing, (
        f"the solo task grants context tools but its data lacks {missing}; every call to "
        f"them would return an AttributeError to the agent as a tool result")


def test_the_retrieval_grant_is_traceable_or_it_cannot_be_audited():
    """Two things depend on the trace existing, and both are load-bearing for this experiment:
    the fairness invariant that every condition saw the same sources under the same gate, and
    the leak audit's temporal check that each row carries a non-null `gate` and an `as_of` at
    or before the cutoff. An untraced retrieval grant is unverifiable in both directions."""

    fields = SoloReviewData.model_fields
    assert "trace_path" in fields and "retrieval_cutoff" in fields


def test_the_default_config_keeps_the_solo_prompt_and_adds_no_context():
    from ape.tasks.lean_tasks.formal_math.review.solo import (
        SOLO_SYSTEM, SoloReviewConfig, solo_context_block, solo_system_prompt,
    )

    config = SoloReviewConfig()
    assert solo_system_prompt(config) == SOLO_SYSTEM
    assert solo_context_block(config, 33098) == ""


def test_a_named_brief_replaces_the_system_prompt_and_a_missing_one_is_refused(tmp_path):
    from ape.tasks.lean_tasks.formal_math.review.solo import SoloReviewConfig, solo_system_prompt

    brief = tmp_path / "brief.md"
    brief.write_text("Act as a probe's reviewer.")
    assert solo_system_prompt(SoloReviewConfig(system_prompt_file=brief)) == "Act as a probe's reviewer."
    # Refused when the config is built, before any session (2026-10-03).
    with pytest.raises(ValueError, match="is not a file"):
        SoloReviewConfig(system_prompt_file=tmp_path / "absent.md")


def test_a_named_file_that_is_not_there_is_refused_before_any_session():
    """`--set task_config.context_file=null` arrived as the path "null" and the run sealed its plan,
    then all 15 sessions of iter_local397_unlock_D_rep1 failed on their first prompt. The null
    value is spelled `None`, and a path that is not a file is refused when the config is built."""
    from ape.tasks.lean_tasks.formal_math.review.solo import SoloReviewConfig
    from ape.utils.config_loader import parse_cli_args

    with pytest.raises(ValueError, match="context_file 'null' is not a file"):
        SoloReviewConfig(context_file="null")
    assert parse_cli_args(["task_config.context_file=None"]) == {"task_config": {"context_file": None}}
    assert SoloReviewConfig(context_file=None).context_file is None


def test_the_context_file_appends_this_prs_sections_and_refuses_a_pr_it_lacks(tmp_path):
    import json

    from ape.tasks.lean_tasks.formal_math.review.solo import SoloReviewConfig, solo_context_block

    context = tmp_path / "context.jsonl"
    context.write_text("\n".join(json.dumps(row) for row in (
        {"pr_number": 1, "sections": [{"title": "The PR model", "text": "MODEL-ONE"}]},
        {"pr_number": 2, "sections": [{"title": "The PR model", "text": "MODEL-TWO"}]})) + "\n")
    config = SoloReviewConfig(context_file=context)
    block = solo_context_block(config, 1)
    assert "## The PR model" in block and "MODEL-ONE" in block and "MODEL-TWO" not in block
    with pytest.raises(KeyError):
        solo_context_block(config, 3)



# --- the filing bar (results/pr_review_v5/probes/filing-bar-2026-09-30) ---------------------

def test_the_default_filing_bar_is_the_wording_every_earlier_run_saw():
    """"merge" must render byte-for-byte what runs before 2026-09-30 read, or every sealed
    plan's prompt changes under a name that says nothing changed."""

    from ape.tasks.lean_tasks.formal_math.review.base import submission_mandate
    from ape.tasks.lean_tasks.formal_math.review.solo import SoloReviewConfig, solo_user_template

    assert SoloReviewConfig().filing_bar == "merge"
    assert "`blocking` if a maintainer would withhold merge over it, else `advisory`" in solo_user_template("merge")
    assert "{severity_line}" not in solo_user_template("merge")
    assert "`merge_ready_as_is: true`" in submission_mandate("submit_findings", "merge")


def test_the_request_filing_bar_removes_every_merge_verdict_from_the_task():
    """The three places the task framed a finding as a merge verdict: the severity line, the
    mandate, and the submit tool's `merge_ready_as_is`. Under "request" none of them survives."""

    import inspect

    from ape.tasks.lean_tasks.formal_math.review.base import BasePRReviewTask, submission_mandate
    from ape.tasks.lean_tasks.formal_math.review.solo import solo_user_template

    template = solo_user_template("request")
    assert "withhold merge" not in template and "would request" in template
    assert "{severity_line}" not in template
    assert "merge_ready_as_is" not in submission_mandate("submit_findings", "request")

    class FakeMCP:
        def __init__(self):
            self.tools = {}

        def tool(self, **_kwargs):
            def decorate(fn):
                self.tools[fn.__name__] = fn
                return fn
            return decorate

    def registered(bar):
        # A real task, not a namespace shaped like one: the fake this replaced lacked each new
        # accessor in turn (`_review_notes`, `_plain_contract`) and broke on every one.
        import asyncio

        from ape.scaffolds.ape_agent.config import ApeAgentConfig
        from ape.tasks.lean_tasks.formal_math.review.solo import SoloReviewConfig

        mcp = FakeMCP()
        task = SoloReviewTask(_data(), ApeAgentConfig(task_config=SoloReviewConfig(filing_bar=bar)))
        task._register_lean_verify_edit = lambda mcp: None
        asyncio.run(BasePRReviewTask.register_task_tools(task, mcp))
        return set(inspect.signature(mcp.tools["submit_findings"]).parameters)

    assert "merge_ready_as_is" in registered("merge")
    assert "merge_ready_as_is" not in registered("request")
    assert registered("request") == {"findings", "confidence", "message"}


def test_the_filing_bar_is_a_closed_choice():
    import pytest
    from ape.tasks.lean_tasks.formal_math.review.solo import SoloReviewConfig

    assert SoloReviewConfig(filing_bar="request").filing_bar == "request"
    with pytest.raises(Exception):
        SoloReviewConfig(filing_bar="lenient")


def test_review_notes_off_renders_every_earlier_prompt_byte_for_byte():
    from ape.tasks.lean_tasks.formal_math.review.base import submission_mandate
    from ape.tasks.lean_tasks.formal_math.review.solo import (
        SOLO_USER, SEVERITY_LINES, SoloReviewConfig, solo_user_template,
    )

    assert SoloReviewConfig().review_notes is False
    for bar in ("merge", "request"):
        rendered = solo_user_template(bar)
        assert "{notes_line}" not in rendered and "`notes`" not in rendered
        assert rendered == SOLO_USER.replace("{severity_line}", SEVERITY_LINES[bar]).replace(
            "{notes_line}", "")
        assert submission_mandate("submit_findings", bar) == submission_mandate(
            "submit_findings", bar, False)
    assert "`notes`" in solo_user_template("request", True)
    assert "and your `notes`" in submission_mandate("submit_findings", "request", True)


def test_review_notes_is_refused_under_the_merge_bar():
    from ape.tasks.lean_tasks.formal_math.review.solo import SoloReviewConfig

    assert SoloReviewConfig(filing_bar="request", review_notes=True).review_notes
    with pytest.raises(ValueError, match="filing_bar: request only"):
        SoloReviewConfig(review_notes=True)


def test_the_notes_submission_refuses_a_blank_account_and_records_a_real_one():
    """Brief X's `notes.md` -- "what you did, object by object, including what you checked and
    found nothing wrong with" -- was written by every Claude reviewer and asked of no gpt
    condition. Here it is a required field of the call that ends the session, on a real task:
    a blank one is refused without ending the session, and a real one reaches the result."""

    import asyncio
    import inspect
    import logging

    from ape.scaffolds.ape_agent.config import ApeAgentConfig
    from ape.tasks.lean_tasks.formal_math.review.base import BasePRReviewTask
    from ape.tasks.lean_tasks.formal_math.review.solo import SoloReviewConfig, SoloReviewResult

    task = SoloReviewTask(_data(), ApeAgentConfig(
        task_config=SoloReviewConfig(filing_bar="request", review_notes=True)))
    task.logger = logging.getLogger("solo-notes")
    task._register_lean_verify_edit = lambda mcp: None

    class FakeMCP:
        def __init__(self):
            self.tools = {}

        def tool(self, **_kwargs):
            def decorate(fn):
                self.tools[fn.__name__] = fn
                return fn
            return decorate

    mcp = FakeMCP()
    asyncio.run(BasePRReviewTask.register_task_tools(task, mcp))
    submit = mcp.tools["submit_findings"]
    params = inspect.signature(submit).parameters
    assert set(params) == {"notes", "findings", "confidence", "message"}
    assert params["notes"].default is inspect.Parameter.empty

    ended = []

    async def terminate(result):
        ended.append(result)

    task.termination_callback = terminate
    refused = asyncio.run(submit(notes="  \n", findings=[]))
    assert refused["success"] is False and refused["outcome"] == "invalid_request"
    assert ended == []
    notes = "- `Foo.bar`: read it and its siblings; nothing to ask."
    asyncio.run(submit(notes=notes, findings=[]))
    assert len(ended) == 1 and isinstance(ended[0], SoloReviewResult)
    assert ended[0].review_notes == notes
    assert "`notes`" in asyncio.run(task.create_user_prompt())


def _v2_task(tmp_path, **config):
    import logging

    from ape.scaffolds.ape_agent.config import ApeAgentConfig
    from ape.tasks.lean_tasks.formal_math.review.solo import SoloReviewConfig

    context = tmp_path / "model_context.jsonl"
    context.write_text('{"pr_number": 33098, "sections": [{"title": "The PR model (pass 0)", '
                       '"text": "### `Foo.bar` (theorem, added)\\n```lean\\ntheorem Foo.bar : {x | x = x} = univ\\n```"}]}\n')
    settings = dict(filing_bar="request", review_notes=True, user_prompt="v2", context_file=context)
    settings.update(config)
    task = SoloReviewTask(_data(), ApeAgentConfig(task_config=SoloReviewConfig(**settings)))
    task.logger = logging.getLogger("solo-v2")
    return task


def test_user_prompt_v1_is_still_every_earlier_prompt():
    from ape.tasks.lean_tasks.formal_math.review.solo import (
        SOLO_USER, SEVERITY_LINES, SoloReviewConfig, solo_user_template,
    )

    config = SoloReviewConfig()
    assert (config.user_prompt, config.notes_form) == ("v1", "per_object")
    assert solo_user_template("merge") == SOLO_USER.replace(
        "{severity_line}", SEVERITY_LINES["merge"]).replace("{notes_line}", "")


def test_user_prompt_v2_drops_what_only_gpt_was_told_and_puts_the_model_before_the_diff(tmp_path):
    """The items the contract-2026-10-01 audit traced to the first solo prompt (28d40719), the
    plumbing (ee44dee3) and the 2026-08-25 mandate, none of which the Claude reviewers saw."""

    import asyncio

    prompt = asyncio.run(_v2_task(tmp_path).create_user_prompt())
    for gone in ("Investigate what you need", "look for existing declarations that overlap",
                 "`concern_family`", "`issue_kind`", "Label a finding", "at most",
                 "You MUST", "fails the task"):
        assert gone not in prompt, gone
    # The PR model is read before the diff, its Lean braces intact through `format`, and once.
    assert prompt.index("## The PR model (pass 0)") < prompt.index("## The diff")
    assert "{x | x = x}" in prompt and prompt.count("## The PR model (pass 0)") == 1
    assert "`path` and `line_start`" in prompt and "`notes`" in prompt
    assert prompt.rstrip().endswith("an empty `findings` list and your `notes`.")


def test_the_family_ledger_asks_for_every_declaration_through_its_concerns(tmp_path):
    import asyncio

    from ape.tasks.lean_tasks.formal_math.review.solo import NOTES_LINE, NOTES_LINE_FAMILY, SoloReviewConfig

    prompt = asyncio.run(_v2_task(tmp_path, notes_form="per_object_family").create_user_prompt())
    assert NOTES_LINE_FAMILY.strip() in prompt and NOTES_LINE.strip() not in prompt
    for concern in ("its proof", "how general", "already has it", "its name", "docstring", "placement"):
        assert concern in NOTES_LINE_FAMILY
    with pytest.raises(ValueError, match="notes_form needs review_notes"):
        SoloReviewConfig(notes_form="per_object_family")


def test_user_prompt_v2_stamps_the_imported_claude_pair_on_every_finding(tmp_path):
    """Not asked for labels, so none are the model's: every finding reaches the judge with the
    family an imported Claude finding carries, whatever the model sent."""

    import asyncio
    import inspect

    from ape.tasks.lean_tasks.formal_math.review.base import BasePRReviewTask
    from src.mathlib_review.analysis.probes import IMPORT_ISSUE_KIND, UNLABELLED_FAMILY

    task = _v2_task(tmp_path, finding_budget=2)
    task._register_lean_verify_edit = lambda mcp: None
    tools = {}

    class FakeMCP:
        def tool(self, **kwargs):
            def decorate(fn):
                tools[fn.__name__] = (fn, kwargs)
                return fn
            return decorate

    asyncio.run(BasePRReviewTask.register_task_tools(task, FakeMCP()))
    submit, registration = tools["submit_findings"]
    assert "INVALID" not in registration["description"]
    ended = []

    async def terminate(result):
        ended.append(result)

    task.termination_callback = terminate
    findings = [{"claim": "`Foo.bar` should be `Foo.baz`.", "concern_family": "naming",
                 "issue_kind": "naming_convention_violation", "path": "Mathlib/A.lean", "line_start": 3},
                {"claim": "`Foo.qux` duplicates `Bar.qux`."}, {"claim": "a third, past the budget"}]
    # Past the budget is refused, not truncated (2026-10-01); within it, every finding is stamped.
    refused = asyncio.run(submit(notes="- `Foo.bar`: renamed; nothing else.", findings=findings))
    assert refused["outcome"] == "invalid_request" and ended == []
    asyncio.run(submit(notes="- `Foo.bar`: renamed; nothing else.", findings=findings[:2]))
    recorded = ended[0].findings
    assert len(recorded) == 2
    assert {(f["concern_family"], f["issue_kind"]) for f in recorded} == {(UNLABELLED_FAMILY, IMPORT_ISSUE_KIND)}
    assert "user_prompt" in inspect.getsource(type(task)._normalize_findings)


def test_a_submission_past_the_budget_is_refused_not_truncated():
    """`_normalize_findings` cut the tail and warned in the log, so a finding past the budget
    vanished with nothing said to the reviewer: 2 and 4 findings on 33149 in two dev reps
    (2026-10-01). Now the call is refused and the reviewer chooses what to drop."""

    import asyncio
    import logging

    from ape.scaffolds.ape_agent.config import ApeAgentConfig
    from ape.tasks.lean_tasks.formal_math.review.base import BasePRReviewTask
    from ape.tasks.lean_tasks.formal_math.review.solo import SoloReviewConfig

    task = SoloReviewTask(_data(), ApeAgentConfig(task_config=SoloReviewConfig(finding_budget=2)))
    task.logger = logging.getLogger("solo-budget")
    task._register_lean_verify_edit = lambda mcp: None

    class FakeMCP:
        def __init__(self):
            self.tools = {}

        def tool(self, **_kwargs):
            def decorate(fn):
                self.tools[fn.__name__] = fn
                return fn
            return decorate

    mcp = FakeMCP()
    asyncio.run(BasePRReviewTask.register_task_tools(task, mcp))
    submit = mcp.tools["submit_findings"]
    ended = []

    async def terminate(result):
        ended.append(result)

    task.termination_callback = terminate
    three = [{"path": "Mathlib/A.lean", "line_start": n, "claim": f"`f{n}` is wrong"} for n in (1, 2, 3)]
    refused = asyncio.run(submit(findings=three))
    assert refused["success"] is False and refused["outcome"] == "invalid_request"
    assert "3 findings exceed" in refused["error"] and "at most 2" in refused["error"]
    assert ended == []
    asyncio.run(submit(findings=three[:2]))
    assert len(ended) == 1 and len(ended[0].findings) == 2
