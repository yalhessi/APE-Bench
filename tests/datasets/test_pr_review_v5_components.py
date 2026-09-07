"""Grouping a PR's changes into the units maintainers review.

The measured motivation is narrower than it first looked, and the tests say so: of 20
anchored gold obligations on heldout11, 16 anchor at a single site, 3 need a family and 1
needs a file. So the component grain is not a fix for anchoring — it is a fix for *context*,
and for the handful of asks that genuinely are one decision about several declarations.

What must hold regardless: every changed target is reachable through some component, the
grouping is deterministic, and nothing here invents a change the graph does not contain.
"""

from __future__ import annotations

from types import SimpleNamespace

from src.mathlib_review.agenda.components import (
    build_components, centrality, components_report, _stem,
)


def target(change_id, name=None, path="Mathlib/A.lean", kind="declaration"):
    return SimpleNamespace(change_id=change_id, kind=kind, path=path,
                           declaration_name=name, base_entity_ids=[], reviewed_entity_ids=[],
                           context_refs=[], declaration_kind="theorem")


def graph(targets, pr_number=1, episode_id="e1"):
    return SimpleNamespace(pr_number=pr_number, episode_id=episode_id, targets=targets)


def relation(kind, source, related, episode_id="e1"):
    return SimpleNamespace(relation_kind=kind, source_change_id=source,
                           related_change_ids=[related], episode_id=episode_id)


def test_a_dualised_api_becomes_one_family():
    """The measured miss: `Dense.continuous_{upperBounds,lowerBounds}` yielded zero tokens
    under v4's tokeniser — `upper`/`Bounds` are under its length floor and `continuous` is on
    its stop-list — so the six declarations the maintainer treated as one API looked
    unrelated, and gold asked two things about that family that we produced neither of."""

    g = graph([
        target("change:a", "Dense.continuous_upperBounds"),
        target("change:b", "Dense.continuous_lowerBounds"),
        target("change:c", "Other.unrelated_thing"),
    ])
    families = [c for c in build_components([g], []) if c.grain == "family"]
    assert len(families) == 1
    assert set(families[0].change_ids) == {"change:a", "change:b"}


def test_a_module_doc_only_pr_still_produces_components():
    """PR 33305 is seven `module_doc` changes and no declarations. A declaration-only site
    rule gave it zero components, and its gold ask is site-local and reviewable."""

    g = graph([target("change:d", None, "Mathlib/X.lean", kind="module_doc")])
    components = build_components([g], [])
    assert [c.grain for c in components] == ["site"]
    assert "docs" in components[0].suggested_arms


def test_every_changed_target_is_reachable_through_some_component():
    g = graph([target("change:a", "N.foo"), target("change:b", "N.bar"),
               target("change:c", None, "Mathlib/B.lean", kind="module_doc")])
    covered = {cid for c in build_components([g], []) for cid in c.change_ids}
    assert covered == {"change:a", "change:b", "change:c"}


def test_components_never_invent_a_change():
    g = graph([target("change:a", "N.foo"), target("change:b", "N.foo_bar")])
    known = {"change:a", "change:b"}
    for component in build_components([g], [relation("name_family", "change:a", "change:zzz")]):
        assert set(component.change_ids) <= known


def test_grouping_is_deterministic():
    targets = [target("change:a", "N.foo_one"), target("change:b", "N.foo_two"),
               target("change:c", "N.foo_three")]
    first = [c.component_id for c in build_components([graph(targets)], [])]
    second = [c.component_id for c in build_components([graph(list(reversed(targets)))], [])]
    assert first == second


def test_centrality_counts_what_the_rest_of_the_pr_leans_on():
    """The PR-local half of importance: if the diff references it, it is what the PR is
    about, and reviewing it badly costs more than reviewing a leaf badly."""

    g = graph([target("change:core", "N.core"), target("change:x", "N.x"),
               target("change:y", "N.y")])
    scores = centrality(g, [
        relation("declaration_dependency", "change:x", "change:core"),
        relation("direct_use_of_changed_declaration", "change:y", "change:core"),
    ])
    assert scores["change:core"] == 2
    assert scores["change:x"] == 0


