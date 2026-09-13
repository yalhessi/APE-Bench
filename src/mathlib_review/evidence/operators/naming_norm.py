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

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from ape.toolkits.code.lean.lean_parser import parse_major_declarations
from ape.toolkits.file_system.utils import walk_workspace_files

from .naming_contrast import declaration_conclusion, outer_lhs

SUBJECT_CLASSIFIER_VERSION = "lean-conclusion-subject-general/1"
POPULATION_VERSION = "snapshot-subject-prefix-population/1"

#: A subject's prefix norm must be this well attested before a rename is proposed. Ported
#: unchanged from the frozen operator, where they were calibrated against the `encard`
#: population (87/91 with no counterexamples).
#: Below this many parsed modules the workspace is a partial checkout, not a snapshot.
#:
#: Mathlib is roughly six thousand modules. The review workspaces were measured at 59, 81,
#: 113 and 229 `.lean` files, which is why this floor exists — but that count was a traversal
#: defect, not a partial checkout: `rglob` refuses to descend the overlay's symlinks, so the
#: scan saw one neighbourhood of a complete tree and said nothing about it (fixed in
#: `scan_population`; the same defect blinded `content_search`, commit `c14fa9b`). The floor
#: stays, because `Mathlib.lean` can itself be truncated to three imports and there is no
#: self-describing module count to compare against.
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
#: `infixl:80 " '' " => Set.image` -- a value-level notation and the declaration it denotes.
#: Derived from the snapshot rather than tabulated here, for the same reason the prefix norm
#: is: a name Mathlib writes with notation (`f '' S`) is named after what the notation means
#: (`image`), and only the corpus knows which is which. 300+ such operators are declared.
_VALUE_NOTATION_RE = re.compile(
    r'^\s*(?:scoped\s+)?(?:infixl|infixr|notation)[^\n=]*?'
    r'"\s*([^A-Za-z0-9\s"][^"]*?)\s*"[^\n=]*?=>\s*([A-Za-z_][\w.]*)')

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
    #: Value-level notation declared by this snapshot, operator -> denoted declaration.
    #: Empty is a valid scan; it only costs `rename_candidates` its statement-derived guess.
    notation: Dict[str, str] = field(default_factory=dict)

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
    notation: Dict[str, str] = {}
    all_fullnames: Set[str] = set()
    failures: List[str] = []
    # Not `rglob`: it does not descend symlinked directories, and a review attempt's
    # workspace is an overlay of symlinks into the shared base with only the PR's own subtree
    # materialised. That is what produced the 59-229 file counts below -- the scan was not
    # looking at a partial checkout, it was looking at a full tree through a traversal that
    # stopped at every symlink.
    paths = sorted(
        path for path in walk_workspace_files(mathlib) if path.suffix == ".lean"
    )
    for path in paths:
        relative = path.relative_to(workspace).as_posix()
        try:
            source = path.read_text(encoding="utf-8")
            declarations = parse_major_declarations(source)
        except (OSError, UnicodeError, ValueError) as exc:
            failures.append(f"{relative}: {exc}")
            continue
        if "=>" in source:
            for line in source.split("\n"):
                if "=>" not in line:
                    continue
                match = _VALUE_NOTATION_RE.match(line)
                if match:
                    notation.setdefault(match.group(1).strip(),
                                        match.group(2).rsplit(".", 1)[-1])
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
        notation=notation,
    )


def statement_head(expression: str, notation: Optional[Dict[str, str]] = None) -> Optional[str]:
    """What the subject is applied *to*: the second half of a Mathlib name.

    A name is "the head symbol and the shape of the statement, in the order they appear"
    (`encard_le_encard`, `isOpen_iUnion`). The prefix norm supplies the head; this supplies
    the shape, by reading the conclusion rather than reusing the old name's tail. That
    difference is the whole of PR 33145's resolution miss: the rule proposed
    `upperBounds_upperBounds` by keeping the old remainder, where the conclusion
    `upperBounds (f '' S) = …` says `upperBounds_image` -- `''` being `Set.image`, which the
    snapshot declares and `scan_population` collects.
    """

    text = (expression or "").strip()
    while text.startswith("(") and text.endswith(")"):
        text = text[1:-1].strip()
    if not text:
        return None
    for operator in sorted(notation or {}, key=len, reverse=True):
        # Single-character operators are far too eager: `+` appears in half of Mathlib.
        if len(operator) >= 2 and operator in text:
            # Last component, defensively: the scan stores `Set.image` as `image`, but a
            # caller passing the raw declaration would otherwise yield `set.image` as a
            # name fragment.
            denoted = (notation or {})[operator].rsplit(".", 1)[-1]
            return denoted[:1].lower() + denoted[1:] if denoted else None
    projection = _PROJECTION_RE.search(text)
    if projection:
        return projection.group(1)
    head = re.search(_IDENT, text)
    return head.group(0) if head else None


