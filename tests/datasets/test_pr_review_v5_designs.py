"""Review designs beside the frozen solo baseline (docs/plans/2026-10-02-review-designs.md §2).

A design is a per-PR task that ends in the solo submission contract, selected by
`dataset.design` from `DESIGNS` -- a registry beside the task registry -- so that everything
after the submission reads every design alike, and adding one is a module, a registry line
and a config. Two things are pinned here before any design exists:

* the baseline is frozen: the two subscription configs, the brief and `solo.py`'s prompt text
  render byte for byte what the hygiene reps read, and a `solo` payload is what it was before
  the registry existed;
* the organization holds: an unknown design is refused at config load, a design outside
  `routing_mode: solo` is refused before anything is spent, and a chained design without its
  first stage's run is refused -- except under `plan`, which reports it instead.
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from types import SimpleNamespace

import pytest

from ape.tasks.base import get_task_class
from ape.tasks.lean_tasks.formal_math.review import DESIGNS, SOLO_TASK_TYPE, SoloReviewTask
from ape.tasks.lean_tasks.formal_math.review.base import BasePRReviewTask

#: The frozen baseline, by digest. A change to any of these moves the prompt or the condition
#: every design is read against, so it fails here by name rather than in a paid rep.
FROZEN = {
    "configs/pr_review_v5_dev_medium_opus55_contract2_claude_sub.yaml":
        "f2852624e076a16690a0d107f22cfb5411051bc90dab3e6fbfe2a0039215c209",
    "configs/pr_review_v5_dev_medium_opus55_contract2_hygiene_claude_sub.yaml":
        "6cf0830a52fbdaa612bfe39faba6aea75a04fb6d98345c10ab5ad58118eb885b",
    "results/pr_review_v5/probes/contract-2026-10-01/brief_G2.md":
        "aafac29605a6edd49d36dd8fcc087b4ed6f64c05c15969b34135f843d2167e5b",
}
SOLO_PROMPT_TEXT_SHA256 = "f37135b188b8678c59e747f87a30704d02542a8f967f40e5b6800e8f34295aaa"
HYGIENE_TEMPLATE_SHA256 = "9f28b17d21358702052e5c29e3dc0a511223b2af494be9bbe4950a2b247e91de"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# --- the frozen baseline ----------------------------------------------------------------------


@pytest.mark.parametrize("path,digest", sorted(FROZEN.items()))
def test_the_baseline_configs_and_brief_are_byte_for_byte_what_the_reps_read(path, digest):
    assert _sha(Path(path).read_bytes()) == digest, (
        f"{path} changed; the solo baseline is frozen and a design is a new task and a new "
        "config (plan §1)")


def test_the_solo_prompt_text_is_unchanged():
    from ape.tasks.lean_tasks.formal_math.review import solo

    parts = [solo.SOLO_SYSTEM, solo.SOLO_USER, solo.SOLO_USER_V2, solo.SEVERITY_LINES["merge"],
             solo.SEVERITY_LINES["request"], solo.NOTES_LINE, solo.NOTES_LINE_FAMILY]
    assert _sha("\n<<>>\n".join(parts).encode()) == SOLO_PROMPT_TEXT_SHA256
    # The template the hygiene configs render (request bar, notes per object family, v2).
    assert _sha(solo.solo_user_template("request", True, "v2", "per_object_family", "").encode()) \
        == HYGIENE_TEMPLATE_SHA256


# --- the registry -----------------------------------------------------------------------------


def test_solo_is_the_default_design_and_the_registry_names_registered_tasks():
    assert DESIGNS["solo"] is SoloReviewTask
    for name, cls in DESIGNS.items():
        assert issubclass(cls, BasePRReviewTask), name
        assert get_task_class(cls.task_type) is cls, (
            f"{name} is in DESIGNS but its task type {cls.task_type!r} is not registered")
        assert isinstance(cls.reads_stage, bool)


def test_every_design_ends_in_the_solo_submission_contract():
    """The downstream chain reads `findings` with an anchor, a claim, a fix and a severity off
    the result (`runner.solo_responses` -> `anchor_submitted_findings`), and the result's
    `episode_id` to key it. A design whose result lacks either would be a design the judge
    cannot see."""

    for name, cls in DESIGNS.items():
        fields = cls.task_result_class.model_fields
        assert {"findings", "episode_id", "invocation_id"} <= set(fields), name
        assert "episode_id" in cls.data_class.model_fields, name


# --- dataset.design ---------------------------------------------------------------------------


def _dataset(**overrides):
    from src.mathlib_review.review.runner import V5DatasetConfig

    payload = dict(release=Path("rel"), modification_inventory=Path("inv"), routing_mode="solo")
    payload.update(overrides)
    return V5DatasetConfig(**payload)


def test_the_default_design_is_solo_and_an_unknown_one_is_refused_at_load():
    assert _dataset().design == "solo"
    with pytest.raises(ValueError, match="unknown design"):
        _dataset(design="not-a-design")


def test_a_solo_plan_records_no_design_and_a_design_is_sealed_when_it_is_not_solo():
    """`evaluation_settings` carries the knob only when set, so every plan sealed before designs
    existed recomputes byte for byte (the rule `forbid_abstention` follows there)."""

    from src.mathlib_review.review.runner import evaluation_settings

    assert "design" not in evaluation_settings(_dataset())
    assert "stage_input_run" not in evaluation_settings(_dataset())
    design = next(iter(name for name in DESIGNS if name != "solo"), None)
    if design is not None:
        settings = evaluation_settings(_dataset(design=design, stage_input_run="stage_a"))
        assert settings["design"] == design and settings["stage_input_run"] == "stage_a"


def _episode(pr: int):
    return SimpleNamespace(
        episode_id=f"ep:{pr}", pr_number=pr, title=SimpleNamespace(text="t"),
        description=SimpleNamespace(text="d"), diff="--- a\n+++ b\n", changed_files=["Mathlib/A.lean"],
        reviewed_head_sha="h" * 40, base_sha="b" * 40)


def _agenda(prs):
    return SimpleNamespace(proposals=[SimpleNamespace(episode_id=f"ep:{pr}") for pr in prs])


def test_a_solo_payload_is_what_it_was_before_the_registry_existed():
    """The task type, the id prefix and every key: the hygiene reps resume on this identity."""

    from src.mathlib_review.review.runner import _solo_task_data

    [payload] = _solo_task_data(_agenda([33337]), [_episode(33337)], _dataset(),
                                {"ep:33337": "2026-01-01T00:00:00Z"}, Path("trace.jsonl"))
    assert payload["task_type"] == SOLO_TASK_TYPE
    assert payload["task_id"] == "pr5solo_ep_33337"
    assert payload["invocation_id"] == "ep:33337#solo_agent"
    assert set(payload) == {
        "task_type", "task_id", "episode_id", "pr_number", "pr_title", "pr_description", "diff",
        "changed_files", "snapshot_head_sha", "snapshot_base_sha", "context_tools",
        "retrieval_cutoff", "invocation_id", "trace_path", "execution_limits", "target_workspace",
    }, "the solo payload grew a key; the baseline's task data is frozen"


def test_a_design_outside_routing_mode_solo_is_refused_before_anything_is_spent():
    import asyncio

    from src.mathlib_review.review.runner import run

    design = next(iter(name for name in DESIGNS if name != "solo"), None)
    if design is None:
        pytest.skip("no design beside solo is registered yet")
    dataset = _dataset(design=design, routing_mode="lead", run_name="t")
    scaffold = SimpleNamespace(llm_config=SimpleNamespace(model_name="gpt_5.2"))
    with pytest.raises(ValueError, match="per-PR reviewer"):
        # Refused at the top of `run`, before the release is read or a model is reached.
        asyncio.run(run(dataset, scaffold, {}, logging.getLogger("t")))


# --- a chained design reads its stage through StageInput --------------------------------------


def test_a_design_that_reads_no_stage_gets_none():
    from src.mathlib_review.review.runner import stage_rows_for

    assert stage_rows_for(_dataset(), [33337], logging.getLogger("t")) is None


class _ChainedForTest(SoloReviewTask):
    task_type = SOLO_TASK_TYPE
    reads_stage = True


def test_a_chained_design_without_its_stage_is_refused_and_plan_reports_it(monkeypatch, caplog):
    import ape.tasks.lean_tasks.formal_math.review as review_pkg
    from src.mathlib_review.review import runner

    monkeypatch.setitem(review_pkg.DESIGNS, "chained_for_test", _ChainedForTest)
    dataset = _dataset(design="chained_for_test")
    with pytest.raises(ValueError, match="--of"):
        runner.stage_rows_for(dataset, [33337], logging.getLogger("t"))
    with caplog.at_level(logging.WARNING, logger="t"):
        assert runner.stage_rows_for(dataset, [33337], logging.getLogger("t"), dry_run=True) is None
    assert "--of" in caplog.text and "refused" in caplog.text


def test_a_chained_design_reads_the_ledgers_and_refuses_an_uncovered_pr(monkeypatch, tmp_path):
    import ape.tasks.lean_tasks.formal_math.review as review_pkg
    from src.mathlib_review.review import runner
    from src.mathlib_review import run_state

    monkeypatch.setitem(review_pkg.DESIGNS, "chained_for_test", _ChainedForTest)
    stage_dir = tmp_path / "stage_a"
    stage_dir.mkdir()
    rows = [{"episode_id": "ep:33337", "pr_number": 33337, "design": "x", "ledger": [{"a": 1}]}]
    (stage_dir / "ledgers.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    monkeypatch.setattr(run_state.StageInput, "of",
                        classmethod(lambda cls, name, **kw: cls.at(stage_dir, run_name=name, **kw)))

    dataset = _dataset(design="chained_for_test", stage_input_run="stage_a")
    got = runner.stage_rows_for(dataset, [33337], logging.getLogger("t"))
    assert got == {"ep:33337": rows[0]}
    with pytest.raises(ValueError, match="none for \\[33149\\]"):
        runner.stage_rows_for(dataset, [33337, 33149], logging.getLogger("t"))


def test_the_ledgers_artifact_is_declared_where_every_artifact_is():
    from src.mathlib_review.run_state import RUN_ARTIFACTS

    assert RUN_ARTIFACTS["ledgers"].filename == "ledgers.jsonl"
    assert RUN_ARTIFACTS["ledgers"].writer == "run"


def test_ledger_rows_carry_only_results_with_a_ledger_and_their_design_keys():
    from ape.tasks.lean_tasks.formal_math.review.solo import SoloReviewResult
    from src.mathlib_review.review.runner import _ledger_rows

    class Result(SoloReviewResult):
        ledger: list = []
        refuted: list = []

    results = SimpleNamespace(task_results=[
        Result(task_id="a", task_type=SOLO_TASK_TYPE, global_index="a", success=True, score=1.0, pr_number=1,
               episode_id="ep:1", ledger=[{"declaration": "x"}], refuted=[], findings=[{"claim": "c"}]),
        Result(task_id="b", task_type=SOLO_TASK_TYPE, global_index="b", success=True, score=1.0, pr_number=2,
               episode_id="ep:2"),  # a solo-shaped result: no ledger, no row
        Result(task_id="c", task_type=SOLO_TASK_TYPE, global_index="c", success=False, score=0.0, pr_number=3,
               episode_id="ep:3", ledger=[{"declaration": "y"}]),
    ])
    rows = _ledger_rows(results, "structured")
    assert [row["episode_id"] for row in rows] == ["ep:1"]
    assert rows[0]["design"] == "structured" and rows[0]["ledger"] == [{"declaration": "x"}]
    assert "findings" not in rows[0], "the base result's keys are in the run's other artifacts"


# --- configs/designs: a design config differs from its baseline in the design alone -------------


DESIGN_CONFIGS = sorted(Path("configs/designs").glob("*.yaml"))


def _resolved(path: Path) -> dict:
    from ape.utils.config_loader import load_yaml

    return load_yaml(path)


def _baseline_of(path: Path) -> Path:
    import yaml

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return (path.parent / raw["extends"]).resolve()


def _flatten(node, prefix=""):
    if isinstance(node, dict):
        out = {}
        for key, value in node.items():
            out.update(_flatten(value, f"{prefix}{key}."))
        return out
    return {prefix[:-1]: node}


def test_there_is_a_config_per_registered_design_and_each_names_its_design():
    designs = {name for name in DESIGNS if name != "solo"}
    named = {_resolved(path)["dataset"]["design"] for path in DESIGN_CONFIGS}
    assert designs <= named, sorted(designs - named)
    for path in DESIGN_CONFIGS:
        assert path.name.startswith(_resolved(path)["dataset"]["design"] + "_"), path


@pytest.mark.parametrize("path", DESIGN_CONFIGS, ids=lambda p: p.name)
def test_a_design_config_differs_from_its_baseline_in_the_design_and_its_own_knobs_alone(path):
    """The pattern of `test_the_two_solo_conditions_differ_only_in_their_scaffold`: a design
    result read against the baseline must not also be a policy, model, tool-grant or cap
    contrast. The design's own task knobs -- fields its config class declares and the solo's
    does not -- are the one allowed addition, since they exist for no other task."""

    from ape.tasks.lean_tasks.formal_math.review import SoloReviewConfig

    design = _resolved(path)
    baseline = _resolved(_baseline_of(path))
    name = design["dataset"]["design"]
    own_knobs = {f"task_config.{field}"
                 for field in DESIGNS[name].task_config_class.model_fields
                 if field not in SoloReviewConfig.model_fields}
    flat_design, flat_base = _flatten(design), _flatten(baseline)
    changed = {key for key in set(flat_design) | set(flat_base)
               if flat_design.get(key, "<absent>") != flat_base.get(key, "<absent>")}
    assert changed - {"dataset.design"} <= own_knobs, sorted(changed - {"dataset.design"})
    assert "dataset.design" in changed and baseline["dataset"].get("design", "solo") == "solo"
    assert design["dataset"]["routing_mode"] == "solo"


@pytest.mark.parametrize("path", DESIGN_CONFIGS, ids=lambda p: p.name)
def test_a_design_config_loads_under_the_run_models(path):
    """`test_config_strictness` globs `configs/*.yaml` only; the designs directory validates here."""

    from src.mathlib_review.review.runner import load_run

    dataset, scaffold, _overrides = load_run(path, {"dataset": {"run_name": "design_test"}})
    assert dataset.design in DESIGNS and dataset.routing_mode == "solo"
    assert scaffold.scaffold_type == "claude_code"
