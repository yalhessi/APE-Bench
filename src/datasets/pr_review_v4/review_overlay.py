"""Join one PR's whole review into a single UI-ready bundle.

Reading what the reviewer did to a PR currently means hand-joining eight JSONL files by
ID. The pipeline is wide — 16 medium PRs decompose into 508 modifications, 2,041 scheduled
investigations and 2,253 capability assessments, which yield 42 opportunities and 39
findings — and that shape is exactly what a table of totals hides. The interesting fact is
not the totals but *where* the attrition happens relative to the diff: the system is
scheduled at nearly every gold site and says the wrong thing there.

So the unit of display is the **change target** — the review site, `change:<sha>`, one
changed declaration with complete `base_code` and `reviewed_code`. `change_id` is the
anchor currency for gold, investigations, candidates and findings alike, and it is stable
across releases (verified: candidates produced against `dev-medium-0.1.0` join 30/30 onto
`dev-medium-0.3.0` targets), which is what makes a cross-artifact join possible at all.

This module is pure data: it produces a `Overlay` of per-PR bundles and nothing else.
`review_overlay_html` renders it. The split is deliberate — `bundle.json` is useful on its own
for ad-hoc analysis, and a rendering bug should never be able to corrupt the join.

Every input except the release is optional. An absent arm produces *present-but-empty*
columns rather than vanishing, because a silently omitted arm reads exactly like an arm
that found nothing.
"""

from __future__ import annotations

import argparse
import difflib
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from src.datasets.pr_review_v5.delegation_view import (
    is_v5_run,
    load_lead_views,
    load_turns,
    run_cost,
)

from . import paths
from .digest import digest_findings
from .io import display_path, load_jsonl, load_jsonl_optional
from .schema import (
    CandidateClaim,
    CapabilityAssessment,
    ChangeGraph,
    EvidenceArtifact,
    EvidencePacket,
    InterventionView,
    InvestigationMethod,
    InvestigationRecord,
    InvestigationTask,
    JudgmentNode,
    ModificationRecord,
    OperatorRun,
    PRRelation,
    RelationEvidence,
    RenderedPrompt,
    ReviewEpisodeInput,
    ReviewFinding,
    ReviewOpportunity,
    ReviewWorkUnit,
    SemanticMatch,
)

OVERLAY_VERSION = "review-overlay/1"

DEFAULT_RELEASE = paths.RELEASES / "dev-medium-0.3.0"
#: v3, not v2. The medium executor ledger keys on v3's investigation IDs (2,253/2,253
#: overlap); against v2's schedule the join is empty, which would render every checker cell
#: as unscheduled and look like the arm was never run.
DEFAULT_TREATMENT = paths.TREATMENTS / "systematic-opportunities-v3-medium"
DEFAULT_EXECUTOR = paths.AUDITS / "phase10-medium-executor-v5"


# --- The column axis -----------------------------------------------------------------

@dataclass(frozen=True)
class Column:
    """One component that can speak about a site: a matrix column."""

    id: str
    arm: str
    label: str


#: Checker-arm methods, in the order the matrix shows them. Taken from the frozen method
#: registry rather than inferred, so a method that produced nothing on this corpus still
#: gets a column and reads as silent instead of absent.
CHECKER_METHODS = (
    ("baseline_failure.v1", "baseline"),
    ("canonical_api_search.v1", "canonical API"),
    ("wrapper_composition.v1", "wrapper"),
    ("naming_contrast.v1", "naming contrast"),
    ("naming_norm.v1", "naming norm"),
    ("lint_norm.v1", "lint"),
    ("repository_policy.v1", "policy"),
)

#: `focused_specs.py` builds exactly these four.
FOCUSED_SPECS = (
    ("proof_golf", "golf"),
    ("proof_idiom", "idiom"),
    ("duplication", "duplication"),
    ("generality", "generality"),
)

#: The file-scoped generalist's spec id. It is a spec in the plumbing sense only; reading
#: "has a spec_id" as "is focused" would file this arm under the arm it is compared with.
FILE_COHERENCE_SPEC = "file_coherence"

GENERALIST_COLUMN = "generalist"


#: Left-to-right arm order in the matrix header.
ARM_ORDER = ("checker", "generalist", "focused", "file_scoped")


def v5_columns(lead_views) -> List[Column]:
    """The arms this run actually enumerated, in agenda order.

    A v5 page used to show v4's seven deterministic method columns and their funnel stages
    as "context" for a run they had no part in. The arms are the components that spoke here,
    so they are the axis; `generalist` leads because the mandatory floor makes it the one
    column that is populated at every site.
    """

    seen: Dict[str, str] = {}
    for view in lead_views.values():
        for row in view.arms:
            seen.setdefault(row["arm_id"], "generalist" if row["mandatory"] else "focused")
    ordered = sorted(seen.items(), key=lambda item: (item[1] != "generalist", item[0]))
    return [
        Column(arm_id, arm, arm_id.replace("_", " "))
        for arm_id, arm in ordered
    ]


def base_columns() -> List[Column]:
    columns = [Column(mid, "checker", label) for mid, label in CHECKER_METHODS]
    columns.append(Column(GENERALIST_COLUMN, "generalist", "generalist"))
    columns += [Column(f"spec:{sid}", "focused", label) for sid, label in FOCUSED_SPECS]
    columns.append(Column(f"spec:{FILE_COHERENCE_SPEC}", "file_scoped", "file coherence"))
    return columns


_FIXED_IDS = frozenset(column.id for column in base_columns())


# --- The state ladder ----------------------------------------------------------------

#: How far a component got at a site. Ordered: within a cell the deepest state wins, and
#: the stage scrubber dims everything below the selected stage's floor.
#:
#: `silent` is load-bearing and must never collapse into `unscheduled`. "We did not check"
#: and "we checked and found nothing" are different results, and only the second one is
#: evidence about the reviewer. `contradicted` sits below `opportunity` so that one
#: surviving candidate at a site is not masked by a refuted sibling.
#:
#: `pruned` is v5's: the agenda enumerated this (arm, site) pair and the lead declined it.
#: It outranks `unscheduled` because a decision not to look is a result, and it is the only
#: honest way to show what the lead left alone — 927 of the held-out run's 1,166 proposals,
#: and every specialist at 323 of its 432 sites.
#:
#: `touched` exists because findings are multi-site: PR 33294's five findings name 72
#: further targets between them. Colouring those as `candidate` made a PR with zero
#: candidates report "claim emitted 72" — the same colour for "a reviewer said something
#: here" and "something said elsewhere lists this line".
STATES = (
    "unscheduled",
    "pruned",
    "unsupported",
    "unavailable",
    "silent",
    "touched",
    "contradicted",
    "opportunity",
    "candidate",
    "finding",
)
STATE_RANK = {state: index for index, state in enumerate(STATES)}

STATE_LABEL = {
    "unscheduled": "not scheduled here",
    "pruned": "proposed, declined by the lead",
    "unsupported": "scheduled, no implementation",
    "unavailable": "operator could not run",
    "silent": "checked, found nothing",
    "touched": "named by a claim anchored elsewhere",
    "contradicted": "claimed, evidence refuted it",
    "opportunity": "transformation constructed",
    "candidate": "claim emitted",
    "finding": "published finding",
}

#: Terminal stages the executor ledger records, mapped onto the ladder.
LEDGER_STATE = {
    "scheduled": "unsupported",
    "capability_assessed": "unsupported",
    "operator_unavailable": "unavailable",
    "operator_completed": "silent",
    "technical_check_completed": "silent",
    "transformation_constructed": "opportunity",
    "worthiness_decided": "opportunity",
    "candidate_emitted": "candidate",
    "finding_selected": "finding",
}


def deepest(*states: str) -> str:
    return max(states, key=lambda state: STATE_RANK.get(state, 0))


@dataclass
class Cell:
    """What one component did at one site."""

    component: str
    arm: str
    state: str = "unscheduled"
    reason: str = ""
    investigation_ids: List[str] = field(default_factory=list)
    opportunity_ids: List[str] = field(default_factory=list)
    candidate_ids: List[str] = field(default_factory=list)
    finding_ids: List[str] = field(default_factory=list)

    def raise_to(self, state: str, reason: str = "") -> None:
        if STATE_RANK.get(state, 0) >= STATE_RANK.get(self.state, 0):
            self.state = state
            if reason:
                self.reason = reason


