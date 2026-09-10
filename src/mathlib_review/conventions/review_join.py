"""Join each review comment to the situation of the code it was written about.

**Why this is the decisive component.** The largest class of conventions -- the ones maintainers
enforce in review that the codebase does not follow -- is invisible in the code at every
granularity. Dot notation is asked for in 224 dated comments and written in 14% of the
declarations it applies to. Git history shows what maintainers *did*; only review shows what
they *asked contributors for*. So "enforced" is the component that cannot be read anywhere else,
and it is only usable once a comment is attached to a *situation* rather than to a PR.

**How a comment finds its declaration.** The precedent index keeps each comment's `diff_hunk`.
Measured on all 34,640: 61% of hunks contain a declaration head outright; a further 7% name the
enclosing declaration in git's `@@ … @@ <function context>` line, which carries the header of the
declaration the hunk sits inside; 33% resolve to nothing from the hunk alone (a `variable` block,
a structure field, a proof interior whose context line is not a declaration). The 67% is the
join; the 33% is reported as unresolved, never guessed.

**What the join is not.** It is not a claim that the comment is *about* the convention the
situation suggests. A comment on a `⊆`-goal proof may be about a typo. Precision -- "a comment
in situation S whose body names form B was a request for B in S" -- is measured on a hand-read
sample before the component is used, and the number is reported with it.
"""

from __future__ import annotations

import collections
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from ape.toolkits.code.lean.lean_parser import parse_major_declarations

from src.mathlib_review.conventions.situations import SITUATIONS_VERSION, Situation, situation_of
from src.mathlib_review.paths import PRECEDENT_INDEX

REVIEW_JOIN_VERSION = "v5-review-join/1"

#: A declaration head on a diff line (`+`, `-`, or context), with attributes and modifiers.
_HEAD = re.compile(
    r"^[-+ ]?\s*(?:@\[[^\]]*\]\s*)*(?:private |protected |noncomputable |nonrec )*"
    r"(theorem|lemma|def|instance|abbrev)\s+([A-Za-z0-9_.'«»]+)", re.M)
#: git's function-context: `@@ -a,b +c,d @@ <the enclosing declaration's header line>`.
_CONTEXT = re.compile(
    r"^@@[^\n]*?@@[^\n]*?\b(theorem|lemma|def|instance|abbrev)\s+([A-Za-z0-9_.'«»]+)([^\n]*)", re.M)


@dataclass(frozen=True)
class JoinedComment:
    """One review comment, attached to the situation of the declaration it sits on."""

    comment_id: str
    pr_number: int
    created_at: str
    path: str
    commenter: Optional[str]
    body: str
    resolved_via: str            # "line" | "head" | "context" | "unresolved"
    declaration: Optional[str]
    kind: Optional[str]
    situation_keys: Dict[str, str]
    conclusion_head: Optional[str]
    predicate_head: Optional[str]
    subject_token: Optional[str]
    tactics: Sequence[str]


def _strip_diff_markers(hunk: str) -> str:
    """The hunk as source: drop the `@@` line and the leading +/-/space of each line.

    Removed lines are kept -- a comment on a deletion is about the deleted declaration.
    """

    out = []
    for line in hunk.splitlines():
        if line.startswith("@@"):
            continue
        out.append(line[1:] if line[:1] in "+- " else line)
    return "\n".join(out)


def _declaration_enclosing_line(hunk: str, position: Optional[int]) -> Optional[re.Match]:
    """The declaration head at or above the commented line, when the comment's position is known.

    GitHub's `original_position` is 1-based over the hunk's lines *after* the `@@` header. The
    precedent index dropped it, and the resolver then took *any* declaration in the hunk -- which
    is why only 27 of 50 hand-read comments were about the declaration they were joined to. The
    raw bundles keep it (`original_position`, `original_line`, `side`, `subject_type`), so a
    rebuilt index can carry it and this walks back from the commented line instead.
    """

    if position is None or position < 1:
        return None
    lines = hunk.splitlines()
    if not lines or lines[0].startswith("@@") is False:
        return None
    index = min(position, len(lines) - 1)   # lines[0] is the header; position 1 -> lines[1]
    for back in range(index, 0, -1):
        match = _HEAD.match(lines[back])
        if match:
            return match
    return None


