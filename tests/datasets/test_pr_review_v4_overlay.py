"""The overlay join must not editorialise, and gold must not leak through the viewer.

Three properties are load-bearing and each has already been wrong once during development:

**The state ladder is a max, not an overwrite.** A cell aggregates several investigations,
candidates and findings. If a later low state could overwrite an earlier high one, a site
that produced a published finding would render as grey depending on iteration order.

**A multi-site claim credits one site.** Findings name several change targets — PR 33057's
build-failure finding names eight, PR 33294's five findings name 72 further targets between
them. Painting all of them as claims reported "claim emitted 72" on a PR with zero
candidates, so non-primary targets get their own `touched` state.

**`include_gold=False` must not open the gold files.** The `input/` vs `gold/` release split
is a physical leak barrier. A viewer that reads gold and then hides it in CSS has broken it
while looking correct.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from src.mathlib_review.analysis import review_overlay

from src.mathlib_review.analysis import review_overlay_html
from src.mathlib_review.analysis.review_overlay import (
    STATE_RANK,
    STATES,
    Cell,
    Column,
    base_columns,
    deepest,
)


def test_state_ladder_is_total_and_ordered():
    assert set(review_overlay.STATE_LABEL) == set(STATES)
    assert set(review_overlay_html.PALETTE) == set(STATES)
    assert STATE_RANK["unscheduled"] == 0
    # Everything the ladder calls a result must outrank "we never looked".
    for state in ("unsupported", "silent", "touched", "candidate", "finding"):
        assert STATE_RANK[state] > STATE_RANK["unscheduled"]
    # A surviving candidate must not be masked by a refuted sibling at the same site.
    assert STATE_RANK["candidate"] > STATE_RANK["contradicted"]
    # Scope spillover must rank below any actual claim about the site.
    assert STATE_RANK["silent"] < STATE_RANK["touched"] < STATE_RANK["contradicted"]


def test_raise_to_never_lowers_a_cell():
    cell = Cell(component="lint_norm.v1", arm="checker")
    cell.raise_to("finding", "published")
    cell.raise_to("unsupported", "no implementation")
    assert cell.state == "finding"
    assert cell.reason == "published"


def test_deepest_ignores_unknown_states():
    assert deepest("silent", "finding", "unsupported") == "finding"
    assert deepest("unscheduled") == "unscheduled"


def test_ledger_terminal_stages_all_map_onto_the_ladder():
    for stage, state in review_overlay.LEDGER_STATE.items():
        assert state in STATES, stage


def test_every_palette_entry_is_a_hex_triplet_per_theme():
    import re

    for state, values in review_overlay_html.PALETTE.items():
        assert len(values) == 6, state
        for value in values:
            assert re.fullmatch(r"#[0-9a-f]{6}", value), (state, value)


def test_columns_are_grouped_by_arm_in_order():
    arms = [column.arm for column in base_columns()]
    # `_matrix` builds header colspans from consecutive runs of the same arm, so an arm
    # appearing twice would fragment the header and misalign every cell after it.
    assert arms == sorted(arms, key=review_overlay.ARM_ORDER.index)


def test_site_label_distinguishes_non_declaration_targets():
    class Target:
        declaration_name = None
        declaration_kind = None
        kind = "module_doc"

    # The obvious fallback was the file basename, which gave PR 33098 nine identical rows.
    assert review_overlay._site_label(Target()) == "‹module doc›"
    Target.declaration_name = "Metric.minimalCover"
    assert review_overlay._site_label(Target()) == "Metric.minimalCover"


def test_visible_text_is_unwrapped_not_stringified():
    class Text:
        text = "feat: minimal covers"
        omission_reason = None

    assert review_overlay._visible(Text(), "fallback") == "feat: minimal covers"
    Text.text = None
    Text.omission_reason = "post_edit_risk"
    assert "post_edit_risk" in review_overlay._visible(Text(), "PR #1")
    assert review_overlay._visible(None, "PR #1") == "PR #1"


def test_pretty_diff_drops_difflibs_empty_file_headers():
    class Target:
        base_code = "a\nb\n"
        reviewed_code = "a\nc\n"

    diff, added, removed = review_overlay._pretty_diff(Target())
    assert not diff.startswith("---")
    assert "+++" not in diff
    assert (added, removed) == (1, 1)
    assert "+c" in diff and "-b" in diff


def test_frozen_roots_are_refused_as_output():
    # An overlay is a regenerable view. Writing it under a frozen root makes every render
    # fail `verify_frozen`'s unsealed-file check, which is a confusing way to learn this.
    from src.mathlib_review.release.verify_frozen import FROZEN_ROOTS

    empty = review_overlay.Overlay(version="t", sources={}, prs=[], gold=None)
    for root in FROZEN_ROOTS:
        with pytest.raises(SystemExit):
            review_overlay.write_overlay(empty, root / "overlays" / "x")
    assert not str(review_overlay.DEFAULT_OUT).startswith("results/pr_review_v4")


def test_blob_cannot_terminate_the_script_tag():
    payload = review_overlay_html._blob("X", {"claim": "see </script> below"})
    assert "</script>" not in payload
    assert "<\\/script>" in payload


# --- the real corpus, when it is present -------------------------------------------

RELEASE = review_overlay.DEFAULT_RELEASE
TREATMENT = review_overlay.DEFAULT_TREATMENT
EXECUTOR = review_overlay.DEFAULT_EXECUTOR
requires_corpus = pytest.mark.skipif(
    not (RELEASE / "input" / "episodes.jsonl").is_file(),
    reason="medium release not present",
)


@pytest.fixture(scope="module")
def medium():
    return review_overlay.build_overlay(
        RELEASE,
        treatment=TREATMENT if TREATMENT.is_dir() else None,
        executor=EXECUTOR if EXECUTOR.is_dir() else None,
        pr_numbers=[33057, 33294],
    )


@requires_corpus
def test_multi_site_finding_credits_only_its_primary_target(medium):
    findings = Path("results/pr_review_v4/conditions/medium-checker-only-v2/findings.jsonl")
    if not findings.is_file():
        pytest.skip("checker condition not present")
    built = review_overlay.build_overlay(
        RELEASE,
        treatment=TREATMENT,
        executor=EXECUTOR,
        conditions=[findings.parent],
        pr_numbers=[33057],
    )
    bundle = built.prs[0]
    states = [cell.state for site in bundle.sites for cell in site.cells.values()]
    # One finding names eight targets; exactly one of them may read as a finding.
    assert states.count("finding") == 1
    assert states.count("touched") == 7


@requires_corpus
def test_gold_off_opens_no_gold_file(monkeypatch):
    opened = []
    real = Path.read_text

    def spy(self, *args, **kwargs):
        opened.append(str(self))
        return real(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", spy)
    built = review_overlay.build_overlay(
        RELEASE, treatment=TREATMENT, include_gold=False, pr_numbers=[33057]
    )
    assert built.gold is None
    assert not [path for path in opened if "/gold/" in path]


@requires_corpus
def test_gold_page_carries_only_its_own_pr(medium):
    built = review_overlay.build_overlay(RELEASE, include_gold=True, pr_numbers=[33057, 33294])
    page = review_overlay_html.to_html(built.prs[0], built.gold, built.sources)
    other = {
        row["obligation_id"]
        for rows in built.gold["by_change"].values()
        for row in rows
        if row["pr_number"] != built.prs[0].pr_number
    }
    assert not [item for item in other if item in page]


@requires_corpus
def test_no_gold_page_contains_no_gold_data(medium):
    built = review_overlay.build_overlay(RELEASE, include_gold=False, pr_numbers=[33057])
    page = review_overlay_html.to_html(built.prs[0], None, built.sources)
    assert "const GOLD=null;" in page
    assert 'id="goldbtn"' not in page


@requires_corpus
def test_distinct_obligation_count_is_not_a_site_product(medium):
    built = review_overlay.build_overlay(RELEASE, include_gold=True)
    counts = review_overlay_html._distinct_obligations(built.gold)
    total = len({item for ids in counts.values() for item in ids})
    # Medium's gold is 43 obligations, 40 of them scoring-eligible. Summing `by_change`
    # rows instead counted (obligation x site) pairs and reported 61 for a 4-ask PR.
    assert total == 43


@requires_corpus
def test_absent_arms_render_as_empty_columns_not_missing_ones(medium):
    for bundle in medium.prs:
        ids = [column["id"] for column in bundle.columns]
        assert "generalist" in ids
        assert "spec:proof_golf" in ids
        assert "spec:file_coherence" in ids
        for site in bundle.sites:
            assert set(site.cells) >= set(ids)


@requires_corpus
def test_degrades_without_treatment_or_executor():
    built = review_overlay.build_overlay(RELEASE, pr_numbers=[33098])
    bundle = built.prs[0]
    assert bundle.sites
    assert all(
        cell.state == "unscheduled" for site in bundle.sites for cell in site.cells.values()
    )
    # The page must still build, and must still say what it does not know.
    page = review_overlay_html.to_html(bundle, built.gold, built.sources)
    assert "review overlay" in page


@requires_corpus
def test_sites_are_ordered_by_file_then_line(medium):
    for bundle in medium.prs:
        keys = [(site.path, site.line_start) for site in bundle.sites]
        by_file = {}
        for path, line in keys:
            by_file.setdefault(path, []).append(line)
        for path, lines in by_file.items():
            assert lines == sorted(lines), path
        # A file's rows must be contiguous, or the file group header lies about its span.
        paths = [path for path, _ in keys]
        assert len(set(paths)) == len([
            index for index, path in enumerate(paths) if index == 0 or paths[index - 1] != path
        ])


# --- the diff pane: sources, windows, routing, bands ---------------------------------

@requires_corpus
def test_reviewed_sources_reconstruct_byte_exact():
    """The pane's line numbers are only meaningful if the reconstruction is the real file."""

    from src.mathlib_review.release.change_graph import parse_unified_diff
    from src.mathlib_review.io import sha256_bytes
    from src.mathlib_review.schema import ChangeGraph, ReviewEpisodeInput

    episodes = {
        item.pr_number: item
        for item in review_overlay.load_jsonl(RELEASE / "input" / "episodes.jsonl", ReviewEpisodeInput)
    }
    graphs = review_overlay.load_jsonl(RELEASE / "derived" / "change_graphs.jsonl", ChangeGraph)
    checked = 0
    for graph in graphs:
        sources = review_overlay._reviewed_sources(
            episodes[graph.pr_number], graph, review_overlay.WORKSPACE_ROOT
        )
        for coverage in graph.file_coverage:
            entry = sources.get(coverage.path)
            if not entry or entry["status"] != "full":
                continue
            text = "\n".join(entry["lines"])
            digest = sha256_bytes((text + "\n").encode("utf-8"))
            assert digest == coverage.reviewed_source_sha256, coverage.path
            checked += 1
    assert checked >= 80, f"expected the medium corpus to reconstruct, got {checked}"


