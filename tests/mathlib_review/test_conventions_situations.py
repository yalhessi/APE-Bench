"""The situation is where a convention lives.

Measured on the base commit: "dot notation" read over every `_of_` lemma is 5.7 % adopted; read
over `of`-lemmas whose conclusion is a namespaced predicate -- the situation the rule is actually
about -- it is 13.7 %. Same convention, 2.4x different reading, from the situation definition
alone. These extractors are the join key for every source of evidence, and a wrong one poisons
all of them at once.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.mathlib_review.conventions.situations import (
    name_form, predicate_head, situation_of,
)


def test_a_predicate_conclusion_yields_its_head():
    """`conclusion_subject` returns `unknown` here because there is no relation to take the
    left side of -- and this is exactly the shape the dot-notation convention is about."""

    assert predicate_head("IsFundamentalSequence f o g") == "IsFundamentalSequence"
    assert predicate_head("Continuous f") == "Continuous"
    assert predicate_head("x.PosSemidef") == "PosSemidef"
    assert predicate_head("(a • x).PosSemidef") == "PosSemidef"
    assert predicate_head("(f ∘ g).Continuous") == "Continuous"


def test_relations_and_quantifiers_are_not_predicates():
    assert predicate_head("a = b") is None
    assert predicate_head("s ⊆ t") is None
    assert predicate_head("∀ x, P x") is None
    assert predicate_head("¬ P x") is None
    assert predicate_head("") is None


def test_the_dot_notation_question_is_answered_per_declaration():
    """The flat and dotted spellings of one lemma share every situation key and differ on
    exactly the field the convention is about."""

    flat = situation_of("theorem", "isFundamentalSequence_of_isNormal",
                        "(h : IsNormal f) : IsFundamentalSequence f o g", "")
    dotted = situation_of("theorem", "IsFundamentalSequence.of_isNormal",
                          "(h : IsNormal f) : IsFundamentalSequence f o g", "")
    assert flat.keys() == dotted.keys()
    assert flat.keys()["of_lemma_of_predicate"] == "of:IsFundamentalSequence"
    assert flat.named_inside_predicate is False
    assert dotted.named_inside_predicate is True


def test_the_grind_family_lands_in_the_subset_goal_class_with_its_tactics():
    """The reference class rung 3b's tool needed, and the tactic multiset that shows the PR
    wrote `simpa`/`by_cases` where the class writes `grind` second."""

    situation = situation_of(
        "lemma", "Metric.minimalCover_subset",
        "(h : coveringNumber ε A ≠ ⊤) : minimalCover ε A ⊆ A",
        "by\n  by_cases h' : x\n  · simpa [minimalCover] using foo")
    keys = situation.keys()
    assert keys["goal"] == "goal:subset"
    # The gate added facets; the goal class is still there and the proof facet now says what the
    # PR's proof actually does -- the thing the maintainer's request was about.
    assert keys["proof_style"] == "proof:tactic:cases"
    assert "predicate" not in keys and "of_lemma_of_predicate" not in keys
    assert situation.tactics == ("by_cases", "simpa")
    assert situation.predicate_head is None


def test_a_tactic_in_a_comment_is_not_counted_as_used():
    situation = situation_of("lemma", "Foo.bar", "(h : x) : a = b",
                             "by\n  -- we could use grind here\n  simp")
    assert "grind" not in situation.tactics


def test_name_form_reads_the_features_naming_conventions_are_stated_over():
    form = name_form("Foo.Bar.baz_of_qux'")
    assert form["leaf"] == "baz_of_qux'"
    assert form["namespace"] == "Foo.Bar"
    assert form["is_of_lemma"] is True
    assert form["primed"] is True
    assert name_form("Foo.of_bar")["is_of_lemma"] is True


def test_proposition_facets_are_not_emitted_for_definitions():
    """A `def`'s conclusion is a type and its body is a term by construction. Before this gate
    the corpus join carried 3,750 `pred:` keys and 3,493 `proof:term` keys on defs, instances
    and abbrevs -- `pred:MetaM`, `pred:Type` -- which are not situations a proof convention can
    live in. Statement form and typeclass binders stay for every kind."""

    from src.mathlib_review.conventions.situations import situation_of

    definition = situation_of("def", "Foo.bar", "def Foo.bar [DecidableEq α] (x : α) : MetaM Unit", "do pure ()")
    keys = definition.keys()
    assert "goal" not in keys and "predicate" not in keys and "proof_style" not in keys
    assert keys["typeclass"] == "class:DecidableEq"
    assert keys["statement_form"] == "stmt:plain"
    theorem = situation_of("theorem", "Foo.baz", "theorem Foo.baz (x : α) : Continuous f", "by\n  fun_prop")
    assert theorem.keys()["predicate"] == "pred:Continuous"
    assert theorem.keys()["proof_style"] == "proof:tactic:one-liner"
