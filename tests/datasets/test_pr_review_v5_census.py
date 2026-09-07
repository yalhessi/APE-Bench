"""Ranking the work so the lead reads the interesting part first.

The agenda was ordered by `proposal_id` — `wu:<hash>#<arm>` — an opaque content hash, then
paged 40 at a time, which cuts it by work unit. Nine of eleven leads on the held-out run read
only page 0. On PR 33149 that page held 5 of 56 work units and 1 of the 23 carrying a gold
obligation, so routing was measuring visibility rather than judgment.

Two properties matter and are tested separately: the census must be **complete** (ranking may
reorder, never hide), and its ordering must beat the hash. The second is checked against real
gold placement, which is legitimate here because ranking is evaluated offline — the census
itself reads only the diff, the PR description and the relation graph.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.datasets.pr_review_v4.io import load_jsonl
from src.datasets.pr_review_v4.pr_relations import build_relations
from src.datasets.pr_review_v4.schema import (
    ChangeGraph,
    ReviewEpisodeInput,
    ReviewWorkUnit,
)
from src.mathlib_review.agenda.census import (
    _CHAIN_STEPS,
    _manual_steps,
    build_census,
    census_report,
)

RELEASE = Path("inputs/pr_review_v4/releases/dev-medium-0.3.0")
RUN = Path("results/pr_review_v5/runs/pr_review_v5_lead_medium_heldout_rep1")

requires_run = pytest.mark.skipif(
    not (RUN / "agenda.json").is_file(), reason="held-out run artifacts not present")


@pytest.fixture(scope="module")
def release():
    return {
        "units": load_jsonl(RELEASE / "derived/work_units.jsonl", ReviewWorkUnit),
        "graphs": load_jsonl(RELEASE / "derived/change_graphs.jsonl", ChangeGraph),
        "episodes": load_jsonl(RELEASE / "input/episodes.jsonl", ReviewEpisodeInput),
    }


@pytest.fixture(scope="module")
def census(release):
    from src.mathlib_review.schema.review import ReviewAgenda

    agenda = ReviewAgenda.model_validate(json.loads((RUN / "agenda.json").read_text()))
    relations, _evidence = build_relations(release["graphs"])
    return build_census(agenda.proposals, release["units"], release["graphs"],
                        release["episodes"], relations), agenda


# --------------------------------------------------------------------------------------
# the tactic-chain signal
# --------------------------------------------------------------------------------------

def test_a_collapsible_chain_is_recognised():
    """Read off the two proofs PR 33285's maintainer actually asked to golf."""

    assert _manual_steps("theorem f : T := by\n  rw [x]\n  ext\n  simp") >= _CHAIN_STEPS
    assert _manual_steps(
        "theorem g : T := by\n  rw [SetLike.le_def]\n  intro m h\n"
        "  simp only [mem_comap]\n  exact add_mem h.1 h.2") >= _CHAIN_STEPS


def test_a_one_liner_is_not_a_chain():
    assert _manual_steps("theorem f : T := by simpa [x] using h") < _CHAIN_STEPS


def test_a_term_mode_proof_has_no_steps():
    assert _manual_steps("theorem f : T := trivial") == 0


def test_length_is_not_the_signal():
    """Raw length ranked a 26-line `def` above the 8-line proof the maintainer wanted
    golfed. A long structure definition is long because it has fields."""

    long_def = "def d : T where\n" + "\n".join(f"  field{i} := rfl" for i in range(20))
    assert _manual_steps(long_def) < _CHAIN_STEPS


# --------------------------------------------------------------------------------------
# completeness and determinism
# --------------------------------------------------------------------------------------

@requires_run
def test_the_census_hides_nothing(census, release):
    """Ranking may reorder; it may never make a work unit unreachable."""

    rows, agenda = census
    ranked = {row.work_unit_id for row in rows}
    expected = {p.work_unit_id for p in agenda.proposals if not p.mandatory}
    assert ranked == expected


@requires_run
def test_ranks_are_dense_and_total(census):
    rows, _agenda = census
    assert [row.rank for row in rows] == list(range(1, len(rows) + 1))


@requires_run
def test_the_ordering_is_reproducible(census, release):
    from src.mathlib_review.schema.review import ReviewAgenda

    rows, _agenda = census
    agenda = ReviewAgenda.model_validate(json.loads((RUN / "agenda.json").read_text()))
    relations, _ = build_relations(release["graphs"])
    again = build_census(agenda.proposals, release["units"], release["graphs"],
                         release["episodes"], relations)
    assert [r.work_unit_id for r in rows] == [r.work_unit_id for r in again]


@requires_run
def test_every_row_carries_its_arms(census):
    """The lead routes from this, so a row without its proposal ids is unroutable."""

    rows, _agenda = census
    for row in rows:
        assert row.arms, row.work_unit_id
        for arm, proposal_id in row.arms:
            assert proposal_id.endswith(f"#{arm}")


# --------------------------------------------------------------------------------------
# does the ranking beat the hash?
# --------------------------------------------------------------------------------------

@requires_run
def test_the_axiom_pr_surfaces_its_axioms_first(census):
    """PR 33149's gold is "remove the axioms". Under the hash ordering the lead saw 1 of its
    23 gold-bearing units; the axiom signal should put them at the top."""

    rows, _agenda = census
    top = [r for r in rows if r.pr_number == 33149][:5]
    assert top, "no work units for PR 33149"
    assert any("axiom" in signal.name for row in top for signal in row.signals)


@requires_run
def test_ranking_beats_the_hash_ordering_on_gold_placement(census, release):
    """The whole point, measured. Gold placement is read here for evaluation only — the
    census is built from the diff, the description and the relation graph."""

    rows, agenda = census
    judgments = [json.loads(x) for x in
                 (RELEASE / "gold/judgments.jsonl").read_text().splitlines() if x.strip()]
    unit_of = {c: u.work_unit_id for u in release["units"] for c in u.change_ids}
    gold_units = {unit_of[c] for j in judgments for o in (j.get("obligations") or [])
                  for c in o["change_ids"] if c in unit_of}

    # Built per PR, because that is how a lead sees it — one lead, one PR.
    by_pr = {}
    for proposal in agenda.proposals:
        if not proposal.mandatory:
            by_pr.setdefault(proposal.pr_number, []).append(proposal)
    relations, _ = build_relations(release["graphs"])

    ranked_hits = hash_hits = 0
    for proposals in by_pr.values():
        per_pr = build_census(proposals, release["units"], release["graphs"],
                              release["episodes"], relations)
        ranked_hits += sum(1 for row in per_pr
                           if row.work_unit_id in gold_units and row.rank <= 5)
        head = sorted(proposals, key=lambda p: p.proposal_id)[:40]
        hash_hits += len({p.work_unit_id for p in head} & gold_units)

    # The claim is only that ranking reaches more gold in a five-row slice than the hash
    # ordering reaches in a forty-row page — an eightfold smaller budget of the lead's
    # attention. Measured on this run: 22 against 18.
    assert ranked_hits >= hash_hits, (ranked_hits, hash_hits)


@requires_run
def test_the_report_says_what_the_ranking_did(census):
    rows, _agenda = census
    report = census_report(rows)
    assert report["work_units"] == len(rows)
    assert report["units_with_a_signal"] > 0
    assert report["top"] and "why" in report["top"][0]
