"""The two solo conditions must differ by their harness and by nothing else.

B (`ape_agent`) and C (`claude_code`) run the same task, so they send byte-identical prompt
text through one submission contract and one anchoring pass. That is the only place commit
43e9d88's byte-identity invariant survives in this experiment -- the whole-PR-vs-work-unit
contrast cannot have it, because the unit of work is the treatment.

The invariant is therefore about the *policy* half of the config, not the whole file: a
scaffold block must differ (only `claude_code` has containment knobs, and only it needs them),
while `dataset:` and `task_config:` must not. An override in either would turn the harness
contrast into a policy contrast without changing anything a reader would notice.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ape.utils.config_loader import load_yaml

PAIRS = [("pr_review_v5_solo_ape_smoke4.yaml", "pr_review_v5_solo_claude_smoke4.yaml"),
         ("pr_review_v5_solo_ape_heldout12.yaml", "pr_review_v5_solo_claude_heldout12.yaml")]

#: Pairs on sets scored by blind matchers rather than the judge, so outside the judge-scope check.
PROBE_PAIRS = [("pr_review_v5_probe_2026_07_08_v1_gpt52_G.yaml",
                "pr_review_v5_probe_2026_07_08_v1_gpt52_G_claude.yaml"),
               ("pr_review_v5_probe_2026_07_08_v1_gpt52_Grc.yaml",
                "pr_review_v5_probe_2026_07_08_v1_gpt52_Grc_claude.yaml")]

#: The same conditions under Codex, held to the same identity.
CODEX_PAIRS = [("pr_review_v5_probe_2026_07_08_v1_gpt52_G.yaml",
                "pr_review_v5_probe_2026_07_08_v1_gpt52_G_codex.yaml"),
               ("pr_review_v5_probe_2026_07_08_v1_gpt52_Grc.yaml",
                "pr_review_v5_probe_2026_07_08_v1_gpt52_Grc_codex.yaml"),
               ("pr_review_v5_probe_2026_07_08_v1_gpt54_Grc.yaml",
                "pr_review_v5_probe_2026_07_08_v1_gpt54_Grc_codex.yaml"),
               ("pr_review_v5_probe_2026_07_08_v1_gpt55_Grc.yaml",
                "pr_review_v5_probe_2026_07_08_v1_gpt55_Grc_codex.yaml")]


@pytest.mark.parametrize("ape_name,claude_name", PAIRS + PROBE_PAIRS + CODEX_PAIRS)
def test_the_two_solo_conditions_differ_only_in_their_scaffold(ape_name, claude_name):
    ape = load_yaml(Path("configs") / ape_name)
    claude = load_yaml(Path("configs") / claude_name)

    assert ape["dataset"] == claude["dataset"], (
        "the harness contrast would also be a policy contrast")
    assert ape.get("task_config") == claude.get("task_config")
    assert ape.get("llm_config") == claude.get("llm_config"), (
        "same model, or the contrast is a model comparison")
    assert ape["scaffold_type"] == "ape_agent"
    assert claude["scaffold_type"] == ("codex" if (ape_name, claude_name) in CODEX_PAIRS else "claude_code")
    assert ape.get("execution") == claude.get("execution"), "the turn limit is part of the condition"


@pytest.mark.parametrize("ape_name,claude_name", PAIRS + PROBE_PAIRS + CODEX_PAIRS)
def test_both_conditions_carry_the_same_pr_set_and_cost_cap(ape_name, claude_name):
    ape = load_yaml(Path("configs") / ape_name)["dataset"]
    claude = load_yaml(Path("configs") / claude_name)["dataset"]

    assert ape["pr_numbers"] == claude["pr_numbers"]
    assert ape["solo_cost_cap"] == claude["solo_cost_cap"]
    if (ape_name, claude_name) in PAIRS:
        assert ape["solo_cost_cap"] == 1.50
    assert ape["routing_mode"] == claude["routing_mode"] == "solo"


@pytest.mark.parametrize("name", [p[1] for p in PAIRS + PROBE_PAIRS])
def test_the_external_condition_is_contained_before_it_is_ever_run(name):
    """Every channel here was verified reachable from a review workspace under the scaffold's
    defaults, which refuse exactly one tool while auto-approving the rest. A config that ships
    without these is a run whose findings cannot be distinguished from the answer key."""

    config = load_yaml(Path("configs") / name)

    assert config["permission_mode"] == "dontAsk", "bypassPermissions makes cwd advisory"
    assert config["setting_sources"] == [], (
        "unset loads this repo's own CLAUDE.md and .claude/rules/, which describe the gold "
        "layout and the retrieval cutoff")
    assert config["strict_mcp_config"] is True
    for tool in ("Bash", "WebFetch", "WebSearch", "Task"):
        assert tool in config["disallowed_tools"], tool
    # The grant says which tools exist, not where they reach: Read takes any absolute path.
    assert config["tools"] == ["Read", "Grep", "Glob", "TodoWrite"]
    assert config["contain_to_workspace"] is True, (
        "without it nothing bounds Read to the workspace and no attempt carries an audit")


@pytest.mark.parametrize("name", [p[0] for p in PAIRS] + [p[1] for p in PAIRS])
def test_the_solo_conditions_scope_the_prs_their_judge_config_scores(name):
    """`judged_pr_scope` refuses a judge config naming a PR the run never reviewed, so a
    condition whose PR set drifts from its judge's is unscoreable -- and a condition scored on
    a different denominator than the one it is compared against measures nothing."""

    config = load_yaml(Path("configs") / name)["dataset"]
    judge_name = ("pr_review_v5_judge.yaml" if "smoke4" in name
                  else "pr_review_v5_medium_heldout_judge.yaml")
    judge = load_yaml(Path("configs") / judge_name)["dataset"]

    scored = set(judge["pr_numbers"]) | set(judge.get("control_pr_numbers") or [])
    assert scored == set(config["pr_numbers"]), sorted(scored ^ set(config["pr_numbers"]))


@pytest.mark.parametrize("name", [p[1] for p in CODEX_PAIRS])
def test_the_codex_condition_has_no_shell_and_only_apes_tools(name):
    """With a shell, Codex reads anything on disk: this repository's gold, the future mathlib clone.
    A read-only sandbox stops writes, not reads, so the shell itself is what goes."""

    config = load_yaml(Path("configs") / name)
    assert {"shell_tool", "unified_exec"} <= set(config["disabled_features"])
    assert {"browser_use", "computer_use", "apps", "plugins", "multi_agent"} <= set(config["disabled_features"])
    assert config["sandbox_mode"] == "read-only"
    assert config["web_search"] is False
    assert config["relayed_builtin_tools"] == ["update_plan"]
    assert config["list_mcp_tools_upfront"] is True
    # Without APE's file tools a shell-less Codex cannot read a file: the first smoke run
    # (pr5_probe0708_gpt52_G_codex_smoke1) was offered no file_read or content_search.
    assert config["use_native_tools"] is True
