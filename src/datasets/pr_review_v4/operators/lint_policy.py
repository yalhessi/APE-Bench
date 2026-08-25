"""Mathlib's text-based style lints and repository policy, reimplemented over change targets.

The first version of this module implemented exactly one rule (line length) while claiming
the name of a whole convention family. Mathlib actually enforces about nineteen style
rules, so a one-rule checker was not a principled scope — it was whichever rule the
motivating PR happened to need.

The rule set here is transcribed from Mathlib's own linters at the reviewed snapshot:

* `scripts/lint-style.py` and `Mathlib/Tactic/Linter/TextBased.lean` — the text-based
  linters: adaptation notes, Windows line endings, trailing whitespace, space before a
  semicolon, non-breaking spaces, isolated `by`, isolated `where`, a leading colon, and a
  missing space after `←`.
* `Mathlib/Tactic/Linter/Style.lean` — the syntax-tree linters. Only the two decidable from
  a single line are reimplemented: `longLine` and `lambdaSyntax`.

Four rules are deliberately **not** reimplemented, because a lexical guess would cost the
precision that is this arm's whole differentiator:

* `setOption`, `missingEnd`, `openClassical`, `show`, `cdotLinter`, `dollarSyntax` need the
  parse tree — `$` and `·` occur inside strings and docstrings, and `missingEnd` needs the
  whole file rather than one target's reviewed span.
* `ERR_IND` (second-line indentation) needs to know where a declaration begins; change
  targets are hunk-level, so the first reviewed line is often mid-declaration.

Error codes match Mathlib's own (`ERR_TWS`, `ERR_IBY`, …) so a finding is traceable to the
rule the project already publishes, rather than to a convention we invented.

Mathlib's own note on these linters is worth keeping in view: they are "enabled in mathlib
by default, but disabled globally since they enforce conventions which are inherently
subjective." That is why a lint hit is evidence for a review request, not proof of one —
and why only lines the PR actually touched are examined.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional

from ..schema import ChangeTarget

LINT_VERSION = "mathlib-text-style/1"
POLICY_VERSION = "mathlib-repository-policy/1"

#: `Mathlib/Tactic/Linter/Style.lean`: the `longLine` linter warns above 100 characters.
MAX_LINE_LENGTH = 100

FORBIDDEN_DECLARATION_KINDS = {"axiom"}
_SORRY_RE = re.compile(r"(?<![A-Za-z0-9_'])sorry(?![A-Za-z0-9_'])")

_ARROW_RE = re.compile(r"←(?:(?=``?\()|(?![%`\s]))(\S)")
_ADAPTATION_RE = re.compile(r"adaptation note", re.IGNORECASE)
_TRAILING_WS_RE = re.compile(r"[ \t]+$")
_SPACE_SEMICOLON_RE = re.compile(r" ;")
_HANGING_BY_RE = re.compile(r", fun [^,]* (=>|↦)$")


@dataclass(frozen=True)
class LintHit:
    """One rule violation on one reviewed line."""

    code: str
    line_number: int
    message: str
    text: str


def _check_line(index: int, line: str, previous: Optional[str]) -> List[LintHit]:
    hits: List[LintHit] = []

    if line.endswith("\r"):
        hits.append(LintHit("ERR_WIN", index, "Line ends with a Windows line ending", line))
        # Every later rule wants the logical line; a carriage return would otherwise be
        # counted toward the length limit and mask the trailing-whitespace rule.
        line = line[:-1]
    stripped = line.strip()

    # `Style.lean:441` exempts any line containing "http" — a URL cannot be wrapped.
    if len(line) > MAX_LINE_LENGTH and "http" not in line:
        hits.append(LintHit("ERR_LIN", index,
                            f"Line is {len(line)} characters; the limit is {MAX_LINE_LENGTH}", line))
    if _TRAILING_WS_RE.search(line):
        hits.append(LintHit("ERR_TWS", index, "Line ends with trailing whitespace", line))
    if _SPACE_SEMICOLON_RE.search(line):
        hits.append(LintHit("ERR_SEM", index, "Line contains a space before a semicolon", line))
    if " " in line:
        hits.append(LintHit("ERR_NSP", index, "Line contains a non-breaking space", line))
    if _ADAPTATION_RE.search(line):
        hits.append(LintHit("ERR_ADN", index, "Line contains an adaptation note", line))

    # Isolated `by`, excusing the hanging-`by` forms Mathlib's linter excuses.
    if stripped == "by":
        prior = (previous or "").rstrip()
        if not prior.endswith(",") and not _HANGING_BY_RE.search(prior):
            hits.append(LintHit("ERR_IBY", index, "Line is an isolated 'by'", line))
    elif line.lstrip().startswith("by ") and (previous or "").rstrip().endswith(":="):
        # Mathlib only reports this when the previous line is short enough to absorb the
        # `by`; longer lines have no obvious auto-fix and are left alone.
        if len((previous or "").rstrip()) <= 97:
            hits.append(LintHit("ERR_IBY", index, "'by' should end the previous line", line))
    if line.lstrip() == "where":
        hits.append(LintHit("ERR_IWH", index, "Line is an isolated 'where'", line))
    if line.lstrip().startswith(":"):
        hits.append(LintHit("ERR_CLN", index,
                            "Put ':' and ':=' before line breaks, not after", line))
    if _ARROW_RE.search(line):
        hits.append(LintHit("ERR_ARR", index, "Missing space after '←'", line))
    if "λ" in line:
        hits.append(LintHit("ERR_LAM", index, "Use 'fun' rather than 'λ'", line))
    return hits


@dataclass(frozen=True)
class LintFinding:
    path: str
    hits: List[LintHit]

    @property
    def codes(self) -> List[str]:
        return sorted({hit.code for hit in self.hits})

    def observed_pattern(self) -> str:
        by_code: Dict[str, List[LintHit]] = {}
        for hit in self.hits:
            by_code.setdefault(hit.code, []).append(hit)
        parts = [
            f"{code} on line{'s' if len(items) > 1 else ''} "
            f"{', '.join(str(item.line_number) for item in items[:4])}"
            f"{'…' if len(items) > 4 else ''} ({items[0].message})"
            for code, items in sorted(by_code.items())
        ]
        return (
            f"`{self.path}` violates {len(by_code)} Mathlib text-style "
            f"lint{'s' if len(by_code) > 1 else ''} on {len(self.hits)} reviewed "
            f"line{'s' if len(self.hits) > 1 else ''}: " + "; ".join(parts) + "."
        )

    def requested_change(self) -> str:
        return (
            f"Fix the Mathlib style-lint violations in `{self.path}` "
            f"({', '.join(self.codes)}) on the lines this PR touched."
        )


def lint_target(target: ChangeTarget) -> Optional[LintFinding]:
    """Run the reimplemented text-style rules over a target's reviewed source.

    Only `reviewed_code` is examined. A pre-existing violation is not this review's
    business, and restricting to touched content is what keeps the rule silent on control
    PRs instead of reporting whole files.
    """

    code = target.reviewed_code
    if not code:
        return None
    # Split on "\n" rather than `splitlines()`: the latter also consumes "\r", which would
    # make the Windows-line-ending rule unable to ever fire.
    lines = code.split("\n")
    hits: List[LintHit] = []
    for index, line in enumerate(lines, start=1):
        hits.extend(_check_line(index, line, lines[index - 2] if index >= 2 else None))
    return LintFinding(target.path, hits) if hits else None


def find_long_lines(target: ChangeTarget, limit: int = MAX_LINE_LENGTH) -> Optional[LintFinding]:
    """Backwards-compatible view: only the `longLine` rule."""

    finding = lint_target(target)
    if finding is None:
        return None
    hits = [hit for hit in finding.hits if hit.code == "ERR_LIN"]
    return LintFinding(finding.path, hits) if hits else None


@dataclass(frozen=True)
class ForbiddenConstructFinding:
    path: str
    declaration_name: Optional[str]
    construct: str

    def observed_pattern(self) -> str:
        name = (
            f"`{self.declaration_name}`" if self.declaration_name
            else f"a declaration in `{self.path}`"
        )
        return (
            f"{name} introduces a new `{self.construct}`, which adds an unproved assumption "
            f"to the library."
        )

    def requested_change(self) -> str:
        name = f"`{self.declaration_name}`" if self.declaration_name else "the declaration"
        return (
            f"Remove {name} and derive the result instead, either by proving it or by using "
            f"an existing Mathlib lemma, so the file introduces no `{self.construct}`."
        )


def find_forbidden_construct(target: ChangeTarget) -> Optional[ForbiddenConstructFinding]:
    """Report a newly introduced `axiom`, or a `sorry` left in a proof.

    Only when the PR *introduces* it: an `axiom` that was already there and is being moved
    is not this review's finding.
    """

    kind = (target.declaration_kind or "").lower()
    reviewed = target.reviewed_code or ""
    base = target.base_code or ""

    if kind in FORBIDDEN_DECLARATION_KINDS and reviewed and not base:
        return ForbiddenConstructFinding(target.path, target.declaration_name, kind)
    if _SORRY_RE.search(reviewed) and not _SORRY_RE.search(base):
        return ForbiddenConstructFinding(target.path, target.declaration_name, "sorry")
    return None
