"""Gold-only semantic issue/resolution evaluation for grounded v4 candidates."""

import argparse
import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from ape.utils.project import PROJECT_ROOT

from . import judge_protocol
from .pr_relations import relation_between
from .io import (
    canonical_json_bytes,
    extract_json_object,
    jsonl_bytes,
    pretty_json_bytes,
    sha256_bytes,
    write_once,
)
from .schema import (
    CandidateClaim, InterventionView, JudgmentNode, ReviewWorkUnit, SemanticMatch,
    SemanticPair,
)


#: Rubric, rendering, verdict and identity all live in `judge_protocol`. This module owns
#: pairing and scoring only. The two used to be tangled, and the tangle is what let the
#: script arm render an empty `## REVIEWED CODE` section under a v8 version string.
JUDGE_VERSION = judge_protocol.JUDGE_VERSION
MAX_TARGET_CODE_CHARS = judge_protocol.MAX_TARGET_CODE_CHARS
JUDGE_PROMPT = judge_protocol.JUDGE_PROMPT
target_code_block = judge_protocol.code_block
parse_verdict = judge_protocol.parse_verdict


def eligible_obligations(
    judgments: Iterable[JudgmentNode],
    views: Iterable[InterventionView],
    scoped_obligation_ids: Optional[Iterable[str]] = None,
):
    included_ids = {obligation_id for view in views if view.evaluation_eligibility == "included"
                    for obligation_id in view.obligation_ids}
    if scoped_obligation_ids is not None:
        included_ids.intersection_update(scoped_obligation_ids)
    return [(judgment, obligation) for judgment in judgments for obligation in judgment.obligations
            if obligation.status == "proposed_atomic" and obligation.obligation_id in included_ids]


def build_pairs(judgments: Iterable[JudgmentNode], views: Iterable[InterventionView],
                candidates: Iterable[CandidateClaim],
                scoped_change_ids: Optional[Iterable[str]] = None,
                scoped_obligation_ids: Optional[Iterable[str]] = None,
                *,
                tiers: Iterable[str] = ("anchor",),
                targets_by_change_id: Optional[Dict] = None,
                relations: Iterable = (),
                ) -> List[Dict]:
    """Plan the comparisons to judge, at the requested pairing tiers.

    `anchor` alone reproduces the original rule exactly, and is the default so every
    existing caller keeps its meaning. Wider tiers are opt-in because widening can only
    raise recall: an obligation unreachable at `anchor` is reported as a miss today, and
    making it reachable is a change to what the number means, not a bug fix.

    A pair is emitted once, at the strictest tier that applies — `anchor`, then `relation`,
    then `file` — so the same comparison is never counted twice at different strengths.
    """

    candidates = list(candidates)
    relations = list(relations)
    targets = targets_by_change_id or {}
    wanted = tuple(tiers)
    scope = set(scoped_change_ids) if scoped_change_ids is not None else None

    def paths(change_ids) -> set:
        return {targets[change_id].path for change_id in change_ids if change_id in targets}

    pairs = []
    for judgment, obligation in eligible_obligations(
        judgments, views, scoped_obligation_ids
    ):
        if scope is not None and not set(obligation.change_ids).intersection(scope):
            continue
        for candidate in candidates:
            if candidate.pr_number != judgment.pr_number:
                continue
            overlap = sorted(set(obligation.change_ids).intersection(candidate.change_ids))
            tier = justification = None
            if overlap:
                tier, justification = "anchor", "shared change_ids: " + ",".join(overlap)
            elif "relation" in wanted:
                relation_id = relation_between(
                    obligation.change_ids, candidate.change_ids, relations
                )
                if relation_id:
                    tier, justification = "relation", f"relation: {relation_id}"
            if tier is None and "file" in wanted:
                shared = sorted(paths(obligation.change_ids) & paths(candidate.change_ids))
                if shared:
                    tier, justification = "file", "shared path: " + ",".join(shared)
            if tier is None or tier not in wanted:
                continue
            pairs.append({
                "judgment": judgment, "obligation": obligation, "candidate": candidate,
                "overlap_change_ids": overlap, "pairing_tier": tier,
                "tier_justification": justification, "role": "observed",
            })
    return pairs


