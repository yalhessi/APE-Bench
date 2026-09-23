"""Every `ChangeTargetKind` is handled by every list that enumerates kinds.

The fourth instance of this project's most expensive bug: a value is registered correctly in the
place that looks authoritative, and a second list that nothing checks it against drops it with no
error. The prior three are in `.claude/rules/mathlib-review.md` -- `documentation` vs `docs`, the
retrieval gate's closed `gate` Literal, and `CONTEXT_TOOLS` vs `naming_norm`, the last of which
cost a paid run that came back looking like "the new contract changed nothing".

This one was caught in pre-flight rather than after a run. `cg1_builder_v3` split `command` into
`doc_comment` and `attribute`, and on `dev-medium-0.4.0` that is 85 of 508 targets. All 85
resolved to `subject_kind: unknown`, which no arm's `subject_kinds` contains, and all 85 were
dropped from the file skeleton -- so the kinds existed, were correct, and reached nothing.

These tests are parameterised over `ChangeTargetKind` itself, so a kind added later fails here
until every vocabulary has an answer for it.
"""

from __future__ import annotations

import typing

import pytest

from src.mathlib_review.agenda.arms import DOCUMENTATION_KINDS, PLACEMENT_KINDS
from src.mathlib_review.agenda.focused_specs import DECLARATION_KINDS
from src.mathlib_review.agenda.review_map import STRUCTURE_KINDS
from src.mathlib_review.release.modification_inventory import _subject_kind
from src.mathlib_review.schema import ChangeTargetKind
from src.mathlib_review.schema.identity import SubjectKind

#: Kinds that describe a file the pipeline does not review, so they have no subject or skeleton
#: row by design rather than by omission.
NOT_REVIEWED = {"whitespace", "non_lean", "unparsed"}

KINDS = [k for k in typing.get_args(ChangeTargetKind) if k not in NOT_REVIEWED]


class _Target:
    """The fields `_subject_kind` reads."""

    def __init__(self, kind):
        self.kind = kind
        self.declaration_kind = "theorem" if kind == "declaration" else None
        self.base_code = None
        self.reviewed_code = "x"
        self.base_entity_ids = []
        self.reviewed_entity_ids = []
        self.diff_fragments = []


@pytest.mark.parametrize("kind", KINDS)
def test_every_kind_has_a_subject_kind(kind):
    """`unknown` is what a target gets when the inventory has no answer, and no arm's
    `subject_kinds` contains it -- so an unknown subject is an unschedulable target."""

    assert _subject_kind(_Target(kind)) != "unknown"


@pytest.mark.parametrize("kind", KINDS)
def test_every_kind_reaches_at_least_one_arm(kind):
    """A subject kind no arm accepts is a target nothing can be scheduled on."""

    subject = _subject_kind(_Target(kind))
    reachable = DECLARATION_KINDS | DOCUMENTATION_KINDS | PLACEMENT_KINDS
    assert subject in reachable, (
        f"{kind} -> subject_kind {subject!r}, which no arm's subject_kinds contains")


@pytest.mark.parametrize("kind", KINDS)
def test_every_subject_kind_is_a_declared_subject_kind(kind):
    """`SubjectKind` is the fifth list, and the only one that refuses rather than drops.

    It is in this file because the first four failing silently is what makes the loud one easy
    to mistake for the whole problem: building the inventory raised on `doc_comment` only after
    the other four had already been taught it.
    """

    assert _subject_kind(_Target(kind)) in typing.get_args(SubjectKind)


@pytest.mark.parametrize("kind", KINDS)
def test_every_kind_appears_in_the_file_skeleton(kind):
    """`build_skeleton` keeps `declaration` and `STRUCTURE_KINDS` and silently drops the rest."""

    assert kind == "declaration" or kind in STRUCTURE_KINDS


def test_the_documentation_arm_owns_a_declarations_own_doc_comment():
    """The specific gap that motivated this file: PR 33321's two documentation obligations sit
    on a declaration's `/-- … -/`, and the `docs` arm could not be scheduled there."""

    assert _subject_kind(_Target("doc_comment")) in DOCUMENTATION_KINDS
