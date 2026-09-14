"""A declaration's doc-comment and attributes belong to the declaration.

Lean writes them as separate syntactic entities, so the change graph produced them as separate
targets and the packer scheduled them as separate review sites. That was invisible while the
prompt pasted the raw `@@` hunk, because the hunk happened to carry the declaration and its
doc-comment together. Scoping each target's diff to itself (`9d4de8f`) removed the accident and
turned it into lost recall: on `pr5_A_lead_heldout12_fp3_rep1` the two PR 33321 obligations about
`IsMulIndecomposable.baseOf` — a docstring fix and a redefinition — were the only obligations
lost that every baseline repetition had found, and the doc-comment was in `wu:d60bad80…` while
the declaration was in `wu:07d1ab97…`.

Measured on `dev-medium-0.3.0` before the change: the `command` kind held 59 doc-comments and 26
attributes against 6 real commands (`#check`, `#print axioms`), and 38 of 59 doc-comments sat in
a work unit holding no declaration at all.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.mathlib_review.io import load_jsonl
from src.mathlib_review.release.change_graph import _command_kind, _structural_kind
from src.mathlib_review.release.work_units import build_work_units
from src.mathlib_review.schema import ChangeGraph

RELEASE = Path("inputs/pr_review_v4/releases/dev-medium-0.3.0")


@pytest.mark.parametrize("code,expected", [
    ('/-- The "base" of `v` relative to `f`. -/', "doc_comment"),
    ("/-! # Module docs -/", "module_doc"),
    ('@[deprecated (since := "2025-12-25")]', "attribute"),
    ("#print axioms GalerkinLimit.smooth", "command"),
    ("namespace IsMulIndecomposable", "namespace"),
    ("section CommRing", "section"),
])
def test_a_command_entity_is_named_for_what_it_is(code, expected):
    assert _command_kind(code) == expected


def test_the_structural_path_separates_a_doc_comment_from_a_module_doc():
    """`/-!` opens a module doc and `/--` a declaration's. The old rule called both, and a bare
    closing `-/`, `module_doc`."""

    doc = "@@ -1 +1,2 @@\n+/-- One lemma's doc. -/\n"
    mod = "@@ -1 +1,2 @@\n+/-! # A module header -/\n"

    class _Range:
        def __init__(self, fragment): self.diff_fragment = fragment

    assert _structural_kind("Mathlib/X.lean", _Range(doc)) == "doc_comment"
    assert _structural_kind("Mathlib/X.lean", _Range(mod)) == "module_doc"


@pytest.fixture(scope="module")
def graphs():
    path = RELEASE / "derived/change_graphs.jsonl"
    if not path.exists():
        pytest.skip("release not present")
    return load_jsonl(path, ChangeGraph)


def test_an_earlier_release_still_packs_into_exactly_the_units_it_froze(graphs):
    """The gate. `renderer_version` is inside the work-unit identity, so re-deriving a frozen
    release must reproduce every `work_unit_id` — the same discipline the prompt renderer keeps."""

    frozen = load_jsonl(RELEASE / "derived/work_units.jsonl", type(build_work_units(graphs[:1])[0]))
    rebuilt = build_work_units(graphs, renderer_version="candidate-prompt/12")
    assert sorted(item.work_unit_id for item in rebuilt) == \
        sorted(item.work_unit_id for item in frozen)


def test_a_declaration_is_packed_with_its_doc_comment_and_attributes(graphs):
    """The fix, stated as the property that was violated.

    The release on disk predates the new kinds, so this asserts the invariant on whatever
    attachments its graphs carry; rebuilt graphs carry 73.
    """

    units = build_work_units(graphs, renderer_version="candidate-prompt/13")
    unit_of = {change_id: unit.work_unit_id for unit in units for change_id in unit.change_ids}
    targets = {item.change_id: item for graph in graphs for item in graph.targets}

    split = [
        change_id for change_id, target in targets.items()
        if target.attached_to and unit_of[change_id] != unit_of[target.attached_to]
    ]
    assert not split, f"{len(split)} attached target(s) scheduled away from their declaration"


def test_packing_charges_a_shared_hunk_once_per_unit(graphs):
    """The budget was summed per target over text the renderer prints once per unit.

    PR 33145 has exactly one 5,196-char fragment on all 12 of its targets; the packer charged
    62,352 and split a six-theorem family four ways over a 24,000 budget whose real content is
    10,198 characters.
    """

    old = build_work_units(graphs, renderer_version="candidate-prompt/12")
    new = build_work_units(graphs, renderer_version="candidate-prompt/13")
    assert len(new) < len(old), "the repack must not fragment more than the accounting it fixes"

    by_pr_old = sum(1 for unit in old if unit.pr_number == 33145)
    by_pr_new = sum(1 for unit in new if unit.pr_number == 33145)
    assert by_pr_new < by_pr_old
