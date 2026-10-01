"""The contract knobs, asserted at the far end: on the pool an arm is handed and the plan it seals.

Two things must hold for the unified contract's first run to be read against the control already
paid for (`pr5_V2_verdicts_fanout4_control_rep1`):

* **The control rebuilds byte-identical.** Built from the control config on today's code, one PR's
  agenda has the prompt hashes, arm hashes and renderer version the paid run sealed, and each pool
  payload is the task data that run dispatched, less the two keys the runner adds at dispatch
  (`retrieval_cutoff`, `trace_path`). If it did not, the "control" would be a third condition.
* **The treatment carries the whole contract.** Every payload -- the generalist's included --
  carries both directives, and every specialist's system prompt carries the three sections that
  say what its tool enforces, and never names an argument the verdict tool does not have.

Built from the configs through `runner.load_run`, as `cli plan` builds them, not from a fixture:
a fixture would agree with itself and not with the run. One PR (33315, the control PR) keeps it
to one exposure scan, ~7 s. Skipped where the paid run's gitignored pool is absent.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.mathlib_review.io import jsonl_rows

CONTROL_RUN = Path("results/pr_review_v5/runs/pr5_V2_verdicts_fanout4_control_rep1")
CONTROL_CONFIG = Path("configs/pr_review_v5_verdicts_fanout4_control.yaml")
TREATMENT_CONFIG = Path("configs/pr_review_v5_verdicts_fanout4.yaml")
PR = 33315
#: Keys `_direct_arm_task_data` adds when it dispatches, which the agenda's pool never holds.
DISPATCH_KEYS = {"retrieval_cutoff", "trace_path"}

#: Arms whose prompt deliberately changed since the paid control, with the exact text that moved.
#: The unification's naming correction (spec identity ee245f077b7e -> 1f4b176a45a4) is one: the
#: bullet said "Submit nothing on naming" for both of `naming_norm`'s empty branches, one of which
#: is the tool failing to resolve the subject; and (2026-09-24) a bullet scoping every verdict to the
#: name's leading prefix, with the closing clause scoped to "every part you can check"; and
#: (2026-10-01) the `conforms` verdict and the two counted `empty_because` reasons, which the tool
#: now returns where it used to say `insufficient_evidence` with no reason. The rebuilt
#: control is identical on every other arm,
#: and on this one differs by exactly these replacements -- anything else would be drift.
MOVED_SINCE_CONTROL = {
    "naming": [
        ("    * `insufficient_evidence` — the repository has no opinion here. Submit nothing on naming.",
         "    * `conforms` — the corpus has a convention and this name already follows it. There is no\n"
         "      prefix change to ask for.\n"
         "    * `insufficient_evidence` — the counts do not settle it, and `empty_because` says why.\n"
         "      `no_population`: the repository has no counted opinion here. `population_too_small`: the\n"
         "      leading spelling has too few declarations to call a convention. `no_dominant_prefix`: no\n"
         "      spelling clears the bar. `subject_unresolved`: the tool could not tell what the declaration\n"
         "      is about and never asked the corpus. In every case but `no_population` the prefix is\n"
         "      unmeasured rather than settled -- judge the name on precedent and on the siblings you read.\n"
         "    * Whatever the verdict, it is about the name's LEADING prefix only. The tool does not measure a\n"
         "      suffix, a prime, argument order or a namespace; judge those against the siblings you read and\n"
         "      against precedent."),
        ("use `coe_`\" is. If the verdict is `insufficient_evidence` and no precedent says otherwise, or the\n"
         "name already follows the convention, submit nothing — a naming check that finds nothing is a\n"
         "normal and correct outcome.",
         "use `coe_`\" is. If the repository has no counted opinion and no precedent says otherwise, or the\n"
         "name already follows the convention in every part you can check, there is nothing to ask — a\n"
         "naming check that finds nothing is a normal and correct outcome."),
    ],
}


def _arm_of(invocation_id: str) -> str:
    return invocation_id.rsplit("#", 1)[-1]


def _as_moved(arm_id: str, text: str) -> str:
    for old, new in MOVED_SINCE_CONTROL.get(arm_id, []):
        assert old in text, (arm_id, old[:60])
        text = text.replace(old, new)
    return text

pool_exists = pytest.mark.skipif(
    not (CONTROL_RUN / "arm_pool.jsonl").is_file(),
    reason="the paid control's arm_pool.jsonl is gitignored and absent in this checkout")


def _built(config: Path):
    import logging

    from src.mathlib_review.agenda.agenda import build_agenda
    from src.mathlib_review.review.runner import (
        load_release, load_run, select_units_and_episodes, stamp_submission_directives,
    )

    dataset, _scaffold, _overrides = load_run(
        config, {"dataset": {"pr_numbers": [PR], "run_name": "far_end_check"}})
    release = load_release(dataset)
    units, episodes = select_units_and_episodes(dataset, release)
    agenda, pool = build_agenda(
        run_name=dataset.run_name, routing_mode=dataset.routing_mode, release=dataset.release,
        modification_inventory=dataset.modification_inventory, units=units, episodes=episodes,
        graphs=release["graphs"], release_prompts=release["release_prompts"],
        modifications=release["modifications"], pr_numbers=[PR],
        use_exposure_index=dataset.use_exposure_index,
        generalist_floor=dataset.generalist_floor,
        submission_verification_policy=dataset.submission_verification_policy,
        target_verdicts=dataset.target_verdicts,
    )
    stamp_submission_directives(pool, dataset, logging.getLogger("far_end"))
    return dataset, agenda, pool


@pytest.fixture(scope="module")
def control():
    return _built(CONTROL_CONFIG)


@pytest.fixture(scope="module")
def treatment():
    return _built(TREATMENT_CONFIG)


@pool_exists
def test_the_control_rebuilds_to_the_prompts_the_paid_control_sealed(control):
    _dataset, agenda, _pool = control
    plan = json.loads((CONTROL_RUN / "run_plan.json").read_text())
    sealed = json.loads((CONTROL_RUN / "agenda.json").read_text())
    rebuilt = {item.invocation_id: item.prompt_sha256 for item in agenda.proposals}
    assert rebuilt, "no proposals for the control PR"
    for key, digest in rebuilt.items():
        moved = _arm_of(key) in MOVED_SINCE_CONTROL
        assert (digest == plan["prompt_sha256_by_invocation"][key]) is (not moved), key
    arms = {arm.arm_id: arm.source_sha256 for arm in agenda.arms}
    for arm_id, digest in plan["arm_sha256_by_id"].items():
        assert (arms[arm_id] == digest) is (arm_id not in MOVED_SINCE_CONTROL), arm_id
    assert agenda.renderer_version == sealed["renderer_version"] == (
        "candidate-prompt/12+focused-prompt/4")


@pool_exists
def test_the_control_pool_is_the_task_data_the_paid_control_dispatched(control):
    _dataset, _agenda, pool = control
    dispatched = {row["invocation_id"]: row["task_data"]
                  for row in jsonl_rows(CONTROL_RUN / "arm_pool.jsonl")
                  if row["task_data"]["pr_number"] == PR}
    assert set(pool) == set(dispatched)
    for invocation_id, payload in pool.items():
        sent = {key: value for key, value in dispatched[invocation_id].items()
                if key not in DISPATCH_KEYS}
        arm_id = _arm_of(invocation_id)
        if arm_id in MOVED_SINCE_CONTROL:
            # The moved arm differs by exactly the recorded text, and so, necessarily, by the
            # hashes of that text: the prompt hash, and `global_index`, the content hash the
            # orchestrator resumes on -- which MUST move, or a new run under the new text would
            # silently resume the paid control's job. Nothing else in its payload moves.
            assert payload["rendered_system_prompt"] == _as_moved(
                arm_id, sent["rendered_system_prompt"]), invocation_id
            for key in ("rendered_system_prompt", "rendered_prompt_sha256", "global_index"):
                assert payload[key] != sent[key], (invocation_id, key)
                sent.pop(key), payload.pop(key)
        assert payload == sent, invocation_id


@pool_exists
def test_the_treatment_carries_the_whole_contract_on_every_payload(treatment):
    dataset, agenda, pool = treatment
    assert dataset.target_verdicts is True
    assert dataset.submission_verification_policy == "verify_edits_if_present"
    assert agenda.renderer_version == (
        "candidate-prompt/12+focused-prompt/4+ask_without_fix+target_verdicts")
    # This config runs no generalist; that the generalist is stamped too is
    # `test_every_payload_carries_the_contract_the_generalist_included` in the agenda tests.
    for invocation_id, payload in pool.items():
        assert payload["target_verdicts"] is True, invocation_id
        assert payload["submission_verification_policy"] == "verify_edits_if_present"


@pool_exists
def test_every_treatment_specialist_reads_what_its_tool_enforces(treatment, control):
    _dataset, _agenda, pool = treatment
    _c, _ca, control_pool = control
    headings = ("## When the fix does not compile", "## Account for every target",
                "## Two strengths of ask")
    specialists = [p for p in pool.values() if p["arm_id"] != "generalist"]
    assert specialists
    for payload in specialists:
        system = payload["rendered_system_prompt"]
        contract = system[system.index("# Submission contract for this run"):]
        for heading in headings:
            assert heading in contract, (payload["invocation_id"], heading)
        assert "abstention_reason" not in contract and "abstention_detail" not in contract
        # The treatment changes the contract and nothing the arm is shown about the code.
        assert payload["rendered_user_prompt"] == (
            control_pool[payload["invocation_id"]]["rendered_user_prompt"])