@dataclass
class Site:
    """One `ChangeTarget`, with everything the UI needs to draw it."""

    change_id: str
    path: str
    declaration_name: str
    declaration_kind: str
    kind: str
    parse_status: str
    line_start: int
    line_end: int
    unified_diff: str
    added: int
    removed: int
    # Inventory (`ModificationRecord`); empty when the treatment did not classify it.
    lifecycle: str = "unknown"
    subject_kind: str = "unknown"
    visibility: str = "unknown"
    classification_status: str = ""
    component_deltas: List[dict] = field(default_factory=list)
    work_unit_ids: List[str] = field(default_factory=list)
    cells: Dict[str, Cell] = field(default_factory=dict)
    depth: str = "unscheduled"
    #: Which changed ranges this target covers. The relation is many-to-many in both
    #: directions — PR 33149 has one range feeding 108 targets, PR 33294 has one target
    #: spanning 15 ranges — so the browser needs the explicit list to draw either edge.
    changed_range_ids: List[str] = field(default_factory=list)
    #: Per method: did it fire here, and if not, which predicate rejected it.
    routing: List[dict] = field(default_factory=list)
    #: `related_change_ids` of this site's investigations, each flagged cross-unit or not.
    related: List[dict] = field(default_factory=list)


@dataclass
class PRBundle:
    pr_number: int
    episode_id: str
    repo: str
    title: str
    description: str
    #: `source_current_value_unverified` means the title was read after the review window,
    #: so it is shown but flagged rather than presented as review-time input.
    title_provenance: str
    base_sha: str
    reviewed_head_sha: str
    round_index: int
    files: List[dict]
    sites: List[Site]
    columns: List[dict]
    stages: List[dict]
    transcripts: Dict[str, List[dict]]
    totals: Dict[str, int]
    #: One entry per changed range, so the diff pane can map a hunk to its targets.
    ranges: List[dict] = field(default_factory=list)
    #: Method applicability vocabularies, shipped once rather than per site.
    methods: List[dict] = field(default_factory=list)
    #: Typed, evidence-cited edges between changed declarations in this PR.
    relations: List[dict] = field(default_factory=list)
    #: The work units this PR's targets were packed into, with true call sizes.
    work_units: List[dict] = field(default_factory=list)
    #: Scheduled-vs-single-call size comparison. Bounded, not cheaper -- see `_call_sizes`.
    call_budget: Dict[str, object] = field(default_factory=dict)
    #: The v5 lead's routing for this PR, when the run is a v5 one. `None` for v4.
    lead: Optional[dict] = None
    #: Transcripts for this PR, keyed by conversation id. Rendered to sibling pages, never
    #: embedded: the held-out run's PR 33149 shard alone is 3.9 MB.
    conversations: Dict[str, List[dict]] = field(default_factory=dict)


@dataclass
class Overlay:
    version: str
    sources: Dict[str, object]
    prs: List[PRBundle]
    gold: Optional[Dict[str, dict]]
    #: Whole-run spend by bucket, against what the manifest claims. v5 runs only.
    cost: Optional[Dict[str, object]] = None


# --- Loading -------------------------------------------------------------------------

def _visible(field, fallback: str) -> str:
    """Unwrap a `VisibleText`.

    It is a model, not a string: `str()` on it yields its field dump, which is how the PR
    title first rendered as `text='...' provenance='...' omission_reason=None`. The text can
    legitimately be absent, in which case `omission_reason` says why.
    """

    if field is None:
        return fallback
    if field.text:
        return field.text
    return f"{fallback} — title unavailable ({field.omission_reason or 'no reason given'})"


def _pretty_diff(target) -> Tuple[str, int, int]:
    """Render one target as a unified diff of its complete base and reviewed regions.

    `diff_fragments` carries the raw `@@` blocks, but those are hunk-shaped: a fragment can
    straddle two declarations, and the whole point of a target is that it is not a
    fragment. Diffing the two complete regions keeps the site self-contained.
    """

    base = (target.base_code or "").splitlines()
    reviewed = (target.reviewed_code or "").splitlines()
    lines = list(difflib.unified_diff(base, reviewed, lineterm="", n=3))
    added = sum(1 for line in lines if line.startswith("+") and not line.startswith("+++"))
    removed = sum(1 for line in lines if line.startswith("-") and not line.startswith("---"))
    # `unified_diff` emits `--- ` / `+++ ` headers even with no file names given, which
    # renders as two blank coloured rows above every diff. The path is already in the panel
    # header, so drop them.
    if lines[:1] and lines[0].startswith("---"):
        lines = lines[2:] if lines[1:] and lines[1].startswith("+++") else lines[1:]
    if not lines:
        # Identical regions: the target is context pulled in by a neighbouring range.
        lines = [" " + line for line in reviewed[:40]]
    return "\n".join(lines), added, removed


def _span(target, ranges_by_id, entities_by_id) -> Tuple[int, int]:
    """Where in the reviewed file this target sits, for diff-order sorting.

    Prefer the target's own semantic entity span. Range spans are far coarser: PR 33098's
    26 targets share 4 changed ranges, so ordering by range would stamp 231 on nine
    consecutive rows and leave their order arbitrary.
    """

    starts, ends = [], []
    for entity_id in target.reviewed_entity_ids or target.base_entity_ids:
        entity = entities_by_id.get(entity_id)
        if entity is not None:
            starts.append(entity.span.line_start)
            ends.append(entity.span.line_end)
    if starts:
        return min(starts), max(ends)
    for range_id in target.changed_range_ids:
        changed = ranges_by_id.get(range_id)
        if changed is None:
            continue
        span = changed.reviewed_span or changed.old_span
        if span is not None:
            starts.append(span.line_start)
            ends.append(span.line_end)
    return (min(starts) if starts else 0, max(ends) if ends else 0)


def _site_label(target) -> str:
    """A row label that distinguishes non-declaration targets from each other.

    `declaration_name` is None for imports, module docs, namespaces and bare commands. The
    file's basename was the obvious fallback and the wrong one: PR 33098 has nine such
    targets in one file, which produced nine identically labelled rows.
    """

    if target.declaration_name:
        return target.declaration_name
    kind = (target.declaration_kind or target.kind).replace("_", " ")
    return f"‹{kind}›"


# --- The PR itself: sources, windows, hunks ------------------------------------------

#: Where full base-side Lean sources live. The release stores only `*_source_sha256`
#: digests; the reviewed text is never persisted at all — `change_graph.py` derives it in
#: memory. So the diff pane reconstructs it the same way the builder did.
WORKSPACE_ROOT = Path("data/code_execute/repos/mathlib4/workspaces")
BLOB_CACHE_ROOT = Path("data/pr_review_v4/cache/base_files")

#: Lines of real context around each hunk. Enough to see the surrounding declaration
#: without shipping whole files: PR 33321's `Mathlib.lean` is 7,444 lines carrying a single
#: import target, and PR 33294 is 6,477 lines across 11 files.
WINDOW_CONTEXT = 12


def _read_base(base_sha: str, path: str, workspace_root: Path) -> Optional[str]:
    """Base-side source, workspace first then blob cache — the builder's own precedence."""

    for root in (workspace_root / base_sha, BLOB_CACHE_ROOT / base_sha):
        candidate = root / path
        if candidate.is_file():
            try:
                return candidate.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                return None
    return None


def _reviewed_sources(episode, graph, workspace_root: Path) -> Dict[str, dict]:
    """Reconstruct each changed file's reviewed text.

    Returns `path -> {"lines": [...], "base_lines": n, "hunks": [...], "status": ...}`.
    A file we cannot rebuild gets `status="unavailable"` and no lines: the pane then falls
    back to the target's own diff fragment. Never raises — a missing workspace must degrade
    the picture, not fail the build.
    """

    from .change_graph import apply_file_patch, parse_unified_diff

    try:
        diff_files = {item.path: item for item in parse_unified_diff(episode.diff)}
    except Exception:  # noqa: BLE001 - a malformed diff costs the pane, not the page
        return {}

    out: Dict[str, dict] = {}
    for path, diff_file in diff_files.items():
        hunks = [
            {
                "old_start": hunk.old_start, "old_lines": hunk.old_lines,
                "new_start": hunk.new_start, "new_lines": hunk.new_lines,
                "header": hunk.header,
            }
            for hunk in diff_file.hunks
        ]
        base = _read_base(graph.base_sha or "", diff_file.old_path or path, workspace_root)
        if base is None and diff_file.status == "added":
            base = ""
        entry = {
            "hunks": hunks, "status": "unavailable", "lines": [], "base_lines": 0,
            "added_lines": _added_lines(diff_file.hunks),
        }
        if base is not None:
            try:
                reviewed = apply_file_patch(base, diff_file)
            except Exception:  # noqa: BLE001 - `apply_file_patch` validates context lines
                entry["status"] = "patch_mismatch"
            else:
                entry["lines"] = reviewed.splitlines()
                entry["base_lines"] = len(base.splitlines())
                entry["status"] = "full"
        out[path] = entry
    return out


