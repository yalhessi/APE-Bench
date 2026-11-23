"""Count delivered comments and the expert requests credited within a prefix of each saved review.

The two original matchers each point to one supporting finding. Another earlier finding could
also address the request. This recount uses the original pointers without rejudging short lists.
"""

from collections import Counter
import json
from pathlib import Path


TABLE = Path(__file__).resolve().parent
PANELS = {"14 PRs": ("P14_val", "P14_post"), "12 PRs": ("D12b",)}
DEPTHS = (1, 3, 5, 20)


def summarize(parts):
    delivered = Counter()
    reached = Counter()
    for part in parts:
        folder = TABLE / f"match_{part}"
        stats = json.loads((folder / "session_stats.json").read_text())
        seal = json.loads((TABLE / f"blinding_{part}_SEALED.json").read_text())
        labels = {pr: {session: label for label, session in assignment.items()}
                  for pr, assignment in seal.items()}
        for sessions in stats.values():
            for session in ("T1", "TA1"):
                for depth in DEPTHS:
                    delivered[session, depth] += min(depth, sessions[session]["findings"])
        for reader in (1, 2):
            rows = json.loads((folder / f"matches.{reader}.json").read_text())["asks"]
            for row in rows:
                pr = str(row["pr"])
                for session in ("T1", "TA1"):
                    label = labels[pr][session]
                    if row[label] != "reached":
                        continue
                    index = row[f"{label}_finding"]
                    if not 0 <= index < stats[pr][session]["findings"]:
                        raise ValueError(f"Invalid finding index on PR {pr}, session {session}")
                    for depth in DEPTHS:
                        reached[session, depth, reader] += index < depth
    return delivered, reached


if __name__ == "__main__":
    print("panel | maximum comments per PR | session | comments | reached (reader 1, reader 2)")
    for panel, parts in PANELS.items():
        delivered, reached = summarize(parts)
        for depth in DEPTHS:
            for session in ("T1", "TA1"):
                print(f"{panel} | {depth} | {session} | {delivered[session, depth]} | "
                      f"{reached[session, depth, 1]}, {reached[session, depth, 2]}")
