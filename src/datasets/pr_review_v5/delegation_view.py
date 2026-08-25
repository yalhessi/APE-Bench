"""Join a v5 run's routing ledger into one view per PR: what the lead was given, chose, and got.

The overlay used to receive a v5 run as `conditions=[...]`, and `build_overlay` reads exactly
one file from a condition — `findings.jsonl`. So it carried the specialists' *conclusions*
and nothing about the work: no delegation, no brief, no wave, no cost, no transcript, and no
record of what the lead declined.

This module assembles the missing half by joining five sources on `invocation_id`:

    agenda.json          proposals[]  -> site_change_ids, mandatory, cost_hint
    delegations.jsonl    the ledger   -> disposition, brief, budget, cost, outcome
    arm_responses.jsonl  what came back -> candidates, verification artifacts
    trajectory/          the sidecar  -> wave, tier, real timings, real tokens, transcripts
    run_plan.json        the caps the lead was held to

Two things about the data shape it is worth stating plainly, because they change what the
view should say:

**The lead never leaves a site unlooked-at.** Every one of the held-out run's 432 sites got a
mandatory generalist; the floor is prepended to wave 1 regardless of what the model asked
for. What the lead actually declines is *specialist* coverage — 323 of those 432 sites had
every specialist pruned, a mean of 4.6 declined per site. So "where it chose not to look" is
a fact about (site, arm) pairs, never about sites.

**Two of the ledger's numeric fields are the tier's aggregate, not the job's.** `token_usage`
and `wall_seconds` are written once per tier orchestrator and copied onto every job in it:
239 ran rows carry 29 distinct `wall_seconds`, one repeated 108 times, and summing
`token_usage.total_cost` yields $1,141.84 against a real $19.17. The sibling `cost` is
per-job and correct. This module reads `cost` and takes tokens and timing from the sidecar;
`_LEDGER_POISONED` names the fields so the prohibition is greppable and testable.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from .paths import run_dir

DELEGATION_VIEW_VERSION = "v5-delegation-view/1"

#: Never read these from `delegations.jsonl`; they are per-tier aggregates. Cost comes from
#: the row's own `cost`, tokens and timing from `trajectory/invocations.jsonl`.
_LEDGER_POISONED = ("token_usage", "wall_seconds")

_RAN = ("mandatory", "proposed", "agent_added")


def _read_jsonl(path: Path) -> List[dict]:
    """Raw dicts, deliberately not pydantic.

    `DelegationRecord` in `schema.py` lacks `brief`, `delivered_prompt_sha256` and
    `reason_given`, all three of which `lead.py::_reconcile` writes. Validating through the
    model would silently drop the lead's stated reasoning, which is the most interesting
    thing in the file.
    """

    if not path.is_file():
        return []
    rows = []
    for line in path.read_text().splitlines():
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def _read_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}


@dataclass
class Delegation:
    """One (arm x work unit) job: proposed, and then run or declined."""

    invocation_id: str
    arm_id: str
    work_unit_id: str
    pr_number: int
    disposition: str
    reason: str
    site_change_ids: List[str]
    mandatory: bool
    cost_hint: Optional[float]
    # Set only when the job ran.
    status: Optional[str] = None
    budget_tier: Optional[str] = None
    budget_cap: Optional[float] = None
    cost: Optional[float] = None
    candidate_count: Optional[int] = None
    verification_artifact_count: Optional[int] = None
    #: The lead's instruction to the specialist. `None` for the mandatory floor, which is
    #: not a decision and carries no brief.
    brief: Optional[dict] = None
    #: The sealed template's hash and what was actually sent. Recorded for auditing, but
    #: they are NOT a test for whether a brief was attached: measured across the held-out
    #: run they differ on all 239 ran jobs, briefed or not, because site context is appended
    #: to the template either way. `brief is not None` is the only signal for that.
    rendered_prompt_sha256: Optional[str] = None
    delivered_prompt_sha256: Optional[str] = None
    context_calls: List[dict] = field(default_factory=list)
    # From the trajectory sidecar; absent when `.ape` was not extracted.
    wave: Optional[str] = None
    tier: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    execution_time: Optional[float] = None
    token_usage: Dict[str, Optional[float]] = field(default_factory=dict)
    turns: int = 0
    tool_calls: Dict[str, int] = field(default_factory=dict)
    has_transcript: bool = False
    #: One line per candidate the arm returned, for the lead view's outcome column.
    claims: List[dict] = field(default_factory=list)


@dataclass
class LeadView:
    """Everything one lead did for one PR."""

    pr_number: int
    episode_id: Optional[str]
    delegations: List[Delegation]
    caps: Dict[str, Optional[float]]
    arms: List[dict]
    waves: List[dict]
    coverage: Dict[str, int]
    cost: Dict[str, float]
    # The lead's own conversation, from the sidecar.
    conversation_id: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    execution_time: Optional[float] = None
    lead_cost: Optional[float] = None
    lead_turns: int = 0
    lead_tool_calls: Dict[str, int] = field(default_factory=dict)
    lead_token_usage: Dict[str, Optional[float]] = field(default_factory=dict)
    #: Recorded by `submit_routing`, never applied by the finalization chain.
    assessments: List[dict] = field(default_factory=list)
    has_transcript: bool = False


def is_v5_run(directory: Path) -> bool:
    """A v5 run directory is identifiable by its agenda; a v4 condition has none.

    Structural rather than name-based, so a renamed or copied run still reads correctly.
    """

    return (directory / "agenda.json").is_file() and (directory / "delegations.jsonl").is_file()


def load_lead_views(directory: Path) -> Dict[int, LeadView]:
    """One `LeadView` per PR in the run, or `{}` if this is not a v5 run."""

    if not is_v5_run(directory):
        return {}

    agenda = _read_json(directory / "agenda.json")
    proposals = {item["invocation_id"]: item for item in agenda.get("proposals", [])}
    arms_by_id = {item["arm_id"]: item for item in agenda.get("arms", [])}
    plan = _read_json(directory / "run_plan.json")
    ledger = _read_jsonl(directory / "delegations.jsonl")

    responses = {item["invocation_id"]: item
                 for item in _read_jsonl(directory / "arm_responses.jsonl")}

    trajectory = directory / "trajectory"
    invocations = {item["invocation_id"]: item
                   for item in _read_jsonl(trajectory / "invocations.jsonl")}
    leads = {item.get("pr_number"): item
             for item in _read_jsonl(trajectory / "leads.jsonl")}

    by_pr: Dict[int, List[Delegation]] = defaultdict(list)
    for row in ledger:
        proposal = proposals.get(row["invocation_id"], {})
        response = responses.get(row["invocation_id"], {})
        traced = invocations.get(row["invocation_id"], {})
        item = Delegation(
            invocation_id=row["invocation_id"],
            arm_id=row["arm_id"],
            work_unit_id=row["work_unit_id"],
            pr_number=row["pr_number"],
            disposition=row.get("disposition", "pruned"),
            reason=row.get("reason") or "",
            site_change_ids=list(proposal.get("site_change_ids", [])),
            mandatory=bool(proposal.get("mandatory")),
            cost_hint=proposal.get("cost_hint"),
            status=row.get("status"),
            budget_tier=row.get("budget_tier"),
            budget_cap=row.get("budget_cap"),
            # `cost` only. See `_LEDGER_POISONED`.
            cost=row.get("cost"),
            candidate_count=row.get("candidate_count"),
            verification_artifact_count=row.get("verification_artifact_count"),
            brief=row.get("brief") or None,
            rendered_prompt_sha256=response.get("rendered_prompt_sha256"),
            delivered_prompt_sha256=row.get("delivered_prompt_sha256"),
            context_calls=list(row.get("context_calls") or []),
            wave=traced.get("wave"),
            tier=traced.get("tier") or row.get("budget_tier"),
            started_at=traced.get("started_at"),
            completed_at=traced.get("completed_at"),
            execution_time=traced.get("execution_time"),
            token_usage=traced.get("token_usage") or {},
            turns=traced.get("turns") or 0,
            tool_calls=traced.get("tool_calls") or {},
            has_transcript=bool(traced.get("has_transcript")),
            claims=[
                {
                    "ordinal": candidate.get("ordinal"),
                    "concern_family": candidate.get("concern_family"),
                    "severity": candidate.get("severity"),
                    "claim": candidate.get("claim"),
                    "requested_change": candidate.get("requested_change"),
                    "primary_change_id": candidate.get("primary_change_id"),
                }
                for candidate in response.get("candidates", [])
            ],
        )
        by_pr[item.pr_number].append(item)

    views: Dict[int, LeadView] = {}
    for pr_number, items in by_pr.items():
        items.sort(key=_delegation_order)
        lead = leads.get(pr_number, {})
        views[pr_number] = LeadView(
            pr_number=pr_number,
            episode_id=next(
                (proposals[item.invocation_id].get("episode_id") for item in items
                 if item.invocation_id in proposals), None
            ),
            delegations=items,
            caps={
                "lead_cost_cap": plan.get("lead_cost_cap"),
                "standard_budget_cap": plan.get("standard_budget_cap"),
                "per_pr_cost_cap": plan.get("per_pr_cost_cap"),
            },
            arms=_arm_rows(items, arms_by_id),
            waves=_wave_rows(items),
            coverage=_coverage(items),
            cost=_pr_cost(items, lead),
            conversation_id=lead.get("conversation_id"),
            started_at=lead.get("started_at"),
            completed_at=lead.get("completed_at"),
            execution_time=lead.get("execution_time"),
            lead_cost=lead.get("cost"),
            lead_turns=lead.get("turns") or 0,
            lead_tool_calls=lead.get("tool_calls") or {},
            lead_token_usage=lead.get("token_usage") or {},
            assessments=list(lead.get("candidate_assessments") or []),
            has_transcript=bool(lead.get("has_transcript")),
        )
    return views


def _delegation_order(item: Delegation) -> tuple:
    """Ran jobs first, in wave then start order; declined jobs after, grouped by arm."""

    ran = item.disposition in _RAN
    return (
        0 if ran else 1,
        item.wave or "",
        item.started_at or "",
        item.arm_id,
        item.work_unit_id,
    )


def _arm_rows(items: Sequence[Delegation], arms_by_id: Dict[str, dict]) -> List[dict]:
    """Per-arm tally for this PR: enumerated, run, declined, what it cost, what it found."""

    rows: Dict[str, dict] = {}
    for item in items:
        row = rows.setdefault(item.arm_id, {
            "arm_id": item.arm_id,
            "kind": (arms_by_id.get(item.arm_id) or {}).get("kind"),
            "mandatory": bool((arms_by_id.get(item.arm_id) or {}).get("mandatory")),
            "enumerated": 0, "ran": 0, "declined": 0,
            "cost": 0.0, "candidates": 0,
        })
        row["enumerated"] += 1
        if item.disposition in _RAN:
            row["ran"] += 1
            row["cost"] += item.cost or 0.0
            row["candidates"] += item.candidate_count or 0
        else:
            row["declined"] += 1
    for row in rows.values():
        row["cost"] = round(row["cost"], 6)
    return sorted(rows.values(), key=lambda row: (not row["mandatory"], row["arm_id"]))


def _wave_rows(items: Sequence[Delegation]) -> List[dict]:
    """The delegation batches, in execution order.

    Wave and tier come from the sidecar's directory walk; without it there is one
    unlabelled group and the ladder still renders, just without wave banding.
    """

    groups: Dict[tuple, dict] = {}
    for item in items:
        if item.disposition not in _RAN:
            continue
        key = (item.wave or "", item.tier or "")
        group = groups.setdefault(key, {
            "wave": item.wave, "tier": item.tier, "jobs": 0, "cost": 0.0,
            "mandatory": 0, "chosen": 0, "started_at": None, "completed_at": None,
            "invocation_ids": [],
        })
        group["jobs"] += 1
        group["cost"] += item.cost or 0.0
        group["mandatory" if item.disposition == "mandatory" else "chosen"] += 1
        group["invocation_ids"].append(item.invocation_id)
        for bound, pick in (("started_at", min), ("completed_at", max)):
            value = getattr(item, bound)
            if value:
                group[bound] = value if group[bound] is None else pick(group[bound], value)
    rows = sorted(groups.values(), key=lambda row: (row["started_at"] or "", row["wave"] or ""))
    for row in rows:
        row["cost"] = round(row["cost"], 6)
    return rows


def _coverage(items: Sequence[Delegation]) -> Dict[str, int]:
    """Per-site arm coverage — the honest form of "where did it choose not to look".

    Not a count of skipped sites: the mandatory floor puts a generalist on every site, so
    that count is always zero. The real decision is which *specialists* were declined where.
    """

    ran: Dict[str, set] = defaultdict(set)
    declined: Dict[str, set] = defaultdict(set)
    for item in items:
        for change_id in item.site_change_ids:
            (ran if item.disposition in _RAN else declined)[change_id].add(item.arm_id)
    sites = set(ran) | set(declined)
    specialists_ran = {
        change_id for change_id in sites if ran.get(change_id, set()) - {"generalist"}
    }
    return {
        "sites": len(sites),
        "generalist_ran": sum(1 for c in sites if "generalist" in ran.get(c, set())),
        "specialist_ran": len(specialists_ran),
        "all_specialists_declined": len(sites) - len(specialists_ran),
        "declined_pairs": sum(len(declined.get(c, ())) for c in sites),
    }


def _pr_cost(items: Sequence[Delegation], lead: dict) -> Dict[str, float]:
    """This PR's spend, split by who spent it."""

    buckets: Dict[str, float] = defaultdict(float)
    for item in items:
        if item.disposition in _RAN and item.cost is not None:
            buckets[item.disposition] += item.cost
    lead_cost = lead.get("cost") or 0.0
    return {
        "lead": round(lead_cost, 6),
        "mandatory": round(buckets.get("mandatory", 0.0), 6),
        "proposed": round(buckets.get("proposed", 0.0), 6),
        "agent_added": round(buckets.get("agent_added", 0.0), 6),
        "total": round(lead_cost + sum(buckets.values()), 6),
    }


