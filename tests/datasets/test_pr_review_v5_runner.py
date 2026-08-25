"""The pre-flight path: everything a real run does before it is allowed to spend anything.

The dry run exists to make mistakes cheap, which only works if it exercises the same code a
real run does. It did not: plan sealing was the one step a real run performed that the dry
run skipped, so a schema error in the sealed plan survived every dry run and surfaced only
after the agenda had been built and the prompt pool written.

The specific bug is worth naming, because the shape of it recurs. `io.git_state()` returns
`(commit, "clean"|"dirty"|"unknown")` — a tri-state string, which v4 consistently binds as
`tree_state`. v5 declared the field as `Optional[bool]`, so the provenance stamp both failed
to validate and, had it validated, could not have represented `unknown` at all.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from src.datasets.pr_review_v4.io import git_state
from src.datasets.pr_review_v5.paths import run_dir
from src.datasets.pr_review_v5.runner import V5DatasetConfig, _build_plan, load_run, run
from src.datasets.pr_review_v5.schema import V5RunPlan

RELEASE = Path("inputs/pr_review_v4/releases/dev-medium-0.3.0")
INVENTORY = Path(
    "inputs/pr_review_v4/treatments/systematic-opportunities-v2-medium/derived/"
    "modification_inventory.jsonl"
)
SMOKE_PRS = [33057, 33066, 33098, 33438]


def test_the_plan_accepts_what_git_state_actually_returns():
    """Pinned against the real function, not against a literal. A test asserting the three
    strings would still pass if `git_state` started returning something else."""

    _commit, tree_state = git_state()
    plan = V5RunPlan(
        run_id="v5run:t", run_name="t", routing_mode="lead", agenda_sha256="a" * 64,
        release="rel", prompt_sha256_by_invocation={}, arm_sha256_by_id={},
        model_name="m", scaffold_config_sha256="b" * 64,
        lead_cost_cap=1.0, standard_budget_cap=0.25, per_pr_cost_cap=4.0,
        git_tree_state=tree_state, source_sha256="",
    )
    assert plan.git_tree_state == tree_state


def test_unknown_provenance_is_representable():
    """`unknown` is a real answer — git was unavailable — and is not the same claim as
    `clean`. A boolean field cannot say it, which is why this is not a bool."""

    plan = V5RunPlan(
        run_id="v5run:t", run_name="t", routing_mode="lead", agenda_sha256="a" * 64,
        release="rel", prompt_sha256_by_invocation={}, arm_sha256_by_id={},
        model_name="m", scaffold_config_sha256="b" * 64,
        lead_cost_cap=1.0, standard_budget_cap=0.25, per_pr_cost_cap=4.0,
        git_tree_state="unknown", source_sha256="",
    )
    assert plan.git_tree_state == "unknown"


def test_a_bogus_tree_state_is_rejected():
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        V5RunPlan(
            run_id="v5run:t", run_name="t", routing_mode="lead", agenda_sha256="a" * 64,
            release="rel", prompt_sha256_by_invocation={}, arm_sha256_by_id={},
            model_name="m", scaffold_config_sha256="b" * 64,
            lead_cost_cap=1.0, standard_budget_cap=0.25, per_pr_cost_cap=4.0,
            git_tree_state="probably fine", source_sha256="",
        )


@pytest.fixture(scope="module")
def scaffold():
    from ape.llm_clients.config import LLMConfig
    from ape.scaffolds.ape_agent.config import ApeAgentConfig

    return ApeAgentConfig(llm_config=LLMConfig(model_name="gpt_5.2"))


def _dataset(run_name: str, mode: str = "lead") -> V5DatasetConfig:
    return V5DatasetConfig(
        routing_mode=mode, release=RELEASE, modification_inventory=INVENTORY,
        run_name=run_name, pr_numbers=SMOKE_PRS, dry_run=True,
    )


def test_the_dry_run_seals_a_plan(scaffold, caplog):
    """The regression. If plan construction is ever skipped again, a schema error in it
    survives every dry run and is paid for with a real one."""

    import logging

    dataset = _dataset("pr_review_v5_test_dryrun")
    with caplog.at_level(logging.INFO):
        result = asyncio.run(run(dataset, scaffold, {}, logging.getLogger("t")))
    assert result is None
    assert any("run plan seals" in record.message for record in caplog.records)


def test_the_dry_run_writes_nothing(scaffold):
    """A dry run that left artifacts behind would block the eventual real run under
    `write_once` if any input changed in between."""

    import logging

    name = "pr_review_v5_test_untouched"
    directory = run_dir(name)
    assert not directory.exists(), "stale test run dir — remove it"
    asyncio.run(run(_dataset(name), scaffold, {}, logging.getLogger("t")))
    assert not directory.exists()


def test_the_dry_run_covers_every_routing_mode(scaffold):
    import logging

    for mode in ("fanout", "rules", "lead"):
        result = asyncio.run(run(
            _dataset(f"pr_review_v5_test_{mode}", mode), scaffold, {}, logging.getLogger("t")))
        assert result is None


def test_the_sealed_plan_carries_one_hash_per_enumerated_pair(scaffold):
    """Keyed on the invocation, not the work unit: five arms share a unit, and a unit-keyed
    map would collide — the bug v4's focused arm had to name explicitly."""

    from src.datasets.pr_review_v4.io import load_jsonl
    from src.datasets.pr_review_v4.schema import (
        ChangeGraph, ModificationRecord, RenderedPrompt, ReviewEpisodeInput, ReviewWorkUnit,
    )
    from src.datasets.pr_review_v5.agenda import build_agenda

    units = load_jsonl(RELEASE / "derived/work_units.jsonl", ReviewWorkUnit)
    episodes = [
        item for item in load_jsonl(RELEASE / "input/episodes.jsonl", ReviewEpisodeInput)
        if item.pr_number in set(SMOKE_PRS)
    ]
    agenda, _pool = build_agenda(
        run_name="t", routing_mode="lead", release=RELEASE,
        modification_inventory=INVENTORY, units=units, episodes=episodes,
        graphs=load_jsonl(RELEASE / "derived/change_graphs.jsonl", ChangeGraph),
        release_prompts=load_jsonl(RELEASE / "derived/rendered_prompts.jsonl", RenderedPrompt),
        modifications=load_jsonl(INVENTORY, ModificationRecord),
        pr_numbers=SMOKE_PRS,
    )
    plan = _build_plan(_dataset("t"), scaffold, agenda)
    assert set(plan.prompt_sha256_by_invocation) == {
        item.invocation_id for item in agenda.proposals
    }
    assert plan.source_sha256 and len(plan.source_sha256) == 64


