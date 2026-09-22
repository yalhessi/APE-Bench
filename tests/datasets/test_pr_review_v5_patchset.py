"""A fix that spans declarations, verified as one thing or not at all.

5 of 19 audited obligations cannot be *resolved* by a reviewer confined to one edit, however
well briefed — PR 33117 needs an import, eleven attributes and thirteen deletions that only
compile together; deleting `Meromorphic.fun_add` without the attribute that regenerates it
breaks the build, so a single-edit split is correctly refused by the compile gate and the
right review comment becomes unpublishable.

What must not weaken: confinement. A patch may only touch files the component already
changes, and the whole candidate falls if any edit escapes or any touched file fails.
"""

from __future__ import annotations

from ape.tasks.lean_tasks.formal_math.review.base import splice_declaration
from src.mathlib_review.patchset import (
    MAX_PATCH_EDITS, PatchEdit, PatchSet, apply, validate, verification_artifact,
)

#: The real splice both edit paths use. `apply` takes it rather than importing it, and these
#: tests pass the real one rather than a stand-in: the defect it replaced was a substring
#: `str.replace` that every test here agreed with, because they all used single-line sources
#: whose declaration name occurred exactly once.
SPLICE = splice_declaration

ALLOWED = ["Mathlib/A.lean", "Mathlib/B.lean"]


def decl(path, name, new):
    return PatchEdit(path=path, declaration_name=name, new_declaration=new)


def span(path, start, end, text):
    return PatchEdit(path=path, line_start=start, line_end=end, replacement=text)


# --- confinement ------------------------------------------------------------------------

def test_an_edit_outside_the_component_is_refused():
    """A coordinated fix that reaches outside the change under review is not a review
    comment, it is a second PR."""

    patch = PatchSet((decl("Mathlib/A.lean", "old", "new"),
                      decl("Mathlib/Elsewhere.lean", "x", "y")))
    problems = validate(patch, ALLOWED)
    assert any("does not change" in p for p in problems)


def test_an_edit_with_no_complete_mode_is_refused():
    patch = PatchSet((PatchEdit(path="Mathlib/A.lean", declaration_name="only_a_name"),))
    assert any("exactly one complete mode" in p for p in validate(patch, ALLOWED))


def test_an_empty_patch_proposes_nothing():
    assert validate(PatchSet(()), ALLOWED)


def test_fan_out_is_bounded():
    patch = PatchSet(tuple(
        decl("Mathlib/A.lean", f"d{i}", f"e{i}") for i in range(MAX_PATCH_EDITS + 1)))
    assert any("exceeds" in p for p in validate(patch, ALLOWED))


# --- atomicity --------------------------------------------------------------------------

def test_overlapping_spans_are_refused():
    """An atomic patch whose meaning depends on application order is not atomic."""

    patch = PatchSet((span("Mathlib/A.lean", 10, 20, "x"),
                      span("Mathlib/A.lean", 15, 25, "y")))
    assert any("overlap" in p for p in validate(patch, ALLOWED))


def test_adjacent_spans_are_allowed():
    patch = PatchSet((span("Mathlib/A.lean", 10, 20, "x"),
                      span("Mathlib/A.lean", 21, 25, "y")))
    assert validate(patch, ALLOWED) == []


def test_two_edits_to_one_declaration_are_refused():
    patch = PatchSet((decl("Mathlib/A.lean", "foo", "a"),
                      decl("Mathlib/A.lean", "foo", "b")))
    assert any("both replace" in p for p in validate(patch, ALLOWED))


def test_spans_are_applied_bottom_up_so_line_numbers_stay_valid():
    """Rewriting an earlier span first shifts every later one, silently corrupting the file."""

    text = "".join(f"line{i}\n" for i in range(1, 11))
    patch = PatchSet((span("Mathlib/A.lean", 2, 3, "EARLY"),
                      span("Mathlib/A.lean", 8, 9, "LATE")))
    out, problems = apply(patch, lambda p: text, SPLICE)
    assert problems == []
    body = out["Mathlib/A.lean"].splitlines()
    assert body[1] == "EARLY"
    assert "LATE" in body
    assert body[-1] == "line10"


def test_a_missing_file_is_reported_not_skipped():
    patch = PatchSet((decl("Mathlib/A.lean", "foo", "bar"),))
    _out, problems = apply(patch, lambda p: None, SPLICE)
    assert any("not present" in p for p in problems)


