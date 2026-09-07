"""Rank the work so the lead reads the interesting part first.

The agenda is a Cartesian product of arms and work units, sorted by `proposal_id` —
`wu:<hash>#<arm>` — which orders it by an opaque content hash. Paging that 40 at a time cuts
it by work unit, so a lead that reads one page sees every arm for a handful of arbitrary
units and nothing at all about the rest. On the held-out run nine of eleven leads read only
page 0; on PR 33149 that page covered **5 of 56 work units and 1 of the 23 that carried a
gold obligation**. Routing was measuring visibility, not judgment.

The census replaces the ordering, not the content. Every work unit still appears — nothing
becomes unreachable — but they arrive ranked by signals that are cheap, deterministic, and
derived only from things a reviewer can see: the changed code, the PR's own description, and
the relation graph. Nothing here reads gold.

**On the weights.** They are not calibrated; there is no held-out set to calibrate them
against that we have not already spent. They encode an ordering argument instead:

* A file that introduces an `axiom` or a `sorry` has one dominant problem and every other
  observation about it is noise until that is settled. It outranks everything.
* A PR whose own title says "golf" is telling you what its author thinks it is. PR 33285's
  title said exactly that and its golf jobs went unselected.
* Relational structure — sibling families, repeated shapes, shared name tokens — is what the
  per-declaration arms are worst at noticing and what a third of the gold asks about.
* Everything else gets a floor, so the tail is ordered rather than truncated.

If the ordering is wrong the lead can still reach anything; if it is right the lead stops
spending its first page on whatever hashed lowest.
"""

from __future__ import annotations

import collections
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence

from src.datasets.pr_review_v4.schema import (
    ChangeGraph,
    ChangeTarget,
    PRRelation,
    ReviewEpisodeInput,
    ReviewWorkUnit,
)

from src.mathlib_review.schema.review import AgendaProposal

CENSUS_VERSION = "v5-census/1"

#: Declarations that assert rather than prove. A PR adding one has a blocking problem, and
#: the maintainer comment on it is about that, not about the proof style two lines down.
_ASSERTION = re.compile(r"^\s*(?:@\[[^\]]*\]\s*)?(?:private\s+|protected\s+)?axiom\b", re.M)
_SORRY = re.compile(r"\bsorry\b")

#: What a PR says it is. Matched against title and description, which the reviewer sees.
_INTENT_KEYWORDS = {
    "golf": ("proof_golf", "proof_idiom"),
    "simplif": ("proof_golf", "proof_idiom"),
    "rename": ("naming",),
    "naming": ("naming",),
    "generalis": ("generality",), "generaliz": ("generality",),
    "deprecat": ("api_reuse", "duplication"),
    "dedup": ("duplication", "api_reuse"),
    "refactor": ("duplication", "generality"),
    "doc": ("docs",),
}

#: Relation kinds `pr_relations` already computes, and what each suggests looking at. These
#: are the cross-declaration asks the per-site arms are structurally worst at noticing.
_RELATION_ARMS = {
    "repeated_implementation_shape": ("duplication", "api_reuse", "generality"),
    "possible_wrapper_or_replacement": ("api_reuse", "duplication"),
    "name_family": ("naming",),
    "changed_siblings": ("naming", "style"),
    "direct_use_of_changed_declaration": ("api_reuse",),
    "declaration_dependency": (),
}

_WEIGHTS = {
    "introduces_axiom": 100.0,      # blocking; nothing else about the file matters first
    "introduces_sorry": 80.0,
    "pr_intent": 25.0,              # the author's own framing of the change
    "repeated_shape": 18.0,         # the relational asks, which no single-site arm sees
    "wrapper_or_replacement": 18.0,
    "name_family": 12.0,
    "changed_siblings": 8.0,
    "manual_tactic_chain": 16.0,    # proof-golf is the largest gold family, and this is
                                    # the shape maintainers actually ask to collapse
    "long_proof": 3.0,              # weak: length alone ranked a 26-line `def` above the
                                    # 8-line proof the maintainer wanted golfed
    "has_calc": 5.0,
    "added_declaration": 3.0,       # duplication/generality only apply to new code
    "baseline": 1.0,                # every unit is ranked, none is unreachable
}

#: A proof this long is worth a golf arm's attention. Weak on its own — see below.
_LONG_PROOF_LINES = 12

