"""`introduction`: the shape that asks "is this already in the library, and is it sound?"

No grain triggered `duplication` or `correctness`, so neither was ever required. Measured on
the 12-PR held-out run: the lead pruned all 107 `correctness` pairs, the arm ran zero times,
and the set holds three correctness obligations -- all on PR 33149, which spent all ten of its
required slots on arms that cannot publish while the free generalist sweep found two of them
anyway.

A declaration the PR adds that did not exist at base is the trigger. Measured over the release:
it fires on 33117 (24 introductions), 33145 (6), 33149 (56), 33294 (10), 33321 (15), 33421 (17)
-- every PR carrying a duplication or correctness obligation -- and is silent on the two
control PRs, which introduce nothing at all. That silence is structural, not tuned: it is the
same failure the `site`/`docs` rule was narrowed for, where 17 of 27 required docs jobs landed
on the controls.
"""

from __future__ import annotations

from types import SimpleNamespace

from src.mathlib_review.agenda.components import GRAINS, build_components


def target(cid, *, base=None, reviewed="theorem foo : True := trivial", kind="declaration"):
    return SimpleNamespace(
        change_id=cid, kind=kind, path="Mathlib/A.lean", declaration_name=f"N.{cid}",
        declaration_kind="theorem", base_code=base, reviewed_code=reviewed,
        base_entity_ids=[], reviewed_entity_ids=[f"e{cid}"], changed_range_ids=[])


def graph(targets, pr=1):
    return SimpleNamespace(pr_number=pr, episode_id="e1", targets=targets, entities=[],
                           base_sha="b", reviewed_head_sha="r")


def _grains(components, pr=1):
    return [c for c in components if c.grain == "introduction" and c.pr_number == pr]


def test_a_new_declaration_yields_an_introduction_component():
    comps = build_components([graph([target("c1")])], [], {})
    intro = _grains(comps)
    assert len(intro) == 1
    assert set(intro[0].suggested_arms) >= {"duplication", "correctness"}


def test_a_modified_declaration_does_not():
    """It existed at base; "does this already exist?" is not the question it raises."""

    comps = build_components([graph([target("c1", base="theorem foo : True := by simp")])], [], {})
    assert _grains(comps) == []


def test_a_deleted_declaration_does_not():
    comps = build_components([graph([target("c1", base="theorem foo : True := trivial",
                                            reviewed="")])], [], {})
    assert _grains(comps) == []


def test_a_non_declaration_change_does_not():
    """A module doc is a change, not an introduction of an API surface."""

    comps = build_components([graph([target("c1", kind="module_doc")])], [], {})
    assert _grains(comps) == []


def test_it_survives_the_structural_dedup():
    """Every introduced declaration is also a `site`. `introduction` is exempt from the
    structural dedup for the same reason `migration` is: it is not a restatement of the site,
    it carries a different question and routes different arms. Deduping it would delete it."""

    comps = build_components([graph([target("c1")])], [], {})
    grains = {c.grain for c in comps if c.change_ids == ("c1",)}
    assert {"site", "introduction"} <= grains


def test_the_grain_is_in_the_vocabulary():
    assert "introduction" in GRAINS