def build_null_pairs(observed: List[Dict], candidates: Iterable[CandidateClaim],
                     limit_per_obligation: int = 2) -> List[Dict]:
    """Near negatives: same PR, same tier of proximity, but not the obligation's own target.

    A null pair measures how often the judge says "same issue" about two things that merely
    sit near each other. Two constraints make it meaningful:

    * **Same PR.** The rubric's own premise is "on the same Mathlib pull request"; a
      cross-PR pair contradicts the prompt and is a trivially easy negative that measures
      nothing.
    * **Not a known negative.** A near pair may be a genuine match — that is the whole
      reason widening exists — so its match rate is a *candidate-negative* rate, not a
      false-positive rate, until the pairs carry human labels.

    Selection is by sorted `candidate_id`, so replanning the same inputs selects the same
    nulls and the artifact stays byte-reproducible.
    """

    candidates = list(candidates)
    paired = {(pair["obligation"].obligation_id, pair["candidate"].candidate_id)
              for pair in observed}
    by_obligation: Dict[str, Dict] = {}
    for pair in observed:
        by_obligation.setdefault(pair["obligation"].obligation_id, pair)

    nulls = []
    for obligation_id, template in sorted(by_obligation.items()):
        judgment, obligation = template["judgment"], template["obligation"]
        pool = sorted(
            (candidate for candidate in candidates
             if candidate.pr_number == judgment.pr_number
             and (obligation_id, candidate.candidate_id) not in paired),
            key=lambda candidate: candidate.candidate_id,
        )
        for candidate in pool[:limit_per_obligation]:
            nulls.append({
                "judgment": judgment, "obligation": obligation, "candidate": candidate,
                "overlap_change_ids": [], "pairing_tier": template["pairing_tier"],
                "tier_justification": "null: same PR, unpaired candidate",
                "role": "null",
            })
    return nulls


def seal_pair(pair: Dict, *, judge_identity: str, prompt: str,
              gold_code: str, candidate_code: str = "") -> SemanticPair:
    """Freeze one planned comparison, prompt hash included.

    The prompt hash is part of the artifact because the prompt *is* the question. A pair
    whose rendered prompt lost its code section is a different comparison from one that
    kept it, and under the previous cache key the two were indistinguishable.
    """

    obligation, candidate = pair["obligation"], pair["candidate"]
    payload = {
        "obligation_id": obligation.obligation_id,
        "obligation_source_sha256": obligation.source_sha256,
        "candidate_id": candidate.candidate_id,
        "candidate_source_sha256": candidate.source_sha256,
        "pr_number": candidate.pr_number,
        "pairing_tier": pair["pairing_tier"],
        "tier_justification": pair["tier_justification"],
        "gold_change_ids": sorted(obligation.change_ids),
        "candidate_change_ids": sorted(candidate.change_ids),
        "gold_code_sha256": sha256_bytes(gold_code.encode()),
        "candidate_code_sha256": sha256_bytes(candidate_code.encode()) if candidate_code else None,
        "prompt_sha256": sha256_bytes(prompt.encode()),
        "judge_identity": judge_identity,
        "role": pair.get("role", "observed"),
    }
    digest = sha256_bytes(canonical_json_bytes(payload))
    return SemanticPair(pair_id=f"semantic-pair:{digest[:24]}", source_sha256=digest, **payload)


class VerdictCoverageError(RuntimeError):
    """The returned verdicts do not reconcile against the planned pairs."""


