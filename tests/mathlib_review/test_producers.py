"""The producer seam: facts about a PR, delivered as a packet section, measured alone.

`docs/research/codebase-redesign-2026-10.md` §4.4. These pin the seam with a producer defined
here (a real class with the protocol's members, not a namespace standing in for one): what a
section says and when it says nothing, how a context file is merged without rewriting its base,
how the bench joins facts to asks by change target, and that no producer can read gold.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml

from src.mathlib_review import producers
from src.mathlib_review.analysis import producer_bench


class EveryTarget:
    """One fact at every change target whose declaration name contains `flag`."""

    name = "every_target"
    version = "every_target/1"
    title = "A test section"
    lead = "Facts for the test."

    def facts(self, graph: Dict[str, Any]) -> List[producers.Fact]:
        return [producers.Fact(self.name, t["change_id"], t["path"], 10, t["declaration_name"],
                               f"`{t['declaration_name']}` is flagged.", "P000")
                for t in graph["targets"] if "flag" in t["declaration_name"]]


@pytest.fixture
def every_target(monkeypatch):
    item = EveryTarget()
    monkeypatch.setattr(producers, "producer", lambda name: item)
    monkeypatch.setattr(producer_bench, "producer", lambda name: item)
    return item


def _graph(pr: int, names: List[str]) -> Dict[str, Any]:
    return {
        "pr_number": pr,
        "entities": [{"entity_id": f"e{i}", "span": {"line_start": 10 * (i + 1), "line_end": 10 * (i + 1) + 5}}
                     for i in range(len(names))],
        "changed_ranges": [],
        "targets": [{"change_id": f"change:{pr}:{i}", "path": "Mathlib/X.lean", "declaration_name": n,
                     "reviewed_entity_ids": [f"e{i}"], "changed_range_ids": []}
                    for i, n in enumerate(names)],
    }


def test_a_pr_with_no_facts_gets_no_section(every_target):
    assert producers.section(every_target, []) is None
    held = producers.section(every_target, every_target.facts(_graph(1, ["flag_b", "flag_a"])))
    assert held["title"] == "A test section"
    assert held["text"].startswith("Facts for the test.")
    assert held["text"].count("\n- ") == 2


def test_context_rows_append_to_the_base_and_never_rewrite_it(every_target):
    base = [{"pr_number": 1, "sections": [{"title": "The PR model (pass 0)", "text": "m"}]}]
    before = json.dumps(base)
    rows = producers.context_rows([_graph(1, ["flag"]), _graph(2, ["quiet"]), _graph(3, ["flag"])],
                                  ["every_target"], base)
    assert json.dumps(base) == before
    by_pr = {row["pr_number"]: row for row in rows}
    assert [s["title"] for s in by_pr[1]["sections"]] == ["The PR model (pass 0)", "A test section"]
    assert by_pr[2]["sections"] == []          # nothing found, nothing said
    assert [s["title"] for s in by_pr[3]["sections"]] == ["A test section"]


def test_an_ask_sits_in_the_target_whose_span_holds_its_line():
    graph = _graph(1, ["a", "b"])               # spans 10-15 and 20-25
    assert producer_bench.ask_targets(graph, "Mathlib/X.lean", 12) == {"change:1:0"}
    assert producer_bench.ask_targets(graph, "Mathlib/X.lean", 22) == {"change:1:1"}
    assert producer_bench.ask_targets(graph, "Mathlib/X.lean", 17) == set()
    assert producer_bench.ask_targets(graph, "Mathlib/Y.lean", 12) == set()
    assert producer_bench.ask_targets(graph, None, None) == set()   # a PR-level ask


def test_the_bench_locates_asks_and_counts_control_emission(every_target, tmp_path):
    release = tmp_path / "release"
    (release / "derived").mkdir(parents=True)
    graphs = [_graph(1, ["flag_x", "other"]), _graph(2, ["flag_y"])]
    (release / "derived/change_graphs.jsonl").write_text("".join(json.dumps(g) + "\n" for g in graphs))
    probe = tmp_path / "probe"
    probe.mkdir()
    (probe / "asks.json").write_text(json.dumps({"asks": {"1": ["d0001", "d0002"], "2": []},
                                                 "controls": [2], "families": {}}))
    (probe / "feedback.json").write_text(json.dumps({"rows": [
        {"cid": "d0001", "path": "Mathlib/X.lean", "line": 12, "body": "rename this"},
        {"cid": "d0002", "path": "Mathlib/X.lean", "line": 22, "body": "golf this"}]}))
    spec = tmp_path / "set.yaml"
    spec.write_text(yaml.safe_dump({"name": "t", "release": str(release), "dataset_config": "c.yaml",
                                    "pr_numbers": [1, 2], "feedback": {"prs_of_release": True},
                                    "cid_prefix": "d", "probe_dir": str(probe)}))

    out = producer_bench.bench("every_target", spec)

    assert out["facts"] == 2 and out["facts_per_pr"] == {"1": 1, "2": 1}
    assert out["control_facts"] == {"2": 1}
    assert out["asks"] == 2 and out["asks_located"] == ["d0001"]
    assert out["located"][0]["ask"] == "rename this"


def test_an_unknown_producer_names_the_registry():
    with pytest.raises(KeyError, match="PRODUCERS"):
        producers.producer("no_such_producer")


def test_no_producer_reads_gold_or_a_reading():
    """A fact reaches a reviewer's packet, so nothing a producer imports may know what the
    maintainers asked. The bench is the one place the two meet, and it lives in `analysis/`."""

    forbidden = ("src.mathlib_review.schema.gold", "src.mathlib_review.analysis",
                 "src.mathlib_review.judge")
    crossing = []
    for path in sorted(Path("src/mathlib_review/producers").rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            module = getattr(node, "module", None) if isinstance(node, ast.ImportFrom) else None
            names = [module] if module else [a.name for a in getattr(node, "names", [])] \
                if isinstance(node, ast.Import) else []
            crossing += [(str(path), n) for n in names if n and n.startswith(forbidden)]
    assert crossing == [], crossing
