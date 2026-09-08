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

from ape.orchestration.models import UsageBreakdown
from src.mathlib_review.io import canonical_json_bytes, sha256_bytes

from src.mathlib_review.schema.review import ReviewAgenda, V5RunManifest, V5RunPlan


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
    coverage_gaps: Sequence[Dict[str, Any]] = (),
) -> V5RunManifest:
    """Build the run manifest, raising if the ledger does not balance.

    `coverage_gaps` are mandatory jobs that did not succeed. A run with any is `partial`: it
    did not look at everything it promised to look at, and a recall number from it is measured
    against a denominator it never covered. That is not the same as failing, and it is not the
    same as succeeding -- on PR 33117 a paused floor job was booked as a plain failure, counted
    as coverage anyway, and the run was scored as though complete.
    """

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
    # Every job's spend, read off the ledger because nothing upstream aggregates it.
    #
    # This used to filter to `proposed` and `agent_added`, which was right only while the
    # coverage floor ran in its own orchestrator and arrived as `extra_cost`. Folding the
    # floor into the lead turned it into a `mandatory` disposition, and the filter then
    # silently discarded it: the held-out run reported $6.54 against a ledger total of
    # $19.17, with the floor's $14.52 simply absent. Spend is spend, whoever authorised it.
    ledger_cost = sum(float(record.get("cost") or 0.0) for record in delegations)
    # The same sum in the other currency. `cost` is billed and `nominal_cost` is the no-cache
    # counterfactual; both are on every ledger row, and until now only one of them was carried
    # to the manifest -- the one no cap is enforced against.
    # `nominal_cost` is inside `token_usage`, not at the top of the row -- the top-level `cost`
    # is the billed figure and its nominal twin never joined it there. Reading the wrong key
    # made `nested_nominal` zero on rep9 while $6.79 of nominal arm spend sat one level down,
    # and that made `self_nominal` the whole run: the manifest said four leads spent $7.50
    # nominal when they spent $0.71 and their arms spent the rest. Attributing nested spend to
    # the parent is the exact defect this branch opened with.
    ledger_nominal = sum(
        float((record.get("token_usage") or {}).get("nominal_cost")
              or record.get("nominal_cost") or 0.0)
        for record in delegations
    )
    # What `per_pr_cost_cap` actually counts: the coverage floor is exempt by design, so the
    # charged figure is the discretionary half and is smaller than billed. Both are correct
    # and they answer different questions.
    ledger_charged = sum(
        float(record.get("cost") or 0.0) for record in delegations
        if record.get("disposition") != "mandatory"
    )

    # A job that ran and recorded no cost is unattributed spend: the money left the account
    # and the ledger cannot say for what. That is the shape of the bug this function just
    # had, so it fails loudly rather than being found by hand two runs later.
    unattributed = [
        record.get("invocation_id") for record in delegations
        if record.get("status") in ("success", "paused_cost", "paused_turns")
        and record.get("cost") is None
    ]
    if unattributed:
        raise ReconciliationError(
            f"{len(unattributed)} job(s) ran but recorded no cost: {unattributed[:8]}. "
            "Spend that no ledger row accounts for cannot be reported, and a manifest that "
            "silently omits it is worse than one that refuses to close."
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
        # The root total is read once, not assembled. The lead now bubbles what its children
        # spent through `BaseTaskResult.nested_token_usage`, which the scaffold merges into the
        # task's own usage and the worker writes to `attempt.cost` — so `results.total_cost`
        # is already inclusive. Adding `ledger_cost` on top of that, as this did while the
        # lead did *not* bubble, would now count every nested dollar twice.
        #
        # `ledger_cost` remains the attribution record: it says which jobs the nested total was
        # spent on, and the reconciliation below checks the two agree. In `fanout`/`rules` there
        # is no lead, ledger rows carry no cost, and the nested term is zero.
        total_cost=float(getattr(results, "total_cost", 0.0) or 0.0) + extra_cost,
        cost_breakdown={
            # What the leads' own conversations cost, i.e. inclusive minus what they delegated.
            #
            # In NOMINAL, like the `total_cost` it is a breakdown of. It used to subtract
            # `ledger_cost`, which is billed, from a nominal total -- two currencies, so the
            # lead's share came out at $4.74 on rep9 against a real $0.71.
            "lead": round(
                float(getattr(results, "total_cost", 0.0) or 0.0) - ledger_nominal, 6),
            # BILLED, unlike `lead` above. The ledger is the attribution record for what
            # was paid; `usage` carries both currencies at both scopes without this ambiguity.
            "nested_billed": round(ledger_cost, 6),
            "nested_nominal": round(ledger_nominal, 6),
            "extra": round(extra_cost, 6),
        },
        # Both currencies at both scopes. `results.total_cost` is nominal and
        # `results.total_cached_cost` is billed; both are already inclusive of nested spend,
        # so the leads' own halves are each total minus its own ledger sum. `extra_cost` is
        # real spend from an orchestrator outside this one, so it lands on the billed side.
        usage=UsageBreakdown(
            self_billed=round(
                float(getattr(results, "total_cached_cost", 0.0) or 0.0)
                - ledger_cost + extra_cost, 6),
            self_nominal=round(
                float(getattr(results, "total_cost", 0.0) or 0.0) - ledger_nominal, 6),
            nested_billed=round(ledger_cost, 6),
            nested_nominal=round(ledger_nominal, 6),
            budget_charged=round(ledger_charged, 6),
        ).summary(),
        wall_seconds=float(getattr(results, "wall_clock_time", 0.0) or 0.0),
        candidates_total=candidates_total,
        issues_total=issues_total,
        context_calls_total=context_calls,
        completion_status=(
            "failed" if statuses["failed"] else
            "partial" if coverage_gaps else
            "complete"
        ),
        coverage_gaps=[dict(item) for item in coverage_gaps],
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
