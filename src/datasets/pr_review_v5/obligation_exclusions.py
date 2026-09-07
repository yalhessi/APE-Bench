"""Obligations excluded from scoring, each with the evidence that justifies it.

The release is an input and is never edited. When an obligation cannot fairly be scored, it
is named here instead — a small, explicit, reviewable list, applied at evaluation time and
reported alongside every number it changes.

**The standard is deliberately narrow.** A row belongs here only when the *release's own
artifacts* contradict it: the maintainer comment it was migrated from does not ask for what
it asks for, or its recorded outcome contradicts its own evidence. An obligation the agent
merely failed is not a defect, and excluding one because it is hard is how a benchmark is
fitted to its system. Every exclusion is decided from `obligation_audit`'s output *before*
results are read, and the reason is written down so a reader can disagree with it.

`obligation_audit.audit` flagged two rows on the heldout set; one survived reading. The other
is below.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Set


@dataclass(frozen=True)
class Exclusion:
    obligation_id: str
    pr_number: int
    reason: str


EXCLUSIONS: Sequence[Exclusion] = (
    Exclusion(
        obligation_id=(
            "obligation:0bb42bd28332beb5c9981a746053cf175213a08300871b86f8bf57e1c259d559"),
        pr_number=33321,
        reason=(
            "The obligation asks to 'revise the module-level documentation … by adding an "
            "\"Implementation details\" discussion outlining the approach taken to handle "
            "ordered coefficients'. The comment it was migrated from "
            "(event:a1e8242ebbbe634804f4474f, jcommelin) is a bare GitHub suggestion block "
            "replacing one line of prose: 'The proof needs a set of ordered coefficients, "
            "even though the ultimate existence statement does'. A suggestion block bounds "
            "the ask to its own text, and a request for a new documentation section is not "
            "in it.\n\n"
            "The row also contradicts itself. Its outcome is recorded as 'dropped' on the "
            "evidence that the module doc was 'unchanged except for a minor wording tweak "
            "(\"existence ultimate\" → \"ultimate existence\")' — which is precisely the "
            "maintainer's suggestion being adopted. An agent that made exactly the requested "
            "edit would be scored a miss for it.\n\n"
            "Status is `migration_proposal`: no curator confirmed this row."
        ),
    ),
)


def excluded_ids() -> Set[str]:
    return {item.obligation_id for item in EXCLUSIONS}


def apply(obligation_ids: Iterable[str]) -> List[str]:
    """Drop excluded obligations from a scoring scope."""

    excluded = excluded_ids()
    return [item for item in obligation_ids if item not in excluded]


def exclusion_report() -> Dict[str, object]:
    """Printed beside every number the exclusions change, so they are never silent."""

    return {
        "excluded": len(EXCLUSIONS),
        "by_pr": {item.pr_number: item.obligation_id for item in EXCLUSIONS},
        "reasons": {item.obligation_id: item.reason for item in EXCLUSIONS},
    }