def test_a_declaration_that_does_not_occur_is_reported():
    patch = PatchSet((decl("Mathlib/A.lean", "missing", "theorem x : True := trivial"),))
    _out, problems = apply(patch, lambda p: "theorem present : True := trivial\n", SPLICE)
    assert any("not found" in p for p in problems)


def test_edits_across_two_files_are_both_applied():
    """The shape PR 33337 needs: rename a pair that lives in two files."""

    patch = PatchSet((decl("Mathlib/A.lean", "old_a", "theorem new_a : True := trivial"),
                      decl("Mathlib/B.lean", "old_b", "theorem new_b : True := trivial")))
    out, problems = apply(
        patch, lambda p: f"theorem old_{p[8].lower()} : True := trivial\n", SPLICE)
    assert problems == []
    assert set(out) == {"Mathlib/A.lean", "Mathlib/B.lean"}
    assert "theorem new_a" in out["Mathlib/A.lean"]
    assert "old_a" not in out["Mathlib/A.lean"]


def test_declaration_mode_replaces_the_declaration_not_the_first_mention_of_its_name():
    """The defect this file could not see, because every source in it was one line.

    `apply` used `text.replace(declaration_name, new_declaration, 1)` under a comment claiming
    it did what the single-edit path does. On a real file the first occurrence of a
    declaration's name is its own docstring, so a well-formed edit spliced the whole
    replacement into the comment, left the declaration standing, and reported no problem --
    then compiled the wreckage and blamed the model.
    """

    src = ("/-- `Dense.continuous_sup` is the supremum form. -/\n"
           "theorem Dense.continuous_sup (h : Dense s) : True := by\n"
           "  trivial\n")
    patch = PatchSet((decl("Mathlib/A.lean", "Dense.continuous_sup",
                           "theorem Dense.upperBounds_image (h : Dense s) : True := by\n"
                           "  trivial"),))
    out, problems = apply(patch, lambda p: src, SPLICE)
    assert problems == []
    edited = out["Mathlib/A.lean"]
    assert "theorem Dense.upperBounds_image" in edited
    assert "theorem Dense.continuous_sup" not in edited
    # The docstring is untouched: it mentions the old name and is not the declaration.
    assert edited.startswith("/-- `Dense.continuous_sup` is the supremum form. -/")


def test_an_empty_replacement_deletes_the_declaration():
    """`deletion` is 3 of the 11 obligation shapes that need a coordinated fix -- PR 33066
    deletes a definition and its five simp lemmas -- and `PatchEdit.mode()` already admits an
    empty `new_declaration`."""

    src = ("theorem keep : True := trivial\n\n"
           "theorem drop_me : True := trivial\n")
    patch = PatchSet((decl("Mathlib/A.lean", "drop_me", ""),))
    out, problems = apply(patch, lambda p: src, SPLICE)
    assert problems == []
    assert "drop_me" not in out["Mathlib/A.lean"]
    assert "theorem keep" in out["Mathlib/A.lean"]


# --- the warrant ------------------------------------------------------------------------

def test_one_artifact_covers_the_whole_patch():
    """A per-file artifact set would let a candidate be half-verified, and a candidate whose
    warrant covers three of its four files has not been verified at all."""

    patch = PatchSet((decl("Mathlib/A.lean", "a", "b"), decl("Mathlib/B.lean", "c", "d")))
    art = verification_artifact(
        work_unit_id="wu:1", candidate_ordinal=0, patch=patch, success=True,
        content="compiled", snapshot_sha="abc", touched=patch.paths())
    assert art["kind"] == "lean_compile_patchset"
    assert art["paths"] == ["Mathlib/A.lean", "Mathlib/B.lean"]
    assert art["edits"] == 2
    assert art["patch_sha256"] == patch.digest()


def test_the_patch_digest_is_stable_and_order_independent_in_identity():
    a = PatchSet((decl("Mathlib/A.lean", "a", "b"),))
    b = PatchSet((decl("Mathlib/A.lean", "a", "b"),))
    assert a.digest() == b.digest()
    c = PatchSet((decl("Mathlib/A.lean", "a", "different"),))
    assert c.digest() != a.digest()


