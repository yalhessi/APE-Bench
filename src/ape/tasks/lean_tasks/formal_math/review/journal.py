"""The lead's state, as an append-only record instead of an attribute.

`_state()` kept everything the lead had done on `self._delegation_state`, guarded by a
`hasattr`. A resumed lead is a fresh object, so a resume reset all of it, and each of the four
things it reset costs money:

* `delegated_spend` -> 0, so the per-PR cap hands out a second full budget;
* `requested` -> empty, so a job that already ran can be dispatched again -- the dedup that
  exists because "a second run of an identical job produces a second set of candidates the
  merge would then have to tell apart from a genuine repeat finding";
* `floor_done` -> False, so the coverage floor runs a second time, and the floor is the
  expensive half (a measured $10.05 on PR 33149);
* `wave` -> 0, so the second wave 1 writes into the first wave 1's subtask directory.

So a resumed lead could spend the whole budget again and overwrite the evidence that it had.
Nothing detected this, because a resumed run looks exactly like a fresh one from inside.

The journal is written as it goes and replayed on construction. Two things are deliberately
*not* in it:

* **Reservations.** `reserved` bounds jobs dispatched and not yet settled. After a restart
  nothing is in flight, so replaying a reservation would consume budget for work that is not
  running -- the same bug the wave-failure path already releases.
* **`JobSpec.payload`.** It is the arm's whole rendered task data and it comes from the pool
  file, unchanged. Journaling it would duplicate the pool on every dispatch; it is rejoined
  from the pool by `invocation_id` at replay.
"""

from __future__ import annotations

import json
from dataclasses import asdict, fields
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

#: Events. Kept as strings rather than an enum: they are written to disk and read back by
#: anything that wants to audit a run, so the wire form is the interface.
COMPREHENSION = "comprehension"
WAVE_OPENED = "wave_opened"
WAVE_FAILED = "wave_failed"
SETTLED = "settled"


def append(path: Optional[str], event: Dict[str, Any]) -> None:
    """One line, flushed. Never raises: a journal failure must not lose a wave's results."""

    if not path:
        return
    try:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True, default=str) + "\n")
    except Exception:  # noqa: BLE001 - see the docstring
        pass


def spec_row(spec: Any) -> Dict[str, Any]:
    """A `JobSpec` without its payload."""

    row = asdict(spec)
    row.pop("payload", None)
    return row


def _spec_from_row(spec_cls, row: Dict[str, Any], payload: Dict[str, Any]):
    known = {item.name for item in fields(spec_cls)}
    return spec_cls(payload=payload, **{k: v for k, v in row.items() if k in known})


def replay(
    path: Optional[str],
    state: Dict[str, Any],
    *,
    pool: Dict[str, Any],
    spec_cls,
    outcome_cls,
    logger=None,
) -> Dict[str, Any]:
    """Fold the journal into a fresh state dict, in place.

    Idempotent by construction: every event is an assignment or a monotone accumulation over a
    set keyed by `invocation_id`, so replaying a journal twice onto a fresh state gives the
    same state. A job that settled twice -- which the dedup is there to prevent and which a
    crash between dispatch and settle cannot produce -- would be counted once.
    """

    if not path or not Path(path).is_file():
        return state

    specs: Dict[str, Any] = {}
    settled: Dict[str, Dict[str, Any]] = {}
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        if logger is not None:
            logger.warning("could not read lead journal %s: %s", path, exc)
        return state

    for number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            # A crash mid-write truncates the last line. Everything before it is intact, and
            # stopping here is right: the events are ordered, so a later line cannot be
            # trusted once one is unreadable.
            if logger is not None:
                logger.warning("lead journal %s: line %d is truncated, replay stops there",
                               path, number)
            break

        event = row.get("event")
        if event == COMPREHENSION:
            state["comprehension"] = row.get("comprehension")
        elif event == WAVE_OPENED:
            state["wave"] = max(state["wave"], int(row.get("wave") or 0))
            for spec_data in row.get("specs") or []:
                invocation_id = spec_data.get("invocation_id")
                if invocation_id:
                    specs[invocation_id] = spec_data
                    state["requested"].add(invocation_id)
            if row.get("floor"):
                state["floor_done"] = True
        elif event == WAVE_FAILED:
            for invocation_id in row.get("invocation_ids") or []:
                state["requested"].discard(invocation_id)
        elif event == SETTLED:
            outcome = row.get("outcome") or {}
            invocation_id = outcome.get("invocation_id")
            if invocation_id:
                settled[invocation_id] = outcome

    for invocation_id, outcome_row in settled.items():
        spec_data = specs.get(invocation_id)
        payload = (pool.get(invocation_id) or {}).get("task_data")
        if spec_data is None or payload is None:
            # The dispatch that produced this settlement is not in the journal, or the pool no
            # longer offers this invocation. Skipping keeps the spend accounting, which is
            # what the cap reads, and drops only the reconstructed object.
            if logger is not None:
                logger.warning("lead journal: %s settled but cannot be rebuilt "
                               "(spec=%s, pool=%s)", invocation_id,
                               spec_data is not None, payload is not None)
            state["spend"] += float(outcome_row.get("cost") or 0.0)
            continue
        known = {item.name for item in fields(outcome_cls)}
        outcome = outcome_cls(**{k: v for k, v in outcome_row.items() if k in known})
        spec = _spec_from_row(spec_cls, spec_data, payload)
        state["outcomes"][invocation_id] = (outcome, spec)
        state["requested"].add(invocation_id)
        state["spend"] += outcome.cost
        if spec.disposition != "mandatory":
            state["delegated_spend"] += outcome.cost

    return state
