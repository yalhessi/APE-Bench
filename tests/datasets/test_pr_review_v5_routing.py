"""The coverage contract: what the lead may not skip, and why.

heldout11 rep2 measured a lead that under-delegated by choice — 30 of 459 specialist
proposals (7%), no PR within half its cost cap or a quarter of its job quota, and
`proof_golf`, `api_reuse` and `generality` at zero across eleven PRs. Two gold obligations
are golf asks on PR 33285, whose title says "golf".

The contract answers that with triggers the PR supplies, not a quota. The tests that matter
most are the ones bounding it: required work is a floor, and a floor that swallows the pool
is a mandate that would erase the routing this system exists to measure.
"""

from __future__ import annotations

from types import SimpleNamespace

from src.datasets.pr_review_v5.components import ReviewComponent
from src.datasets.pr_review_v5.routing import (
    MAX_INTENT_REQUIRED_PER_PR, MAX_REQUIRED_SPECIALISTS_PER_PR, Pair,
    plan_coverage, routing_contract_report,
)


def component(grain, change_ids, *, arms=(), cid=None, pr=1):
    return ReviewComponent(
        component_id=cid or f"component:{grain}:{'-'.join(change_ids)}", grain=grain,
        pr_number=pr, episode_id="e1", change_ids=tuple(change_ids),
        subjects=(), reason=f"a {grain}", suggested_arms=tuple(arms))


def pair(arm, unit, change_ids, *, eligible=True, pr=1):
    return Pair(invocation_id=f"{unit}#{arm}", arm_id=arm, work_unit_id=unit,
                pr_number=pr, change_ids=tuple(change_ids), eligible=eligible)


def test_a_family_requires_one_naming_look_not_one_per_member():
    """Requiring every suggested arm on every member made 388 of 554 proposals mandatory —
    a mandate at the cost of full fanout, not a floor."""

    fam = component("family", ["c1", "c2", "c3"])
    pairs = [pair("naming", f"wu:{i}", [c]) for i, c in enumerate(["c1", "c2", "c3"])]
    decisions = plan_coverage(pairs, {1: [fam]})
    required = [d for d in decisions.values() if d.priority == "required"]
    assert len(required) == 1
    assert required[0].component_grain == "family"


def test_a_stated_intent_covers_every_changed_proof():
    """PR 33285's two gold obligations sit on two different work units, so "one golf look"
    would be the wrong rule here — the ask is over every changed proof."""

    intent = component("pr_intent", ["c1", "c2", "c3"], arms=("proof_golf",))
    pairs = [pair("proof_golf", f"wu:{i}", [c]) for i, c in enumerate(["c1", "c2", "c3"])]
    decisions = plan_coverage(pairs, {1: [intent]})
    assert sum(d.priority == "required" for d in decisions.values()) == 3


def test_a_stated_intent_cannot_become_full_fanout():
    """Whichever bound is tighter wins — here the per-PR specialist budget.

    Required jobs ride the coverage floor, which is exempt from `per_pr_cost_cap`, so the
    only thing standing between a stated intent and an unbounded bill is this ceiling.
    """

    intent = component("pr_intent", [f"c{i}" for i in range(40)], arms=("proof_golf",))
    pairs = [pair("proof_golf", f"wu:{i}", [f"c{i}"]) for i in range(40)]
    decisions = plan_coverage(pairs, {1: [intent]})
    required = sum(d.priority == "required" for d in decisions.values())
    assert required == min(MAX_INTENT_REQUIRED_PER_PR, MAX_REQUIRED_SPECIALISTS_PER_PR)


def test_no_pr_can_mandate_unbounded_specialist_work():
    """The bound is per PR and applies across every trigger, not per trigger."""

    components = [
        component("family", [f"c{i}" for i in range(30)], cid="component:fam"),
        component("file", [f"c{i}" for i in range(30)], cid="component:file"),
        component("pr_intent", [f"c{i}" for i in range(30)], arms=("proof_golf",)),
    ]
    pairs = [pair(arm, f"wu:{i}", [f"c{i}"])
             for i in range(30) for arm in ("naming", "style", "proof_golf")]
    decisions = plan_coverage(pairs, {1: components})
    assert sum(d.priority == "required"
               for d in decisions.values()) <= MAX_REQUIRED_SPECIALISTS_PER_PR