def _added_lines(diff_hunks) -> set:
    """Reviewed-side line numbers this diff actually added.

    Walking the hunk body, not its extent. A hunk's `new_start .. new_start+new_lines` span
    includes its context lines, so marking the extent painted 23 unchanged lines of PR
    33098's module doc as additions — the pane would be asserting a change that is not there.
    """

    marked = set()
    for hunk in diff_hunks:
        line = hunk.new_start
        for body in hunk.lines:
            marker = body[:1]
            if marker == "-":
                continue
            if marker == "+":
                marked.add(line)
            line += 1
    return marked


def _windows(source: dict, spans: Sequence[Tuple[int, int]]) -> List[dict]:
    """Merge (hunk ± context) and every target span into non-overlapping windows.

    The elision between windows is reported as a line count so the pane can say
    "173 unchanged lines" rather than silently jumping — position has to stay honest when
    the body is not the whole file.
    """

    lines = source["lines"]
    if not lines:
        return []
    total = len(lines)
    wanted: List[Tuple[int, int]] = []
    for hunk in source["hunks"]:
        start = max(1, hunk["new_start"] - WINDOW_CONTEXT)
        end = min(total, hunk["new_start"] + max(hunk["new_lines"], 1) - 1 + WINDOW_CONTEXT)
        wanted.append((start, end))
    for start, end in spans:
        if start:
            wanted.append((max(1, start), min(total, max(end, start))))
    if not wanted:
        return []

    merged: List[List[int]] = []
    for start, end in sorted(wanted):
        if merged and start <= merged[-1][1] + 1:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])

    changed = source.get("added_lines", set())
    windows, cursor = [], 1
    for start, end in merged:
        windows.append({
            "start": start,
            "end": end,
            "elided_before": start - cursor,
            "lines": [
                {"n": n, "changed": n in changed, "text": lines[n - 1]}
                for n in range(start, end + 1)
            ],
        })
        cursor = end + 1
    if cursor <= total:
        windows.append({"start": total + 1, "end": total, "elided_before": total - cursor + 1,
                        "lines": []})
    return windows


# --- Why this method fired here ------------------------------------------------------

#: The four predicates of `investigations.method_applies`, named for display. Recomputing
#: them here rather than storing a verdict is deliberate: the derived schedule is asserted
#: against `investigation_tasks.jsonl`, so a drift in either direction fails loudly.
_PREDICATES = (
    ("subject_kind", "subject_kinds"),
    ("lifecycle", "lifecycles"),
    ("visibility", "visibilities"),
)


def method_applicability(methods) -> List[dict]:
    """What each method declares it applies to. Constant per method, so it ships once.

    Carrying it on every site instead cost 313 KB on PR 33294 alone — 119 sites x 7 methods
    repeating the same three vocabularies.
    """

    return [
        {
            "method_id": method.method_id,
            "subject_kinds": sorted(method.applies_when.subject_kinds),
            "lifecycles": sorted(method.applies_when.lifecycles),
            "visibilities": sorted(method.applies_when.visibilities),
            "components": sorted(method.applies_when.any_changed_components),
        }
        for method in methods
    ]


def _routing(modification, methods) -> List[dict]:
    """Per method: did it fire at this target, and if not, which predicate rejected it."""

    if modification is None:
        return []
    changed = {
        item.component for item in modification.component_deltas
        if item.status != "unchanged"
    }
    rows = []
    for method in methods:
        applies = method.applies_when
        failed = [
            name for name, attribute in _PREDICATES
            if getattr(modification, name) not in getattr(applies, attribute)
        ]
        overlap = changed & set(applies.any_changed_components)
        if not overlap:
            failed.append("changed_components")
        rows.append({
            "method_id": method.method_id,
            "scheduled": not failed,
            "failed": failed,
            "matched_components": sorted(overlap),
        })
    return rows


# --- What each call actually cost ----------------------------------------------------

def _call_sizes(prompts: Sequence[RenderedPrompt]) -> Dict[str, int]:
    """True prompt size per work unit, measured from the stored prompt text.

    Not `RenderedPrompt.rendered_chars`: `render_prompts.py` computes that as
    `len(SYSTEM_PROMPT) + len(user)` while `user` already embeds the system prompt, so the
    system text is counted twice (~8.6% over across the medium set), and renderer `/12` adds
    the `/11` constant besides. The stored `system_prompt`/`user_prompt` strings are exact.
    """

    return {
        prompt.work_unit_id: len(prompt.system_prompt) + len(prompt.user_prompt)
        for prompt in prompts
    }

def _load_ledger(executor: Optional[Path]) -> Dict[str, dict]:
    """`pipeline_ledger.jsonl` has no pydantic model; it is written as plain dicts."""

    if executor is None:
        return {}
    path = executor / "pipeline_ledger.jsonl"
    if not path.is_file():
        return {}
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    return {row["investigation_id"]: row for row in rows}


def _resolve_run_release(run_dir: Path) -> Optional[Path]:
    """Find the release a model run was generated against.

    Work unit IDs are content-addressed on the work unit and so move between releases
    (`dev-medium-0.1.0` and `0.3.0` share none of their 225), while change IDs do not. To
    learn which *sites* an invocation covered — including the ones it stayed silent about —
    the run's own release has to supply the work-unit-to-change-id map.
    """

    plan_path = run_dir / "run_plan.json"
    if not plan_path.is_file():
        return None
    try:
        manifest = json.loads(plan_path.read_text()).get("dataset_manifest_path")
    except (OSError, json.JSONDecodeError):
        return None
    if not manifest:
        return None
    release = Path(manifest).parent
    return release if (release / "derived" / "work_units.jsonl").is_file() else None


@dataclass
class RunArm:
    """One model-arm run, resolved to the sites it actually invoked."""

    name: str
    candidates: List[CandidateClaim]
    packets: Dict[str, EvidencePacket]
    artifacts: Dict[str, List[EvidenceArtifact]]
    invoked_change_ids: set
    responses: Dict[str, dict]
    unresolved_coverage: bool


def _load_run(run_dir: Path) -> RunArm:
    candidates = load_jsonl_optional(run_dir / "candidates.jsonl", CandidateClaim)
    packets = load_jsonl_optional(run_dir / "evidence" / "packets.jsonl", EvidencePacket)
    artifacts = load_jsonl_optional(run_dir / "evidence" / "artifacts.jsonl", EvidenceArtifact)

    responses: Dict[str, dict] = {}
    response_path = run_dir / "candidate_responses.jsonl"
    if response_path.is_file():
        for line in response_path.read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                responses[row["work_unit_id"]] = row

    invoked: set = set()
    unresolved = bool(responses)
    release = _resolve_run_release(run_dir)
    if release is not None:
        units = load_jsonl(release / "derived" / "work_units.jsonl", ReviewWorkUnit)
        by_id = {unit.work_unit_id: unit for unit in units}
        for work_unit_id in responses:
            unit = by_id.get(work_unit_id)
            if unit is not None:
                invoked.update(unit.change_ids)
        unresolved = bool(responses) and not invoked
    # Candidates always prove their own site was invoked, whatever the release said.
    for candidate in candidates:
        invoked.update(candidate.change_ids)

    by_candidate: Dict[str, List[EvidenceArtifact]] = defaultdict(list)
    for artifact in artifacts:
        by_candidate[artifact.candidate_id].append(artifact)

    return RunArm(
        name=run_dir.name,
        candidates=candidates,
        packets={packet.candidate_id: packet for packet in packets},
        artifacts=dict(by_candidate),
        invoked_change_ids=invoked,
        responses=responses,
        unresolved_coverage=unresolved,
    )


def _candidate_column(candidate: CandidateClaim) -> str:
    if candidate.spec_id:
        return f"spec:{candidate.spec_id}"
    return GENERALIST_COLUMN


def _finding_columns(finding: ReviewFinding) -> List[str]:
    """Which columns a finding belongs to, read off its sources rather than its arm.

    `arm` alone cannot place a merged finding, and a focused finding's spec is only on the
    source. Findings with no usable source fall back to the generalist column so that they
    appear somewhere rather than being dropped.
    """

    columns = []
    for source in finding.sources:
        if source.method_id:
            columns.append(source.method_id)
        elif source.spec_id:
            columns.append(f"spec:{source.spec_id}")
        elif source.arm in ("generalist", "holistic"):
            columns.append(GENERALIST_COLUMN)
        elif source.arm == "file_generalist":
            columns.append(f"spec:{FILE_COHERENCE_SPEC}")
    return columns or [GENERALIST_COLUMN]


# --- The join ------------------------------------------------------------------------

