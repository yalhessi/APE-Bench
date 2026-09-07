"""The trajectory sidecar and the routing view must not repeat the run's own accounting bugs.

Three numbers in a finished v5 run are wrong, and all three are the sort a viewer would
happily render without noticing:

* `delegations.jsonl::token_usage` is the *tier's* aggregate copied onto every job in it.
  Summing it over the held-out run gives $1,141.84 against a real $19.17 — a 54x inflation
  that still looks like a plausible dollar figure on a page.
* `delegations.jsonl::wall_seconds` is likewise per-tier: 239 rows carry 29 distinct values,
  one repeated 108 times. Gantt bars drawn from it would all be the same length and all
  wrong.
* `run_manifest.json::total_cost` omits the mandatory floor, under-reporting the held-out
  run by $14.52 of $21.06.

So these tests pin the corrected figures rather than trusting the artifacts, and assert the
view reads `cost` and the sidecar rather than the poisoned fields. If someone fixes the
pipeline upstream, the pinned pairs fail loudly instead of the page silently changing.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.mathlib_review.analysis import delegation_view
from src.mathlib_review.analysis import trajectory
from src.mathlib_review.paths import run_dir

RUN = "pr_review_v5_lead_medium_heldout_rep1"
DIRECTORY = run_dir(RUN)
APE = trajectory.DEFAULT_APE_ROOT / RUN

requires_run = pytest.mark.skipif(
    not (DIRECTORY / "delegations.jsonl").is_file(),
    reason="held-out v5 run not present",
)
requires_sidecar = pytest.mark.skipif(
    not (DIRECTORY / "trajectory" / "invocations.jsonl").is_file(),
    reason="trajectory sidecar not extracted",
)


# --- unit ---------------------------------------------------------------------------

def test_poisoned_ledger_fields_are_named_and_unused():
    """The prohibition has to be greppable, or it decays into a comment nobody reads."""

    assert delegation_view._LEDGER_POISONED == ("token_usage", "wall_seconds")
    source = Path(delegation_view.__file__).read_text()
    body = source.split('@dataclass\nclass Delegation', 1)[1]
    # The only mentions may be the constant and the docstrings that explain it.
    assert 'row.get("token_usage")' not in body
    assert 'row.get("wall_seconds")' not in body
    assert 'row.get("cost")' in body


def test_wave_and_tier_come_from_the_path():
    parts = Path("x/tasks/1/samples/0/attempts/a/subtasks/wave2/cheap/b/tasks/2/task_result.json")
    assert trajectory._wave_and_tier(parts) == ("wave2", "cheap")
    assert trajectory._wave_and_tier(Path("x/tasks/1/task_result.json")) == (None, None)


def test_turn_extraction_truncates_results_but_never_the_model(tmp_path):
    session = tmp_path / "ape_agent_session_1.jsonl"
    long_result = "R" * 9000
    long_text = "T" * 9000
    session.write_text("\n".join(json.dumps(row) for row in [
        {"type": "system", "message": {"content": []}},
        {"type": "assistant", "timestamp": "t1", "message": {"content": [
            {"type": "text", "text": long_text},
            {"type": "tool_use", "name": "file_read", "id": "c1", "input": {"path": "a.lean"}},
        ]}},
        {"type": "user", "timestamp": "t2", "message": {"content": [
            {"type": "tool_result", "name": "file_read", "tool_use_id": "c1",
             "result_content": long_result},
        ]}},
    ]))
    turns = trajectory._read_turns(session, "conv", cap=100)
    assert [turn.role for turn in turns] == ["assistant", "user"]
    text = turns[0].items[0]
    assert text["t"] == "text" and text["v"] == long_text, "assistant text must be verbatim"
    result = turns[1].items[0]
    assert len(result["v"]) == 100 and result["bytes"] == 9000, "result must report its true size"


def test_missing_ape_root_degrades(tmp_path):
    extracted = trajectory.extract("nope", ape_root=tmp_path)
    assert extracted["present"] is False
    assert extracted["invocations"] == [] and extracted["leads"] == []


def test_is_v5_run_is_structural(tmp_path):
    assert not delegation_view.is_v5_run(tmp_path)
    (tmp_path / "agenda.json").write_text("{}")
    assert not delegation_view.is_v5_run(tmp_path)
    (tmp_path / "delegations.jsonl").write_text("")
    assert delegation_view.is_v5_run(tmp_path)


# --- against the real run -------------------------------------------------------------

@requires_run
@requires_sidecar
def test_every_invocation_extracts_with_timing_and_tokens():
    rows = delegation_view._read_jsonl(DIRECTORY / "trajectory" / "invocations.jsonl")
    assert len(rows) == 232
    assert all(row["started_at"] and row["completed_at"] for row in rows)
    assert all(row["token_usage"].get("total_cost") is not None for row in rows)
    assert {row["wave"] for row in rows} <= {"wave1", "wave2", "wave3"}


@requires_run
def test_every_delegation_resolves_to_agenda_sites():
    agenda = json.loads((DIRECTORY / "agenda.json").read_text())
    proposals = {item["invocation_id"] for item in agenda["proposals"]}
    ledger = delegation_view._read_jsonl(DIRECTORY / "delegations.jsonl")
    assert len(ledger) == 1166
    assert all(row["invocation_id"] in proposals for row in ledger)


@requires_run
@requires_sidecar
def test_cost_matches_the_ledger_and_not_the_poisoned_field():
    ledger = delegation_view._read_jsonl(DIRECTORY / "delegations.jsonl")
    ran = [row for row in ledger if row.get("disposition") != "pruned"]
    from_ledger = sum(row.get("cost") or 0.0 for row in ran)
    from_sidecar = sum(
        row.get("cost") or 0.0
        for row in delegation_view._read_jsonl(DIRECTORY / "trajectory" / "invocations.jsonl")
    )
    assert round(from_ledger, 2) == round(from_sidecar, 2) == 19.17
    # What the page would say if it trusted the ledger's token block.
    poisoned = sum((row.get("token_usage") or {}).get("total_cost", 0.0) for row in ran)
    assert poisoned > 1000, "the poisoned field should still be poisoned; recheck the fixture"


@requires_run
@requires_sidecar
def test_manifest_undercount_is_exactly_the_mandatory_floor():
    views = delegation_view.load_lead_views(DIRECTORY)
    cost = delegation_view.run_cost(DIRECTORY, views)
    assert round(cost["actual_total"], 2) == 21.06
    assert round(cost["manifest_total"], 2) == 6.54
    # The whole gap is the floor: `trace.reconcile` sums leads + proposed and the floor runs
    # inside the lead's own orchestrator, so it lands in neither term.
    assert round(cost["manifest_understates_by"], 2) == round(cost["mandatory"], 2) == 14.52


@requires_run
def test_wall_seconds_is_per_tier_so_the_gantt_must_not_use_it():
    ledger = delegation_view._read_jsonl(DIRECTORY / "delegations.jsonl")
    ran = [row for row in ledger if row.get("disposition") != "pruned"]
    distinct = {row.get("wall_seconds") for row in ran}
    assert len(ran) == 239 and len(distinct) < 40, (
        "wall_seconds is expected to be duplicated per tier; if this ever becomes per-job "
        "the Gantt could use it directly"
    )


@requires_run
@requires_sidecar
def test_briefs_survive_the_schema_gap():
    """`DelegationRecord` omits `brief`; reading through it would drop the lead's reasoning."""

    from src.mathlib_review.schema.review import DelegationRecord

    assert "brief" not in DelegationRecord.model_fields
    views = delegation_view.load_lead_views(DIRECTORY)
    briefed = [job for view in views.values() for job in view.delegations if job.brief]
    assert len(briefed) == 36
    assert all(job.disposition == "proposed" for job in briefed)
    assert all(job.brief.get("question") for job in briefed)
    # The floor is not a decision and carries none.
    floor = [job for view in views.values() for job in view.delegations
             if job.disposition == "mandatory"]
    assert len(floor) == 203 and not any(job.brief for job in floor)


@requires_run
@requires_sidecar
def test_coverage_counts_declined_specialists_not_skipped_sites():
    """The floor puts a generalist on every site, so "sites skipped" is always zero.

    What the lead actually declines is specialist coverage, and that is what the view counts.
    """

    views = delegation_view.load_lead_views(DIRECTORY)
    total = {"sites": 0, "generalist_ran": 0, "all_specialists_declined": 0}
    for view in views.values():
        for key in total:
            total[key] += view.coverage[key]
    assert total["sites"] == total["generalist_ran"] == 432
    assert total["all_specialists_declined"] == 323


@requires_run
@requires_sidecar
def test_summary_totals():
    summary = delegation_view.summarize(DIRECTORY)
    assert summary["proposals"] == 1166
    assert summary["ran"] == 239
    assert summary["declined"] == 927
    assert summary["with_brief"] == 36
