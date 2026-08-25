"""Derive conservative review-time relations among changed PR targets."""

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

from ape.toolkits.code.lean.lean_parser import mask_noncode_regions

from .io import (
    canonical_json_bytes,
    jsonl_bytes,
    load_jsonl,
    pretty_json_bytes,
    sha256_bytes,
    write_once,
)
from .modification_inventory import declaration_components
from .schema import ChangeGraph, ChangeTarget, PRRelation, RelationEvidence


RELATION_VERSION = "pr-relations/1"
MIN_SHORT_IDENTIFIER = 8
MIN_FAMILY_TOKEN = 7
IGNORED_NAME_TOKENS = {
    "apply", "auxiliary", "basic", "continuous", "definition", "equiv", "lemma",
    "theorem", "instance", "property", "subset",
}


def _identifier_aliases(target: ChangeTarget) -> List[str]:
    if not target.declaration_name:
        return []
    fullname = target.declaration_name
    short = fullname.rsplit(".", 1)[-1]
    aliases = [fullname]
    if len(short) >= MIN_SHORT_IDENTIFIER and short != fullname:
        aliases.append(short)
    elif len(short) >= MIN_SHORT_IDENTIFIER:
        aliases = [short]
    return list(dict.fromkeys(aliases))


def _contains_identifier(text: str, aliases: Iterable[str]) -> Optional[str]:
    masked = mask_noncode_regions(text)
    for alias in sorted(set(aliases), key=lambda value: (-len(value), value)):
        pattern = rf"(?<![A-Za-z0-9_']){re.escape(alias)}(?![A-Za-z0-9_'])"
        if re.search(pattern, masked):
            return alias
    return None


def _namespace(name: Optional[str]) -> str:
    return (name or "").rsplit(".", 1)[0] if "." in (name or "") else ""


def _name_tokens(name: Optional[str]) -> Set[str]:
    short = (name or "").rsplit(".", 1)[-1]
    pieces = []
    for part in short.split("_"):
        pieces.extend(re.findall(r"[A-Z]+(?=[A-Z][a-z]|\b)|[A-Z]?[a-z]+|[0-9]+", part))
    return {
        token.lower()
        for token in pieces
        if len(token) >= MIN_FAMILY_TOKEN and token.lower() not in IGNORED_NAME_TOKENS
    }


def _relation(
    graph: ChangeGraph,
    kind: str,
    source: ChangeTarget,
    related: ChangeTarget,
    evidence_id: str,
) -> PRRelation:
    identity = {
        "version": RELATION_VERSION,
        "episode_id": graph.episode_id,
        "relation_kind": kind,
        "source_change_id": source.change_id,
        "related_change_ids": [related.change_id],
        "evidence_artifact_ids": [evidence_id],
    }
    digest = sha256_bytes(canonical_json_bytes(identity))
    return PRRelation(
        relation_id=f"pr-relation:{digest[:24]}",
        episode_id=graph.episode_id,
        pr_number=graph.pr_number,
        relation_kind=kind,
        source_change_id=source.change_id,
        related_change_ids=[related.change_id],
        evidence_artifact_ids=[evidence_id],
        confidence="exact" if kind in {
            "declaration_dependency", "direct_use_of_changed_declaration"
        } else "high",
        producer="deterministic",
        source_sha256=digest,
    )


def _evidence(
    graph: ChangeGraph,
    kind: str,
    source: ChangeTarget,
    related: ChangeTarget,
    match_kind: str,
    content: str,
) -> RelationEvidence:
    identity = {
        "version": RELATION_VERSION,
        "episode_id": graph.episode_id,
        "relation_kind": kind,
        "source_change_id": source.change_id,
        "related_change_id": related.change_id,
        "match_kind": match_kind,
        "source_ref": f"change-graph:{graph.graph_id}:{source.change_id}",
        "content": content,
    }
    digest = sha256_bytes(canonical_json_bytes(identity))
    return RelationEvidence(
        evidence_id=f"relation-evidence:{digest[:24]}",
        episode_id=graph.episode_id,
        pr_number=graph.pr_number,
        relation_kind=kind,
        source_change_id=source.change_id,
        related_change_id=related.change_id,
        match_kind=match_kind,
        source_ref=identity["source_ref"],
        content=content,
        source_sha256=digest,
    )


