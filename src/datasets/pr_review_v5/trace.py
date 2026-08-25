"""Close a run only when every proposal is accounted for.

v4's `run_contract.seal_run` asserts that every expected work unit produced exactly one
successful terminal response. That is the right rule for a fixed pipeline and an impossible
one for a lead that prunes — and weakening it for everyone would remove a guarantee v4's
whole record rests on. So v5 reconciles against *dispositions* instead:

* every enumerated proposal ends as `mandatory`, `proposed`, `agent_added` or `pruned`, and
* every response maps to exactly one recorded job.

The guarantee has the same shape as v4's — nothing ran that was not planned, nothing planned
went missing without a reason — while allowing the set that ran to be a decision rather than
a constant.

Failed and paused jobs are counted, never dropped. A run summary that reports only what
succeeded makes budget exhaustion invisible, and budget exhaustion is a fact about routing,
which is the thing being measured.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Sequence

from src.datasets.pr_review_v4.io import canonical_json_bytes, sha256_bytes

from .schema import ReviewAgenda, V5RunManifest, V5RunPlan


class ReconciliationError(RuntimeError):
    """A run could not be closed because its ledger does not balance."""


def reconcile(
    *,
    agenda: ReviewAgenda,
    delegations: Sequence[Dict[str, Any]],
    responses: Sequence[Dict[str, Any]],
    plan: V5RunPlan,
    results: Any,
    issues_total: int,
    extra_cost: float = 0.0,
) -> V5RunManifest:
    """Build the run manifest, raising if the ledger does not balance."""

    proposals = {item.proposal_id: item for item in agenda.proposals}
    by_invocation: Dict[str, Dict[str, Any]] = {}
    for record in delegations:
        invocation_id = record.get("invocation_id")
        if invocation_id in by_invocation:
            raise ReconciliationError(
                f"{invocation_id} appears twice in the delegation ledger; a pair may run "
                "at most once per review"
            )
        by_invocation[invocation_id] = record

    missing = [
        proposal_id for proposal_id, proposal in sorted(proposals.items())
        if proposal.invocation_id not in by_invocation
    ]
    if missing:
        raise ReconciliationError(
            f"{len(missing)} proposal(s) have no disposition: {missing[:8]}. Every "
            "enumerated pair must end delegated or pruned."
        )

    unplanned = [
        record.get("invocation_id") for record in delegations
        if record.get("invocation_id") not in {
            item.invocation_id for item in agenda.proposals
        }
    ]
    if unplanned:
        raise ReconciliationError(
            f"{len(unplanned)} job(s) ran that the sealed agenda never enumerated: "
            f"{unplanned[:8]}. A job outside the pool has a prompt the plan did not vouch for."
        )

    orphan = [
        response.get("invocation_id") for response in responses
        if response.get("invocation_id") not in by_invocation
    ]
    if orphan:
        raise ReconciliationError(
            f"{len(orphan)} response(s) map to no recorded job: {orphan[:8]}"
        )

    counted = {"mandatory": 0, "proposed": 0, "agent_added": 0, "pruned": 0}
    statuses = {"success": 0, "failed": 0, "paused_cost": 0, "paused_turns": 0}
    total_cost = 0.0
    context_calls = 0
    for record in delegations:
        counted[record.get("disposition", "pruned")] = (
            counted.get(record.get("disposition", "pruned"), 0) + 1
        )
        status = record.get("status")
        if status in statuses:
            statuses[status] += 1
        total_cost += float(record.get("cost") or 0.0)
        context_calls += len(record.get("context_calls") or [])

    delegated = counted["mandatory"] + counted["proposed"] + counted["agent_added"]
    # Specialist spend, read off the ledger because nothing upstream aggregates it. The
    # floor's rows carry no cost (it is passed in as `extra_cost`), so this cannot double
    # count them.
    delegated_cost = sum(
        float(record.get("cost") or 0.0) for record in delegations
        if record.get("disposition") in ("proposed", "agent_added")
    )
    candidates_total = sum(len(item.get("candidates") or []) for item in responses)
    manifest = V5RunManifest(
        run_id=plan.run_id,
        run_name=plan.run_name,
        run_plan_sha256=plan.source_sha256,
        routing_mode=agenda.routing_mode,
        proposals_total=len(proposals),
        delegated=delegated,
        pruned=counted["pruned"],
        agent_added=counted["agent_added"],
        mandatory=counted["mandatory"],
        succeeded=statuses["success"],
        failed=statuses["failed"],
        paused=statuses["paused_cost"] + statuses["paused_turns"],
        # The orchestrator's own total is authoritative for spend; the per-job sum is only
        # what the ledger could attribute, and an unattributed cost is still spent.
        # Three separate orchestrators spend money in a lead run and none of them knows
        # about the others: the leads (`results`), the coverage floor (`extra_cost`), and
        # every specialist, which runs in a nested orchestrator under its lead's attempt and
        # is therefore absent from `results.total_cost` entirely. Summing only the first two
        # under-reported rep3 by $1.98 on $6.27 — about a third of the run.
        total_cost=(
            float(getattr(results, "total_cost", 0.0) or 0.0)
            + extra_cost
            + delegated_cost
        ),
        wall_seconds=float(getattr(results, "wall_clock_time", 0.0) or 0.0),
        candidates_total=candidates_total,
        issues_total=issues_total,
        context_calls_total=context_calls,
        completion_status="complete" if statuses["failed"] == 0 else "failed",
        source_sha256="",
    )
    return manifest.model_copy(update={"source_sha256": sha256_bytes(canonical_json_bytes(
        manifest.model_dump(mode="json", exclude={"source_sha256"})))})


def routing_report(delegations: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """What the lead actually did — the first thing to read after a run.

    Deliberately reported before any recall number. If routing is degenerate — the lead
    pruned nothing, added nothing, and spent uniformly — then the mechanism did not engage
    and a recall figure is measuring the arms, not the delegation.
    """

    rows = list(delegations)
    by_arm: Dict[str, Dict[str, int]] = {}
    by_tier: Dict[str, int] = {}
    tools: Dict[str, int] = {}
    for record in rows:
        arm = by_arm.setdefault(record.get("arm_id", "?"),
                                {"delegated": 0, "pruned": 0, "agent_added": 0})
        disposition = record.get("disposition")
        if disposition == "pruned":
            arm["pruned"] += 1
        else:
            arm["delegated"] += 1
            if disposition == "agent_added":
                arm["agent_added"] += 1
        if record.get("budget_tier"):
            by_tier[record["budget_tier"]] = by_tier.get(record["budget_tier"], 0) + 1
        for call in record.get("context_calls") or []:
            tools[call.get("tool", "?")] = tools.get(call.get("tool", "?"), 0) + 1
    delegated = sum(item["delegated"] for item in by_arm.values())
    pruned = sum(item["pruned"] for item in by_arm.values())
    return {
        "jobs_delegated": delegated,
        "jobs_pruned": pruned,
        "jobs_agent_added": sum(item["agent_added"] for item in by_arm.values()),
        "by_arm": by_arm,
        "by_budget_tier": by_tier,
        "context_calls_by_tool": tools,
        # The two ways routing fails to engage at all. Both are worth seeing before recall.
        "degenerate_fanout": pruned == 0,
        "degenerate_silent": delegated == 0,
    }
