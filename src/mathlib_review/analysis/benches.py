"""Per-arm benches: what one arm should find, and whether it finds it.

Today an arm can only be measured by running the whole pipeline — a lead, a nested
orchestrator, a full judge run — and then attributing findings backwards. That costs a paid
run to learn anything about one arm, which is why "investigate each arm separately" has never
actually happened, and why a proposed replacement for `proof_golf` has no way to prove itself.

A bench is the fixture that makes one arm answerable on its own: the work units where gold
asks for something this arm owns, and the obligation it should have produced there.

**The gold stays on this side of the line.** The arm is handed a work unit and nothing else —
the same gold-free payload the agenda builds. The expected obligation is joined afterwards, by
the scorer. `obligation_capability.py:20` states the rule this follows: gold-derived
classification must never reach routing or prompts, and this session has already produced one
contamination incident from ignoring it.

A fixture is deliberately *not* only positives. An arm that reports something everywhere scores
perfectly against positives alone, so each bench also carries the work units in the same PRs
where gold asked for nothing of that kind — the arm should stay quiet there.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set

from src.mathlib_review.io import canonical_json_bytes, load_jsonl, sha256_bytes
from src.mathlib_review.schema import JudgmentNode, ReviewWorkUnit

#: Bumped when the fixture construction changes, so two bench results can be told apart.
BENCH_VERSION = "v5-bench/1"

#: Arm concern family -> the label gold actually uses.
#:
#: There is exactly one mismatch and it costs an entire arm: every arm declares
#: `documentation` and every gold judgment says `docs`. Nothing joins the two, so the `docs`
#: arm had **zero** gold obligations attributable to it — it has been unmeasurable since it
#: was added, and no amount of improving it could have shown up anywhere.
#:
#: Bridged here rather than by renaming either side, because both spellings are baked into
#: sealed artifacts: `concern_family` is hashed into every finding and every judge pair, and
#: `concern_labels` into every frozen release. `test_the_two_concern_vocabularies_are_bridged`
#: fails if a new mismatch appears, so this table cannot quietly grow.
CONCERN_ALIASES: Dict[str, str] = {
    "documentation": "docs",
}


def _gold_labels_for(families: Sequence[str]) -> Set[str]:
    """The gold labels that correspond to a set of arm concern families."""

    out: Set[str] = set()
    for family in families:
        out.add(str(family))
        alias = CONCERN_ALIASES.get(str(family))
        if alias:
            out.add(alias)
    return out


@dataclass(frozen=True)
class BenchCase:
    """One work unit an arm will be run on, and what gold says about it."""

    work_unit_id: str
    pr_number: int
    episode_id: str
    change_ids: Sequence[str]
    #: The obligations this arm should produce here. Empty for a negative case.
    expected_obligation_ids: Sequence[str] = ()
    #: Gold's own words, for reading a failure. Never shown to the arm.
    expected: Sequence[str] = ()

    @property
    def is_positive(self) -> bool:
        return bool(self.expected_obligation_ids)


@dataclass
class ArmBench:
    """Every case for one arm, positives and negatives together."""

    arm_id: str
    concern_families: Sequence[str]
    cases: List[BenchCase] = field(default_factory=list)
    #: How the positives were chosen. Part of the identity, because a bench selected by gold
    #: label and one selected from the audited request groups are different experiments that
    #: would otherwise share a fixture hash.
    selector: str = "gold_label"

    @property
    def positives(self) -> List[BenchCase]:
        return [case for case in self.cases if case.is_positive]

    @property
    def negatives(self) -> List[BenchCase]:
        return [case for case in self.cases if not case.is_positive]

    def identity(self) -> str:
        """A hash of the fixture, so a score names the fixture it was measured on."""

        return sha256_bytes(canonical_json_bytes({
            "version": BENCH_VERSION,
            "arm_id": self.arm_id,
            "selector": self.selector,
            "cases": [
                {"work_unit_id": case.work_unit_id,
                 "expected": sorted(case.expected_obligation_ids)}
                for case in sorted(self.cases, key=lambda c: c.work_unit_id)
            ],
        }))

    def report(self) -> Dict[str, Any]:
        return {
            "bench_version": BENCH_VERSION,
            "arm_id": self.arm_id,
            "concern_families": list(self.concern_families),
            "selector": self.selector,
            "fixture_sha256": self.identity(),
            "cases": len(self.cases),
            "positives": len(self.positives),
            "negatives": len(self.negatives),
            "prs": sorted({case.pr_number for case in self.cases}),
            "expected_obligations": sorted({
                item for case in self.positives for item in case.expected_obligation_ids
            }),
        }


def _units_by_change(units: Sequence[ReviewWorkUnit]) -> Dict[str, List[ReviewWorkUnit]]:
    index: Dict[str, List[ReviewWorkUnit]] = defaultdict(list)
    for unit in units:
        for change_id in unit.change_ids:
            index[change_id].append(unit)
    return index


def build_bench(
    arm_id: str,
    concern_families: Sequence[str],
    *,
    units: Sequence[ReviewWorkUnit],
    judgments: Sequence[JudgmentNode],
    pr_numbers: Optional[Sequence[int]] = None,
    negatives_per_pr: int = 3,
    audited_obligation_ids: Optional[Set[str]] = None,
) -> ArmBench:
    """The cases for one arm: units gold says it should speak at, plus quiet units.

    An obligation lands on one or more `change_id`s; a work unit is a set of change ids. A unit
    is a positive when it contains a change the obligation anchors, which is the same join the
    judge's anchor tier uses — so a bench hit and a scored hit mean the same thing.

    **Which obligations count as this arm's, and why the default is wrong.** Passing
    `audited_obligation_ids` selects from `request_groups`, where the answerable arms were read
    off the maintainer's comment. Omitting it falls back to matching the arm's concern family
    against the *gold concern label*, which is unusable for this question: 13 of PR33098's 14
    obligations carry `style`, the seven `grind` requests included. Measured across the
    development set the two selectors disagree on more than half of every arm's fixture, and on
    `family_design` they share **no** group at all — the label rule hands it one, and it is the
    wrong one. The fallback is kept only so existing callers keep their meaning; a bench that
    is meant to test a conclusion should pass the audited set.
    """

    wanted_prs = set(pr_numbers) if pr_numbers else None
    families = _gold_labels_for(concern_families)
    by_change = _units_by_change(units)

    expected_by_unit: Dict[str, Set[str]] = defaultdict(set)
    words_by_unit: Dict[str, Set[str]] = defaultdict(set)
    touched_prs: Set[int] = set()

    for judgment in judgments:
        if wanted_prs is not None and judgment.pr_number not in wanted_prs:
            continue
        touched_prs.add(judgment.pr_number)
        by_label = bool(
            families & {str(item) for item in (judgment.concern_labels or [])})
        if audited_obligation_ids is None and not by_label:
            continue
        for obligation in judgment.obligations or []:
            if (audited_obligation_ids is not None
                    and obligation.obligation_id not in audited_obligation_ids):
                continue
            for change_id in obligation.change_ids or []:
                for unit in by_change.get(change_id, ()):
                    expected_by_unit[unit.work_unit_id].add(obligation.obligation_id)
                    text = getattr(obligation, "requested_change", "") or ""
                    if text:
                        words_by_unit[unit.work_unit_id].add(text)

    bench = ArmBench(arm_id=arm_id, concern_families=sorted(families),
                     selector="audited" if audited_obligation_ids is not None else "gold_label")
    seen: Set[str] = set()
    for unit in units:
        if wanted_prs is not None and unit.pr_number not in wanted_prs:
            continue
        if unit.work_unit_id in seen:
            continue
        expected = expected_by_unit.get(unit.work_unit_id)
        if expected:
            seen.add(unit.work_unit_id)
            bench.cases.append(BenchCase(
                work_unit_id=unit.work_unit_id, pr_number=unit.pr_number,
                episode_id=unit.episode_id, change_ids=list(unit.change_ids),
                expected_obligation_ids=sorted(expected),
                expected=sorted(words_by_unit.get(unit.work_unit_id, ())),
            ))

    # Negatives: quiet units from the same PRs. Same PRs on purpose -- a negative drawn from a
    # PR the arm never sees measures nothing, and one drawn from a PR gold does cover is a
    # place a maintainer looked and asked for nothing of this kind.
    per_pr: Dict[int, int] = defaultdict(int)
    for unit in units:
        if unit.work_unit_id in seen:
            continue
        if unit.pr_number not in touched_prs:
            continue
        if per_pr[unit.pr_number] >= negatives_per_pr:
            continue
        per_pr[unit.pr_number] += 1
        seen.add(unit.work_unit_id)
        bench.cases.append(BenchCase(
            work_unit_id=unit.work_unit_id, pr_number=unit.pr_number,
            episode_id=unit.episode_id, change_ids=list(unit.change_ids)))

    bench.cases.sort(key=lambda case: (case.pr_number, case.work_unit_id))
    return bench


def audited_obligations_by_arm(release: Path) -> Dict[str, Set[str]]:
    """`arm_id -> the obligations the audited request groups say it could answer`.

    Imported lazily so this module keeps no import-time dependency on the classification, and
    so a checkout without it degrades to the gold-label fallback rather than failing.
    """

    from src.mathlib_review.analysis.request_groups import answerable_by, build

    groups = {group.group_id: group for group in build(release)}
    return {
        arm_id: {obligation
                 for group_id in group_ids
                 for obligation in groups[group_id].obligation_ids}
        for arm_id, group_ids in answerable_by(groups.values()).items()
    }


def build_all(
    release: Path,
    arms: Mapping[str, Sequence[str]],
    *,
    pr_numbers: Optional[Sequence[int]] = None,
    negatives_per_pr: int = 3,
    selector: str = "gold_label",
) -> Dict[str, ArmBench]:
    """A bench per arm, from one release.

    `arms` maps arm id to the concern families that arm may declare. It is passed in rather
    than imported: this module is evaluation, the arm registry is generation, and evaluation
    importing generation is the direction that makes gold reachable from a prompt. The caller
    supplies the roster.

    `selector="audited"` chooses positives from the audited request groups instead of the gold
    concern label. It changes the fixture substantially and on purpose: `family_design` goes
    from **1** positive to 14, `proof_idiom` from 3 to 8, and `style` — which the label rule
    floods, because 13 of PR33098's 14 obligations are labelled `style` — from 12 down to 4.
    """

    if selector not in ("gold_label", "audited"):
        raise ValueError(f"unknown bench selector {selector!r}")
    units = load_jsonl(release / "derived/work_units.jsonl", ReviewWorkUnit)
    judgments = load_jsonl(release / "gold/judgments.jsonl", JudgmentNode)
    audited = audited_obligations_by_arm(release) if selector == "audited" else {}
    return {
        arm_id: build_bench(
            arm_id, sorted(concerns),
            units=units, judgments=judgments, pr_numbers=pr_numbers,
            negatives_per_pr=negatives_per_pr,
            # An arm the audit never names still gets an audited bench -- an empty one. That
            # is the honest fixture: it says "gold asks this arm for nothing here", where
            # falling back to the label rule would silently hand it someone else's work.
            audited_obligation_ids=(audited.get(arm_id, set())
                                    if selector == "audited" else None),
        )
        for arm_id, concerns in sorted(arms.items())
    }


def coverage_report(benches: Dict[str, ArmBench]) -> Dict[str, Any]:
    """Which arms have something to be measured against, and which have nothing.

    An arm with no positives cannot be improved by its bench, and that is worth saying out
    loud rather than discovering after a paid run: it means either the release asks for
    nothing this arm owns, or the arm owns a concern gold does not use.
    """

    rows = {arm_id: bench.report() for arm_id, bench in sorted(benches.items())}
    return {
        "bench_version": BENCH_VERSION,
        "arms": rows,
        "arms_with_no_positives": sorted(
            arm_id for arm_id, row in rows.items() if not row["positives"]),
        "total_positive_cases": sum(row["positives"] for row in rows.values()),
    }


# --- scoring --------------------------------------------------------------------------------
#
# The bench's cheap signal, not a substitute for the judge. It answers "did the arm speak, and
# in the right place" -- location and silence -- which is what an arm-level iteration loop needs
# between paid semantic runs. Whether the claim is *right* is still the judge's question, and a
# bench hit is a necessary condition for a scored hit, never a sufficient one.


@dataclass
class CaseResult:
    """What one arm did on one bench case."""

    work_unit_id: str
    pr_number: int
    is_positive: bool
    #: change_ids the arm anchored candidates on.
    anchored: Sequence[str] = ()
    candidate_count: int = 0
    #: True when a positive case drew a candidate on a change the obligation anchors.
    located: bool = False
    #: True when a negative case drew any candidate at all.
    spoke_when_quiet: bool = False
    error: Optional[str] = None


def score_bench(
    bench: ArmBench,
    anchors_by_unit: Mapping[str, Sequence[str]],
    *,
    gold_anchors_by_unit: Optional[Mapping[str, Sequence[str]]] = None,
    errors_by_unit: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    """Score one arm's run over its fixture.

    `anchors_by_unit` maps work unit id to the change ids the arm anchored candidates on. The
    gold side is joined here and nowhere earlier: the arm was handed a work unit and never saw
    an obligation.
    """

    gold_anchors = dict(gold_anchors_by_unit or {})
    errors = dict(errors_by_unit or {})
    results: List[CaseResult] = []

    for case in bench.cases:
        anchored = list(anchors_by_unit.get(case.work_unit_id, ()))
        expected_anchors = set(gold_anchors.get(case.work_unit_id, case.change_ids))
        results.append(CaseResult(
            work_unit_id=case.work_unit_id,
            pr_number=case.pr_number,
            is_positive=case.is_positive,
            anchored=anchored,
            candidate_count=len(anchored),
            located=bool(case.is_positive and (set(anchored) & expected_anchors)),
            spoke_when_quiet=bool(not case.is_positive and anchored),
            error=errors.get(case.work_unit_id),
        ))

    positives = [item for item in results if item.is_positive]
    negatives = [item for item in results if not item.is_positive]
    located = sum(1 for item in positives if item.located)
    noisy = sum(1 for item in negatives if item.spoke_when_quiet)

    return {
        "bench_version": BENCH_VERSION,
        "arm_id": bench.arm_id,
        "fixture_sha256": bench.identity(),
        "positives": len(positives),
        "negatives": len(negatives),
        # Did the arm say something where gold asked for something of its kind?
        "located": located,
        "location_rate": round(located / len(positives), 4) if positives else None,
        # Did it stay quiet where gold asked for nothing of its kind?
        "spoke_when_quiet": noisy,
        # NOT a false-alarm rate, and it used to be called one. A "negative" here is a work
        # unit where *this release's gold* records no request of this kind — and maintainer
        # comment gold is a lower bound on what could legitimately have been asked, not an
        # enumeration of it. The control PR is the standing proof: 33438 was merged with no
        # comments at all and the reviewer found two compile-verified improvements there.
        # Speaking where gold is silent is therefore evidence about gold as much as about the
        # arm. `false_alarm_rate` is reserved for negatives someone has adjudicated.
        "gold_silent_speech_rate": (
            round(noisy / len(negatives), 4) if negatives else None),
        "false_alarm_rate": None,
        "negatives_are_adjudicated": False,
        "abstained_on_positives": sum(1 for item in positives if not item.candidate_count),
        "candidates_total": sum(item.candidate_count for item in results),
        "errors": {item.work_unit_id: item.error for item in results if item.error},
        "note": (
            "Location and silence only. A bench hit is a necessary condition for a scored "
            "hit, never a sufficient one -- whether the claim is correct is the judge's "
            "question and needs a semantic run."
        ),
        "cases": [
            {
                "work_unit_id": item.work_unit_id,
                "pr_number": item.pr_number,
                "positive": item.is_positive,
                "candidates": item.candidate_count,
                "located": item.located,
                "spoke_when_quiet": item.spoke_when_quiet,
                **({"error": item.error} if item.error else {}),
            }
            for item in results
        ],
    }


def gold_anchor_index(bench: ArmBench, judgments: Sequence[JudgmentNode]) -> Dict[str, List[str]]:
    """`work_unit_id -> the change ids its expected obligations actually anchor`.

    Narrower than the work unit's own change ids, so a candidate that lands anywhere in a
    multi-target unit does not count as having found the obligation's site.
    """

    wanted = {
        item for case in bench.positives for item in case.expected_obligation_ids
    }
    anchors: Dict[str, Set[str]] = defaultdict(set)
    by_obligation: Dict[str, Set[str]] = defaultdict(set)
    for judgment in judgments:
        for obligation in judgment.obligations or []:
            if obligation.obligation_id in wanted:
                by_obligation[obligation.obligation_id].update(obligation.change_ids or [])
    for case in bench.positives:
        for obligation_id in case.expected_obligation_ids:
            anchors[case.work_unit_id].update(by_obligation.get(obligation_id, ()))
    return {unit: sorted(values) for unit, values in anchors.items()}
