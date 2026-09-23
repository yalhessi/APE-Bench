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

from pathlib import Path

import pytest

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


# ---------------------------------------------------------------------------------------
# The grep prefilter in front of the collector's scan. `declares_identifier` still decides;
# grep only says which files are worth reading. Measured before it was added: 5.4 s per
# candidate over 8,504 files, run serially for 200 of a run's 268 candidates.


def test_a_leaf_grep_is_a_sound_prefilter_for_declares_identifier(tmp_path):
    """The property the prefilter rests on: `declares_identifier`'s pattern embeds
    `re.escape(leaf)`, so text that declares the identifier must contain the leaf literally.
    A fixed-string grep for the leaf can therefore only ever return too many files."""

    from ape.toolkits.file_system.utils import grep_candidate_files

    files = {
        "declares.lean": "theorem Finset.sum_comm : True := trivial\n",
        "declares_private.lean": "private noncomputable def sum_comm : Nat := 0\n",
        "attribute.lean": "@[simp]\nlemma sum_comm : True := trivial\n",
        "mentions_only.lean": "-- see Finset.sum_comm for the general case\nimport Mathlib\n",
        "unrelated.lean": "theorem other_thing : True := trivial\n",
    }
    for name, text in files.items():
        (tmp_path / name).write_text(text)
    paths = sorted(tmp_path.glob("*.lean"))

    declaring = {str(p) for p in paths
                 if declares_identifier(p.read_text(), "Finset.sum_comm")}
    assert {Path(p).name for p in declaring} == {
        "declares.lean", "declares_private.lean", "attribute.lean"}

    candidates = grep_candidate_files(["sum_comm"], paths, use_regex=False)
    assert candidates is not None
    assert declaring <= candidates, (
        f"prefilter dropped {declaring - candidates}, which declare the identifier")
    # It is allowed to be generous, and is: the comment-only file survives the prefilter and
    # is then rejected by `declares_identifier`, which is the whole division of labour.
    assert str(tmp_path / "mentions_only.lean") in candidates
    assert str(tmp_path / "unrelated.lean") not in candidates


def test_the_prefilter_keeps_a_dotted_identifier_by_its_leaf(tmp_path):
    """`declares_identifier` matches on the leaf, so the prefilter must search the leaf too.
    Grepping the dotted name would miss `theorem sum_comm` in a namespaced file."""

    from ape.toolkits.file_system.utils import grep_candidate_files

    (tmp_path / "ns.lean").write_text("namespace Finset\ntheorem sum_comm : True := trivial\nend Finset\n")
    paths = sorted(tmp_path.glob("*.lean"))
    assert declares_identifier(paths[0].read_text(), "Finset.sum_comm")
    assert grep_candidate_files(["sum_comm"], paths, use_regex=False) == {str(paths[0])}
    assert grep_candidate_files(["Finset.sum_comm"], paths, use_regex=False) == set(), (
        "searching the dotted name is what the leaf split exists to avoid")


def test_single_flight_computes_once_for_concurrent_callers_and_never_caches_a_failure():
    """The evidence chain's threads share their caches and miss together on the first pass; a
    replay measured 29 baseline compiles for 7 files and 17 walks for 3 workspaces before this.
    The first caller computes, the rest wait for its result. A failure is not stored: the caller
    that raised sees it, and a later caller computes afresh, as an uncached failure always did."""

    import threading
    import time

    from src.mathlib_review.evidence.evidence import single_flight

    cache, calls, results = {}, [], []

    def slow():
        calls.append(1)
        time.sleep(0.2)
        return "value"

    threads = [threading.Thread(target=lambda: results.append(single_flight(cache, "k", slow)))
               for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert len(calls) == 1 and results == ["value"] * 8

    failures = {}

    def boom():
        raise OSError("no lean")

    with pytest.raises(OSError):
        single_flight(failures, "k", boom)
    assert "k" not in failures
    assert single_flight(failures, "k", lambda: "recovered") == "recovered"
    assert single_flight(None, "k", lambda: "uncached") == "uncached"
