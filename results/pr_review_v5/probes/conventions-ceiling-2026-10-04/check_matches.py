"""Check blind matchers' outputs before they are unblinded.

Every ask of every PR in the folder must be judged for every reviewer label, each value one of
reached / partial / no, each finding index null or in range. A matcher that died after writing is
checked the same way: its file is neither assumed partial nor assumed whole.

usage: python3 <this file> <matcher folder> [...]
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

VALUES = {"reached", "partial", "no"}
bad = 0
for folder in map(Path, sys.argv[1:]):
    try:
        rows = {(str(a["pr"]), a["ask_id"]): a for a in json.loads((folder / "matches.json").read_text())["asks"]}
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"{folder.name}: matches.json unusable: {error!r}")
        bad += 1
        continue
    errors, counts, cells = [], Counter(), 0
    for asks_file in sorted(folder.glob("asks_pr*.json")):
        pr = re.search(r"pr(\d+)", asks_file.name).group(1)
        sizes = {f.name.split("_")[0]: len(json.loads(f.read_text())) for f in folder.glob(f"R*_pr{pr}.json")}
        for ask in json.loads(asks_file.read_text()):
            row = rows.get((pr, ask["ask_id"]))
            if row is None:
                errors.append(f"{pr}/{ask['ask_id']} not judged")
                continue
            for label, n in sorted(sizes.items()):
                value, index = row.get(label), row.get(f"{label}_finding")
                cells += 1
                counts[value] += 1
                if value not in VALUES:
                    errors.append(f"{pr}/{ask['ask_id']} {label}: value {value!r}")
                elif index is not None and not (isinstance(index, int) and 0 <= index < n):
                    errors.append(f"{pr}/{ask['ask_id']} {label}: finding {index!r} of {n}")
    print(f"{folder.name}: {cells} cells, {dict(counts)}, {len(errors)} error(s) {errors[:6]}")
    bad += bool(errors) or not cells
sys.exit(1 if bad else 0)
