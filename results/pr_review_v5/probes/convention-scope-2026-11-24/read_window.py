"""Recount the October comparison on the 33 requests in the ten PRs actually run."""

import json
from collections import Counter
from pathlib import Path
from statistics import mean


ARCHIVE = Path(__file__).resolve().parent.parent / "conventions-ceiling-2026-10-04"


def load(path):
    return json.loads(path.read_text())


def counts(stages, requests, reader, depth):
    hits = Counter()
    comments = Counter()
    observed = {}
    for stage in stages:
        for panel in ("val", "post"):
            folder = ARCHIVE / f"match_{stage}_{panel}"
            labels = load(ARCHIVE / f"blinding_{stage}_{panel}_SEALED.json")
            stats = load(folder / "session_stats.json")
            for row in load(folder / f"matches.{reader}.json")["asks"]:
                request = row["ask_id"]
                if request not in requests:
                    continue
                pr = str(row["pr"])
                for label, session in labels[pr].items():
                    # Stage D judged its first repeat and its next two in separate rounds.
                    # Exclude the Opus anchors shown again in both judging rounds.
                    if stage in ("D1", "D23") and not session.startswith("D"):
                        continue
                    seen = observed.setdefault(session, set())
                    assert request not in seen
                    seen.add(request)
                    n = stats[pr][session]["findings"]
                    comments[session, pr] = min(depth, n) if depth is not None else n
                    if row[label] == "reached":
                        index = row[label + "_finding"]
                        assert isinstance(index, int) and 0 <= index < n
                        hits[session] += depth is None or index < depth
    assert all(ids == requests for ids in observed.values())
    return {
        name: (mean(hits[s] for s in observed if s.rstrip("0123456789") == name),
               mean(sum(n for (session, _), n in comments.items() if session == s)
                    for s in observed if s.rstrip("0123456789") == name))
        for name in sorted({s.rstrip("0123456789") for s in observed})
    }


if __name__ == "__main__":
    prs = set(load(ARCHIVE / "briefs_applicable.json")["prs"])
    requests = {ask for ask, label in load(ARCHIVE / "briefs_exact.json")["asks"].items()
                if label["in_census"] and str(label["pr"]) in prs}
    assert (len(prs), len(requests)) == (10, 33)
    print("depth reader design | solo design exact | net gain / exact gain | comments per PR")
    for depth in (None, 5):
        for reader in (1, 2):
            for stage, design in (("F", "A"), ("G", "G"), ("AP", "AP")):
                result = counts([stage], requests, reader, depth)
                if stage == "AP":
                    reference = counts(["D1", "D23"], requests, reader, depth)
                    baseline, exact = "DX", "DP"
                else:
                    reference = result
                    baseline, exact = "X", "E"
                solo, candidate, oracle = result[baseline], result[design], reference[exact]
                gain = candidate[0] - solo[0]
                exact_gain = oracle[0] - reference[baseline][0]
                print(depth or "all", reader, design, "|",
                      *(f"{cell[0]:.3g}" for cell in (solo, candidate, oracle)), "|",
                      f"{gain:.3g} / {exact_gain:.3g} = {gain / exact_gain:.1%}", "|",
                      *(f"{cell[1] / len(prs):.2f}" for cell in (solo, candidate, oracle)))
