"""Composition through the same plan and run commands a researcher invokes."""
import json
import shutil
from pathlib import Path

import pytest
import yaml

from src.mathlib_review.review import cli, runner


def preview(capsys, *options, study="review-matrix"):
    assert cli.main(["plan", "--study", str(study), *options]) == 0
    return json.loads(capsys.readouterr().out)


@pytest.fixture
def catalogue(tmp_path):
    root = tmp_path / "configs"
    for folder in ("designs/composed", "models", "scaffolds", "probe_sets", "studies"):
        shutil.copytree(Path("configs") / folder, root / folder)
    return root


def test_review_matrix_records_each_condition_and_the_frozen_heads(capsys, monkeypatch):
    def no_generation(*args, **kwargs):
        pytest.fail("Planning called the orchestrator")

    monkeypatch.setattr(runner.TaskOrchestrator, "run", no_generation)
    plan = preview(capsys)
    cells = plan["conditions"]
    assert len(cells) == len({tuple(c["choices"].values()) for c in cells}) == 32
    for cell in cells:
        assert cell["samples"] == 1 and cell["episode_count"] == 1
        assert cell["episodes"][0]["reviewed_head_sha"] == "c5474cb4a68a515228b49225b38a2507264f91f7"
        assert cell["episodes"][0]["author"] == "wwylele"
        assert cell["stages"]["reviewer"]["run_config"]["dataset"]["pr_numbers"] == [42184]
        assert all(Path(source["path"]).is_file() for source in cell["sources"].values())
    subset = preview(capsys, "--condition", "design=solo,model=gpt55,scaffold=codex")
    assert subset["conditions"] == [c for c in cells if c["choices"] == {
        "design": "solo", "model": "gpt55", "scaffold": "codex", "cases": "post-42184"}]


def test_a_definition_edit_changes_only_its_cells(capsys, catalogue):
    root = catalogue
    study = root / "studies/review-matrix.yaml"

    def conditions():
        return {tuple(c["choices"].values()): c for c in preview(capsys, study=study)["conditions"]}

    original = conditions()
    trials = [
        ("designs/composed/whole-pr", lambda d: d["stages"]["reviewer"].update(
            brief="Check the names of all new declarations."), 0, "whole-pr", 8,
         lambda c: c["run_config"]["dataset"]["whole_pr_brief"], "Check the names of all new declarations."),
        ("models/gpt55", lambda d: d.update(reasoning_effort="medium"), 1, "gpt55", 8,
         lambda c: c["effective_scaffold"]["llm_config"]["reasoning_effort"], "medium"),
        ("scaffolds/codex", lambda d: d.update(list_mcp_tools_upfront=False), 2, "codex", 16,
         lambda c: c["effective_scaffold"]["list_mcp_tools_upfront"], False)]
    for file, change, axis, choice, count, setting, expected in trials:
        path = root / (file + ".yaml")
        before = path.read_text()
        data = yaml.safe_load(before)
        change(data)
        path.write_text(yaml.safe_dump(data))
        revised = conditions()
        changed = {key for key in original if revised[key] != original[key]}
        assert changed == {key for key in original if key[axis] == choice}
        assert len(changed) == count
        assert all(setting(revised[key]["stages"]["reviewer"]) == expected for key in changed)
        path.write_text(before)
    (root / "designs/composed/fifth.yaml").write_text("extends: whole-pr.yaml\n")
    data = yaml.safe_load(study.read_text())
    data["designs"].append("fifth")
    study.write_text(yaml.safe_dump(data))
    expanded = conditions()
    assert len(expanded) == 40
    assert all(expanded[key] == value for key, value in original.items())


def test_case_selection_keeps_ai_reviews_and_detects_the_october_drift(capsys, catalogue):
    from ape.utils.config_loader import load_yaml

    root = catalogue
    historical = Path("configs/pr_review_v5_dev_medium_gpt55_Grc_contract2.yaml")
    dev = load_yaml(historical)
    (root / "probe_sets/dev-one.yaml").write_text(yaml.safe_dump({
        "extends": "dev_medium_0_3_0.yaml", "pr_numbers": [33066],
        "review_context": dev["task_config"]["context_file"]}))
    file = root / "studies/check.yaml"
    study = {"extends": "review-matrix.yaml", "designs": ["solo"], "models": ["gpt55"],
             "scaffolds": ["ape-agent"], "cases": ["post-42184", "dev-one"]}
    file.write_text(yaml.safe_dump(study))
    post, development = preview(capsys, study=file)["conditions"]
    assert post["episodes"][0]["pr_number"] == 42184 and development["episodes"][0]["pr_number"] == 33066
    post_stage, dev_stage = (c["stages"]["reviewer"] for c in (post, development))
    assert post_stage["brief"] == dev_stage["brief"]
    assert post_stage["effective_task"]["enabled_tools"] == dev_stage["effective_task"]["enabled_tools"]
    study["controls"] = {"post-42184": "configs/pr_review_v5_probe_2026_07_08_v1_gpt55_Grc.yaml",
                         "dev-one": str(historical)}
    file.write_text(yaml.safe_dump(study))
    with pytest.raises(SystemExit):
        cli.main(["run", "--execute", "--study", str(file), "--run-name", "drift"])
    err = capsys.readouterr().err
    assert all(word in err for word in ("dev-one", "gpt55", "solo", "ape-agent", "brief_G2", "file_search"))
    assert not Path(".ape/studies/drift").exists()
    study.update(cases=["postcutoff_2026_07_08_v1"], designs=["whole-pr"], controls={})
    file.write_text(yaml.safe_dump(study))
    cell, = preview(capsys, study=file)["conditions"]
    ai = next(ep for ep in cell["episodes"] if ep["pr_number"] == 41271)
    assert cell["episode_count"] == 10 and ai["ai"] and "label" in ai["ai_evidence"]


