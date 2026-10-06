"""The `dot_notation` producer: census conventions P108 (placement) and P057 (method call).

Pre-registered in `results/pr_review_v5/probes/convention-detectors-2026-10-06/README.md`. These
pin what each shape states and where it must stay silent: code the PR did not add, comments, a
head that does not match, a name the PR did not introduce.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.mathlib_review.producers import change_graphs, producer

DOT = producer("dot_notation")


def _graph(code: str, added: list, *, base_name=None, name="Ordinal.foo_of_bar"):
    entities = [{"entity_id": "r", "fullname": name, "kind": "theorem", "code": code,
                 "span": {"line_start": 100, "line_end": 100 + code.count("\n")}}]
    base_ids = []
    if base_name:
        entities.append({"entity_id": "b", "fullname": base_name, "kind": "theorem", "code": code,
                         "span": {"line_start": 100, "line_end": 110}})
        base_ids = ["b"]
    return {"pr_number": 1, "entities": entities, "changed_ranges": [], "targets": [{
        "change_id": "change:1", "kind": "declaration", "path": "Mathlib/X.lean",
        "reviewed_entity_ids": ["r"], "base_entity_ids": base_ids,
        "diff_fragments": ["@@ -1 +1 @@\n" + "\n".join("+" + line for line in added)]}]}


PLACED = "theorem isFoo_of_bar (h : Bar x) : IsFoo x := by\n  exact h.isFoo\n"
CALLED = ("theorem baz (H : Order.IsNormal f) (s : Set α) : P f := by\n"
          "  rw [Order.IsNormal.map_iSup H (bdd _)]\n"
          "  -- Order.IsNormal.map_sSup H in a comment is not code\n"
          "  exact Set.eq_empty_or_nonempty t\n")


def test_a_new_of_lemma_concluding_a_predicate_is_placed_in_its_namespace():
    (fact,) = DOT.facts(_graph(PLACED, PLACED.splitlines(), name="Ordinal.isFoo_of_bar"))
    assert fact.convention == "P108" and "`IsFoo.of_bar`" in fact.text and fact.line == 100


def test_placement_is_silent_for_a_name_the_pr_did_not_introduce():
    graph = _graph(PLACED, ["  exact h.isFoo"], name="Ordinal.isFoo_of_bar", base_name="Ordinal.isFoo_of_bar")
    assert [f for f in DOT.facts(graph) if f.convention == "P108"] == []


def test_a_lemma_applied_to_a_binder_of_its_namespace_can_be_a_method_call():
    graph = _graph(CALLED, CALLED.splitlines(), name="Ordinal.baz")
    facts = [f for f in DOT.facts(graph) if f.convention == "P057"]
    assert [f.text for f in facts] == [
        "`Order.IsNormal.map_iSup H` applies a `IsNormal` lemma to `H : Order.IsNormal …`; "
        "it can be written `H.map_iSup`."]
    assert facts[0].line == 101   # the rw line; the comment and `t` (not a binder) are silent


def test_a_method_call_on_a_line_the_pr_did_not_add_is_not_charged_to_it():
    graph = _graph(CALLED, ["theorem baz (H : Order.IsNormal f) (s : Set α) : P f := by"], name="Ordinal.baz")
    assert [f for f in DOT.facts(graph) if f.convention == "P057"] == []


DEV = Path("inputs/pr_review_v4/releases/dev-medium-0.3.0")


@pytest.mark.skipif(not DEV.is_dir(), reason="needs the dev release")
def test_the_in_sample_placement_ask_is_stated_exactly():
    """33294, `d0038`: the maintainer's suggestion is `isFundamentalSequence.of_isNormal`."""
    facts = DOT.facts(change_graphs(DEV, [33294])[33294])
    assert any("`IsFundamentalSequence.of_isNormal`" in f.text for f in facts)


# --- dot_notation/2, stage 4: one test per condition -------------------------------------------

def _one_call(signature_binders: str, call: str):
    code = f"theorem baz {signature_binders} : Q := by\n  exact {call}\n"
    return [f for f in DOT.facts(_graph(code, code.splitlines(), name="Ordinal.baz"))
            if f.convention == "P057"]


def test_r1_a_qualified_binder_head_must_be_the_prefix():
    assert _one_call("(H : Ordinal.IsNormal f)", "Order.IsNormal.map_iSup H") == []
    assert len(_one_call("(H : Order.IsNormal f)", "Order.IsNormal.map_iSup H")) == 1
    assert len(_one_call("(H : IsNormal f)", "Order.IsNormal.map_iSup H")) == 1


def test_r2_a_variable_is_not_a_namespace():
    assert _one_call("(P : RootPairing ι R M N) (h : P.IsCrystallographic)", "P.chain_le h") == []
    assert _one_call("(h : S x)", "S.closed h") == []


def test_r3_a_relation_typed_binder_is_not_a_receiver():
    assert _one_call("(h : Fintype.card α = Fintype.card β)", "Fintype.equivOfCardEq h") == []


def test_an_argument_followed_by_a_projection_is_not_the_receiver():
    """dot_notation/3: `Finset.range F.card` applies `Finset.range` to `F.card`, not to `F`."""
    assert _one_call("(F : Finset ℕ)", "Finset.range F.card") == []
    assert _one_call("(h : IsNormal f)", "IsNormal.map_iSup h.1") == []
    assert len(_one_call("(F : Finset ℕ)", "Finset.card_pos F")) == 1
