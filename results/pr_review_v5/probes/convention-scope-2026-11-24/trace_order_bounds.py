"""Trace four fixed unary order-bound subjects in the reviewed file's Git history."""

import csv
import json
import re
import subprocess
import sys
from pathlib import Path


SOURCE = Path("data/code_execute/repos/mathlib4/source")
EPISODES = Path("inputs/probes/probe-2026-07-08-v1/input/episodes.jsonl")
FILE = "Mathlib/Topology/Algebra/InfiniteSum/Order.lean"
CUTOFFS = ("2024-01-01", "2024-07-01", "2025-07-01", "2026-01-01")
DECLARATION = re.compile(r"^(?:(?:protected|nonrec) )*(?:theorem|lemma) ([\w'.]+)")
# Before March 2024 the handwritten declarations were the additive ones.
# Afterwards the multiplicative source generates the additive API with to_additive.
SUBJECTS = [
    ("weak lower", ("tsum_nonneg", "one_le_tprod"), ("HasSum.nonneg", "HasProd.one_le")),
    ("weak upper", ("tsum_nonpos", "tprod_le_one"), ("HasSum.nonpos", "HasProd.le_one")),
    ("strict lower", ("tsum_pos", "Summable.tsum_pos", "one_lt_tprod", "Multipliable.one_lt_tprod"),
     ("HasSum.pos", "zero_lt_hasSum", "HasProd.one_lt", "one_lt_hasProd")),
    ("strict upper", ("tsum_neg", "Summable.tsum_neg", "tprod_lt_one", "Multipliable.tprod_lt_one"),
     ("hasSum_lt_zero", "HasProd.lt_one", "hasProd_lt_one")),
]


def git(*args):
    return subprocess.check_output(["git", "-C", SOURCE, *args], text=True).strip()


def unique(names, declarations):
    matches = [name for name in names if name in declarations]
    if len(matches) > 1:
        raise ValueError(f"Ambiguous source declarations: {matches}")
    return matches[0] if matches else None


def trace(ref, cutoff, writer):
    sha, date = git("show", "-s", "--format=%H %cI", ref).split()
    lines = git("show", f"{sha}:{FILE}").splitlines()
    declarations = {m[1]: ix for ix, line in enumerate(lines) if (m := DECLARATION.match(line))}
    for subject, operations, witnesses in SUBJECTS:
        value = unique(operations, declarations)
        witness = unique(witnesses, declarations)
        evidence = []
        if value:
            start = declarations[value]
            for ix in range(start + 1, len(lines)):
                line = lines[ix].strip()
                if not line or line.startswith("#align"):
                    break
                if re.search(r"\.(?:hasSum|hasProd)\.|(?:tsum_lt_tsum|tprod_lt_tprod)", line):
                    evidence.append(f"{ix + 1} {line}")
            if not evidence:
                raise ValueError(f"Inspect changed proof of {value} at {sha}")
        def location(name):
            return f"{name}@{declarations[name] + 1}" if name else "-"
        writer.writerow([cutoff, sha, date, subject, location(value), location(witness),
                         " | ".join(evidence) or "-"])


def main():
    with EPISODES.open() as rows:
        episode, = (row for row in map(json.loads, rows) if row["pr_number"] == 42184)
    base = episode["base_sha"]
    if episode["changed_files"] != [FILE]:
        raise ValueError("Reviewed file differs from the bounded source cohort")
    writer = csv.writer(sys.stdout, delimiter="\t", lineterminator="\n")
    writer.writerow(["cutoff", "commit", "committed_at", "subject", "value_declaration",
                     "named_witness", "proof_line"])
    for day in CUTOFFS:
        timestamp = day + "T00:00:00Z"
        ref = git("rev-list", "--first-parent", "-1", f"--before={timestamp}", base)
        trace(ref, timestamp, writer)
    trace(base, "review base", writer)


if __name__ == "__main__":
    main()
