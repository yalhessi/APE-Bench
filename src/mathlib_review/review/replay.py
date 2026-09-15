"""Decision-turn replay for review arms: what the arm decides, with its investigation held still.

Every change aimed at the submission decision -- abstention wording, the bar, field order,
confidence elicitation -- used to be tested with a whole rep, which re-samples the
investigation as well. A decision change then competes with investigation variance it did not
cause, read through a judge that splits its own vote on ~11% of pairs. Forcing the decision
alone moved issue recall 0.20 -> 0.50 on the same PRs, so the decision is where this system's
findings go missing (`docs/todo/replay-decision-turn.md`).

The replay itself is not review code. `ape.scaffolds.ape_agent.replay` runs any recorded task
again from a point inside its conversation, as the same task type; this module supplies the
two things that are review's own: where an arm's decision starts, and what it decided.

**Where the decision starts: before the first `submit_candidates` call.** Not the last: ~9% of
arm sessions on the held-out reps had their first submission refused (26 / 31 / 28 of 321 / 316 /
322) and then repaired it, and the arm task counts refusals on its instance
(`_mute_abstentions`, `_forced_presses`), which a replayed instance starts at zero. The repair
turns are part of the decision stage and are re-sampled with it. Measured on the same reps: no
session puts another tool call in the assistant node that submits, and every arm session has a
successful attempt with a submission.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ape.scaffolds.ape_agent.replay import tool_calls

SUBMIT_TOOL = "submit_candidates"


def submission_summary(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """One `submit_candidates` call, reduced to the levels a replay is compared at.

    `argument_order` and `candidate_field_order` are the model's emission order, read off the
    call arguments -- a field-order condition is effective only if the model follows it, and the
    accepted result cannot say, because validation re-serialises it in schema order.
    """

    candidates = [item for item in (arguments.get("candidates") or []) if isinstance(item, dict)]
    return {
        "filed": bool(candidates),
        "abstention_reason": None if candidates else arguments.get("abstention_reason"),
        "anchors": sorted({str(item.get("primary_change_id")) for item in candidates}),
        "candidate_keys": sorted({
            "|".join(str(item.get(key)) for key in
                     ("primary_change_id", "concern_family", "issue_kind"))
            for item in candidates}),
        "model_confidence": [item.get("model_confidence") for item in candidates],
        "argument_order": list(arguments),
        "candidate_field_order": [list(item) for item in candidates],
    }


def accepted_summary(result: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """The submission the task accepted, from its result; None when nothing was accepted."""

    if not result or not result.get("success"):
        return None
    summary = submission_summary({
        "candidates": result.get("candidates") or [],
        "abstention_reason": (result.get("abstention") or {}).get("reason"),
    })
    for key in ("argument_order", "candidate_field_order"):
        summary.pop(key)
    return summary


def decision_record(nodes: List[Dict[str, Any]], start: int) -> Dict[str, Any]:
    """Every submission from `start` on: how many turns, what was refused, what came first."""

    calls = tool_calls(nodes, start, SUBMIT_TOOL)
    return {
        "turns": sum(1 for node in nodes[start:] if node.get("type") == "assistant"),
        "submissions": len(calls),
        "refusals": [call["message"] for call in calls if call["accepted"] is False],
        "first": submission_summary(calls[0]["arguments"]) if calls else None,
    }
