import difflib
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ape.toolkits.code.lean.lean_parser import (
    extract_imports,
    extract_proof_blocks,
    mask_noncode_regions,
    parse_major_declarations,
)


def _normalize_for_compare(text: str) -> str:
    if not text:
        return ""
    masked = mask_noncode_regions(text)
    return re.sub(r"\s+", " ", masked.strip())


@dataclass(frozen=True)
class _DeclDelta:
    kind: str
    signature_changed: bool
    body_changed: bool


def _decl_key(decl) -> Optional[str]:
    if getattr(decl, "fullname", None):
        return decl.fullname
    if getattr(decl, "name", None):
        return decl.name
    return None


def _decl_start_pos(decl) -> int:
    if hasattr(decl, "header_span") and getattr(decl, "header_span") is not None:
        return int(getattr(decl, "header_span")[0])
    if hasattr(decl, "span") and getattr(decl, "span") is not None:
        return int(getattr(decl, "span")[0])
    return 0


def _build_named_decl_map(decls) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for d in decls:
        k = _decl_key(d)
        if not k:
            continue
        if k in out:
            continue
        out[k] = d
    return out


def _build_decl_index_map_for_localization(decls) -> Dict[str, Any]:
    """
    Map decls to unique keys, including anonymous decls, for within-file localization.
    """
    out: Dict[str, Any] = {}
    for d in decls:
        k = _decl_key(d)
        if not k:
            k = f"<anon:{getattr(d, 'kind', 'decl')}@{_decl_start_pos(d)}>"
        if k in out:
            k = f"{k}#{_decl_start_pos(d)}"
        out[k] = d
    return out


def _fingerprint_signature_without_name(decl) -> str:
    sig = _normalize_for_compare(getattr(decl, "signature", "") or "")
    name = getattr(decl, "name", "") or ""
    if name:
        sig = sig.replace(name, "<NAME>", 1)
    return sig


def _pair_potential_renames(
    removed_keys: List[str],
    added_keys: List[str],
    orig_map: Dict[str, Any],
    ref_map: Dict[str, Any],
    similarity_threshold: float = 0.92,
) -> List[Tuple[str, str]]:
    candidates_by_kind: Dict[str, List[str]] = defaultdict(list)
    for k in added_keys:
        d = ref_map.get(k)
        if d is None:
            continue
        candidates_by_kind[getattr(d, "kind", "decl")].append(k)

    pairs: List[Tuple[str, str]] = []
    used_added: set[str] = set()

    for old_key in removed_keys:
        old_decl = orig_map.get(old_key)
        if old_decl is None:
            continue
        kind = getattr(old_decl, "kind", "decl")
        old_fp = _fingerprint_signature_without_name(old_decl)

        best = None
        best_score = 0.0
        for new_key in candidates_by_kind.get(kind, []):
            if new_key in used_added:
                continue
            new_decl = ref_map.get(new_key)
            if new_decl is None:
                continue
            new_fp = _fingerprint_signature_without_name(new_decl)
            score = difflib.SequenceMatcher(a=old_fp, b=new_fp).ratio()
            if score > best_score:
                best_score = score
                best = new_key

        if best is not None and best_score >= similarity_threshold:
            used_added.add(best)
            pairs.append((old_key, best))

    return pairs


def _match_anonymous_decls(
    anon_orig: List[Any],
    anon_ref: List[Any],
    similarity_threshold: float = 0.92,
) -> Tuple[List[Tuple[Any, Any]], List[Any], List[Any]]:
    ref_by_kind: Dict[str, List[Any]] = defaultdict(list)
    for d in anon_ref:
        ref_by_kind[getattr(d, "kind", "decl")].append(d)

    used_ref: set[int] = set()
    matched: List[Tuple[Any, Any]] = []
    unmatched_orig: List[Any] = []

    for o in anon_orig:
        kind = getattr(o, "kind", "decl")
        o_fp = _normalize_for_compare(getattr(o, "signature", "") or "")

        best = None
        best_score = 0.0
        for r in ref_by_kind.get(kind, []):
            rid = id(r)
            if rid in used_ref:
                continue
            r_fp = _normalize_for_compare(getattr(r, "signature", "") or "")
            score = difflib.SequenceMatcher(a=o_fp, b=r_fp).ratio()
            if score > best_score:
                best_score = score
                best = r

        if best is not None and best_score >= similarity_threshold:
            used_ref.add(id(best))
            matched.append((o, best))
        else:
            unmatched_orig.append(o)

    unmatched_ref = [r for r in anon_ref if id(r) not in used_ref]
    return matched, unmatched_orig, unmatched_ref


