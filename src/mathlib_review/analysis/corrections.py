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

`token_census` answers the neighbouring question off the same walk of the same tree: not "what
did the ledger miss" but "what did each role actually consume", which is what the token
ceilings in `configs/bases/v5_generation.yaml` were calibrated against. It lives here because
`_iter_samples` is here; the caps it feeds are in
`docs/research/2026-09-22-token-budget-calibration.md`, and the rate it reports has to be
re-measured whenever the model changes.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from src.mathlib_review.io import canonical_json_bytes, sha256_bytes

from src.mathlib_review.paths import run_dir

#: Bumped whenever the recovery changes what it reads or how it aggregates, so a sidecar can
#: be told apart from one produced by a different rule.
CORRECTION_VERSION = "v5-correction/1"

#: Attempt statuses that consumed budget without producing a terminal result. "Money" was the
#: right word while every ceiling was a dollar one; a token-paused attempt on a zero-priced
#: model spent no money and is just as unbooked.
_UNBOOKED = {"paused_cost_limit", "paused_token_limit", "paused_max_turns"}


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
    #: What the scratch tree actually holds, whatever each attempt's status.
    on_disk_attempts: int = 0
    on_disk_nominal_cost: float = 0.0
    on_disk_billed_cost: float = 0.0
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
            # The general check, and the one that does not depend on knowing *why* a cost was
            # missed. `unaccounted_billed` is spend sitting in the scratch tree that the
            # manifest's own figure does not cover. Pausing is one cause; a discarded wave is
            # another, and there will be others.
            "on_disk": {
                "attempts": self.on_disk_attempts,
                "billed_cost": self.on_disk_billed_cost,
                "nominal_cost": self.on_disk_nominal_cost,
                "unaccounted_nominal": (
                    None if self.reported_total_cost is None
                    else round(self.on_disk_nominal_cost - self.reported_total_cost, 6)),
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

    # Everything on disk, whatever its status. `recovered` above answers "which attempts did
    # the ledger book at $0.00 because they paused"; this answers the more general question the
    # ledger can actually be wrong about -- "does the manifest account for what was spent".
    #
    # `pr5_smoke4_rep8` is why. Its attempts *succeeded*; a bookkeeping bug discarded their
    # outcomes, so nothing paused and this function reported $0.00 hidden while $2.86 of billed
    # work sat in the scratch tree. Under-reporting has more causes than pausing.
    on_disk_nominal = on_disk_billed = 0.0
    attempts = 0
    for _path, sample in _iter_samples(scratch):
        for attempt in sample.get("attempts") or []:
            nominal = float(attempt.get("cost") or 0.0)
            on_disk_nominal += nominal
            on_disk_billed += float(attempt.get("cached_cost") or nominal)
            attempts += 1
    correction.on_disk_attempts = attempts
    correction.on_disk_nominal_cost = round(on_disk_nominal, 6)
    correction.on_disk_billed_cost = round(on_disk_billed, 6)
    return correction


def write_sidecar(run_name: str, *, scratch_root: Path = Path(".ape/runs")) -> Path:
    """Write `correction_sidecar.json` beside the run's other artifacts."""

    correction = recover(run_name, scratch_root=scratch_root)
    out = run_dir(run_name) / "correction_sidecar.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(correction.as_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


#: Which task types the census reports separately. Grouping by `task_type` and not by depth:
#: an arm run directly by a fanout orchestrator and one run as a lead's child are the same
#: task under the same ceiling, and splitting them would halve every n for no question.
_CENSUS_ROLES = {
    "lean_pr_review_v5_arm": "arm",
    "lean_pr_review_v5_lead": "lead",
    "lean_pr_review_v5_solo": "solo",
    "lean_pr_review_v4_semantic_judgment": "judge",
}


def _quantile(values: List[float], fraction: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round(fraction * (len(ordered) - 1)))]


def _task_types(scratch: Path) -> Dict[str, str]:
    """`task directory -> task_type`, from the record written for every scheduled task.

    A paused attempt has no result and therefore no `task_type` on it, and a run whose jobs
    all hit their ceiling would otherwise report its whole distribution as `unknown`.
    `task_outcome.json` exists precisely because `task_result.json` is reserved for a legal
    successful submission.
    """

    types: Dict[str, str] = {}
    for path in scratch.rglob("task_outcome.json"):
        try:
            types[str(path.parent)] = json.loads(
                path.read_text(encoding="utf-8")).get("task_type") or ""
        except Exception:  # noqa: BLE001 - an unreadable outcome leaves the role unknown
            continue
    return types


