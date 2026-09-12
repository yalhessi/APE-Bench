"""`solo` is the fourth routing mode: no work-unit job is scheduled at all.

`fanout`, `rules` and `lead` all presuppose the work-unit decomposition, so the three of them
answer "which routing is best" and none answers "is any of this better than one agent reading
the whole PR". `docs/research/step-by-step.md:24` names that baseline Step 5 -- "purpose is not
leaderboard numbers but instrument validation" -- and `:28` warns against skipping it. It was
skipped, and `docs/dead-ends.md` has no entry for it.

The mode is added to `ROUTING_MODES` rather than expressed as a separate entrypoint or a
`conditions.py` condition for one reason that the comparison depends on: `build_agenda` uses
`routing_mode` in exactly one place -- stamping the sealed agenda -- and never filters
proposals, so a `solo` run writes a byte-identical `agenda_report.json` PR scope to the `lead`
run on the same config. That file is what `judged_pr_scope` corroborates the denominator
against, and a floor condition scored on a different denominator would measure nothing.
"""

from __future__ import annotations

import pytest

from src.mathlib_review.agenda.agenda import initial_jobs
from src.mathlib_review.io import sealed_model
from src.mathlib_review.schema.review import (
    ROUTING_MODES, RUNTIME_ROUTED_MODES, AgendaProposal, ReviewAgenda,
)


def _agenda(routing_mode: str, pr_numbers=(1, 2)) -> ReviewAgenda:
    proposals = [
        sealed_model(
            AgendaProposal, proposal_id=f"wu:{pr}#generalist",
            invocation_id=f"wu:{pr}#generalist", arm_id="generalist",
            work_unit_id=f"wu:{pr}", episode_id=f"ep:{pr}", pr_number=pr,
            site_change_ids=["change:a"], eligible=True, mandatory=True,
            prompt_sha256="a" * 64, cost_hint=0.079, rationale="r",
        )
        for pr in pr_numbers
    ]
    return sealed_model(
        ReviewAgenda, agenda_id="agenda:t", run_name="t", routing_mode=routing_mode,
        release="rel", arms=[], proposals=proposals,
        scheduler_version="s", renderer_version="r",
    )


def test_solo_is_a_routing_mode():
    assert "solo" in ROUTING_MODES


def test_solo_and_lead_are_both_runtime_routed():
    """Both are reached through the same `else:` in the runner, and both must be branched on
    before it. `lead` decides its jobs at run time; `solo` has no such jobs."""

    assert set(RUNTIME_ROUTED_MODES) == {"lead", "solo"}


def test_solo_schedules_no_work_unit_job_and_says_so_by_name():
    """The failure mode this guards: a fourth mode that falls into the `fanout`/`rules` path
    would be scheduled as an arm mode. It raises -- after the plan is sealed, before any spend
    -- but the message used to say "decides its jobs at run time", which is true of `lead` and
    false of `solo`, and would send a reader looking for a routing decision that does not
    exist."""

    with pytest.raises(ValueError, match="schedules no work-unit job"):
        initial_jobs(_agenda("solo"))


def test_lead_still_raises_for_its_own_reason():
    with pytest.raises(ValueError, match="decides its jobs at run time"):
        initial_jobs(_agenda("lead"))


@pytest.mark.parametrize("mode,expected", [("fanout", 2), ("rules", 2)])
def test_the_arm_modes_are_unchanged(mode, expected):
    assert len(initial_jobs(_agenda(mode))) == expected


def test_solo_and_lead_agendas_scope_the_same_prs():
    """The test that makes the whole comparison legitimate.

    `judged_pr_scope` reads `agenda_report.json` and refuses a judge config naming a PR the run
    never reviewed, so two conditions are only comparable if their agendas scope identically.
    If `routing_mode` ever starts filtering proposals, this fails and the denominator guarantee
    is gone -- which is exactly the defect that let two runs share a 40-obligation denominator
    they had not both earned.
    """

    from src.mathlib_review.agenda.agenda import agenda_report

    lead = agenda_report(_agenda("lead"))
    solo = agenda_report(_agenda("solo"))
    assert solo["pr_numbers"] == lead["pr_numbers"] == [1, 2]
