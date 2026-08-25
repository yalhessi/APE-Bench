"""Subject-general naming-convention discovery over a frozen Mathlib snapshot.

The frozen `naming_contrast` operator hardcodes one subject (`Set.encard`) and one rename
(`card_` → `encard_`). That is why the coverage census scored C2 = 5/40 with nothing
outside the development PR: the *method* covers naming, but the *implementation* only
fires on one token. This module derives the subject from the target's own conclusion and
mines the snapshot for that subject's prefix norm, so the same rule reaches any subject
the corpus has an opinion about.

The purity contract is unchanged and is what makes the deterministic arm worth having:
no gold, no network, no model — a snapshot scan and lexical analysis, with every decision
traceable to counted evidence.

`naming_contrast` is deliberately left alone: it produces the frozen 0.9.1–0.9.3 smoke
releases that Phase 9 consumes, and the executor-equivalence gate found its evidence prose
is not reproducible from the generalized path.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

from ape.toolkits.code.lean.lean_parser import parse_major_declarations

from .naming_contrast import declaration_conclusion, outer_lhs

SUBJECT_CLASSIFIER_VERSION = "lean-conclusion-subject-general/1"
POPULATION_VERSION = "snapshot-subject-prefix-population/1"

#: A subject's prefix norm must be this well attested before a rename is proposed. Ported
#: unchanged from the frozen operator, where they were calibrated against the `encard`
#: population (87/91 with no counterexamples).
#: Below this many parsed modules the workspace is a partial checkout, not a snapshot.
#:
#: Mathlib is roughly six thousand modules. The review workspaces materialize the full
#: directory tree but only the files a task touches — measured at 59, 81, 113 and 229
#: `.lean` files, with `Mathlib.lean` itself truncated to three imports, so there is no
#: self-describing module count to compare against and a floor has to be stated.
#:
#: This is a correctness guard, not tidiness. A scan of ~2% of the corpus still produces
#: subjects that clear `MIN_SUPPORT`: measured, 30 subjects across those four workspaces
#: passed the strong-norm test. Those are sampling artifacts, and publishing one as a naming
#: norm would assert a repository measurement the repository was never asked.
MIN_CORPUS_FILES = 1000

MIN_SUPPORT = 20
MIN_SUPPORT_RATIO = 0.80
MAX_CONFLICT_RATIO = 0.05

_IDENT = r"[A-Za-z_][A-Za-z0-9_'!?]*"
#: Trailing projection: `(maximalSeparatedSet ε A).encard`, `K.starProjection.toLinearMap`.
_PROJECTION_RE = re.compile(rf"\.({_IDENT})\s*$")
#: Leading application head: `upperBounds (f '' S)`.
_HEAD_RE = re.compile(rf"^\(*\s*({_IDENT})")
#: A coercion ascription: `(K.orthogonalProjection : E →ₗ[𝕜] K)`.
_ASCRIPTION_RE = re.compile(r"^\(\s*(?P<expr>.+?)\s*:\s*(?P<type>.+?)\s*\)$", re.DOTALL)
#: Type arrows/constructors that name a coercion family. The token is the *arrow*, not a
#: guessed declaration name — what the corpus calls such conclusions is then measured.
_TYPE_TOKEN_RE = re.compile(r"(→ₗ|→ₐ|→\+|→\*|≃ₗ|≃ₐ|≃|→)")


@dataclass(frozen=True)
class SubjectInference:
    """What a declaration's conclusion is *about*, derived from the conclusion alone."""

    token: Optional[str]
    kind: str          # projection | application_head | coercion_ascription | unknown
    expression: Optional[str]
    confidence: str    # high | medium | low


def conclusion_subject(conclusion: str) -> SubjectInference:
    """Infer the semantic subject of a declaration's conclusion.

    Only direct left-hand-side conclusions carry a subject strong enough to name a
    declaration after; quantified and role-conditioned statements are deliberately
    rejected, exactly as the frozen operator rejects them.
    """

    lhs = outer_lhs(conclusion or "")
    if not lhs:
        return SubjectInference(None, "unknown", None, "low")
    lhs = lhs.strip()

    ascription = _ASCRIPTION_RE.match(lhs)
    if ascription:
        # `(x : T)` states that x is being viewed as a T; the subject is the coercion,
        # named by the type arrow. This is the shape a naive head rule misreads as the
        # bound variable — it is why PR 33337's second rename was previously unreachable.
        arrow = _TYPE_TOKEN_RE.search(ascription.group("type"))
        if arrow:
            return SubjectInference(arrow.group(1), "coercion_ascription", lhs, "high")
        return SubjectInference(None, "unknown", lhs, "low")

    projection = _PROJECTION_RE.search(lhs)
    if projection:
        return SubjectInference(projection.group(1), "projection", lhs, "high")

    head = _HEAD_RE.match(lhs)
    if head:
        return SubjectInference(head.group(1), "application_head", lhs, "high")
    return SubjectInference(None, "unknown", lhs, "low")


def leaf_prefix(leaf_name: str) -> str:
    """The naming segment a convention is expressed in: the leaf's first token."""

    return leaf_name.split("_", 1)[0] if "_" in leaf_name else leaf_name