def test_a_stated_intent_puts_every_change_in_scope():
    """PR 33285's title says golf, its gold is two golf asks, and `proof_golf` ran zero
    times because no single site looked remarkable enough to route it."""

    episode = SimpleNamespace(
        episode_id="e1", pr_number=1,
        title=SimpleNamespace(text="chore: golf some proofs"),
        description=SimpleNamespace(text=""))
    g = graph([target("change:a", "N.foo"), target("change:b", "N.bar")])
    intents = [c for c in build_components([g], [], [episode]) if c.grain == "pr_intent"]
    assert len(intents) == 1
    assert set(intents[0].change_ids) == {"change:a", "change:b"}
    assert "proof_golf" in intents[0].suggested_arms


def test_a_rename_intent_is_a_migration_not_a_bare_intent():
    episode = SimpleNamespace(
        episode_id="e1", pr_number=1,
        title=SimpleNamespace(text="refactor: deprecate Ordinal.IsNormal for Order.IsNormal"),
        description=SimpleNamespace(text=""))
    g = graph([target("change:a", "N.foo"), target("change:b", "N.bar")])
    grains = {c.grain for c in build_components([g], [], [episode])}
    assert "migration" in grains


def test_identical_change_sets_do_not_produce_two_components():
    """A file whose every change is one family is one review unit, not two."""

    g = graph([target("change:a", "N.foo_x"), target("change:b", "N.foo_y")])
    coarse = [c for c in build_components([g], []) if c.grain != "site"]
    assert len({c.change_ids for c in coarse}) == len(coarse)


def test_the_report_names_prs_the_decomposition_did_nothing_for():
    g = graph([target("change:a", "N.alpha")], pr_number=7)
    report = components_report(build_components([g], []))
    assert report["site_only_prs"] == [7]


def test_stem_is_namespace_plus_leading_token():
    assert _stem("Dense.continuous_upperBounds") == ("Dense", "continuous")
    assert _stem("Dense.continuous_sup'") == ("Dense", "continuous")
    assert _stem("nonamespace") is None


# --- exact evidence may assert; similarity may only suggest -----------------------------

def test_relation_and_stem_groupings_are_never_merged():
    """Merging them through one union-find made PR 33294 report a fourteen-member "family"
    spanning `Ordinal.add_*` and `Ordinal.deriv_*`: stem joined A to B, `changed_siblings`
    joined B to C, a stem joined C to D, and the transitive closure swallowed unrelated APIs.
    A component asserted on that premise hands a reviewer a claim about unrelated code."""

    g = graph([
        target("change:a", "N.add_one"), target("change:b", "N.add_two"),
        target("change:c", "N.deriv_one"), target("change:d", "N.deriv_two"),
    ])
    # `changed_siblings` bridges one member of each stem group.
    rels = [relation("changed_siblings", "change:b", "change:c")]
    families = [c for c in build_components([g], rels) if c.grain == "family"]
    assert families, "expected some grouping"
    assert not any(len(f.change_ids) == 4 for f in families), (
        "the two stem groups were merged through the bridging relation")


def test_a_stem_grouping_is_labelled_a_hypothesis():
    """`Dense.continuous_*` is only a family by shared leading token — v4's tokeniser yields
    nothing for any of them — so it is a suspicion to check, not a fact to build on."""

    g = graph([target("change:a", "Dense.continuous_sup"),
               target("change:b", "Dense.continuous_inf")])
    family = next(c for c in build_components([g], []) if c.grain == "family")
    assert family.evidence == "hypothesis"
    assert "MAY be one API" in family.reason
    assert "check the statements" in family.reason


def test_a_relation_grouping_is_asserted():
    g = graph([target("change:a", "N.alpha"), target("change:b", "M.beta")])
    rels = [relation("name_family", "change:a", "change:b")]
    family = next(c for c in build_components([g], rels) if c.grain == "family")
    assert family.evidence == "exact"
    assert "MAY be" not in family.reason
