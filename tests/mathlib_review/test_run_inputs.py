"""A brief or context file a run names is sealed by content, read only as sealed, and inspectable.

Until 2026-10-22 only the path reached the run's identity, inside the resumable scaffold digest:
a brief edited at the same path was read by every later session of a resumed run, and nothing
refused it. These pin the four properties that replace that: an edited file refuses a resume; a
session refuses bytes other than the sealed ones; the same bytes at another path are the same
input; and `report inputs` shows a run's stored first messages, not today's files.
"""

from __future__ import annotations

import json
import logging

import pytest

from src.mathlib_review.io import sha256_bytes
from src.mathlib_review.review import inputs as I
from src.mathlib_review.review import runner as R
from src.mathlib_review.schema.review import V5RunPlan

from pathlib import Path

#: A real solo config, so the dataset is the real model (`.claude/rules`: never a hand-built fake).
SOLO_CONFIG = Path("configs/pr_review_v5_dev_medium_opus55_contract2_claude_sub.yaml")


def _brief(tmp_path, text="You are a reviewer.\n", name="brief.md"):
    path = tmp_path / name
    path.write_text(text)
    return path


def test_the_resolver_reads_digests_and_pins_them(tmp_path):
    brief = _brief(tmp_path)
    resolved = I.resolve_input_files({"system_prompt_file": str(brief), "filing_bar": "request"})
    assert resolved == {"system_prompt_file": {"path": str(brief),
                                               "sha256": sha256_bytes(brief.read_bytes())}}
    assert I.pin_overrides(resolved) == {"system_prompt_sha256": resolved["system_prompt_file"]["sha256"]}
    assert I.sealed_digests(resolved) == {"system_prompt_file": resolved["system_prompt_file"]["sha256"]}
    assert I.resolve_input_files({"system_prompt_file": None}) == {}


def test_a_snapshot_keeps_the_bytes_by_content(tmp_path):
    brief = _brief(tmp_path)
    resolved = I.resolve_input_files({"system_prompt_file": str(brief)})
    snapped = I.snapshot_input_files(resolved, tmp_path / "run")
    snapshot = tmp_path / "run" / I.SNAPSHOT_DIR / f"system_prompt_file-{resolved['system_prompt_file']['sha256'][:16]}.md"
    assert snapped["system_prompt_file"]["snapshot"] == str(snapshot)
    assert snapshot.read_bytes() == brief.read_bytes()
    I.snapshot_input_files(resolved, tmp_path / "run")          # the same bytes again: no error


def test_a_session_refuses_bytes_other_than_the_sealed_ones(tmp_path):
    from ape.tasks.lean_tasks.formal_math.review.solo import (
        SoloReviewConfig, solo_context_block, solo_system_prompt,
    )

    brief = _brief(tmp_path)
    context = tmp_path / "context.jsonl"
    context.write_text(json.dumps({"pr_number": 7, "sections": [{"title": "Model", "text": "x"}]}) + "\n")
    pins = I.pin_overrides(I.resolve_input_files(
        {"system_prompt_file": str(brief), "context_file": str(context)}))
    config = SoloReviewConfig(system_prompt_file=brief, context_file=context, **pins)
    assert solo_system_prompt(config) == brief.read_text()
    assert "## Model" in solo_context_block(config, 7)
    brief.write_text("You are a different reviewer.\n")
    context.write_text(json.dumps({"pr_number": 7, "sections": [{"title": "Other", "text": "y"}]}) + "\n")
    with pytest.raises(ValueError, match="edited after the plan was sealed"):
        solo_system_prompt(config)
    with pytest.raises(ValueError, match="edited after the plan was sealed"):
        solo_context_block(config, 7)
    unpinned = SoloReviewConfig(system_prompt_file=brief)
    assert solo_system_prompt(unpinned) == brief.read_text()     # None reads as before


def _plan(settings):
    return V5RunPlan(run_id="v5run:r", run_name="r", routing_mode="solo", agenda_sha256="a",
                     release="rel", prompt_sha256_by_invocation={}, arm_sha256_by_id={},
                     model_name="m", scaffold_config_sha256="s", lead_cost_cap=0.0,
                     standard_budget_cap=0.0, per_pr_cost_cap=0.0,
                     evaluation_settings=settings, source_sha256="x")


def test_an_edited_brief_refuses_a_resume(tmp_path):
    out = tmp_path / "run"
    R.seal_or_revise_plan(out, _plan({"input_files": {"system_prompt_file": "a" * 64}}),
                          logging.getLogger("t"))
    with pytest.raises(R.PlanChangedSemantically, match="evaluation_settings"):
        R.seal_or_revise_plan(out, _plan({"input_files": {"system_prompt_file": "b" * 64}}),
                              logging.getLogger("t"))


def test_the_same_bytes_at_another_path_are_the_same_input(tmp_path):
    a = _brief(tmp_path, name="a.md")
    b = _brief(tmp_path, name="b.md")
    assert (I.sealed_digests(I.resolve_input_files({"system_prompt_file": str(a)}))
            == I.sealed_digests(I.resolve_input_files({"system_prompt_file": str(b)})))


def test_a_run_sealed_before_inputs_were_recorded_resumes_with_a_revision(tmp_path, caplog):
    out = tmp_path / "run"
    R.seal_or_revise_plan(out, _plan({"pr_finding_limit": 3}), logging.getLogger("t"))
    with caplog.at_level(logging.WARNING):
        path = R.seal_or_revise_plan(
            out, _plan({"pr_finding_limit": 3, "input_files": {"context_file": "c" * 64}}),
            logging.getLogger("t"))
    assert path.name == "run_plan_revision_2.json"
    assert "were not recorded when its plan was sealed" in caplog.text
    # But a recorded setting that changed alongside is still refused.
    with pytest.raises(R.PlanChangedSemantically):
        R.seal_or_revise_plan(
            out, _plan({"pr_finding_limit": 4, "input_files": {"context_file": "c" * 64}}),
            logging.getLogger("t"))