@requires_corpus
def test_windows_account_for_every_line():
    """Shown plus elided must equal the file. An elision that does not count is a lie about
    where the reader is in the file, which is the one thing the pane exists to get right."""

    built = review_overlay.build_overlay(RELEASE, treatment=TREATMENT, include_gold=False)
    for bundle in built.prs:
        for meta in bundle.files:
            if meta["context"] != "full":
                continue
            shown = sum(len(window["lines"]) for window in meta["windows"])
            elided = sum(window["elided_before"] for window in meta["windows"])
            assert shown + elided == meta["reviewed_lines"], meta["path"]
            # Every target must be visible, or its header has no anchor in the flow.
            spans = {
                site.change_id: (site.line_start, site.line_end)
                for site in bundle.sites if site.path == meta["path"] and site.line_start
            }
            covered = {n for window in meta["windows"] for n in range(window["start"],
                                                                     window["end"] + 1)}
            for change_id, (start, _end) in spans.items():
                assert start in covered, (meta["path"], change_id)


@requires_corpus
def test_windowing_actually_elides_a_large_file():
    """PR 33321's `Mathlib.lean` is 7,444 lines carrying one import target. Shipping it whole
    is what the windowing exists to prevent."""

    built = review_overlay.build_overlay(RELEASE, treatment=TREATMENT, include_gold=False,
                                      pr_numbers=[33321])
    root = [f for f in built.prs[0].files if f["path"] == "Mathlib.lean"][0]
    assert root["reviewed_lines"] > 7000
    assert sum(len(w["lines"]) for w in root["windows"]) < 200


