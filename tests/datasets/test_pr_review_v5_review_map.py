"""Context slices: what one job is told beyond its own targets, and nothing more.

10 of 19 audited obligations cannot be concluded from the changed declaration alone, and an
arm currently sees only its own targets plus the PR title. The map supplies the difference —
but per job, because broadcasting one digest to 161 jobs pays its cost 161 times and dilutes
site reviews that need none of it.

The properties that matter are about restraint: a slice states structure and asks questions,
it never asserts a finding, and it distinguishes what is established from what is merely
suspected.
"""

from __future__ import annotations

from types import SimpleNamespace

from src.mathlib_review.agenda.components import ReviewComponent
from src.mathlib_review.agenda.review_map import (
    ContextSlice, build_slices, convention_questions, file_skeletons, slices_report,
)


def entity(eid, line):
    return SimpleNamespace(entity_id=eid, span=SimpleNamespace(line_start=line, line_end=line))


def target(cid, kind, line, name=None, path="Mathlib/A.lean"):
    return SimpleNamespace(change_id=cid, kind=kind, path=path, declaration_name=name,
                           reviewed_entity_ids=[f"e{cid}"], base_entity_ids=[])


def graph(targets, lines, pr_number=1, episode_id="e1"):
    return SimpleNamespace(
        pr_number=pr_number, episode_id=episode_id, targets=targets,
        entities=[entity(f"e{cid}", line) for cid, line in lines.items()])


def component(grain, change_ids, *, evidence="exact", subjects=(), arms=()):
    return ReviewComponent(
        component_id=f"component:{grain}:{'-'.join(change_ids)}", grain=grain, pr_number=1,
        episode_id="e1", change_ids=tuple(change_ids), subjects=tuple(subjects),
        reason=f"a {grain}", suggested_arms=tuple(arms), evidence=evidence)


def test_a_skeleton_shows_markers_against_the_declarations_around_them():
    """PR 33362 asks to move declarations inside `namespace Complex`. That is visible only as
    the ordering of a namespace marker against what follows it — a list of declarations alone
    is the diff again, and a namespace line alone answers nothing."""

    g = graph([target("a", "namespace", 52), target("b", "declaration", 58, "N.foo")],
              {"a": 52, "b": 58})
    skeleton = file_skeletons(g)[0]
    assert [row[1] for row in skeleton.rows] == ["namespace", "declaration"]


def test_a_file_with_no_structural_marker_produces_no_skeleton():
    g = graph([target("a", "declaration", 10, "N.foo")], {"a": 10})
    assert file_skeletons(g) == []


def test_skeleton_rows_are_deduplicated():
    """A target contributes the same row through both its base and reviewed entities, and a
    skeleton listing `module_doc` twice at line 11 reads as though the file had two."""

    t = target("a", "module_doc", 11)
    t.base_entity_ids = ["ea"]
    g = graph([t, target("b", "namespace", 20)], {"a": 11, "b": 20})
    rows = file_skeletons(g)[0].rows
    assert len(rows) == len(set(rows))


def test_a_hypothesis_family_is_offered_as_a_suspicion():
    fam = component("family", ["c1", "c2"], evidence="hypothesis", subjects=("N.a", "N.b"))
    text = ContextSlice("wu:1#naming", families=(fam,)).render()
    assert "may be one group" in text
    assert "are one group" not in text


def test_an_exact_family_is_stated_plainly():
    fam = component("family", ["c1", "c2"], evidence="exact", subjects=("N.a", "N.b"))
    assert "are one group" in ContextSlice("wu:1#naming", families=(fam,)).render()


def test_a_slice_never_asserts_a_finding():
    """It is context. Admission stays a property of evidence, and an arm that repeats the
    slice has established nothing."""

    fam = component("family", ["c1", "c2"], evidence="exact", subjects=("N.a",))
    text = ContextSlice("wu:1#naming", families=(fam,)).render()
    assert "Context, not findings" in text
    assert "Establish anything you report" in text