def test_pinning_hands_the_digests_to_the_tasks_before_the_plan_is_built(tmp_path):
    from ape.scaffolds.ape_agent.config import ApeAgentConfig

    brief = _brief(tmp_path)
    scaffold = ApeAgentConfig(task_config_overrides={"system_prompt_file": str(brief)})
    resolved = R.pin_input_files(scaffold)
    assert scaffold.task_config_overrides["system_prompt_sha256"] == resolved["system_prompt_file"]["sha256"]
    dataset, _scaffold, _overrides = R.load_run(SOLO_CONFIG)
    settings = R._settings_with_inputs(dataset, scaffold)
    assert settings["input_files"] == {"system_prompt_file": resolved["system_prompt_file"]["sha256"]}
    # A config that names no file seals exactly what it sealed before.
    assert "input_files" not in R._settings_with_inputs(dataset, ApeAgentConfig())


# --- report inputs ------------------------------------------------------------------------------


def _attempt_tree(tmp_path, scaffold, *, brief_sha=None, overrides=None):
    from datetime import datetime

    from ape.orchestration.models import Attempt, ExecutionStatus, Sample
    from ape.orchestration.persistence import TaskStorage
    import asyncio

    ape_root = tmp_path / "ape"
    root = ape_root / "r1"
    (root).mkdir(parents=True)
    (root / "config.json").write_text(json.dumps({"config": {
        "scaffold_type": scaffold, "claude_model": "claude-opus-5-5" if scaffold == "claude_code" else None,
        "cli_version": "2.1.285" if scaffold == "claude_code" else None,
        "llm_config": {"model_name": None if scaffold == "claude_code" else "local_ds"},
        "task_config_overrides": overrides or {}}}))
    task_dir = root / "tasks" / "gi"
    attempt = task_dir / "samples" / "0" / "attempts" / "attempt_1"
    attempt.mkdir(parents=True)
    now = datetime.now()
    storage = TaskStorage(task_dir, "gi")
    asyncio.run(storage.save_sample(Sample(
        sample_id="s", task_global_index="gi", sample_index=0, status=ExecutionStatus.SUCCESS,
        created_at=now, updated_at=now,
        attempts=[Attempt(attempt_id=1, path=attempt, status=ExecutionStatus.SUCCESS,
                          created_at=now, max_turns=5, cost_limit=None)])))
    (task_dir / "task_outcome.json").write_text(json.dumps(
        {"task_id": "pr5solo_mathlib4_33117_round1_abc"}))
    if scaffold == "ape_agent":
        rows = [{"type": "system", "message": {"content": "SYSTEM TEXT"}},
                {"type": "tool_definitions", "message": {"tools": [
                    {"type": "function", "function": {"name": "file_read", "parameters": {}}}]}},
                {"type": "user", "message": {"content": [{"type": "text", "text": "USER TEXT"}]}}]
        (attempt / "ape_agent_session_1__x.jsonl").write_text(
            "".join(json.dumps(r) + "\n" for r in rows))
    else:
        (attempt / "claude_code_conversation_1__y.jsonl").write_text(
            json.dumps({"type": "user", "message": {"content": "FIRST USER MESSAGE"}}) + "\n")
        (attempt / "claude_code_session.json").write_text(json.dumps({"init": {
            "tools": ["Read", "mcp__core__submit_findings"], "model": "claude-opus-5-5",
            "claude_code_version": "2.1.285", "permissionMode": "dontAsk"}}))
    return ape_root


def test_report_inputs_shows_an_ape_agent_attempts_stored_messages_and_tools(monkeypatch, tmp_path):
    from src.mathlib_review import paths
    from src.mathlib_review.analysis.trace import run_inputs

    brief = _brief(tmp_path)
    sha = sha256_bytes(brief.read_bytes())
    results = tmp_path / "results"
    results.mkdir()
    (results / "run_plan.json").write_text(json.dumps(
        {"evaluation_settings": {"input_files": {"system_prompt_file": sha}}}))
    monkeypatch.setattr(paths, "run_dir", lambda name: results)
    ape_root = _attempt_tree(tmp_path, "ape_agent", overrides={"system_prompt_file": str(brief)})
    out = run_inputs("r1", pr=33117, full=True, ape_root=ape_root)
    (attempt,) = out["attempts"]
    assert attempt["system"] == "SYSTEM TEXT" and attempt["user"] == "USER TEXT"
    assert attempt["tools"] == ["file_read"] and attempt["opaque"] == []
    assert out["input_files"]["system_prompt_file"]["status"] == "unchanged since sealed"
    brief.write_text("edited\n")
    out = run_inputs("r1", ape_root=ape_root)
    assert out["input_files"]["system_prompt_file"]["status"].startswith("changed since sealed")
    assert run_inputs("r1", pr=1, ape_root=ape_root)["attempts"] == []


def test_report_inputs_names_what_the_claude_code_route_does_not_record(monkeypatch, tmp_path):
    from src.mathlib_review import paths
    from src.mathlib_review.analysis.trace import run_inputs

    monkeypatch.setattr(paths, "run_dir", lambda name: tmp_path / "none")
    ape_root = _attempt_tree(tmp_path, "claude_code")
    (attempt,) = run_inputs("r1", ape_root=ape_root)["attempts"]
    assert attempt["user"]["head"] == "FIRST USER MESSAGE" and attempt["system"] is None
    assert attempt["observed"]["model"] == "claude-opus-5-5"
    assert any("system prompt is not recorded" in o for o in attempt["opaque"])