def test_an_empty_patch_never_verifies():
    """Vacuous truth is the wrong default for a warrant: `focused_findings` joins a
    successful artifact to a candidate, so "no files failed" would publish a claim backed by
    no compile at all."""

    from pathlib import Path

    from src.mathlib_review.patchset import verify

    ok, report, touched = verify(PatchSet(()), Path("/nonexistent"))
    assert ok is False and touched == []
    assert "nothing to verify" in report


# --- the capability is granted narrowly, and confinement comes from the task -------------

def _arm_task(arm_id):
    """A real `ReviewArmTask` over a real `ReviewArmData`.

    Not a `SimpleNamespace`: these tests used one for `task.data`, so they agreed with
    whatever fields the code happened to read on the day they were written and stopped
    compiling against the class. Both of the defects this file now covers survived tests in
    this file for that reason.
    """

    from ape.scaffolds.ape_agent.config import ApeAgentConfig
    from ape.tasks.lean_tasks.formal_math.review.arm import ReviewArmData, ReviewArmTask

    data = ReviewArmData(
        task_id="pr5_test", invocation_id=f"wu:abc#{arm_id}", arm_id=arm_id, spec_id=arm_id,
        work_unit_id="wu:abc", episode_id="ep:abc", pr_number=33145,
        diff="--- a\n+++ b\n", changed_files=["Mathlib/A.lean", "Mathlib/B.lean"],
        change_ids=["c1"], entity_ids_by_change={"c1": []},
        primary_subjects_by_change={"c1": "Foo.claimed", "c2": "Foo.unclaimed"},
        paths_by_change={"c1": "Mathlib/A.lean", "c2": "Mathlib/A.lean"},
        rendered_system_prompt="sys", rendered_user_prompt="usr",
        rendered_prompt_sha256="a" * 64, submission_verification_policy="none",
        context_tools=[],
        target_workspace={
            "name": "target", "commit_hash": "c" * 40,
            "repo_url": "https://example.invalid/mathlib4.git", "default_target": "Mathlib"},
    )
    return ReviewArmTask(data, ApeAgentConfig())


def _candidate(patch_set):
    return {"primary_change_id": "c1", "change_ids": ["c1"], "patch_set": patch_set}


def test_only_the_arms_a_compile_can_settle_may_carry_a_patch_set():
    """A coordinated patch's only warrant is one compile of every file it touches, so the
    grant is the arms whose claims a compile settles. An arm outside that set has no way to
    earn the warrant, and `_patch_set_error` says so rather than letting it try."""

    from src.mathlib_review.agenda import registry

    granted = _arm_task(sorted(registry.patch_set_arms())[0])
    assert granted.patch_set_paths == ("Mathlib/A.lean",)
    assert granted._patch_set_error(_candidate([
        {"path": "Mathlib/A.lean", "change_id": "c1", "declaration_name": "Foo.claimed",
         "new_declaration": "theorem Foo.claimed : True := trivial"}])) is None

    ungranted = _arm_task("naming")
    assert ungranted.patch_set_paths == ()
    assert "not accepted" in (ungranted._patch_set_error(_candidate([
        {"path": "Mathlib/A.lean", "declaration_name": "Foo.claimed",
         "new_declaration": "x"}])) or "")


def test_a_patch_cannot_widen_its_own_scope():
    """Confinement comes from the task data, never from the submission: a patch naming a file
    it would like to edit does not thereby gain permission to edit it."""

    from src.mathlib_review.agenda import registry

    task = _arm_task(sorted(registry.patch_set_arms())[0])
    error = task._patch_set_error(_candidate([
        {"path": "Mathlib/Elsewhere.lean", "change_id": "c1", "declaration_name": "a",
         "new_declaration": "b"}]))
    assert error and "does not change" in error


def test_the_submission_path_refuses_an_unclaimed_sibling():
    """End to end through the task, not just the pure checker: the unit holds `Foo.unclaimed`
    as target `c2`, the candidate claims only `c1`, and the edit rewrites the sibling."""

    from src.mathlib_review.agenda import registry

    task = _arm_task(sorted(registry.patch_set_arms())[0])
    error = task._patch_set_error(_candidate([
        {"path": "Mathlib/A.lean", "change_id": "c1", "declaration_name": "Foo.unclaimed",
         "new_declaration": "theorem Foo.unclaimed : True := trivial"}]))
    assert error and "is not one this candidate claims" in error


