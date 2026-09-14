"""A rendered prompt says each thing once, and says it about the target it is for.

Two rounds of the same defect. Within one prompt, measured on smoke4's 143 prompts: 44% of all
prompt text was a verbatim repeat of text already in that prompt — 32% diff hunks re-pasted once
per review target, 13% the checklist appended to every target. That is not only cost; the
`family_design` arm on PR 33117 was handed the same 100-line diff five times and ran out of
budget mid-review.

Across prompts, measured on the 12-PR held-out lead run: `### Exact changed fragments` was 43.6%
of all rendered prompt characters and 95.5% of its volume was a re-send of a block another job
for the same PR already carried, because the section held the raw `@@` hunks and a target in a
single-hunk file inherits the whole file diff. PR 33149 shipped one 17,303-char hunk to 120 jobs
that each review one declaration. Scoping the section to the target's own regions removes 94.0%
of `dev-medium-0.3.0`'s fragment characters and 73.8% of the arm pool's target-block volume.

These tests assert the structural properties — each payload appears once, and a target's diff is
about that target — rather than percentages, which drift with the fixture.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.mathlib_review.io import load_jsonl
from src.mathlib_review.agenda.render_prompts import (
    FACET_CHECKLIST_ONCE,
    target_blocks,
    target_diff_section,
)
from src.mathlib_review.schema import (
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
    blocks = target_blocks([
        _Target("c1", "Meromorphic.neg", hunk),
        _Target("c2", "Meromorphic.fun_neg", hunk),
        _Target("c3", "Meromorphic.add", hunk),
    ], scoped=False)
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

    blocks = target_blocks([
        _Target("c1", "A", "@@ hunk one @@\n"),
        _Target("c2", "B", "@@ hunk two @@\n"),
    ], scoped=False)
    rendered = "\n\n".join(blocks)
    assert "@@ hunk one @@" in rendered
    assert "@@ hunk two @@" in rendered
    assert "Identical to the fragments" not in rendered


def test_a_targets_diff_is_about_that_target():
    """The scoped section shows the target's own change, not the hunk it happens to sit in.

    `_Target` gives every target the same file-wide hunk and its own reviewed region, which is
    the shape that made this section 43.6% of a run's prompt characters: three targets, one
    17,000-char-style hunk, three copies.
    """

    hunk = ("@@ -1,3 +1,9 @@\n+lemma neg : True := trivial\n"
            "+lemma fun_neg : True := trivial\n+lemma add : True := trivial\n")
    blocks = target_blocks([
        _Target("c1", "Meromorphic.neg", hunk),
        _Target("c2", "Meromorphic.fun_neg", hunk),
    ], scoped=True)
    rendered = "\n\n".join(blocks)

    assert hunk not in rendered, "the raw file-wide hunk is still being pasted"
    # Each target's own reviewed region is what it is shown, as an addition.
    assert "+lemma Meromorphic.neg : True := trivial" in rendered
    assert "+lemma Meromorphic.fun_neg : True := trivial" in rendered
    # Distinct diffs, so neither is deduplicated away.
    assert "Identical to the fragments" not in rendered


def test_a_target_with_no_regions_keeps_its_raw_hunk():
    """Import blocks carry no semantic entities, so the hunk is the only record of the change.

    Falling through to an empty diff would show the arm a blank change; on
    `dev-medium-0.3.0` this exception is 17 of 508 targets and 2,195 of 2,583,336 fragment
    characters.
    """

    target = _Target("c1", "Mathlib/X.lean", "@@ -1 +1,2 @@\n+import Mathlib.Tactic.ToFun\n")
    target.kind = "import"
    target.declaration_name = None
    target.base_code = None
    target.reviewed_code = None

    assert "+import Mathlib.Tactic.ToFun" in target_diff_section(target)


@pytest.fixture(scope="module")
def arm_prompts():
    """Every specialist prompt the agenda renders for the smoke4 PRs.

    `FACET_CHECKLIST` and the raw-hunk section keep their per-target form for every renderer
    version that already exists, because they are hashed into every frozen
    `rendered_prompts.jsonl`. The deduplicated and scoped forms are what the newer versions
    select — `focused-prompt/3` for the arms this fixture renders, `candidate-prompt/13` for the
    generalist, which reaches a release only through `rerender_release`.
    """

    from src.mathlib_review.schema import ModificationRecord, RenderedPrompt
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
        assert prompt.count(FACET_CHECKLIST_ONCE) == 1, arm_id


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


def test_the_contract_is_sent_once_from_candidate_prompt_13():
    """The system prompt is the contract; the user message must not repeat it.

    Measured on `pr5_A_lead_heldout12_fp3_rep1`: 203 of 203 generalist prompts carried the
    identical 2,482-character contract twice — once as the system prompt and once under
    `# Review contract` — for 503,846 characters, 12.5% of that run's generalist user text, and
    the duplicate is the expensive copy, since user text is billed at roughly 4.7x a token
    inside the cached prefix. The focused arms never carried it (0 of 1,206 in the same run)
    and review normally.

    Pinned at the version boundary in both directions: /12 keeps it, because that text is
    hashed into every frozen `rendered_prompts.jsonl`.
    """

    from src.mathlib_review.io import load_jsonl
    from src.mathlib_review.agenda.render_prompts import render_work_unit
    from src.mathlib_review.schema import ChangeGraph, ReviewEpisodeInput, ReviewWorkUnit

    graphs = {item.episode_id: item for item in
              load_jsonl(RELEASE / "derived/change_graphs.jsonl", ChangeGraph)}
    episodes = {item.episode_id: item for item in
                load_jsonl(RELEASE / "input/episodes.jsonl", ReviewEpisodeInput)}
    unit = load_jsonl(RELEASE / "derived/work_units.jsonl", ReviewWorkUnit)[0]
    episode, graph = episodes[unit.episode_id], graphs[unit.episode_id]

    old = render_work_unit(unit, episode, graph)
    assert old.system_prompt in old.user_prompt, "/12 must keep the copy it was frozen with"

    new = render_work_unit(
        unit.model_copy(update={"renderer_version": "candidate-prompt/13"}), episode, graph)
    assert new.system_prompt, "the contract still has to be sent as the system prompt"
    assert new.system_prompt not in new.user_prompt
    assert "# Review contract" not in new.user_prompt
    # The review targets themselves are untouched by this.
    assert "## Review target" in new.user_prompt
