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


_QUIET = SimpleNamespace(warning=lambda *a, **k: None, info=lambda *a, **k: None)


def _collected(task):
    from ape.scaffolds.prompts import task_system_prompt

    return asyncio.run(task_system_prompt(task, _QUIET))


def test_a_task_system_prompt_is_collected():
    class Task:
        async def create_system_prompt(self):
            return "ARM CONTRACT: report duplication findings only."

    text = _collected(Task())
    assert text == "ARM CONTRACT: report duplication findings only."


def test_a_task_without_one_contributes_nothing():
    """`BaseTask` does not declare the method; most tasks put everything in the user prompt."""

    assert _collected(SimpleNamespace()) is None


def test_an_empty_prompt_is_treated_as_absent():
    class Task:
        async def create_system_prompt(self):
            return "   \n  "

    assert _collected(Task()) is None


def test_a_failing_prompt_degrades_rather_than_aborts():
    """A missing contract should make the review worse, not kill the run."""

    class Task:
        async def create_system_prompt(self):
            raise RuntimeError("renderer exploded")

    assert _collected(Task()) is None


def test_not_implemented_is_absence_not_an_error():
    class Task:
        async def create_system_prompt(self):
            raise NotImplementedError

    assert _collected(Task()) is None


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
    text = _collected(task)
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
    text = _collected(task)
    assert text == "DUPLICATION CONTRACT: only duplication findings."


def test_the_scaffold_actually_appends_it():
    """The seam that was broken: building the prompt is not delivering it."""

    import inspect

    from ape.scaffolds.ape_agent import conversation

    source = inspect.getsource(conversation.ApeAgentConversationManager.create_conversation_session)
    assert "with_task_system_prompt(system_prompt, self.task" in source


def test_appending_keeps_the_preamble_and_the_old_separator():
    """Appended, never substituted, with the separator `ape_agent` always used, so its
    delivered text does not move."""

    from ape.scaffolds.prompts import with_task_system_prompt

    class Task:
        async def create_system_prompt(self):
            return "CONTRACT"

    assert asyncio.run(with_task_system_prompt("PREAMBLE", Task(), _QUIET)) == (
        f"PREAMBLE\n\n{'=' * 80}\n\nCONTRACT")
    assert asyncio.run(with_task_system_prompt("PREAMBLE", SimpleNamespace(), _QUIET)) == "PREAMBLE"


@pytest.mark.parametrize("scaffold_path", [
    "ape.scaffolds.claude_code.scaffold:ClaudeCodeScaffold",
    "ape.scaffolds.codex.scaffold:CodexScaffold",
])
def test_claude_code_and_codex_deliver_the_task_contract(scaffold_path, monkeypatch):
    """Until 2026-10-01 neither did: the solo reviewer ran under them with no brief at all.

    Asserted on the first message the scaffold sends, which is where both put APE's prompt
    (each harness keeps its own system prompt): preamble, then the contract, then the task.
    """

    import importlib

    from ape.scaffolds import prompts

    async def preamble(**_kwargs):
        return "PREAMBLE"

    monkeypatch.setattr(prompts, "build_system_prompt", preamble)

    class Task:
        scratch_workspace = target_workspace = reference_workspaces = None
        config = SimpleNamespace(disabled_features=[], batch_preamble="standard", workspace_environment=True)

        async def create_system_prompt(self):
            return "BRIEF: compare against what Mathlib already has."

        async def create_user_prompt(self):
            return "Review PR 1."

    module_name, class_name = scaffold_path.split(":")
    scaffold = object.__new__(getattr(importlib.import_module(module_name), class_name))
    scaffold.task = Task()
    scaffold.logger = _QUIET

    sent = asyncio.run(scaffold._initial_prompt("/ws"))
    assert sent.count("BRIEF: compare against what Mathlib already has.") == 1
    assert sent.index("PREAMBLE") < sent.index("BRIEF:") < sent.index("Review PR 1.")
    assert "Your current working directory is `/ws`" in sent


def test_codex_is_told_about_shell_paths_only_when_it_has_a_shell(monkeypatch):
    """The paragraph tells the model to call /bin/ls by absolute path; a review disables the shell."""

    from ape.scaffolds import prompts
    from ape.scaffolds.codex.scaffold import CodexScaffold

    async def preamble(**_kwargs):
        return "PREAMBLE"

    monkeypatch.setattr(prompts, "build_system_prompt", preamble)

    def sent(disabled):
        class Task:
            scratch_workspace = target_workspace = reference_workspaces = None
            config = SimpleNamespace(disabled_features=disabled, batch_preamble="standard",
                                     workspace_environment=True)

            async def create_user_prompt(self):
                return "Review PR 1."

        scaffold = object.__new__(CodexScaffold)
        scaffold.task = Task()
        scaffold.logger = _QUIET
        return asyncio.run(scaffold._initial_prompt("/ws"))

    assert "Shell Command Requirements" in sent([])
    assert "Shell Command Requirements" not in sent(["shell_tool", "unified_exec"])