def test_a_candidate_with_no_patch_set_is_unaffected():
    from types import SimpleNamespace

    from ape.tasks.lean_tasks.formal_math.review.arm import ReviewArmTask

    task = ReviewArmTask.__new__(ReviewArmTask)
    task.data = SimpleNamespace(arm_id="proof_golf", change_ids=[], paths_by_change={})
    assert task._patch_set_error({"proposed_edit": {"path": "A"}}) is None


def test_every_patch_set_arm_is_a_registered_spec():
    """A capability granted to an arm that does not exist reads as coverage that is not
    there — the same defect as `code_references` sitting in `SUPPORTED_TOOLS` with its
    registration commented out."""

    from ape.tasks.lean_tasks.formal_math.review.arm import ReviewArmTask
    from src.mathlib_review.agenda.arms import specs_by_arm_id

    assert ReviewArmTask.PATCH_SET_ARMS <= set(specs_by_arm_id())


# --- confinement by anchor, not only by file ---------------------------------------------

PATHS = {"c1": "Mathlib/A.lean", "c2": "Mathlib/A.lean"}
SUBJECTS = {"c1": "Foo.claimed", "c2": "Foo.unclaimed"}


def anchored(change_id, name, new="theorem Foo.claimed : True := trivial"):
    return PatchEdit(path="Mathlib/A.lean", change_id=change_id,
                     declaration_name=name, new_declaration=new)


def test_an_edit_anchored_outside_the_candidates_targets_is_refused():
    """`validate` confines a patch to the component's files. Since the repack a unit holds up
    to a dozen declarations of one file, so file confinement alone lets an edit rewrite a
    declaration the candidate never claimed. The 2026-09-08 plan named this the precondition
    for granting patch sets more widely."""

    from src.mathlib_review.patchset import anchor_problems

    patch = PatchSet((anchored("c9", "Foo.claimed"),))
    problems = anchor_problems(patch, change_ids=["c1"], paths_by_change=PATHS,
                               subjects_by_change=SUBJECTS)
    assert any("does not claim" in p for p in problems)


def test_a_declaration_edit_may_not_rewrite_a_target_the_candidate_did_not_claim():
    """The tightening. Anchored at a claimed target, in the right file, rewriting a sibling
    the request was never about."""

    from src.mathlib_review.patchset import anchor_problems

    patch = PatchSet((anchored("c1", "Foo.unclaimed"),))
    problems = anchor_problems(patch, change_ids=["c1"], paths_by_change=PATHS,
                               subjects_by_change=SUBJECTS)
    assert any("is not one this candidate claims" in p for p in problems)

    # Claim it and the same edit is allowed: this confines, it does not forbid coordination.
    assert anchor_problems(patch, change_ids=["c1", "c2"], paths_by_change=PATHS,
                           subjects_by_change=SUBJECTS) == []


def test_an_edit_must_change_the_file_of_the_target_it_is_about():
    """`normalize_candidate_edit`'s rule for `proposed_edit`, applied per edit."""

    from src.mathlib_review.patchset import anchor_problems

    patch = PatchSet((PatchEdit(path="Mathlib/B.lean", change_id="c1",
                                declaration_name="Foo.claimed", new_declaration="x"),))
    problems = anchor_problems(patch, change_ids=["c1"],
                               paths_by_change={"c1": "Mathlib/A.lean"},
                               subjects_by_change=SUBJECTS)
    assert any("must change the target it is about" in p for p in problems)


def test_a_span_edit_keeps_file_confinement_only():
    """A line span may cover an import, a `namespace` line or a blank region that belongs to
    no declaration, so there is no anchor to check it against."""

    from src.mathlib_review.patchset import anchor_problems

    patch = PatchSet((PatchEdit(path="Mathlib/A.lean", change_id="c1",
                                line_start=1, line_end=2, replacement="import Mathlib.Tactic"),))
    assert anchor_problems(patch, change_ids=["c1"], paths_by_change=PATHS,
                           subjects_by_change=SUBJECTS) == []


def test_the_anchor_is_part_of_the_patch_identity():
    """Two patches that edit different targets are different patches, so the digest the
    warrant is keyed on must say so."""

    a = PatchSet((anchored("c1", "Foo.claimed"),))
    b = PatchSet((anchored("c2", "Foo.claimed"),))
    assert a.digest() != b.digest()