def test_the_shipped_configs_load():
    """A config that does not parse is a run that fails after the agenda is built."""

    for path in (
        Path("configs/pr_review_v5_smoke4.yaml"),
        Path("configs/pr_review_v5_smoke4_rules.yaml"),
    ):
        if not path.is_file():
            pytest.skip(f"{path} not present (configs are gitignored)")
        dataset, _scaffold, _overrides = load_run(path)
        assert dataset.routing_mode in ("fanout", "rules", "lead")
        assert dataset.pr_numbers


def test_a_run_that_cannot_name_its_model_is_refused():
    """A plan stamped with a null model cannot be compared with any other run, so the run is
    refused rather than recorded as anonymous."""

    from ape.scaffolds.ape_agent.config import ApeAgentConfig

    from src.datasets.pr_review_v5.agenda import build_agenda
    from src.datasets.pr_review_v4.io import load_jsonl
    from src.datasets.pr_review_v4.schema import (
        ChangeGraph, ModificationRecord, RenderedPrompt, ReviewEpisodeInput, ReviewWorkUnit,
    )

    episodes = [
        item for item in load_jsonl(RELEASE / "input/episodes.jsonl", ReviewEpisodeInput)
        if item.pr_number in set(SMOKE_PRS)
    ]
    agenda, _pool = build_agenda(
        run_name="t", routing_mode="lead", release=RELEASE,
        modification_inventory=INVENTORY,
        units=load_jsonl(RELEASE / "derived/work_units.jsonl", ReviewWorkUnit),
        episodes=episodes,
        graphs=load_jsonl(RELEASE / "derived/change_graphs.jsonl", ChangeGraph),
        release_prompts=load_jsonl(RELEASE / "derived/rendered_prompts.jsonl", RenderedPrompt),
        modifications=load_jsonl(INVENTORY, ModificationRecord),
        pr_numbers=SMOKE_PRS,
    )
    with pytest.raises(ValueError, match="model_name"):
        _build_plan(_dataset("t"), ApeAgentConfig(), agenda)


