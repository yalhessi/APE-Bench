"""What a review comment is: every rule the PR pipelines used to spell separately, written once.

`docs/research/review-task-spec.md` §3.1 defines a reviewer on PR `p` by three rules: not a bot,
not the PR author, and on the curated roster -- with `author_association ∈ {MEMBER, OWNER,
COLLABORATOR}` as fallback. The release builder implemented all three. The retrieval corpus
(`pr_review_v2/corpus.py: keep_comment`) implemented neither of the last two, and the cost was
measured on the 201 cached bundles: of 115 comments it kept, 44 were PR authors replying on their
own PRs (a collaborator authoring a PR still carries `COLLABORATOR`), and it dropped 144 comments
by roster reviewers GitHub reports as `CONTRIBUTOR`, because GitHub reports `MEMBER` only for
*public* org membership. Recall 71/215, precision 71/115.

That was one of fourteen divergences. Before this module there were five copies of the
association set (one comparing without `.upper()`), four bot predicates (two disagreeing on an
empty login), three `.lean` predicates over three different objects, two copies of the trivial-
feedback patterns, and five roster loaders. Every copy is now a caller of this one.

Two predicates keep separate names because they answer different questions, and conflating them
is how the `.lean` filters diverged:

* `is_mathlib_lean_file` -- does a PR *change* Mathlib source? The funnel's content gate, over the
  PR's changed files.
* `is_lean_anchor` -- is a *comment* anchored on a Lean file? The corpus gate, over the comment's
  path, deliberately any directory (`Archive/`, `test/`, `Counterexamples/` are Lean review too).

`is_bot` in `src/datasets/zulip/identity.py` is not a copy of this one and must not become one: it
matches display names (`Mathlib Bot`) where this matches GitHub logins.
"""

from __future__ import annotations

import collections
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, FrozenSet, Iterable, Literal, Mapping, Optional

from ape.utils.project import PROJECT_ROOT
from src.mathlib_review.io import sha256_file
from src.mathlib_review.paths import V2_EVAL_SET, V4_RELEASES

DEFINITIONS_VERSION = "pull-review-definitions/1"

# --- identity ------------------------------------------------------------------------------

MAINTAINER_ASSOCIATIONS: FrozenSet[str] = frozenset({"MEMBER", "OWNER", "COLLABORATOR"})

#: Bot logins beyond the `[bot]` / `-bot` suffixes. From spec §3.1's explicit denylist.
BOT_LOGINS: FrozenSet[str] = frozenset({
    "bors", "github-actions", "leanprover-community-bot", "leanprover-community-mathlib4-bot",
})


def is_bot(login: Optional[str]) -> bool:
    """A GitHub login that is not a person. An absent login counts as a bot: a comment with no
    author cannot be attributed to a reviewer, so it must not be counted as one."""

    lowered = str(login or "").lower()
    return (not lowered or lowered.endswith("[bot]") or lowered.endswith("-bot")
            or lowered in BOT_LOGINS)


def load_roster(path: Path) -> FrozenSet[str]:
    """Lower-cased logins, one per line; `#` lines are comments (including `# UNMAPPED: …`)."""

    return frozenset(
        line.strip().lower()
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    )


def roster_sha256(path: Path) -> str:
    """The roster a projection used, recorded in its manifest -- membership is time-varying, so a
    number is only interpretable relative to the snapshot it was computed against."""

    return sha256_file(Path(path))


ReviewerBasis = Literal["roster", "association", "both", "none"]
Exclusion = Literal["no_login", "bot", "pr_author", "not_roster_or_association"]


@dataclass(frozen=True)
class CommenterClass:
    """Why a commenter is or is not a reviewer. `basis` is computed whatever the exclusion, so an
    author who is a collaborator reads `basis="association", excluded="pr_author"` -- the exact
    case the corpus used to keep."""

    is_reviewer: bool
    basis: ReviewerBasis
    excluded: Optional[Exclusion]


def classify_commenter(
    login: Optional[str], association: Optional[str], pr_author: Optional[str],
    roster: Iterable[str], *, use_association_fallback: bool = True,
) -> CommenterClass:
    """Spec §3.1, all three rules. `roster` must already be lower-cased (`load_roster` does it)."""

    lowered = str(login or "").lower()
    on_roster = bool(lowered) and lowered in roster
    by_association = str(association or "").upper() in MAINTAINER_ASSOCIATIONS
    basis: ReviewerBasis = ("both" if on_roster and by_association else "roster" if on_roster
                            else "association" if by_association else "none")
    if not lowered:
        return CommenterClass(False, basis, "no_login")
    if is_bot(lowered):
        return CommenterClass(False, basis, "bot")
    if lowered == str(pr_author or "").lower():
        return CommenterClass(False, basis, "pr_author")
    if on_roster or (use_association_fallback and by_association):
        return CommenterClass(True, basis, None)
    return CommenterClass(False, basis, "not_roster_or_association")


def is_reviewer(
    login: Optional[str], association: Optional[str], pr_author: Optional[str],
    roster: Iterable[str], *, use_association_fallback: bool = True,
) -> bool:
    return classify_commenter(login, association, pr_author, roster,
                              use_association_fallback=use_association_fallback).is_reviewer


