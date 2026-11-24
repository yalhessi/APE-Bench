"""Input-only feasibility screen. From the checkout run PYTHONPATH=.:src ape/bin/python THIS_FILE."""

import hashlib
import json
import re
from pathlib import Path

from ape.toolkits.code.lean.lean_parser import parse_major_declarations
from src.mathlib_review.evidence.operators.naming_contrast import declaration_conclusion, outer_lhs
from src.mathlib_review.io import jsonl_rows
from src.mathlib_review.release.change_graph import parse_unified_diff
from src.mathlib_review.retrieval.declaration_table import conclusion_head


COHORTS = {
    "development": "data/pr_review_v5/first_round_development_before_2026-01-01.jsonl",
    "july": "inputs/probes/probe-2026-07-08-v1/input/episodes.jsonl",
}
BROAD = re.compile(r"[∑∏]'|(?<![A-Za-z0-9])(?:tsum|tprod|[hH]asSum|[hH]asProd(?!uct)|[sS]ummable|[mM]ultipliable)")
TOTAL = re.compile(r"(?:[∑∏]'|(?:_root_\.)?t(?:sum|prod)\b)")
NUMERAL = re.compile(r"[0-9]+")


def numeric_bound(conclusion):
    if conclusion_head(conclusion) not in {"ge", "le"}:
        return False
    lhs = outer_lhs(conclusion)
    if not lhs:
        return False
    rest = conclusion[len(lhs):].strip()
    if not rest.startswith(("≤", "≥")):
        return False
    rhs = rest[1:].strip()
    return any(NUMERAL.fullmatch(bound) and TOTAL.match(total)
               for bound, total in ((lhs, rhs), (rhs, lhs)))


def screen(diff):
    candidates = []
    broad = False
    unavailable = []
    for file in parse_unified_diff(diff):
        if not file.path.endswith(".lean") or file.status == "removed":
            continue
        if file.missing_patch_reason:
            unavailable.append(file.path)
        for hunk in file.hunks:
            post = [line for line in hunk.lines if line.startswith((" ", "+"))]
            source = "\n".join(line[1:] for line in post)
            if not BROAD.search(hunk.header + "\n" + source):
                continue
            broad = True
            for decl in parse_major_declarations(source):
                if decl.kind not in {"theorem", "lemma"} or not decl.signature.rstrip().endswith(":="):
                    continue
                result = declaration_conclusion(decl.signature)
                if not numeric_bound(result):
                    continue
                first = source.count("\n", 0, decl.span[0])
                last = first + decl.signature.count("\n")
                if any(line.startswith("+") for line in post[first:last + 1]):
                    candidates.append({"file": file.path, "line": hunk.new_start + first,
                                       "name": decl.name, "conclusion": " ".join(result.split())})
    return broad, candidates, unavailable


def census(path, input_key):
    digest = hashlib.sha256()
    all_prs, broad_prs, fires, partial = [], [], {}, {}
    for row in jsonl_rows(Path(path)):
        pr = row["pr_number"]
        diff = (row["input"] if input_key else row)["diff"]
        digest.update(f"{pr} {row['reviewed_head_sha']} {hashlib.sha256(diff.encode()).hexdigest()}\n".encode())
        all_prs.append(pr)
        broad, candidates, unavailable = screen(diff)
        if broad:
            broad_prs.append(pr)
        if candidates:
            fires[pr] = candidates
        if unavailable:
            partial[pr] = unavailable
    if len(set(all_prs)) != len(all_prs):
        raise ValueError("Expected one episode per PR")
    return {"input_path": path, "ordered_pr_head_diff_sha256": digest.hexdigest(),
            "count": len(all_prs), "all_prs": sorted(all_prs), "broad_prs": sorted(broad_prs),
            "candidates_by_pr": fires, "unavailable_lean_patches_by_pr": partial}


if __name__ == "__main__":
    print(json.dumps({k: census(path, k == "development") for k, path in COHORTS.items()},
                     ensure_ascii=False, sort_keys=True, indent=2))
