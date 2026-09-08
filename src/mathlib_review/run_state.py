"""What states a review run can be in, and which moves between them are legal.

Every transition below is already enforced somewhere -- `TaskExecutionStatus` in the
orchestrator, `completion_status` on the run manifest, the judge's refusal to score a run that
did not cover what it promised. What did not exist is a place that states the machine, so the
guarantee had to be assembled by reading three files and hoping they agreed. They did; the
reason to write it down is that the next change has somewhere to be checked against.

    planned ──▶ running ◀──▶ paused
                   │
                   ├──▶ generated ──▶ finalized ──▶ judged
                   └──▶ partial
                   └──▶ failed

**`paused` is not `partial`.** `paused` is a run state: work stopped on a budget or turn limit
and can resume. `partial` is a *closed* run that cannot satisfy required coverage -- a mandatory
job ran and failed, so a work unit was never reviewed. The distinction is the one that voided
two September runs: they closed `failed`, were scored anyway, and their recall was reported
against a denominator that included units nobody looked at.

**A partial run never enters the successful chain.** Forensic processing is allowed and
labelled: `judge --allow-partial` scores it and marks the output forensic. What is refused is
the silent path where a partial run is judged as though it were complete.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, FrozenSet


class RunState(str, Enum):
    """The state of a whole review run, as opposed to one task's execution."""

    #: Sealed, priced, nothing spent. What `plan` produces and stops at.
    PLANNED = "planned"
    #: Model calls in flight.
    RUNNING = "running"
    #: Stopped on a limit, resumable. Spend is booked; nothing is concluded.
    PAUSED = "paused"
    #: Closed, and every mandatory job that was supposed to run did.
    GENERATED = "generated"
    #: Closed, and a mandatory job did not succeed. Numbers from here measure coverage loss.
    PARTIAL = "partial"
    #: Closed on an error that is not a coverage gap.
    FAILED = "failed"
    #: Findings assembled, channels assigned, `findings.jsonl` written.
    FINALIZED = "finalized"
    #: Scored against gold.
    JUDGED = "judged"


#: The only moves that are legal. A state absent as a key is terminal.
TRANSITIONS: Dict[RunState, FrozenSet[RunState]] = {
    RunState.PLANNED: frozenset({RunState.RUNNING}),
    RunState.RUNNING: frozenset({
        RunState.PAUSED, RunState.GENERATED, RunState.PARTIAL, RunState.FAILED}),
    # A resume goes back to running; it does not jump straight to a closed state, because the
    # thing that closes a run is reconciliation and that only happens after work stops.
    RunState.PAUSED: frozenset({RunState.RUNNING}),
    RunState.GENERATED: frozenset({RunState.FINALIZED}),
    RunState.FINALIZED: frozenset({RunState.JUDGED}),
    # `partial` and `failed` are terminal for the successful chain. Forensic reading of either
    # is allowed and is not a transition -- it produces a separately labelled artifact rather
    # than moving the run forward.
    RunState.PARTIAL: frozenset(),
    RunState.FAILED: frozenset(),
    RunState.JUDGED: frozenset(),
}

#: States a run may be scored from without `--allow-partial`.
SCOREABLE: FrozenSet[RunState] = frozenset({RunState.GENERATED, RunState.FINALIZED})


class IllegalTransition(RuntimeError):
    """A move the machine does not allow."""


def assert_transition(current: RunState, target: RunState) -> None:
    allowed = TRANSITIONS.get(current, frozenset())
    if target not in allowed:
        raise IllegalTransition(
            f"a run cannot go {current.value} -> {target.value}. From {current.value} the "
            f"legal moves are {sorted(s.value for s in allowed) or 'none, it is terminal'}."
        )


def from_manifest(completion_status: str) -> RunState:
    """The manifest's vocabulary, mapped onto this one.

    `run_manifest.json` writes `complete` / `partial` / `failed`, which predate this module.
    They are not renamed: the string is in every manifest in the tree and renaming it would
    make old runs unreadable to say the same thing in different words.
    """

    return {
        "complete": RunState.GENERATED,
        "partial": RunState.PARTIAL,
        "failed": RunState.FAILED,
        "incomplete": RunState.PARTIAL,
    }.get(completion_status, RunState.FAILED)