def build_overlay(
    release: Path,
    *,
    treatment: Optional[Path] = None,
    executor: Optional[Path] = None,
    runs: Sequence[Path] = (),
    conditions: Sequence[Path] = (),
    judge: Optional[Path] = None,
    include_gold: bool = True,
    pr_numbers: Optional[Iterable[int]] = None,
    workspace_root: Path = WORKSPACE_ROOT,
) -> Overlay:
    wanted = set(pr_numbers) if pr_numbers else None

    # v5 first: its arms, funnel and ledger describe a different pipeline, and loading v4's
    # treatment would add seven deterministic method columns and their `capability_assessed`
    # stages to a page about a run they took no part in.
    lead_views: Dict[int, object] = {}
    v5_dir: Optional[Path] = None
    for condition in conditions:
        if is_v5_run(condition):
            v5_dir = condition
            lead_views.update(load_lead_views(condition))
    if v5_dir is not None:
        treatment = executor = None

    episodes = load_jsonl(release / "input" / "episodes.jsonl", ReviewEpisodeInput)
    graphs = load_jsonl(release / "derived" / "change_graphs.jsonl", ChangeGraph)
    work_units = load_jsonl_optional(release / "derived" / "work_units.jsonl", ReviewWorkUnit)
    prompts = load_jsonl_optional(
        release / "derived" / "rendered_prompts.jsonl", RenderedPrompt
    )

    if wanted:
        episodes = [item for item in episodes if item.pr_number in wanted]
        graphs = [item for item in graphs if item.pr_number in wanted]

    modifications: List[ModificationRecord] = []
    tasks: List[InvestigationTask] = []
    assessments: List[CapabilityAssessment] = []
    methods: List[InvestigationMethod] = []
    relations: List[PRRelation] = []
    # `RelationEvidence` carries no `relation_id`; the edge points at it through
    # `PRRelation.evidence_artifact_ids`, which resolves 1005/1005 on the medium treatment.
    evidence_by_id: Dict[str, RelationEvidence] = {}
    if treatment is not None:
        methods = load_jsonl_optional(treatment / "methods.jsonl", InvestigationMethod)
        methods.sort(key=lambda item: item.method_id)
        derived = treatment / "derived"
        modifications = load_jsonl_optional(
            derived / "modification_inventory.jsonl", ModificationRecord
        )
        tasks = load_jsonl_optional(derived / "investigation_tasks.jsonl", InvestigationTask)
        assessments = load_jsonl_optional(
            derived / "capability_assessments.jsonl", CapabilityAssessment
        )
        relations = load_jsonl_optional(derived / "pr_relations.jsonl", PRRelation)
        evidence_by_id = {
            item.evidence_id: item
            for item in load_jsonl_optional(
                derived / "relation_evidence.jsonl", RelationEvidence
            )
        }

    ledger = _load_ledger(executor)
    records: List[InvestigationRecord] = []
    operator_runs: List[OperatorRun] = []
    opportunities: List[ReviewOpportunity] = []
    if executor is not None:
        records = load_jsonl_optional(
            executor / "investigation_records.jsonl", InvestigationRecord
        )
        operator_runs = load_jsonl_optional(executor / "operator_runs.jsonl", OperatorRun)
        opportunities = load_jsonl_optional(executor / "opportunities.jsonl", ReviewOpportunity)

    arms = [_load_run(run) for run in runs]

    findings: Dict[str, ReviewFinding] = {}
    finding_conditions: Dict[str, List[str]] = defaultdict(list)
    for condition in conditions:
        for finding in load_jsonl_optional(condition / "findings.jsonl", ReviewFinding):
            findings[finding.finding_id] = finding
            finding_conditions[finding.finding_id].append(condition.name)
    issues, _digest_report = digest_findings(findings.values()) if findings else ([], {})
    issue_of_finding = {
        finding_id: issue.issue_id for issue in issues for finding_id in issue.finding_ids
    }
    issue_by_id = {issue.issue_id: issue for issue in issues}

    matches: List[SemanticMatch] = []
    if judge is not None:
        matches = load_jsonl_optional(judge / "matches.jsonl", SemanticMatch)

    # --- indices ---------------------------------------------------------------------
    modification_by_change = {item.primary_change_id: item for item in modifications}
    task_by_id = {item.investigation_id: item for item in tasks}
    assessments_by_investigation: Dict[str, List[CapabilityAssessment]] = defaultdict(list)
    for assessment in assessments:
        assessments_by_investigation[assessment.investigation_id].append(assessment)
    record_by_investigation = {item.investigation_id: item for item in records}
    runs_by_investigation: Dict[str, List[OperatorRun]] = defaultdict(list)
    for run in operator_runs:
        runs_by_investigation[run.investigation_id].append(run)
    opportunities_by_investigation: Dict[str, List[ReviewOpportunity]] = defaultdict(list)
    for opportunity in opportunities:
        opportunities_by_investigation[opportunity.investigation_id].append(opportunity)

    units_by_change: Dict[str, List[str]] = defaultdict(list)
    for unit in work_units:
        for change_id in unit.change_ids:
            units_by_change[change_id].append(unit.work_unit_id)
    prompt_specs = {
        prompt.work_unit_id: prompt.spec_id for prompt in prompts if prompt.spec_id
    }
    call_chars = _call_sizes(prompts)
    system_chars = max((len(prompt.system_prompt) for prompt in prompts), default=0)
    # Bands come from the release's own work units. `InvestigationTask.work_unit_id` looks
    # like it would do, and does not: the v3 treatment's tasks carry `dev-medium-0.1.0` unit
    # ids, which share 0 of 225 with `dev-medium-0.3.0` because unit ids hash the renderer
    # version. Banding on the task field would silently draw nothing.
    units_by_pr: Dict[int, List[ReviewWorkUnit]] = defaultdict(list)
    for unit in work_units:
        units_by_pr[unit.pr_number].append(unit)
    relations_by_pr: Dict[int, List[PRRelation]] = defaultdict(list)
    for relation in relations:
        relations_by_pr[relation.pr_number].append(relation)

    episode_by_pr = {episode.pr_number: episode for episode in episodes}

    # Columns for anything the corpus contains that the fixed axis does not name — a method
    # added to the registry must not vanish from the matrix. They join their own arm group
    # rather than being appended at the end, or the header's colspans fragment and a checker
    # method ends up sitting past the model arms.
    if lead_views:
        columns = v5_columns(lead_views)
    else:
        columns = base_columns()
    known = {column.id for column in columns}
    extras: List[Column] = []
    for task in (() if lead_views else tasks):
        if task.method_id not in known:
            extras.append(Column(task.method_id, "checker", task.method_id))
            known.add(task.method_id)
    for arm in arms:
        for candidate in arm.candidates:
            column_id = _candidate_column(candidate)
            if column_id not in known:
                extras.append(Column(column_id, "focused", column_id.split(":", 1)[-1]))
                known.add(column_id)
    if extras:
        order = {arm: index for index, arm in enumerate(ARM_ORDER)}
        columns = sorted(
            columns + extras,
            key=lambda column: (order.get(column.arm, len(order)), column.id not in _FIXED_IDS),
        )

    bundles = []
    for graph in sorted(graphs, key=lambda item: item.pr_number):
        episode = episode_by_pr.get(graph.pr_number)
        if episode is None:
            continue
        bundles.append(
            _build_pr(
                graph=graph,
                episode=episode,
                columns=columns,
                modification_by_change=modification_by_change,
                tasks=[t for t in tasks if t.pr_number == graph.pr_number],
                task_by_id=task_by_id,
                assessments_by_investigation=assessments_by_investigation,
                ledger=ledger,
                record_by_investigation=record_by_investigation,
                runs_by_investigation=runs_by_investigation,
                opportunities_by_investigation=opportunities_by_investigation,
                arms=arms,
                findings=findings,
                finding_conditions=finding_conditions,
                issue_of_finding=issue_of_finding,
                issue_by_id=issue_by_id,
                units_by_change=units_by_change,
                prompt_specs=prompt_specs,
                methods=methods,
                episode_sources=_reviewed_sources(episode, graph, workspace_root),
                work_units=units_by_pr.get(graph.pr_number, []),
                call_chars=call_chars,
                system_chars=system_chars,
                relations=relations_by_pr.get(graph.pr_number, []),
                evidence_by_id=evidence_by_id,
                lead_view=lead_views.get(graph.pr_number),
                v5_dir=v5_dir,
            )
        )

    gold = None
    if include_gold:
        gold = _build_gold(release, bundles, arms, findings, matches)

    sources = {
        "release": display_path(release),
        "treatment": display_path(treatment) if treatment else None,
        "executor": display_path(executor) if executor else None,
        "runs": [display_path(run) for run in runs],
        "conditions": [display_path(condition) for condition in conditions],
        "judge": display_path(judge) if judge else None,
        "gold": bool(include_gold),
        "unresolved_run_coverage": [arm.name for arm in arms if arm.unresolved_coverage],
        "run_cost": run_cost(v5_dir, lead_views) if v5_dir else None,
    }
    return Overlay(
        version=OVERLAY_VERSION, sources=sources, prs=bundles, gold=gold,
        cost=run_cost(v5_dir, lead_views) if v5_dir else None,
    )


