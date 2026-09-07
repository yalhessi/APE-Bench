"""Apply the lead's read on what came back — but only ever to remove or combine.

The lead has always emitted `candidate_assessments`. Nothing read them: they were sealed
into the result, counted in the trajectory view, and applied nowhere. So a lead that
correctly noticed two specialists had said the same thing in different words watched both
findings get suppressed as an unresolved conflict, which is the outcome the merge takes when
it cannot choose between equal warrants. On the verify probe that cost both halves of a
correct observation — one arm asked to rename `dist_le_dist_of_mapsTo_ball_self`, the other
to fix its docstring, and the merge published neither.

**The authority granted here is subtractive, and that boundary is the whole design.** An
assessment may drop a candidate or fold it into another. It may never admit one, never
attach a warrant, never raise a severity, and never resurrect something a gate rejected —
because publication is a property of evidence, and a model that could talk a finding past
the evidence chain would make every published finding mean less. What the lead decides is
*which of the things already entitled to be said are worth saying*.

Consequently this runs **before** projection, on candidates, not after it on findings. A
candidate the lead drops never reaches the evidence chain at all; a candidate it keeps gets
exactly the scrutiny it would have had anyway.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

#: How the lead names another candidate in `duplicate_of`. The lead sees `invocation_id` and
#: a per-claim `ordinal` in the `delegate` response, so this is the only address it can
#: actually write. A bare `candidate_id` is accepted too, for callers that have one.
DUPLICATE_ADDRESS = "<invocation_id>#<ordinal>"


def _address_index(responses: Iterable[Dict[str, Any]]) -> Dict[str, Tuple[str, Optional[str]]]:
    """`invocation_id` -> the `(work_unit_id, spec_id)` its candidates were sealed under.

    Enough to locate a candidate, because `trace.reconcile` already refuses a run in which
    one `(arm, work unit)` pair ran twice — so the pair plus an ordinal is unique.
    """

    index: Dict[str, Tuple[str, Optional[str]]] = {}
    for response in responses:
        invocation_id = response.get("invocation_id")
        if invocation_id:
            index[invocation_id] = (response.get("work_unit_id"), response.get("spec_id"))
    return index


def _resolve(address: str, by_invocation, by_candidate_id) -> Optional[str]:
    """Turn a lead-written address into a `candidate_id`, or `None` if it names nothing."""

    if address in by_candidate_id:
        return address
    invocation_id, _, ordinal = address.rpartition("#")
    if not invocation_id or not ordinal.isdigit():
        return None
    return by_invocation.get((invocation_id, int(ordinal)))


def apply_assessments(
    *,
    generalist: Sequence[Any],
    specialist: Sequence[Any],
    evidence_specialist: Sequence[Any],
    responses: Iterable[Dict[str, Any]],
    assessments: Iterable[Dict[str, Any]],
    logger=None,
) -> Tuple[List[Any], List[Any], List[Any], List[Tuple[Any, str]], Dict[str, Any]]:
    """Drop and fold candidates per the lead's assessments; return what survives.

    Returns the three surviving candidate lists, the removed candidates paired with the
    reason each was removed, and a report.

    **The removed candidates are returned, not discarded.** Measured on heldout11 rep2:
    of the twelve candidates that landed on a gold obligation's site, synthesis deleted
    seven — five dropped and two folded — and because they never reached `findings.jsonl`
    the judge never saw them and nobody could say whether the lead had been right. A
    decision that destroys its own evidence cannot be evaluated. `finalize` projects these
    into `diagnostic` findings *after* the merge, so the published review is unchanged and
    the audit trail is complete.

    The report is not optional bookkeeping either: an assessment that named nothing is the
    signal that the lead was addressing candidates it could not see, which is a routing bug
    wearing a synthesis costume.
    """

    responses = list(responses)
    assessments = [dict(item) for item in assessments]
    everything = [*generalist, *specialist, *evidence_specialist]
    by_candidate_id = {item.candidate_id: item for item in everything}

    invocation_pair = _address_index(responses)
    by_invocation: Dict[Tuple[str, int], str] = {}
    for invocation_id, (work_unit_id, spec_id) in invocation_pair.items():
        for candidate in everything:
            if candidate.work_unit_id == work_unit_id and candidate.spec_id == spec_id:
                by_invocation[(invocation_id, candidate.ordinal)] = candidate.candidate_id

    verdicts: Dict[str, int] = {}
    dropped: Dict[str, str] = {}
    duplicate_of: Dict[str, str] = {}
    unmatched: List[Dict[str, Any]] = []
    recorded_not_applied: List[str] = []

    for item in assessments:
        verdict = item.get("verdict")
        verdicts[verdict] = verdicts.get(verdict, 0) + 1
        address = f"{item.get('invocation_id')}#{item.get('candidate_ordinal')}"
        candidate_id = _resolve(address, by_invocation, by_candidate_id)
        if candidate_id is None:
            unmatched.append({"address": address, "verdict": verdict,
                              "reason": "names no candidate this run produced"})
            continue
        # Severity is deliberately not applied. Re-grading a claim is neither removing nor
        # combining it, and `blocking` is what the per-PR limit orders publication by.
        if item.get("severity"):
            recorded_not_applied.append(candidate_id)
        if verdict == "drop":
            dropped[candidate_id] = item.get("reason") or "the lead dropped this claim"
        elif verdict == "duplicate_of":
            target = _resolve(str(item.get("duplicate_of") or ""),
                              by_invocation, by_candidate_id)
            if target is None or target == candidate_id:
                # A duplicate of nothing is not a duplicate. Dropping it here would delete a
                # claim on the strength of a pointer that resolves to no other claim.
                unmatched.append({
                    "address": address, "verdict": verdict,
                    "duplicate_of": item.get("duplicate_of"),
                    "reason": f"duplicate_of names no other candidate (expected {DUPLICATE_ADDRESS})",
                })
                continue
            duplicate_of[candidate_id] = target

    # Follow each duplicate chain to a root that is not itself a duplicate. A cycle is broken
    # deterministically on the smallest id, so a lead that marks two claims as duplicates of
    # each other loses one rather than both.
    absorbed: Dict[str, str] = {}
    cycles_broken = 0
    for candidate_id in sorted(duplicate_of):
        seen = [candidate_id]
        target = duplicate_of[candidate_id]
        while target in duplicate_of and target not in seen:
            seen.append(target)
            target = duplicate_of[target]
        if target in seen:
            survivor = min(seen)
            cycles_broken += 1
            if candidate_id == survivor:
                continue
            target = survivor
        absorbed[candidate_id] = target

    removed = {**{cid: "dropped by the lead" for cid in dropped},
               **{cid: f"folded into {tid}" for cid, tid in absorbed.items()}}

    def _keep(items: Sequence[Any]) -> List[Any]:
        return [item for item in items if item.candidate_id not in removed]

    # Ordered by candidate_id so the audit trail is byte-stable across runs.
    removed_candidates = [
        (item, removed[item.candidate_id])
        for item in sorted(everything, key=lambda c: c.candidate_id)
        if item.candidate_id in removed
    ]

    report = {
        "assessments": len(assessments),
        "by_verdict": dict(sorted(verdicts.items())),
        "candidates_dropped": len(dropped),
        "candidates_absorbed": len(absorbed),
        "duplicate_cycles_broken": cycles_broken,
        "severity_overrides_recorded_not_applied": len(recorded_not_applied),
        "unmatched": unmatched,
        "removed_by_candidate": dict(sorted(removed.items())),
        # The invariant, asserted in the artifact rather than only in a test: synthesis is
        # subtractive, so the surviving set is always a subset of what the arms produced.
        "candidates_in": len(everything),
        "candidates_out": len(everything) - len(removed),
    }
    if logger and assessments:
        logger.info(
            "lead synthesis: %d assessment(s) -> %d dropped, %d folded, %d unmatched",
            len(assessments), len(dropped), len(absorbed), len(unmatched),
        )
        if unmatched:
            logger.warning(
                "%d assessment(s) named no candidate this run produced — the lead was "
                "addressing claims it could not see: %s",
                len(unmatched), unmatched[:4],
            )
    return (_keep(generalist), _keep(specialist), _keep(evidence_specialist),
            removed_candidates, report)
