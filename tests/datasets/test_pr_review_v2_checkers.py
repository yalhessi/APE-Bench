"""Tests for the decomposed review checkers + the shared base (no network).

Covers: all three review tasks register and share the base data model; the holistic
task selects framings from PROMPT_VERSIONS; each checker carries its focused prompt
and search/verify tool defaults; the prompts format with the standard task fields.
"""

import asyncio
import logging

import ape.tasks.lean_tasks  # noqa: F401  (triggers registration)
from ape.tasks.base import get_task_class
from ape.tasks.lean_tasks.formal_math.review.base import (
    BasePRReviewData,
    BasePRReviewTask,
    VerifiedPRReviewTask,
)
from ape.tasks.lean_tasks.formal_math.pr_review_v2.duplication import (
    DUP_SYSTEM,
    DUP_USER,
    LeanPRReviewDupTask,
)
from ape.tasks.lean_tasks.formal_math.pr_review_v2.generality import (
    GEN_SYSTEM,
    GEN_USER,
    LeanPRReviewGenTask,
)
from ape.tasks.lean_tasks.formal_math.pr_review_v2.golf import (
    GOLF_SYSTEM,
    GOLF_USER,
    LeanPRReviewGolfTask,
)
from ape.tasks.lean_tasks.formal_math.pr_review_v2.task import LeanPRReviewV2Task

PROMPT_FIELDS = dict(
    pr_number=1, title="t", description="d", diff="x",
    changed_files="  - a", tool_summary="grep the repo", submit_tool_name="submit", budget=10,
)


def test_all_review_tasks_register_and_share_base():
    for tt, cls in [
        ("lean_pr_review_v2", LeanPRReviewV2Task),
        ("lean_pr_review_dup", LeanPRReviewDupTask),
        ("lean_pr_review_gen", LeanPRReviewGenTask),
        ("lean_pr_review_golf", LeanPRReviewGolfTask),
    ]:
        registered = get_task_class(tt)
        assert registered is cls
        assert registered.task_type == tt
        assert issubclass(registered, BasePRReviewTask)
        assert registered.data_class is BasePRReviewData  # one shared data model


def test_holistic_selects_framings_from_registry():
    task = LeanPRReviewV2Task.__new__(LeanPRReviewV2Task)  # _get_prompts needs no instance state
    sys_acc, _ = task._get_prompts("acceptability_v2")
    sys_mr, _ = task._get_prompts("mergeready_v1")
    assert "acceptability" in sys_acc.lower()
    assert sys_acc != sys_mr  # the two framings differ


def test_duplication_checker_is_focused_and_search_heavy():
    cfg = LeanPRReviewDupTask.task_config_class()
    assert "content_search" in cfg.enabled_tools and "lean_verify" in cfg.enabled_tools
    assert "duplicat" in DUP_SYSTEM.lower()
    # focused: it tells the agent NOT to do the other strata
    assert "only job" in DUP_SYSTEM.lower()
    assert DUP_USER.format(**PROMPT_FIELDS)  # user formats with the standard fields
    assert "replacement" in DUP_USER  # in-file verified edit


def test_generality_checker_demands_verified_stronger_statement():
    cfg = LeanPRReviewGenTask.task_config_class()
    assert "lean_verify" in cfg.enabled_tools
    assert "general" in GEN_SYSTEM.lower()
    assert "lean_verify" in GEN_SYSTEM  # must VERIFY the generalization compiles
    assert GEN_USER.format(**PROMPT_FIELDS)
    assert "replacement" in GEN_USER


def test_golf_checker_demands_verified_shorter_proof():
    cfg = LeanPRReviewGolfTask.task_config_class()
    assert "lean_verify" in cfg.enabled_tools
    assert "shorter" in GOLF_SYSTEM.lower() and "only job" in GOLF_SYSTEM.lower()
    assert "lean_verify" in GOLF_SYSTEM  # must VERIFY the shorter proof compiles
    assert GOLF_USER.format(**PROMPT_FIELDS)
    assert "replacement" in GOLF_USER


def test_checkers_enforce_verification_at_submission():
    # All three verifiable checkers submit through the kernel-gated path; the holistic
    # acceptability pass keeps the free-text submit.
    for cls in (LeanPRReviewGolfTask, LeanPRReviewDupTask, LeanPRReviewGenTask):
        assert issubclass(cls, VerifiedPRReviewTask)
    assert not issubclass(LeanPRReviewV2Task, VerifiedPRReviewTask)


def test_mark_verified_sets_evidence_and_flag():
    task = VerifiedPRReviewTask.__new__(VerifiedPRReviewTask)  # no decl_name -> no workspace access
    out = task._mark_verified([{"claim": "c", "verification": "theorem t : True := trivial"}])
    assert out[0]["verified"] is True
    assert out[0]["evidence"] == "theorem t : True := trivial"


def test_verify_gate_accepts_compiling_rejects_failing(monkeypatch):
    """The submission gate compiles each finding's `verification` and rejects any that
    fail (or are missing) — independent of the agent's claim."""
    class FakeLeanVerify:
        def __init__(self, **_):
            pass

        async def execute(self, code, **_):
            return {"success": "GOOD" in code, "errors": [{"data": "did not compile"}]}

    monkeypatch.setattr(
        "ape.toolkits.execute.lean.tools.LeanVerifyToolsProvider", FakeLeanVerify
    )
    task = VerifiedPRReviewTask.__new__(VerifiedPRReviewTask)
    task.config = None
    task.logger = logging.getLogger("test")
    findings = [
        {"claim": "ok", "verification": "GOOD: example : True := trivial"},
        {"claim": "bad-proof", "verification": "example : False := trivial"},
        {"claim": "no-snippet"},  # missing verification -> rejected
    ]
    failures = asyncio.run(task._verify_findings(findings))
    assert {i for i, _, _ in failures} == {1, 2}  # only the compiling one survives