@requires_corpus
def test_routing_reproduces_the_real_schedule():
    """The explainer recomputes `method_applies`; if it drifted from the scheduler it would
    be confidently describing a decision the pipeline never made."""

    import collections

    tasks = collections.defaultdict(set)
    for task in review_overlay.load_jsonl(
        TREATMENT / "derived" / "investigation_tasks.jsonl",
        review_overlay.InvestigationTask,
    ):
        tasks[task.primary_change_id].add(task.method_id)

    built = review_overlay.build_overlay(RELEASE, treatment=TREATMENT, include_gold=False)
    counts, zero = collections.Counter(), []
    for bundle in built.prs:
        for site in bundle.sites:
            derived = {row["method_id"] for row in site.routing if row["scheduled"]}
            assert derived == tasks.get(site.change_id, set()), site.change_id
            counts[len(derived)] += 1
            if not derived:
                zero.append(site.lifecycle)
    assert counts == {0: 19, 1: 43, 2: 75, 3: 90, 5: 77, 6: 23, 7: 181}
    # Nothing handles removals, which is why those 19 are never looked at.
    assert set(zero) == {"removed"}


@requires_corpus
def test_every_unscheduled_method_names_a_failing_predicate():
    built = review_overlay.build_overlay(RELEASE, treatment=TREATMENT, include_gold=False,
                                      pr_numbers=[33098, 33294])
    for bundle in built.prs:
        for site in bundle.sites:
            for row in site.routing:
                assert bool(row["failed"]) != row["scheduled"], (site.change_id, row)


