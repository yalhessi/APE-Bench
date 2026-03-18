import re
from typing import Any, Dict, Optional

from ape.toolkits.code.lean.lean_parser import mask_noncode_regions, parse_major_declarations

from .ape_bench_parser_taxonomy import compute_ape_bench_parser_taxonomy


def _signature_binder_total_proxy(signature: str) -> int:
    if not signature:
        return 0
    masked = mask_noncode_regions(signature)
    masked = re.sub(r"@\[[^\]]*\]", " ", masked)
    return masked.count("(") + masked.count("{") + masked.count("[")


def _bin_small_med_large(n: int) -> str:
    if n <= 2:
        return "0–2"
    if n <= 6:
        return "3–6"
    return "≥7"


def _infer_statement_signature_bins(theorem_statement: str) -> Dict[str, Any]:
    decls = parse_major_declarations(theorem_statement) if theorem_statement else []
    if not decls:
        return {"binder_total": 0, "binder_total_bin": "0–2"}
    best = max(decls, key=lambda d: len(getattr(d, "signature", "") or ""))
    binder_total = _signature_binder_total_proxy(getattr(best, "signature", "") or "")
    return {"binder_total": int(binder_total), "binder_total_bin": _bin_small_med_large(int(binder_total))}


def annotate_record_metadata(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Attach taxonomy tags to `record["metadata"]` (in-place) and return the record.

    This is designed to be called during dataset conversion / construction.
    """
    metadata = record.get("metadata") or {}
    if not isinstance(metadata, dict):
        metadata = {}
    record["metadata"] = metadata

    task_type = record.get("task_type") or ""
    taxonomy: Dict[str, Any] = {
        "task_type": task_type,
        "dataset": metadata.get("dataset"),
    }

    if task_type == "lean_proof_engineering":
        original_code = record.get("original_code") or ""
        reference = record.get("reference_implementation") or ""
        gold_diff = record.get("gold_diff") or ""
        filename = record.get("filename")

        if gold_diff and reference:
            taxonomy.update(
                {
                    "task_family": "proof_engineering",
                    "edit_regime": "file_patch",
                }
            )
            parser_tax = compute_ape_bench_parser_taxonomy(
                original_code=original_code,
                reference_implementation=reference,
                gold_diff=gold_diff,
                filename=filename,
            )
            primary = (parser_tax.get("decl_change") or {}).get("task_archetype", "unknown")
            taxonomy["primary_archetype"] = primary
            taxonomy["additive_flavor"] = (parser_tax.get("decl_change") or {}).get("additive_flavor", "n/a")
            taxonomy["instance_related"] = bool((parser_tax.get("decl_change") or {}).get("instance_related", False))
            taxonomy["import_change_type"] = parser_tax.get("import_change_type", "unknown")
            taxonomy["touched_span_bin"] = (parser_tax.get("diff_localization") or {}).get("touched_span_new_ratio_bin", "unknown")
            taxonomy["header_body_focus"] = (parser_tax.get("diff_localization") or {}).get("header_body_focus_new", "unknown")
            taxonomy["math_domain"] = parser_tax.get("math_domain", "Other")
            taxonomy["diff_primary_category"] = parser_tax.get("diff_primary_category", "unknown")
            taxonomy["proof_tactic_primary"] = (parser_tax.get("proof_tactic_proxy") or {}).get(
                "added_proof_primary_tactic_family", "none"
            )
            taxonomy["ape_bench_parser"] = parser_tax
        else:
            # Hole-filling / new-file style proof engineering tasks (e.g., miniCTX, autoformalization).
            taxonomy.update(
                {
                    "task_family": "proof_engineering",
                    "edit_regime": "new_file" if not original_code else "hole_filling",
                }
            )
            taxonomy["primary_archetype"] = taxonomy["edit_regime"]

            if original_code:
                masked = mask_noncode_regions(original_code)
                taxonomy["hole_count"] = int(len(re.findall(r"\bsorry\b", masked)))
            else:
                taxonomy["hole_count"] = 0

            # If there is a theorem statement in the file, extract a signature proxy.
            taxonomy["statement_signature"] = _infer_statement_signature_bins(original_code)

    elif task_type == "lean_theorem_proving":
        statement = record.get("theorem_statement") or ""
        taxonomy.update(
            {
                "task_family": "theorem_proving",
                "edit_regime": "theorem_proving",
                "primary_archetype": "theorem_proving",
                "statement_signature": _infer_statement_signature_bins(statement),
            }
        )

    elif task_type == "lean_judgment":
        target_code = record.get("target_code") or ""
        taxonomy.update(
            {
                "task_family": "judgment",
                "edit_regime": "judgment",
                "primary_archetype": "judgment",
                "statement_signature": _infer_statement_signature_bins(target_code),
            }
        )

    elif task_type in {"lean_code_generation", "lean_spec_generation"}:
        taxonomy.update(
            {
                "task_family": "program_synthesis",
                "edit_regime": task_type,
                "primary_archetype": task_type,
            }
        )
        source_language = record.get("source_language") or metadata.get("source_language")
        if source_language:
            taxonomy["source_language"] = source_language

    else:
        taxonomy.update({"task_family": "other", "edit_regime": "unknown", "primary_archetype": "unknown"})

    metadata["taxonomy"] = taxonomy
    return record