def token_census(run_names: Iterable[str], *,
                 scratch_root: Path = Path(".ape/runs")) -> Dict[str, Any]:
    """Per-role processed-token distributions, and the tokens-per-billed-dollar rate.

    Reads `Attempt.tokens`, so a paused attempt counts: it consumed its tokens whether or not
    it produced a result, which is exactly the case the ceiling exists for -- and the paused
    ones are the heavy ones by construction, so dropping them understates a run precisely
    where it matters. The first version of this read `result.token_usage`, which a pause
    never writes: on the ELM probe it saw 1 attempt of 11 and reported the distribution of
    the single job that finished under the ceiling.

    `result.token_usage` stays as the fallback for runs recorded before `Attempt.tokens`
    existed. Those lose their paused attempts, which is a property of what was written down
    at the time and not something this can recover; `recover()` above is what reads them.

    **The lead rows are the lead's OWN turns.** Costs bubble from children to parents and
    token counts do not -- `subtasks.nested_usage` fills only the cost fields -- so an
    attempt's `cost` is inclusive for a lead while its `tokens` are not. Dividing one by the
    other gives a rate 11.5x too low, which is what the first pass of this measurement did.
    The rate below is therefore computed from the tokens and a *recomputed* self cost, and is
    reported per run rather than per task for the same reason.
    """

    rows: List[Dict[str, Any]] = []
    for run_name in run_names:
        scratch = scratch_root / run_name
        if not scratch.is_dir():
            continue
        types = _task_types(scratch)
        for path, sample in _iter_samples(scratch):
            # `<task dir>/samples/<n>/sample.json`
            task_type = types.get(str(path.parent.parent.parent), "")
            for attempt in sample.get("attempts") or []:
                result = attempt.get("result") or {}
                usage = result.get("token_usage") or {}
                tokens = int(attempt.get("tokens")
                             or usage.get("total_tokens")
                             or (int(usage.get("input_tokens") or 0)
                                 + int(usage.get("output_tokens") or 0)))
                if not tokens:
                    continue
                rows.append({
                    "run": run_name,
                    "role": _CENSUS_ROLES.get(
                        result.get("task_type") or task_type, "other"),
                    # Only the aggregate survives on a paused attempt, so the input/output
                    # split is unknown there rather than zero.
                    "split_known": bool(usage),
                    "tokens": tokens,
                    "input_tokens": int(usage.get("input_tokens") or 0),
                    "output_tokens": int(usage.get("output_tokens") or 0),
                    "cache_read": int(usage.get("cache_read_input_tokens") or 0),
                    "turns": int(attempt.get("turns") or 0),
                    "status": str(attempt.get("status") or ""),
                    # Inclusive of nested spend for a lead; see the docstring.
                    "recorded_billed": float(attempt.get("cached_cost")
                                             or attempt.get("cost") or 0.0),
                })

    by_role: Dict[str, Any] = {}
    for role in sorted({row["role"] for row in rows}):
        group = [row for row in rows if row["role"] == role]
        tokens = [row["tokens"] for row in group]
        split = [row for row in group if row["split_known"]]
        by_role[role] = {
            "n": len(group),
            "p50": _quantile(tokens, 0.50),
            "p90": _quantile(tokens, 0.90),
            "p99": _quantile(tokens, 0.99),
            "max": max(tokens),
            "mean": round(sum(tokens) / len(tokens)),
            # Over the attempts whose split survives, and null when none does. Reporting 0.0
            # for a paused attempt would read as "it generated nothing", which is the
            # opposite of why it paused.
            "output_share": (round(sum(row["output_tokens"] for row in split)
                                   / sum(row["tokens"] for row in split), 4)
                             if split else None),
            "output_share_n": len(split),
            "turns_p50": _quantile([row["turns"] for row in group], 0.50),
        }

    # Per run, with the reason stated wherever there is no rate to state. Two different
    # reasons, and conflating them would hide the one that matters: a run whose leads bubble
    # their children's dollars cannot divide its own tokens by its own cost, and a run on a
    # model priced 0.0 has no denominator at all -- which is the entire premise of the token
    # ceiling rather than a gap in the measurement.
    rates: Dict[str, Any] = {}
    for run_name in sorted({row["run"] for row in rows}):
        group = [row for row in rows if row["run"] == run_name]
        if any(row["role"] == "lead" for row in group):
            rates[run_name] = "no rate: nested spend is inside this run's recorded costs"
            continue
        billed = sum(row["recorded_billed"] for row in group)
        rates[run_name] = (round(sum(row["tokens"] for row in group) / billed) if billed
                           else "no rate: nothing was billed, the model is priced 0.0")
    stated = [value for value in rates.values() if isinstance(value, int)]
    return {
        "attempts": len(rows),
        "by_role": by_role,
        "tokens_per_billed_dollar": rates,
        "tokens_per_billed_dollar_median": (_quantile(stated, 0.50) if stated else None),
    }


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
