"""What the precedent corpus is made of, and what must be kept out of it.

Two functions, both previously private-ish names inside `pr_review_v2` that v5's index reached
across a package boundary to get.

`eval_pr_numbers` is the corpus-build half of the leak gate. `retrieval_gate` answers "was
this available at review time"; this answers "is this PR one we are being scored on", and a
comment from a scored PR must not be in the corpus at all, whatever its timestamp says. The
date cutoff already excludes them and this is the belt to that pair of braces -- worth keeping
precisely because a leak found by only one of two independent checks is a leak that was one
edit away from happening.

`hunk_code` turns a diff hunk into the code a comment was actually about: no `@@` headers, no
`+`/`-` markers, and removed lines dropped, because the reviewed state is what the reviewer
saw. Six call sites across two packages spell that rule by calling this, and none spell it
themselves.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Set

#: The scored set. A precedent drawn from one of these PRs is the answer, not a precedent.
EVAL_SET = Path("inputs/pr_review_v2/mathlib_pr_review_v2_actionable_20260618.jsonl")


def eval_pr_numbers(path: Path = EVAL_SET) -> Set[int]:
    """PRs the system is scored on, excluded from the corpus outright.

    Returns empty when the file is absent rather than raising: the corpus can legitimately be
    built in a tree that has no eval set, and the date cutoff is the primary exclusion.
    """

    if not path.is_file():
        return set()
    return {
        json.loads(line)["pr_number"]
        for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    }


def hunk_code(hunk_text: str) -> str:
    """A diff hunk as the code it is about: markers stripped, removed lines dropped."""

    lines = []
    for line in (hunk_text or "").splitlines():
        if line.startswith(("@@", "diff ", "+++", "---")):
            continue
        if line[:1] == "-":  # removed lines: not the reviewed state
            continue
        lines.append(line[1:] if line[:1] == "+" else line)
    return "\n".join(lines).strip()
