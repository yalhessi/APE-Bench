"""A rendered prompt says each thing once.

Measured on smoke4's 143 prompts before this change: 44% of all prompt text was a verbatim
repeat of text already in the same prompt — 32% diff hunks re-pasted once per review target,
13% the maintainer checklist appended to every target. The mean prompt carried 1.8 distinct
hunks across 3.4 targets, and one `api_reuse` job carried six targets, one unique hunk, and
16,710 duplicate characters out of 33,174.

That is not only cost. The `family_design` arm on PR 33117 was handed the same 100-line diff
five times and then ran out of budget mid-review.

These tests assert the structural property — each payload appears once — rather than a
percentage, which would be an incidental number that drifts with the fixture.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.datasets.pr_review_v4.io import load_jsonl
from src.datasets.pr_review_v4.render_focused import _target_blocks
from src.datasets.pr_review_v4.render_focused import FOCUSED_FACET_CHECKLIST
from src.datasets.pr_review_v4.schema import (
    ChangeGraph, ReviewEpisodeInput, ReviewWorkUnit,
)

RELEASE = Path("inputs/pr_review_v4/releases/dev-medium-0.3.0")


class _Target:
    """The three fields the renderer reads off a change target."""

    def __init__(self, change_id, subject, fragments):
        self.change_id = change_id
        self.path = "Mathlib/X.lean"
        self.kind = "declaration"
        self.declaration_name = subject
        self.reviewed_entity_ids = []
        self.base_entity_ids = []
        self.base_code = None
        self.reviewed_code = f"lemma {subject} : True := trivial"
        self.diff_fragments = [fragments]


def test_a_shared_hunk_is_printed_once_and_pointed_at_afterwards():
    """The common case: a work unit is related changes in one file, so its targets share a
    hunk."""

    hunk = "@@ -1,3 +1,9 @@\n+lemma neg : True := trivial\n+lemma fun_neg : True := trivial\n"
    blocks = _target_blocks([
        _Target("c1", "Meromorphic.neg", hunk),
        _Target("c2", "Meromorphic.fun_neg", hunk),
        _Target("c3", "Meromorphic.add", hunk),
    ])
    rendered = "\n\n".join(blocks)

    assert rendered.count(hunk) == 1
    assert rendered.count("Identical to the fragments shown for `Meromorphic.neg` above.") == 2
    # Every target still carries its own identity: the submission contract keys on these.
    for change_id in ("c1", "c2", "c3"):
        assert f"`{change_id}`" in rendered
    for subject in ("Meromorphic.neg", "Meromorphic.fun_neg", "Meromorphic.add"):
        assert f"Primary subject (copy exactly): `{subject}`" in rendered


def test_distinct_hunks_are_all_printed():
    """Deduplication must not drop a hunk a target actually needs."""

    blocks = _target_blocks([
        _Target("c1", "A", "@@ hunk one @@\n"),
        _Target("c2", "B", "@@ hunk two @@\n"),
    ])
    rendered = "\n\n".join(blocks)
    assert "@@ hunk one @@" in rendered
    assert "@@ hunk two @@" in rendered
    assert "Identical to the fragments" not in rendered


@pytest.fixture(scope="module")
def arm_prompts():
    """Every specialist prompt the agenda renders for the smoke4 PRs.

    Only the focused renderer is deduplicated. `render_prompts.FACET_CHECKLIST` and the
    production target block keep their per-target form on purpose: they are hashed into every
    frozen `rendered_prompts.jsonl`, so editing them moves every prompt hash in every release at
    once. The generalist path still carries the repetition until a release is re-rendered.
    """

    from src.datasets.pr_review_v4.schema import ModificationRecord, RenderedPrompt
    from src.mathlib_review.agenda.agenda import build_agenda

    inventory = Path("inputs/pr_review_v4/treatments/"
                     "systematic-opportunities-v2-medium/derived/modification_inventory.jsonl")
    if not (RELEASE.exists() and inventory.exists()):
        pytest.skip("release or inventory not present")

    _, pool = build_agenda(
        run_name="dedup-test", routing_mode="lead", release=RELEASE,
        modification_inventory=inventory, pr_numbers=[33117, 33145, 33337, 33362],
        units=load_jsonl(RELEASE / "derived/work_units.jsonl", ReviewWorkUnit),
        episodes=load_jsonl(RELEASE / "input/episodes.jsonl", ReviewEpisodeInput),
        graphs=load_jsonl(RELEASE / "derived/change_graphs.jsonl", ChangeGraph),
        release_prompts=load_jsonl(RELEASE / "derived/rendered_prompts.jsonl", RenderedPrompt),
        modifications=load_jsonl(inventory, ModificationRecord),
    )
    return [
        (payload["arm_id"], (payload.get("task_data") or payload)["rendered_user_prompt"])
        for payload in pool.values()
        if payload["arm_id"] != "generalist"
    ]


def test_every_arm_prompt_carries_exactly_one_checklist(arm_prompts):
    assert arm_prompts, "no specialist prompts were rendered"
    for arm_id, prompt in arm_prompts:
        assert prompt.count("### Maintainer ask checklist") == 1, arm_id
        assert prompt.count(FOCUSED_FACET_CHECKLIST) == 1, arm_id


def test_no_arm_prompt_repeats_a_diff_hunk(arm_prompts):
    """The end-to-end property, on the PR set where this was measured.

    Before the change these prompts carried 32% repeated hunk text; the `api_reuse` job on
    33117 had six targets, one unique hunk, and 16,710 duplicate characters.
    """

    for arm_id, prompt in arm_prompts:
        sections = prompt.split("### Exact changed fragments")[1:]
        hunks = [
            section.split("```")[1] for section in sections
            if section.lstrip().startswith("```")
        ]
        assert len(hunks) == len(set(hunks)), f"{arm_id} repeats a hunk"