#: Low-level tactics that a golfed proof collapses into one combinator. Read off the two
#: proofs PR 33285's maintainer actually asked to golf — `rw` / `ext` / `simp`, and
#: `rw` / `intro` / `simp only` / `exact` — not chosen a priori.
_MANUAL_TACTICS = (
    "rw", "rewrite", "intro", "intros", "ext", "exact", "apply", "refine", "change",
    "constructor", "cases", "rcases", "obtain", "unfold", "simp only", "simp", "simpa",
    "rfl", "subst", "have", "show",
)
#: Three steps is where a chain starts looking collapsible; both gold proofs had 3 and 4.
_CHAIN_STEPS = 3

#: Golf asks target proofs. A long `def` is long because it has fields, and ranking it above
#: a short collapsible proof is what raw length did on PR 33285 — the gold proofs are 8 lines
#: and sat below a 26-line structure definition nobody commented on.
_PROVING_KINDS = {"theorem", "lemma", "example"}


@dataclass(frozen=True)
class Signal:
    name: str
    weight: float
    detail: str
    suggests: tuple = ()


def _targets_by_change(graphs: Iterable[ChangeGraph]) -> Dict[str, ChangeTarget]:
    return {t.change_id: t for graph in graphs for t in graph.targets}


def _intent_signals(episode: ReviewEpisodeInput) -> List[Signal]:
    text = f"{episode.title.text or ''} {episode.description.text or ''}".lower()
    seen, out = set(), []
    for keyword, arms in _INTENT_KEYWORDS.items():
        if keyword in text and arms not in seen:
            seen.add(arms)
            out.append(Signal("pr_intent", _WEIGHTS["pr_intent"],
                              f"the PR describes itself as {keyword!r}", arms))
    return out


def _manual_steps(code: str) -> int:
    """How many low-level tactic steps the proof body is made of.

    Deliberately crude — it counts lines whose first token is a manual tactic, after the
    `:= by`. A golfable proof is a *sequence* of small steps, which is a different thing from
    a long proof, and distinguishing them is the whole point.
    """

    body = code.split(":= by", 1)
    if len(body) < 2:
        return 0
    steps = 0
    for line in body[1].splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        for tactic in _MANUAL_TACTICS:
            if stripped == tactic or stripped.startswith(tactic + " ") \
                    or stripped.startswith(tactic + "["):
                steps += 1
                break
    return steps


def _code_signals(targets: Sequence[ChangeTarget]) -> List[Signal]:
    out: List[Signal] = []
    for target in targets:
        code = target.reviewed_code or ""
        if not code:
            continue
        name = target.declaration_name or target.path
        if _ASSERTION.search(code):
            out.append(Signal("introduces_axiom", _WEIGHTS["introduces_axiom"],
                              f"`{name}` introduces an axiom", ("correctness",)))
        if _SORRY.search(code):
            out.append(Signal("introduces_sorry", _WEIGHTS["introduces_sorry"],
                              f"`{name}` contains `sorry`", ("correctness",)))
        proves = (target.declaration_kind or "").lower() in _PROVING_KINDS
        steps = _manual_steps(code)
        if proves and steps >= _CHAIN_STEPS:
            out.append(Signal("manual_tactic_chain", _WEIGHTS["manual_tactic_chain"],
                              f"`{name}` is a chain of {steps} low-level tactic steps",
                              ("proof_golf", "proof_idiom")))
        lines = code.count("\n") + 1
        if proves and lines >= _LONG_PROOF_LINES:
            out.append(Signal("long_proof", _WEIGHTS["long_proof"],
                              f"`{name}` is {lines} lines", ("proof_golf", "proof_idiom")))
        if "calc" in code:
            out.append(Signal("has_calc", _WEIGHTS["has_calc"],
                              f"`{name}` uses a `calc` block", ("proof_golf",)))
    return out


def _relation_signals(change_ids: Sequence[str],
                      relations: Sequence[PRRelation]) -> List[Signal]:
    wanted = set(change_ids)
    grouped: Dict[str, set] = collections.defaultdict(set)
    for relation in relations:
        if relation.source_change_id in wanted or wanted & set(relation.related_change_ids):
            grouped[relation.relation_kind] |= set(relation.related_change_ids)
    label = {
        "repeated_implementation_shape": ("repeated_shape", "repeats a shape seen in"),
        "possible_wrapper_or_replacement": ("wrapper_or_replacement", "may wrap or replace"),
        "name_family": ("name_family", "shares a name family with"),
        "changed_siblings": ("changed_siblings", "was changed alongside"),
    }
    out = []
    for kind, related in sorted(grouped.items()):
        if kind not in label:
            continue
        key, phrase = label[kind]
        out.append(Signal(key, _WEIGHTS[key],
                          f"{phrase} {len(related)} other changed declaration(s)",
                          _RELATION_ARMS.get(kind, ())))
    return out