def build_relations(
    graphs: Iterable[ChangeGraph],
) -> Tuple[List[PRRelation], List[RelationEvidence]]:
    graphs = list(graphs)
    relations: List[PRRelation] = []
    evidence_rows: List[RelationEvidence] = []
    seen: Set[Tuple[str, str, str]] = set()

    def add(
        graph: ChangeGraph,
        kind: str,
        source: ChangeTarget,
        related: ChangeTarget,
        match_kind: str,
        content: str,
    ) -> None:
        key = (kind, source.change_id, related.change_id)
        if source.change_id == related.change_id or key in seen:
            return
        seen.add(key)
        evidence = _evidence(graph, kind, source, related, match_kind, content)
        evidence_rows.append(evidence)
        relations.append(_relation(graph, kind, source, related, evidence.evidence_id))

    for graph in sorted(graphs, key=lambda item: (item.pr_number, item.episode_id)):
        declarations = sorted(
            [target for target in graph.targets if target.kind == "declaration"],
            key=lambda item: item.change_id,
        )
        target_by_entity = {
            entity_id: target
            for target in declarations
            for entity_id in [*target.base_entity_ids, *target.reviewed_entity_ids]
        }
        component_cache: Dict[str, Dict[str, str]] = {}
        for source in declarations:
            components, problems = declaration_components(source.reviewed_code or source.base_code)
            component_cache[source.change_id] = {} if problems else components

        for source in declarations:
            components = component_cache[source.change_id]
            signature = components.get("statement_or_type", "")
            body = components.get("proof", "") or components.get("value_or_body", "")
            for related in declarations:
                if source.change_id == related.change_id:
                    continue
                aliases = _identifier_aliases(related)
                if not aliases:
                    continue
                signature_match = _contains_identifier(signature, aliases)
                if signature_match:
                    add(
                        graph, "declaration_dependency", source, related,
                        "signature_identifier",
                        f"Reviewed declaration signature references exact identifier `{signature_match}`.",
                    )
                body_match = _contains_identifier(body, aliases)
                if body_match:
                    add(
                        graph, "direct_use_of_changed_declaration", source, related,
                        "body_identifier",
                        f"Reviewed declaration body references exact identifier `{body_match}`.",
                    )

            for entity_id in source.context_refs:
                related = target_by_entity.get(entity_id)
                if (
                    related
                    and related.path == source.path
                    and related.declaration_kind == source.declaration_kind
                ):
                    add(
                        graph, "changed_siblings", source, related,
                        "adjacent_parser_entity",
                        "The parser change graph records the declarations as adjacent changed entities "
                        "of the same declaration kind.",
                    )

        for index, source in enumerate(declarations):
            source_tokens = _name_tokens(source.declaration_name)
            if not source_tokens:
                continue
            for related in declarations[index + 1 :]:
                if _namespace(source.declaration_name) != _namespace(related.declaration_name):
                    continue
                shared = sorted(source_tokens & _name_tokens(related.declaration_name))
                if not shared:
                    continue
                content = f"Declarations share namespace and name token(s): {', '.join(shared)}."
                add(graph, "name_family", source, related, "shared_name_token", content)
                add(graph, "name_family", related, source, "shared_name_token", content)

    relations.sort(key=lambda item: (item.pr_number, item.relation_kind, item.relation_id))
    evidence_rows.sort(key=lambda item: (item.pr_number, item.relation_kind, item.evidence_id))
    validate_relations(graphs, relations, evidence_rows)
    return relations, evidence_rows


