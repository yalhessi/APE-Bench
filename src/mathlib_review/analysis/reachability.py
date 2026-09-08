"""How much of the gold the publication mechanism could admit, declared before the run.

Both September runs published only through the compile gate. The evidence chain, which is the
only other admission path, returned **zero** supported verdicts across 18 packets (17
inconclusive, 1 contradicted). Only 16 of the release's 43 gold obligations carry a concern a
compile can settle, so **27 of 43 were unpublishable by construction** — and every run so far
was reported against a denominator of 43.

That makes a published-recall figure two claims at once: how good the reviewer is, and how much
of the target the mechanism can express. Reporting the second alongside the first separates
them.

Two rules keep this honest, and both matter:

* **Predeclared, not observed.** Reachability comes from a mapping stated here and hashed
  before generation, never from which concerns happened to publish. Deriving it after the fact
  would let a run that published nothing declare nothing reachable and score 100%.
* **Evaluation-only.** Nothing here may reach routing, prompts or arm eligibility. It is a
  property of the scoring mechanism, and feeding it back into generation would tell the
  reviewer which concerns are worth raising — which is the same contamination as telling it
  the answer.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional

from src.mathlib_review.io import canonical_json_bytes, sha256_bytes

#: Bumped whenever the mapping below changes, so a reachability figure can be told apart from
#: one computed under a different mechanism.
REACHABILITY_VERSION = "v5-reachability/1"

#: What each admission channel can settle, by concern family.
#:
#: `verification` is the compile gate: an arm proposes a replacement declaration, the file is
#: recompiled, and the artifact is the warrant. It settles exactly the concerns whose claim is
#: falsified by a failed elaboration.
#:
#: `evidence_chain` is the claim-scoped collector path for everything else. It is listed as
#: *declared* rather than *working*: it has produced no supported verdict in any run, which is
#: why `EVIDENCE_CHAIN_ADMITS` defaults to False and the reachable set is currently the
#: compile-checkable concerns alone.
VERIFIABLE_BY_COMPILE = frozenset({
    "proof-golf",
    "duplication",
    "generalization",
    "correctness",
})

#: Concerns for which no deterministic warrant exists today. Naming needs a cutoff-respecting
#: precedent citation, documentation a structural check, style a linter result, scope an
#: import analysis. None is implemented, so each is currently unpublishable however well an
#: arm reasons about it.
#:
#: Both spellings of the documentation concern are listed: gold judgments label it `docs` and
#: findings label it `documentation`. Carrying one spelling would silently exclude the other
#: from the reachable set the day the evidence chain starts admitting anything.
AWAITING_A_WARRANT = frozenset({
    "naming",
    "docs",
    "documentation",
    "style",
    "scope",
})

#: Whether the evidence chain is counted as an admission path. False until it admits
#: something: counting a channel that has never returned `supported` would inflate the
#: reachable denominator with obligations nothing can actually publish.
EVIDENCE_CHAIN_ADMITS = False


def reachable_concerns(*, evidence_chain_admits: bool = EVIDENCE_CHAIN_ADMITS) -> frozenset:
    """The concern families the publication mechanism can currently admit."""

    if evidence_chain_admits:
        return VERIFIABLE_BY_COMPILE | AWAITING_A_WARRANT
    return VERIFIABLE_BY_COMPILE


def mechanism_identity(*, evidence_chain_admits: bool = EVIDENCE_CHAIN_ADMITS) -> str:
    """A hash of the declared mapping, so a run records which mechanism it was scored under."""

    return sha256_bytes(canonical_json_bytes({
        "version": REACHABILITY_VERSION,
        "verification": sorted(VERIFIABLE_BY_COMPILE),
        "awaiting_warrant": sorted(AWAITING_A_WARRANT),
        "evidence_chain_admits": evidence_chain_admits,
    }))


def _is_reachable(concerns, *, evidence_chain_admits: bool = EVIDENCE_CHAIN_ADMITS) -> bool:
    """Whether one obligation has an admission path.

    Reachable if *any* of its concerns does, which is the generous reading and keeps this from
    overstating the ceiling. Extracted so `reachability_report` and `annotate_recall` cannot
    disagree about which obligations they are each counting -- disagreeing about exactly that
    is how a recall rate came out at 3.0.
    """

    admits = reachable_concerns(evidence_chain_admits=evidence_chain_admits)
    labels = [str(item) for item in (concerns or [])] or ["(none)"]
    return any(label in admits for label in labels)


def reachability_report(
    obligation_concerns: Iterable[Iterable[str]],
    *,
    evidence_chain_admits: bool = EVIDENCE_CHAIN_ADMITS,
) -> Dict[str, Any]:
    """Split a set of obligations into reachable and unreachable, by concern.

    `obligation_concerns` is one iterable of concern labels per obligation — an obligation
    counts as reachable if *any* of its concerns has an admission path, which is the generous
    reading and keeps this from overstating the ceiling.
    """

    admits = reachable_concerns(evidence_chain_admits=evidence_chain_admits)
    reachable = 0
    total = 0
    by_concern: Dict[str, Dict[str, int]] = {}
    for concerns in obligation_concerns:
        labels = [str(item) for item in (concerns or [])] or ["(none)"]
        total += 1
        is_reachable = _is_reachable(concerns, evidence_chain_admits=evidence_chain_admits)
        reachable += int(is_reachable)
        for label in labels:
            row = by_concern.setdefault(label, {"total": 0, "reachable": 0})
            row["total"] += 1
            row["reachable"] += int(label in admits)

    return {
        "reachability_version": REACHABILITY_VERSION,
        "mechanism_sha256": mechanism_identity(
            evidence_chain_admits=evidence_chain_admits),
        "obligations_total": total,
        "obligations_reachable": reachable,
        "obligations_unreachable": total - reachable,
        "reachable_share": round(reachable / total, 4) if total else None,
        "admitting_channels": (
            ["verification", "evidence_chain"] if evidence_chain_admits else ["verification"]
        ),
        "by_concern": dict(sorted(by_concern.items())),
        # Said in the artifact, so a recall figure lifted out of it carries the caveat.
        "note": (
            "Recall against `obligations_total` measures the reviewer and the publication "
            "mechanism together. Recall against `obligations_reachable` measures the reviewer "
            "alone, given what the mechanism can currently express. Report both."
        ),
    }


def annotate_recall(
    report: Mapping[str, Any],
    concerns_by_obligation: Mapping[str, Iterable[str]],
    *,
    evidence_chain_admits: bool = EVIDENCE_CHAIN_ADMITS,
) -> Dict[str, Any]:
    """Add the reachable denominator beside an existing judge report's recall figures.

    **Numerator and denominator must describe the same obligations.** They did not: the
    numerator was the total hit count across every obligation and the denominator counted only
    the reachable ones, so `pr5_smoke4_rep9` reported `issue_recall_reachable: 3.0` -- six hits
    over two reachable obligations. A rate above 1 is the visible symptom; the real error is
    that the two halves were about different sets.

    They were about different *questions* too, which is why the arithmetic could drift without
    looking wrong. A hit is identification: the reviewer named the thing gold asks for.
    Reachable is publication: a compile can settle it. Fourteen of that run's seventeen
    obligations are `style`, which no mechanism can settle, and several were hit -- correctly
    identified and unpublishable. Restricting the numerator to reachable obligations makes the
    figure mean "of the obligations this mechanism could publish, how many did the reviewer
    find", which is the question it is named for.

    Takes a mapping now rather than a bare sequence of concern lists, because pairing a hit to
    its reachability needs the obligation id and the old signature threw it away.
    """

    ordered = [list(concerns_by_obligation[key]) for key in sorted(concerns_by_obligation)]
    reach = reachability_report(ordered, evidence_chain_admits=evidence_chain_admits)

    reachable_ids = {
        obligation_id for obligation_id, concerns in concerns_by_obligation.items()
        if _is_reachable(concerns, evidence_chain_admits=evidence_chain_admits)
    }
    out: Dict[str, Any] = {"reachability": reach}
    denominator = len(reachable_ids)
    per_obligation = report.get("per_obligation") or []
    for axis in ("issue", "resolution"):
        field = f"{axis}_status"
        if not any(field in row for row in per_obligation):
            continue
        hits = sum(
            1 for row in per_obligation
            if row.get("obligation_id") in reachable_ids and row.get(field) == "hit"
        )
        out[f"{axis}_recall_reachable"] = (
            round(hits / denominator, 4) if denominator else None)
        # Both halves, so a reader can see the sets rather than infer them from a ratio.
        out[f"{axis}_hits_reachable"] = hits
        out[f"{axis}_hits_unreachable"] = sum(
            1 for row in per_obligation
            if row.get("obligation_id") not in reachable_ids and row.get(field) == "hit"
        )
    return out