def _build_pr(
    *,
    graph: ChangeGraph,
    episode: ReviewEpisodeInput,
    columns: Sequence[Column],
    modification_by_change,
    tasks: Sequence[InvestigationTask],
    task_by_id,
    assessments_by_investigation,
    ledger,
    record_by_investigation,
    runs_by_investigation,
    opportunities_by_investigation,
    arms: Sequence[RunArm],
    findings: Dict[str, ReviewFinding],
    finding_conditions,
    issue_of_finding,
    issue_by_id,
    units_by_change,
    prompt_specs,
    methods: Sequence[InvestigationMethod] = (),
    episode_sources: Optional[Dict[str, dict]] = None,
    work_units: Sequence[ReviewWorkUnit] = (),
    call_chars: Optional[Dict[str, int]] = None,
    system_chars: int = 0,
    relations: Sequence[PRRelation] = (),
    evidence_by_id: Optional[Dict[str, object]] = None,
    lead_view=None,
    v5_dir: Optional[Path] = None,
) -> PRBundle:
    episode_sources = episode_sources or {}
    call_chars = call_chars or {}
    evidence_by_id = evidence_by_id or {}
    ranges_by_id = {item.range_id: item for item in graph.changed_ranges}
    entities_by_id = {item.entity_id: item for item in graph.entities}
    file_order = {
        coverage.path: index
        for index, coverage in enumerate(sorted(graph.file_coverage, key=lambda c: c.path))
    }

    sites: Dict[str, Site] = {}
    for target in graph.targets:
        diff, added, removed = _pretty_diff(target)
        line_start, line_end = _span(target, ranges_by_id, entities_by_id)
        site = Site(
            change_id=target.change_id,
            path=target.path,
            declaration_name=_site_label(target),
            declaration_kind=target.declaration_kind or target.kind,
            kind=target.kind,
            parse_status=target.parse_status,
            line_start=line_start,
            line_end=line_end,
            unified_diff=diff,
            added=added,
            removed=removed,
            work_unit_ids=units_by_change.get(target.change_id, []),
            changed_range_ids=list(target.changed_range_ids),
        )
        modification = modification_by_change.get(target.change_id)
        site.routing = _routing(modification, methods)
        if modification is not None:
            site.lifecycle = modification.lifecycle
            site.subject_kind = modification.subject_kind
            site.visibility = modification.visibility
            site.classification_status = modification.classification_status
            site.component_deltas = [
                {"component": item.component, "status": item.status}
                for item in modification.component_deltas
                if item.status != "unchanged"
            ]
        for column in columns:
            site.cells[column.id] = Cell(component=column.id, arm=column.arm)
        sites[target.change_id] = site

    transcripts: Dict[str, List[dict]] = defaultdict(list)
    blocks: Dict[Tuple[str, str], dict] = {}

    def block(change_id: str, column_id: str) -> Optional[dict]:
        """Get (creating on first use) the transcript block for one cell."""

        site = sites.get(change_id)
        if site is None:
            return None
        key = (change_id, column_id)
        if key not in blocks:
            cell = site.cells.setdefault(
                column_id, Cell(component=column_id, arm="checker")
            )
            entry = {
                "component": column_id,
                "arm": cell.arm,
                "investigations": [],
                "delegations": [],
                "candidates": [],
                "findings": [],
            }
            blocks[key] = entry
            transcripts[change_id].append(entry)
        return blocks[key]

    # --- checker arm -----------------------------------------------------------------
    for task in tasks:
        site = sites.get(task.primary_change_id)
        if site is None:
            continue
        cell = site.cells.setdefault(
            task.method_id, Cell(component=task.method_id, arm="checker")
        )
        cell.investigation_ids.append(task.investigation_id)

        row = ledger.get(task.investigation_id)
        record = record_by_investigation.get(task.investigation_id)
        found = opportunities_by_investigation.get(task.investigation_id, [])

        if row is not None:
            state = LEDGER_STATE.get(row.get("terminal_stage", ""), "unsupported")
            cell.raise_to(state, row.get("terminal_reason", "") or "")
        elif record is not None:
            cell.raise_to(
                "opportunity" if record.opportunity_ids else "silent", record.basis
            )
        else:
            # Scheduled, but no execution artifact reached us at all.
            cell.raise_to("unsupported", "no execution record for this investigation")
        cell.opportunity_ids += [item.opportunity_id for item in found]

        entry = block(task.primary_change_id, task.method_id)
        entry["investigations"].append({
            "investigation_id": task.investigation_id,
            "method_id": task.method_id,
            "expected_operators": task.expected_operators,
            "related_change_ids": task.related_change_ids,
            "terminal_stage": (row or {}).get("terminal_stage"),
            "terminal_reason": (row or {}).get("terminal_reason"),
            "disposition": record.disposition if record else None,
            "basis": record.basis if record else None,
            "assessments": [
                {
                    "implementation_id": item.implementation_id,
                    "status": item.status,
                    "reason_code": item.reason_code,
                }
                for item in assessments_by_investigation.get(task.investigation_id, [])
            ],
            "operator_runs": [
                {
                    "operator": item.operator,
                    "status": item.status,
                    "result_count": item.result_count,
                    "failure_reason": item.failure_reason,
                }
                for item in runs_by_investigation.get(task.investigation_id, [])
            ],
            "opportunities": [
                {
                    "opportunity_id": item.opportunity_id,
                    "observed_pattern": item.observed_pattern,
                    "transformation": (
                        {
                            "kind": item.proposed_transformation.kind,
                            "description": item.proposed_transformation.description,
                            "symbols": item.proposed_transformation.symbols,
                        }
                        if item.proposed_transformation
                        else None
                    ),
                    "discovery_rank": item.discovery_rank,
                    "discovery_score": item.discovery_score,
                }
                for item in found
            ],
        })

    # --- v5 delegations ---------------------------------------------------------------
    # Every enumerated (arm, site) pair gets a cell, including the declined ones. A pruned
    # proposal is the lead's decision and has to be visible; leaving it `unscheduled` would
    # make "the agenda offered this and the lead said no" indistinguishable from "nobody ever
    # considered it".
    if lead_view is not None:
        for job in lead_view.delegations:
            ran = job.disposition in ("mandatory", "proposed", "agent_added")
            if ran:
                state = "silent" if not job.candidate_count else "candidate"
                reason = (
                    f"{job.disposition} · {job.tier or 'tier?'} · "
                    f"{job.candidate_count or 0} claim(s)"
                )
            else:
                state = "pruned"
                reason = job.reason or "not selected by the lead"
            for change_id in job.site_change_ids:
                site = sites.get(change_id)
                if site is None:
                    continue
                cell = site.cells.setdefault(
                    job.arm_id, Cell(component=job.arm_id, arm="generalist")
                )
                cell.raise_to(state, reason)
                if ran:
                    cell.investigation_ids.append(job.invocation_id)
                entry = block(change_id, job.arm_id)
                entry["delegations"].append({
                    "invocation_id": job.invocation_id,
                    "arm_id": job.arm_id,
                    "disposition": job.disposition,
                    "reason": job.reason,
                    "brief": job.brief,
                    "tier": job.tier,
                    "budget_cap": job.budget_cap,
                    "status": job.status,
                    "cost": job.cost,
                    "execution_time": job.execution_time,
                    "turns": job.turns,
                    "tool_calls": job.tool_calls,
                    "candidate_count": job.candidate_count,
                    "has_transcript": job.has_transcript,
                    "claims": job.claims,
                })

    # --- model arms ------------------------------------------------------------------
    invoked_columns: Dict[str, set] = defaultdict(set)
    for arm in arms:
        # A work unit the run responded to marks every site in it as *checked*, whether or
        # not the model said anything there. That is the only way a model arm's silence
        # becomes visible; without it silence is indistinguishable from not being asked.
        for change_id in arm.invoked_change_ids:
            site = sites.get(change_id)
            if site is None:
                continue
            spec_ids = {
                prompt_specs[work_unit_id]
                for work_unit_id in site.work_unit_ids
                if work_unit_id in prompt_specs
            }
            targets = (
                [f"spec:{spec_id}" for spec_id in sorted(spec_ids)]
                if spec_ids
                else [GENERALIST_COLUMN]
            )
            for column_id in targets:
                invoked_columns[change_id].add(column_id)
                cell = site.cells.setdefault(
                    column_id, Cell(component=column_id, arm="generalist")
                )
                cell.raise_to("silent", "invoked, made no claim at this site")

        for candidate in arm.candidates:
            column_id = _candidate_column(candidate)
            packet = arm.packets.get(candidate.candidate_id)
            state = "candidate"
            reason = f"{candidate.concern_family}: {candidate.concern_label}"
            if packet is not None and packet.status == "contradicted":
                state = "contradicted"
                reason = "evidence contradicted the claim"
            primary = candidate.primary_change_id or (
                candidate.change_ids[0] if candidate.change_ids else None
            )
            for change_id in candidate.change_ids:
                site = sites.get(change_id)
                if site is None:
                    continue
                cell = site.cells.setdefault(
                    column_id, Cell(component=column_id, arm="generalist")
                )
                cell.candidate_ids.append(candidate.candidate_id)
                if change_id == primary:
                    cell.raise_to(state, reason)
                else:
                    cell.raise_to("touched", "named by a candidate anchored elsewhere")
                entry = block(change_id, column_id)
                entry["candidates"].append({
                    "candidate_id": candidate.candidate_id,
                    "run": arm.name,
                    "primary": change_id == primary,
                    "concern_family": candidate.concern_family,
                    "concern_label": candidate.concern_label,
                    "issue_kind": candidate.issue_kind,
                    "severity": candidate.severity,
                    "claim": candidate.claim,
                    "requested_change": candidate.requested_change,
                    "suggested_fix": candidate.suggested_fix,
                    "model_confidence": candidate.model_confidence,
                    "proposed_edit": (
                        candidate.proposed_edit.model_dump(mode="json")
                        if candidate.proposed_edit
                        else None
                    ),
                    "packet": (
                        {
                            "status": packet.status,
                            "requested_collectors": packet.requested_collectors,
                            "completed_collectors": packet.completed_collectors,
                            "terminal_failures": packet.terminal_failures,
                        }
                        if packet
                        else None
                    ),
                    "artifacts": [
                        {
                            "collector": item.collector,
                            "kind": item.kind,
                            "polarity": item.polarity,
                            "source_ref": item.source_ref,
                            "content": item.content[:1200],
                        }
                        for item in arm.artifacts.get(candidate.candidate_id, [])
                    ],
                })

    # --- findings --------------------------------------------------------------------
    pr_findings = [item for item in findings.values() if item.pr_number == graph.pr_number]
    for finding in pr_findings:
        issue_id = issue_of_finding.get(finding.finding_id)
        issue = issue_by_id.get(issue_id) if issue_id else None
        for change_id in finding.change_ids:
            site = sites.get(change_id)
            if site is None:
                continue
            primary = change_id == finding.primary_change_id
            for column_id in _finding_columns(finding):
                cell = site.cells.setdefault(
                    column_id, Cell(component=column_id, arm="checker")
                )
                cell.finding_ids.append(finding.finding_id)
                # A single build-failure finding names eight targets. Crediting all of them
                # at full weight paints a whole file as reviewed, so only the primary
                # target gets the `finding` state; the rest read as `touched`.
                cell.raise_to(
                    "finding" if primary else "touched",
                    finding.action_key if primary else "named by a finding anchored elsewhere",
                )
                entry = block(change_id, column_id)
                entry["findings"].append({
                    "finding_id": finding.finding_id,
                    "primary": primary,
                    "arm": finding.arm,
                    "admission": finding.admission,
                    "admission_reason": finding.admission_reason,
                    "concern_family": finding.concern_family,
                    "issue_kind": finding.issue_kind,
                    "severity": finding.severity,
                    "claim": finding.claim,
                    "requested_change": finding.requested_change,
                    "evidence_tier": finding.evidence_tier,
                    "action_key": finding.action_key,
                    "site_count": len(finding.change_ids),
                    "conditions": finding_conditions.get(finding.finding_id, []),
                    "issue_id": issue_id,
                    "issue_admission": issue.admission if issue else None,
                    "issue_aggregation": issue.aggregation if issue else None,
                    "issue_site_count": issue.site_count if issue else None,
                })

    for site in sites.values():
        site.depth = deepest(*(cell.state for cell in site.cells.values()), "unscheduled")

    ordered = sorted(
        sites.values(),
        key=lambda item: (file_order.get(item.path, 999), item.line_start, item.declaration_name),
    )

    # Ordering the file list by first appearance in `ordered` keeps the rail, the diff pane
    # and the matrix in one sequence; sorting by path alone would desynchronise them.
    file_rank = {}
    for index, site in enumerate(ordered):
        file_rank.setdefault(site.path, index)
    files = []
    for coverage in sorted(graph.file_coverage,
                           key=lambda c: (file_rank.get(c.path, 1 << 30), c.path)):
        source = episode_sources.get(coverage.path, {})
        file_sites = [site for site in ordered if site.path == coverage.path]
        spans = [(site.line_start, site.line_end) for site in file_sites]
        units = sorted({unit for site in file_sites for unit in site.work_unit_ids})
        files.append({
            "path": coverage.path,
            "file_status": coverage.file_status,
            "source_status": coverage.source_status,
            "exclusion_reason": coverage.exclusion_reason,
            "sites": len(file_sites),
            "change_ids": [site.change_id for site in file_sites],
            # True reviewed line count. The rail's strip is proportional to this, so it must
            # come from the reconstructed source: hunk extents run a median 0.41 of true
            # length, and 0.01 on PR 33421's import-only edits.
            "reviewed_lines": len(source.get("lines", [])),
            "base_lines": source.get("base_lines", 0),
            "context": source.get("status", "unavailable"),
            "hunks": source.get("hunks", []),
            "windows": _windows(source, spans) if source.get("lines") else [],
            "added": sum(site.added for site in file_sites),
            "removed": sum(site.removed for site in file_sites),
            "work_unit_ids": units,
            "range_ids": sorted({
                range_id for site in file_sites for range_id in site.changed_range_ids
            }),
        })

    ranges = [
        {
            "range_id": item.range_id,
            "path": item.path,
            "hunk_index": item.hunk_index,
            "range_index": item.range_index,
            "change_kind": item.change_kind,
            "old_span": (
                [item.old_span.line_start, item.old_span.line_end] if item.old_span else None
            ),
            "reviewed_span": (
                [item.reviewed_span.line_start, item.reviewed_span.line_end]
                if item.reviewed_span else None
            ),
            "change_ids": sorted(
                site.change_id for site in ordered if item.range_id in site.changed_range_ids
            ),
        }
        for item in sorted(graph.changed_ranges, key=lambda r: (r.path, r.range_index))
    ]

    unit_rows = [
        {
            "work_unit_id": unit.work_unit_id,
            "change_ids": [cid for cid in unit.change_ids if cid in sites],
            "path": next(
                (sites[cid].path for cid in unit.change_ids if cid in sites), ""
            ),
            "chars": call_chars.get(unit.work_unit_id, 0),
        }
        for unit in sorted(work_units, key=lambda u: u.work_unit_id)
    ]
    unit_rows = [row for row in unit_rows if row["change_ids"]]
    unit_rows.sort(key=lambda row: min(
        ordered.index(sites[cid]) for cid in row["change_ids"] if cid in sites
    ))

    # Relation edges, symmetric like the scheduler's own view of them, so selecting either
    # end of an edge shows it. `unit_of` decides the cross-unit flag: an edge leaving the
    # primary's work unit is exactly what a per-work-unit reviewer cannot see.
    unit_of = {
        change_id: site.work_unit_ids[0] if site.work_unit_ids else None
        for change_id, site in sites.items()
    }
    relation_rows = []
    for relation in relations:
        evidence = [
            evidence_by_id[item].content
            for item in relation.evidence_artifact_ids
            if item in evidence_by_id
        ]
        for related_id in relation.related_change_ids:
            if relation.source_change_id not in sites or related_id not in sites:
                continue
            relation_rows.append({
                "relation_id": relation.relation_id,
                "kind": relation.relation_kind,
                "source": relation.source_change_id,
                "target": related_id,
                "confidence": relation.confidence,
                "cross_unit": (
                    unit_of.get(relation.source_change_id) != unit_of.get(related_id)
                ),
                "evidence": evidence[:3],
            })

    related_by_change: Dict[str, List[dict]] = defaultdict(list)
    for row in relation_rows:
        for near, far in ((row["source"], row["target"]), (row["target"], row["source"])):
            related_by_change[near].append({
                "change_id": far,
                "kind": row["kind"],
                "cross_unit": row["cross_unit"],
                "confidence": row["confidence"],
                "evidence": row["evidence"],
            })
    for change_id, site in sites.items():
        seen, unique = set(), []
        for row in related_by_change.get(change_id, []):
            key = (row["change_id"], row["kind"])
            if key not in seen:
                seen.add(key)
                unique.append(row)
        site.related = unique

    stages = (
        _v5_stages(ordered, lead_view, pr_findings, issue_by_id, issue_of_finding)
        if lead_view is not None
        else _build_stages(ordered, tasks, ledger, arms, pr_findings, issue_by_id,
                           issue_of_finding)
    )
    totals = {
        "sites": len(ordered),
        "investigations": len(tasks),
        "candidates": sum(
            1
            for arm in arms
            for candidate in arm.candidates
            if candidate.pr_number == graph.pr_number
        ),
        "findings": len(pr_findings),
        "published": sum(
            1
            for issue in issue_by_id.values()
            if issue.pr_number == graph.pr_number and issue.admission == "published"
        ),
    }

    return PRBundle(
        pr_number=graph.pr_number,
        episode_id=graph.episode_id,
        repo=graph.repo,
        title=_visible(episode.title, f"PR #{graph.pr_number}"),
        description=_visible(episode.description, ""),
        title_provenance=episode.title.provenance,
        base_sha=graph.base_sha or "",
        reviewed_head_sha=graph.reviewed_head_sha or "",
        round_index=graph.round_index,
        files=files,
        sites=ordered,
        columns=[asdict(column) for column in columns],
        stages=stages,
        transcripts=dict(transcripts),
        totals=totals,
        ranges=ranges,
        methods=method_applicability(methods),
        relations=relation_rows,
        work_units=unit_rows,
        call_budget=_call_budget(unit_rows, graph, episode, system_chars),
        lead=_lead_payload(lead_view) if lead_view is not None else None,
        conversations=(
            load_turns(v5_dir, graph.pr_number) if (v5_dir and lead_view is not None) else {}
        ),
    )


