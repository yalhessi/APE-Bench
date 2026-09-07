"""One answer to "was this available to the reviewer?".

Every retrieval source in this project answers it, and each answered it differently:

    zulip.store.gate               `timestamp_epoch >= cutoff` drop; drop if `exclude_pr` in
                                   the message's `pr_refs`
    precedent_index.eligible_mask  `_created < _iso_to_epoch(as_of)` keep; `_pr != exclude_pr`
    retrieval.eligible_precedents  `occurred < start` keep; drop if `pr_number` matches
    retrieval.validate_precedents  `occurred >= start` **raises**; same

Four spellings of one rule, three ISO parsers, and the parsers do not agree:

* `precedent_index._iso_to_epoch` returns **0** when parsing fails. Zero is before every real
  cutoff, so a row with a missing or malformed timestamp is *always eligible*. In a leak gate,
  failing open is the wrong direction, and it is the direction it fails.
* It also parses a naive timestamp through `datetime.fromisoformat(...).timestamp()`, which
  uses the machine's local time. Measured on this machine (UTC-4): `2026-08-01T12:00:00`
  resolves four hours later than the same instant does in `zulip.datetimes`, and a bare
  `2026-08-01` likewise. Whether a precedent row is eligible therefore depends on the timezone
  of the machine that built the index -- under-including here, over-including east of UTC.
  `zulip/datetimes.py` was written to avoid exactly this and says so: "A naive datetime is
  *assumed* UTC rather than localised: the alternative silently shifts every gate by the
  machine's offset."

GitHub stamps its timestamps with `Z`, so the second is latent rather than demonstrated on
today's corpus. The first is not conditional on anything.

**What is genuinely per-source, and stays.** Self-exclusion is not one rule. Zulip excludes a
message that *references* the PR under review, because a maintainer discussing it elsewhere is
still discussing it. The precedent sources exclude rows that *originate* in it. Both are right
for their source; neither was written down. `excludes_pr` takes both and says which it used.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Optional, Sequence

from src.datasets.zulip.datetimes import iso_to_epoch

#: Returned by `cutoff_epoch()` when no cutoff was requested.
NO_CUTOFF = None


class UngatedTimestamp(ValueError):
    """A row carries no usable timestamp, so the gate cannot say whether it was available.

    Raised rather than defaulted. The two available defaults are "treat as ancient", which
    admits it to every review, and "treat as now", which hides it from every review; the first
    is a leak and the second silently shrinks a corpus. Neither is a fact about the row.
    """


@dataclass(frozen=True)
class RetrievalGate:
    """The temporal and self-reference rule for one review.

    `as_of` is **exclusive**: something written at exactly the instant review began was not
    available to the reviewer beforehand. All four implementations agreed on this and none
    said it in a place the others could read.
    """

    as_of: Optional[str] = None
    exclude_pr: Optional[int] = None

    @property
    def cutoff_epoch(self) -> Optional[int]:
        """The cutoff as a UTC epoch, for a source that filters in SQL or numpy.

        A source is free to pre-filter with this and then call `allows` on what survives --
        that is what `zulip.store.search` does, over-fetching so the gate can still drop rows
        without shrinking the page. What a source must not do is treat its pre-filter as the
        decision.
        """

        return iso_to_epoch(self.as_of) if self.as_of else None

    def epoch_of(self, value: Any, *, field: str = "timestamp") -> int:
        """One parser. Raises rather than guessing, which is what `_iso_to_epoch` did."""

        if value in (None, ""):
            raise UngatedTimestamp(
                f"row has no {field}, so it cannot be dated against the retrieval cutoff")
        try:
            return iso_to_epoch(value)
        except ValueError as error:
            raise UngatedTimestamp(f"unusable {field} {value!r}") from error

    def allows_time(self, value: Any, *, field: str = "timestamp") -> bool:
        return self.cutoff_epoch is None or self.epoch_of(value, field=field) < self.cutoff_epoch

    def excludes_pr(self, *, pr_number: Optional[int] = None,
                    pr_refs: Sequence[int] = ()) -> bool:
        """Whether this row belongs to, or talks about, the PR under review.

        Both halves, because the sources need different ones and a caller that passes only
        what it has gets only that check. Zulip passes `pr_refs`; the precedent sources pass
        `pr_number`.
        """

        if self.exclude_pr is None:
            return False
        if pr_number is not None and int(pr_number) == int(self.exclude_pr):
            return True
        return int(self.exclude_pr) in {int(item) for item in pr_refs or ()}

    def allows(self, *, timestamp: Any = None, pr_number: Optional[int] = None,
               pr_refs: Sequence[int] = (), field: str = "timestamp") -> bool:
        """The whole rule for one row."""

        if self.excludes_pr(pr_number=pr_number, pr_refs=pr_refs):
            return False
        return self.allows_time(timestamp, field=field)

    def filter(self, rows: Iterable[Any], *, timestamp, pr_number=None, pr_refs=None,
               field: str = "timestamp") -> list:
        """Apply the rule to rows, given accessors for the fields it needs."""

        kept = []
        for row in rows:
            if self.allows(
                timestamp=timestamp(row),
                pr_number=pr_number(row) if pr_number else None,
                pr_refs=pr_refs(row) if pr_refs else (),
                field=field,
            ):
                kept.append(row)
        return kept