def _file_modification_type_from_diff(diff: str) -> str:
    if not diff:
        return "unknown"
    if "--- a/null" in diff or "--- /dev/null" in diff:
        return "new_file"
    if "+++ b/null" in diff or "+++ /dev/null" in diff:
        return "file_deletion"
    return "file_modification"


def _import_change_type(old_imports: List[str], new_imports: List[str]) -> str:
    a = set(old_imports)
    b = set(new_imports)
    added = b - a
    removed = a - b
    if not added and not removed:
        return "none"
    if added and not removed:
        return "add"
    if removed and not added:
        return "remove"
    return "add+remove"


def _import_change_counts(old_imports: List[str], new_imports: List[str]) -> Dict[str, int]:
    a = set(old_imports)
    b = set(new_imports)
    return {
        "added": int(len(b - a)),
        "removed": int(len(a - b)),
        "old_total": int(len(a)),
        "new_total": int(len(b)),
    }


_TACTIC_HINTS = re.compile(
    r"\b(by|simp|rw|simp_rw|aesop|linarith|nlinarith|omega|ring|exact|refine|intro|cases|rcases|"
    r"induction|simp\?|tauto|have|calc)\b"
)


def _diff_line_category_counts(diff: str) -> Dict[str, int]:
    counts = Counter()
    if not diff:
        return dict(counts)

    for line in diff.splitlines():
        if not line.startswith(("+", "-")):
            continue
        if line.startswith("+++") or line.startswith("---"):
            continue
        content = line[1:].lstrip()
        if not content:
            counts["blank"] += 1
            continue
        if re.match(r"^import\b", content):
            counts["import"] += 1
        elif re.match(r"^@\[[^\]]*\]", content) or re.match(r"^attribute\b", content):
            counts["attribute"] += 1
        elif re.match(r"^/--|^/-!|^/-|^--", content):
            counts["doc_or_comment"] += 1
        elif re.match(r"^(namespace|section|end|open|export|variable|variables|universe|universes)\b", content):
            counts["scope_or_open"] += 1
        elif re.match(r"^(set_option|notation|infix|prefix|postfix|macro|macro_rules|syntax|elab|run_cmd|#)", content):
            counts["command"] += 1
        elif re.match(r"^(theorem|lemma|def|instance|structure|class|abbrev|axiom|inductive)\b", content):
            counts["decl_header"] += 1
        elif _TACTIC_HINTS.search(mask_noncode_regions(content)):
            counts["proof_tactic"] += 1
        else:
            counts["other"] += 1

    return dict(counts)


def _diff_primary_category(counts: Dict[str, int]) -> str:
    if not counts:
        return "none"
    non_blank = {k: v for k, v in counts.items() if k != "blank"}
    if non_blank:
        return max(non_blank.items(), key=lambda kv: kv[1])[0]
    return "blank"


def _extract_math_domain(filename: Optional[str]) -> str:
    if not filename:
        return "Other"
    m = re.search(r"^Mathlib/([^/]+)/", filename)
    if m:
        return m.group(1)
    return "Other"


def _api_impact_level(added_count: int, removed_count: int, signature_changed_count: int) -> str:
    if added_count == 0 and removed_count == 0 and signature_changed_count == 0:
        return "none"
    if removed_count > 0 or signature_changed_count > 0:
        return "modify+add" if added_count > 0 else "modify"
    return "additive"