def _call_budget(unit_rows, graph, episode, system_chars: int = 0) -> Dict[str, object]:
    """What the scheduling costs, stated honestly.

    It does not buy cheapness, and -- measured here rather than assumed -- it does not buy
    much bounding either. Across the medium set the scheduled arm spends 4.80M characters
    over 225 calls against 456k for whole-PR single calls: **10.5x more**, because packing
    repeats each file's diff and code into every unit that touches the file. PR 33149 is
    71.6x on its own, 108 calls for a PR whose entire content is 36.6k characters.

    The bounding argument is weak on this corpus: the largest scheduled call is 47.1k
    characters and the largest single call would be 106.1k (PR 33294) -- a 2.2x reduction in
    peak size, and *every* PR here fits in one call comfortably. An earlier framing claimed
    PR 33149 would be 2.03M characters as one call; that number came from concatenating its
    identical diff blob once per target, which is an artefact of the packer, not something a
    single-call harness would ever send.

    So what decomposition actually buys is **per-site attribution** -- 508 targets each
    carrying their own scheduled investigations and terminal state, which one call cannot
    produce. The page should say that, and should not claim a cost or context-window win.
    """

    sizes = [row["chars"] for row in unit_rows if row["chars"]]
    return {
        "calls": len(unit_rows),
        "total_chars": sum(sizes),
        "largest_call_chars": max(sizes) if sizes else 0,
        # One call carrying the same material once: the same system prompt, the diff, and
        # every target's two code regions. The system prompt has to be in here or the
        # comparison is rigged -- `total_chars` pays for it on every one of N calls.
        "single_call_chars": system_chars + len(episode.diff) + sum(
            len(target.base_code or "") + len(target.reviewed_code or "")
            for target in graph.targets
        ),
        #: No whole-PR-diff arm exists in the pipeline; this is a counterfactual, and the
        #: page must label it as one rather than as a measured baseline.
        "single_call_is_counterfactual": True,
        "measured": bool(sizes),
        "overhead_ratio": (
            round(sum(sizes) / single, 1)
            if (single := system_chars + len(episode.diff) + sum(
                len(target.base_code or "") + len(target.reviewed_code or "")
                for target in graph.targets)) else 0.0
        ),
    }

