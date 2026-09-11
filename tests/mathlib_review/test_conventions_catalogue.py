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
