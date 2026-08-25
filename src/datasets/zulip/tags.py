"""
Mechanical tags: everything derivable from a message deterministically.

No model, no network, no judgement. This is the whole tag layer for v1 — semantic
tags (what *kind* of discussion this is, whether a norm was decided or contested) are
a later cached LLM pass with a reserved schema slot, because judge-free quantities are
the ones this project can trust without a noise-floor argument.

Precision choices worth knowing:

- `pr_refs` comes from linkified hrefs and from the `!4#N` / `!3#N` source spellings.
  Bare `#N` is deliberately NOT parsed from text: Zulip linkifies it when it means a
  mathlib issue/PR, and reading it unlinkified would swallow section numbers, footnote
  markers and "#1 problem".
- `decl_refs` combines two sources of very different precision, both kept because they
  fail in opposite directions: `docs#Foo` links are near-perfect but only fire when an
  author bothered to link, while backticked *dotted* identifiers catch the rest. The
  dot requirement is what keeps the second source clean — undotted backticked tokens
  are as often prose as they are declarations.
"""

import re
from typing import Iterable, List, Optional, Sequence, Set, Tuple
from urllib.parse import unquote

from .html_text import ExtractedContent

MATHLIB4_PULL = re.compile(
    r"https?://github\.com/leanprover-community/mathlib4/pull/(\d+)"
)
MATHLIB4_ISSUE = re.compile(
    r"https?://github\.com/leanprover-community/mathlib4/issues/(\d+)"
)
#: Zulip's Mathlib linkifier source spellings: `!4#12345` (mathlib4), `!3#12345`
#: (mathlib3). Present in message text and, in `144837-PR-reviews`, in topic titles.
BANG_PR = re.compile(r"!(\d)#(\d+)")

DOCS_LINK = re.compile(
    r"https?://leanprover-community\.github\.io/mathlib4_docs/find/\?pattern=([^&#\s]+)"
)
#: A backticked token with at least one dot and Lean identifier characters.
DOTTED_IDENT = re.compile(r"`([A-Za-z_][A-Za-z0-9_'!?₀-₉]*(?:\.[A-Za-z0-9_'!?₀-₉]+)+)`")
MATHLIB_FILE = re.compile(r"\b(Mathlib(?:/[A-Za-z0-9_\-]+)+\.lean)\b")



def _unique(values: Iterable[str]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            out.append(value)
    return out


def pr_refs(text: str, hrefs: Sequence[str]) -> List[int]:
    numbers: List[int] = []
    for href in hrefs:
        numbers += [int(n) for n in MATHLIB4_PULL.findall(href)]
    # `!4#N` is mathlib4; `!3#N` is the mathlib3 repo and is a different numbering
    # space, so it must not be folded in.
    numbers += [int(n) for repo, n in BANG_PR.findall(text) if repo == "4"]
    return sorted(set(numbers))


def issue_refs(text: str, hrefs: Sequence[str]) -> List[int]:
    numbers: List[int] = []
    for href in hrefs:
        numbers += [int(n) for n in MATHLIB4_ISSUE.findall(href)]
    return sorted(set(numbers))


def decl_refs(text: str, hrefs: Sequence[str]) -> List[str]:
    names: List[str] = []
    for href in hrefs:
        # The `#doc` fragment is already excluded by the pattern; percent-escapes are
        # not, and declarations legitimately contain characters that get escaped.
        names += [unquote(raw) for raw in DOCS_LINK.findall(href)]
    names += DOTTED_IDENT.findall(text)
    return _unique(sorted(set(names)))


def file_refs(text: str) -> List[str]:
    return _unique(sorted(set(MATHLIB_FILE.findall(text))))


def topic_pr_ref(topic: str) -> Optional[int]:
    """PR number encoded in a topic title, the `144837-PR-reviews` convention."""
    match = BANG_PR.search(topic)
    if match and match.group(1) == "4":
        return int(match.group(2))
    return None


def is_poll(text: str) -> bool:
    """Zulip polls render as a literal `/poll <question>` opening line."""
    return text.lstrip().startswith("/poll")


def tag_message(content: ExtractedContent) -> dict:
    """Every mechanical tag for one extracted message body."""
    langs = _unique(lang for lang, _ in content.code_blocks if lang)
    return {
        "pr_refs": pr_refs(content.text, content.hrefs),
        "issue_refs": issue_refs(content.text, content.hrefs),
        "decl_refs": decl_refs(content.text, content.hrefs),
        "file_refs": file_refs(content.text),
        "mentions": content.mentions,
        "code_langs": langs,
        "has_lean_code": any(lang.lower().startswith("lean") for lang in langs),
        "is_poll": is_poll(content.text),
        "is_reply_quote": content.has_quote,
    }


def merge_lists(values: Iterable[Sequence]) -> List:
    """Union preserving determinism: sorted, deduplicated."""
    merged: Set = set()
    for value in values:
        merged.update(value)
    return sorted(merged)


#: Tag names counted in the coverage report, so a gap is visible rather than silent.
COUNTED_TAGS: Tuple[str, ...] = (
    "pr_refs",
    "issue_refs",
    "decl_refs",
    "file_refs",
    "mentions",
    "has_lean_code",
    "is_poll",
    "is_reply_quote",
)
