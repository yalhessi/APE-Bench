"""The three-repetition reporting protocol, as code rather than prose.

Every headline in this project is a 3-repetition measurement reported as mean, union,
and stable-across-reps — a rule adopted after the 0.9.0 baseline scored 3/6, 2/6, and
1/6 on identical inputs, and after four full-corpus runs (13, 13, 19, 12 covered) were
narrated as differences when they sat in one noise band. The rule has lived only in
`docs/research/`, which is why six modules each grew their own aggregation. This module
is the single spelling.

The mean/union gap is itself the diagnostic that motivated the systematic treatment: on
0.9.0, per-run recall was ~2/6 while the union across reps was 4/6, which says the
capability was present but under-sampled per run.

(Run-directory aggregation is deliberately *not* here yet. The six existing
implementations report genuinely different shapes, and the shared shape only becomes
knowable when `runs.py` lands and phase7/8/9 are repointed at it.)
"""

from dataclasses import dataclass, field
from math import ceil
from typing import Dict, Iterable, List, Optional, Sequence, Set


@dataclass(frozen=True)
class RepetitionSummary:
    """Mean / union / stable over repetitions of one condition."""

    repetitions: int
    denominator: int
    per_repetition_hits: List[int]
    union_ids: List[str]
    stable_ids: List[str]
    stable_min_repetitions: int
    hit_frequency: Dict[str, int] = field(default_factory=dict)

    @property
    def mean_recall(self) -> Optional[float]:
        if not self.repetitions or not self.denominator:
            return None
        return sum(self.per_repetition_hits) / self.repetitions / self.denominator

    @property
    def union_recall(self) -> Optional[float]:
        return len(self.union_ids) / self.denominator if self.denominator else None

    @property
    def stable_recall(self) -> Optional[float]:
        return len(self.stable_ids) / self.denominator if self.denominator else None

    @property
    def sampling_gap(self) -> Optional[float]:
        """Union minus mean: how much recall exists in the distribution but not per run.

        A large gap means the capability is present but under-sampled; a gap near zero
        means runs are reproducible and recall is a genuine ceiling.
        """

        if self.mean_recall is None or self.union_recall is None:
            return None
        return self.union_recall - self.mean_recall

    def as_dict(self) -> Dict:
        return {
            "repetitions": self.repetitions,
            "denominator": self.denominator,
            "per_repetition_hits": self.per_repetition_hits,
            "mean_recall": self.mean_recall,
            "union_recall": self.union_recall,
            "stable_recall": self.stable_recall,
            "stable_min_repetitions": self.stable_min_repetitions,
            "sampling_gap": self.sampling_gap,
            "union_ids": self.union_ids,
            "stable_ids": self.stable_ids,
            "hit_frequency": self.hit_frequency,
        }


def rep_summary(
    per_repetition_hit_ids: Sequence[Iterable[str]],
    denominator_ids: Iterable[str],
    *,
    stable_min_repetitions: Optional[int] = None,
) -> RepetitionSummary:
    """Summarize one condition's repetitions over a fixed denominator.

    `per_repetition_hit_ids` is one iterable of hit item IDs (obligations, typically)
    per repetition; `denominator_ids` is the eligible set. Hits outside the denominator
    are ignored so that a condition cannot inflate recall by scoring ineligible items.

    `stable_min_repetitions` defaults to the project's two-thirds rule (2 of 3).
    """

    denominator: Set[str] = set(denominator_ids)
    reps = [set(ids) & denominator for ids in per_repetition_hit_ids]
    if stable_min_repetitions is None:
        stable_min_repetitions = ceil(2 * len(reps) / 3) if reps else 0

    frequency: Dict[str, int] = {
        item: sum(item in rep for rep in reps)
        for item in sorted(denominator)
    }
    return RepetitionSummary(
        repetitions=len(reps),
        denominator=len(denominator),
        per_repetition_hits=[len(rep) for rep in reps],
        union_ids=sorted(set().union(*reps)) if reps else [],
        stable_ids=sorted(
            item for item, count in frequency.items() if count >= stable_min_repetitions
        ) if reps else [],
        stable_min_repetitions=stable_min_repetitions,
        hit_frequency={item: count for item, count in frequency.items() if count},
    )


def compare_conditions(
    summaries: Dict[str, RepetitionSummary],
) -> Dict:
    """Compare conditions on the same denominator, including their disjointness.

    Phase 9's central finding was that two arms tied on mean recall while recovering
    nearly disjoint obligations, so a comparison that reports only means is misleading;
    `combined_union` is what a routed or unioned system could reach.
    """

    denominators = {summary.denominator for summary in summaries.values()}
    if len(denominators) > 1:
        raise ValueError(f"conditions must share one denominator, got {sorted(denominators)}")
    denominator = denominators.pop() if denominators else 0
    unions = {name: set(summary.union_ids) for name, summary in summaries.items()}
    combined = sorted(set().union(*unions.values())) if unions else []
    return {
        "denominator": denominator,
        "conditions": {name: summary.as_dict() for name, summary in summaries.items()},
        "combined_union_ids": combined,
        "combined_union_recall": len(combined) / denominator if denominator else None,
        "exclusive_ids": {
            name: sorted(ids - set().union(*(
                other for other_name, other in unions.items() if other_name != name
            ))) if len(unions) > 1 else sorted(ids)
            for name, ids in unions.items()
        },
    }