def reconcile(planned: Iterable[SemanticPair], matches: Iterable[SemanticMatch]) -> Dict:
    """Require exact correspondence between planned pairs and returned verdicts.

    Without this, a pair that never produced a verdict is indistinguishable from one the
    judge answered "no" — the failure silently becomes a miss and depresses recall. Every
    discrepancy is fatal rather than reported, because each one means the number would be
    computed over a different pair set than the one that was sealed.
    """

    planned = list(planned)
    matches = list(matches)
    by_pair = {item.pair_id: item for item in planned}
    seen: Dict[str, int] = {}
    extra, stale = [], []
    for match in matches:
        if match.pair_id is None or match.pair_id not in by_pair:
            extra.append(match.match_id)
            continue
        pair = by_pair[match.pair_id]
        if (match.candidate_source_sha256 != pair.candidate_source_sha256
                or match.obligation_source_sha256 != pair.obligation_source_sha256):
            stale.append(match.pair_id)
        seen[match.pair_id] = seen.get(match.pair_id, 0) + 1
    missing = sorted(set(by_pair) - set(seen))
    duplicated = sorted(key for key, count in seen.items() if count > 1)
    versions = sorted({item.judge_version for item in matches})
    models = sorted({item.judge_model for item in matches})
    problems = {
        "missing": missing, "duplicated": duplicated, "extra": sorted(extra),
        "stale_source": sorted(set(stale)),
        "mixed_judge_version": versions if len(versions) > 1 else [],
        "mixed_judge_model": models if len(models) > 1 else [],
    }
    if any(problems.values()):
        raise VerdictCoverageError(
            "verdicts do not reconcile against the sealed pairs: "
            + json.dumps({key: value for key, value in problems.items() if value})
        )
    return {"pairs_planned": len(planned), "verdicts_returned": len(matches), "complete": True}


def _match(pair: Dict, model: str, issue: bool, resolution: bool, reason: str) -> SemanticMatch:
    candidate, obligation = pair["candidate"], pair["obligation"]
    payload = {
        "candidate_id": candidate.candidate_id, "obligation_id": obligation.obligation_id,
        "issue_match": issue, "resolution_match": resolution and issue, "reason": reason,
        "judge_model": model, "judge_version": JUDGE_VERSION,
        "candidate_source_sha256": candidate.source_sha256,
        "obligation_source_sha256": obligation.source_sha256,
    }
    digest = sha256_bytes(canonical_json_bytes(payload))
    return SemanticMatch(match_id=f"semantic-match:{digest[:24]}", source_sha256=digest, **payload)


# `judge_pairs` used to live here: a second LLM path with its own file cache, whose only
# caller never passed the change graph, so it rendered "(reviewed code unavailable for this
# target)" while stamping verdicts with the v8 version string. Its cache key omitted the
# code, so code-less and code-bearing verdicts collided in the same slot.
#
# It is gone rather than fixed. `judge_runner.py --config` is now the only path that spends
# money on a judge, which closes the defect by construction instead of by remembering to
# pass an argument.


#: Resolved against the repo root, not the caller's cwd. As a relative path this failed
#: *open*: `load` returned `{}` from any other directory, silently reverting to two-way
#: scoring and turning a ruled-ambiguous obligation back into a hit.
AMBIGUOUS_REGISTRY = PROJECT_ROOT / "inputs/pr_review_v4/curation/ambiguous_pairs_v2.json"


def load_ambiguous_rulings(path: Optional[Path] = None) -> Dict:
    """Human rulings that a specific comparison is undecidable under the current rubric.

    Keyed by `(obligation_id, candidate_id, level)`. The documented ruling is about a
    *relationship* — a candidate asking for a prerequisite of the maintainer's change —
    not a property of the obligation, so registering it against the obligation alone
    over-applied it to every other candidate that happened to reach the same obligation.
    `candidate_id: "*"` keeps an obligation-wide ruling expressible where that is genuinely
    what was meant.

    A missing registry raises. Scoring silently without the rulings is the failure mode
    this replaces.
    """

    path = path or AMBIGUOUS_REGISTRY
    if not path.is_file():
        raise FileNotFoundError(
            f"ambiguity registry is missing: {path}. Scoring without it silently reverts "
            "to two-way match/miss and counts ruled-ambiguous comparisons as hits."
        )
    payload = json.loads(path.read_text())
    rulings = {}
    for row in payload.get("rulings", []):
        key = (row["obligation_id"], row.get("candidate_id", "*"), row.get("level", "issue"))
        rulings[key] = row
    return {"path": path, "sha256": sha256_bytes(path.read_bytes()), "rulings": rulings}


def _is_ambiguous(rulings: Dict, obligation_id: str, candidate_id: str, level: str) -> bool:
    return (
        (obligation_id, candidate_id, level) in rulings
        or (obligation_id, "*", level) in rulings
    )


