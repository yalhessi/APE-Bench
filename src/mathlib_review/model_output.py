"""Reading a model's text output when it was asked for JSON.

`_extract_json_object` had ten import sites across four packages, every one of them reaching
past a leading underscore. That is the largest single private-name violation in the tree, and
it is the shape of the problem: a genuinely shared parsing rule that happened to be written
first inside `pr_review_v2/predictions.py`, so every later caller imported it from there
rather than from anywhere it belonged.

The rule itself is worth stating once. A model asked for JSON returns JSON *somewhere* in its
reply -- inside a fence, after a sentence of preamble, occasionally with commentary after the
closing brace. Scanning for the first position that decodes as an object is tolerant of all
three without being tolerant of the thing that matters, which is a reply containing no object
at all: that raises, because silently returning `{}` turns a broken response into an empty
result and an empty result into a finding of "the model said nothing".
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict

_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def extract_json_object(text: str) -> Dict[str, Any]:
    """The first JSON object in the text. Fences and surrounding prose are tolerated.

    Raises `ValueError` when there is none, rather than returning an empty dict.
    """

    cleaned = _FENCE.sub("", (text or "").strip())
    decoder = json.JSONDecoder()
    for start in range(len(cleaned)):
        if cleaned[start] != "{":
            continue
        try:
            obj, _ = decoder.raw_decode(cleaned[start:])
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            return obj
    raise ValueError("no JSON object found in response")
