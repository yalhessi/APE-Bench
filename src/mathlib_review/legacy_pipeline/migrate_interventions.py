"""Map legacy i5 intervention scope onto stable first-round cg1 targets."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from src.mathlib_review.release.events import payload_at_source_key
from src.mathlib_review.io import canonical_json_bytes, jsonl_bytes, pretty_json_bytes, sha256_bytes, write_once
from src.mathlib_review.paths import LEGACY_INTERVENTIONS_V5, LEGACY_V2_ANNOTATED
from src.mathlib_review.schema import (
    ChangeGraph,
    ChangeTarget,
    DatasetManifest,
    InterventionScopeMigration,
    LineSpan,
    ScopeResolution,
    SourceEvent,
)


SCOPE_MIGRATION_VERSION = "i5_cg1_mapper_v2"
_TICK_RE = re.compile(r"`([^`\n]+)`")


def _hash_id(prefix: str, value: object) -> str:
    return f"{prefix}:{sha256_bytes(canonical_json_bytes(value))}"


def intervention_scope_projection(intervention: Dict[str, Any]) -> Dict[str, Any]:
    """Allowlisted i5 fields used by scope mapping; outcomes are intentionally invisible."""
    return {
        "schema_version": intervention.get("schema_version"),
        "intervention_id": intervention.get("intervention_id"),
        "pr_number": intervention.get("pr_number"),
        "canonical_ask": intervention.get("canonical_ask") or "",
        "concern": intervention.get("concern"),
        "judgeable": bool(intervention.get("judgeable")),
        "meta": bool(intervention.get("meta")),
        "anchors": [
            {
                "hunk_id": item.get("hunk_id"),
                "path": item.get("path"),
                "line_start": item.get("line_start"),
                "line_end": item.get("line_end"),
                "inferred": bool(item.get("inferred")),
            }
            for item in intervention.get("anchors") or []
        ],
        "source_comments": [
            {
                "id": item.get("id"),
                "submitted_at": item.get("submitted_at"),
                "body": item.get("body") or "",
            }
            for item in intervention.get("source_comments") or []
        ],
    }


class GraphIndex:
    def __init__(self, graph: ChangeGraph):
        self.graph = graph
        self.entities = {item.entity_id: item for item in graph.entities}
        self.ranges = {item.range_id: item for item in graph.changed_ranges}
        self.targets = {item.change_id: item for item in graph.targets}

    @staticmethod
    def _contains(span: Optional[LineSpan], line: int) -> bool:
        return bool(span and span.line_start <= line <= span.line_end)

    @staticmethod
    def _overlaps(span: Optional[LineSpan], start: int, end: int) -> bool:
        return bool(span and span.line_start <= end and start <= span.line_end)

    def _target_entity_ids(self, target: ChangeTarget, side: str) -> List[str]:
        return target.base_entity_ids if side == "LEFT" else target.reviewed_entity_ids

    def entity_ids_for_changes(self, change_ids: Iterable[str]) -> List[str]:
        ids = set()
        for change_id in change_ids:
            target = self.targets[change_id]
            ids.update(target.base_entity_ids)
            ids.update(target.reviewed_entity_ids)
        return sorted(ids)

    def line_targets(self, path: str, line: int, side: str) -> Tuple[List[str], str]:
        entity_hits = []
        for target in self.graph.targets:
            if target.path != path:
                continue
            if any(
                self._contains(self.entities[entity_id].span, line)
                for entity_id in self._target_entity_ids(target, side)
            ):
                entity_hits.append(target)
        if entity_hits:
            declarations = [item for item in entity_hits if item.kind == "declaration"]
            selected = declarations or entity_hits
            return sorted({item.change_id for item in selected}), "review_line_entity"

        range_hits = []
        for target in self.graph.targets:
            if target.path != path:
                continue
            for range_id in target.changed_range_ids:
                changed = self.ranges[range_id]
                span = changed.old_span if side == "LEFT" else changed.reviewed_span
                if self._contains(span, line):
                    range_hits.append(target.change_id)
                    break
        if range_hits:
            return sorted(set(range_hits)), "review_line_range"

        nearest: List[Tuple[int, str]] = []
        for target in self.graph.targets:
            if target.path != path:
                continue
            distances = []
            for range_id in target.changed_range_ids:
                changed = self.ranges[range_id]
                span = changed.old_span if side == "LEFT" else changed.reviewed_span
                if span:
                    distances.append(
                        0
                        if span.line_start <= line <= span.line_end
                        else min(abs(line - span.line_start), abs(line - span.line_end))
                    )
            if distances:
                nearest.append((min(distances), target.change_id))
        if nearest and min(item[0] for item in nearest) <= 3:
            distance = min(item[0] for item in nearest)
            return sorted({change_id for value, change_id in nearest if value == distance}), (
                "review_line_nearest"
            )
        return [], "unresolved"

    def span_targets(self, path: str, start: int, end: int) -> List[str]:
        hits = []
        for target in self.graph.targets:
            if target.path != path:
                continue
            if any(
                self._overlaps(self.entities[entity_id].span, start, end)
                for entity_id in target.reviewed_entity_ids
            ):
                hits.append(target.change_id)
                continue
            if any(
                self._overlaps(self.ranges[range_id].reviewed_span, start, end)
                for range_id in target.changed_range_ids
            ):
                hits.append(target.change_id)
        return sorted(set(hits))

    def identifier_targets(self, identifier: str) -> List[str]:
        normalized = identifier.strip()
        hits = []
        for target in self.graph.targets:
            name = target.declaration_name
            if not name:
                continue
            if normalized == name or name.endswith(f".{normalized}"):
                hits.append(target.change_id)
        return sorted(set(hits))

    def axiom_targets(self) -> List[str]:
        return sorted(
            target.change_id
            for target in self.graph.targets
            if target.kind == "declaration" and target.declaration_kind == "axiom"
        )


def _resolution(
    *,
    source_kind: str,
    source_ref: str,
    method: str,
    confidence: str,
    change_ids: Sequence[str],
    index: GraphIndex,
    path: Optional[str] = None,
    line_start: Optional[int] = None,
    line_end: Optional[int] = None,
    side: Optional[str] = None,
    contributes: bool = True,
    note: Optional[str] = None,
) -> ScopeResolution:
    identity = {
        "source_kind": source_kind,
        "source_ref": source_ref,
        "path": path,
        "line_start": line_start,
        "line_end": line_end,
        "side": side,
        "method": method,
        "change_ids": sorted(change_ids),
    }
    return ScopeResolution(
        resolution_id=_hash_id("scope", identity),
        source_kind=source_kind,
        source_ref=source_ref,
        path=path,
        line_start=line_start,
        line_end=line_end,
        side=side,
        method=method,
        confidence=confidence,
        change_ids=sorted(change_ids),
        entity_ids=index.entity_ids_for_changes(change_ids),
        contributes_to_scope=contributes,
        note=note,
    )


def _load_graphs(release_dir: Path) -> Dict[int, ChangeGraph]:
    manifest = DatasetManifest.model_validate_json((release_dir / "manifest.json").read_text())
    ref = next(item for item in manifest.derived_artifacts if item.schema_version == "cg1")
    graphs = [
        ChangeGraph.model_validate_json(line)
        for line in (release_dir / ref.path).read_text().splitlines()
        if line.strip()
    ]
    return {item.pr_number: item for item in graphs if item.round_index == 1}


def _load_comments(records_path: Path) -> Dict[Tuple[int, str], Dict[str, Any]]:
    records = [json.loads(line) for line in records_path.read_text().splitlines() if line.strip()]
    return {
        (int(record["pr_number"]), str(comment["id"])): comment
        for record in records
        for comment in (record.get("gold") or {}).get("comments") or []
    }


def _legacy_event_key(event_type: str, raw_id: Any) -> Optional[str]:
    prefixes = {"review_comment": "rc", "issue_comment": "ic", "review": "review"}
    prefix = prefixes.get(event_type)
    return f"{prefix}_{raw_id}" if prefix and raw_id is not None else None


def _load_source_events(release_dir: Path, prs: set[int]) -> Dict[Tuple[int, str], str]:
    manifest = DatasetManifest.model_validate_json((release_dir / "manifest.json").read_text())
    ref = next(item for item in manifest.source_artifacts if item.schema_version == "event1")
    events = [
        SourceEvent.model_validate_json(line)
        for line in (release_dir / ref.path).read_text().splitlines()
        if line.strip() and int(json.loads(line).get("pr_number")) in prs
    ]
    bundles: Dict[str, Dict[str, Any]] = {}
    result = {}
    for event in events:
        if event.event_type not in {"review", "review_comment", "issue_comment"}:
            continue
        source_path = event.source_object.path
        if source_path not in bundles:
            bundles[source_path] = json.loads(Path(source_path).read_text())
        payload = payload_at_source_key(bundles[source_path], event.source_key)
        key = _legacy_event_key(event.event_type, payload.get("id"))
        if key:
            result[(event.pr_number, key)] = event.event_id
    return result


def map_intervention(
    intervention: Dict[str, Any],
    *,
    graph: ChangeGraph,
    comments: Dict[Tuple[int, str], Dict[str, Any]],
    source_events: Dict[Tuple[int, str], str],
) -> InterventionScopeMigration:
    projection = intervention_scope_projection(intervention)
    intervention_hash = sha256_bytes(canonical_json_bytes(projection))
    pr_number = int(projection["pr_number"])
    index = GraphIndex(graph)
    resolutions: List[ScopeResolution] = []
    exceptions = set()
    source_event_ids = []
    primary_ids = set()
    unresolved_direct = 0
    anchored_comments = 0

    for source_comment in projection["source_comments"]:
        comment_id = str(source_comment.get("id") or "")
        event_id = source_events.get((pr_number, comment_id))
        if event_id:
            source_event_ids.append(event_id)
        else:
            exceptions.add("source_event_unresolved")
        comment = comments.get((pr_number, comment_id))
        if not comment:
            exceptions.add("source_comment_missing_from_v2")
            continue
        anchor = comment.get("anchor")
        if not anchor or not anchor.get("path"):
            continue
        anchored_comments += 1
        line = anchor.get("original_line") or anchor.get("line")
        if not line:
            exceptions.add("source_anchor_missing_line")
            continue
        side = "LEFT" if str(anchor.get("side") or "RIGHT").upper() == "LEFT" else "RIGHT"
        change_ids, method = index.line_targets(str(anchor["path"]), int(line), side)
        confidence = (
            "exact"
            if method == "review_line_entity"
            else "overlap"
            if method in {"review_line_range", "review_line_nearest"}
            else "unresolved"
        )
        if change_ids:
            primary_ids.update(change_ids)
        else:
            unresolved_direct += 1
            exceptions.add("review_anchor_unmapped")
        resolutions.append(
            _resolution(
                source_kind="source_comment",
                source_ref=comment_id,
                method=method,
                confidence=confidence,
                change_ids=change_ids,
                index=index,
                path=str(anchor["path"]),
                line_start=int(line),
                line_end=int(line),
                side=side,
                note="Original GitHub review anchor in the review-time head.",
            )
        )

    identifiers = []
    for value in _TICK_RE.findall(str(projection.get("canonical_ask") or "")):
        value = value.strip()
        if value and "\n" not in value and len(value) <= 120:
            identifiers.append(value)
    for identifier in dict.fromkeys(identifiers):
        change_ids = index.identifier_targets(identifier)
        if not change_ids:
            continue
        primary_ids.update(change_ids)
        resolutions.append(
            _resolution(
                source_kind="identifier",
                source_ref=identifier,
                method="identifier_exact",
                confidence="exact",
                change_ids=change_ids,
                index=index,
                note="Exact declaration name in the canonical ask.",
            )
        )

    ask = str(projection.get("canonical_ask") or "")
    if re.search(r"\baxioms?\b", ask, re.I):
        change_ids = index.axiom_targets()
        if change_ids:
            primary_ids.update(change_ids)
            resolutions.append(
                _resolution(
                    source_kind="identifier",
                    source_ref="axiom",
                    method="axiom_declaration_kind",
                    confidence="exact",
                    change_ids=change_ids,
                    index=index,
                    note="Canonical ask names the Lean declaration kind `axiom`.",
                )
            )

    fallback_candidates = []
    for anchor in projection["anchors"]:
        path = str(anchor.get("path") or "")
        start = int(anchor.get("line_start") or 1)
        end = int(anchor.get("line_end") or start)
        change_ids = index.span_targets(path, start, end) if path else []
        contributes = not primary_ids and bool(change_ids) and len(change_ids) <= 20
        if contributes:
            fallback_candidates.extend(change_ids)
        if len(change_ids) > 20:
            exceptions.add("revision_anchor_too_broad")
        if not change_ids:
            exceptions.add("revision_anchor_unmapped")
        resolutions.append(
            _resolution(
                source_kind="i5_revision_hunk",
                source_ref=str(anchor.get("hunk_id") or ""),
                method="revision_span_overlap" if change_ids else "unresolved",
                confidence="inferred" if anchor.get("inferred") else "overlap" if change_ids else "unresolved",
                change_ids=change_ids,
                index=index,
                path=path or None,
                line_start=start,
                line_end=end,
                contributes=contributes,
                note="Legacy i5 revision-delta span; retained as fallback evidence only.",
            )
        )
    primary_ids.update(fallback_candidates)

    if projection["meta"]:
        resolutions = [
            item.model_copy(update={"contributes_to_scope": False}) for item in resolutions
        ]
        primary_ids.clear()
        resolutions.append(
            _resolution(
                source_kind="policy",
                source_ref="pr_metadata",
                method="metadata_policy",
                confidence="exact",
                change_ids=[],
                index=index,
                contributes=False,
                note="Intervention targets PR metadata rather than a code change.",
            )
        )
        exceptions.add("metadata_no_code_target")

    if not anchored_comments:
        exceptions.add("no_review_time_source_anchor")
    if not primary_ids and not projection["meta"]:
        exceptions.add("no_scope_match")
        resolutions.append(
            _resolution(
                source_kind="policy",
                source_ref="scope_exception",
                method="unresolved",
                confidence="unresolved",
                change_ids=[],
                index=index,
                contributes=False,
                note="No deterministic review-time target could be recovered.",
            )
        )

    if projection["meta"]:
        status = "metadata"
    elif not projection["judgeable"]:
        status = "not_judgeable"
    elif primary_ids and unresolved_direct:
        status = "partial"
    elif primary_ids:
        status = "resolved"
    else:
        status = "unresolved"

    resolved_changes = sorted(primary_ids)
    migration_source = {
        "version": SCOPE_MIGRATION_VERSION,
        "intervention_sha256": intervention_hash,
        "graph_id": graph.graph_id,
        "status": status,
        "resolved_change_ids": resolved_changes,
        "source_event_ids": sorted(set(source_event_ids)),
        "resolutions": [item.model_dump(mode="json") for item in resolutions],
        "exception_codes": sorted(exceptions),
    }
    return InterventionScopeMigration(
        migration_id=_hash_id("i5-cg1", migration_source),
        intervention_id=str(projection["intervention_id"]),
        pr_number=pr_number,
        episode_id=graph.episode_id,
        graph_id=graph.graph_id,
        status=status,
        resolved_change_ids=resolved_changes,
        resolved_entity_ids=index.entity_ids_for_changes(resolved_changes),
        source_event_ids=sorted(set(source_event_ids)),
        resolutions=resolutions,
        exception_codes=sorted(exceptions),
        intervention_sha256=intervention_hash,
        source_sha256=sha256_bytes(canonical_json_bytes(migration_source)),
    )


def build_scope_migrations(
    *,
    release_dir: Path,
    interventions_path: Path,
    records_path: Path,
) -> Tuple[List[InterventionScopeMigration], Dict[str, Any]]:
    interventions = [
        json.loads(line) for line in interventions_path.read_text().splitlines() if line.strip()
    ]
    graphs = _load_graphs(release_dir)
    comments = _load_comments(records_path)
    prs = {int(item["pr_number"]) for item in interventions}
    source_events = _load_source_events(release_dir, prs)
    migrations = [
        map_intervention(
            intervention,
            graph=graphs[int(intervention["pr_number"])],
            comments=comments,
            source_events=source_events,
        )
        for intervention in interventions
    ]
    statuses = Counter(item.status for item in migrations)
    methods = Counter(
        resolution.method for item in migrations for resolution in item.resolutions
    )
    exceptions = Counter(code for item in migrations for code in item.exception_codes)
    interventions_by_id = {
        str(item["intervention_id"]): item for item in interventions
    }
    review_queue = []
    for migration in migrations:
        direct = any(
            resolution.source_kind == "source_comment"
            and resolution.contributes_to_scope
            and resolution.change_ids
            for resolution in migration.resolutions
        )
        reasons = []
        if migration.status in {"unresolved", "partial"}:
            reasons.append(migration.status)
        if migration.status == "resolved" and not direct:
            reasons.append("no_direct_source_anchor")
        if len(migration.resolved_change_ids) > 10:
            reasons.append("broad_scope_over_10_targets")
        if reasons:
            intervention = interventions_by_id[migration.intervention_id]
            review_queue.append(
                {
                    "intervention_id": migration.intervention_id,
                    "pr_number": migration.pr_number,
                    "status": migration.status,
                    "reasons": reasons,
                    "canonical_ask": intervention.get("canonical_ask") or "",
                    "resolved_change_ids": migration.resolved_change_ids,
                    "exception_codes": migration.exception_codes,
                }
            )
    report = {
        "schema_version": "scope-map-audit1",
        "mapper_version": SCOPE_MIGRATION_VERSION,
        "interventions": len(migrations),
        "prs": len(prs),
        "status": dict(sorted(statuses.items())),
        "methods": dict(sorted(methods.items())),
        "exception_codes": dict(sorted(exceptions.items())),
        "resolved_change_relations": sum(len(item.resolved_change_ids) for item in migrations),
        "source_event_coverage": {
            "referenced_comments": sum(
                len(item.get("source_comments") or []) for item in interventions
            ),
            "resolved_events": sum(len(item.source_event_ids) for item in migrations),
        },
        "review_queue": review_queue,
        "unresolved": [
            {
                "intervention_id": item.intervention_id,
                "pr_number": item.pr_number,
                "status": item.status,
                "exception_codes": item.exception_codes,
            }
            for item in migrations
            if item.status in {"unresolved", "partial"}
        ],
        "migrations_sha256": sha256_bytes(jsonl_bytes(migrations)),
    }
    return migrations, report


def main() -> None:
    parser = argparse.ArgumentParser(description="Map i5 intervention scope onto v4 cg1")
    parser.add_argument("release", type=Path)
    parser.add_argument("--interventions", type=Path, default=LEGACY_INTERVENTIONS_V5)
    parser.add_argument(
        "--records",
        type=Path,
        default=LEGACY_V2_ANNOTATED,
    )
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    migrations, report = build_scope_migrations(
        release_dir=args.release,
        interventions_path=args.interventions,
        records_path=args.records,
    )
    write_once(args.out, jsonl_bytes(migrations))
    write_once(args.report, pretty_json_bytes(report))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