def semantic_report(judgments: Iterable[JudgmentNode], views: Iterable[InterventionView],
                    candidates: Iterable[CandidateClaim], matches: Iterable[SemanticMatch],
                    scoped_change_ids: Optional[Iterable[str]] = None,
                    scoped_obligation_ids: Optional[Iterable[str]] = None,
                    ambiguous_registry: Optional[Path] = None,
                    planned_pairs: Optional[Iterable[SemanticPair]] = None,
                    control_pr_numbers: Iterable[int] = (),
                    scoped_pr_numbers: Optional[Iterable[int]] = None,
                    null_pairs_requested: Optional[int] = None) -> Dict:
    candidates = list(candidates)
    matches = list(matches)
    registry = load_ambiguous_rulings(ambiguous_registry)
    rulings = registry["rulings"]
    control_prs = set(control_pr_numbers)

    # Null pairs calibrate the judge; they are never evidence that an obligation was found.
    observed = [item for item in matches if item.role == "observed"]
    nulls = [item for item in matches if item.role == "null"]

    coverage = {"pairs_planned": None, "verdicts_returned": len(matches), "complete": True}
    if planned_pairs is not None:
        try:
            coverage = reconcile(planned_pairs, matches)
            coverage["complete"] = True
        except VerdictCoverageError as error:
            # Recalls are withheld rather than computed over a different pair set than the
            # one that was sealed. A `failed_model` pair must never read as a "no".
            return {
                "schema_version": "v4-semantic-report3",
                "scored": False,
                "coverage": {"complete": False, "error": str(error)},
            }

    scope = set(scoped_change_ids) if scoped_change_ids is not None else None
    # The denominator must be the obligations of the PRs actually judged. `pr_numbers`
    # already filters which *pairs* are built, but nothing filtered the obligation census,
    # so a run over 11 PRs reported 40 obligations — 20 of them belonging to PRs it never
    # reviewed, each an automatic miss. Recall was being divided by other runs' work.
    # `None` preserves the previous whole-release behaviour for every existing caller.
    pr_scope = set(scoped_pr_numbers) if scoped_pr_numbers is not None else None
    obligations = [obligation for judgment, obligation in eligible_obligations(
        judgments, views, scoped_obligation_ids
    )
                   if (scope is None or set(obligation.change_ids).intersection(scope))
                   and (pr_scope is None or judgment.pr_number in pr_scope)]
    by_obligation: Dict[str, List[SemanticMatch]] = {}
    for match in observed:
        by_obligation.setdefault(match.obligation_id, []).append(match)
    count = len(obligations)

    def level_status(obligation_id: str, level: str) -> str:
        """`hit` / `ambiguous` / `miss` for one obligation at one level.

        Ambiguity is decided per comparison. An obligation whose only matching comparison
        is ruled undecidable is `ambiguous`; if any unruled comparison matches, it is a
        plain `hit`, because a clean match elsewhere settles it.
        """

        rows = by_obligation.get(obligation_id, [])
        matched = [row for row in rows
                   if (row.issue_match if level == "issue" else row.resolution_match)]
        if not matched:
            return "miss"
        # An issue-level ruling propagates: if it is undecidable whether the candidate
        # names the same issue, whether its fix resolves it cannot be decidable either.
        clean = [row for row in matched
                 if not _is_ambiguous(rulings, obligation_id, row.candidate_id, level)
                 and not _is_ambiguous(rulings, obligation_id, row.candidate_id, "issue")]
        return "hit" if clean else "ambiguous"

    issue_status = {item.obligation_id: level_status(item.obligation_id, "issue")
                    for item in obligations}
    resolution_status = {item.obligation_id: level_status(item.obligation_id, "resolution")
                         for item in obligations}
    location = {item.obligation_id: bool(by_obligation.get(item.obligation_id))
                for item in obligations}

    def rate(statuses, wanted) -> Optional[float]:
        return sum(value in wanted for value in statuses.values()) / count if count else None

    issue_recall = rate(issue_status, {"hit"})
    resolution_recall = rate(resolution_status, {"hit"})
    if issue_recall is not None and resolution_recall is not None and resolution_recall > issue_recall:
        # Definitionally impossible: resolution is conditional on issue. It was reachable
        # because ambiguity demoted issue hits out of the numerator while resolution
        # ignored the registry entirely.
        raise ValueError(
            f"resolution_recall ({resolution_recall}) exceeds issue_recall ({issue_recall}); "
            "the two levels are being scored under different rules"
        )

    evaluated_prs = {item.pr_number for item in candidates}
    scored_candidates = [item for item in candidates if item.pr_number in evaluated_prs]
    issue_candidates = {item.candidate_id for item in observed if item.issue_match}
    paired_candidates = {item.candidate_id for item in observed}
    control_candidates = [item for item in candidates if item.pr_number in control_prs]

    return {
        "schema_version": "v4-semantic-report3",
        "scored": True,
        "judge_version": _single_judge_version(matches),
        "judge_model": _single(matches, "judge_model"),
        "coverage": coverage,
        "ambiguity_registry_sha256": registry["sha256"],
        "counts": {
            "obligations": count,
            "candidates": len(candidates),
            "observed_pairs": len(observed),
            "null_pairs": len(nulls),
            "paired_candidates": len(paired_candidates),
        },
        "location_recall": (
            sum(location.values()) / count if count else None
        ),
        "issue_recall": issue_recall,
        "issue_recall_including_ambiguous": rate(issue_status, {"hit", "ambiguous"}),
        "resolution_recall": resolution_recall,
        "resolution_recall_including_ambiguous": rate(resolution_status, {"hit", "ambiguous"}),
        "ambiguous_rate": rate(issue_status, {"ambiguous"}),
        # NOT precision. Gold is a lower bound on what a maintainer could legitimately have
        # asked for — the holistic arm found a real `extenal` docstring typo in 3/3 runs
        # that simply is not in gold — so a candidate absent from gold is unaligned, not
        # wrong. True precision needs human adjudication of the findings themselves.
        "gold_alignment_rate": (
            len(issue_candidates) / len(scored_candidates) if scored_candidates else None
        ),
        "gold_alignment_within_paired": (
            len(issue_candidates) / len(paired_candidates) if paired_candidates else None
        ),
        # NOT a false-finding rate. Zero maintainer interventions is a ledger fact; calling
        # an emission *invented* presumes a judgement only human review can make.
        "silent_pr_emission": {
            "control_pr_numbers": sorted(control_prs),
            "candidates": len(control_candidates),
            "candidates_per_control_pr": (
                len(control_candidates) / len(control_prs) if control_prs else None
            ),
        },
        "null_pair_diagnostics": {
            "pairs": len(nulls),
            "requested": null_pairs_requested,
            # Widening can exhaust the unpaired pool: once every same-PR candidate is
            # compared to an obligation, there is nothing left to draw a near negative
            # from. That is reduced calibration coverage and is reported as such — the
            # alternative, substituting a cross-PR pair, contradicts the rubric's own
            # "same pull request" premise and would measure nothing.
            "coverage": (
                None if not null_pairs_requested
                else min(1.0, len(nulls) / null_pairs_requested)
            ),
            # A near pair may be a genuine match — that is why widening exists — so this is
            # a candidate-negative match rate, not a false-positive rate, until the pairs
            # carry human labels.
            "candidate_negative_issue_match_rate": (
                sum(item.issue_match for item in nulls) / len(nulls) if nulls else None
            ),
        },
        "by_pairing_tier": {
            tier: {
                "pairs": sum(item.pairing_tier == tier for item in observed),
                "issue_matches": sum(
                    item.pairing_tier == tier and item.issue_match for item in observed
                ),
            }
            for tier in ("anchor", "relation", "file")
        },
        "obligation_status_counts": {
            level: {
                status: sum(value == status for value in statuses.values())
                for status in ("hit", "ambiguous", "miss")
            }
            for level, statuses in (("issue", issue_status), ("resolution", resolution_status))
        },
        "per_obligation": [{"obligation_id": item.obligation_id,
                            "issue_status": issue_status[item.obligation_id],
                            "resolution_status": resolution_status[item.obligation_id],
                            "location_hit": location[item.obligation_id]}
                           for item in obligations],
        "manual_audit_required": True,
    }