@requires_corpus
def test_bands_come_from_the_release_not_the_task_field():
    """`InvestigationTask.work_unit_id` carries `dev-medium-0.1.0` ids, which share 0 of 225
    with the 0.3.0 release. Banding on them would draw nothing at all."""

    from src.mathlib_review.schema import ReviewWorkUnit

    release_units = {
        unit.work_unit_id: set(unit.change_ids)
        for unit in review_overlay.load_jsonl(
            RELEASE / "derived" / "work_units.jsonl", ReviewWorkUnit
        )
    }
    task_units = {
        task.work_unit_id
        for task in review_overlay.load_jsonl(
            TREATMENT / "derived" / "investigation_tasks.jsonl", review_overlay.InvestigationTask
        )
    }
    assert not (task_units & set(release_units)), "lineage assumption changed; recheck bands"

    built = review_overlay.build_overlay(RELEASE, treatment=TREATMENT, include_gold=False)
    for bundle in built.prs:
        for band in bundle.work_units:
            assert band["work_unit_id"] in release_units
            assert set(band["change_ids"]) <= release_units[band["work_unit_id"]]


@requires_corpus
def test_added_lines_exclude_hunk_context():
    """Marking a hunk's extent rather than its body painted 23 unchanged lines of PR 33098's
    module doc as additions."""

    from src.mathlib_review.schema import ChangeGraph, ReviewEpisodeInput

    episode = [
        item for item in review_overlay.load_jsonl(
            RELEASE / "input" / "episodes.jsonl", ReviewEpisodeInput)
        if item.pr_number == 33098
    ][0]
    graph = [
        item for item in review_overlay.load_jsonl(
            RELEASE / "derived" / "change_graphs.jsonl", ChangeGraph)
        if item.pr_number == 33098
    ][0]
    source = review_overlay._reviewed_sources(episode, graph, review_overlay.WORKSPACE_ROOT)
    entry = source["Mathlib/Topology/MetricSpace/CoveringNumbers.lean"]
    added = entry["added_lines"]
    # The first hunk starts at 29 but only rewrites from 32 onward.
    assert 29 not in added and 32 in added
    for line in added:
        assert 1 <= line <= len(entry["lines"])


@requires_corpus
def test_missing_workspace_degrades_without_failing():
    built = review_overlay.build_overlay(
        RELEASE, treatment=TREATMENT, include_gold=False, pr_numbers=[33098],
        workspace_root=Path("/nonexistent-workspace-root"),
    )
    bundle = built.prs[0]
    assert bundle.files[0]["context"] == "unavailable"
    assert bundle.files[0]["windows"] == []
    assert len(bundle.sites) == 26
    page = review_overlay_html.to_html(bundle, None, built.sources)
    assert "Full source unavailable" in page
    assert page.count('class="th') == 26


@requires_corpus
def test_relations_are_symmetric_and_evidence_backed():
    built = review_overlay.build_overlay(RELEASE, treatment=TREATMENT, include_gold=False,
                                      pr_numbers=[33098])
    bundle = built.prs[0]
    assert bundle.relations
    by_change = {site.change_id: site for site in bundle.sites}
    for edge in bundle.relations:
        assert edge["evidence"], edge["relation_id"]
        # Both ends must be able to show the edge, or selecting one silently loses it.
        assert any(r["change_id"] == edge["target"] for r in by_change[edge["source"]].related)
        assert any(r["change_id"] == edge["source"] for r in by_change[edge["target"]].related)