def test_importance_recommends_but_never_requires_on_its_own():
    """Importance says *where* to look, not *for what*. Letting it require would mandate
    every arm on every central change."""

    decisions = plan_coverage(
        [pair("duplication", "wu:1", ["c1"], eligible=False)], {}, {"c1"})
    decision = decisions["wu:1#duplication"]
    assert decision.priority == "recommended"
    assert "central" in decision.reason


def test_a_declaration_site_does_not_require_docs():
    """A `site` grain says "one change", not "a doc change". Requiring `docs` on every
    declaration site fired 51 times across eleven PRs and meant nothing."""

    plain = component("site", ["c1"])
    decisions = plan_coverage([pair("docs", "wu:1", ["c1"])], {1: [plain]})
    assert decisions["wu:1#docs"].priority != "required"


def test_a_changed_module_doc_requires_docs():
    """PR 33305 is seven module-doc changes and nothing else, and its gold ask is an
    over-long line in one of them."""

    doc_site = component("site", ["c1"], arms=("docs", "style"))
    decisions = plan_coverage([pair("docs", "wu:1", ["c1"])], {1: [doc_site]})
    assert decisions["wu:1#docs"].priority == "required"


def test_an_ineligible_pair_with_no_trigger_stays_optional():
    decisions = plan_coverage([pair("naming", "wu:1", ["c1"], eligible=False)], {})
    assert decisions["wu:1#naming"].priority == "optional"


def test_allocation_is_deterministic():
    fam = component("family", ["c1", "c2"])
    pairs = [pair("naming", "wu:a", ["c1"]), pair("naming", "wu:b", ["c2"])]
    first = plan_coverage(pairs, {1: [fam]})
    second = plan_coverage(list(reversed(pairs)), {1: [fam]})
    assert {k: v.priority for k, v in first.items()} == {
        k: v.priority for k, v in second.items()}


def test_every_pair_gets_exactly_one_decision():
    pairs = [pair("naming", "wu:1", ["c1"]), pair("style", "wu:1", ["c1"]),
             pair("docs", "wu:2", ["c2"])]
    decisions = plan_coverage(pairs, {1: [component("family", ["c1", "c2"])]})
    assert set(decisions) == {p.invocation_id for p in pairs}


def test_the_report_separates_the_contract_from_what_the_lead_then_did():
    proposals = [
        SimpleNamespace(arm_id="naming", pr_number=1, routing_priority="required",
                        routing_reason="a family"),
        SimpleNamespace(arm_id="style", pr_number=1, routing_priority="recommended",
                        routing_reason=""),
    ]
    report = routing_contract_report(proposals)
    assert report["by_priority"] == {"recommended": 1, "required": 1}
    assert report["required_by_arm"] == {"naming": 1, "style": 0}


def test_a_doc_heavy_pr_gets_one_docs_look_not_one_per_changed_doc():
    """Claiming per module-doc site put 17 of 27 required `docs` jobs on the two control
    PRs — documentation-heavy PRs where maintainers asked for nothing at all. Most of the
    arm's budget was being spent manufacturing false positives on the PRs that measure
    precision, for a concern that is 3 of 43 gold obligations release-wide."""

    docs_sites = [component("site", [f"c{i}"], arms=("docs", "style"), cid=f"component:s{i}")
                  for i in range(9)]
    pairs = [pair("docs", f"wu:{i}", [f"c{i}"]) for i in range(9)]
    decisions = plan_coverage(pairs, {1: docs_sites})
    assert sum(d.priority == "required" for d in decisions.values()) == 1


def test_a_family_requires_the_arm_whose_scope_is_the_group():
    """Counterpart questions live in name families — a missing dual, a lemma that restates
    its sibling, a generated form spelled by hand — and `family_design` is the only arm whose
    scope is a set and the only one that may submit a coordinated patch. `naming` runs
    alongside it because renaming a pair is the commonest family ask and is a different
    question from whether the group's design is right."""

    fam = component("family", ["c1", "c2"])
    pairs = [pair("family_design", "wu:1", ["c1"]), pair("naming", "wu:1", ["c1"])]
    decisions = plan_coverage(pairs, {1: [fam]})
    assert {d.priority for d in decisions.values()} == {"required"}


def test_an_unrelated_arm_is_not_required_by_a_family():
    """The grain requires the arms whose question it raises, not every arm that could run."""

    fam = component("family", ["c1", "c2"])
    decisions = plan_coverage([pair("proof_golf", "wu:1", ["c1"])], {1: [fam]})
    assert decisions["wu:1#proof_golf"].priority != "required"