def situate_hunk(hunk: str, position: Optional[int] = None) -> Dict[str, Any]:
    """Resolve a hunk to a declaration and its situation, saying how it was resolved.

    With `position` (the comment's `original_position`), the declaration is the one enclosing the
    commented line; without it, the first declaration in the hunk -- the coarse behaviour the
    gate measured at 27/50 about-declaration.
    """

    hunk = hunk or ""
    # 0. Line-level: the declaration whose head is at or above the commented line.
    enclosing = _declaration_enclosing_line(hunk, position)
    if enclosing:
        kind, name = enclosing.group(1), enclosing.group(2)
        # `_HEAD.match` ran on one hunk line, so `.string` is that line: the declaration header.
        header = enclosing.string.split(":=")[0]
        situation = situation_of(kind, name, header, "")
        return {"resolved_via": "line", "declaration": name, "kind": kind, "situation": situation}
    source = _strip_diff_markers(hunk)
    # 1. A full declaration inside the hunk: parse it properly.
    try:
        declarations = parse_major_declarations(source)
    except Exception:  # noqa: BLE001 -- a hunk is a fragment; the parser may object
        declarations = []
    for declaration in declarations:
        if declaration.kind in ("theorem", "lemma", "def", "instance", "abbrev"):
            situation = situation_of(
                declaration.kind, declaration.fullname or declaration.name or "",
                getattr(declaration, "signature", "") or "", getattr(declaration, "proof", "") or "")
            return {"resolved_via": "head", "declaration": declaration.fullname or declaration.name,
                    "kind": declaration.kind, "situation": situation}
    # 2. A head line without a complete body: situate from the header text alone.
    head = _HEAD.search(hunk)
    if head:
        kind, name = head.group(1), head.group(2)
        header_line = hunk[head.start():hunk.find("\n", head.start()) if "\n" in hunk[head.start():] else len(hunk)]
        situation = situation_of(kind, name, header_line.split(":=")[0], "")
        return {"resolved_via": "head", "declaration": name, "kind": kind, "situation": situation}
    # 3. git's function context names the enclosing declaration.
    context = _CONTEXT.search(hunk)
    if context:
        kind, name, rest = context.group(1), context.group(2), context.group(3)
        situation = situation_of(kind, name, rest.split(":=")[0], "")
        return {"resolved_via": "context", "declaration": name, "kind": kind, "situation": situation}
    return {"resolved_via": "unresolved", "declaration": None, "kind": None, "situation": None}


def join_comment(row: Dict[str, Any]) -> JoinedComment:
    position = row.get("original_position")
    resolved = situate_hunk(row.get("diff_hunk") or "",
                            int(position) if isinstance(position, int) else None)
    situation: Optional[Situation] = resolved["situation"]
    return JoinedComment(
        comment_id=str(row.get("comment_id")),
        pr_number=int(row.get("pr_number") or 0),
        created_at=str(row.get("created_at") or ""),
        path=str(row.get("path") or ""),
        commenter=row.get("commenter"),
        body=str(row.get("body") or ""),
        resolved_via=resolved["resolved_via"],
        declaration=resolved["declaration"],
        kind=resolved["kind"],
        situation_keys=situation.keys() if situation else {},
        conclusion_head=situation.conclusion_head if situation else None,
        predicate_head=situation.predicate_head if situation else None,
        subject_token=situation.subject_token if situation else None,
        tactics=situation.tactics if situation else (),
    )


def load_index_rows(meta: Path = PRECEDENT_INDEX / "meta.jsonl") -> List[Dict[str, Any]]:
    return [json.loads(line) for line in meta.read_text(encoding="utf-8").splitlines() if line.strip()]


def join_all(rows: Iterable[Dict[str, Any]]) -> List[JoinedComment]:
    return [join_comment(row) for row in rows]


def by_situation(joined: Iterable[JoinedComment]) -> Dict[str, List[JoinedComment]]:
    """`situation key -> comments`, the index the enforcement component reads."""

    index: Dict[str, List[JoinedComment]] = collections.defaultdict(list)
    for item in joined:
        for key in item.situation_keys.values():
            index[key].append(item)
    return dict(index)


def report(joined: Sequence[JoinedComment]) -> Dict[str, Any]:
    via = collections.Counter(item.resolved_via for item in joined)
    keys = collections.Counter(k for item in joined for k in item.situation_keys)
    return {
        "schema_version": REVIEW_JOIN_VERSION,
        "situations_version": SITUATIONS_VERSION,
        "comments": len(joined),
        "resolved_via": dict(via),
        "resolved_share": round((via["head"] + via["context"]) / max(1, len(joined)), 4),
        "situation_key_kinds": dict(keys),
        "note": (
            "A resolved comment is attached to the situation of the declaration its hunk sits "
            "on. That is a join, not a claim that the comment is about the convention the "
            "situation suggests; precision is measured separately on a hand-read sample."
        ),
    }


def write(joined: Sequence[JoinedComment], out: Path) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    (out / "joined_comments.jsonl").write_text(
        "".join(json.dumps(asdict(item), ensure_ascii=False, sort_keys=True,
                           separators=(",", ":")) + "\n" for item in joined), encoding="utf-8")
    (out / "report.json").write_text(json.dumps(report(joined), indent=2, sort_keys=True) + "\n",
                                     encoding="utf-8")
    return out


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=Path("data/pr_review_v5/review_join"))
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    joined = join_all(load_index_rows())
    payload = report(joined)
    if args.write:
        payload["written"] = str(write(joined, args.out))
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