@dataclass
class ReviewerAudit:
    """Spec threat #7: *"roster drift on old PRs -- report roster-vs-association disagreement
    rate"*. The eval side kept a counter of association-only reviewers; the corpus side had none,
    which is how its 44 author replies and 144 missing roster reviewers went unreported."""

    decisions: collections.Counter = field(default_factory=collections.Counter)

    def record(self, decision: CommenterClass) -> CommenterClass:
        self.decisions[(decision.is_reviewer, decision.basis, decision.excluded)] += 1
        return decision

    def report(self) -> Dict[str, Any]:
        by_basis: Dict[str, int] = collections.Counter()
        excluded: Dict[str, int] = collections.Counter()
        for (ok, basis, reason), n in self.decisions.items():
            if ok:
                by_basis[basis] += n
            else:
                excluded[reason or "unknown"] += n
        total_reviewers = sum(by_basis.values())
        return {
            "definitions_version": DEFINITIONS_VERSION,
            "reviewers": total_reviewers,
            "reviewers_by_basis": dict(by_basis),
            "association_only_share": (round(by_basis.get("association", 0) / total_reviewers, 4)
                                       if total_reviewers else None),
            "roster_only_share": (round(by_basis.get("roster", 0) / total_reviewers, 4)
                                  if total_reviewers else None),
            "excluded": dict(excluded),
        }


# --- substance ------------------------------------------------------------------------------

#: Delegation/merge commands: a command-only message sets the verdict but is not a finding (§3.2).
APPROVAL_SIGNAL_RE = re.compile(r"\bbors\s+(?:merge|r\+|d\+|d=)|\bmaintainer\s+merge\b", re.I)

TRIVIAL_FEEDBACK_PATTERNS = (
    r"\bmaintainer\s+merge\b",
    r"\bbors\s+(?:merge|r\+|d\+|d=)",
    r"\blgtm\b",
    r"\blooks good(?: to me)?\b",
    r"\bthanks?\b",
    r"\bthank you\b",
    r":\w+:",  # :emoji: shortcodes
)


def strip_trivial_tokens(body: Any) -> str:
    """The body with approvals, thanks, emoji and punctuation removed; empty means no content."""

    text = re.sub(r"\s+", " ", str(body or "").strip().lower())
    for pattern in TRIVIAL_FEEDBACK_PATTERNS:
        text = re.sub(pattern, " ", text)
    text = re.sub(r"[`*_>#:\-.,!?()\[\]{}\"'/\\~+]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def is_substantive_text(body: Any) -> bool:
    return bool(strip_trivial_tokens(body))


def is_substantive_event(event: Mapping[str, Any]) -> bool:
    """A review requesting changes is substantive even with an empty body (spec §3.2)."""

    return event.get("state") == "CHANGES_REQUESTED" or is_substantive_text(event.get("body"))


# --- files and titles -----------------------------------------------------------------------

TOOLCHAIN_ONLY_FILES: FrozenSet[str] = frozenset({
    "lean-toolchain", "lakefile.lean", "lakefile.toml", "lake-manifest.json",
})
REVERT_TITLE_RE = re.compile(r"^\s*revert\b", re.I)
BORS_MERGED_TITLE_RE = re.compile(r"^\s*\[merged by bors\](?:\s|-|$)", re.I)
BORS_TITLE_PREFIX_RE = re.compile(r"^\s*\[(?:merged|closed) by bors\]\s*-?\s*", re.I)


def is_mathlib_lean_file(path: Optional[str]) -> bool:
    """A changed file that is Mathlib source -- the funnel's content gate."""

    text = str(path or "")
    return text.startswith("Mathlib/") and text.endswith(".lean")


def is_lean_anchor(path: Optional[str]) -> bool:
    """A comment anchored on any Lean file -- the corpus gate. Case-insensitive and any
    directory, exactly as the corpus has always collected, so the new corpus stays a superset."""

    return str(path or "").lower().endswith(".lean")


def clean_title(title: Any) -> str:
    """Remove post-hoc Mathlib/bors outcome prefixes from a model-visible title."""

    return BORS_TITLE_PREFIX_RE.sub("", str(title or "")).strip()


def clean_description(body: Any) -> str:
    """Remove PR-template boilerplate (HTML comments, `---`, gitpod badges) from a description."""

    text = str(body or "").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    kept = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "---" or "gitpod.io/" in stripped.lower():
            continue
        kept.append(line.rstrip())
    return re.sub(r"\n{3,}", "\n\n", "\n".join(kept)).strip()


# --- the scored set ---------------------------------------------------------------------------

def scored_pr_numbers(*, root: Path = PROJECT_ROOT) -> FrozenSet[int]:
    """Every PR the system is scored on: the v2 eval set and every release manifest's PRs.

    A comment from one of these is the answer rather than a precedent, so it must not reach the
    corpus whatever its timestamp says. The predecessor, `mathlib_review.corpus.eval_pr_numbers`,
    read a *relative* path and returned an empty set when it was missing, justified by "the date
    cutoff is the primary exclusion". Once the corpus ran into December that stopped being true,
    and a wrong working directory silently disabled the only exclusion left. So: anchored at the
    repo root, and a missing eval set raises.
    """

    eval_set = root / V2_EVAL_SET
    if not eval_set.is_file():
        raise FileNotFoundError(
            f"the scored-PR set is missing ({eval_set}); refusing to return an empty exclusion, "
            "which would let the answers into the corpus")
    numbers = {
        int(json.loads(line)["pr_number"])
        for line in eval_set.read_text(encoding="utf-8").splitlines() if line.strip()
    }
    for manifest in sorted((root / V4_RELEASES).glob("*/manifest.json")):
        numbers.update(int(n) for n in json.loads(manifest.read_text(encoding="utf-8"))
                       .get("pr_numbers") or ())
    return frozenset(numbers)
