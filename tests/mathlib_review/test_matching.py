"""A matching end to end: a sealed plan that holds the exact inputs, verdicts from Tasks or imported,
one report that carries its identity, and a trace from a cell back to its bytes.

The historical check is the strong one: the post-cutoff probe's committed seal, rebuilt as a
`1-session` plan, must hold byte for byte the inputs its matchers judged (the digests the probe
tests already pin), and its committed `matches.{1,2}.json`, imported, must give the committed numbers.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.mathlib_review.analysis import matching as MA
from src.mathlib_review.analysis import probes
from src.mathlib_review.analysis.trace import trace_matching
from src.mathlib_review.judge import ask_matching as M

SETS = Path("configs/probe_sets")
POST = probes.load_probe_set(SETS / "postcutoff_2026_07_08_v1.yaml")
G52_DIR = Path("results/pr_review_v5/probes/gpt52-postcutoff-2026-09-29")
#: The same digests `test_probes.py` pins for these seals' committed matcher inputs.
INPUT_DIGEST = "6b3086faec3e65c8e393e602d8a60f677f35d5db3cf308ee546002f58168bb55"


def _sources():
    solo = lambda run: probes.Source(kind="solo", run=run)
    return {"G1": solo("probe_postcutoff_gpt52_G_rep1"), "G2": solo("probe_postcutoff_gpt52_G_rep2"),
            "K1": solo("probe_postcutoff_gpt52_K_rep1"), "K2": solo("probe_postcutoff_gpt52_K_rep2"),
            "X1": probes.Source(kind="claude"), "X2": probes.Source(kind="claude")}


@pytest.fixture(scope="module")
def historical(tmp_path_factory):
    out = tmp_path_factory.mktemp("rematch")
    seal_path = G52_DIR / "blinding_SEALED.json"
    plan = MA.plan_matching(POST, name="g52_rematch", seal=json.loads(seal_path.read_text()),
                            seal_path=seal_path, sources=_sources(), out_dir=out,
                            version=M.V1_SESSION, replicates=2)
    return plan, out


def test_a_v1_plan_holds_the_bytes_the_historical_matchers_judged(historical):
    plan, _out = historical
    h = hashlib.sha256()
    files = {}
    for packet in plan.packets:
        for name, content in M.packet_files(packet).items():
            files[name] = json.dumps(content, ensure_ascii=False, indent=1).encode()
    files["session_stats.json"] = json.dumps(plan.session_stats, ensure_ascii=False, indent=1).encode()
    for name in sorted(files):
        h.update(name.encode())
        h.update(files[name])
    assert h.hexdigest() == INPUT_DIGEST
    assert plan.identity.instrument_version == M.V1_SESSION
    assert plan.identity.rubric_sha256 == M.rubric_sha256(M.V1_SESSION, "request_only")
    assert {s.session: s.channel for s in plan.identity.subjects} == {
        "G1": "submitted", "G2": "submitted", "K1": "submitted", "K2": "submitted",
        "X1": "packet", "X2": "packet"}
    assert plan.expected_cells == sum(len(p.asks) * len(p.reviewers) for p in plan.packets)


def test_a_plan_is_written_once_and_an_edited_plan_is_refused(historical, tmp_path):
    plan, out = historical
    assert MA.load_plan(out) == plan
    edited = json.loads((out / MA.PLAN_FILE).read_text())
    edited["packets"][0]["asks"][0]["comment"] = "something else"
    (tmp_path / MA.PLAN_FILE).write_text(json.dumps(edited))
    with pytest.raises(ValueError, match="edited"):
        MA.load_plan(tmp_path)


def test_the_imported_historical_matching_gives_the_committed_numbers(historical):
    plan, out = historical
    MA.import_matches(plan, out, {m: G52_DIR / "match_rematch" / f"matches.{m}.json"
                                  for m in ("1", "2")}, name="g52")
    asks = json.loads(POST.asks_file.read_text())
    report = MA.report_matching(out, families=asks["families"])
    for rep in ("external_import:1", "external_import:2"):
        assert report[rep]["condition_reach"] == pytest.approx(
            {"G": 0.125, "K": 0.0625, "X": 0.46875})
    m = report["measurement"]
    assert m["forensic"] is False and m["identity_sha256"] == plan.identity_sha256
    assert all(r["complete"] for r in m["replicates"].values())
    assert m["replicates"]["external_import:1"]["rows"][0]["locator"]["sha256"]
    scoped = MA.report_matching(out, families=asks["families"],
                                scope={"F1", "F2", "F3", "F4", "F5", "F6", "F7"}, write=False)
    assert scoped["asks"] == 9


def test_an_import_that_misses_a_cell_is_refused(historical, tmp_path):
    plan, _out = historical
    data = json.loads((G52_DIR / "match_rematch" / "matches.1.json").read_text())
    data["asks"] = data["asks"][1:]
    broken = tmp_path / "matches.1.json"
    broken.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="does not cover"):
        MA.import_matches(plan, tmp_path, {"1": broken}, name="broken")
    MA.import_matches(plan, tmp_path / "forensic", {"1": broken}, name="broken",
                      allow_incomplete=True)


def test_a_cell_traces_to_its_label_its_shown_findings_and_both_verdicts(historical):
    plan, out = historical
    reached = None
    table = MA.replicate_tables(plan, MA.verdict_rows(out, plan.plan_id))["external_import:1"]
    for row in table["matches"]["asks"]:
        for label, session in plan.seal[str(row["pr"])].items():
            if row.get(label) == "reached" and session.startswith("X"):
                reached = (row["pr"], row["ask_id"], session, label)
                break
        if reached:
            break
    pr, ask_id, session, label = reached
    trace = trace_matching(out, pr, ask_id, session)
    assert trace["seal"]["label"] == label
    assert trace["shown"]["findings"] == [
        f.model_dump(mode="json") for p in plan.packets if p.pr == pr for f in p.reviewers[label]]
    one = next(c for c in trace["cells"] if c["replicate"] == "external_import:1")
    assert one["value"] == "reached" and one["shown_finding"] is not None
    assert one["verdict_bytes"]["locator"]["file"].endswith("matches.1.json")
    assert trace["subject"]["channel"] == "packet"


# --- A v2 matching run as Tasks ------------------------------------------------------------------


def _v2_plan(tmp_path):
    """Two PRs, two sessions written to findings files (the shape demonstrated-change's probe
    builds by hand), asks given as packets, batches of one PR."""

    found = {"S1": {"7": [{"target": "Mathlib/A.lean:3", "claim": "rename", "requested_change": "x",
                           "severity": "advisory"}], "8": []},
             "S2": {"7": [], "8": [{"target": "Mathlib/B.lean:9", "claim": "golf",
                                    "requested_change": "y", "severity": "advisory"}]}}
    sources = {}
    for session, by_pr in found.items():
        path = tmp_path / f"{session}.json"
        path.write_text(json.dumps(by_pr))
        sources[session] = probes.Source(kind="findings_file", path=str(path))
    asks = {"7": [{"ask_id": "a7", "comment": "rename it"}],
            "8": [{"ask_id": "a8", "comment": "golf it"}]}
    seal = {"7": {"R1": "S1", "R2": "S2"}, "8": {"R1": "S2", "R2": "S1"}}
    seal_path = tmp_path / "seal.json"
    seal_path.write_text(json.dumps(seal))
    return MA.plan_matching(POST, name="v2demo", seal=seal, seal_path=seal_path, sources=sources,
                            out_dir=tmp_path / "m", ask_packets=asks, batch_size=1,
                            question_policy="questions")


def test_a_v2_plan_batches_its_prs_and_binds_declared_findings(tmp_path):
    plan = _v2_plan(tmp_path)
    assert [b.prs for b in plan.batches] == [[7], [8]]
    assert {s.channel for s in plan.identity.subjects} == {"declared"}
    payloads = MA.task_payloads(plan)
    assert [p["batch_id"] for p in payloads] == ["b1", "b2"]
    assert payloads[0]["question_policy"] == "questions"


def test_a_v1_plan_does_not_run(historical):
    plan, _out = historical
    with pytest.raises(ValueError, match="imported"):
        MA.task_payloads(plan)


def test_a_v2_run_reads_every_replicate_back_and_reports(monkeypatch, tmp_path):
    from ape.orchestration import orchestrator as orchestrator_module
    from ape.orchestration.models import Attempt, ExecutionStatus, Sample
    from ape.orchestration.persistence import TaskStorage
    from ape.scaffolds.ape_agent.config import ApeAgentConfig
    from ape.tasks.lean_tasks.formal_math.review.ask_matching import AskMatchingResult

    plan = _v2_plan(tmp_path)
    answers = {("b1", 0): "reached", ("b1", 1): "partial", ("b2", 0): "reached", ("b2", 1): "no"}

    async def fake_run(self, tasks):
        for task in tasks:
            index = task.data.global_index
            storage = TaskStorage(self.tasks_dir / index, index)
            pr = task.data.packets[0].pr
            for n in range(self.config.execution.sample_count):
                value = answers[(task.data.batch_id, n)]
                rows = [{"pr": pr, "ask_id": f"a{pr}", "R1": value, "R1_finding": 0 if pr == 7 and value != "no" else None,
                         "R2": "no", "R2_finding": None, "note": ""}]
                if pr == 8:
                    rows[0].update(R1=value, R1_finding=0 if value != "no" else None)
                result = AskMatchingResult(task_id=task.data.task_id, task_type=task.task_type,
                                           global_index=index, success=True, score=1.0,
                                           plan_id=plan.plan_id, batch_id=task.data.batch_id,
                                           prompt_sha256="p", asks=rows,
                                           unmatched={str(pr): {"R1": 0, "R2": 0}})
                now = datetime.now()
                await storage.save_sample(Sample(
                    sample_id=f"s{n}", task_global_index=index, sample_index=n,
                    status=ExecutionStatus.SUCCESS, created_at=now, updated_at=now,
                    attempts=[Attempt(attempt_id=1, path=storage.task_dir / f"a{n}",
                                      status=ExecutionStatus.SUCCESS, created_at=now,
                                      max_turns=5, cost_limit=None,
                                      result=result.model_dump(mode="json"))]))
        return SimpleNamespace(task_results=[], total_token_usage=None)

    monkeypatch.setattr(orchestrator_module.TaskOrchestrator, "run", fake_run)
    config = ApeAgentConfig(runs_base_dir=tmp_path / "runs")
    rows = asyncio.run(MA.run_matching(plan, tmp_path / "m", config, "v2demo_run", logger=None))
    assert sorted((r.batch_id, r.replicate) for r in rows) == [
        ("b1", "1"), ("b1", "2"), ("b2", "1"), ("b2", "2")]
    assert config.execution.sample_count == 2
    report = MA.report_matching(tmp_path / "m")
    assert report["measurement"]["forensic"] is False
    # Reach is asks reached over every ask in the seal (two): each session reached its one.
    assert report["task:1"]["reach"] == {"S1": 0.5, "S2": 0.5}
    assert report["task:2"]["reach"] == {"S1": 0.0, "S2": 0.0}
    trace = trace_matching(tmp_path / "m", 8, "a8", "S2")
    assert trace["seal"]["label"] == "R1"
    assert trace["original"]["findings"][0]["claim"] == "golf"
    task_cell = next(c for c in trace["cells"] if c["replicate"] == "task:1")
    assert task_cell["verdict_bytes"]["locator"]["run"] == "v2demo_run"


def test_match_without_execute_runs_nothing_and_says_so(monkeypatch, tmp_path, capsys):
    from src.mathlib_review.review import cli

    _v2_plan(tmp_path)
    called = []
    monkeypatch.setattr(MA, "run_matching", lambda *a, **k: called.append(a))
    code = cli.main(["match", "--plan", str(tmp_path / "m"), "--config",
                     "configs/match/ask_match_opus55_claude_sub.yaml", "--run-name", "x"])
    assert code == 0 and called == []
    err = capsys.readouterr().err
    assert "NOTHING RAN" in err and "2 batch task(s) x 2 replicate(s)" in err
    assert "claude-opus-5-5" in err


def test_match_execute_refuses_without_the_subscription_login(monkeypatch, tmp_path):
    from src.mathlib_review.review import cli
    from src.mathlib_review.review.preflight import PreflightError

    _v2_plan(tmp_path)
    monkeypatch.delenv("CLAUDE_CODE_OAUTH_TOKEN", raising=False)
    monkeypatch.setattr(MA, "run_matching", lambda *a, **k: pytest.fail("ran without a login"))
    with pytest.raises(PreflightError, match="CLAUDE_CODE_OAUTH_TOKEN"):
        cli.main(["match", "--plan", str(tmp_path / "m"), "--config",
                  "configs/match/ask_match_opus55_claude_sub.yaml", "--run-name", "x",
                  "--execute"])


JUDGED = Path("results/pr_review_v5/audits/iter-ds41-contract2-keepthink-high-rep1")


@pytest.mark.skipif(not (JUDGED / "semantic_report.json").is_file()
                    or not Path(".ape/runs/pr_review_v5_judge_iter_ds41_contract2_keepthink_high_rep1").is_dir(),
                    reason="needs that judged run and its judge tasks on disk")
def test_a_judged_obligation_traces_to_its_pair_verdict_votes_finding_and_task():
    from src.mathlib_review.analysis.trace import trace_judgment

    report = json.loads((JUDGED / "semantic_report.json").read_text())
    hit = next(r["obligation_id"] for r in report["per_obligation"] if r["issue_status"] == "hit")
    trace = trace_judgment("iter_ds41_contract2_keepthink_high_rep1", hit)
    assert trace["obligation"]["issue_status"] == "hit"
    assert trace["audit"]["measurement"] == "unrecorded (judged before 2026-10-22)"
    pair = next(p for p in trace["pairs"] if p["verdict"] != "(no verdict)"
                and p["verdict"]["issue_match"])
    assert pair["prompt_sha256"] and pair["votes"]["issue_votes"] >= 2
    assert pair["finding"]["claim"]
    assert Path(pair["task"]["task_dir"]).is_dir()


def test_a_matching_leaves_its_row_in_each_source_runs_ledger(monkeypatch, tmp_path, historical):
    from src.mathlib_review import paths
    from src.mathlib_review.io import jsonl_rows

    plan, out = historical
    runs = tmp_path / "runs"
    for name in ("probe_postcutoff_gpt52_G_rep1", "probe_postcutoff_gpt52_K_rep2"):
        (runs / name).mkdir(parents=True)
    monkeypatch.setattr(paths, "run_dir", lambda name: runs / name)
    verdicts = out / MA.VERDICTS_DIR / "import-g52.jsonl"
    written = MA.record_match_stage(plan, out, "matcher_run_x", verdicts)
    assert sorted(written) == ["probe_postcutoff_gpt52_G_rep1", "probe_postcutoff_gpt52_K_rep2"]
    (row,) = jsonl_rows(runs / "probe_postcutoff_gpt52_G_rep1" / "stages.jsonl")
    assert row["stage"] == "match" and row["identity"]["identity_sha256"] == plan.identity_sha256
    assert row["identity"]["channel"] == "submitted"
    assert not any("comment" in str(v) for v in row["produced"].values())
