"""The `generated_twins` producer: census convention P201 (stage 3 of the detector probe)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.mathlib_review.producers import change_graphs, producer
from src.mathlib_review.producers.generated_twins import additive

TWINS = producer("generated_twins")


def _graph(decls, base=()):
    entities, targets = [], []
    for i, (name, code) in enumerate(decls):
        entities.append({"entity_id": f"r{i}", "fullname": name, "kind": "theorem", "code": code,
                         "side": "reviewed", "path": "Mathlib/X.lean",
                         "span": {"line_start": 10 * (i + 1), "line_end": 10 * (i + 1) + 2}})
        targets.append({"change_id": f"change:{i}", "kind": "declaration", "path": "Mathlib/X.lean",
                        "reviewed_entity_ids": [f"r{i}"], "base_entity_ids": [], "diff_fragments": []})
    for j, (name, code) in enumerate(base):
        entities.append({"entity_id": f"b{j}", "fullname": name, "kind": "theorem", "code": code,
                         "side": "base", "path": "Mathlib/X.lean", "span": {"line_start": 1, "line_end": 2}})
    return {"pr_number": 1, "entities": entities, "changed_ranges": [], "targets": targets}


def test_the_additive_translation_is_word_for_word():
    assert additive("Monoid.prod_mul_one") == "AddMonoid.sum_add_zero"
    assert additive("Foo.bar") is None


def test_a_hand_written_fun_form_beside_its_source_is_stated():
    graph = _graph([("Meromorphic.fun_add", "theorem fun_add : P := x")],
                   base=[("Meromorphic.add", "theorem add : P := x")])
    (fact,) = TWINS.facts(graph)
    assert fact.convention == "P201" and "`@[to_fun]` on `Meromorphic.add`" in fact.text


def test_a_source_already_carrying_to_fun_is_silent():
    graph = _graph([("Meromorphic.fun_add", "theorem fun_add : P := x")],
                   base=[("Meromorphic.add", "@[to_fun] theorem add : P := x")])
    assert TWINS.facts(graph) == []


def test_a_hand_written_additive_twin_is_stated_and_a_ring_pair_is_not():
    group = _graph([("Group.prod_inv", "theorem prod_inv [CommGroup G] : P := x"),
                    ("AddGroup.sum_neg", "theorem sum_neg [AddCommGroup G] : P := x")])
    (fact,) = TWINS.facts(group)
    assert fact.declaration == "AddGroup.sum_neg" and "`@[to_additive]`" in fact.text
    ring = _graph([("RingHom.map_mul", "theorem map_mul [Semiring R] (f : R →+* S) : P := x"),
                   ("RingHom.map_add", "theorem map_add [Semiring R] (f : R →+* S) : P := x")])
    assert TWINS.facts(ring) == []


DEV = Path("inputs/pr_review_v4/releases/dev-medium-0.3.0")


@pytest.mark.skipif(not DEV.is_dir(), reason="needs the dev release")
def test_the_in_sample_to_fun_ask_is_reached():
    """33117, `57bcc9fd`: replace the hand-written `fun_*` lemmas with `@[to_fun]`."""
    facts = TWINS.facts(change_graphs(DEV, [33117])[33117])
    assert any("`@[to_fun]`" in f.text for f in facts), [f.text for f in facts]