def test_checker_prompts_are_distinct_from_holistic_and_each_other():
    holistic = LeanPRReviewV2Task.__new__(LeanPRReviewV2Task)._get_prompts("acceptability_v2")[0]
    assert len({DUP_SYSTEM, GEN_SYSTEM, GOLF_SYSTEM, holistic}) == 4


def test_in_file_verification_splices_replacement_into_patched_file(tmp_path):
    """In-file verification: `replacement` is spliced over [line_start,line_end] of the
    REVIEWED file and the whole file is recompiled — so the edit sees the PR's own new
    declarations (the harness fix). Falls back to a standalone `verification` snippet."""
    from types import SimpleNamespace
    from ape.tasks.lean_tasks.formal_math.review.base import _strip_ws_prefix

    assert _strip_ws_prefix("target/Mathlib/A.lean") == "Mathlib/A.lean"

    (tmp_path / "Mathlib").mkdir()
    f = tmp_path / "Mathlib" / "A.lean"
    f.write_text("import Mathlib.Tactic\n\ntheorem foo : True := by\n  trivial\n")
    task = VerifiedPRReviewTask.__new__(VerifiedPRReviewTask)
    task.target_workspace = SimpleNamespace(path=tmp_path)

    # in-file splice over line 4 ("  trivial")
    code, err = task._build_verification_code(
        {"path": "target/Mathlib/A.lean", "line_start": 4, "line_end": 4, "replacement": "  exact trivial"})
    assert err == "" and "exact trivial" in code and "import Mathlib.Tactic" in code  # full file, edited
    # out-of-range / missing file are rejected with a clear error, not a crash
    assert task._build_verification_code(
        {"path": "Mathlib/A.lean", "line_start": 99, "line_end": 99, "replacement": "x"})[0] is None
    assert task._build_verification_code(
        {"path": "Mathlib/Nope.lean", "line_start": 1, "line_end": 1, "replacement": "x"})[0] is None
    # fallback to a standalone snippet when no line span is given
    code2, err2 = task._build_verification_code({"verification": "example : True := trivial"})
    assert code2 == "example : True := trivial" and err2 == ""
    # neither edit nor snippet -> error
    assert task._build_verification_code({"claim": "x"})[0] is None
    # compile-as-is: omit the span -> returns the whole file unedited (cross-file/A diagnostic)
    asis, aerr = task._edited_file_code("Mathlib/A.lean", None, None, None)
    assert aerr == "" and "theorem foo" in asis and "trivial" in asis


def test_declaration_targeted_replacement_handles_match_arms(tmp_path):
    """Naming a declaration and replacing it WHOLE avoids the line-range / match-arm friction:
    the replacement is always a complete declaration, attributes are preserved, and a sibling
    declaration is untouched."""
    from types import SimpleNamespace

    (tmp_path / "Mathlib").mkdir()
    (tmp_path / "Mathlib" / "P.lean").write_text(
        "import Mathlib.Tactic\n\n"
        "@[to_additive]\nlemma foo_le : Nat -> Nat\n  | 0 => 0\n  | n + 1 => n + 1\n\n"
        "@[simp]\ntheorem after : True := trivial\n"
    )
    task = VerifiedPRReviewTask.__new__(VerifiedPRReviewTask)
    task.target_workspace = SimpleNamespace(path=tmp_path)

    new = "lemma foo_le : Nat -> Nat\n  | 0 => 0\n  | n + 1 => Nat.succ n"
    code, err = task._edited_file_code(
        "target/Mathlib/P.lean", declaration_name="foo_le", new_declaration=new)
    assert err == ""
    assert "@[to_additive]" in code            # leading attribute preserved
    assert "Nat.succ n" in code                # golf applied to the n+1 arm
    assert "theorem after : True := trivial" in code  # sibling declaration untouched
    # not-found and the gate path both work
    assert task._edited_file_code("Mathlib/P.lean", declaration_name="nope", new_declaration="x")[0] is None
    c2, e2 = task._build_verification_code(
        {"path": "Mathlib/P.lean", "declaration_name": "after",
         "new_declaration": "theorem after : True := by trivial"})
    assert e2 == "" and "by trivial" in c2
    # CRITICAL: a declaration-mode finding (no line span) must get a line anchor backfilled,
    # else the line-anchored evaluator can't locate it (anchored_predictions=0 bug).
    marked = task._mark_verified([{
        "path": "target/Mathlib/P.lean", "declaration_name": "foo_le", "claim": "golf",
        "new_declaration": "lemma foo_le : Nat -> Nat\n  | 0 => 0\n  | n + 1 => Nat.succ n"}])[0]
    assert isinstance(marked["line_start"], int) and marked["line_start"] == 4  # foo_le's keyword line


def test_lean_verify_edit_tool_is_registered_on_verified_checkers():
    """The exploration tool: agents can test an in-file edit before submitting (same primitive
    as the submission gate, so cross-file build (A) applies to both)."""
    registered = {}

    class FakeMCP:
        def tool(self, **_):
            def deco(fn):
                registered[fn.__name__] = fn
                return fn
            return deco

    task = VerifiedPRReviewTask.__new__(VerifiedPRReviewTask)
    asyncio.run(task.register_task_tools(FakeMCP()))
    assert "lean_verify_edit" in registered and "submit_findings" in registered
