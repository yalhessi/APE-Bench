"""The `generated_twins` producer: census convention P201 (stage 3; version 2 retired the
`@[to_additive]` shape, wrong on 29 of 29 facts)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.mathlib_review.producers import change_graphs, producer

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


def test_a_hand_written_fun_form_beside_its_source_is_stated():
    graph = _graph([("Meromorphic.fun_add", "theorem fun_add : P := x")],
                   base=[("Meromorphic.add", "theorem add : P := x")])
    (fact,) = TWINS.facts(graph)
    assert fact.convention == "P201" and "`@[to_fun]` on `Meromorphic.add`" in fact.text


def test_a_source_already_carrying_to_fun_is_silent():
    graph = _graph([("Meromorphic.fun_add", "theorem fun_add : P := x")],
                   base=[("Meromorphic.add", "@[to_fun] theorem add : P := x")])
    assert TWINS.facts(graph) == []


def test_a_multiplicative_and_additive_pair_is_no_longer_a_fact():
    """The retired shape: `posLog_zero` beside `posLog_one` is a coincidence of words, not a twin."""
    graph = _graph([("Real.posLog_one", "theorem posLog_one : posLog 1 = 0 := x"),
                    ("Real.posLog_zero", "theorem posLog_zero : posLog 0 = 0 := x")])
    assert TWINS.facts(graph) == []


DEV = Path("inputs/pr_review_v4/releases/dev-medium-0.3.0")


@pytest.mark.skipif(not DEV.is_dir(), reason="needs the dev release")
def test_the_in_sample_to_fun_ask_is_reached():
    """33117, `57bcc9fd`: replace the hand-written `fun_*` lemmas with `@[to_fun]`."""
    facts = TWINS.facts(change_graphs(DEV, [33117])[33117])
    assert any("`@[to_fun]`" in f.text for f in facts), [f.text for f in facts]
