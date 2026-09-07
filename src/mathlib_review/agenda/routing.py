"""What the lead may not skip, and why — derived from the PR, never from a quota.

heldout11 rep2 measured a lead that under-delegated by choice, not by constraint: 30 of 459
specialist proposals ran (7%), no PR came within half its cost cap (max $0.80 of $1.50) or a
quarter of its job quota (max 6 of 25), and three arms — `proof_golf`, `api_reuse`,
`generality` — ran **zero times across eleven PRs**. Two of the twenty gold obligations are
proof-golf asks on PR 33285, whose title says "golf", sitting on work units where
`proof_golf` was proposed and pruned.

A per-arm quota would fix that case and be wrong in general: it spends the same on an arm
whether or not the PR gives any reason to run it. What the coverage contract does instead is
require work the PR itself asks for:

* **the PR says what it is doing** — a stated golf intent puts every changed proof in scope
  for `proof_golf`, a stated rename puts every changed declaration in scope for `naming`;
* **the change has a shape a grain owns** — a dualised family gets a family-level look, a
  module doc gets `docs`, a multi-change file gets the namespace/placement check that no
  declaration in it owns;
* **the change is important** — measured centrality within the PR, and exposure in the
  library outside it.

Everything else stays `recommended` or `optional`, and the lead keeps full authority there.
The contract is a floor under coverage, not a replacement for routing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from src.mathlib_review.agenda.components import ReviewComponent

#: A required rule fires only when the PR supplies the trigger. Each entry is
#: (grain, arms it makes required, why) and is checked against the components actually built.
#: Exactly one arm per grain is *required*; the grain's other suggested arms stay
#: recommended. Requiring every suggested arm on every member of a component made 388 of 554
#: proposals mandatory — 70% — which is not a floor under coverage but a mandate replacing
#: the routing this system exists to measure, at roughly the cost of full fanout.
_GRAIN_REQUIREMENTS: Dict[str, Tuple[Tuple[str, ...], str]] = {
    "migration": (("naming",), "the PR describes a rename, deprecation or migration"),
    # A family is the grain a per-declaration arm cannot see: renames, dualisations and
    # missing counterparts are one decision about several declarations.
    # `family_design` is the arm whose *scope* is the group, and it owns both shapes a
    # group's defect takes — a generated form written by hand (`duplication`) and a missing
    # counterpart or hardcoded shared parameter (`generalization`). It is also the only arm
    # besides `migration_consistency` that may submit a coordinated patch, which is what the
    # five obligations in this class need to be resolvable rather than merely noticed.
    # `naming` stays alongside it because renaming a pair is the commonest family ask and is
    # a different question from whether the group's design is right.
    "family": (("family_design", "naming"), "these declarations are one API family"),
    # Namespace placement, section structure and the module docstring belong to the file.
    "file": (("style",), "namespace placement and module docs are properties of the file"),
    # A changed module doc is a site whose only reviewer is `docs` — but ONE look per PR,
    # not one per changed module doc. Claiming per site put 17 of 27 required `docs` jobs on
    # the two control PRs, which happen to be documentation-heavy and where maintainers asked
    # for nothing at all: most of the budget for this arm was being spent manufacturing false
    # positives on the PRs that measure precision. Documentation is also 3 of 43 gold
    # obligations release-wide, so a large share of required work was doubly unwarranted.
    "site": (("docs",), "this PR changes module documentation"),
}

#: `pr_intent` is the exception to once-per-component. When a PR says it is a golf PR, the
#: ask is over *every changed proof* — that is the content of the claim, and PR 33285's two
#: gold obligations sit on two different work units. Bounded per PR so a large PR cannot
#: turn a stated intent into full fanout.
MAX_INTENT_REQUIRED_PER_PR = 12

#: A hard bound on contract-mandated specialist work per PR.
#:
#: Required jobs ride the coverage floor, and the floor is deliberately exempt from
#: `per_pr_cost_cap` — charging coverage to the routing allowance once left PR 33149 with a
#: $10.05 floor against a $1.50 cap and therefore zero specialists. That exemption was safe
#: while the floor was only the generalist pass. Making specialists required puts unbounded
#: work inside it, so the bound moves here, where it is visible and per PR rather than
#: discovered on the invoice.
MAX_REQUIRED_SPECIALISTS_PER_PR = 10

#: How much measured importance is enough to require a look on its own, independent of any
#: stated intent. Deliberately a rank rather than an absolute: the point is "the most
#: important changes in this PR", which is comparable across PRs of very different sizes.
DEFAULT_CENTRAL_RANK = 3


@dataclass(frozen=True)
class RoutingDecision:
    """What the contract says about one (arm, work unit) pair."""

    priority: str
    reason: str
    component_id: Optional[str] = None
    component_grain: Optional[str] = None


def _components_for(unit_change_ids: Set[str],
                    components: Sequence[ReviewComponent]) -> List[ReviewComponent]:
    """Components this work unit participates in, finest grain first.

    Overlap, not containment: a work unit is a review target and a component is a reason to
    look at it, and a unit that holds half a family is still doing family work.
    """

    hits = [c for c in components if unit_change_ids & set(c.change_ids)]
    return sorted(hits, key=lambda c: (len(c.change_ids), c.component_id))


@dataclass(frozen=True)
class Pair:
    """One (arm, work unit) pair the agenda could schedule."""

    invocation_id: str
    arm_id: str
    work_unit_id: str
    pr_number: int
    change_ids: Tuple[str, ...]
    eligible: bool


def plan_coverage(
    pairs: Sequence[Pair],
    components_by_pr: Dict[int, Sequence[ReviewComponent]],
    central_change_ids: Set[str] = frozenset(),
) -> Dict[str, RoutingDecision]:
    """Decide the whole contract at once, because "required" is a budget, not a predicate.

    Deciding pair-by-pair cannot express "this family needs *a* naming look" — only "every
    member of this family needs a naming look", which is how 70% of the pool became
    mandatory. Allocation is therefore global: each (component, required arm) claims exactly
    one pair, and everything else falls back to the lead's discretion.

    `central_change_ids` is the importance input — what the PR is built around and what it
    touches that the library leans on. It raises a pair to `recommended`; it never requires
    on its own, because importance says *where* to look and not *for what*.
    """

    decisions: Dict[str, RoutingDecision] = {}
    claimed: Set[Tuple[str, str]] = set()
    intent_required: Dict[int, int] = {}
    required_per_pr: Dict[int, int] = {}

    def _take(pr_number: int) -> bool:
        """Claim one unit of this PR's required-specialist budget, if any is left."""

        if required_per_pr.get(pr_number, 0) >= MAX_REQUIRED_SPECIALISTS_PER_PR:
            return False
        required_per_pr[pr_number] = required_per_pr.get(pr_number, 0) + 1
        return True

    # Deterministic: the same agenda must produce the same contract every time.
    for pair in sorted(pairs, key=lambda p: (p.pr_number, p.work_unit_id, p.arm_id)):
        change_ids = set(pair.change_ids)
        chosen: Optional[RoutingDecision] = None
        for component in _components_for(change_ids, components_by_pr.get(pair.pr_number, [])):
            if component.grain == "pr_intent":
                # The stated intent applies to every changed proof, not to one of them.
                if (pair.arm_id in set(component.suggested_arms)
                        and intent_required.get(pair.pr_number, 0)
                        < MAX_INTENT_REQUIRED_PER_PR
                        and _take(pair.pr_number)):
                    intent_required[pair.pr_number] = (
                        intent_required.get(pair.pr_number, 0) + 1)
                    chosen = RoutingDecision(
                        "required", "the PR states this is what it is doing (pr_intent)",
                        component.component_id, component.grain)
                    break
                continue
            arms, why = _GRAIN_REQUIREMENTS.get(component.grain, ((), ""))
            required_arms = set(arms)
            if component.grain == "site":
                # Only the sites that carry a suggested arm — in practice `module_doc`.
                # Requiring `docs` on every declaration site fired 51 times on eleven PRs
                # and meant nothing: a site grain says "one change", not "a doc change".
                required_arms &= set(component.suggested_arms)
            key = (
                # Module-doc sites share one claim across the whole PR; every other grain
                # claims per component.
                (pair.pr_number, "module_doc") if component.grain == "site"
                else component.component_id,
                pair.arm_id,
            )
            if (pair.arm_id in required_arms and key not in claimed
                    and _take(pair.pr_number)):
                claimed.add(key)
                chosen = RoutingDecision(
                    "required", f"{why} ({component.grain})",
                    component.component_id, component.grain)
                break
        if chosen is None:
            central = bool(change_ids & central_change_ids)
            chosen = RoutingDecision(
                priority="recommended" if (pair.eligible or central) else "optional",
                reason=(
                    "this change is central to the PR or widely used in the library"
                    if central else
                    "the deterministic rule finds this arm applicable" if pair.eligible
                    else "renderable, but no rule selected it"),
            )
        decisions[pair.invocation_id] = chosen
    return decisions


