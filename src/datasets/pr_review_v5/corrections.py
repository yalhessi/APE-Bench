"""Recover what a finished run actually spent, without rewriting its ledger.

Two runs in September closed with `completion_status: failed` and were scored anyway. Their
delegation ledgers book the paused jobs at `$0.00`, because a sample that paused on budget was
judged resumable, never aggregated, and reached the ledger as a bare failure — the defect fixed
in `worker._try_aggregate` and `Sample.can_execute`.

Those ledgers are left exactly as they are. Rewriting a run's raw artifacts after the fact
destroys the evidence that the defect existed and makes the fix unfalsifiable, so the recovery
lands beside them as a derived artifact instead: `correction_sidecar.json`, carrying its own
derivation version, the hash of every source it read, and the figures the ledger could not see.

The sidecar is what makes those runs usable as regression fixtures. It is not a score, and the
runs it describes remain forensic.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.datasets.pr_review_v4.io import canonical_json_bytes, sha256_bytes

from .paths import run_dir

#: Bumped whenever the recovery changes what it reads or how it aggregates, so a sidecar can
#: be told apart from one produced by a different rule.
CORRECTION_VERSION = "v5-correction/1"

#: Attempt statuses that spent money without producing a terminal result.
_UNBOOKED = {"paused_cost_limit", "paused_max_turns"}


@dataclass
class RecoveredAttempt:
    """One attempt whose spend the ledger could not see."""

    path: str
    status: str
    billed_cost: float
    nominal_cost: float
    turns: int = 0

    def as_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path, "status": self.status,
            "billed_cost": round(self.billed_cost, 6),
            "nominal_cost": round(self.nominal_cost, 6),
            "turns": self.turns,
        }


@dataclass
class RunCorrection:
    run_name: str
    recovered: List[RecoveredAttempt] = field(default_factory=list)
    reported_total_cost: Optional[float] = None
    reported_paused: Optional[int] = None
    reported_status: Optional[str] = None
    sources: Dict[str, str] = field(default_factory=dict)

    @property
    def hidden_billed(self) -> float:
        return sum(item.billed_cost for item in self.recovered)

    @property
    def hidden_nominal(self) -> float:
        return sum(item.nominal_cost for item in self.recovered)

    def as_dict(self) -> Dict[str, Any]:
        corrected_nominal = (
            None if self.reported_total_cost is None
            else self.reported_total_cost + self.hidden_nominal
        )
        payload: Dict[str, Any] = {
            "schema_version": "v5-correction1",
            "correction_version": CORRECTION_VERSION,
            "run_name": self.run_name,
            # What the run said about itself.
            "reported": {
                "completion_status": self.reported_status,
                "total_cost_nominal": self.reported_total_cost,
                "paused": self.reported_paused,
            },
            # What it did not say. `nominal` is the no-cache counterfactual and `billed` is
            # what was actually paid; quoting the first as spend overstates it by ~2.5x.
            "recovered": {
                "paused_attempts": len(self.recovered),
                "hidden_billed_cost": round(self.hidden_billed, 6),
                "hidden_nominal_cost": round(self.hidden_nominal, 6),
                "attempts": [item.as_dict() for item in self.recovered],
            },
            "corrected": {
                "total_cost_nominal": (
                    None if corrected_nominal is None else round(corrected_nominal, 6)),
                "hidden_share_of_corrected_nominal": (
                    None if not corrected_nominal
                    else round(self.hidden_nominal / corrected_nominal, 4)),
                "paused": len(self.recovered),
            },
            "sources": dict(sorted(self.sources.items())),
            # Says it plainly, in the artifact, so a number lifted out of this file carries
            # the caveat with it.
            "verdict": (
                "forensic: this run's recall figures were computed over coverage it did not "
                "have, and its ledger under-reports spend. Usable as a regression fixture, "
                "not as a measurement."
                if self.recovered or self.reported_status != "complete"
                else "no correction needed"
            ),
        }
        payload["source_sha256"] = sha256_bytes(canonical_json_bytes(payload))
        return payload


def _iter_samples(scratch: Path):
    for path in sorted(scratch.rglob("samples/*/sample.json")):
        try:
            yield path, json.loads(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue


def recover(run_name: str, *, scratch_root: Path = Path(".ape/runs")) -> RunCorrection:
    """Read a run's scratch tree and its manifest, and report what the ledger missed."""

    correction = RunCorrection(run_name=run_name)

    manifest_path = run_dir(run_name) / "run_manifest.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        correction.reported_total_cost = manifest.get("total_cost")
        correction.reported_paused = manifest.get("paused")
        correction.reported_status = manifest.get("completion_status")
        correction.sources["run_manifest.json"] = sha256_bytes(
            manifest_path.read_bytes())

    scratch = scratch_root / run_name
    if not scratch.is_dir():
        return correction

    for path, sample in _iter_samples(scratch):
        for attempt in sample.get("attempts") or []:
            status = str(attempt.get("status") or "")
            if status not in _UNBOOKED:
                continue
            # A paused attempt that produced no task_result is exactly the row the ledger
            # booked at $0.00.
            nominal = float(attempt.get("cost") or 0.0)
            billed = float(attempt.get("cached_cost") or nominal)
            correction.recovered.append(RecoveredAttempt(
                path=str(path.parent.relative_to(scratch)),
                status=status, billed_cost=billed, nominal_cost=nominal,
                turns=int(attempt.get("turns") or 0),
            ))
    correction.recovered.sort(key=lambda item: item.path)
    return correction


def write_sidecar(run_name: str, *, scratch_root: Path = Path(".ape/runs")) -> Path:
    """Write `correction_sidecar.json` beside the run's other artifacts."""

    correction = recover(run_name, scratch_root=scratch_root)
    out = run_dir(run_name) / "correction_sidecar.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(correction.as_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--run", required=True, action="append",
                        help="run_name to correct; repeatable")
    parser.add_argument("--scratch-root", type=Path, default=Path(".ape/runs"))
    args = parser.parse_args()

    for run_name in args.run:
        correction = recover(run_name, scratch_root=args.scratch_root)
        path = write_sidecar(run_name, scratch_root=args.scratch_root)
        print(
            f"{run_name}: {len(correction.recovered)} paused attempt(s), "
            f"hidden billed ${correction.hidden_billed:.4f} / "
            f"nominal ${correction.hidden_nominal:.4f} -> {path}"
        )


if __name__ == "__main__":
    main()