def test_conventions_point_at_review_history_not_corpus_frequency():
    """Measured: the code corpus argues against the maintainer on both naming conventions in
    this set — `toLinearMap_` 50 against `coe_`'s 4,707, dot notation 2,359 against 22,345.
    Frequency measures where the library has been, not where it is going."""

    questions = convention_questions([component("migration", ["c1"])], ["N.coe_thing"])
    kinds = {q.kind for q in questions}
    assert "rename_form" in kinds and "coercion_name" in kinds
    text = ContextSlice("wu:1#naming", conventions=tuple(questions)).render()
    assert "review history" in text
    assert "not against how common a spelling is today" in text


def test_a_primed_name_raises_its_own_question():
    questions = convention_questions([], ["N.round_eq'"])
    assert any(q.kind == "primed_name" for q in questions)


def test_a_job_is_not_told_about_a_family_wholly_inside_its_own_targets():
    """If the arm can already see every member, the family adds nothing but tokens."""

    fam = component("family", ["c1", "c2"])
    slices = build_slices(
        components_by_pr={1: [fam]}, graphs_by_episode={},
        jobs=[("wu:1#naming", 1, "e1", ["c1", "c2"])],
        subjects_by_change={}, paths_by_change={})
    assert slices["wu:1#naming"].families == ()


def test_a_job_is_told_about_a_family_that_extends_beyond_it():
    fam = component("family", ["c1", "c2"], subjects=("N.a", "N.b"))
    slices = build_slices(
        components_by_pr={1: [fam]}, graphs_by_episode={},
        jobs=[("wu:1#naming", 1, "e1", ["c1"])],
        subjects_by_change={}, paths_by_change={})
    assert slices["wu:1#naming"].families


def test_an_empty_slice_renders_to_nothing():
    """Most site jobs need no context, and a heading with nothing under it is pure cost."""

    assert ContextSlice("wu:1#docs").render() == ""


def test_the_report_counts_jobs_that_got_nothing():
    slices = {"a": ContextSlice("a"), "b": ContextSlice("b", conventions=(
        convention_questions([], ["N.x'"])[0],))}
    report = slices_report(slices)
    assert report["jobs"] == 2 and report["with_context"] == 1


# --- the floor gets context too, and the seal stays honest ------------------------------

def test_appending_context_rehashes_the_prompt():
    """A sealed plan whose `prompt_sha256` no longer matches its body certifies the wrong
    text, which is worse than carrying no hash at all."""

    from src.datasets.pr_review_v4.io import canonical_json_bytes, sha256_bytes
    from src.datasets.pr_review_v4.schema import RenderedPrompt
    from src.mathlib_review.agenda.review_map import with_context

    base = RenderedPrompt(
        work_unit_id="wu:1", renderer_version="test/1",
        system_prompt="S", user_prompt="U",
        system_sha256="x", user_sha256="y", prompt_sha256="z",
        rendered_chars=2, estimated_tokens=1, included_change_ids=["c1"])
    updated = with_context(base, "\n\nCONTEXT")
    assert updated.user_prompt.endswith("CONTEXT")
    assert updated.prompt_sha256 == sha256_bytes(canonical_json_bytes(
        {"system": "S", "user": "U\n\nCONTEXT"}))
    assert updated.rendered_chars == len("S") + len("U\n\nCONTEXT")


def test_an_empty_slice_leaves_the_prompt_untouched():
    """Most units need no context, and re-hashing an unchanged prompt would churn the plan."""

    from src.datasets.pr_review_v4.schema import RenderedPrompt
    from src.mathlib_review.agenda.review_map import with_context

    base = RenderedPrompt(
        work_unit_id="wu:1", renderer_version="test/1",
        system_prompt="S", user_prompt="U",
        system_sha256="x", user_sha256="y", prompt_sha256="z",
        rendered_chars=2, estimated_tokens=1, included_change_ids=["c1"])
    assert with_context(base, "") is base