def _task_archetype(file_modification_type: str, semantic_change_subtype: str, api_impact_level: str) -> str:
    if file_modification_type == "new_file":
        return "new_module_creation"
    if semantic_change_subtype.startswith("remove"):
        return "migration_or_removal"
    if semantic_change_subtype in {"add_only", "add+body"} and api_impact_level == "additive":
        return "additive_extension"
    if api_impact_level in {"modify", "modify+add"}:
        return "integration_or_api_update"
    if semantic_change_subtype.startswith("modify_"):
        return "modification_only"
    return "other"


def _additive_flavor(added_workload_focus: str) -> str:
    if added_workload_focus == "proof_like":
        return "proof_centric"
    if added_workload_focus == "implementation_like":
        return "api_centric"
    if added_workload_focus == "mixed":
        return "mixed"
    return "n/a"


def _bin_dispersion_ratio(x: float) -> str:
    if x <= 0.05:
        return "≤5%"
    if x <= 0.20:
        return "5–20%"
    if x <= 0.50:
        return "20–50%"
    if x <= 0.80:
        return "50–80%"
    if x <= 0.95:
        return "80–95%"
    return ">95%"


def _header_body_focus(header_count: int, body_count: int, total_touched: int) -> str:
    if total_touched == 0:
        return "none"
    if header_count > 0 and body_count == 0:
        return "header_only"
    if body_count > 0 and header_count == 0:
        return "body_only"
    if header_count >= body_count * 2:
        return "header_heavy"
    if body_count >= header_count * 2:
        return "body_heavy"
    return "mixed"


def _decl_dispersion_ratio(src_len: int, decl_spans: List[Tuple[int, int]]) -> float:
    if src_len <= 0 or not decl_spans:
        return 0.0
    starts = [s for s, _ in decl_spans]
    ends = [e for _, e in decl_spans]
    span = max(ends) - min(starts)
    return float(span) / float(max(src_len, 1))


def _overall_span_for_proof_block_decl(decl) -> Tuple[int, int]:
    start = min(decl.header_span[0], decl.body_span[0])
    end = max(decl.header_span[1], decl.body_span[1])
    return (start, end)