def _single(matches: List[SemanticMatch], field: str) -> Optional[str]:
    values = sorted({getattr(item, field) for item in matches})
    if len(values) > 1:
        raise ValueError(f"report mixes {field}: {values}")
    return values[0] if values else None


def _single_judge_version(matches: List[SemanticMatch]) -> str:
    """Read the version off the verdicts, never off the module constant.

    The shipped v8 reports are stamped `v4-semantic-v1-v7.1-rubric` while their own matches
    say v8 — a report that cannot mislabel itself is worth the two lines.
    """

    return _single(matches, "judge_version") or JUDGE_VERSION


def audit_sample(pairs: List[Dict], matches: List[SemanticMatch], per_class: int = 10) -> List[Dict]:
    match_by_pair = {(item.candidate_id, item.obligation_id): item for item in matches}
    rows = []
    for pair in pairs:
        candidate, obligation = pair["candidate"], pair["obligation"]
        match = match_by_pair[(candidate.candidate_id, obligation.obligation_id)]
        rows.append({
            "candidate_id": candidate.candidate_id, "obligation_id": obligation.obligation_id,
            "overlap_change_ids": pair["overlap_change_ids"],
            "gold_request": obligation.claim,
            "candidate_claim": candidate.claim,
            "candidate_requested_change": candidate.requested_change,
            "issue_match": match.issue_match, "resolution_match": match.resolution_match,
            "judge_reason": match.reason,
            "human_issue_match": None, "human_resolution_match": None,
            "human_notes": None,
        })
    accepted = sorted((row for row in rows if row["issue_match"]),
                      key=lambda row: (row["obligation_id"], row["candidate_id"]))[:per_class]
    rejected = sorted((row for row in rows if not row["issue_match"]),
                      key=lambda row: (row["obligation_id"], row["candidate_id"]))[:per_class]
    return accepted + rejected


