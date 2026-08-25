"""A proposed edit must change the target it claims to be about.

`normalize_candidate_edit` checked only that the edit's path was one of the PR's *changed
files* — a PR-wide list. So an agent scheduled on file A could submit an edit to file B,
declare a `primary_change_id` in A, and pass every check; `_verify_candidate_submission`
then compiled B and awarded `verified_compile`. That hole is why per-work-unit scheduling
does not, on its own, give exact anchoring.

Enforcement needs per-target paths, which only exist from renderer `candidate-prompt/12`.
On earlier releases the check cannot run, and these tests pin that it degrades to the old
behaviour rather than silently rejecting everything.
"""

from __future__ import annotations

from ape.tasks.lean_tasks.formal_math.pr_review_v4.candidates import normalize_candidate_edit

CHANGED_FILES = ["Mathlib/A.lean", "Mathlib/B.lean"]
PATHS = {"change:a": "Mathlib/A.lean", "change:b": "Mathlib/B.lean"}


def _candidate(path, primary="change:a"):
    return {
        "primary_change_id": primary,
        "proposed_edit": {
            "path": path, "declaration_name": "Foo.bar",
            "new_declaration": "theorem Foo.bar : True := trivial",
        },
    }


def test_an_edit_to_another_file_is_rejected():
    """The hole: B is a changed file, so the old check passed it."""

    problems = []
    normalize_candidate_edit(_candidate("Mathlib/B.lean"), CHANGED_FILES, problems, PATHS)
    assert problems and "primary change target" in problems[0]


def test_an_edit_to_its_own_target_is_accepted():
    problems = []
    normalize_candidate_edit(_candidate("Mathlib/A.lean"), CHANGED_FILES, problems, PATHS)
    assert problems == []


def test_a_file_outside_the_pr_is_still_rejected():
    problems = []
    normalize_candidate_edit(_candidate("Mathlib/Other.lean"), CHANGED_FILES, problems, PATHS)
    assert problems and "changed files" in problems[0]


def test_without_per_target_paths_the_old_behaviour_is_unchanged():
    """Releases at /11 and earlier record no paths; the check degrades, it does not fire."""

    problems = []
    normalize_candidate_edit(_candidate("Mathlib/B.lean"), CHANGED_FILES, problems, {})
    assert problems == []


def test_edit_mode_validation_still_applies():
    problems = []
    candidate = _candidate("Mathlib/A.lean")
    candidate["proposed_edit"]["line_start"] = 1
    candidate["proposed_edit"]["line_end"] = 2
    candidate["proposed_edit"]["replacement"] = "x"
    normalize_candidate_edit(candidate, CHANGED_FILES, problems, PATHS)
    assert any("exactly one complete mode" in item for item in problems)