def _lead_payload(view) -> dict:
    """The lead view, flattened for the browser.

    Delegations are shipped whole because the lead pane lists all of them, declined
    included; on the busiest PR that is 40 rows, and on the run's largest, 109.
    """

    return {
        "pr_number": view.pr_number,
        "caps": view.caps,
        "arms": view.arms,
        "waves": view.waves,
        "coverage": view.coverage,
        # `cost` is the per-bucket split; `lead_cost` is the lead's own turns alone. Both
        # are needed and they are not the same number.
        "cost": view.cost,
        "lead_cost": view.lead_cost,
        "conversation_id": view.conversation_id,
        "started_at": view.started_at,
        "completed_at": view.completed_at,
        "execution_time": view.execution_time,
        "turns": view.lead_turns,
        "tool_calls": view.lead_tool_calls,
        "token_usage": view.lead_token_usage,
        "assessments": view.assessments,
        "has_transcript": view.has_transcript,
        "delegations": [asdict(job) for job in view.delegations],
    }

def _v5_stages(sites, view, pr_findings, issue_by_id, issue_of_finding) -> List[dict]:
    """v5's funnel: what the agenda offered, what the lead ran, what came back.

    Deliberately not v4's. `capability_assessed` and `operator_unavailable` are stages of a
    deterministic executor that took no part in a v5 run, and showing them made the page
    describe machinery that was not there.
    """

    ran = [job for job in view.delegations
           if job.disposition in ("mandatory", "proposed", "agent_added")]
    floor = sum(1 for job in ran if job.disposition == "mandatory")
    chosen = len(ran) - floor
    spoke = sum(1 for job in ran if job.candidate_count)
    claims = sum(job.candidate_count or 0 for job in ran)
    published = sum(
        1 for issue_id in {issue_of_finding.get(f.finding_id) for f in pr_findings}
        if issue_id and issue_by_id[issue_id].admission == "published"
    )
    coverage = view.coverage
    return [
        {"id": "sites", "label": "Review sites", "count": len(sites), "min_state": None,
         "note": "change targets in this PR's diff"},
        {"id": "proposed", "label": "Proposed", "count": len(view.delegations),
         "min_state": "pruned",
         "note": f"(arm x site) jobs the agenda enumerated"},
        {"id": "delegated", "label": "Delegated", "count": len(ran), "min_state": "silent",
         "note": f"{floor} mandatory floor, {chosen} chosen by the lead"},
        {"id": "spoke", "label": "Arms that spoke", "count": spoke, "min_state": "candidate",
         "note": f"{claims} claim(s) returned"},
        {"id": "finding", "label": "Findings", "count": len(pr_findings),
         "min_state": "finding", "note": "survived merge and adjudication"},
        {"id": "published", "label": "Published", "count": published, "min_state": "finding",
         "note": "issues a maintainer would be shown",
         "coverage": coverage,
         "top_reasons": [
             ("every specialist declined here",
              coverage.get("all_specialists_declined", 0)),
             ("declined (arm, site) pairs", coverage.get("declined_pairs", 0)),
         ]},
    ]

def _build_stages(sites, tasks, ledger, arms, pr_findings, issue_by_id, issue_of_finding):
    """The funnel ribbon: counts, attrition, and the floor each stage dims below.

    `min_state` is what makes the scrubber free — the page dims every cell whose state
    ranks below the selected stage rather than storing a separate colouring per stage.
    """

    rows = [ledger.get(task.investigation_id) for task in tasks]
    present = [row for row in rows if row]
    stage_counts = Counter(row.get("terminal_stage") for row in present)
    reasons = Counter(
        row.get("terminal_reason") for row in present if row.get("terminal_reason")
    )

    scheduled = len(tasks)
    ran = sum(
        1
        for row in present
        if LEDGER_STATE.get(row.get("terminal_stage", ""), "unsupported") != "unsupported"
    )
    constructed = sum(
        1
        for row in present
        if STATE_RANK[LEDGER_STATE.get(row.get("terminal_stage", ""), "unsupported")]
        >= STATE_RANK["opportunity"]
    )
    pr_numbers = {site.change_id for site in sites}
    candidates = sum(
        1
        for arm in arms
        for candidate in arm.candidates
        if set(candidate.change_ids) & pr_numbers
    )
    published = sum(
        1
        for issue_id in {issue_of_finding.get(f.finding_id) for f in pr_findings}
        if issue_id and issue_by_id[issue_id].admission == "published"
    )

    return [
        {"id": "sites", "label": "Review sites", "count": len(sites), "min_state": None,
         "note": "change targets in this PR's diff"},
        {"id": "agenda", "label": "Scheduled", "count": scheduled, "min_state": "unsupported",
         "note": "investigations the agenda enumerated"},
        {"id": "ran", "label": "Operators ran", "count": ran, "min_state": "silent",
         "note": f"{scheduled - ran} had no supported implementation"},
        {"id": "opportunity", "label": "Opportunities", "count": constructed,
         "min_state": "opportunity", "note": "transformations constructed"},
        {"id": "candidate", "label": "Candidates", "count": candidates,
         "min_state": "candidate", "note": "claims emitted by any arm"},
        {"id": "finding", "label": "Findings", "count": len(pr_findings),
         "min_state": "finding", "note": "survived merge and adjudication"},
        {"id": "published", "label": "Published", "count": published, "min_state": "finding",
         "note": "issues a maintainer would be shown",
         "terminal_stages": dict(stage_counts),
         "top_reasons": reasons.most_common(8)},
    ]


