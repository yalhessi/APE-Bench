"""Run one arm's bench.

    ./ape/bin/python -m src.datasets.pr_review_v5.bench_cli --release <release> --arm duplication

Without `--execute` this prints the fixture and what would run, and makes no model call and no
write. That default is the point: a bench is the cheap way to learn about an arm, and it should
be possible to look at one without spending anything.

This module sits on the v5 side and imports the evaluation side, which is the forward
direction. `benches.py` itself knows nothing about arms — it is handed a roster — because
evaluation importing generation is the direction that would make gold reachable from a prompt.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.datasets.pr_review_v4.benches import build_all, coverage_report

from .arm_registry import ARM_DEFINITIONS


def roster():
    """`arm_id -> the concern families it may declare`, from the arm registry."""

    return {item.arm_id: sorted(item.allowed_concerns) for item in ARM_DEFINITIONS}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--arm", action="append", help="restrict to these arms; repeatable")
    parser.add_argument("--pr", type=int, action="append", dest="pr_numbers")
    parser.add_argument("--negatives-per-pr", type=int, default=3)
    parser.add_argument(
        "--execute", action="store_true",
        help="actually run the arm. Without it this is a read-only look at the fixture.")
    args = parser.parse_args()

    benches = build_all(args.release, roster(), pr_numbers=args.pr_numbers,
                        negatives_per_pr=args.negatives_per_pr)
    if args.arm:
        wanted = set(args.arm)
        unknown = wanted - set(benches)
        if unknown:
            raise SystemExit(f"unknown arm(s): {sorted(unknown)}; "
                             f"known: {sorted(benches)}")
        benches = {k: v for k, v in benches.items() if k in wanted}

    report = coverage_report(benches)
    print(json.dumps(report, indent=2))

    if not args.execute:
        total = sum(len(b.cases) for b in benches.values())
        print(f"\n-- no --execute: {total} case(s) across {len(benches)} arm(s) would run. "
              "Nothing was called and nothing was written.")
        return

    raise SystemExit(
        "running an arm against its bench is not wired yet. The fixture, its hash and its "
        "coverage are what this command produces today; executing it needs the arm task to be "
        "constructible without a lead, which is the next step of the arm split."
    )


if __name__ == "__main__":
    main()