def main() -> None:
    """Score an existing verdict set. This CLI no longer judges anything.

    Judging happens only through `judge_runner.py --config`, which renders the reviewed code
    and drives the registered task. Splitting the two is what makes it impossible to
    accidentally score a run whose prompts were missing their code.
    """

    parser = argparse.ArgumentParser(description="Report over judged semantic matches")
    parser.add_argument("--judgments", type=Path, required=True)
    parser.add_argument("--views", type=Path, required=True)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--matches", type=Path, required=True,
                        help="matches.jsonl produced by judge_runner")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--work-units", type=Path)
    parser.add_argument("--work-unit-ids", nargs="*")
    parser.add_argument("--obligation-ids", nargs="*")
    parser.add_argument("--audit-per-class", type=int, default=10)
    args = parser.parse_args()
    load = lambda path, cls: [cls.model_validate_json(line) for line in path.read_text().splitlines() if line]
    judgments = load(args.judgments, JudgmentNode)
    views = load(args.views, InterventionView)
    candidates = load(args.candidates, CandidateClaim)
    matches = load(args.matches, SemanticMatch)
    scoped_change_ids = None
    if args.work_unit_ids:
        if args.work_units is None:
            raise ValueError("--work-unit-ids requires --work-units")
        wanted = set(args.work_unit_ids)
        units = [item for item in load(args.work_units, ReviewWorkUnit) if item.work_unit_id in wanted]
        missing = wanted - {item.work_unit_id for item in units}
        if missing:
            raise ValueError(f"unknown work-unit IDs: {sorted(missing)}")
        scoped_change_ids = {change_id for unit in units for change_id in unit.change_ids}
    scoped_obligation_ids = set(args.obligation_ids) if args.obligation_ids else None
    if scoped_obligation_ids:
        eligible_ids = {
            obligation.obligation_id
            for _judgment, obligation in eligible_obligations(judgments, views)
        }
        missing = scoped_obligation_ids - eligible_ids
        if missing:
            raise ValueError(f"unknown or ineligible obligation IDs: {sorted(missing)}")
    pairs = build_pairs(
        judgments, views, candidates, scoped_change_ids, scoped_obligation_ids
    )
    report = semantic_report(
        judgments, views, candidates, matches, scoped_change_ids, scoped_obligation_ids
    )
    report["scoped_work_unit_ids"] = sorted(args.work_unit_ids or []) or None
    report["scoped_obligation_ids"] = sorted(args.obligation_ids or []) or None
    write_once(args.out_dir / "report.json", pretty_json_bytes(report))
    write_once(args.out_dir / "audit.jsonl",
               b"".join(canonical_json_bytes(row) + b"\n"
                        for row in audit_sample(pairs, matches, args.audit_per_class)))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