def rename_candidates(
    current_fullname: str,
    conventional_prefix: str,
    expression: Optional[str],
    notation: Optional[Dict[str, str]] = None,
) -> List[str]:
    """Ranked rename candidates for one declaration, best first.

    Two generators disagree usefully, so both are offered rather than one being guessed at:

    * **prefix swap** -- the conventional prefix with the old name's remainder. Right when the
      old name already described the statement and only its head was wrong (PR 33337:
      `coe_starProjection_eq_isComplProjection` -> `toLinearMap_starProjection_eq_…`).
    * **statement-derived** -- the conventional prefix with what the conclusion is applied to.
      Right when the old name's remainder was the thing being corrected (PR 33145:
      `continuous_upperBounds` -> `upperBounds_image`, never `upperBounds_upperBounds`).

    Measured over the release's rename asks that this operator fires on, the first is right on
    one and the second on the other; offering both puts the maintainer's name in the list for
    both. Candidates change only *what* a firing says, never *whether* it fires, so this
    cannot cost control-PR silence -- unlike widening the population test, which can.
    """

    namespace, _, leaf = current_fullname.rpartition(".")
    remainder = leaf.split("_", 1)[1] if "_" in leaf else ""
    ranked: List[str] = []

    def offer(candidate_leaf: str) -> None:
        full = f"{namespace}.{candidate_leaf}" if namespace else candidate_leaf
        if full != current_fullname and full not in ranked:
            ranked.append(full)

    if remainder:
        offer(f"{conventional_prefix}_{remainder}")
    text = (expression or "").strip()
    ascription = _ASCRIPTION_RE.match(text)
    if ascription:
        subject_of = ascription.group("expr")
    else:
        projection = _PROJECTION_RE.search(text)
        subject_of = text[: projection.start()] if projection else re.sub(_IDENT, "", text, count=1)
    applied_to = statement_head(subject_of, notation)
    if applied_to:
        offer(f"{conventional_prefix}_{applied_to}")
        tail = remainder.split("_", 1)[1] if "_" in remainder else ""
        if tail:
            offer(f"{conventional_prefix}_{applied_to}_{tail}")
    return ranked


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
    #: Further candidate names, best first, excluding `proposed_fullname`. Defaulted and
    #: appended last on purpose: `proposed_fullname` and `observed_pattern()` are what the
    #: opportunities executor reads and what the frozen naming-smoke releases sealed, and
    #: neither moves because this exists.
    alternatives: Tuple[str, ...] = ()

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


#: Where a scanned snapshot's norms are kept, beside the workspaces they were read from.
#: One file per base commit; the scan is deterministic given the snapshot, so the sha is the
#: whole key and a stale entry is impossible without the snapshot changing.
NORM_CACHE_DIR = Path("data/code_execute/norms")

NORM_INDEX_VERSION = "naming-norm-index/1"


def norm_index(
    workspace: Path,
    snapshot_sha: str,
    cache_dir: Optional[Path] = None,
    *,
    build_if_missing: bool = True,
) -> Optional[Dict[str, Any]]:
    """The snapshot's prefix norms, cached on disk: `{subject: {prefix: count}}` + notation.

    `scan_population` costs ~35 s over Mathlib's 7,400 modules, which is fine once per snapshot
    and not fine once per arm invocation. This persists the part a naming question needs --
    the per-subject prefix counts and the notation map -- and deliberately not
    `all_fullnames`, which is 214k strings and is only wanted by the collision check that runs
    in the executor, where the full scan is already in hand.

    Returns None when the snapshot is not on this machine, so a caller can degrade to asking
    the question without the counts rather than failing.
    """

    root = Path(cache_dir) if cache_dir is not None else NORM_CACHE_DIR
    path = root / f"{snapshot_sha}.json"
    if path.is_file():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if payload.get("version") == NORM_INDEX_VERSION:
                return payload
        except (OSError, ValueError):
            pass
    if not build_if_missing or not (Path(workspace) / "Mathlib").is_dir():
        # `build_if_missing=False` is for callers that must stay cheap -- a dry run should
        # read a norm that is already there and otherwise ask its question without counts,
        # not spend 36s per snapshot to build one.
        return None
    scan = scan_population(Path(workspace), snapshot_sha)
    payload = {
        "version": NORM_INDEX_VERSION,
        "snapshot_sha": snapshot_sha,
        "parsed_files": scan.parsed_files,
        "representative": scan.is_representative(),
        "notation": dict(scan.notation),
        "subjects": {
            token: dict(population.prefix_counts)
            for token, population in scan.by_subject.items()
        },
    }
    try:
        root.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    except OSError:
        pass                      # a cache that cannot be written is still a usable answer
    return payload


def norm_for(index: Optional[Dict[str, Any]], subject_token: Optional[str]) -> Optional[SubjectPopulation]:
    """The population for one subject, rebuilt from a cached index."""

    if not index or not subject_token:
        return None
    counts = (index.get("subjects") or {}).get(subject_token)
    if not counts:
        return None
    prefix_counts = Counter({str(k): int(v) for k, v in counts.items()})
    return SubjectPopulation(subject_token, prefix_counts, sum(prefix_counts.values()))


def propose_rename(
    current_fullname: str,
    subject: SubjectInference,
    population: Optional[SubjectPopulation],
    notation: Optional[Dict[str, str]] = None,
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
    ranked = rename_candidates(current_fullname, conventional, subject.expression, notation)
    return RenameProposal(
        current_fullname=current_fullname,
        proposed_fullname=proposed,
        alternatives=tuple(name for name in ranked if name != proposed),
        subject_token=subject.token,
        current_prefix=current_prefix,
        conventional_prefix=conventional,
        support=population.support,
        members=population.members,
        conflict_count=population.prefix_counts.get(current_prefix, 0),
    )
