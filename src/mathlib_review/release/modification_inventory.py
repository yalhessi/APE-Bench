"""Build deterministic modification records from stable v4 change graphs."""

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from ape.toolkits.code.lean.lean_parser import parse_major_declarations

from src.mathlib_review.io import canonical_json_bytes, jsonl_bytes, pretty_json_bytes, sha256_bytes, write_once
from src.mathlib_review.schema import (
    ChangeGraph,
    ChangeTarget,
    ModificationComponent,
    ModificationRecord,
)


INVENTORY_VERSION = "modification-inventory/1"
DECLARATION_PARSER = "ape_lean_major_decl_components_v1"


def _hash(value: str) -> Optional[str]:
    return sha256_bytes(value.encode("utf-8")) if value else None


def _subject_kind(target: ChangeTarget) -> str:
    if target.kind == "declaration":
        kind = (target.declaration_kind or "").lower()
        if kind in {"theorem", "lemma", "axiom", "example"}:
            return "theorem"
        if kind in {"def", "opaque"}:
            return "definition"
        if kind == "instance":
            return "instance"
        if kind in {"structure", "class"}:
            return "structure_or_class"
        if kind == "inductive":
            return "inductive"
        if kind == "abbrev":
            return "abbreviation"
        return "unknown"
    return {
        "import": "import",
        "module_doc": "module_doc",
        "namespace": "namespace_or_section",
        "section": "namespace_or_section",
        "command": "command",
        "non_lean": "non_lean",
    }.get(target.kind, "unknown")


def _lifecycle(target: ChangeTarget) -> str:
    has_base = bool(target.base_entity_ids or target.base_code)
    has_reviewed = bool(target.reviewed_entity_ids or target.reviewed_code)
    if has_reviewed and not has_base:
        return "added"
    if has_base and not has_reviewed:
        return "removed"
    if has_base and has_reviewed:
        return "modified"
    if target.diff_fragments:
        return "modified"
    return "unknown"


def _visibility(target: ChangeTarget) -> str:
    if target.kind != "declaration":
        return "unknown"
    code = target.reviewed_code or target.base_code or ""
    prefix = code[: code.find(target.declaration_kind or "")]
    if re.search(r"\bprivate\b", prefix):
        return "private"
    if re.search(r"\blocal\b", prefix):
        return "local"
    return "public"


def _prefix_parts(prefix: str) -> Tuple[str, str]:
    """Split parser-external declaration prefix into docs and modifiers/attributes."""

    doc_spans = [match.span() for match in re.finditer(r"/--.*?-\/", prefix, re.S)]
    docs = "\n".join(prefix[start:end].strip() for start, end in doc_spans)
    remaining = list(prefix)
    for start, end in doc_spans:
        remaining[start:end] = " " * (end - start)
    attributes = "".join(remaining).strip()
    return docs, attributes


def _comment_text(code: str) -> str:
    comments = re.findall(r"--[^\n]*|/-.*?-\/", code, re.S)
    return "\n".join(comment.strip() for comment in comments if comment.strip())


def declaration_components(code: Optional[str]) -> Tuple[Dict[str, str], List[str]]:
    """Return parser-backed coarse declaration components and explicit parse problems."""

    if not code:
        return {}, []
    declarations = parse_major_declarations(code)
    if len(declarations) != 1:
        return {}, [f"expected_one_major_declaration_found_{len(declarations)}"]
    declaration = declarations[0]
    start, _end = declaration.span
    prefix = code[:start]
    _prefix_documentation, attributes = _prefix_parts(prefix)
    documentation = _comment_text(code)
    signature = declaration.signature
    if declaration.name_span and declaration.name:
        name_start = declaration.name_span[0] - start
        name_end = declaration.name_span[1] - start
        if 0 <= name_start <= name_end <= len(signature):
            signature = signature[:name_start] + "<DECL_NAME>" + signature[name_end:]
        else:
            return {}, ["declaration_name_span_outside_signature"]
    components = {
        "name": declaration.fullname or declaration.name or "",
        "statement_or_type": signature.strip(),
        "documentation": documentation,
        "attributes": attributes,
    }
    body_kind = (
        "proof"
        if declaration.kind in {"theorem", "lemma", "example"}
        else "value_or_body"
    )
    components[body_kind] = declaration.proof.strip()
    return {key: value for key, value in components.items() if value}, []


def _structural_components(target: ChangeTarget, code: Optional[str]) -> Dict[str, str]:
    if not code:
        return {}
    component = {
        "import": "imports",
        "module_doc": "documentation",
        "namespace": "namespace",
        "section": "namespace",
        "whitespace": "layout",
    }.get(target.kind, "value_or_body" if target.kind == "command" else "unknown")
    return {component: code}


def _structural_fragment_side(target: ChangeTarget, marker: str) -> str:
    lines = []
    for fragment in target.diff_fragments:
        for line in fragment.splitlines():
            if line.startswith(marker) and not line.startswith(marker * 3):
                lines.append(line[1:])
    return "\n".join(lines)


