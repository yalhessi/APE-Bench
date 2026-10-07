"""Stage 5's S2 context: S1's rows, each followed by the closing section the amendment fixes.

The text is the README's, word for word (stage 5 on gpt-5.5, 2026-10-07): the generation-without-
suppression plan's C1 as stage W measured it, worded for places. Run from the repo root.
"""

import json
from pathlib import Path

HERE = Path(__file__).parent / "stage5"
TITLE = "Dispositions for the places above"
TEXT = ("Give every place listed in the sections above a disposition, and say in your submission's "
        "`message` which you gave and on what ground. `departs`: file the change its section describes, "
        "as a finding at that place. `conforms`: only if a check you ran, or a line of the code you quote, "
        "shows the required form already holds there. What Mathlib usually requires, accepts or enforces, "
        "how minor the change is, and whether a maintainer would insist on it are not grounds for either "
        "disposition. For these places this replaces the brief's instruction to emit only what you would "
        "actually request.")

rows = [json.loads(line) for line in (HERE / "model_context_s1.jsonl").read_text().splitlines() if line]
assert all(len(row["sections"]) >= 2 for row in rows), "every stage-5 PR has at least one section"
with (HERE / "model_context_s2.jsonl").open("w") as out:
    for row in rows:
        out.write(json.dumps(dict(row, sections=row["sections"] + [{"title": TITLE, "text": TEXT}]),
                             ensure_ascii=False) + "\n")
print(f"{len(rows)} rows")
