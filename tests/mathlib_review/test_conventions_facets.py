"""The facets reviewers actually comment on.

The review-join gate measured what maintainers' form requests are about, on a hand-read 50 rated
by two panels: proof_style 11, statement_form 5, typeclass 4, naming 3, tactic 3. The situation
keys built before that measurement were tactic- and naming-shaped, because those were the two
conventions already known; every proof_style request came back "partial" and every typeclass
request "no". These facets are the representation that was missing.
"""

from __future__ import annotations

from src.mathlib_review.conventions.facets import (
    _split_binders, proof_structure, statement_shape, typeclass_binders,
)
from src.mathlib_review.conventions.situations import situation_of


def test_proof_structure_distinguishes_term_from_tactic_and_reads_the_closer():
    assert proof_structure("fun _ _ ↦ (cancel_right hf).mp")["mode"] == "term"
    one = proof_structure("by grind [minimalCover]")
    assert one["mode"] == "tactic" and one["one_liner"] and one["closes_with"] == "grind"
    multi = proof_structure("by\n  by_cases h : x\n  · simpa [minimalCover] using foo\n  · simp [h]")
    assert multi["case_splits"] == 1 and multi["focus_bullets"] == 2 and multi["closes_with"] == "simp"
    assert proof_structure("")["mode"] == "none"


def test_a_tactic_named_in_a_comment_is_not_a_step():
    assert proof_structure("by\n  -- maybe grind?\n  simp")["closes_with"] == "simp"


def test_binders_are_split_by_kind_with_depth_tracking():
    kinds = [k for k, _ in _split_binders("{R : Type*} [CommRing R] (I : Ideal (Fin 3 → R)) ⦃x⦄ : P")]
    assert kinds == ["implicit", "instance", "explicit", "strict"]


def test_statement_shape_reads_what_reviewers_ask_to_change():
    """'State it as an iff', 'weaken `card = 3`', 'take it as an instance argument'."""

    shape = statement_shape("{R : Type*} [CommRing R] (I : Ideal R) (h : card = 3) : I.colon ⊤ = I ↔ P")
    assert shape["conclusion_is_iff"] is True
    assert shape["instance_binders"] == 1
    assert shape["explicit_hypotheses"] == 2
    assert shape["numerals_in_hypotheses"] == 1
    assert statement_shape("(h : a) : b → c")["conclusion_is_implication"] is True


def test_typeclass_binders_read_heads_from_signature_and_section_variables():
    """'You only need `NonAssocSemiring` here' is a request about these heads."""

    found = typeclass_binders(
        "[NonAssocSemiring β] [NonAssocSemiring γ] (f : α →+* β) : Injective f",
        variables=["{R : Type*}", "[CommRing R]"])
    assert found["instance_heads"] == ["CommRing", "NonAssocSemiring"]
    assert found["instance_count"] == 3


def test_the_facets_reach_the_situation_keys():
    """So a proof_style or typeclass request can be joined on something that describes it."""

    grind_family = situation_of(
        "lemma", "Metric.minimalCover_subset",
        "(h : coveringNumber ε A ≠ ⊤) : minimalCover ε A ⊆ A",
        "by\n  by_cases h' : x\n  · simpa [minimalCover] using foo")
    assert grind_family.keys()["proof_style"] == "proof:tactic:cases"
    assert grind_family.keys()["statement_form"] == "stmt:plain"

    typeclass = situation_of(
        "theorem", "Foo.bar", "[NonAssocSemiring β] (f : α →+* β) (h : card = 3) : Injective f ↔ P",
        "fun _ _ ↦ (cancel_right hf).mp")
    assert typeclass.keys()["typeclass"] == "class:NonAssocSemiring"
    assert typeclass.keys()["proof_style"] == "proof:term"
    assert typeclass.keys()["statement_form"] == "stmt:iff+numeral-hyp"