def _parse_unified_diff_changed_line_numbers(diff: str) -> Tuple[List[int], List[int]]:
    old_changed: List[int] = []
    new_changed: List[int] = []
    if not diff:
        return old_changed, new_changed

    old_line = 0
    new_line = 0
    in_hunk = False

    for raw in diff.splitlines():
        if raw.startswith("@@"):
            m = re.search(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", raw)
            if not m:
                in_hunk = False
                continue
            old_line = int(m.group(1))
            new_line = int(m.group(3))
            in_hunk = True
            continue

        if not in_hunk:
            continue

        if raw.startswith(" "):
            old_line += 1
            new_line += 1
            continue

        if raw.startswith("-"):
            if raw.startswith("---"):
                continue
            old_changed.append(old_line)
            old_line += 1
            continue

        if raw.startswith("+"):
            if raw.startswith("+++"):
                continue
            new_changed.append(new_line)
            new_line += 1
            continue

    return old_changed, new_changed


def _line_starts(src: str) -> List[int]:
    starts = [0]
    for i, ch in enumerate(src):
        if ch == "\n":
            starts.append(i + 1)
    return starts


def _line_to_byte_span(src: str, line_starts: List[int], line_1_based: int) -> Tuple[int, int]:
    if line_1_based <= 0:
        return (0, 0)
    idx = line_1_based - 1
    if idx >= len(line_starts):
        return (len(src), len(src))
    start = line_starts[idx]
    end = line_starts[idx + 1] if idx + 1 < len(line_starts) else len(src)
    return (start, end)


def _overlaps(a: Tuple[int, int], b: Tuple[int, int]) -> bool:
    return max(a[0], b[0]) < min(a[1], b[1])


def _tactic_family_counts(text: str) -> Dict[str, int]:
    if not text or not text.strip():
        return {}
    masked = mask_noncode_regions(text)
    c = Counter()
    patterns = {
        "simp": r"\b(simp|dsimp|simp_rw)\b",
        "rw": r"\b(rw|rewrite)\b",
        "aesop": r"\b(aesop)\b",
        "linarith": r"\b(linarith|nlinarith)\b",
        "ring": r"\b(ring)\b",
        "omega": r"\b(omega)\b",
        "ext": r"\b(ext)\b",
        "cases": r"\b(cases|rcases)\b",
        "induction": r"\b(induction)\b",
        "calc": r"\b(calc)\b",
    }
    for name, pat in patterns.items():
        hits = len(re.findall(pat, masked))
        if hits:
            c[name] += hits
    return dict(c)


def _primary_tactic_family(counts: Dict[str, int]) -> str:
    if not counts:
        return "none"
    return max(counts.items(), key=lambda kv: kv[1])[0]


def compute_ape_bench_parser_taxonomy(
    *,
    original_code: str,
    reference_implementation: str,
    gold_diff: str,
    filename: Optional[str],
) -> Dict[str, Any]:
    """
    Compute parser-based taxonomy for file-patch proof engineering tasks.

    This function is intentionally *side-effect free* and returns only compact,
    benchmarking-oriented fields (no declaration name lists) suitable for embedding
    in `metadata`.
    """
    original = original_code or ""
    reference = reference_implementation or ""
    diff = gold_diff or ""

    math_domain = _extract_math_domain(filename)

    orig_decls = parse_major_declarations(original) if original else []
    ref_decls = parse_major_declarations(reference) if reference else []

    orig_map = _build_named_decl_map(orig_decls)
    ref_map = _build_named_decl_map(ref_decls)

    anon_orig = [d for d in orig_decls if _decl_key(d) is None]
    anon_ref = [d for d in ref_decls if _decl_key(d) is None]

    orig_keys = set(orig_map.keys())
    ref_keys = set(ref_map.keys())

    added_named = sorted(ref_keys - orig_keys)
    removed_named = sorted(orig_keys - ref_keys)
    common = sorted(orig_keys & ref_keys)

    # Pair potential renames/moves to avoid false add/remove.
    rename_pairs = _pair_potential_renames(removed_named, added_named, orig_map, ref_map)
    paired_removed = {a for a, _ in rename_pairs}
    paired_added = {b for _, b in rename_pairs}
    removed_named = [k for k in removed_named if k not in paired_removed]
    added_named = [k for k in added_named if k not in paired_added]

    deltas: List[_DeclDelta] = []
    for k in common:
        o = orig_map[k]
        r = ref_map[k]
        sig_changed = _normalize_for_compare(getattr(o, "signature", "") or "") != _normalize_for_compare(
            getattr(r, "signature", "") or ""
        )
        body_changed = _normalize_for_compare(getattr(o, "proof", "") or "") != _normalize_for_compare(
            getattr(r, "proof", "") or ""
        )
        deltas.append(_DeclDelta(kind=getattr(r, "kind", "decl"), signature_changed=bool(sig_changed), body_changed=bool(body_changed)))

    for old_k, new_k in rename_pairs:
        o = orig_map.get(old_k)
        r = ref_map.get(new_k)
        if o is None or r is None:
            continue
        sig_changed = _normalize_for_compare(getattr(o, "signature", "") or "") != _normalize_for_compare(
            getattr(r, "signature", "") or ""
        )
        body_changed = _normalize_for_compare(getattr(o, "proof", "") or "") != _normalize_for_compare(
            getattr(r, "proof", "") or ""
        )
        deltas.append(_DeclDelta(kind=getattr(r, "kind", "decl"), signature_changed=bool(sig_changed), body_changed=bool(body_changed)))

    changed_signature_named = sum(1 for d in deltas if d.signature_changed)
    changed_body_named = sum(1 for d in deltas if d.body_changed)
    kinds_changed = Counter(d.kind for d in deltas if d.signature_changed or d.body_changed)

    # Anonymous matching (captures unnamed instances/examples).
    anon_matched, anon_unmatched_orig, anon_unmatched_ref = _match_anonymous_decls(anon_orig, anon_ref)
    anon_added_count = len(anon_unmatched_ref)
    anon_removed_count = len(anon_unmatched_orig)
    anon_sig_changed = 0
    anon_body_changed = 0
    for o, r in anon_matched:
        if _normalize_for_compare(getattr(o, "signature", "") or "") != _normalize_for_compare(getattr(r, "signature", "") or ""):
            anon_sig_changed += 1
        if _normalize_for_compare(getattr(o, "proof", "") or "") != _normalize_for_compare(getattr(r, "proof", "") or ""):
            anon_body_changed += 1

    total_added = len(added_named) + anon_added_count
    total_removed = len(removed_named) + anon_removed_count
    total_sig_changed = changed_signature_named + anon_sig_changed
    total_body_changed = changed_body_named + anon_body_changed

    # Semantic subtype (interpretable).
    has_add = total_added > 0
    has_remove = total_removed > 0
    has_sig = total_sig_changed > 0
    has_body = total_body_changed > 0
    if has_remove:
        if (not has_add) and (not has_sig) and (not has_body):
            semantic_subtype = "remove_only"
        elif has_add and (not has_sig) and (not has_body):
            semantic_subtype = "remove+add"
        elif (not has_add) and (has_sig or has_body):
            semantic_subtype = "remove+modify"
        elif has_add and (has_sig or has_body):
            semantic_subtype = "remove+add+modify"
        else:
            semantic_subtype = "remove_involved"
    elif has_add and not has_sig and not has_body:
        semantic_subtype = "add_only"
    elif has_add and has_sig and not has_body:
        semantic_subtype = "add+signature"
    elif has_add and has_body and not has_sig:
        semantic_subtype = "add+body"
    elif has_add and has_sig and has_body:
        semantic_subtype = "add+sig+body"
    elif (not has_add) and has_sig and not has_body:
        semantic_subtype = "modify_signature_only"
    elif (not has_add) and has_body and not has_sig:
        semantic_subtype = "modify_body_only"
    elif (not has_add) and has_body and has_sig:
        semantic_subtype = "modify_sig+body"
    elif (not has_add) and (not has_remove) and (not has_sig) and (not has_body):
        semantic_subtype = "non_decl_only"
    else:
        semantic_subtype = "mixed_other"

    file_modification_type = _file_modification_type_from_diff(diff)

    old_imports = extract_imports(original) if original else []
    new_imports = extract_imports(reference) if reference else []
    import_change_type = _import_change_type(old_imports, new_imports)
    import_change_counts = _import_change_counts(old_imports, new_imports)

    diff_line_counts = _diff_line_category_counts(diff)
    diff_primary_category = _diff_primary_category(diff_line_counts)

    # Added-kind profiles (include anonymous additions).
    kinds_added_named = Counter(getattr(ref_map.get(k), "kind", "decl") for k in added_named if k in ref_map)
    kinds_added_anon = Counter(getattr(d, "kind", "decl") for d in anon_unmatched_ref)
    kinds_added = kinds_added_named + kinds_added_anon

    proof_like_added = sum(kinds_added.get(k, 0) for k in ("lemma", "theorem", "example"))
    impl_like_added = sum(kinds_added.get(k, 0) for k in ("def", "instance", "class", "structure", "abbrev"))
    if proof_like_added > 0 and impl_like_added == 0:
        added_workload_focus = "proof_like"
    elif impl_like_added > 0 and proof_like_added == 0:
        added_workload_focus = "implementation_like"
    elif proof_like_added > 0 and impl_like_added > 0:
        added_workload_focus = "mixed"
    else:
        added_workload_focus = "none"

    api_impact_level = _api_impact_level(total_added, total_removed, total_sig_changed)
    task_archetype = _task_archetype(file_modification_type, semantic_subtype, api_impact_level)
    additive_flavor = _additive_flavor(added_workload_focus) if task_archetype == "additive_extension" else "n/a"

    # Diff-to-declaration localization (header/body, dispersion).
    # Not applicable for new files: the "edited span" is trivially the whole file.
    old_changed_lines, new_changed_lines = _parse_unified_diff_changed_line_numbers(diff)
    orig_line_starts = _line_starts(original) if original else [0]
    ref_line_starts = _line_starts(reference) if reference else [0]
    old_byte_spans = [_line_to_byte_span(original, orig_line_starts, ln) for ln in old_changed_lines]
    new_byte_spans = [_line_to_byte_span(reference, ref_line_starts, ln) for ln in new_changed_lines]

    orig_blocks = extract_proof_blocks(original) if original else []
    ref_blocks = extract_proof_blocks(reference) if reference else []
    orig_block_map = _build_decl_index_map_for_localization(orig_blocks)
    ref_block_map = _build_decl_index_map_for_localization(ref_blocks)

    touched_new_any: set[str] = set()
    touched_new_header: set[str] = set()
    touched_new_body: set[str] = set()
    for k, d in ref_block_map.items():
        for sp in new_byte_spans:
            if not _overlaps(sp, d.header_span) and not _overlaps(sp, d.body_span):
                continue
            touched_new_any.add(k)
            if _overlaps(sp, d.header_span):
                touched_new_header.add(k)
            if _overlaps(sp, d.body_span):
                touched_new_body.add(k)

    touched_kinds_new = Counter()
    for k in touched_new_any:
        d = ref_block_map.get(k)
        if d is not None:
            touched_kinds_new[getattr(d, "kind", "decl")] += 1

    # Instance-related tag: union across added/changed/touched declaration kinds.
    kind_union = set(kinds_added.keys()) | set(kinds_changed.keys()) | set(touched_kinds_new.keys())
    instance_related = any(k in {"instance", "class", "structure"} for k in kind_union)

    touched_new_spans = [
        _overall_span_for_proof_block_decl(ref_block_map[k])
        for k in touched_new_any
        if k in ref_block_map
    ]
    dispersion_new = _decl_dispersion_ratio(len(reference), touched_new_spans)

    header_body_focus_new = _header_body_focus(
        header_count=len(touched_new_header),
        body_count=len(touched_new_body),
        total_touched=len(touched_new_any),
    )
    diff_localization_applicable = bool(
        file_modification_type != "new_file"
        and reference
        and len(touched_new_any) > 0
    )

    # Proof technique proxy: only from added proofs and changed bodies.
    changed_body_tactics = Counter()
    # We only have stable text for named decls; for anonymous, skip (still OK as proxy).
    for k in common:
        o = orig_map[k]
        r = ref_map[k]
        if _normalize_for_compare(getattr(o, "proof", "") or "") != _normalize_for_compare(getattr(r, "proof", "") or ""):
            changed_body_tactics.update(_tactic_family_counts(getattr(r, "proof", "") or ""))

    added_proof_tactics = Counter()
    for k in added_named:
        d = ref_map.get(k)
        if d is None:
            continue
        if getattr(d, "kind", "") in {"lemma", "theorem", "example"}:
            added_proof_tactics.update(_tactic_family_counts(getattr(d, "proof", "") or ""))

    return {
        "math_domain": math_domain,
        "file_modification_type": file_modification_type,
        "import_change_type": import_change_type,
        "import_change_counts": import_change_counts,
        "diff_primary_category": diff_primary_category,
        "diff_line_category_counts": diff_line_counts,
        "decl_change": {
            "added_count": int(total_added),
            "removed_count": int(total_removed),
            "signature_changed_count": int(total_sig_changed),
            "body_changed_count": int(total_body_changed),
            "semantic_subtype": semantic_subtype,
            "api_impact_level": api_impact_level,
            "task_archetype": task_archetype,
            "additive_flavor": additive_flavor,
            "added_workload_focus": added_workload_focus,
            "instance_related": bool(instance_related),
        },
        "diff_localization": {
            "applicable": bool(diff_localization_applicable),
            "header_body_focus_new": header_body_focus_new,
            "touched_span_new_ratio": round(float(dispersion_new), 4),
            "touched_span_new_ratio_bin": _bin_dispersion_ratio(float(dispersion_new)) if diff_localization_applicable else "n/a",
            "touched_decl_new_count": int(len(touched_new_any)),
            "touched_header_new_count": int(len(touched_new_header)),
            "touched_body_new_count": int(len(touched_new_body)),
            "touched_kinds_new": dict(touched_kinds_new),
        },
        "proof_tactic_proxy": {
            "added_proof_primary_tactic_family": _primary_tactic_family(dict(added_proof_tactics)),
            "changed_body_primary_tactic_family": _primary_tactic_family(dict(changed_body_tactics)),
        },
    }
