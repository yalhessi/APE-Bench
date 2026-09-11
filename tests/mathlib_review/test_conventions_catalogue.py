"""The catalogue reads enforcement from linter sets, not from whether an option exists.

Both assertions here are defects that actually occurred while building the extractor: the naive
docstring regex ran back across an earlier `-/` and attributed an unrelated comment to the option,
and reading "registered" as "enforced" would have promoted 28 switched-off capabilities into
conventions -- the same error as reading the existence of the `grind` tactic as the `grind`
convention.
"""

from __future__ import annotations

import pytest

from src.mathlib_review.conventions.catalogue import (
    CATALOGUE_VERSION, build, extract_library_notes, extract_linters, lakefile_options, linter_sets,
)
from src.mathlib_review.retrieval.declaration_table import MATHLIB_CLONE


def _tree(root, files):
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root


LINTERS = '''
/-- An unrelated helper. -/
def helper : Nat := 0

/-- The `binding` linter enforces a real rule. -/
public register_option linter.style.binding : Bool := {
  defValue := false
  descr := "binding"
}

/-- The `capability` linter is registered but switched off and in no set. -/
register_option linter.style.capability : Bool := {
  defValue := false
}

/-- The `onByDefault` linter is on without belonging to a set. -/
register_option linter.onByDefault : Bool := {
  defValue := true
}

/-- A developer regression probe, not a convention. -/
register_option linter.regress.probe : Bool := {
  defValue := false
}
'''

INIT = '''
register_linter_set linter.mathlibStandardSet :=
  linter.style.binding
  -- linter.style.retired -- disabled, deliberately not imposed downstream

register_linter_set linter.nightlyRegressionSet :=
  linter.regress.probe
'''

LAKEFILE = '''
  ⟨`linter.mathlibStandardSet, true⟩,
  ⟨`linter.style.header, true⟩,
'''


def test_enforcement_comes_from_set_membership_and_not_from_registration(tmp_path):
    """The 28 `available` options at `28908c09` are capabilities; promoting them would repeat the
    error of reading a tactic's existence as its convention."""

    workspace = _tree(tmp_path, {
        "Mathlib/Tactic/Linter/Style.lean": LINTERS,
        "Mathlib/Init.lean": INIT,
        "lakefile.lean": LAKEFILE,
    })
    tiers = {r.key: r.tier for r in extract_linters(workspace)}

    assert tiers["linter.style.binding"] == "standard"       # in the globally-enabled set
    assert tiers["linter.style.capability"] == "available"   # registered, off, unset
    assert tiers["linter.onByDefault"] == "default_on"
    # A regression probe finds where `grind` does NOT yet supersede an older tactic. Reading it as
    # "Mathlib wants grind" inverts the sign, so it gets its own tier and never `standard`.
    assert tiers["linter.regress.probe"] == "nightly"

    sets = linter_sets(workspace)
    assert sets["linter.mathlibStandardSet"]["active"] == ["linter.style.binding"]
    # A member commented out of a set carries its reason, which is evidence, so it is kept.
    assert "linter.style.retired" in sets["linter.mathlibStandardSet"]["disabled"]
    assert "linter.style.header" in lakefile_options(workspace)


def test_a_docstring_may_not_run_back_across_an_earlier_comment(tmp_path):
    """`linter.style.emptyLine` was first extracted carrying the docstring of an unrelated
    `Substring.Raw.getRange`, because the naive regex let the doc span a `-/`."""

    workspace = _tree(tmp_path, {"Mathlib/A.lean": LINTERS, "Mathlib/Init.lean": INIT})
    statements = {r.key: r.statement for r in extract_linters(workspace)}

    assert statements["linter.style.binding"] == "The `binding` linter enforces a real rule."
    assert "unrelated helper" not in statements["linter.style.binding"].lower()


def test_a_library_note_is_weighted_by_citations_not_by_existing(tmp_path):
    workspace = _tree(tmp_path, {
        "Mathlib/Notes.lean": 'library_note "widely followed" /-- Do it this way. -/\n'
                              'library_note "ignored" /-- Nobody cites this. -/\n',
        "Mathlib/User.lean": "-- See note [widely followed]\n-- See note [widely followed]\n",
    })
    rows = {r.key: r for r in extract_library_notes(workspace)}

    assert rows["widely followed"].weight == 2 and rows["widely followed"].tier == "cited"
    assert rows["ignored"].weight == 0 and rows["ignored"].tier == "uncited"
    assert rows["widely followed"].statement == "Do it this way."


