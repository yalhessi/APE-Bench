"""Temporally safe, content-ranked maintainer precedent retrieval."""

import json
import math
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Set, Tuple

from .events import payload_at_source_key
from .io import canonical_json_bytes, sha256_bytes
from .schema import (
    ChangeGraph,
    PromptPrecedent,
    ReviewEpisodeBoundary,
    RetrievalCutoff,
    ReviewRoundSegment,
    ReviewWorkUnit,
    SourceEvent,
)


PROMPT_PRECEDENT_CORPUS_VERSION = "maintainer-context-to-ask-bm25/1"
_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_']{2,}")
_CAMEL_BOUNDARY_RE = re.compile(r"([a-z0-9])([A-Z])")
_UNRESOLVED_CONTEXT_RE = re.compile(
    r"\b(same here|same as|as above|ditto|likewise|same comment)\b", re.IGNORECASE
)
_STOP_TERMS = {
    "all", "and", "are", "can", "change", "could", "def", "for", "from", "fun",
    "have", "here", "into", "its", "lemma", "let", "mathlib", "more", "not", "one",
    "only", "review", "same", "set", "should", "target", "that", "the", "then", "theorem",
    "this", "two", "use", "used", "using", "was", "when", "where", "which", "with", "would",
    "you", "your",
}
_LEAN_IDIOMS = {
    "aesop", "all_goals", "apply", "by_cases", "by_contra", "calc", "cases", "change",
    "classical", "constructor", "contrapose", "convert", "exact", "ext", "field_simp",
    "funext", "grind", "have", "induction", "intro", "let", "linarith", "norm_num",
    "obtain", "omega", "push_neg", "rcases", "refine", "rfl", "rw", "rwa", "simp",
    "simpa", "specialize", "subst", "suffices",
}
_DISTINCTIVE_IDIOMS = {
    "all_goals", "by_cases", "by_contra", "calc", "contrapose", "field_simp", "funext",
    "grind", "linarith", "norm_num", "obtain", "omega", "push_neg", "rcases", "rwa",
    "specialize", "suffices",
}