# --- Gold ----------------------------------------------------------------------------

def _build_gold(release, bundles, arms, findings, matches) -> Dict[str, dict]:
    """Obligations pinned to their change targets, with whatever outcome we can show.

    Loaded only when gold is requested, and returned as a separate blob so `--no-gold`
    omits the bytes rather than hiding them in CSS. The `input/` vs `gold/` split is a
    physical leak barrier; a viewer must not be the thing that breaks it.
    """

    judgments = load_jsonl(release / "gold" / "judgments.jsonl", JudgmentNode)
    views = load_jsonl(release / "gold" / "intervention_views.jsonl", InterventionView)
    included = {
        view.source_intervention_id
        for view in views
        if view.evaluation_eligibility == "included"
    }

    prs = {bundle.pr_number for bundle in bundles}
    site_ids = {site.change_id for bundle in bundles for site in bundle.sites}

    # Location semantics are `evaluate._covered`'s: does any prediction's change set
    # intersect the obligation's? Funnel-only — it says a prediction landed on the right
    # target, never that it asked for the right thing.
    candidate_sites: Dict[int, set] = defaultdict(set)
    candidate_ids_by_change: Dict[str, List[str]] = defaultdict(list)
    for arm in arms:
        for candidate in arm.candidates:
            candidate_sites[candidate.pr_number].update(candidate.change_ids)
            for change_id in candidate.change_ids:
                candidate_ids_by_change[change_id].append(candidate.candidate_id)
    finding_sites: Dict[int, set] = defaultdict(set)
    finding_ids_by_change: Dict[str, List[str]] = defaultdict(list)
    for finding in findings.values():
        finding_sites[finding.pr_number].update(finding.change_ids)
        for change_id in finding.change_ids:
            finding_ids_by_change[change_id].append(finding.finding_id)

    verdicts: Dict[str, List[SemanticMatch]] = defaultdict(list)
    for match in matches:
        verdicts[match.obligation_id].append(match)

    by_change: Dict[str, List[dict]] = defaultdict(list)
    orphans: List[dict] = []
    for judgment in judgments:
        if judgment.pr_number not in prs:
            continue
        eligible = judgment.source_intervention_id in included
        for obligation in judgment.obligations:
            gold_sites = set(obligation.change_ids)
            observed = [item for item in verdicts.get(obligation.obligation_id, [])
                        if item.role == "observed" and not item.abstain]
            entry = {
                "obligation_id": obligation.obligation_id,
                "judgment_id": judgment.judgment_id,
                "pr_number": judgment.pr_number,
                "included": eligible,
                "claim": obligation.claim,
                "resolution_criteria": obligation.resolution_criteria,
                "required": obligation.required,
                "status": obligation.status,
                "action": {"kind": judgment.action.kind, "object": judgment.action.object},
                "speech_act": judgment.speech_act,
                "blocking_force": judgment.blocking_force,
                "concern_labels": judgment.concern_labels,
                "change_ids": sorted(gold_sites),
                "annotation_status": judgment.annotation.status,
                "atomicity_status": judgment.annotation.atomicity_status,
                "candidate_location_hit": bool(
                    gold_sites & candidate_sites.get(judgment.pr_number, set())
                ),
                "finding_location_hit": bool(
                    gold_sites & finding_sites.get(judgment.pr_number, set())
                ),
                "issue_match": any(item.issue_match for item in observed),
                "resolution_match": any(item.resolution_match for item in observed),
                "judged": bool(observed),
                "matched_candidate_ids": sorted(
                    {item.candidate_id for item in observed if item.issue_match}
                ),
                "predictions_here": sorted(
                    {cid for change_id in gold_sites
                     for cid in candidate_ids_by_change.get(change_id, [])}
                    | {fid for change_id in gold_sites
                       for fid in finding_ids_by_change.get(change_id, [])}
                ),
            }
            anchored = [cid for cid in gold_sites if cid in site_ids]
            if anchored:
                for change_id in anchored:
                    by_change[change_id].append(entry)
            else:
                orphans.append(entry)

    return {"by_change": dict(by_change), "unanchored": orphans}


# --- Emission ------------------------------------------------------------------------

def bundle_json(overlay: Overlay) -> dict:
    return {
        "version": overlay.version,
        "sources": overlay.sources,
        "cost": overlay.cost,
        "prs": [asdict(bundle) for bundle in overlay.prs],
        "gold": overlay.gold,
    }


#: A rendered overlay is a regenerable view, not a research artifact. `verify_frozen`
#: hashes every file under `inputs/pr_review_v4` and `results/pr_review_v4` and fails on any
#: it has not sealed, so writing pages there turns each render into an integrity-gate
#: failure. Default outside those roots, and refuse to be pointed inside them.
DEFAULT_OUT = Path("results/overlays/pr_review_v4")


def _reject_frozen_destination(out: Path) -> None:
    from .verify_frozen import FROZEN_ROOTS

    resolved = out.resolve()
    for root in FROZEN_ROOTS:
        root = root.resolve()
        if resolved == root or root in resolved.parents:
            raise SystemExit(
                f"refusing to write overlays into the frozen root {root}: every render "
                "would fail the FROZEN.lock integrity gate. Use "
                f"--out {DEFAULT_OUT.as_posix()}/<name> instead."
            )


def write_overlay(overlay: Overlay, out: Path) -> dict:
    """Write `bundle.json`, one page per PR, and the index. Never raises on a page.

    A page that fails to render must not take the rest of the build with it: the join is
    the expensive part and the other pages are still correct.
    """

    from . import review_overlay_html

    _reject_frozen_destination(out)
    out.mkdir(parents=True, exist_ok=True)
    payload = bundle_json(overlay)
    (out / "bundle.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )

    written, failed = [], {}
    conversations = 0
    for bundle in overlay.prs:
        page = out / f"pr-{bundle.pr_number}.html"
        try:
            page.write_text(
                review_overlay_html.to_html(bundle, overlay.gold, overlay.sources),
                encoding="utf-8",
            )
            written.append(page.name)
            # Transcripts are siblings, not sections: PR 33149's alone are 3.9 MB.
            pages = review_overlay_html.conversation_pages(bundle)
            if pages:
                (out / "conv").mkdir(exist_ok=True)
                for name, html in pages.items():
                    (out / "conv" / name).write_text(html, encoding="utf-8")
                conversations += len(pages)
        except Exception as error:  # noqa: BLE001 - one bad page must not lose the rest
            failed[bundle.pr_number] = f"{type(error).__name__}: {error}"

    index = out / "index.html"
    index.write_text(
        review_overlay_html.write_index(overlay.prs, overlay.gold, overlay.sources),
        encoding="utf-8",
    )
    return {
        "out": display_path(out),
        "pages": len(written),
        "index": display_path(index),
        "bundle": display_path(out / "bundle.json"),
        "conversations": conversations,
        "failed": failed,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render a per-PR visualization of how the v4 reviewer reviewed a PR"
    )
    parser.add_argument("--release", type=Path, default=DEFAULT_RELEASE)
    parser.add_argument("--treatment", type=Path, default=DEFAULT_TREATMENT)
    parser.add_argument("--executor", type=Path, default=DEFAULT_EXECUTOR)
    parser.add_argument("--run", type=Path, action="append", default=[],
                        help="model-arm run directory; repeatable")
    parser.add_argument("--condition", type=Path, action="append", default=[],
                        help="condition directory holding findings.jsonl; repeatable")
    parser.add_argument("--judge", type=Path, default=None,
                        help="semantic-judge directory holding matches.jsonl")
    parser.add_argument("--pr", type=int, action="append", default=[],
                        help="restrict to these PR numbers; repeatable")
    parser.add_argument("--no-gold", action="store_true",
                        help="omit gold entirely; the gold files are not opened")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT / "latest")
    args = parser.parse_args()

    paths.assert_repo_root()
    overlay = build_overlay(
        args.release,
        treatment=args.treatment if args.treatment and args.treatment.is_dir() else None,
        executor=args.executor if args.executor and args.executor.is_dir() else None,
        runs=[run for run in args.run if run.is_dir()],
        conditions=[item for item in args.condition if item.is_dir()],
        judge=args.judge if args.judge and args.judge.is_dir() else None,
        include_gold=not args.no_gold,
        pr_numbers=args.pr or None,
    )
    report = write_overlay(overlay, args.out)
    report["prs"] = [bundle.pr_number for bundle in overlay.prs]
    report["totals"] = {
        key: sum(bundle.totals[key] for bundle in overlay.prs)
        for key in ("sites", "investigations", "candidates", "findings", "published")
    }
    report["sources"] = overlay.sources
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