def central_changes(
    census_rows: Sequence[Any],
    centrality_by_change: Dict[str, int],
    *,
    top_rank: int = DEFAULT_CENTRAL_RANK,
    exposure_by_change: Optional[Dict[str, int]] = None,
    exposure_floor: int = 5,
) -> Set[str]:
    """The changes important enough to require a look, by two independent measures.

    * **PR centrality** — the top-ranked census rows, plus any change the rest of the diff
      depends on. If the PR is built around it, reviewing it badly costs more than reviewing
      a leaf badly.
    * **Library exposure** — a change to a declaration many other modules reference. This is
      the "someone else's widely-used code, touched in passing" case, and it is the half a
      PR-local measure cannot see.

    Exposure is optional: when no index is available the caller passes nothing and the rule
    degrades to PR centrality alone rather than silently treating absent data as zero.
    """

    central: Set[str] = set()
    for row in census_rows:
        if getattr(row, "rank", 1 << 30) <= top_rank:
            central.update(getattr(row, "change_ids", ()) or ())
    central.update(cid for cid, score in centrality_by_change.items() if score >= 2)
    if exposure_by_change:
        central.update(cid for cid, reach in exposure_by_change.items()
                       if reach >= exposure_floor)
    return central


def routing_contract_report(proposals: Sequence[Any]) -> Dict[str, Any]:
    """What the contract obliges, before the lead sees any of it.

    Read alongside `trace.routing_report`, which says what the lead then did. A contract that
    requires nothing and a lead that prunes everything look identical in the outcome and are
    completely different problems.
    """

    by_priority: Dict[str, int] = {}
    by_arm: Dict[str, Dict[str, int]] = {}
    by_pr: Dict[int, int] = {}
    reasons: Dict[str, int] = {}
    for proposal in proposals:
        priority = getattr(proposal, "routing_priority", "optional")
        by_priority[priority] = by_priority.get(priority, 0) + 1
        arm = getattr(proposal, "arm_id", "?")
        by_arm.setdefault(arm, {}).setdefault(priority, 0)
        by_arm[arm][priority] += 1
        if priority == "required":
            pr = getattr(proposal, "pr_number", 0)
            by_pr[pr] = by_pr.get(pr, 0) + 1
            reason = getattr(proposal, "routing_reason", "") or "(none)"
            reasons[reason] = reasons.get(reason, 0) + 1
    return {
        "by_priority": dict(sorted(by_priority.items())),
        "required_by_arm": {
            arm: counts.get("required", 0) for arm, counts in sorted(by_arm.items())
        },
        "required_by_pr": dict(sorted(by_pr.items())),
        "required_reasons": dict(sorted(reasons.items(), key=lambda kv: -kv[1])),
        # A PR the contract requires nothing on is one where coverage is entirely the lead's
        # judgment. That may be right; it should not be invisible.
        "prs_with_no_required_work": [],
    }
