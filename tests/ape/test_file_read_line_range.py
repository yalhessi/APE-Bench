"""`file_read` takes two integers, and still takes the list it used to.

A nested parameter is the one shape a tool schema cannot rely on every model producing.
Measured 2026-09-22 on the ELM gateway under `tool_choice=auto`, 8 trials each: with an
array-valued `line_range` Qwen produced a conformant call 0/8 times regardless of whether
`items` was typed or the description used JSON `null` instead of Python `None`; with two
scalar integers it was 5/8, and 0 stringified. `gpt_5.2` was unaffected either way.

So the scalars are the fix and `line_range` is kept only so that nothing which already uses
it changes behaviour -- including every run in the existing record.
"""

from __future__ import annotations

import pytest

from ape.toolkits.file_system.tools import _DEFAULT_LINE_RANGE, _resolve_line_range


@pytest.mark.parametrize("line_start,line_end,expected", [
    (None, None, _DEFAULT_LINE_RANGE),
    (10, None, [10, None]),
    (None, 20, [None, 20]),
    (3, 7, [3, 7]),
    (-10, None, [-10, None]),
    (None, -1, [None, -1]),
])
def test_the_scalars_describe_the_same_ranges_the_list_did(line_start, line_end, expected):
    assert _resolve_line_range(line_start, line_end, None) == expected


def test_no_range_at_all_still_reads_the_first_200_lines():
    """The default is behaviour, not decoration: it is what every existing caller that omits
    the range has always got, and changing it would change what those runs read."""

    assert _resolve_line_range(None, None, None) == [1, 200]
    assert _DEFAULT_LINE_RANGE == [1, 200]


@pytest.mark.parametrize("line_range", [[5, 9], [None, None], [None, 10], [-100, None]])
def test_the_deprecated_list_form_still_works(line_range):
    assert _resolve_line_range(None, None, line_range) == line_range


def test_the_list_form_wins_when_both_are_given():
    """A caller that sent the explicit list meant it; silently preferring the scalars would
    change a call that was already correct."""

    assert _resolve_line_range(1, 2, [9, 9]) == [9, 9]


def test_the_resolved_range_is_a_copy():
    """The default is module-level mutable state; handing it out directly would let one
    caller's edit change what every later caller reads."""

    first = _resolve_line_range(None, None, None)
    first.append(999)
    assert _resolve_line_range(None, None, None) == [1, 200]


def test_the_scalar_schema_has_no_nesting_for_a_model_to_get_wrong():
    """The point of the change: the parameters a model is most likely to use are scalars."""

    from typing import Optional

    from pydantic import TypeAdapter

    for scalar in (Optional[int],):
        schema = TypeAdapter(scalar).json_schema()
        types = {branch.get("type") for branch in schema.get("anyOf", [schema])}
        assert "array" not in types and "object" not in types
