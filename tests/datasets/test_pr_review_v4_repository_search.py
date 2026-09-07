"""The repository-search collector must not accept a claim because its prose says "the".

This is the defect that would have made a focused duplication/generality arm look
spectacular for no reason. The collector tokenised the *model's own* `requested_change` on
`[A-Za-z_][A-Za-z0-9_'.]{2,}` with a seven-word stoplist, then accepted any file containing
**any** term. Measured on a real snapshot: the term list for a realistic duplication query
was `['Finset.sum_comm', 'Replace', 'the', 'new', 'declaration', 'with', ...]`, and it hit
**400 of 400** sampled Mathlib files — an automatic `supports`, since
`evidence.py` promotes any hit to `supports` for `duplication` and `generalization`.

The existing smoke's honest zero-published result survived only because it contained zero
candidates of either family.
"""

from __future__ import annotations

from src.mathlib_review.evidence.evidence import declares_identifier, searchable_identifiers

REALISTIC_QUERY = (
    "primary=Finset.sum_comm; requested_change=Replace the new declaration with the "
    "existing Finset.sum_comm from Mathlib"
)


def test_english_prose_yields_no_search_terms():
    assert searchable_identifiers(REALISTIC_QUERY) == ["Finset.sum_comm"]
    assert searchable_identifiers(
        "primary=foo; requested_change=Replace the new one with the existing declaration"
    ) == []


def test_a_claim_naming_no_identifier_cannot_be_searched():
    """It becomes a collector failure, not a silent absence of duplicates."""

    assert searchable_identifiers("this already exists somewhere in the library") == []


def test_a_declaration_is_matched_but_a_mention_is_not():
    """A duplication claim is about an existing declaration, so a comment is not evidence."""

    declared = "theorem Finset.sum_comm (s : Finset α) : True := trivial"
    assert declares_identifier(declared, "Finset.sum_comm")
    assert declares_identifier("lemma sum_comm : True := trivial", "Finset.sum_comm")
    assert declares_identifier(
        "@[simp]\nprotected theorem Finset.sum_comm : True := trivial", "Finset.sum_comm"
    )

    assert not declares_identifier("-- see Finset.sum_comm for details", "Finset.sum_comm")
    assert not declares_identifier("import Mathlib.Finset.sum_comm", "Finset.sum_comm")
    assert not declares_identifier("  exact Finset.sum_comm h", "Finset.sum_comm")


def test_a_longer_name_containing_the_leaf_is_not_a_match():
    """`sum_comm` must not be satisfied by `sum_comm_of_foo`."""

    assert not declares_identifier(
        "theorem sum_comm_of_foo : True := trivial", "Finset.sum_comm"
    )


def test_the_rule_still_finds_real_mathlib_declarations():
    """Guard against replacing a rubber stamp with a rubber wall."""

    source = (
        "theorem equitableOn_empty [LE β] [Add β] [One β] (f : α → β) : "
        "EquitableOn ∅ f := fun a _ ha => absurd ha (Set.not_mem_empty a)\n"
    )
    assert declares_identifier(source, "equitableOn_empty")
    assert declares_identifier(source, "Finset.equitableOn_empty"), (
        "a qualified claim must match the declaration's leaf name"
    )


def test_camelcase_type_names_are_searchable_but_capitalised_english_is_not():
    """Mathlib declaration names include CamelCase compounds with no separator.

    Requiring a `.` or `_` would have silently excluded every structure and class — exactly
    the declarations a duplication claim about a new type would cite. The discriminator is
    two capitals: `IsSeparated` and `ExistingFoo` qualify, `Replace` and `Mathlib` do not.
    """

    assert searchable_identifiers("requested_change=Replace Foo with ExistingFoo.") == [
        "ExistingFoo"
    ]
    assert searchable_identifiers("this duplicates IsSeparated from Mathlib") == [
        "IsSeparated"
    ]
    for capitalised_english in ("Replace", "Mathlib", "Simplify", "Rename"):
        assert searchable_identifiers(f"{capitalised_english} the declaration") == [], (
            f"{capitalised_english!r} is an English word, not an identifier"
        )
