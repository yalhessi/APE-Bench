"""The `missing_attribute` producer: census convention P201's missing-attribute asks (stage 6)."""

from __future__ import annotations

from src.mathlib_review.producers import producer
from src.mathlib_review.producers.missing_attribute import attributes

MISSING = producer("missing_attribute")


def _graph(new_name, new_code, siblings):
    entities = [{"entity_id": "n", "fullname": new_name, "kind": "theorem", "code": new_code,
                 "side": "reviewed", "path": "Mathlib/X.lean", "span": {"line_start": 50, "line_end": 52}}]
    for i, (name, code) in enumerate(siblings):
        entities.append({"entity_id": f"s{i}", "fullname": name, "kind": "theorem", "code": code,
                         "side": "base", "path": "Mathlib/X.lean", "span": {"line_start": i, "line_end": i}})
    return {"pr_number": 1, "entities": entities, "changed_ranges": [], "targets": [{
        "change_id": "change:1", "kind": "declaration", "path": "Mathlib/X.lean",
        "reviewed_entity_ids": ["n"], "base_entity_ids": [], "diff_fragments": []}]}


TAGGED = [(f"G.lemma{i}", f"@[to_additive]\ntheorem lemma{i} : P := x") for i in range(4)]


def test_the_attribute_block_is_read_before_the_keyword_only():
    assert attributes("@[simp, to_additive (attr := simp)]\ntheorem foo : P := x") == {"to_additive"}
    assert attributes("theorem foo : P := by\n  -- to_additive in a comment\n  x") == set()


def test_a_new_declaration_without_the_attribute_most_siblings_carry_is_stated():
    (fact,) = MISSING.facts(_graph("G.mul_comm_left", "theorem mul_comm_left : P := x", TAGGED))
    assert fact.convention == "P201" and "`@[to_additive]`" in fact.text and "4 of the 4" in fact.text


def test_silent_when_it_carries_it_when_too_few_siblings_do_or_when_it_is_the_additive_form():
    assert MISSING.facts(_graph("G.mul_x", "@[to_additive]\ntheorem mul_x : P := x", TAGGED)) == []
    assert MISSING.facts(_graph("G.mul_x", "theorem mul_x : P := x", TAGGED[:2])) == []
    assert MISSING.facts(_graph("G.add_x", "theorem add_x : P := x", TAGGED)) == []
    untagged = [(f"G.other{i}", f"theorem other{i} : P := x") for i in range(6)]
    assert MISSING.facts(_graph("G.mul_x", "theorem mul_x : P := x", TAGGED + untagged)) == []
