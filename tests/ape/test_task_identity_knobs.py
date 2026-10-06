"""A `knob()` field enters a task's `global_index` only once it is set.

`generate_global_index` hashes the whole data model, defaults included, so one ordinary new field
moves the identity of every task of that type, and every cache and resume then misses
(`docs/research/codebase-redesign-2026-10.md` §4.3; the rules file's "What moves a hash"). These
pin the three behaviours: an unset knob leaves the identity where it was, a set one forks it, and
an ordinary field still moves it -- the reason the knob exists.
"""

from __future__ import annotations

from typing import Optional

from ape.tasks.base import IDENTITY_WHEN_SET, BaseTaskData, knob


class Before(BaseTaskData):
    reviewed_path: str


class WithKnob(Before):
    new_policy: Optional[bool] = knob("a policy added after tasks of this type already ran")


class WithField(Before):
    new_policy: Optional[bool] = None


def _ids(cls, **extra):
    return cls(task_type="t", task_id="a", reviewed_path="X.lean", **extra).global_index


def test_an_unset_knob_leaves_the_identity_where_it_was():
    assert _ids(WithKnob) == _ids(Before)
    assert _ids(WithKnob, new_policy=None) == _ids(Before)


def test_a_set_knob_forks_the_identity():
    assert _ids(WithKnob, new_policy=True) != _ids(Before)
    assert _ids(WithKnob, new_policy=True) != _ids(WithKnob, new_policy=False)


def test_an_ordinary_new_field_moves_every_identity_which_is_why_knobs_exist():
    assert _ids(WithField) != _ids(Before)


def test_a_knob_is_none_by_default_and_says_so_in_its_schema():
    info = WithKnob.model_fields["new_policy"]
    assert info.default is None and info.json_schema_extra == {IDENTITY_WHEN_SET: True}
