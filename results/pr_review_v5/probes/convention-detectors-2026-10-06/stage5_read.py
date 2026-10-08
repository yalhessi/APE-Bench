"""Stage 5 on gpt-5.5, read by hand and blind to condition (README, the 2026-10-07 amendment).

  stage5_read.py inputs <round> <session>=<run> <session>=<run>
      seal the sessions on all 16 PRs (`probes.seal_labels`, a fresh draw), write the blind inputs
      (`probes.match_inputs`, the two ask-less PRs given an empty list) and one sheet to read:
      per PR the target asks, the section facts, and each label's findings.
  stage5_read.py unblind <round>
      after `marks.json` is written by hand: per session, the target asks reached and the
      section facts repeated, by stratum.

Session names end in a digit (`base1`, `sections1`, `disposition1`): `probes.condition` strips it.
Run from the repo root.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from src.mathlib_review.analysis import probes
from src.mathlib_review.io import jsonl_rows

HERE = Path(__file__).parent / "stage5"
SET = Path("configs/probe_sets/census_detectors_v1.yaml")
#: Stratum A's 13 asks, each stated exactly by a packet-ready detector (README, stage 5).
TARGETS = {28484: ["v0644"], 31961: ["v1252", "v1254"], 32674: ["v1397"], 32715: ["v1412", "v1413", "v1414"],
           34241: ["v1661"], 30645: ["v1057"], 31007: ["v1096"], 32992: ["v1490"], 35807: ["v1935"],
           36355: ["v2081"]}
STRATUM_B = [31077, 31793, 32540, 32610, 33006, 37009]


def facts(pr: int) -> list:
    """The section facts S1 shows on this PR, in order: (section title, bullet)."""

    for row in jsonl_rows(HERE / "model_context_s1.jsonl"):
        if row["pr_number"] == pr:
            return [(s["title"], b[2:]) for s in row["sections"][1:]
                    for b in s["text"].splitlines() if b.startswith("- ")]
    return []


def inputs(round_: str, pairs: list) -> None:
    spec = probes.load_probe_set(SET)
    seal_file = HERE / f"blinding_{round_}_SEALED.json"
    if seal_file.exists():
        raise SystemExit(f"{seal_file} exists; a seal is written once")
    sources = {s: probes.Source(kind="solo", run=run) for s, run in (p.split("=", 1) for p in pairs)}
    seal = probes.seal_labels(spec.pr_numbers, list(sources))
    probes.write_json(seal_file, seal)
    asks = json.loads(spec.asks_file.read_text())
    asks = {**asks, "asks": {str(pr): asks["asks"].get(str(pr), []) for pr in spec.pr_numbers}}
    out = HERE / f"match_{round_}"
    probes.match_inputs(spec, json.loads(spec.feedback_file.read_text()), asks, seal, sources, out)
    lines = [f"# Stage 5, {round_}: blind sheet\n"]
    for pr in spec.pr_numbers:
        stratum = "A" if pr in TARGETS else "B"
        lines.append(f"\n## PR {pr} (stratum {stratum})\n")
        for a in json.loads((out / f"asks_pr{pr}.json").read_text()):
            if a["ask_id"] in TARGETS.get(pr, []):
                code = "\n".join(a["code_at_comment"].splitlines()[-4:])
                lines.append(f"**TARGET {a['ask_id']}** `{a['path']}`\n```\n{code}\n```\n> {a['comment']}\n")
        for n, (title, bullet) in enumerate(facts(pr)):
            lines.append(f"- fact {n} [{title}]: {bullet}")
        for label in sorted(seal[str(pr)]):
            lines.append(f"\n### {label}\n")
            for f in json.loads((out / f"{label}_pr{pr}.json").read_text()):
                lines.append(f"- [{f['i']}] `{f['target']}` ({f['severity']}): {f['claim']}"
                             f"\n  -> {f['requested_change']}")
    (out / "sheet.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({"sealed": str(seal_file), "sheet": str(out / "sheet.md"), "sessions": list(sources)}))


def unblind(round_: str) -> None:
    seal = json.loads((HERE / f"blinding_{round_}_SEALED.json").read_text())
    marks = json.loads((HERE / f"match_{round_}" / "marks.json").read_text())
    sessions = sorted({s for labels in seal.values() for s in labels.values()})
    reached = {s: [] for s in sessions}
    for a in marks["asks"]:
        for label, session in seal[str(a["pr"])].items():
            if a.get(label) == "reached":
                reached[session].append(a["ask_id"])
    repeats = {s: {"A": 0, "B": 0} for s in sessions}
    for pr, by_label in marks["repeats"].items():
        for label, fact_ids in by_label.items():
            repeats[seal[pr][label]]["A" if int(pr) in TARGETS else "B"] += len(fact_ids)
    marked = {(a["pr"], a["ask_id"]) for a in marks["asks"]}
    missing = [(pr, c) for pr, cs in TARGETS.items() for c in cs if (pr, c) not in marked]
    print(json.dumps({"unmarked_targets": missing,
                      "targets_reached": {s: {"count": len(v), "asks": sorted(v)} for s, v in reached.items()},
                      "fact_repeats": repeats,
                      "fact_repeats_per_stratum_b_pr": {s: r["B"] / len(STRATUM_B) for s, r in repeats.items()}},
                     indent=1))


if __name__ == "__main__":
    command, round_ = sys.argv[1], sys.argv[2]
    inputs(round_, sys.argv[3:]) if command == "inputs" else unblind(round_)
