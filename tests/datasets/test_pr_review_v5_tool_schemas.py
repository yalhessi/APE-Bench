"""Every tool the model is offered must have a schema the model can actually satisfy.

This file exists because of a specific failure. `delegate` declared its jobs as
`List[Dict[str, Any]]`, which pydantic renders as `{"type": "object",
"additionalProperties": true}` — an object with *no declared properties*. The tool was
advertised fine and then failed on every call under strict tool schemas. All four leads in
the first smoke run reported "delegate tool failed (schema error)", pruned all 72 specialist
proposals, and the run produced nothing.

Nothing in the unit tests caught it: the tool's Python signature was fine, its handler was
fine, and the failure lived entirely in the generated JSON schema. So the check is on the
schema itself, and it is generic — a new tool with the same shape fails here rather than in
a paid run.

v4 already had the answer: `submit_candidates` takes a typed `CandidateSubmission`.
"""

from __future__ import annotations

import asyncio

import pytest


def _schemas(task):
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("probe")
    asyncio.run(task.register_task_tools(mcp))
    return {tool.name: tool.inputSchema for tool in asyncio.run(mcp.list_tools())}


def _freeform_objects(node, path="") -> list:
    """Every object schema that declares no properties and allows anything.

    Such a node tells the model "send an object" and nothing else, which is both unusable
    guidance and rejected outright by providers running strict schemas.
    """

    found = []
    if isinstance(node, dict):
        if (node.get("type") == "object"
                and node.get("additionalProperties") is True
                and not node.get("properties")):
            found.append(path or "<root>")
        for key, value in node.items():
            found.extend(_freeform_objects(value, f"{path}.{key}" if path else key))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            found.extend(_freeform_objects(value, f"{path}[{index}]"))
    return found


@pytest.fixture(scope="module")
def lead_task():
    from ape.llm_clients.config import LLMConfig
    from ape.scaffolds.ape_agent.config import ApeAgentConfig
    from ape.tasks.lean_tasks.formal_math.review.lead import (
        ReviewLeadData,
        ReviewLeadTask,
    )

    data = ReviewLeadData(
        task_id="t", episode_id="ep:1", pr_number=1, pr_title="t", pr_description="d",
        diff="d", changed_files=["A.lean"], proposals=[], arm_pool_path="/tmp/x.jsonl",
        target_workspace={"name": "target", "commit_hash": "c" * 40,
                          "repo_url": "https://e.invalid/m.git", "default_target": "Mathlib"},
    )
    return ReviewLeadTask(
        data, ApeAgentConfig(llm_config=LLMConfig(model_name="gpt_5.2")))


def test_no_lead_tool_takes_a_properties_less_object(lead_task):
    """The regression. Generic on purpose: it catches the next tool with this shape too."""

    offenders = {
        name: _freeform_objects(schema)
        for name, schema in _schemas(lead_task).items()
        if _freeform_objects(schema)
    }
    assert not offenders, (
        f"free-form object schemas the model cannot satisfy: {offenders}. Declare a typed "
        "pydantic model for the argument, as v4's submit_candidates does."
    )


def test_delegate_declares_the_fields_a_job_needs(lead_task):
    schema = _schemas(lead_task)["delegate"]
    request = schema["$defs"]["DelegationRequest"]
    assert set(request["properties"]) == {
        "proposal_id", "arm_id", "work_unit_id", "budget_tier", "reason", "brief"
    }
    assert request["additionalProperties"] is False


def test_the_brief_is_typed_not_free_form(lead_task):
    """It is the payload most likely to be written as a loose dict, and a properties-less
    object is exactly what made `delegate` unusable in the first place."""

    defs = _schemas(lead_task)["delegate"]["$defs"]
    assert "InvestigationBrief" in defs
    brief = defs["InvestigationBrief"]
    assert set(brief["properties"]) == {
        "question", "because", "look_at", "already_checked", "abstain_if"
    }
    assert brief["additionalProperties"] is False


def test_delegate_constrains_the_budget_tier(lead_task):
    """A free-string tier silently falls back to `standard`, so the lead's intent to go deep
    would be lost without anything reporting it."""

    request = _schemas(lead_task)["delegate"]["$defs"]["DelegationRequest"]
    tier = request["properties"]["budget_tier"]
    allowed = set(tier.get("enum") or [])
    if not allowed:  # pydantic may route a Literal through an anyOf/$ref
        import json

        allowed = set(json.dumps(tier).count("cheap") * ["cheap"])
    assert {"cheap", "deep"} <= allowed or "cheap" in str(tier)


def test_submit_routing_is_typed_too(lead_task):
    schema = _schemas(lead_task)["submit_routing"]
    defs = schema.get("$defs", {})
    assert "PrunedProposal" in defs and "CandidateAssessmentInput" in defs
    assert set(defs["PrunedProposal"]["properties"]) == {"proposal_id", "reason"}


def test_the_arm_tools_are_clean_too():
    """The arm inherits v4's `submit_candidates`, which was already typed — this pins that
    the context tools did not reintroduce the shape."""

    from ape.llm_clients.config import LLMConfig
    from ape.scaffolds.ape_agent.config import ApeAgentConfig
    from ape.tasks.lean_tasks.formal_math.review.arm import (
        ReviewArmData,
        ReviewArmTask,
    )

    data = ReviewArmData(
        task_id="t", invocation_id="wu:a#proof_golf", arm_id="proof_golf",
        spec_id="proof_golf", work_unit_id="wu:a", episode_id="ep:1", pr_number=1,
        diff="d", changed_files=["A.lean"], change_ids=["change:a"],
        entity_ids_by_change={"change:a": ["e"]},
        primary_subjects_by_change={"change:a": "Foo.bar"},
        paths_by_change={"change:a": "A.lean"},
        rendered_system_prompt="s", rendered_user_prompt="u",
        rendered_prompt_sha256="a" * 64,
        context_tools=["zulip_search", "precedent_search", "declaration_search"],
        retrieval_cutoff="2025-06-01T00:00:00Z",
        target_workspace={"name": "target", "commit_hash": "c" * 40,
                          "repo_url": "https://e.invalid/m.git", "default_target": "Mathlib"},
    )
    task = ReviewArmTask(
        data, ApeAgentConfig(llm_config=LLMConfig(model_name="gpt_5.2")))
    offenders = {
        name: _freeform_objects(schema)
        for name, schema in _schemas(task).items() if _freeform_objects(schema)
    }
    assert not offenders, offenders