def run_cost(directory: Path, views: Dict[int, LeadView]) -> Dict[str, object]:
    """Whole-run spend against what the manifest claims.

    `trace.reconcile` sums the leads plus `proposed` and `agent_added` delegations. The
    mandatory floor executes inside the lead's own nested orchestrator and lands in neither
    term, so the manifest under-reports the held-out run by $14.52 of a $21.06 spend. The
    view reports the split rather than a corrected single number, because the floor being
    two thirds of the bill is the fact worth seeing.
    """

    totals = defaultdict(float)
    for view in views.values():
        for key, value in view.cost.items():
            totals[key] += value
    manifest = _read_json(directory / "run_manifest.json")
    reported = manifest.get("total_cost")
    actual = round(totals.get("total", 0.0), 6)
    return {
        "lead": round(totals.get("lead", 0.0), 6),
        "mandatory": round(totals.get("mandatory", 0.0), 6),
        "proposed": round(totals.get("proposed", 0.0), 6),
        "agent_added": round(totals.get("agent_added", 0.0), 6),
        "actual_total": actual,
        "manifest_total": reported,
        "manifest_understates_by": (
            round(actual - reported, 6) if isinstance(reported, (int, float)) else None
        ),
    }


def load_turns(directory: Path, pr_number: int) -> Dict[str, List[dict]]:
    """This PR's transcripts, keyed by conversation id.

    Sharded per PR by the extractor so a page loads only its own: the held-out run's PR
    33149 draws a mandatory generalist on each of its 108 work units and its shard alone is
    3.9 MB, which no other page should have to carry.
    """

    shard = directory / "trajectory" / "turns" / f"pr-{pr_number}.jsonl"
    grouped: Dict[str, List[dict]] = defaultdict(list)
    for row in _read_jsonl(shard):
        grouped[row["conversation_id"]].append(row)
    for rows in grouped.values():
        rows.sort(key=lambda row: row.get("index", 0))
    return dict(grouped)


def summarize(directory: Path) -> dict:
    """Run-level counts, for the CLI and for tests."""

    views = load_lead_views(directory)
    delegations = [item for view in views.values() for item in view.delegations]
    return {
        "schema_version": DELEGATION_VIEW_VERSION,
        "prs": sorted(views),
        "proposals": len(delegations),
        "ran": sum(1 for item in delegations if item.disposition in _RAN),
        "declined": sum(1 for item in delegations if item.disposition not in _RAN),
        "with_brief": sum(1 for item in delegations if item.brief),
        "with_transcript": sum(1 for item in delegations if item.has_transcript),
        "cost": run_cost(directory, views),
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Summarize a v5 run's routing ledger")
    parser.add_argument("--run", required=True)
    args = parser.parse_args()
    print(json.dumps(summarize(run_dir(args.run)), indent=2))