@requires_corpus
def test_call_budget_compares_like_with_like():
    """`total_chars` pays for the system prompt on every call, so the single-call
    counterfactual has to include it once or the comparison is rigged."""

    built = review_overlay.build_overlay(RELEASE, treatment=TREATMENT, include_gold=False,
                                      pr_numbers=[33098, 33149])
    for bundle in built.prs:
        budget = bundle.call_budget
        assert budget["measured"]
        assert budget["single_call_is_counterfactual"] is True
        assert budget["single_call_chars"] > len(bundle.sites)
        assert budget["largest_call_chars"] <= budget["total_chars"]
    # Decomposition costs more here; the page must not be able to claim otherwise.
    assert all(b.call_budget["overhead_ratio"] > 1 for b in built.prs)


@requires_corpus
def test_method_applicability_ships_once_not_per_site():
    built = review_overlay.build_overlay(RELEASE, treatment=TREATMENT, include_gold=False,
                                      pr_numbers=[33294])
    bundle = built.prs[0]
    assert bundle.methods and len(bundle.methods) == 7
    for site in bundle.sites:
        for row in site.routing:
            assert "wants_components" not in row


# --- the v5 lead path -----------------------------------------------------------------

V5_RUN = Path("results/pr_review_v5/runs/pr_review_v5_lead_medium_heldout_rep1")
requires_v5 = pytest.mark.skipif(
    not (V5_RUN / "delegations.jsonl").is_file(), reason="held-out v5 run not present"
)


@pytest.fixture(scope="module")
def v5():
    return review_overlay.build_overlay(
        RELEASE, treatment=TREATMENT, executor=EXECUTOR,
        conditions=[V5_RUN], include_gold=False, pr_numbers=[33145],
    )


@requires_v5
def test_v5_run_drops_v4_furniture(v5):
    """A v5 page must not describe the deterministic executor, which took no part in it."""

    bundle = v5.prs[0]
    ids = {column["id"] for column in bundle.columns}
    assert not [item for item in ids if item.endswith(".v1")], ids
    assert "generalist" in ids and "proof_golf" in ids
    # The funnel is v5's, not `capability_assessed` / `operator_unavailable`.
    labels = [stage["label"] for stage in bundle.stages]
    assert labels[:3] == ["Review sites", "Proposed", "Delegated"]
    markup = review_overlay_html.to_html(bundle, None, v5.sources).split("<script>")[0]
    for banned in ("capability_assessed", "reason_code", "unsupported_shape",
                   "operator_completed", "terminal_reason"):
        assert banned not in markup, banned


@requires_v5
def test_pruned_proposals_are_visible_as_a_decision(v5):
    """`unscheduled` and `declined` must not look alike: one is nobody's decision."""

    bundle = v5.prs[0]
    states = [cell.state for site in bundle.sites for cell in site.cells.values()]
    assert states.count("pruned") > 0
    assert STATE_RANK["pruned"] > STATE_RANK["unscheduled"]
    declined = [job for job in bundle.lead["delegations"] if job["disposition"] == "pruned"]
    ran = [job for job in bundle.lead["delegations"] if job["disposition"] != "pruned"]
    assert len(declined) + len(ran) == len(bundle.lead["delegations"])
    assert declined and all(job["site_change_ids"] for job in declined)


@requires_v5
def test_lead_pane_reports_the_corrected_cost(v5):
    page = review_overlay_html.to_html(v5.prs[0], None, v5.sources)
    assert "What the lead was given" in page
    assert "What the lead declined" in page
    # The lead's own cost is a scalar, not the bucket dict. Passing the dict raised
    # "unsupported format string passed to dict.__format__" once, so pin the rendered shape.
    assert "{'lead'" not in page and "__format__" not in page
    assert re.search(r"lead \$\d+\.\d{4}, floor \$\d+\.\d{4}", page)
    cost = v5.sources["run_cost"]
    assert round(cost["actual_total"], 2) == 21.06
    assert round(cost["manifest_total"], 2) == 6.54


