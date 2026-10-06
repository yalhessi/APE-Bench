"""The `primed_names` producer: census convention P113 (stage 3 of the detector probe)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.mathlib_review.producers import change_graphs, producer

PRIMED = producer("primed_names")


def _entity(eid, name, code, line, side="reviewed"):
    return {"entity_id": eid, "fullname": name, "kind": "theorem", "code": code, "side": side,
            "path": "Mathlib/X.lean", "span": {"line_start": line, "line_end": line + 1}}


def _graph(new_name, sibling=True):
    entities = [_entity("n", new_name, f"theorem {new_name.rsplit('.', 1)[-1]} (x : α) : f x = g x := rfl", 20)]
    if sibling:
        entities.append(_entity("s", "Foo.bar", "theorem bar (x : α) : f x = h x := rfl", 10))
    return {"pr_number": 1, "entities": entities, "changed_ranges": [], "targets": [{
        "change_id": "change:1", "kind": "declaration", "path": "Mathlib/X.lean",
        "reviewed_entity_ids": ["n"], "base_entity_ids": [], "diff_fragments": []}]}


def test_a_new_primed_name_beside_its_sibling_is_stated_with_both_conclusions():
    (fact,) = PRIMED.facts(_graph("Foo.bar'"))
    assert fact.convention == "P113" and fact.line == 20
    assert "`bar` is declared at `Mathlib/X.lean:10`" in fact.text
    assert "`f x = g x`" in fact.text and "`f x = h x`" in fact.text


def test_a_primed_name_with_no_visible_sibling_is_skipped():
    assert PRIMED.facts(_graph("Foo.bar'", sibling=False)) == []


def test_an_unprimed_new_name_is_not_a_fact():
    assert PRIMED.facts(_graph("Foo.baz")) == []


DEV = Path("inputs/pr_review_v4/releases/dev-medium-0.3.0")


@pytest.mark.skipif(not DEV.is_dir(), reason="needs the dev release")
def test_the_in_sample_primed_ask_is_reached():
    """33421, `6b02b611`: rename `round_eq'` (to `round_eq_div`)."""
    facts = PRIMED.facts(change_graphs(DEV, [33421])[33421])
    assert any(f.declaration.endswith("round_eq'") for f in facts), [f.declaration for f in facts]