def _agenda_and_pool():
    from src.datasets.pr_review_v4.io import load_jsonl
    from src.datasets.pr_review_v4.schema import (
        ChangeGraph, ModificationRecord, RenderedPrompt, ReviewEpisodeInput, ReviewWorkUnit,
    )
    from src.datasets.pr_review_v5.agenda import build_agenda

    episodes = [
        item for item in load_jsonl(RELEASE / "input/episodes.jsonl", ReviewEpisodeInput)
        if item.pr_number in set(SMOKE_PRS)
    ]
    return build_agenda(
        run_name="t", routing_mode="lead", release=RELEASE,
        modification_inventory=INVENTORY,
        units=load_jsonl(RELEASE / "derived/work_units.jsonl", ReviewWorkUnit),
        episodes=episodes,
        graphs=load_jsonl(RELEASE / "derived/change_graphs.jsonl", ChangeGraph),
        release_prompts=load_jsonl(RELEASE / "derived/rendered_prompts.jsonl", RenderedPrompt),
        modifications=load_jsonl(INVENTORY, ModificationRecord),
        pr_numbers=SMOKE_PRS,
    )


def test_a_failed_arm_does_not_become_an_orphan_response():
    """A task that never reached a terminal submission carries no identity. Synthesizing a
    null-keyed response for it made reconciliation see an orphan and refuse to close the
    run — so a single failed generalist job cost the whole manifest."""

    from types import SimpleNamespace

    from src.datasets.pr_review_v5.runner import _responses_from_results

    results = SimpleNamespace(task_results=[
        {"invocation_id": "wu:1#generalist", "arm_id": "generalist", "work_unit_id": "wu:1",
         "pr_number": 1, "success": True, "candidates": [{"claim": "x"}]},
        # the failed one: the orchestrator returns a result with no identity fields
        {"invocation_id": None, "arm_id": None, "work_unit_id": None, "pr_number": None,
         "success": False, "candidates": []},
    ])
    responses = _responses_from_results(results, "rules")
    assert len(responses) == 1
    assert responses[0]["invocation_id"] == "wu:1#generalist"
    assert all(item.get("invocation_id") for item in responses)


def test_specialist_spend_is_counted_in_the_manifest():
    """Three orchestrators spend money in a lead run and none knows about the others: the
    leads, the floor, and every specialist — which runs nested under its lead's attempt and
    so never appears in the lead orchestrator's total. rep3 under-reported by $1.98 on
    $6.27, about a third of the run."""

    from types import SimpleNamespace

    from src.datasets.pr_review_v4.io import canonical_json_bytes, sha256_bytes
    from src.datasets.pr_review_v5.schema import V5RunPlan
    from src.datasets.pr_review_v5.trace import reconcile

    agenda, _pool = _agenda_and_pool()
    records = []
    for index, item in enumerate(agenda.proposals):
        if item.mandatory:
            records.append({"schema_version": "v5-delegation1",
                            "invocation_id": item.invocation_id,
                            "proposal_id": item.proposal_id, "arm_id": item.arm_id,
                            "work_unit_id": item.work_unit_id, "pr_number": item.pr_number,
                            "disposition": "mandatory", "reason": "", "status": "success",
                            # floor rows carry no cost; it arrives as extra_cost
                            "cost": None, "context_calls": []})
        elif index % 7 == 0:
            records.append({"schema_version": "v5-delegation1",
                            "invocation_id": item.invocation_id,
                            "proposal_id": item.proposal_id, "arm_id": item.arm_id,
                            "work_unit_id": item.work_unit_id, "pr_number": item.pr_number,
                            "disposition": "proposed", "reason": "", "status": "success",
                            "cost": 0.10, "context_calls": []})
        else:
            records.append({"schema_version": "v5-delegation1",
                            "invocation_id": item.invocation_id,
                            "proposal_id": item.proposal_id, "arm_id": item.arm_id,
                            "work_unit_id": item.work_unit_id, "pr_number": item.pr_number,
                            "disposition": "pruned", "reason": "r", "status": None,
                            "cost": None, "context_calls": []})
    specialists = sum(1 for r in records if r["disposition"] == "proposed")
    plan = V5RunPlan(
        run_id="v5run:t", run_name="t", routing_mode="lead", agenda_sha256="a" * 64,
        release="rel", prompt_sha256_by_invocation={}, arm_sha256_by_id={},
        model_name="m", scaffold_config_sha256="b" * 64, lead_cost_cap=1.0,
        standard_budget_cap=0.5, per_pr_cost_cap=4.0, source_sha256="",
    )
    plan = plan.model_copy(update={"source_sha256": sha256_bytes(canonical_json_bytes(
        plan.model_dump(mode="json", exclude={"source_sha256"})))})
    manifest = reconcile(
        agenda=agenda, delegations=records, responses=[], plan=plan,
        results=SimpleNamespace(total_cost=1.30, wall_clock_time=180.0),
        issues_total=30, extra_cost=2.97,
    )
    assert manifest.total_cost == pytest.approx(1.30 + 2.97 + 0.10 * specialists)
    # And the floor is not double counted through the ledger.
    assert manifest.total_cost > 4.27