def _component_rows(
    target: ChangeTarget,
) -> Tuple[List[ModificationComponent], List[str]]:
    if target.kind == "declaration":
        base, base_problems = declaration_components(target.base_code)
        reviewed, reviewed_problems = declaration_components(target.reviewed_code)
        problems = [f"base:{value}" for value in base_problems] + [
            f"reviewed:{value}" for value in reviewed_problems
        ]
        if problems:
            return [ModificationComponent(
                component="unknown",
                status="unknown",
                base_sha256=_hash(target.base_code or ""),
                reviewed_sha256=_hash(target.reviewed_code or ""),
                classifier=DECLARATION_PARSER,
            )], problems
    else:
        base_code = target.base_code or _structural_fragment_side(target, "-")
        reviewed_code = target.reviewed_code or _structural_fragment_side(target, "+")
        base = _structural_components(target, base_code)
        reviewed = _structural_components(target, reviewed_code)
        problems = ["unparsed_change_target"] if target.parse_status == "unparsed" else []
        if problems:
            return [ModificationComponent(
                component="unknown",
                status="unknown",
                base_sha256=_hash(target.base_code or ""),
                reviewed_sha256=_hash(target.reviewed_code or ""),
                classifier=DECLARATION_PARSER,
            )], problems

    rows = []
    for component in sorted(set(base) | set(reviewed)):
        base_value = base.get(component, "")
        reviewed_value = reviewed.get(component, "")
        if base_value and not reviewed_value:
            status = "removed"
        elif reviewed_value and not base_value:
            status = "added"
        elif base_value == reviewed_value:
            status = "unchanged"
        else:
            status = "modified"
        rows.append(ModificationComponent(
            component=component,
            status=status,
            base_sha256=_hash(base_value),
            reviewed_sha256=_hash(reviewed_value),
            classifier=DECLARATION_PARSER,
        ))
    if not rows:
        rows.append(ModificationComponent(
            component="unknown",
            status="unknown",
            classifier=DECLARATION_PARSER,
        ))
        problems.append("no_classifiable_component")
    return rows, problems


def build_inventory(graphs: Iterable[ChangeGraph]) -> List[ModificationRecord]:
    graphs = list(graphs)
    records = []
    for graph in sorted(graphs, key=lambda item: (item.pr_number, item.episode_id)):
        for target in sorted(graph.targets, key=lambda item: item.change_id):
            components, problems = _component_rows(target)
            identity = {
                "version": INVENTORY_VERSION,
                "episode_id": graph.episode_id,
                "pr_number": graph.pr_number,
                "primary_change_id": target.change_id,
                "target_source_sha256": target.source_sha256,
                "subject_kind": _subject_kind(target),
                "lifecycle": _lifecycle(target),
                "visibility": _visibility(target),
                "component_deltas": [item.model_dump(mode="json") for item in components],
                "unknown_reasons": problems,
            }
            digest = sha256_bytes(canonical_json_bytes(identity))
            records.append(ModificationRecord(
                modification_id=f"modification:{digest[:24]}",
                episode_id=graph.episode_id,
                pr_number=graph.pr_number,
                primary_change_id=target.change_id,
                subject_kind=identity["subject_kind"],
                lifecycle=identity["lifecycle"],
                visibility=identity["visibility"],
                component_deltas=components,
                classification_status="complete" if not problems else "unknown",
                unknown_reasons=problems,
                source_sha256=digest,
            ))
    validate_inventory(graphs, records)
    return records


def validate_inventory(
    graphs: Iterable[ChangeGraph], records: Iterable[ModificationRecord]
) -> None:
    expected = {
        target.change_id: (graph.episode_id, graph.pr_number)
        for graph in graphs
        for target in graph.targets
    }
    records = list(records)
    actual = [item.primary_change_id for item in records]
    if len(actual) != len(set(actual)):
        raise ValueError("modification inventory contains duplicate primary change IDs")
    if set(actual) != set(expected):
        raise ValueError(
            f"modification coverage mismatch: missing={sorted(set(expected) - set(actual))} "
            f"extra={sorted(set(actual) - set(expected))}"
        )
    for item in records:
        episode_id, pr_number = expected[item.primary_change_id]
        if (item.episode_id, item.pr_number) != (episode_id, pr_number):
            raise ValueError(f"modification points at the wrong episode: {item.modification_id}")
        if item.lifecycle == "modified" and not any(
            component.status != "unchanged" for component in item.component_deltas
        ):
            raise ValueError(f"modified target has no changed component: {item.modification_id}")


def inventory_report(records: Iterable[ModificationRecord]) -> Dict:
    records = list(records)
    changed_components = Counter(
        component.component
        for item in records
        for component in item.component_deltas
        if component.status != "unchanged"
    )
    source = {
        "schema_version": "modification-inventory-report1",
        "inventory_version": INVENTORY_VERSION,
        "records": len(records),
        "prs": len({item.pr_number for item in records}),
        "by_subject_kind": dict(sorted(Counter(item.subject_kind for item in records).items())),
        "by_lifecycle": dict(sorted(Counter(item.lifecycle for item in records).items())),
        "by_classification_status": dict(sorted(
            Counter(item.classification_status for item in records).items()
        )),
        "changed_components": dict(sorted(changed_components.items())),
        "unknown_reasons": dict(sorted(Counter(
            reason for item in records for reason in item.unknown_reasons
        ).items())),
    }
    return {**source, "source_sha256": sha256_bytes(canonical_json_bytes(source))}


def _load_graphs(path: Path) -> List[ChangeGraph]:
    return [ChangeGraph.model_validate_json(line) for line in path.read_text().splitlines() if line]


def main() -> None:
    parser = argparse.ArgumentParser(description="Build deterministic v4 modification inventory")
    parser.add_argument("--graphs", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    records = build_inventory(_load_graphs(args.graphs))
    write_once(args.out, jsonl_bytes(records))
    report = inventory_report(records)
    write_once(args.report, pretty_json_bytes(report))
    print(json.dumps({"inventory": str(args.out), **report}, indent=2))


if __name__ == "__main__":
    main()
