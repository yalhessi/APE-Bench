"""Freeze actual PacketSession inputs and exercise the two selector paths without a model."""
import json
from pathlib import Path

import pytest

from src.mathlib_review.analysis import sessions
from src.mathlib_review.io import jsonl_bytes, pretty_json_bytes, sha256_file

from src.mathlib_review.analysis import probes
from src.mathlib_review.conventions import selection as study
from src.mathlib_review.retrieval import excerpts
from src.mathlib_review.review.cli import main
from src.mathlib_review.review.study import ReviewStudy
import yaml


def test_history_comparison_accepts_no_selector_and_reuses_older_studies(tmp_path, monkeypatch):
    spec = yaml.safe_load(Path("configs/studies/familiar-conventions.yaml").read_text())
    old_selector = spec.pop("selector")
    spec.update(strategies=["solo", "history"], output=str(tmp_path / "out"))
    config = tmp_path / "study.yaml"
    seal = tmp_path / "out/study.json"
    # History indexing has its own tests. Keep the CLI, case validation and on-disk pin real.
    monkeypatch.setattr(excerpts, "prepare", lambda *args: None)

    def prepare():
        config.write_text(yaml.safe_dump(spec))
        return main(["study", "prepare", str(config)])

    assert prepare() == 0
    definition = json.loads(seal.read_bytes())
    assert "selector" not in definition
    spec["selector"] = "unused.yaml"
    assert prepare() == 0
    assert not (seal.parent / "conventions").exists()

    old_bytes = pretty_json_bytes({**definition, "selector": old_selector})
    seal.write_bytes(old_bytes)
    assert prepare() == 0
    assert seal.read_bytes() == old_bytes
    spec["name"] += "-different-study"
    with pytest.raises(SystemExit, match="2"):
        prepare()
    assert seal.read_bytes() == old_bytes


@pytest.mark.parametrize("strategy", ["automatic", "exact"])
def test_selection_requires_a_selector_before_execution(tmp_path, capsys, strategy):
    spec = yaml.safe_load(Path("configs/studies/familiar-conventions.yaml").read_text())
    del spec["selector"]
    spec.update(strategies=["solo", strategy], output=str(tmp_path / "out"))
    config = tmp_path / "study.yaml"
    config.write_text(yaml.safe_dump(spec))
    with pytest.raises(SystemExit, match="2"):
        main(["study", "prepare", str(config)])
    assert "Supply a selector config" in capsys.readouterr().err
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("selectors", [("automatic", "exact"), ("automatic",), ("exact",)])
def test_source_only_and_separate_selectors(tmp_path, monkeypatch, selectors):
    source = tmp_path / "history/excerpts.jsonl"
    source.parent.mkdir()
    source.write_bytes(jsonl_bytes([{"comment_id": 123, "pr_number": 42, "diff_hunk": "+lemma foo",
                                     "body": "Use the theorem with weaker assumptions."}]))
    (source.parent / "manifest.json").write_bytes(pretty_json_bytes({"corpus_sha256": sha256_file(source)}))
    out = tmp_path / "private"
    spec = ReviewStudy.model_validate(yaml.safe_load(Path("configs/studies/familiar-conventions.yaml").read_text()))
    inputs = {"reference": probes.load_probe_set(spec.reference), "heads": spec.heads, "config": spec.selector,
              "selectors": selectors}
    stages = []

    def local_observations(plan, directory, config, run):
        stage = directory.parent.name
        stages.append(stage)
        rows = []
        for packet in plan.packets:
            if stage == "extract":
                assert set(packet.files) == {"instructions.md", "excerpts.jsonl"}
                value = {"conventions": [{"principle": "Use weaker assumptions when they suffice.",
                                          "evidence": [{"comment_id": 123, "quote": "weaker assumptions"}]}],
                         "omitted_ids": []}
            elif stage == "merge":
                assert set(packet.files) == {"instructions.md", "drafts.jsonl"}
                value = []
            elif stage == "automatic":
                assert set(packet.files) == {"instructions.md", "catalogue.jsonl", "pr.json"}
                assert set(json.loads(packet.files["catalogue.jsonl"])) == {"id", "principle"}
                assert isinstance(json.loads(packet.files["pr.json"])["title"], str)
                value = [{"id": "C0001", "where": "an assumption", "why": "test"}]
            else:
                assert stage == "exact"
                assert set(packet.files) == {"instructions.md", "catalogue.jsonl", "pr.json", "asks.json"}
                value = [{"ask_id": ask["ask_id"], "ids": [], "why": "uncovered"}
                         for ask in json.loads(packet.files["asks.json"])]
            attempt = tmp_path / run / packet.packet_id
            attempt.mkdir(parents=True)
            (attempt / "containment_audit.json").write_text('{"clean":true}')
            (attempt / "claude_code_session.json").write_text('{"usage":{"total_tokens":42}}')
            rows.append(sessions._store(directory, plan, f"task-{run}", packet.packet_id, "1",
                                        "task", {"attempt": str(attempt)}, {}, {"answer.json": json.dumps(value)}))
        sessions._write_index(directory, f"task-{run}", rows)

    monkeypatch.setattr(study, "execute_packets", local_observations)
    assert study.prepare(out, source, **inputs) is None
    assert stages == []
    with monkeypatch.context() as changed:
        changed.setattr(study, "AUTO", "Use a different selector contract.")
        with pytest.raises(FileExistsError, match="protocol.json"):
            study.prepare(out, source, **inputs, execute=True)
    assert stages == []
    actual = study.prepare(out, source, **inputs, execute=True)
    assert stages == ["extract", "merge", *selectors]
    if "automatic" in selectors:
        assert actual["automatic"] == {"prs": {"41930": ["C0001"], "42184": ["C0001"]}}
    if "exact" in selectors:
        assert actual["exact"] == {"prs": {"41930": [], "42184": []}}
    assert study.prepare(out, source, **inputs) == actual
    assert len(stages) == 2 + len(selectors)
    (out / f"{selectors[0]}.json").write_text("{}")
    with pytest.raises(FileExistsError, match=selectors[0]):
        study.prepare(out, source, **inputs)


def test_reject_fabricated_citation_in_anotherwise_valid_rule():
    batches = {"batch": [{"comment_id": 123, "body": "prefer A", "diff_hunk": "+lemma foo"}]}
    rule = {"principle": "Prefer A.", "evidence": [{"comment_id": 123, "quote": "prefer B"}]}
    with pytest.raises(ValueError, match="locate quote"):
        study.build_drafts(batches, {"batch": {"conventions": [rule], "omitted_ids": []}})
    with pytest.raises(ValueError, match="account for every excerpt"):
        study.build_drafts(batches, {"batch": {"conventions": [], "omitted_ids": []}})


def test_scoped_rules_survive_consolidation_and_missing_ask_is_refused():
    drafts = {f"D{i}": {"principle": f"rule {i}", "source_ids": [i]} for i in range(3)}
    result = study.consolidate(drafts, [["D1", "D0"]])
    assert [row["principle"] for row in result] == ["rule 1", "rule 2"]
    assert result[0]["source_ids"] == [0, 1]
    with pytest.raises(ValueError, match="overlapping"):
        study.consolidate(drafts, [["D0", "D1"], ["D1", "D2"]])
    with pytest.raises(ValueError, match="missing or repeats"):
        study.select([], {"C0001"}, ask_ids=["ask"])
