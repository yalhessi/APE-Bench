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

def test_only_the_structural_arms_may_carry_a_patch_set():
    """A capability nothing granted is a capability nothing can misuse. An arm reviewing one
    site has no use for a coordinated fix, and granting it broadly would turn a bounded
    capability into a licence to rewrite whatever the arm was shown."""

    from types import SimpleNamespace

    from ape.tasks.lean_tasks.formal_math.review.arm import ReviewArmTask

    task = ReviewArmTask.__new__(ReviewArmTask)
    task.data = SimpleNamespace(
        arm_id="proof_golf", change_ids=["c1"],
        paths_by_change={"c1": "Mathlib/A.lean"})
    assert task.patch_set_paths == ()
    assert "not accepted" in (task._patch_set_error(
        {"patch_set": [{"path": "Mathlib/A.lean", "declaration_name": "a",
                        "new_declaration": "b"}]}) or "")

    task.data = SimpleNamespace(
        arm_id="family_design", change_ids=["c1"],
        paths_by_change={"c1": "Mathlib/A.lean"})
    assert task.patch_set_paths == ("Mathlib/A.lean",)
    assert task._patch_set_error(
        {"patch_set": [{"path": "Mathlib/A.lean", "declaration_name": "a",
                        "new_declaration": "b"}]}) is None


def test_a_patch_cannot_widen_its_own_scope():
    """Confinement comes from the task data, never from the submission: a patch naming a file
    it would like to edit does not thereby gain permission to edit it."""

    from types import SimpleNamespace

    from ape.tasks.lean_tasks.formal_math.review.arm import ReviewArmTask

    task = ReviewArmTask.__new__(ReviewArmTask)
    task.data = SimpleNamespace(
        arm_id="family_design", change_ids=["c1"],
        paths_by_change={"c1": "Mathlib/A.lean"})
    error = task._patch_set_error({"patch_set": [
        {"path": "Mathlib/Elsewhere.lean", "declaration_name": "a", "new_declaration": "b"}]})
    assert error and "does not change" in error


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
