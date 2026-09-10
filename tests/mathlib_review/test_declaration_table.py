"""Measuring a norm over the corpus, and the ways that measurement goes quietly wrong.

Rung 3a established that `proof_idiom` cannot ask about a tactic outside its repertoire: forced
to sweep its own list, it produced 53 `simpa` variants and never wrote `grind` once. So the
question this table answers is *generative* — what closes proofs like this one — and the tests
here pin both the populations it divides by and the two ways a population becomes a lie.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.mathlib_review.retrieval.declaration_table import (
    CONCLUSION_CLASSIFIER_VERSION, DeclarationRow, DeclarationTable, MIN_CORPUS_FILES,
    conclusion_head, distribution, load_table, table_dir, trajectory, write_table,
)

BASE = "af239326a46dea977a6d5444466c14aa423f4b10"


def _table():
    try:
        return load_table(BASE)
    except (FileNotFoundError, ValueError) as exc:
        pytest.skip(f"no declaration table for {BASE}: {exc}")


# --- the classifier ---------------------------------------------------------------------

def test_conclusion_head_reads_the_outermost_relation():
    assert conclusion_head("s ⊆ t") == "subset"
    assert conclusion_head("a ≤ b") == "le"
    assert conclusion_head("a = b") == "eq"
    assert conclusion_head("p ↔ q") == "iff"
    assert conclusion_head("x ∈ s") == "mem"
    assert conclusion_head("∀ x, p x") == "quantified"
    assert conclusion_head("∃ x, p x") == "quantified"
    assert conclusion_head("Continuous f") == "other"
    assert conclusion_head("") is None


def test_a_relation_inside_a_binder_does_not_decide_the_class():
    """Depth tracking is the whole point: `(h : a = b)` must not make this an equality."""

    assert conclusion_head("(fun x => x) s ⊆ t") == "subset"
    assert conclusion_head("f (a = b) ⊆ t") == "subset"


def test_a_lambda_arrow_is_not_an_equality():
    assert conclusion_head("(fun x => x) ∈ s") == "mem"


def test_the_conclusion_must_come_from_the_first_top_level_colon():
    """The 92x error, pinned.

    The first version of this probe took the conclusion with `signature.rfind(':')` — the
    *last* top-level colon, which in a signature carrying a quantified conclusion is the
    quantifier's. It reported the `subset` population as 25 against the true 2302, in a table
    that read as authoritative.
    """

    from src.mathlib_review.evidence.operators.naming_contrast import declaration_conclusion

    signature = "(s : Set α) : ∀ x : α, x ∈ s → True"
    correct = declaration_conclusion(signature)
    assert correct == "∀ x : α, x ∈ s → True"
    assert conclusion_head(correct) == "quantified"

    # What the discarded proxy would have produced from the same signature.
    proxy = signature[signature.rfind(":") + 1:].strip()
    assert conclusion_head(proxy) == "mem"
    assert conclusion_head(proxy) != conclusion_head(correct)


# --- the populations --------------------------------------------------------------------

def test_the_corpus_populations_are_what_was_measured():
    """A regression in any extractor shows up here as a population change."""

    table = _table()
    assert table.parsed_files == 7409
    assert len(table.rows) == 168058
    assert table.is_representative()

    heads = {}
    for row in table.rows:
        heads[row.conclusion_head] = heads.get(row.conclusion_head, 0) + 1
    assert heads["eq"] == 84395
    assert heads["other"] == 42205
    assert heads["iff"] == 14919
    assert heads["le"] == 10171
    assert heads["mem"] == 6953
    assert heads["quantified"] == 6608
    assert heads["subset"] == 2302
    # A large unextracted class would mean the conclusion extractor is failing.
    assert heads[None] == 321
    assert heads[None] / len(table.rows) < 0.01


def test_the_level_buries_grind_and_the_rank_surfaces_it():
    """Both halves of the design argument, on the real corpus.

    Share says `grind` is a 1% tactic — and below 1% in the reviewed PR's own directory, which
    is *worse* than global. Rank inside the reference class the target lemma actually belongs to
    says it is the second most common thing that closes such proofs. The arm proposed `simpa`,
    which is first.
    """

    table = _table()

    def share(rows, tactic):
        rows_out = distribution(rows)["tactics"]
        found = next((item for item in rows_out if item["tactic"] == tactic), None)
        return (found["share"] if found else 0.0,
                [item["tactic"] for item in rows_out])

    overall, _ = share(table.rows, "grind")
    assert 0.010 <= overall <= 0.011                      # 1.06 %

    local, _ = share(table.select(directory="Topology/MetricSpace"), "grind")
    assert local < overall                                # 0.46 % — conditioning makes it worse

    subset_share, subset_rank = share(
        table.select(conclusion_head_="subset"), "grind")
    assert subset_share > overall                         # 2.65 %
    assert subset_rank.index("grind") == 1                # second, behind `simpa`
    assert subset_rank[0] == "simpa"


def test_the_table_cannot_see_the_prs_own_declarations():
    """Temporal safety, structurally: the table is the base commit, so every lemma the PR adds
    is absent. These five are exactly the ones the maintainer asked about."""

    table = _table()
    names = {row.fullname.rsplit(".", 1)[-1] for row in table.rows}
    for added in ("minimalCover_subset", "finite_minimalCover", "isCover_minimalCover",
                  "card_minimalCover", "maximalSeparatedSet_subset"):
        assert added not in names, f"{added} is new in PR 33098 and must not be in the table"


def test_a_distribution_always_carries_its_population_and_versions():
    table = _table()
    payload = distribution(table.select(conclusion_head_="subset"))
    assert payload["population"] == 2302
    assert payload["conclusion_classifier_version"] == CONCLUSION_CLASSIFIER_VERSION
    assert payload["tactic_vocabulary_version"]
    assert payload["vocabulary"] == "strict"


# --- the partial-checkout trap ----------------------------------------------------------

def test_a_table_built_from_a_partial_checkout_is_refused(tmp_path):
    """`evidence.py` learned this: review workspaces materialize the tree but only the files a
    task touches, and a scan of ~2% of Mathlib still clears any support threshold. A sampling
    artifact published as a repository measurement is the failure mode; abstaining is correct.
    """

    partial = DeclarationTable(snapshot_sha="deadbeef", parsed_files=120)
    partial.rows.append(DeclarationRow(
        path="Mathlib/X.lean", directory="X", namespace="X", kind="lemma",
        fullname="X.foo", conclusion_head="eq", tactics=("grind",), wide_tactics=("grind",),
        proof_lines=1))
    assert not partial.is_representative()
    write_table(partial, tmp_path)

    with pytest.raises(ValueError) as excinfo:
        load_table("deadbeef", tmp_path)
    message = str(excinfo.value)
    assert str(MIN_CORPUS_FILES) in message
    assert "sampling artifacts" in message


def test_a_representative_table_round_trips(tmp_path):
    full = DeclarationTable(snapshot_sha="cafe", parsed_files=MIN_CORPUS_FILES)
    full.rows.append(DeclarationRow(
        path="Mathlib/Y.lean", directory="Y", namespace="Y", kind="theorem",
        fullname="Y.bar", conclusion_head="subset", tactics=("simpa",),
        wide_tactics=("simp", "simpa"), proof_lines=3))
    write_table(full, tmp_path)
    back = load_table("cafe", tmp_path)
    assert back.rows == full.rows
    manifest = json.loads((table_dir("cafe", tmp_path) / "manifest.json").read_text())
    assert manifest["representative"] is True
    assert manifest["rows"] == 1


# --- trajectory -------------------------------------------------------------------------

def test_the_trajectory_is_what_makes_the_norm_visible():
    """Zero to 9.2 % of files in fourteen months, inflecting one quarter before the PR.

    Same substrate as the level, differing only in `as_of`, which is why the two are
    comparable — a discussion corpus would not have been.
    """

    from src.mathlib_review.retrieval.declaration_table import MATHLIB_CLONE

    if not MATHLIB_CLONE.is_dir():
        pytest.skip("no Mathlib clone with history")
    rows = trajectory("grind", BASE,
                      ["2024-10-01", "2025-01-01", "2025-04-01",
                       "2025-07-01", "2025-10-01", "2025-12-19"])
    shares = [row["share"] for row in rows]

    # Shape, with tolerance, not four decimal places. `rev-list -1 --before=<date>` picks the
    # newest ancestor before a midnight boundary, and adjacent ancestors differ by a file or
    # two -- an earlier measurement of this same curve landed on a neighbouring commit and read
    # 0.0921 where this one reads 0.0922. Pinning the digit made the test fail on a difference
    # of one file, which is not the claim. The claim is that the tactic went from absent to
    # widespread inside fourteen months, and that is what is asserted.
    assert shares == sorted(shares), "the curve must be monotone over these points"
    assert shares[0] == 0.0 and shares[1] == 0.0, "absent for the first year"
    assert shares[2] < 0.001 and shares[3] < 0.002, "still negligible by mid-2025"
    assert shares[4] > 0.04, "inflects in Q4 2025"
    assert shares[5] > 0.08, "widespread by the base commit"
    # And the rise is an order of magnitude, which is the part a share alone cannot show.
    assert shares[5] > 40 * max(shares[3], 1e-9)


def test_the_trajectory_cannot_reach_past_the_base_commit():
    """`rev-list --before` walks ancestors of the base, so a later date is gated by construction
    rather than by a check that could be forgotten."""

    from src.mathlib_review.retrieval.declaration_table import MATHLIB_CLONE

    if not MATHLIB_CLONE.is_dir():
        pytest.skip("no Mathlib clone with history")
    rows = trajectory("grind", BASE, ["2026-06-01"])
    assert rows[0]["commit"] == BASE[:12]