def test_the_real_catalogue_records_the_revision_it_was_read_from():
    if not (MATHLIB_CLONE / "Mathlib").is_dir():
        pytest.skip("no Mathlib clone")
    payload = build(MATHLIB_CLONE)

    assert payload["schema_version"] == CATALOGUE_VERSION
    assert payload["workspace_revision"], "a catalogue that cannot name its snapshot is undatable"
    assert payload["counts"]["total"] > 50
    # Options whose docstring could not be read are reported rather than silently dropped.
    assert isinstance(payload["linter_options_without_a_readable_docstring"], list)
    assert payload["by_tier"].get("standard", 0) >= 10


# --- the pre-registration ------------------------------------------------------------------------

def test_the_calibration_thresholds_are_frozen():
    """Frozen 2026-09-11 before the first declaration was read.

    This test exists to be an obstacle. The project has fitted thresholds while looking at the
    answer twice -- `n>=2 with docstring` existed so `to_fun` would pass, and "every target with
    n>=6 is a genuine convention" was recognition of names already known. Moving a number here
    means editing an assertion that says it was frozen, which is the only protection available
    against doing it quietly.
    """

    from src.mathlib_review.conventions import catalogue as c

    assert c.CALIBRATION_SAMPLE == 30
    assert c.CALIBRATION_SEED == 20260911
    assert c.KILL_CRITERION_MIN_USEFUL_FRACTION == pytest.approx(1.0 / 3.0)
    assert c.ADHERENCE_BANDS[0] == (0.95, "settled")


def test_a_candidate_needing_a_field_the_table_lacks_is_unverifiable_not_a_silent_pass():
    """The gap has to be counted, not estimated.

    `DeclarationRow` holds no signature, attributes or binders, so statement-shape and typeclass
    candidates cannot be checked. If such a candidate quietly evaluated to a rate, the tooling gap
    would be invisible and the pilot would overstate its own reach.
    """

    from src.mathlib_review.conventions.catalogue import Candidate, adherence

    checkable = Candidate(key="k1", statement="tactic-level", requires=("tactics", "conclusion_head"))
    needs_more = Candidate(key="k2", statement="typeclass-level", requires=("signature", "binders"))

    assert checkable.verifiable and checkable.missing_fields == []
    assert not needs_more.verifiable
    assert needs_more.missing_fields == ["binders", "signature"]

    class _Table:
        rows = []

    result = adherence(_Table(), needs_more, lambda r: True, lambda r: True)
    assert result["verifiable"] is False and result["rate"] is None
    assert result["missing_fields"] == ["binders", "signature"]


def test_the_sample_is_reproducible_and_spread_across_directories():
    from src.mathlib_review.conventions.catalogue import CALIBRATION_SEED, sample

    class _Row:
        def __init__(self, directory, fullname):
            self.directory, self.fullname = directory, fullname

    class _Table:
        rows = [_Row(f"Mathlib/D{i % 40}", f"lemma_{i}") for i in range(400)]

    first = [r.fullname for r in sample(_Table(), 20, seed=CALIBRATION_SEED)]
    again = [r.fullname for r in sample(_Table(), 20, seed=CALIBRATION_SEED)]
    other = [r.fullname for r in sample(_Table(), 20, seed=CALIBRATION_SEED + 1)]

    assert first == again, "a sample must be reproducible from its recorded seed"
    assert first != other
    # One declaration per directory: uniform sampling would pool wherever the library is largest.
    assert len({r.directory for r in sample(_Table(), 20, seed=CALIBRATION_SEED)}) == 20


def test_the_verdict_is_computed_from_counts_not_from_an_impression():
    from src.mathlib_review.conventions.catalogue import Candidate, calibration_verdict

    candidates = [
        Candidate(key="a", statement="", requires=("tactics",)),                       # useful
        Candidate(key="b", statement="", requires=("kind",)),                          # useful
        Candidate(key="c", statement="", requires=("tactics",), encoded_as="linter.x"),  # encoded
        Candidate(key="d", statement="", requires=("signature",)),                     # unverifiable
    ]
    verdict = calibration_verdict(candidates)

    assert verdict["unencoded_and_checkable"] == 2
    assert verdict["already_encoded"] == 1
    assert verdict["unencoded_but_unverifiable"] == 1
    assert verdict["useful_fraction"] == pytest.approx(0.5)
    assert verdict["proceed_to_model_pass"] is True