def test_the_plain_preamble_drops_the_imperatives_and_the_default_is_unchanged():
    """`batch_preamble: plain` is the contract condition's preamble: the Claude reviewers gpt is
    compared with never saw "TEXT ALONE ... accomplishes NOTHING", "batch ALL tool calls" or
    "COMPLETED and VALIDATED". The default must render every earlier run's preamble byte for byte,
    and the scaffold must pass its config's choice, not a default."""

    import inspect

    from pydantic import ValidationError

    from ape.llm_clients.config import LLMConfig
    from ape.scaffolds import prompts
    from ape.scaffolds.ape_agent import conversation
    from ape.scaffolds.ape_agent.config import ApeAgentConfig

    standard = asyncio.run(prompts.build_system_prompt(None, None, None))
    plain = asyncio.run(prompts.build_system_prompt(None, None, None, batch_preamble="plain"))
    assert standard.startswith(prompts.BATCH_MODE_SYSTEM_PROMPT)
    for imperative in ("TEXT ALONE", "batch ALL tool calls", "COMPLETED and VALIDATED",
                       "MUST include TOOL CALLS"):
        assert imperative in standard and imperative not in plain, imperative
    assert "submission tool" in plain

    assert ApeAgentConfig(llm_config=LLMConfig(model_name="gpt_5.2")).batch_preamble == "standard"
    assert ApeAgentConfig(llm_config=LLMConfig(model_name="gpt_5.2"),
                          batch_preamble="plain").batch_preamble == "plain"
    with pytest.raises(ValidationError):
        ApeAgentConfig(llm_config=LLMConfig(model_name="gpt_5.2"), batch_preamble="terse")
    source = inspect.getsource(conversation.ApeAgentConversationManager.create_conversation_session)
    assert "batch_preamble=self.config.batch_preamble" in source


def test_workspace_environment_off_drops_the_section_but_never_a_blocked_path_note():
    from ape.scaffolds import prompts
    from ape.tasks.models import WorkspaceInfo

    target = WorkspaceInfo(name="target", commit_hash="c" * 40, repo_url="x",
                           read_only_path_patterns=["**/*"])
    scratch = WorkspaceInfo(name="scratch", commit_hash="c" * 40, repo_url="x")
    standard = asyncio.run(prompts.build_system_prompt(scratch, target, None))
    plain = asyncio.run(prompts.build_system_prompt(scratch, target, None, workspace_environment=False))
    assert "<environment>" in standard and "rapid iteration" in standard
    assert "<environment>" not in plain and "rapid iteration" not in plain
    assert "<WORKSPACE_PATHS>" in plain
    blocked = WorkspaceInfo(name="target", commit_hash="c" * 40, repo_url="x",
                            blocked_path_patterns=["Mathlib/Secret.lean"])
    kept = asyncio.run(prompts.build_system_prompt(scratch, blocked, None, workspace_environment=False))
    assert "Blocked Paths" in kept


@pytest.mark.parametrize("scaffold_path", [
    "ape.scaffolds.claude_code.scaffold:ClaudeCodeScaffold",
    "ape.scaffolds.codex.scaffold:CodexScaffold",
])
def test_the_contract_preamble_knobs_reach_claude_code_and_codex(scaffold_path, monkeypatch):
    """Contract v2 sets `batch_preamble: plain` and `workspace_environment: false`. They were
    APE-Agent's fields, so under Claude Code the config was refused, and the first message kept
    the standard preamble. A harness comparison under "the same prompt" would then not have
    had one. Now on the base config, and passed by every scaffold."""

    import importlib

    from ape.scaffolds import prompts

    seen = {}

    async def preamble(**kwargs):
        seen.update(kwargs)
        return "PREAMBLE"

    monkeypatch.setattr(prompts, "build_system_prompt", preamble)

    class Task:
        scratch_workspace = target_workspace = reference_workspaces = None
        config = SimpleNamespace(batch_preamble="plain", workspace_environment=False,
                                 disabled_features=[])

        async def create_system_prompt(self):
            return "BRIEF"

        async def create_user_prompt(self):
            return "Review PR 1."

    module_name, class_name = scaffold_path.split(":")
    scaffold = object.__new__(getattr(importlib.import_module(module_name), class_name))
    scaffold.task = Task()
    scaffold.logger = _QUIET
    asyncio.run(scaffold._initial_prompt("/ws"))
    assert seen["batch_preamble"] == "plain"
    assert seen["workspace_environment"] is False


def test_every_scaffold_config_accepts_the_contract_preamble_knobs():
    from ape.llm_clients.config import LLMConfig
    from ape.scaffolds.claude_code.config import ClaudeCodeConfig
    from ape.scaffolds.codex.config import CodexConfig

    for config_class in (ClaudeCodeConfig, CodexConfig):
        config = config_class(llm_config=LLMConfig(model_name="gpt_5.2"),
                              batch_preamble="plain", workspace_environment=False)
        assert (config.batch_preamble, config.workspace_environment) == ("plain", False)


def test_system_prompt_role_user_moves_the_system_text_into_the_first_user_message():
    """`system_prompt_role: user` (2026-10-03): no system message, the same text opening the first
    user message with `with_task_system_prompt`'s separator. The default delivers as before."""

    import inspect

    from ape.llm_clients.config import LLMConfig
    from ape.scaffolds.ape_agent import conversation
    from ape.scaffolds.ape_agent.config import ApeAgentConfig
    from ape.scaffolds.prompts import first_user_prompt

    assert first_user_prompt("SYSTEM", "PR") == f"SYSTEM\n\n{'=' * 80}\n\nPR"
    assert first_user_prompt(None, "PR") == "PR" == first_user_prompt("", "PR")
    assert ApeAgentConfig(llm_config=LLMConfig(model_name="gpt_5.2")).system_prompt_role == "system"

    create = inspect.getsource(conversation.ApeAgentConversationManager.create_conversation_session)
    assert 'self.config.system_prompt_role == "user"' in create
    assert "self._system_text_for_first_user = system_prompt" in create
    run = inspect.getsource(conversation.ApeAgentConversationManager.run_conversation)
    assert 'first_user_prompt(getattr(self, "_system_text_for_first_user", None), prompt)' in run