def load_reviewer_roster(path: Path) -> Set[str]:
    return {
        line.strip().lower()
        for line in path.read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def build_retrieval_cutoffs(segments: Iterable[ReviewRoundSegment]) -> List[RetrievalCutoff]:
    cutoffs = []
    for segment in segments:
        if not segment.episode_id or segment.hydration_status != "hydrated":
            continue
        identity = {
            "episode_id": segment.episode_id,
            "repo": segment.repo,
            "pr_number": segment.pr_number,
            "review_started_at": segment.review_started_at,
            "source_segment_id": segment.segment_id,
        }
        digest = sha256_bytes(canonical_json_bytes(identity))
        cutoffs.append(RetrievalCutoff(
            cutoff_id=f"cutoff:{digest[:24]}", source_sha256=digest, **identity
        ))
    if len({item.episode_id for item in cutoffs}) != len(cutoffs):
        raise ValueError("retrieval cutoffs contain duplicate episode IDs")
    return cutoffs


def lexical_terms(text: str) -> List[str]:
    """Keep exact Lean identifiers and their components for transparent lexical transfer."""
    terms = []
    for raw in _TOKEN_RE.findall(text):
        exact = raw.lower().strip("'")
        if len(exact) >= 3 and exact not in _STOP_TERMS:
            terms.append(exact)
        split = _CAMEL_BOUNDARY_RE.sub(r"\1 \2", raw).replace("_", " ").replace("'", " ")
        terms.extend(
            item for item in split.lower().split()
            if len(item) >= 3 and item not in _STOP_TERMS and item != exact
        )
    return terms


def idiom_terms(text: str) -> List[str]:
    return [raw.lower().strip("'") for raw in _TOKEN_RE.findall(text)
            if raw.lower().strip("'") in _LEAN_IDIOMS]


def _payload_text(event: SourceEvent) -> str:
    path = Path(event.source_object.path)
    payload = payload_at_source_key(json.loads(path.read_text()), event.source_key)
    if isinstance(payload, dict):
        return str(payload.get("body") or "")
    return str(payload)


def _prompt_precedent_payload(event: SourceEvent) -> Tuple[str, str, str, bool]:
    payload = payload_at_source_key(
        json.loads(Path(event.source_object.path).read_text()), event.source_key
    )
    if not isinstance(payload, dict):
        return str(payload), "", "", False
    body = str(payload.get("body") or "").strip()
    diff_hunk = str(payload.get("diff_hunk") or "").strip()
    lines = diff_hunk.splitlines()
    if len(lines) > 40:
        lines = [lines[0], *lines[-39:]]
    context = "\n".join(lines)
    return body, context, str(payload.get("path") or ""), payload.get("in_reply_to_id") is not None


def _target_query(target) -> str:
    return "\n".join([
        target.declaration_name or "",
        target.path,
        target.base_code or "",
        target.reviewed_code or "",
    ])


def _bm25_rank(query: str, rows: List[Tuple[SourceEvent, str, List[str]]]):
    if not rows:
        return []
    query_terms = set(lexical_terms(query))
    document_frequency = Counter(term for _event, _body, terms in rows for term in set(terms))
    average_length = sum(len(terms) for _event, _body, terms in rows) / len(rows)
    ranked = []
    for event, body, terms in rows:
        frequencies = Counter(terms)
        matched = sorted(query_terms.intersection(frequencies))
        score = 0.0
        for term in matched:
            frequency = frequencies[term]
            inverse_frequency = math.log(
                1 + (len(rows) - document_frequency[term] + 0.5)
                / (document_frequency[term] + 0.5)
            )
            denominator = frequency + 1.2 * (
                1 - 0.75 + 0.75 * len(terms) / max(average_length, 1)
            )
            score += inverse_frequency * frequency * 2.2 / denominator
            if term in _LEAN_IDIOMS:
                score += inverse_frequency * 1.5
        transfers_distinctive_idiom = bool(set(matched).intersection(_DISTINCTIVE_IDIOMS))
        compound_matches = [term for term in matched if "_" in term]
        idiom_matches = set(matched).intersection(_LEAN_IDIOMS)
        if score > 0 and (
            transfers_distinctive_idiom or compound_matches or len(idiom_matches) >= 2
            or len(matched) >= 4
        ):
            ranked.append((score, event, body, matched))
    return sorted(ranked, key=lambda row: (-row[0], row[1].occurred_at or "", row[1].event_id))


def build_prompt_precedents(
    units: Iterable[ReviewWorkUnit],
    graphs: Iterable[ChangeGraph],
    cutoffs: Iterable[RetrievalCutoff],
    events: Iterable[SourceEvent],
    reviewer_logins: Set[str],
    limit_per_target: int = 1,
) -> List[PromptPrecedent]:
    """Retrieve prior human maintainer asks without consulting judgment or outcome artifacts."""
    units, graphs, cutoffs, events = list(units), list(graphs), list(cutoffs), list(events)
    graph_by_id = {graph.graph_id: graph for graph in graphs}
    cutoff_by_episode = {item.episode_id: item for item in cutoffs}
    corpus = []
    for event in events:
        if event.event_type != "review_comment" or not event.occurred_at:
            continue
        if not event.actor or event.actor.lower() not in reviewer_logins:
            continue
        body, context, context_path, is_reply = _prompt_precedent_payload(event)
        terms = lexical_terms(context)
        if (body and context and context_path and terms and not is_reply
                and not _UNRESOLVED_CONTEXT_RE.search(body)):
            corpus.append((event, body, terms, context, context_path))

    precedents = []
    for unit in units:
        cutoff_record = cutoff_by_episode.get(unit.episode_id)
        if cutoff_record is None:
            raise ValueError(f"missing retrieval cutoff for {unit.episode_id}")
        # Same rule as `eligible_precedents`, from the same place. It was spelled out here a
        # third time, with the same local-time parse.
        rule = _rule(cutoff_record.review_started_at, unit.pr_number)
        eligible_rows = [
            row for row in corpus
            if not rule.excludes_pr(pr_number=row[0].pr_number)
            and rule.allows_time(row[0].occurred_at, field="occurred_at")
        ]
        eligible = [(event, body, terms) for event, body, terms, _context, _path in eligible_rows]
        context_by_event = {
            event.event_id: (context, context_path)
            for event, _body, _terms, context, context_path in eligible_rows
        }
        graph = graph_by_id[unit.graph_id]
        target_by_id = {target.change_id: target for target in graph.targets}
        for change_id in unit.change_ids:
            query = _target_query(target_by_id[change_id])
            query_sha256 = sha256_bytes(query.encode())
            rank = 0
            for score, event, body, matched in _bm25_rank(query, eligible):
                rank += 1
                context, context_path = context_by_event[event.event_id]
                identity = {
                    "corpus_version": PROMPT_PRECEDENT_CORPUS_VERSION,
                    "work_unit_id": unit.work_unit_id,
                    "primary_change_id": change_id,
                    "target_episode_id": unit.episode_id,
                    "target_pr_number": unit.pr_number,
                    "cutoff_at": cutoff_record.review_started_at,
                    "source_event_id": event.event_id,
                    "source_pr_number": event.pr_number,
                    "source_event_type": event.event_type,
                    "actor": event.actor,
                    "occurred_at": event.occurred_at,
                    "context_path": context_path,
                    "context": context,
                    "context_sha256": sha256_bytes(context.encode()),
                    "body": body,
                    "body_sha256": sha256_bytes(body.encode()),
                    "query_sha256": query_sha256,
                    "matched_terms": matched,
                    "lexical_score": round(score, 8),
                    "rank": rank,
                }
                digest = sha256_bytes(canonical_json_bytes(identity))
                precedents.append(PromptPrecedent(
                    precedent_id=f"precedent:{digest[:24]}", source_sha256=digest, **identity
                ))
                if rank >= limit_per_target:
                    break
    return precedents


#: Event types that carry a maintainer's opinion. A commit or a label is not a precedent.
PRECEDENT_EVENT_TYPES = frozenset({"review", "review_comment", "issue_comment"})


def _rule(review_started_at: str, pr_number: int):
    """The retrieval rule, from the one place it is defined."""

    from src.mathlib_review.retrieval_gate import RetrievalGate

    return RetrievalGate(as_of=review_started_at, exclude_pr=pr_number)


def _gate_for(target: ReviewEpisodeBoundary):
    """This episode's retrieval rule, from the one place it is defined.

    Both functions below used to parse `review_started_at` and every event's `occurred_at`
    with `datetime.fromisoformat(x.replace("Z", "+00:00"))`. That handles the `Z` spelling and
    nothing else: a naive timestamp resolves in the machine's local time, so eligibility
    depended on where the code ran. See `mathlib_review/retrieval_gate.py`.
    """

    return _rule(target.review_started_at, target.pr_number)


def validate_precedents(target: ReviewEpisodeBoundary, events: Iterable[SourceEvent]) -> List[SourceEvent]:
    """The paranoid pass: selected rows are re-checked, and a future one is an error.

    Deliberately not the same shape as `eligible_precedents`. That one filters, because a
    global ledger legitimately contains rows this episode may not see; this one raises,
    because a row that reached selection and is in the future means the filter did not run.
    """

    rule = _gate_for(target)
    safe = []
    for event in events:
        if rule.excludes_pr(pr_number=event.pr_number) or not event.occurred_at:
            continue
        if not rule.allows_time(event.occurred_at, field="occurred_at"):
            raise ValueError(f"future precedent {event.event_id} for {target.episode_id}")
        if event.event_type in PRECEDENT_EVENT_TYPES:
            safe.append(event)
    return safe


def eligible_precedents(target: ReviewEpisodeBoundary,
                        events: Iterable[SourceEvent]) -> List[SourceEvent]:
    """Filter a global ledger before ranking; selected rows are validated again."""

    rule = _gate_for(target)
    eligible = []
    for event in events:
        if rule.excludes_pr(pr_number=event.pr_number) or not event.occurred_at:
            continue
        if (rule.allows_time(event.occurred_at, field="occurred_at")
                and event.event_type in PRECEDENT_EVENT_TYPES):
            eligible.append(event)
    return eligible


def retrieve_payloads(target: ReviewEpisodeBoundary, events: Iterable[SourceEvent],
                      query: str, limit: int = 6) -> List[Tuple[SourceEvent, str]]:
    rows = []
    for event in eligible_precedents(target, events):
        path = Path(event.source_object.path)
        payload = payload_at_source_key(json.loads(path.read_text()), event.source_key)
        text = str(payload.get("body") or payload.get("state") or "") if isinstance(payload, dict) else str(payload)
        rows.append((event, text))
    terms = set(re.findall(r"[a-z0-9_]{3,}", query.lower()))
    selected = sorted(rows, key=lambda row: (
        -len(terms.intersection(set(re.findall(r"[a-z0-9_]{3,}", row[1].lower())))),
        row[0].occurred_at or "", row[0].event_id,
    ))[:limit]
    validate_precedents(target, [event for event, _text in selected])
    return selected


def lexical_rank(query: str, events: Iterable[SourceEvent], limit: int = 6) -> List[SourceEvent]:
    """Rank only source metadata here; payload rendering remains a separate hashed artifact."""
    terms = set(re.findall(r"[a-z0-9_]{3,}", query.lower()))
    return sorted(events, key=lambda event: (
        -len(terms.intersection(set(re.findall(r"[a-z0-9_]{3,}", event.source_key.lower())))),
        event.occurred_at or "", event.event_id,
    ))[:limit]
