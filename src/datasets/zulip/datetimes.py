"""
Timestamp handling. One module, because the temporal gate is the correctness
mechanism of this store and a timezone slip in it would be invisible.

Everything internal is a UTC epoch integer; everything printed is ISO-8601 UTC with
a `Z` suffix, matching the `validation.t1` / `occurred_at` spelling already used by
the PR-review datasets so an `as_of` can be passed straight through.
"""

from datetime import datetime, timezone
from typing import Union


def epoch_to_iso(epoch: Union[int, float]) -> str:
    return (
        datetime.fromtimestamp(int(epoch), timezone.utc)
        .strftime("%Y-%m-%dT%H:%M:%SZ")
    )


def iso_to_epoch(value: Union[str, int, float, datetime]) -> int:
    """Accept an epoch, a `datetime`, `YYYY-MM-DD`, or any ISO-8601 instant.

    A bare date means midnight UTC. A naive datetime is *assumed* UTC rather than
    localised: the alternative silently shifts every gate by the machine's offset.
    """
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, datetime):
        moment = value
    else:
        text = str(value).strip()
        if not text:
            raise ValueError("empty timestamp")
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            moment = datetime.fromisoformat(text)
        except ValueError as error:
            raise ValueError(f"unrecognised timestamp: {value!r}") from error
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return int(moment.astimezone(timezone.utc).timestamp())
