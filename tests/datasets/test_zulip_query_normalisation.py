"""A Zulip query is free text, not FTS5 syntax — and its terms are OR-ed, not AND-ed.

Both halves are regressions from the same measurement: of the 140 `zulip_search` calls the v5
runs made, **99 (71%) returned nothing**, and the zero-rate rose with query length (85% at 1-2
tokens, 60% at 5-6, 92% at 7+). Two causes, and neither was an absence in the corpus:

* Raw text reached `MATCH`, so a backtick, an apostrophe, a `.` or a bracket raised
  `OperationalError: fts5: syntax error` and the tool reported "zulip search failed".
* FTS5 ANDs adjacent terms, so a six-word question demanded all six words in one message.

The case that motivated this: the naming arm on 33337 asked
`coe_ lemma naming convention toLinearMap` and got nothing. The same terms OR-ed return the
`mathlib4 > Naming convention` thread, whose top hits include a maintainer writing "`coe`
should be a prefix" and a rename poll — the exact evidence the arm concluded did not exist.

OR is safe rather than sloppy because ranking is BM25: a message carrying more of the terms,
and rarer ones, outranks a message carrying one common word, so a conjunction hit still comes
back first when one exists.
"""

from __future__ import annotations

import pytest

from src.datasets.zulip.store import fts_query


@pytest.mark.parametrize("raw", [
    "`coe_` naming",          # fts5: syntax error near "`"
    "don't rename",           # fts5: syntax error near "'"
    "Submodule.starProjection",  # fts5: syntax error near "."
    "naming (convention)",    # fts5: syntax error near "naming"
    "a:b",                    # read as a column filter: no such column: a
])
def test_punctuation_that_used_to_be_a_syntax_error_is_now_a_term(raw):
    expression = fts_query(raw)
    assert expression, f"{raw!r} must still be searchable"
    for char in "`'.():":
        assert char not in expression, f"{char!r} must not reach the matcher"


def test_terms_are_ored_by_default():
    assert fts_query("coe_ lemma naming convention toLinearMap") == (
        '"coe_" OR "lemma" OR "naming" OR "convention" OR "toLinearMap"')


def test_match_all_restores_the_conjunction_for_a_caller_that_means_it():
    assert fts_query("naming convention", match_all=True) == '"naming" AND "convention"'


def test_lean_identifier_fragments_survive_as_single_terms():
    assert fts_query("coe_starProjection_eq_isComplProjection") == (
        '"coe_starProjection_eq_isComplProjection"')


def test_a_dotted_name_becomes_its_parts():
    """`Submodule.starProjection` is two terms, which is what OR wants: a message naming
    either half is relevant, and one naming both ranks above it."""

    assert fts_query("Submodule.starProjection") == '"Submodule" OR "starProjection"'


def test_a_query_with_no_searchable_term_is_empty_rather_than_an_error():
    assert fts_query("... !!! ???") == ""
    assert fts_query("") == ""
    assert fts_query(None) == ""


def test_the_store_returns_nothing_rather_than_matching_everything(tmp_path):
    """An empty expression must not reach `MATCH` — `MATCH ''` is an FTS5 error, and a store
    that fell back to no predicate would return the whole corpus ranked by nothing."""

    from src.datasets.zulip.store import ZulipStore

    store = ZulipStore.__new__(ZulipStore)
    store._conn = None  # any use of the connection would raise
    assert store.search("!!!") == []