def validate_relations(
    graphs: Iterable[ChangeGraph],
    relations: Iterable[PRRelation],
    evidence_rows: Iterable[RelationEvidence],
) -> None:
    graphs = list(graphs)
    relations = list(relations)
    evidence_rows = list(evidence_rows)
    graph_targets = {
        graph.episode_id: {target.change_id for target in graph.targets}
        for graph in graphs
    }
    evidence_by_id = {item.evidence_id: item for item in evidence_rows}
    if len(evidence_by_id) != len(evidence_rows):
        raise ValueError("relation evidence contains duplicate IDs")
    if len({item.relation_id for item in relations}) != len(relations):
        raise ValueError("PR relations contain duplicate IDs")
    for relation in relations:
        allowed = graph_targets.get(relation.episode_id, set())
        if relation.source_change_id not in allowed or not set(relation.related_change_ids) <= allowed:
            raise ValueError(f"relation escapes review episode: {relation.relation_id}")
        if not relation.evidence_artifact_ids:
            raise ValueError(f"relation lacks evidence: {relation.relation_id}")
        for evidence_id in relation.evidence_artifact_ids:
            evidence = evidence_by_id.get(evidence_id)
            if evidence is None or evidence.source_change_id != relation.source_change_id:
                raise ValueError(f"relation evidence lineage is invalid: {relation.relation_id}")


def relation_report(relations: Iterable[PRRelation], evidence: Iterable[RelationEvidence]) -> Dict:
    relations = list(relations)
    evidence = list(evidence)
    source = {
        "schema_version": "pr-relation-report1",
        "relation_version": RELATION_VERSION,
        "relations": len(relations),
        "evidence_records": len(evidence),
        "prs": len({item.pr_number for item in relations}),
        "by_kind": dict(sorted(Counter(item.relation_kind for item in relations).items())),
        "by_confidence": dict(sorted(Counter(item.confidence for item in relations).items())),
    }
    return {**source, "source_sha256": sha256_bytes(canonical_json_bytes(source))}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build conservative v4 PR relations")
    parser.add_argument("--graphs", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--evidence-out", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    relations, evidence = build_relations(load_jsonl(args.graphs, ChangeGraph))
    write_once(args.out, jsonl_bytes(relations))
    write_once(args.evidence_out, jsonl_bytes(evidence))
    report = relation_report(relations, evidence)
    write_once(args.report, pretty_json_bytes(report))
    print(json.dumps({"relations": str(args.out), **report}, indent=2))


if __name__ == "__main__":
    main()


#: The relation kinds and confidences strong enough to say two change targets are talking
#: about the same thing. Named once here because two consumers need the same answer: the
#: judge's `relation` pairing tier, and the merge that clusters findings.
#:
#: `synthesis._relation_connects` predates this and still carries its own copy. It is not
#: repointed here because `synthesis.py` is the frozen Phase 9 lineage; the merge that
#: replaces it uses this function.
STRONG_RELATION_KINDS = frozenset({
    "changed_siblings", "name_family", "direct_use_of_changed_declaration",
})
STRONG_RELATION_CONFIDENCES = frozenset({"exact", "high"})


def relation_between(
    left_change_ids: Iterable[str],
    right_change_ids: Iterable[str],
    relations: Iterable[PRRelation],
) -> Optional[str]:
    """The ID of a strong relation connecting the two change-ID sets, or None.

    Returns the relation rather than a bool so a widened pair can record *why* it was
    compared. Deterministic: the lowest matching `relation_id`, so replanning the same
    inputs yields the same justification.
    """

    left, right = set(left_change_ids), set(right_change_ids)
    if not left or not right:
        return None
    found = [
        relation.relation_id
        for relation in relations
        if relation.confidence in STRONG_RELATION_CONFIDENCES
        and relation.relation_kind in STRONG_RELATION_KINDS
        and (
            (relation.source_change_id in left
             and bool(set(relation.related_change_ids) & right))
            or (relation.source_change_id in right
                and bool(set(relation.related_change_ids) & left))
        )
    ]
    return min(found) if found else None
