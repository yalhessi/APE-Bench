"""
Compact, citable rendering of messages and threads.

Every rendered message leads with its permalink and date so that anything read here
can be cited back to the source — the same discipline the review pipeline applies to
precedent evidence. Author lines carry the maintainer flag, because "who said it"
is most of what makes a Zulip statement norm-bearing.

The same function serves human browsing now and prompt injection later; keeping one
renderer means what a person reviewed is what a model would be shown.
"""

from typing import Iterable, List, Optional, Sequence

from .schema import ZulipMessage, ZulipThread

RULE = "─" * 78


def render_message(message: ZulipMessage, *, indent: str = "", body: bool = True) -> str:
    role = " [maintainer]" if message.sender_is_maintainer else ""
    handle = f" (@{message.sender_github})" if message.sender_github else ""
    head = f"{indent}{message.sender_full_name}{handle}{role} — {message.timestamp}"
    lines = [head, f"{indent}{message.permalink}"]
    if body:
        lines.append("")
        lines += [f"{indent}{line}" if line else indent for line in message.text.split("\n")]
    return "\n".join(lines).rstrip()


def _unique(values: Iterable) -> List:
    """First-appearance order, no duplicates. Deterministic, so a rendering is reproducible."""

    seen, out = set(), []
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out


def render_thread(
    thread: ZulipThread,
    messages: Sequence[ZulipMessage],
    *,
    truncated: bool = False,
    max_messages: Optional[int] = None,
) -> str:
    # EVERY summary line is computed from `messages`, never from `thread`.
    #
    # `thread` is the row the builder wrote over the whole thread, so its aggregates describe
    # messages the gate has just removed. Measured against the 33337 cutoff over the 400
    # threads that span it: `last_ts` and `message_count` were post-cutoff in 100% of them
    # (one header would have printed 2026-06-16, nearly six months past the cutoff), `pr_refs`
    # in 29%, `maintainer_participants` in 28%, and `decl_refs` in 22% -- the last being a
    # declaration name from the future handed to an arm whose whole job is to judge a name.
    # `messages` is already gated by `ZulipStore._view`, so deriving from it is correct both
    # here and for an ungated human browse, where the two sets coincide.
    ordered = list(messages)
    span = f"{ordered[0].timestamp} .. {ordered[-1].timestamp}" if ordered else "(no messages)"
    count = f"{len(ordered)} message(s)" + (" (prefix)" if truncated else "")
    header = [
        RULE,
        f"#{thread.stream} > {thread.topic}",
        f"{count} | {span}",
    ]
    maintainers = _unique(m.sender_full_name for m in ordered if m.sender_is_maintainer)
    if maintainers:
        header.append(f"maintainers: {', '.join(maintainers)}")
    decl_refs = _unique(ref for m in ordered for ref in (m.decl_refs or []))
    if decl_refs:
        shown = decl_refs[:12]
        suffix = f" (+{len(decl_refs) - 12} more)" if len(decl_refs) > 12 else ""
        header.append(f"declarations: {', '.join(shown)}{suffix}")
    pr_refs = _unique(ref for m in ordered for ref in (m.pr_refs or []))
    if pr_refs:
        header.append(f"PRs: {', '.join('#' + str(n) for n in pr_refs)}")
    if truncated:
        header.append(
            "NOTE: filtered by the temporal gate — this is a prefix, not the whole thread."
        )
    header.append(thread.archive_url)
    header.append(RULE)

    shown_messages: Iterable[ZulipMessage] = messages
    omitted = 0
    if max_messages is not None and len(messages) > max_messages:
        shown_messages = messages[:max_messages]
        omitted = len(messages) - max_messages

    body: List[str] = [render_message(m) for m in shown_messages]
    if omitted:
        body.append(f"… {omitted} further message(s) not shown")
    return "\n".join(header) + "\n\n" + "\n\n".join(body) + "\n"


def render_hits(messages: Sequence[ZulipMessage], *, snippet: int = 320) -> str:
    """One-block-per-hit rendering for search results."""
    blocks = []
    for message in messages:
        text = message.text.replace("\n", " ").strip()
        if len(text) > snippet:
            text = text[:snippet].rstrip() + "…"
        role = " [maintainer]" if message.sender_is_maintainer else ""
        blocks.append(
            f"#{message.stream} > {message.topic}\n"
            f"  {message.sender_full_name}{role} — {message.timestamp}\n"
            f"  {text}\n"
            f"  {message.permalink}"
        )
    return "\n\n".join(blocks)