def test_two_stage_design_holds_the_upstream_model_fixed_and_refuses_missing_operations(capsys, catalogue):
    root = catalogue
    upstream = {"algorithm": "structured", "operations": ["file_read"], "context_tools": []}
    critic = {"algorithm": "structured_critic", "reads": "selector", "operations": ["file_read"]}
    stages = {"reviewer": critic, "selector": upstream}
    design = root / "designs/composed/critic.yaml"
    design.write_text(yaml.safe_dump({"stages": stages}))
    file = root / "studies/critic.yaml"
    file.write_text(yaml.safe_dump({"extends": "review-matrix.yaml", "designs": ["critic"],
                                    "stage_models": {"selector": "gpt52"}, "models": ["gpt54", "gpt55"],
                                    "scaffolds": ["ape-agent"]}))
    a, b = preview(capsys, study=file)["conditions"]
    assert a["stages"]["selector"] == b["stages"]["selector"]
    assert a["stages"]["selector"]["model"] == "gpt_5.2"
    assert [c["stages"]["reviewer"]["model"] for c in (a, b)] == ["gpt_5.4", "gpt_5.5"]
    assert a["stages"]["reviewer"]["reads"] == "selector"
    for field, value, reason in [("operations", ["no_such_tool"], "no_such_tool"),
                                 ("algorithm", "solo", "no ledger")]:
        design.write_text(yaml.safe_dump({"stages": {**stages, "selector": {**upstream, field: value}}}))
        with pytest.raises(SystemExit):
            cli.main(["run", "--study", str(file), "--run-name", "invalid", "--execute"])
        err = capsys.readouterr().err
        assert all(w in err for w in ("critic", "ape-agent", "gpt54", reason))
    design.write_text(yaml.safe_dump({"stages": stages}))
    file.write_text(file.read_text().replace("gpt55", "opus55"))
    with pytest.raises(SystemExit):
        cli.main(["run", "--study", str(file), "--run-name", "invalid", "--execute"])
    assert "opus55" in capsys.readouterr().err and not Path(".ape/studies/invalid").exists()


def test_ape_and_codex_preserve_the_standalone_october_settings(capsys):
    for choice, suffix in [("ape-agent", ""), ("codex", "_codex")]:
        cell, = preview(capsys, "--condition", f"design=solo,model=gpt55,scaffold={choice}")["conditions"]
        stage = cell["stages"]["reviewer"]
        path = Path("configs") / f"pr_review_v5_probe_2026_07_08_v1_gpt55_Grc{suffix}.yaml"
        ds, scaffold, task = runner.load_run(path)
        planned = stage["effective_scaffold"]
        assert planned["llm_config"] == scaffold.llm_config.model_dump(mode="json")
        assert ds.solo_context_tools == stage["run_config"]["dataset"]["solo_context_tools"]
        assert stage["brief"] == Path(task["system_prompt_file"]).read_text()
        assert stage["effective_task"]["enabled_tools"] == task["enabled_tools"]
        assert planned["execution"]["max_turns"] == scaffold.execution.max_turns
        if choice == "codex":
            for key in ("relayed_builtin_tools", "disabled_features", "sandbox_mode", "use_native_tools"):
                assert planned[key] == getattr(scaffold, key)


def test_search_design_pins_the_history_and_grants_search(capsys, catalogue, monkeypatch):
    from src.mathlib_review.review.reviewers import ExcerptCollection
    from src.mathlib_review.retrieval.precedent_index import PrecedentIndex

    directory = catalogue / "frozen-index"
    directory.mkdir()

    def index(collection, *, prepare):
        assert prepare is False
        (directory / "manifest.json").write_text(json.dumps({"corpus_sha256": collection.sha256}))
        return directory

    monkeypatch.setattr(ExcerptCollection, "index", index)
    monkeypatch.setattr(PrecedentIndex, "shared", lambda *args, **kwargs: None)
    path = catalogue / "studies/search.yaml"
    path.write_text(yaml.safe_dump({"extends": "whole-pr-subscription.yaml", "designs": ["pr-search"]}))
    cell, = preview(capsys, study=path)["conditions"]
    stage = cell["stages"]["reviewer"]
    assert stage["history"]["sha256"] == json.loads((directory / "manifest.json").read_text())["corpus_sha256"]
    inputs, = stage["review_inputs"].values()
    assert "precedent_search" in inputs["mcp"]