@dataclass(frozen=True)
class CensusRow:
    """One work unit, everything known about why it might be worth looking at."""

    work_unit_id: str
    pr_number: int
    episode_id: str
    rank: int
    score: float
    subjects: tuple
    signals: tuple                 # of Signal
    arms: tuple                    # arm_id -> proposal_id, as a sorted tuple of pairs
    suggested_arms: tuple          # arms the signals point at, in signal order

    def render(self) -> Dict[str, Any]:
        """The shape the lead reads. Prose, because the lead reasons over it."""

        return {
            "work_unit_id": self.work_unit_id,
            "rank": self.rank,
            "subjects": list(self.subjects),
            "why": [signal.detail for signal in self.signals] or ["no distinguishing signal"],
            "suggested_arms": list(self.suggested_arms),
            "available_arms": {arm: proposal for arm, proposal in self.arms},
        }


def build_census(
    proposals: Sequence[AgendaProposal],
    units: Sequence[ReviewWorkUnit],
    graphs: Sequence[ChangeGraph],
    episodes: Sequence[ReviewEpisodeInput],
    relations: Optional[Sequence[PRRelation]] = None,
) -> List[CensusRow]:
    """Rank every work unit. Complete by construction — nothing is dropped, only ordered."""

    targets = _targets_by_change(graphs)
    episode_by_id = {item.episode_id: item for item in episodes}
    unit_by_id = {item.work_unit_id: item for item in units}
    relations = list(relations or [])

    by_unit: Dict[str, List[AgendaProposal]] = collections.defaultdict(list)
    for proposal in proposals:
        if not proposal.mandatory:      # the floor is not a routing choice
            by_unit[proposal.work_unit_id].append(proposal)

    rows: List[tuple] = []
    for work_unit_id, unit_proposals in by_unit.items():
        unit = unit_by_id.get(work_unit_id)
        if unit is None:
            continue
        episode = episode_by_id.get(unit.episode_id)
        unit_targets = [targets[c] for c in unit.change_ids if c in targets]
        signals = _code_signals(unit_targets)
        signals += _relation_signals(unit.change_ids, relations)
        if episode is not None:
            signals += _intent_signals(episode)
        if any(t.change_id in targets and (targets[t.change_id].base_code is None)
               for t in unit_targets):
            signals.append(Signal("added_declaration", _WEIGHTS["added_declaration"],
                                  "introduces a new declaration",
                                  ("duplication", "generality")))
        score = sum(s.weight for s in signals) + _WEIGHTS["baseline"]
        signals.sort(key=lambda s: (-s.weight, s.name))
        suggested, seen = [], set()
        for signal in signals:
            for arm in signal.suggests:
                if arm not in seen:
                    seen.add(arm)
                    suggested.append(arm)
        rows.append((
            score, work_unit_id, unit, tuple(signals), tuple(suggested),
            tuple(sorted((p.arm_id, p.proposal_id) for p in unit_proposals)),
        ))

    # Ties break on work_unit_id so the ordering is total and reproducible.
    rows.sort(key=lambda row: (-row[0], row[1]))
    census = []
    for rank, (score, work_unit_id, unit, signals, suggested, arms) in enumerate(rows, 1):
        subjects = tuple(sorted({
            unit.primary_subjects_by_change.get(c) or c
            for c in unit.change_ids
        }))
        census.append(CensusRow(
            work_unit_id=work_unit_id, pr_number=unit.pr_number, episode_id=unit.episode_id,
            rank=rank, score=round(score, 3), subjects=subjects, signals=signals,
            arms=arms, suggested_arms=suggested,
        ))
    return census


def census_report(census: Sequence[CensusRow]) -> Dict[str, Any]:
    """What the ranking did, for the dry run — before any of it is acted on."""

    signal_counts = collections.Counter(
        signal.name for row in census for signal in row.signals)
    return {
        "census_version": CENSUS_VERSION,
        "work_units": len(census),
        "units_with_a_signal": sum(1 for row in census if row.signals),
        "signal_counts": dict(sorted(signal_counts.items())),
        "top": [
            {"rank": row.rank, "score": row.score, "pr": row.pr_number,
             "subjects": list(row.subjects)[:2],
             "why": [s.detail for s in row.signals][:3]}
            for row in census[:10]
        ],
    }
