"""Combine both review arms into one final finding set — the system's actual output.

The two arms previously ended in incompatible record types with no shared consumer, and
`synthesis.link_candidates` raised unless a candidate mapped to exactly one opportunity, so
a holistic finding (which has no opportunity) could not pass through it at all. This is the
arm-neutral replacement. `synthesis.py` is left untouched: it carries the frozen Phase 9
lineage, and bending holistic findings into its opportunity-shaped records would mean
fabricating opportunity IDs.

Two things this module deliberately does not do:

* **It does not rank by model confidence.** Self-confidence has been falsified as a ranking
  signal three times (precision flat 9% -> 12%), alongside five failed selector designs.
* **It does not resolve genuine disagreements.** Two findings asking for incompatible
  transformations on the same anchor, with no evidence-strength difference between them,
  produce a `ConflictRecord` — reporting a winner would claim confidence the system has not
  earned.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from src.mathlib_review.io import sealed_model
from src.mathlib_review.schema import (
    ARMS,
    FILE_COHERENCE_SPEC,
    FILE_GENERALIST_ARM,
    GENERALIST_ARM,
    CandidateClaim,
    ConflictRecord,
    EVIDENCE_TIERS,
    FindingSource,
    ReviewFinding,
    ReviewOpportunity,
    WorthinessDecision,
    evidence_rank,
)


MERGE_VERSION = "arm-neutral-merge/1"

#: Applied per PR, after every other step. The previous limit was checked against a flat
#: list spanning all PRs while its own message said "PR finding budget" — harmless at two
#: PRs, silently truncating at sixteen, and cutting in sha256 order.
DEFAULT_PR_FINDING_LIMIT = 20

_WHITESPACE = re.compile(r"\s+")


def canonical_action(concern_family: str, requested_change: str) -> str:
    """A normalized key for "asks for the same thing".

    Deliberately conservative: case and whitespace only. Anything cleverer — stemming,
    synonyms, embeddings — would merge findings we cannot prove equivalent, and a merge is
    lossy: only the representative's wording survives to be judged.
    """

    return f"{concern_family}:{_WHITESPACE.sub(' ', requested_change.strip().lower())}"


def finding_key(finding) -> str:
    """The identity of a CLAIM, across runs and across repetitions.

    `finding_id` is the identity of one finding's exact wording, which is what a merge needs
    and what an adjudication cannot use: a label is about what the system asked for at a site,
    and free text does not reproduce. Measured on the three committed held-out reps
    (285 / 318 / 304 findings), 2026-09-21:

        key                                            in all three reps    in >= 2
        (pr, change, issue_kind, action_key)                    0                2
        (pr, change, issue_kind)                              127              225

    `canonical_action` normalises case and whitespace of model free text and nothing else --
    deliberately, since anything cleverer would merge claims we cannot prove equivalent -- so
    the full key is an identity of the sentence and recurs essentially never. The site-and-kind
    key recurs for about half of everything emitted, which is what makes labelling it once and
    carrying the label worth doing at all.

    The cost is a real collision rate: within one rep, 285 findings share 238 keys, so about
    16% sit on a site and kind some sibling also claims. An adjudication report must say that
    rate beside its coverage rather than let a label stand silently for two asks. The exemplar's
    `action_key` is recorded with the label so a reader can see which sentence was judged.
    """

    return f"{finding.pr_number}|{finding.primary_change_id}|{finding.issue_kind}"


def _seal(model, prefix: str, payload: Dict):
    """Seal a record, deriving its ID from its own content hash.

    Built on `io.sealed_model` so nested models (sources, proposed edits) serialize through
    pydantic rather than being handed raw to the JSON encoder. The ID is derived here rather
    than supplied, so two identical findings from different runs collide by construction.
    """

    draft = sealed_model(model, **{f"{prefix}_id": "", **payload})
    return draft.model_copy(
        update={f"{prefix}_id": f"{prefix}:{draft.source_sha256[:24]}"}
    )


def finding_from_candidate(
    candidate: CandidateClaim,
    *,
    admission: str,
    admission_reason: str,
    evidence_tier: str = "model_assertion",
    evidence_artifact_ids: Sequence[str] = (),
    arm: Optional[str] = None,
) -> ReviewFinding:
    """Project a model candidate into the common shape, under the arm that produced it.

    The arm is read from `spec_id`, not passed in: a candidate carrying a spec came from a
    scheduled focused invocation, and that is the only thing that distinguishes it from a
    holistic one — `producer` is `model` for both. Hard-coding `holistic` here filed every
    focused finding under the arm it is supposed to be measured against.

    `arm` overrides that derivation, for the one case it does not cover: a per-site
    specialist whose concern is *not settled by compiling*. `focused_agent` carries a hard
    invariant — a focused source must name a verification artifact, because the arm's whole
    warrant is "the compiler accepted this replacement". A naming or docstring specialist
    cannot produce one (renaming breaks call sites; a typo fix proves nothing by elaborating),
    so deriving `focused_agent` for it makes the finding unconstructible. Such an arm is a
    `generalist` in this vocabulary — same sites, evidence-warranted, narrower checklist — and
    `source.spec_id` still records which specialist produced it, so attribution is not lost.
    """

    if arm is None:
        if candidate.spec_id == FILE_COHERENCE_SPEC:
            arm = FILE_GENERALIST_ARM
        elif candidate.spec_id:
            arm = "focused_agent"
        else:
            arm = GENERALIST_ARM
    source = FindingSource(
        arm=arm,
        candidate_id=candidate.candidate_id,
        spec_id=candidate.spec_id,
        evidence_artifact_ids=list(evidence_artifact_ids),
    )
    payload = {
        "pr_number": candidate.pr_number,
        "episode_id": candidate.episode_id,
        "arm": arm,
        "admission": admission,
        "admission_reason": admission_reason,
        "change_ids": sorted(candidate.change_ids),
        "primary_change_id": candidate.primary_change_id or sorted(candidate.change_ids)[0],
        "concern_family": candidate.concern_family,
        "issue_kind": candidate.issue_kind,
        "primary_subject": candidate.primary_subject,
        "severity": candidate.severity,
        "claim": candidate.claim,
        "requested_change": candidate.requested_change or candidate.suggested_fix or "",
        "proposed_edit": candidate.proposed_edit,
        "evidence_tier": evidence_tier,
        "action_key": canonical_action(
            candidate.concern_family,
            candidate.requested_change or candidate.suggested_fix or "",
        ),
        # Provenance, recorded rather than inferred. `arm` is a coarse class that several arms
        # share, so it cannot say which arm found this; `spec_id` can, and is easy to lose in
        # a merge.
        "origin_arm_id": candidate.spec_id,
        # What the claim is about, as the arm saw it. Non-gating, unlike `concern_family`.
        # The candidate's own tags carry anything the arm layer observed and declined to
        # refuse — `off-concern:<arm_id>` above all, which is what the concern gate used to
        # reject a submission over.
        "concern_tags": sorted(
            set(candidate.concern_tags or [])
            | ({candidate.concern_family} if candidate.concern_family else set())
        ),
        "sources": [source],
    }
    return _seal(ReviewFinding, "finding", payload)


def finding_from_opportunity(
    opportunity: ReviewOpportunity,
    decision: WorthinessDecision,
    *,
    concern_family: str,
    evidence_tier: str,
    issue_kind: Optional[str] = None,
) -> ReviewFinding:
    """Project a deterministic opportunity and its adjudication into the common shape.

    Only `request` is published. Everything else — `no_request`, `advisory_option`, and
    `defer` — is retained as `diagnostic`, so the arm's reach stays measurable without
    claiming it would have said anything to a maintainer.
    """

    published = decision.review_worthiness == "request"
    transformation = opportunity.proposed_transformation
    requested = transformation.description if transformation else opportunity.observed_pattern
    payload = {
        "pr_number": opportunity.pr_number,
        "episode_id": opportunity.episode_id,
        "arm": "deterministic",
        "admission": "published" if published else "diagnostic",
        "admission_reason": f"adjudicated {decision.review_worthiness}",
        "change_ids": sorted({opportunity.primary_change_id, *opportunity.related_change_ids}),
        "primary_change_id": opportunity.primary_change_id,
        "concern_family": concern_family,
        "issue_kind": issue_kind,
        "primary_subject": (transformation.symbols[0] if transformation and transformation.symbols
                            else None),
        "severity": "blocking" if decision.request_force == "blocking" else "advisory",
        "claim": opportunity.observed_pattern,
        "requested_change": requested,
        "proposed_edit": None,
        "evidence_tier": evidence_tier,
        "action_key": canonical_action(concern_family, requested),
        "sources": [FindingSource(
            arm="deterministic",
            opportunity_id=opportunity.opportunity_id,
            method_id=opportunity.method_id,
            evidence_artifact_ids=list(opportunity.source_artifact_ids),
        )],
    }
    return _seal(ReviewFinding, "finding", payload)


def _merge_group(findings: Sequence[ReviewFinding]) -> ReviewFinding:
    """Fold findings that ask for the same thing at the same place into one.

    The representative is the strongest-evidence member, so a verified deterministic finding
    supplies the surviving wording when a model assertion agrees with it — the merged text
    is the one with the best warrant behind it, not the first by hash.
    """

    if len(findings) == 1:
        return findings[0]
    best = max(findings, key=lambda item: (evidence_rank(item.evidence_tier), item.finding_id))
    payload = best.model_dump(mode="json", exclude={"finding_id", "source_sha256", "sources",
                                                    "arm", "schema_version"})
    payload["arm"] = "merged" if len({item.arm for item in findings}) > 1 else best.arm
    payload["severity"] = (
        "blocking" if any(item.severity == "blocking" for item in findings) else "advisory"
    )
    payload["sources"] = [
        source.model_dump(mode="json")
        for item in sorted(findings, key=lambda row: row.finding_id)
        for source in item.sources
    ]
    # Provenance combines rather than inheriting the representative's. Two arms finding the
    # same thing is a fact about the finding, and keeping only the winner's would report one
    # arm's work as the whole of it.
    origins = {item.origin_arm_id for item in findings if item.origin_arm_id}
    payload["origin_arm_id"] = origins.pop() if len(origins) == 1 else None
    payload["concern_tags"] = sorted({
        tag for item in findings for tag in (item.concern_tags or [])
    })
    return _seal(ReviewFinding, "finding", payload)


def _is_verified_proposal(finding: ReviewFinding) -> bool:
    """A finding that carries an edit the compiler accepted.

    This is what separates an *alternative* from a *contradiction*. A verified edit proves
    its own achievability, so two of them at one target are competing implementations. Two
    unverified prose claims that disagree are genuinely undecidable, and stay a conflict.
    """

    return finding.evidence_tier == "verified_compile" and finding.proposed_edit is not None


def _edit_size(finding: ReviewFinding) -> int:
    edit = finding.proposed_edit
    if edit is None:
        return 0
    return len((edit.new_declaration or edit.replacement or "").strip())


def _select_alternative(group: Sequence[ReviewFinding]) -> ReviewFinding:
    """Pick one verified edit from several at the same target.

    Smallest edit first: the more conservative ask, and for a proof rewrite it is the
    criterion the golf checker states for itself. Ties break on the stable finding ID, never
    on `model_confidence` — falsified three times as a ranking signal.
    """

    return min(group, key=lambda item: (_edit_size(item), item.finding_id))


def merge_findings(
    findings: Iterable[ReviewFinding],
    *,
    pr_finding_limit: Optional[int] = DEFAULT_PR_FINDING_LIMIT,
) -> Tuple[List[ReviewFinding], List[ConflictRecord], Dict]:
    """Merge, detect conflicts, then apply the per-PR publication limit.

    Returns `(findings, conflicts, report)`. The report carries pre- and post-limit counts,
    because a truncated finding set that reports only its post-limit size hides the fact
    that it was truncated at all.
    """

    findings = list(findings)
    grouped: Dict[Tuple, List[ReviewFinding]] = defaultdict(list)
    for finding in findings:
        # Merge only on identical anchors, family and canonical action. Nothing weaker:
        # an uncertain paraphrase stays a separate finding, because recall is not improved
        # by collapsing things we cannot prove equivalent.
        grouped[(finding.pr_number, tuple(finding.change_ids), finding.concern_family,
                 finding.action_key)].append(finding)

    merged = [_merge_group(group) for _key, group in sorted(grouped.items())]

    conflicts: List[ConflictRecord] = []
    by_anchor: Dict[Tuple, List[ReviewFinding]] = defaultdict(list)
    for finding in merged:
        by_anchor[(finding.pr_number, finding.primary_change_id, finding.concern_family)].append(
            finding
        )
    # finding_id -> why it was demoted. Three causes that used to share one message:
    # a stronger warrant elsewhere, an unresolved conflict, and an unselected alternative.
    suppressed: Dict[str, str] = {}
    alternatives = 0
    for (pr_number, change_id, family), group in sorted(by_anchor.items()):
        if len(group) < 2:
            continue
        ranks = {evidence_rank(item.evidence_tier) for item in group}
        if len(ranks) > 1:
            # A strictly stronger warrant resolves it; the weaker sides become diagnostic
            # rather than vanishing.
            best = max(ranks)
            for item in group:
                if evidence_rank(item.evidence_tier) < best:
                    suppressed[item.finding_id] = (
                        "a better-warranted finding covers this target"
                    )
            continue
        if all(_is_verified_proposal(item) for item in group):
            # Alternatives, not contradictions. Two verified edits at one target are two
            # ways of doing the achievable thing — each compiles, so each proves itself.
            # Treating them as a contradiction and demoting both makes the system publish
            # *less* the more of its checkers succeed, which is backwards.
            winner = _select_alternative(group)
            alternatives += len(group) - 1
            for item in group:
                if item.finding_id != winner.finding_id:
                    suppressed[item.finding_id] = (
                        f"an alternative verified edit was selected ({winner.finding_id})"
                    )
            continue
        conflicts.append(_seal(ConflictRecord, "conflict", {
            "pr_number": pr_number,
            "primary_change_id": change_id,
            "concern_family": family,
            "finding_ids": sorted(item.finding_id for item in group),
            "action_keys": sorted(item.action_key for item in group),
            "evidence_tiers": sorted({item.evidence_tier for item in group}),
            "rationale": (
                "Findings on the same target ask for different transformations with equal "
                "evidence strength and no verified edit to choose between them; no side is "
                "preferred."
            ),
        }))
        for item in group:
            suppressed[item.finding_id] = "in an unresolved conflict at this anchor"

    resolved = [
        item if item.finding_id not in suppressed
        else item.model_copy(update={
            "admission": "diagnostic",
            "admission_reason": suppressed[item.finding_id],
        })
        for item in merged
    ]

    # Publication limit: per PR, applied last, ordered by warrant — never by confidence.
    published_before = sum(item.admission == "published" for item in resolved)
    kept: List[ReviewFinding] = []
    per_pr: Dict[int, int] = defaultdict(int)
    for finding in sorted(
        resolved,
        key=lambda item: (
            item.pr_number,
            -evidence_rank(item.evidence_tier),
            0 if item.severity == "blocking" else 1,
            item.finding_id,
        ),
    ):
        if finding.admission == "published":
            # `None` defers the limit to the digest phase, where it applies to *issues*. A
            # limit applied here counts one 19-site pattern nineteen times against a budget
            # of twenty and crowds out every other arm on that PR.
            if pr_finding_limit is not None and per_pr[finding.pr_number] >= pr_finding_limit:
                finding = finding.model_copy(update={
                    "admission": "diagnostic",
                    "admission_reason": f"per-PR publication limit of {pr_finding_limit} reached",
                })
            else:
                per_pr[finding.pr_number] += 1
        kept.append(finding)

    published_after = sum(item.admission == "published" for item in kept)
    report = {
        "merge_version": MERGE_VERSION,
        "inputs": len(findings),
        "after_merge": len(merged),
        "conflicts": len(conflicts),
        "alternatives_not_selected": alternatives,
        "published_before_limit": published_before,
        "published_after_limit": published_after,
        "suppressed_by_limit": published_before - published_after,
        "pr_finding_limit": pr_finding_limit,
        "by_admission": {
            tier: sum(item.admission == tier for item in kept)
            for tier in ("published", "diagnostic")
        },
        # Derived from the schema, not listed here. A literal list does not fail when an arm
        # is added — it silently reports nothing for it, so a new arm's entire output reads
        # as zero in every report that consumes this.
        "by_arm": {
            arm: sum(item.arm == arm for item in kept) for arm in ARMS
        },
        "by_evidence_tier": {
            tier: sum(item.evidence_tier == tier for item in kept) for tier in EVIDENCE_TIERS
        },
    }
    return kept, conflicts, report


# ============================================================================
# The union of several passes: identical asks collapse, agreement is a label
# ============================================================================

UNION_VERSION = "pass-union/1"

#: What `union_findings` collapses on: the grouping key of `merge_findings`, and nothing weaker.
UNION_GROUPING_KEY = "(pr_number, change_ids, concern_family, action_key)"
#: What `passes_agreeing` counts over: the claim identity across runs (`finding_key`).
UNION_LABEL_KEY = "finding_key: (pr_number, primary_change_id, issue_kind)"


def union_findings(
    by_run: Dict[str, Sequence[ReviewFinding]],
    *,
    control_pr_numbers: Iterable[int] = (),
) -> Tuple[List[ReviewFinding], Dict]:
    """The union of several passes' findings, with agreement kept as a label.

    Layer 2 of `docs/plans/2026-10-01-beyond-the-solo-baseline.md`: K passes over one PR, their
    findings unioned, nothing voted on. Two things here are deliberately not `merge_findings`:

    * **only identical asks collapse** -- the grouping key `merge_findings` uses (PR, change
      ids, concern family, canonical action), so nothing is lost but a duplicate sentence.
      Measured on the four Opus passes of 2026-10-01, that key folds 6 of 375 findings; every
      other finding is a distinct ask and survives;
    * **the suppression step never runs.** Demoting alternatives at one anchor, resolving by
      warrant and the per-PR limit are each a decision about which findings reach a
      maintainer, and that is selection (`.claude/rules/mathlib-review.md`). A union is
      generation.

    Each surviving finding is stamped `passes` / `passes_agreeing`: the source runs that filed
    a finding with the same `finding_key` (site and issue kind -- the claim identity across
    runs, which recurs for about half of what is emitted where the full action key recurs
    essentially never) and their count. It is a label for the reading `selection-signal.md`
    asks for -- hit rate by k, with no cut -- and nothing here reads it.

    The `review` channel only, every admission: a finding's `admission` was set by its own
    run's merge and is carried on the representative, never recomputed. The report's
    `members` map each union finding to the (run, finding_id) rows it stands for.
    """

    runs = list(by_run)
    rows: List[Tuple[str, ReviewFinding]] = [
        (run, finding) for run in runs for finding in by_run[run]
        if "review" in finding.channels
    ]
    grouped: Dict[Tuple, List[Tuple[str, ReviewFinding]]] = defaultdict(list)
    agreeing: Dict[str, set] = defaultdict(set)
    for run, finding in rows:
        grouped[(finding.pr_number, tuple(finding.change_ids), finding.concern_family,
                 finding.action_key)].append((run, finding))
        agreeing[finding_key(finding)].add(run)

    merged: List[ReviewFinding] = []
    members: Dict[str, List[Dict[str, str]]] = {}
    k_identical: Counter = Counter()
    for _key, group in sorted(grouped.items(), key=lambda item: item[0]):
        representative = _merge_group([finding for _run, finding in group])
        passes = sorted(agreeing[finding_key(representative)])
        payload = representative.model_dump(mode="json", exclude={"finding_id", "source_sha256"})
        payload["passes"] = passes
        payload["passes_agreeing"] = len(passes)
        finding = _seal(ReviewFinding, "finding", payload)
        merged.append(finding)
        members[finding.finding_id] = [
            {"run": run, "finding_id": item.finding_id}
            for run, item in sorted(group, key=lambda row: (row[0], row[1].finding_id))]
        k_identical[len({run for run, _item in group})] += 1

    controls = sorted(set(control_pr_numbers))
    per_pr: Counter = Counter(finding.pr_number for finding in merged)
    per_pr_per_run = {
        run: Counter(finding.pr_number for finding in by_run[run] if "review" in finding.channels)
        for run in runs}
    report = {
        "union_version": UNION_VERSION,
        "grouping_key": UNION_GROUPING_KEY,
        "label_key": UNION_LABEL_KEY,
        "runs": runs,
        "findings_per_run": {run: len(by_run[run]) for run in runs},
        "inputs": len(rows),
        "dropped_not_in_review_channel": sum(len(by_run[run]) for run in runs) - len(rows),
        "union": len(merged),
        "collapsed_identical_asks": len(rows) - len(merged),
        "per_pr": {str(pr): per_pr[pr] for pr in sorted(per_pr)},
        "per_pr_per_run": {
            str(pr): {run: per_pr_per_run[run][pr] for run in runs} for pr in sorted(per_pr)},
        "control_pr_numbers": controls,
        "control_findings": {str(pr): per_pr.get(pr, 0) for pr in controls},
        "control_findings_per_run": {
            run: {str(pr): per_pr_per_run[run].get(pr, 0) for pr in controls} for run in runs},
        # Two distributions, because they answer different questions. `k_identical_ask` is how
        # many runs filed the very sentence a union finding stands for; `k_site_and_kind` is the
        # label, how many runs filed something of its claim identity.
        "k_identical_ask": {str(k): k_identical[k] for k in sorted(k_identical)},
        "k_site_and_kind": {
            str(k): n for k, n in sorted(Counter(f.passes_agreeing for f in merged).items())},
        "site_and_kind_keys": len(agreeing),
        "k_site_and_kind_keys": {
            str(k): n for k, n in sorted(Counter(len(v) for v in agreeing.values()).items())},
        "members": members,
    }
    return merged, report


def write_union_run(run_names: Sequence[str], derived: str, *,
                    control_pr_numbers: Iterable[int] = ()) -> Dict:
    """Write the union of several finished runs as a derived run the judge reads like any other.

    Each source is read through `StageInput` with `require=("findings",)`, which hashes what
    was read and refuses a run whose manifest says it did not cover what it promised: a partial
    pass would union in its silences. The derived run holds `findings.jsonl`, `union_report.json`
    and a `union` row in its own `stages.jsonl` naming every source digest. It has no manifest
    and no agenda -- it ran nothing -- and the judge reads such a run as unchecked rather than
    refusing it, taking its PR scope from the judge config.

    `write_once` binds the derived name to its inputs: the same sources regenerate it as a
    no-op, and different ones are refused. A derived run that could be quietly rebuilt from
    other passes under the same name would not be a run name (CLAUDE.md: every knob that
    changes what a run does goes into the run name).
    """

    from src.mathlib_review.io import jsonl_bytes, load_jsonl, pretty_json_bytes, write_once
    from src.mathlib_review.paths import run_dir
    from src.mathlib_review.run_state import (
        RUN_ARTIFACTS, StageInput, append_stage, digests_of, stage_record,
    )

    names = list(run_names)
    if len(names) < 2 or len(set(names)) != len(names):
        raise ValueError(f"a union needs two or more distinct runs, got {names}")
    if derived in names:
        raise ValueError(f"the derived run {derived!r} cannot be one of its own sources")

    by_run: Dict[str, List[ReviewFinding]] = {}
    consumed: Dict[str, str] = {}
    sources: Dict[str, Dict] = {}
    for name in names:
        stage = StageInput.of(name, require=("findings",))
        by_run[name] = load_jsonl(stage.path("findings"), ReviewFinding)
        consumed[f"{name}/findings"] = stage.consumed["findings"]
        sources[name] = {
            "completion_status": (stage.manifest or {}).get("completion_status"),
            "state": stage.state.value,
        }

    findings, report = union_findings(by_run, control_pr_numbers=control_pr_numbers)
    out = run_dir(derived)
    findings_path = out / RUN_ARTIFACTS["findings"].filename
    report_path = out / RUN_ARTIFACTS["union_report"].filename
    written = write_once(findings_path, jsonl_bytes(findings))
    write_once(report_path, pretty_json_bytes(
        {**report, "derived_run": derived, "sources": sources}))
    if written:
        append_stage(out, stage_record(
            "union", run_name=derived, consumed=consumed,
            produced=digests_of([findings_path, report_path]),
            identity={"union_version": UNION_VERSION, "source_runs": names,
                      "grouping_key": UNION_GROUPING_KEY, "label_key": UNION_LABEL_KEY}))
    return {"derived_run": derived, "run_dir": str(out), "written": written,
            **{key: value for key, value in report.items() if key != "members"}}