@requires_v5
def test_conversations_are_sibling_pages_not_embedded(v5):
    """PR 33149's transcripts alone are 3.9 MB; embedding would make every page pay."""

    bundle = v5.prs[0]
    pages = review_overlay_html.conversation_pages(bundle)
    assert pages, "expected transcripts for a run with an extracted sidecar"
    page = review_overlay_html.to_html(bundle, None, v5.sources)
    assert 'href="conv/' in page
    # The turn bodies must not be in the overlay payload.
    assert '"conversations"' not in page
    one = next(iter(pages.values()))
    assert "back to the overlay" in one and "<title>" in one


@requires_v5
def test_ids_are_behind_the_debug_toggle(v5):
    page = review_overlay_html.to_html(v5.prs[0], None, v5.sources)
    markup = page.split("<script>")[0]
    assert ".onlydebug{display:none}" in page
    assert "body.debug .onlydebug{display:revert}" in page
    assert 'id="debugbtn"' in page and "explain mode" not in page
    # `data-id` attributes carry ids because selection needs them, and are never shown. What
    # must stay behind the toggle is id *text*, so strip attributes before looking.
    # `class` is deliberately kept: it carries the `onlydebug` marker this looks for.
    text_only = re.sub(r'\s(?:data-[\w-]+|title|href|id)="[^"]*"', "", markup)
    for token in re.findall(r"(?:change|wu):[0-9a-f]{8}", text_only):
        index = text_only.index(token)
        assert "onlydebug" in text_only[max(0, index - 300):index], token


@requires_v5
def test_v4_page_is_unaffected_by_the_v5_path():
    built = review_overlay.build_overlay(
        RELEASE, treatment=TREATMENT, executor=EXECUTOR, include_gold=False,
        pr_numbers=[33098],
    )
    bundle = built.prs[0]
    assert bundle.lead is None
    assert built.cost is None
    ids = {column["id"] for column in bundle.columns}
    assert "baseline_failure.v1" in ids
    assert [stage["label"] for stage in bundle.stages][:2] == ["Review sites", "Scheduled"]


@requires_v5
def test_v5_sites_keep_their_inventory_classification(v5):
    """Suppressing v4's treatment on a v5 run must not take the diff's own classification.

    The modification inventory says what each target *is* — added public theorem, which
    components changed. It is not executor machinery, and dropping it with the rest left
    every site on PR 33117 reading "unknown unknown".
    """

    bundle = v5.prs[0]
    assert bundle.sites
    assert {site.lifecycle for site in bundle.sites} != {"unknown"}
    assert {site.subject_kind for site in bundle.sites} != {"unknown"}
    assert all(site.component_deltas for site in bundle.sites)


@requires_v5
def test_claims_are_shown_only_at_the_site_they_are_about(v5):
    """An arm answers per work unit, and a unit holds several targets.

    Attaching the whole claim list to every target in the unit put 59 of PR 33117's 71
    claims under a declaration they were not about.
    """

    bundle = v5.prs[0]
    strays = 0
    for change_id, blocks in bundle.transcripts.items():
        for block in blocks:
            for job in block.get("delegations", []):
                for claim in job.get("claims", []):
                    if claim.get("primary_change_id") != change_id:
                        strays += 1
    assert strays == 0
    # Siblings are counted, not silently dropped.
    assert any(
        job.get("claims_elsewhere")
        for blocks in bundle.transcripts.values()
        for block in blocks
        for job in block.get("delegations", [])
    )


@requires_v5
def test_no_finding_lands_outside_the_drawn_axis(v5):
    """v4 names a focused column `spec:<id>`; v5 names its arms bare.

    A v5 specialist finding mapped to `spec:proof_idiom` landed in a column the page never
    draws, so it vanished from both the strip and the matrix.
    """

    bundle = v5.prs[0]
    axis = {column["id"] for column in bundle.columns}
    for site in bundle.sites:
        assert set(site.cells) <= axis, set(site.cells) - axis


@requires_v5
def test_a_site_reads_silent_when_its_arm_spoke_about_a_sibling(v5):
    """`candidate` must mean "said something here", not "said something in this call"."""

    bundle = v5.prs[0]
    for site in bundle.sites:
        for column_id, cell in site.cells.items():
            if cell.state != "candidate":
                continue
            blocks = [b for b in bundle.transcripts.get(site.change_id, [])
                      if b["component"] == column_id]
            assert any(job.get("claims") for block in blocks
                       for job in block.get("delegations", [])) or cell.finding_ids