@dataclass(frozen=True)
class SubjectPopulation:
    """Counted naming evidence for one subject, from a frozen snapshot."""

    subject_token: str
    prefix_counts: Counter
    members: int

    @property
    def dominant_prefix(self) -> Optional[str]:
        return self.prefix_counts.most_common(1)[0][0] if self.prefix_counts else None

    @property
    def support(self) -> int:
        prefix = self.dominant_prefix
        return self.prefix_counts.get(prefix, 0) if prefix else 0

    @property
    def support_ratio(self) -> float:
        return self.support / self.members if self.members else 0.0

    def conflict_ratio(self, prefix: str) -> float:
        return self.prefix_counts.get(prefix, 0) / self.members if self.members else 0.0

    def is_strong(self) -> bool:
        """Whether the corpus has a convention here worth holding a PR to."""

        return bool(
            self.members
            and self.support >= MIN_SUPPORT
            and self.support_ratio >= MIN_SUPPORT_RATIO
        )


@dataclass(frozen=True)
class PopulationScan:
    by_subject: Dict[str, SubjectPopulation]
    all_fullnames: Set[str]
    parsed_files: int
    parse_failures: List[str]

    def population(self, subject_token: str) -> Optional[SubjectPopulation]:
        return self.by_subject.get(subject_token)

    def is_representative(self) -> bool:
        """Whether this scan saw enough of the corpus to speak for it.

        A measurement, deliberately not enforced inside `scan_population`: callers decide
        what to do with an unrepresentative scan, and the frozen operator runs keep the
        behaviour they were sealed with.
        """

        return self.parsed_files >= MIN_CORPUS_FILES


def scan_population(workspace: Path, snapshot_sha: str) -> PopulationScan:
    """One pass over the snapshot, bucketing every direct-LHS lemma by its subject.

    The frozen operator makes the same pass but discards everything that is not `encard`.
    Keeping all subjects is what makes the rule general; the cost is one Counter per
    subject rather than one list.
    """

    mathlib = workspace / "Mathlib"
    if not mathlib.is_dir():
        raise FileNotFoundError(f"Mathlib source tree is unavailable: {mathlib}")

    buckets: Dict[str, Counter] = defaultdict(Counter)
    all_fullnames: Set[str] = set()
    failures: List[str] = []
    paths = sorted(mathlib.rglob("*.lean"))
    for path in paths:
        relative = path.relative_to(workspace).as_posix()
        try:
            source = path.read_text(encoding="utf-8")
            declarations = parse_major_declarations(source)
        except (OSError, UnicodeError, ValueError) as exc:
            failures.append(f"{relative}: {exc}")
            continue
        for declaration in declarations:
            fullname = declaration.fullname or declaration.name or ""
            if fullname:
                all_fullnames.add(fullname)
            if declaration.kind not in {"lemma", "theorem"} or not fullname:
                continue
            subject = conclusion_subject(declaration_conclusion(declaration.signature or ""))
            if subject.token is None or subject.confidence != "high":
                continue
            buckets[subject.token][leaf_prefix(fullname.rsplit(".", 1)[-1])] += 1

    return PopulationScan(
        by_subject={
            token: SubjectPopulation(token, counts, sum(counts.values()))
            for token, counts in buckets.items()
        },
        all_fullnames=all_fullnames,
        parsed_files=len(paths),
        parse_failures=failures,
    )


@dataclass(frozen=True)
class RenameProposal:
    current_fullname: str
    proposed_fullname: str
    subject_token: str
    current_prefix: str
    conventional_prefix: str
    support: int
    members: int
    conflict_count: int

    def observed_pattern(self) -> str:
        """The quantitative warrant, in the form the evidence-parity gate requires."""

        conflicts = (
            f"{self.conflict_count} `{self.current_prefix}_` examples"
            if self.conflict_count else f"no `{self.current_prefix}_` examples"
        )
        return (
            f"`{self.current_fullname}` has direct left-hand subject `{self.subject_token}` "
            f"but uses the conflicting `{self.current_prefix}_` prefix. The scoped "
            f"review-base population has {self.support}/{self.members} direct-subject "
            f"declarations with an `{self.conventional_prefix}_` leaf prefix and {conflicts}."
        )


def propose_rename(
    current_fullname: str,
    subject: SubjectInference,
    population: Optional[SubjectPopulation],
) -> Optional[RenameProposal]:
    """Propose a rename only when the corpus demonstrably disagrees with the current name.

    Returns None when the subject is unresolved, the corpus has no strong convention, the
    name already follows it, or the current prefix is itself well attested for this
    subject — that last check is what keeps the rule off legitimate alternative
    conventions, and is the main reason control PRs stay silent.
    """

    if subject.token is None or subject.confidence != "high" or population is None:
        return None
    if not population.is_strong():
        return None
    conventional = population.dominant_prefix
    if conventional is None:
        return None

    namespace, _, leaf = current_fullname.rpartition(".")
    current_prefix = leaf_prefix(leaf)
    if current_prefix == conventional:
        return None
    if population.conflict_ratio(current_prefix) > MAX_CONFLICT_RATIO:
        # The corpus tolerates this prefix for this subject; not a violation.
        return None

    remainder = leaf.split("_", 1)[1] if "_" in leaf else leaf
    proposed_leaf = f"{conventional}_{remainder}"
    proposed = f"{namespace}.{proposed_leaf}" if namespace else proposed_leaf
    if proposed == current_fullname:
        return None
    return RenameProposal(
        current_fullname=current_fullname,
        proposed_fullname=proposed,
        subject_token=subject.token,
        current_prefix=current_prefix,
        conventional_prefix=conventional,
        support=population.support,
        members=population.members,
        conflict_count=population.prefix_counts.get(current_prefix, 0),
    )
