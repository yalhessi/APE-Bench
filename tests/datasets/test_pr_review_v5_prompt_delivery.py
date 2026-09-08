"""The task's system prompt must actually reach the model.

`create_system_prompt()` is defined on seven task classes across v2, v4 and v5 — the focused
checkers' contracts, the v4 candidate prompts, the v5 lead's routing policy — and until this
was fixed it was called by **no scaffold at all**. `BaseTask` does not even declare it. Every
one of those prompts was silently discarded, and only the user prompt reached the model.

The consequence was invisible in every other test: the prompt text existed, its hash was
sealed into the run plan, and the run completed. It was only detectable by reading a
persisted session and noticing the contract was not in it. So that is what these tests do —
they assert on the delivered artifact, not on the code that builds it.

Concretely, in the rep3 smoke run this meant the lead never saw "cheap is almost never
right" or "two waves beat one" (it used cheap for all 13 jobs and ran one wave), and the
`generality` arm never saw its own contract, so it reported style and naming findings that
its arm gate then rejected.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest


class _Recorder:
    """Stands in for the conversation manager's collaborators."""

    def __init__(self, task):
        self.task = task
        self.logger = SimpleNamespace(warning=lambda *a, **k: None,
                                      info=lambda *a, **k: None)


def _manager_for(task):
    from ape.scaffolds.ape_agent.conversation import ApeAgentConversationManager

    manager = object.__new__(ApeAgentConversationManager)
    manager.task = task
    manager.logger = SimpleNamespace(warning=lambda *a, **k: None,
                                     info=lambda *a, **k: None)
    return manager


def test_a_task_system_prompt_is_collected():
    class Task:
        async def create_system_prompt(self):
            return "ARM CONTRACT: report duplication findings only."

    text = asyncio.run(_manager_for(Task())._task_system_prompt())
    assert text == "ARM CONTRACT: report duplication findings only."


def test_a_task_without_one_contributes_nothing():
    """`BaseTask` does not declare the method; most tasks put everything in the user prompt."""

    assert asyncio.run(_manager_for(SimpleNamespace())._task_system_prompt()) is None


def test_an_empty_prompt_is_treated_as_absent():
    class Task:
        async def create_system_prompt(self):
            return "   \n  "

    assert asyncio.run(_manager_for(Task())._task_system_prompt()) is None


def test_a_failing_prompt_degrades_rather_than_aborts():
    """A missing contract should make the review worse, not kill the run."""

    class Task:
        async def create_system_prompt(self):
            raise RuntimeError("renderer exploded")

    assert asyncio.run(_manager_for(Task())._task_system_prompt()) is None


def test_not_implemented_is_absence_not_an_error():
    class Task:
        async def create_system_prompt(self):
            raise NotImplementedError

    assert asyncio.run(_manager_for(Task())._task_system_prompt()) is None


def test_the_lead_contributes_its_routing_policy():
    """The specific prompt that went missing in rep3."""

    from ape.llm_clients.config import LLMConfig
    from ape.scaffolds.ape_agent.config import ApeAgentConfig
    from ape.tasks.lean_tasks.formal_math.review.lead import (
        ReviewLeadData,
        ReviewLeadTask,
    )

    task = ReviewLeadTask(
        ReviewLeadData(
            task_id="t", episode_id="ep:1", pr_number=1, pr_title="t", pr_description="d",
            diff="d", changed_files=["A.lean"], proposals=[], arm_pool_path="/tmp/x.jsonl",
            target_workspace={"name": "target", "commit_hash": "c" * 40,
                              "repo_url": "https://e.invalid/m.git",
                              "default_target": "Mathlib"}),
        ApeAgentConfig(llm_config=LLMConfig(model_name="gpt_5.2")))
    text = asyncio.run(_manager_for(task)._task_system_prompt())
    assert text
    # The two policies the lead demonstrably never received.
    assert "cheap" in text and "never right" in text
    assert "wave" in text.lower()
    # And the authority boundary, which is the whole design.
    assert "routing" in text.lower()


def test_an_arm_contributes_its_rendered_contract():
    from ape.llm_clients.config import LLMConfig
    from ape.scaffolds.ape_agent.config import ApeAgentConfig
    from ape.tasks.lean_tasks.formal_math.review.arm import (
        ReviewArmData,
        ReviewArmTask,
    )

    task = ReviewArmTask(
        ReviewArmData(
            task_id="t", invocation_id="wu:a#duplication", arm_id="duplication",
            spec_id="duplication", work_unit_id="wu:a", episode_id="ep:1", pr_number=1,
            diff="d", changed_files=["A.lean"], change_ids=["change:a"],
            entity_ids_by_change={"change:a": ["e"]},
            primary_subjects_by_change={"change:a": "Foo.bar"},
            paths_by_change={"change:a": "A.lean"},
            rendered_system_prompt="DUPLICATION CONTRACT: only duplication findings.",
            rendered_user_prompt="u", rendered_prompt_sha256="a" * 64,
            target_workspace={"name": "target", "commit_hash": "c" * 40,
                              "repo_url": "https://e.invalid/m.git",
                              "default_target": "Mathlib"}),
        ApeAgentConfig(llm_config=LLMConfig(model_name="gpt_5.2")))
    text = asyncio.run(_manager_for(task)._task_system_prompt())
    assert text == "DUPLICATION CONTRACT: only duplication findings."


def test_the_scaffold_actually_appends_it():
    """The seam that was broken: building the prompt is not delivering it."""

    import inspect

    from ape.scaffolds.ape_agent import conversation

    source = inspect.getsource(conversation.ApeAgentConversationManager.create_conversation_session)
    assert "_task_system_prompt()" in source
    # Appended, never substituted — the workspace/tool preamble is what the harness needs.
    assert "system_prompt = f\"{system_prompt}" in source
